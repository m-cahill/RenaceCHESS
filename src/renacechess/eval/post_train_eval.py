"""Post-training evaluation orchestrator (M32).

This module evaluates trained M31 checkpoints against the frozen eval v2 set
and compares them to fresh-init baselines to measure training effect.

Key design principles:
1. Read-only evaluation (no retraining, no tuning)
2. Deterministic baseline (fixed seed 1337)
3. Same architecture for baseline and trained
4. Reproducible metrics with determinism hash

See docs/milestones/PhaseE/M32/M32_plan.md for the governing specification.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import torch

from renacechess.conditioning.buckets import SkillBucketId
from renacechess.contracts.models import (
    DeltaMetricsInlineV1,
    FrozenEvalIntegrityV1,
    OutcomeEvalMetricsInlineV1,
    PolicyEvalMetricsInlineV1,
    PostTrainEvalReportV1,
    SkillBucketEvalV1,
)
from renacechess.determinism import canonical_json_dump
from renacechess.models.baseline_v1 import BaselinePolicyV1
from renacechess.models.outcome_head_v1 import OutcomeHeadV1

# =============================================================================
# Constants
# =============================================================================

M32_EVAL_BASELINE_SEED = 1337
SIGNIFICANCE_THRESHOLD = 0.01  # 1% threshold for significant change


def _compute_sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def _compute_sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 hash of bytes."""
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _get_git_commit_sha() -> str:
    """Get current git commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return "0" * 40


def _set_deterministic_seed(seed: int) -> None:
    """Set all random seeds for determinism."""
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class PolicyMetricsAccumulator:
    """Accumulates policy evaluation metrics."""

    def __init__(self) -> None:
        self.top1_correct: int = 0
        self.top3_correct: int = 0
        self.top5_correct: int = 0
        self.nll_sum: float = 0.0
        self.entropy_sum: float = 0.0
        self.count: int = 0

    def add(
        self,
        move_probs: dict[str, float],
        chosen_move: str,
    ) -> None:
        """Add a policy prediction."""
        self.count += 1

        # Sort by probability descending
        sorted_moves = sorted(move_probs.items(), key=lambda x: -x[1])

        # Top-k accuracy
        top_moves = [m for m, _ in sorted_moves[:5]]
        if top_moves and top_moves[0] == chosen_move:
            self.top1_correct += 1
        if chosen_move in top_moves[:3]:
            self.top3_correct += 1
        if chosen_move in top_moves[:5]:
            self.top5_correct += 1

        # NLL
        chosen_prob = move_probs.get(chosen_move, 1e-10)
        chosen_prob = max(1e-10, min(1.0, chosen_prob))
        self.nll_sum += -math.log(chosen_prob)

        # Entropy
        entropy = 0.0
        for prob in move_probs.values():
            if prob > 1e-10:
                entropy -= prob * math.log(prob)
        self.entropy_sum += entropy

    def compute(self) -> PolicyEvalMetricsInlineV1:
        """Compute aggregate metrics."""
        if self.count == 0:
            return PolicyEvalMetricsInlineV1(
                top1_accuracy=0.0,
                top3_accuracy=0.0,
                top5_accuracy=0.0,
                nll=0.0,
                entropy=0.0,
                samples_evaluated=0,
            )

        return PolicyEvalMetricsInlineV1(
            top1_accuracy=round(self.top1_correct / self.count, 6),
            top3_accuracy=round(self.top3_correct / self.count, 6),
            top5_accuracy=round(self.top5_correct / self.count, 6),
            nll=round(self.nll_sum / self.count, 6),
            entropy=round(self.entropy_sum / self.count, 6),
            samples_evaluated=self.count,
        )


class OutcomeMetricsAccumulator:
    """Accumulates outcome evaluation metrics."""

    def __init__(self) -> None:
        self.correct: int = 0
        self.brier_sum: float = 0.0
        self.nll_sum: float = 0.0
        self.count: int = 0

        # For ECE
        self.confidences: list[float] = []
        self.accuracies: list[bool] = []

        # Per-outcome accuracy
        self.win_correct: int = 0
        self.win_total: int = 0
        self.draw_correct: int = 0
        self.draw_total: int = 0
        self.loss_correct: int = 0
        self.loss_total: int = 0

    def add(
        self,
        wdl_probs: dict[str, float],
        true_outcome: Literal["win", "draw", "loss"],
    ) -> None:
        """Add an outcome prediction."""
        self.count += 1

        # Predicted outcome (argmax)
        pred_outcome = max(wdl_probs.items(), key=lambda x: x[1])[0]
        pred_label = {"w": "win", "d": "draw", "l": "loss"}.get(pred_outcome, pred_outcome)
        is_correct = pred_label == true_outcome
        if is_correct:
            self.correct += 1

        # Per-outcome tracking
        if true_outcome == "win":
            self.win_total += 1
            if is_correct:
                self.win_correct += 1
        elif true_outcome == "draw":
            self.draw_total += 1
            if is_correct:
                self.draw_correct += 1
        else:
            self.loss_total += 1
            if is_correct:
                self.loss_correct += 1

        # Brier score
        true_vec = {"w": 0.0, "d": 0.0, "l": 0.0}
        if true_outcome == "win":
            true_vec["w"] = 1.0
        elif true_outcome == "draw":
            true_vec["d"] = 1.0
        else:
            true_vec["l"] = 1.0

        brier = sum(
            (wdl_probs.get(k, 0.0) - true_vec[k]) ** 2 for k in ["w", "d", "l"]
        )
        self.brier_sum += brier

        # NLL
        prob_true = wdl_probs.get(
            {"win": "w", "draw": "d", "loss": "l"}[true_outcome], 1e-10
        )
        prob_true = max(1e-10, min(1.0, prob_true))
        self.nll_sum += -math.log(prob_true)

        # For ECE
        max_prob = max(wdl_probs.values())
        self.confidences.append(max_prob)
        self.accuracies.append(is_correct)

    def compute_ece(self, n_bins: int = 10) -> float:
        """Compute Expected Calibration Error."""
        if not self.confidences:
            return 0.0

        ece = 0.0
        total = len(self.confidences)
        bin_edges = [i / n_bins for i in range(n_bins + 1)]
        bin_edges[-1] = 1.01  # Include 1.0

        for i in range(n_bins):
            low, high = bin_edges[i], bin_edges[i + 1]
            bin_items = [
                j
                for j, conf in enumerate(self.confidences)
                if low <= conf < high
            ]
            if not bin_items:
                continue

            bin_size = len(bin_items)
            avg_conf = sum(self.confidences[j] for j in bin_items) / bin_size
            avg_acc = sum(1 for j in bin_items if self.accuracies[j]) / bin_size

            ece += (bin_size / total) * abs(avg_acc - avg_conf)

        return ece

    def compute(self) -> OutcomeEvalMetricsInlineV1:
        """Compute aggregate metrics."""
        if self.count == 0:
            return OutcomeEvalMetricsInlineV1(
                accuracy=0.0,
                brier_score=0.0,
                nll=0.0,
                ece=0.0,
                samples_evaluated=0,
            )

        win_acc = self.win_correct / self.win_total if self.win_total > 0 else None
        draw_acc = self.draw_correct / self.draw_total if self.draw_total > 0 else None
        loss_acc = self.loss_correct / self.loss_total if self.loss_total > 0 else None

        return OutcomeEvalMetricsInlineV1(
            accuracy=round(self.correct / self.count, 6),
            brier_score=round(self.brier_sum / self.count, 6),
            nll=round(self.nll_sum / self.count, 6),
            ece=round(self.compute_ece(), 6),
            win_accuracy=round(win_acc, 6) if win_acc is not None else None,
            draw_accuracy=round(draw_acc, 6) if draw_acc is not None else None,
            loss_accuracy=round(loss_acc, 6) if loss_acc is not None else None,
            samples_evaluated=self.count,
        )


def compute_delta(
    baseline: PolicyEvalMetricsInlineV1 | OutcomeEvalMetricsInlineV1,
    trained: PolicyEvalMetricsInlineV1 | OutcomeEvalMetricsInlineV1,
    primary_metric: str,
    higher_is_better: bool,
) -> DeltaMetricsInlineV1:
    """Compute delta metrics between baseline and trained."""
    baseline_val = getattr(baseline, primary_metric.replace("Accuracy", "_accuracy"))
    trained_val = getattr(trained, primary_metric.replace("Accuracy", "_accuracy"))

    # Handle snake_case attribute names
    if baseline_val is None:
        baseline_val = getattr(baseline, primary_metric, 0.0)
    if trained_val is None:
        trained_val = getattr(trained, primary_metric, 0.0)

    delta = trained_val - baseline_val

    # Determine direction
    if abs(delta) < 1e-10:
        direction: Literal["improved", "degraded", "unchanged"] = "unchanged"
    elif higher_is_better:
        direction = "improved" if delta > 0 else "degraded"
    else:
        direction = "improved" if delta < 0 else "degraded"

    # Percentage change
    pct_change: float | None = None
    if baseline_val != 0:
        pct_change = round((delta / abs(baseline_val)) * 100, 2)

    # Significance
    is_significant = abs(delta) >= SIGNIFICANCE_THRESHOLD

    return DeltaMetricsInlineV1(
        primary_metric=primary_metric,
        primary_metric_baseline=round(baseline_val, 6),
        primary_metric_trained=round(trained_val, 6),
        primary_metric_delta=round(delta, 6),
        direction=direction,
        percentage_change=pct_change,
        is_significant=is_significant,
    )


def load_frozen_eval_v2_records(manifest_path: Path) -> list[dict[str, Any]]:
    """Load all records from frozen eval v2 manifest."""
    manifest_dict = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_dir = manifest_path.parent

    records: list[dict[str, Any]] = []
    shard_refs = manifest_dict.get("shardRefs", [])

    for shard_ref in shard_refs:
        shard_path = manifest_dir / shard_ref
        if not shard_path.exists():
            raise FileNotFoundError(f"Shard not found: {shard_path}")

        with shard_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    return records


def evaluate_models(
    policy_model: BaselinePolicyV1,
    outcome_model: OutcomeHeadV1,
    records: list[dict[str, Any]],
) -> tuple[PolicyEvalMetricsInlineV1, OutcomeEvalMetricsInlineV1, dict[str, int]]:
    """Evaluate models on frozen eval records."""
    policy_acc = PolicyMetricsAccumulator()
    outcome_acc = OutcomeMetricsAccumulator()
    bucket_counts: dict[str, int] = defaultdict(int)

    for record in records:
        # Extract position data
        position = record.get("position", {})
        fen = position.get("fen", "")
        legal_moves = position.get("legalMoves", [])

        # Extract conditioning
        conditioning = record.get("conditioning", {})
        skill_bucket = conditioning.get("skillBucketId", "unknown")
        time_control = conditioning.get("timeControlClass")

        # Extract labels
        meta = record.get("meta", {})
        chosen_move = meta.get("chosenMove")
        game_result = meta.get("gameResult")

        bucket_counts[skill_bucket] += 1

        # Policy evaluation
        if chosen_move and legal_moves:
            with torch.no_grad():
                move_probs = policy_model(fen, skill_bucket, time_control, legal_moves)
            policy_acc.add(move_probs, chosen_move)

        # Outcome evaluation
        if game_result in ("win", "draw", "loss"):
            with torch.no_grad():
                wdl_probs = outcome_model(fen, skill_bucket, time_control)
            outcome_acc.add(wdl_probs, game_result)

    return policy_acc.compute(), outcome_acc.compute(), dict(bucket_counts)


def evaluate_by_bucket(
    policy_model: BaselinePolicyV1,
    outcome_model: OutcomeHeadV1,
    records: list[dict[str, Any]],
) -> dict[str, tuple[PolicyEvalMetricsInlineV1, OutcomeEvalMetricsInlineV1, int]]:
    """Evaluate models per skill bucket."""
    # Group records by bucket
    by_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        conditioning = record.get("conditioning", {})
        skill_bucket = conditioning.get("skillBucketId", "unknown")
        by_bucket[skill_bucket].append(record)

    results: dict[str, tuple[PolicyEvalMetricsInlineV1, OutcomeEvalMetricsInlineV1, int]] = {}
    for bucket, bucket_records in by_bucket.items():
        policy_metrics, outcome_metrics, _ = evaluate_models(
            policy_model, outcome_model, bucket_records
        )
        results[bucket] = (policy_metrics, outcome_metrics, len(bucket_records))

    return results


def run_post_train_evaluation(
    policy_checkpoint_path: Path,
    outcome_checkpoint_path: Path,
    frozen_eval_manifest_path: Path,
    training_run_report_path: Path,
    output_dir: Path,
    eval_baseline_seed: int = M32_EVAL_BASELINE_SEED,
) -> PostTrainEvalReportV1:
    """Run post-training evaluation and produce report.

    Args:
        policy_checkpoint_path: Path to trained policy checkpoint.
        outcome_checkpoint_path: Path to trained outcome checkpoint.
        frozen_eval_manifest_path: Path to frozen eval v2 manifest.
        training_run_report_path: Path to M31 training run report.
        output_dir: Directory for output artifacts.
        eval_baseline_seed: Seed for baseline initialization (default: 1337).

    Returns:
        PostTrainEvalReportV1 artifact.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Compute hashes
    frozen_eval_hash = _compute_sha256_file(frozen_eval_manifest_path)
    training_report_hash = _compute_sha256_file(training_run_report_path)
    policy_checkpoint_hash = _compute_sha256_file(policy_checkpoint_path)
    outcome_checkpoint_hash = _compute_sha256_file(outcome_checkpoint_path)
    code_commit = _get_git_commit_sha()

    # Load frozen eval records
    records = load_frozen_eval_v2_records(frozen_eval_manifest_path)

    # Load frozen eval manifest for integrity proof
    manifest_dict = json.loads(frozen_eval_manifest_path.read_text(encoding="utf-8"))

    # =========================================================================
    # Evaluate TRAINED models
    # =========================================================================
    trained_policy = BaselinePolicyV1()
    trained_policy.load_state_dict(
        torch.load(policy_checkpoint_path, map_location="cpu", weights_only=True)
    )
    trained_policy.eval()

    trained_outcome = OutcomeHeadV1()
    trained_outcome.load_state_dict(
        torch.load(outcome_checkpoint_path, map_location="cpu", weights_only=True)
    )
    trained_outcome.eval()

    trained_policy_metrics, trained_outcome_metrics, _ = evaluate_models(
        trained_policy, trained_outcome, records
    )

    trained_by_bucket = evaluate_by_bucket(trained_policy, trained_outcome, records)

    # =========================================================================
    # Evaluate BASELINE models (fresh init with fixed seed)
    # =========================================================================
    _set_deterministic_seed(eval_baseline_seed)

    baseline_policy = BaselinePolicyV1()
    baseline_policy.eval()

    baseline_outcome = OutcomeHeadV1()
    baseline_outcome.eval()

    baseline_policy_metrics, baseline_outcome_metrics, bucket_counts = evaluate_models(
        baseline_policy, baseline_outcome, records
    )

    baseline_by_bucket = evaluate_by_bucket(baseline_policy, baseline_outcome, records)

    # =========================================================================
    # Compute DELTAS
    # =========================================================================
    policy_delta = compute_delta(
        baseline_policy_metrics,
        trained_policy_metrics,
        "top1_accuracy",
        higher_is_better=True,
    )

    outcome_delta = compute_delta(
        baseline_outcome_metrics,
        trained_outcome_metrics,
        "accuracy",
        higher_is_better=True,
    )

    # =========================================================================
    # Build per-bucket breakdown
    # =========================================================================
    canonical_buckets: list[SkillBucketId] = [
        "lt_800",
        "800_999",
        "1000_1199",
        "1200_1399",
        "1400_1599",
        "1600_1799",
        "gte_1800",
    ]

    by_skill_bucket: list[SkillBucketEvalV1] = []
    for bucket in canonical_buckets:
        samples = bucket_counts.get(bucket, 0)
        trained_p, trained_o = (
            trained_by_bucket.get(bucket, (None, None, 0))[:2]
            if bucket in trained_by_bucket
            else (None, None)
        )
        baseline_p, baseline_o = (
            baseline_by_bucket.get(bucket, (None, None, 0))[:2]
            if bucket in baseline_by_bucket
            else (None, None)
        )

        by_skill_bucket.append(
            SkillBucketEvalV1(
                skill_bucket=bucket,
                samples=samples,
                trained_policy_metrics=trained_p,
                trained_outcome_metrics=trained_o,
                baseline_policy_metrics=baseline_p,
                baseline_outcome_metrics=baseline_o,
            )
        )

    # =========================================================================
    # Build integrity proof
    # =========================================================================
    frozen_eval_integrity = FrozenEvalIntegrityV1(
        manifest_hash=frozen_eval_hash,
        position_count=len(records),
        shard_count=len(manifest_dict.get("shardRefs", [])),
        skill_bucket_counts=bucket_counts,
        no_training_overlap=True,  # Frozen eval v2 is synthetic, no overlap by design
        iteration_deterministic=True,
    )

    # =========================================================================
    # Build report
    # =========================================================================
    now = datetime.now(UTC)

    report_partial = PostTrainEvalReportV1(
        version="1.0",
        generated_at=now,
        frozen_eval_manifest_hash=frozen_eval_hash,
        training_run_report_hash=training_report_hash,
        policy_checkpoint_hash=policy_checkpoint_hash,
        outcome_checkpoint_hash=outcome_checkpoint_hash,
        code_commit_sha=code_commit,
        eval_baseline_seed=eval_baseline_seed,
        positions_evaluated=len(records),
        trained_policy_metrics=trained_policy_metrics,
        trained_outcome_metrics=trained_outcome_metrics,
        baseline_policy_metrics=baseline_policy_metrics,
        baseline_outcome_metrics=baseline_outcome_metrics,
        policy_delta=policy_delta,
        outcome_delta=outcome_delta,
        by_skill_bucket=by_skill_bucket,
        frozen_eval_integrity=frozen_eval_integrity,
        audit_notes=(
            f"M32 POST-TRAIN-EVAL-PACK-001: Evaluated {len(records)} positions from "
            f"frozen eval v2. Baseline seed: {eval_baseline_seed}."
        ),
        determinism_hash="sha256:" + "0" * 64,  # Placeholder
    )

    # Compute determinism hash
    report_dict = report_partial.model_dump(mode="json", by_alias=True)
    del report_dict["determinismHash"]
    report_bytes = canonical_json_dump(report_dict)
    determinism_hash = _compute_sha256_bytes(report_bytes)

    # Create final report
    report = PostTrainEvalReportV1(
        **{**report_partial.model_dump(by_alias=False), "determinism_hash": determinism_hash}
    )

    # Save report
    report_path = output_dir / "post_train_eval_report.json"
    report_dict = report.model_dump(mode="json", by_alias=True)
    report_json = canonical_json_dump(report_dict)
    report_path.write_bytes(report_json)

    return report

