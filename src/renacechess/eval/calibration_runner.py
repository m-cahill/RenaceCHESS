"""Calibration evaluation runner for M24.

This module provides deterministic calibration metrics computation for
measuring human-aligned calibration quality of policy and outcome predictions.

Per M24 locked decisions:
- Requires --manifest flag (fail fast if missing)
- Checkpoint-optional (CI uses baselines only)
- Measurement-only (does not feed runtime logic)
- Per-Elo bucket stratification using canonical buckets from conditioning.buckets
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, get_args

from renacechess.conditioning.buckets import SkillBucketId
from renacechess.contracts.models import (
    CalibrationBinV1,
    CalibrationHistogramV1,
    CalibrationMetricsV1,
    EloBucketCalibrationV1,
    FrozenEvalManifestV1,
    OutcomeCalibrationMetricsV1,
    PolicyCalibrationMetricsV1,
)
from renacechess.determinism import canonical_hash

# Fixed bin edges for calibration histograms (10 bins)
BIN_EDGES = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


def get_canonical_skill_buckets() -> list[str]:
    """Return canonical skill bucket IDs from conditioning.buckets.

    This function is the single source of truth for skill bucket enumeration.
    It ensures M24 calibration uses the same buckets as M06 conditioning.
    """
    # Extract from the Literal type
    return list(get_args(SkillBucketId))


class CalibrationAccumulator:
    """Accumulates samples for calibration metric computation.

    Tracks predictions and outcomes for computing ECE, Brier score, and NLL.
    """

    def __init__(self) -> None:
        self.predictions: list[float] = []  # Predicted confidence/probability
        self.outcomes: list[int] = []  # 1 if correct/occurred, 0 otherwise
        self.nll_sum: float = 0.0
        self.nll_count: int = 0

    def add(self, confidence: float, correct: bool, prob_for_nll: float | None = None) -> None:
        """Add a single prediction.

        Args:
            confidence: Predicted confidence (0-1)
            correct: Whether the prediction was correct
            prob_for_nll: Probability assigned to true outcome (for NLL)
        """
        self.predictions.append(confidence)
        self.outcomes.append(1 if correct else 0)

        # Compute NLL contribution
        if prob_for_nll is not None and prob_for_nll > 0:
            self.nll_sum += -math.log(prob_for_nll)
            self.nll_count += 1

    @property
    def count(self) -> int:
        """Return number of samples accumulated."""
        return len(self.predictions)

    def compute_ece(self) -> float:
        """Compute Expected Calibration Error (ECE).

        ECE = Σ (|B_m| / n) * |acc(B_m) - conf(B_m)|

        where B_m is the set of predictions in bin m.
        """
        if not self.predictions:
            return 0.0

        n = len(self.predictions)
        ece = 0.0

        for i in range(len(BIN_EDGES) - 1):
            bin_start = BIN_EDGES[i]
            bin_end = BIN_EDGES[i + 1]

            # Get samples in this bin
            bin_indices = [
                j
                for j, conf in enumerate(self.predictions)
                if bin_start <= conf < bin_end or (i == len(BIN_EDGES) - 2 and conf == bin_end)
            ]

            if not bin_indices:
                continue

            bin_size = len(bin_indices)
            avg_conf = sum(self.predictions[j] for j in bin_indices) / bin_size
            avg_acc = sum(self.outcomes[j] for j in bin_indices) / bin_size

            ece += (bin_size / n) * abs(avg_acc - avg_conf)

        return ece

    def compute_brier_score(self) -> float:
        """Compute Brier score.

        Brier = (1/n) * Σ (p_i - y_i)^2
        """
        if not self.predictions:
            return 0.0

        n = len(self.predictions)
        return sum((p - o) ** 2 for p, o in zip(self.predictions, self.outcomes)) / n

    def compute_nll(self) -> float:
        """Compute average negative log-likelihood."""
        if self.nll_count == 0:
            return 0.0
        return self.nll_sum / self.nll_count

    def build_histogram(self) -> CalibrationHistogramV1:
        """Build calibration histogram with per-bin statistics."""
        bins: list[CalibrationBinV1] = []

        for i in range(len(BIN_EDGES) - 1):
            bin_start = BIN_EDGES[i]
            bin_end = BIN_EDGES[i + 1]

            # Get samples in this bin
            bin_indices = [
                j
                for j, conf in enumerate(self.predictions)
                if bin_start <= conf < bin_end or (i == len(BIN_EDGES) - 2 and conf == bin_end)
            ]

            count = len(bin_indices)
            avg_conf: float | None = None
            emp_acc: float | None = None

            if count > 0:
                avg_conf = sum(self.predictions[j] for j in bin_indices) / count
                emp_acc = sum(self.outcomes[j] for j in bin_indices) / count

            bins.append(
                CalibrationBinV1(
                    bin_start=bin_start,
                    bin_end=bin_end,
                    count=count,
                    avg_confidence=round(avg_conf, 6) if avg_conf is not None else None,
                    empirical_accuracy=round(emp_acc, 6) if emp_acc is not None else None,
                )
            )

        return CalibrationHistogramV1(bin_edges=BIN_EDGES.copy(), bins=bins)


class OutcomeCalibrationAccumulator:
    """Accumulates samples for outcome (W/D/L) calibration."""

    def __init__(self) -> None:
        self.win_acc = CalibrationAccumulator()
        self.draw_acc = CalibrationAccumulator()
        self.loss_acc = CalibrationAccumulator()

    def add(
        self,
        p_win: float,
        p_draw: float,
        p_loss: float,
        actual_outcome: Literal["win", "draw", "loss"],
    ) -> None:
        """Add an outcome prediction.

        Args:
            p_win: Predicted win probability
            p_draw: Predicted draw probability
            p_loss: Predicted loss probability
            actual_outcome: The actual game outcome
        """
        # Map outcome to probabilities
        if actual_outcome == "win":
            prob_true = p_win
            self.win_acc.add(p_win, True, prob_true)
            self.draw_acc.add(p_draw, False, None)
            self.loss_acc.add(p_loss, False, None)
        elif actual_outcome == "draw":
            prob_true = p_draw
            self.win_acc.add(p_win, False, None)
            self.draw_acc.add(p_draw, True, prob_true)
            self.loss_acc.add(p_loss, False, None)
        else:  # loss
            prob_true = p_loss
            self.win_acc.add(p_win, False, None)
            self.draw_acc.add(p_draw, False, None)
            self.loss_acc.add(p_loss, True, prob_true)

    @property
    def count(self) -> int:
        """Return number of samples accumulated."""
        return self.win_acc.count

    def compute_metrics(self) -> OutcomeCalibrationMetricsV1:
        """Compute outcome calibration metrics."""
        # Compute Brier score across all outcomes
        # For multiclass: (1/n) * Σ_i Σ_c (p_ic - y_ic)^2
        n = self.count
        if n == 0:
            return OutcomeCalibrationMetricsV1(
                brier_score=0.0,
                nll=0.0,
                ece=0.0,
                histogram=self._empty_histogram(),
            )

        brier = (
            self.win_acc.compute_brier_score()
            + self.draw_acc.compute_brier_score()
            + self.loss_acc.compute_brier_score()
        ) / 3

        # ECE using win probability as the primary calibration signal
        ece = self.win_acc.compute_ece()

        # NLL from true outcome probabilities
        total_nll = self.win_acc.nll_sum + self.draw_acc.nll_sum + self.loss_acc.nll_sum
        total_count = self.win_acc.nll_count + self.draw_acc.nll_count + self.loss_acc.nll_count
        nll = total_nll / total_count if total_count > 0 else 0.0

        return OutcomeCalibrationMetricsV1(
            brier_score=round(brier, 6),
            nll=round(nll, 6),
            ece=round(ece, 6),
            histogram=self.win_acc.build_histogram(),
        )

    def _empty_histogram(self) -> CalibrationHistogramV1:
        """Create an empty histogram for zero-sample case."""
        bins = [
            CalibrationBinV1(
                bin_start=BIN_EDGES[i],
                bin_end=BIN_EDGES[i + 1],
                count=0,
                avg_confidence=None,
                empirical_accuracy=None,
            )
            for i in range(len(BIN_EDGES) - 1)
        ]
        return CalibrationHistogramV1(bin_edges=BIN_EDGES.copy(), bins=bins)


class PolicyCalibrationAccumulator:
    """Accumulates samples for policy (move distribution) calibration."""

    def __init__(self) -> None:
        self.acc = CalibrationAccumulator()

    def add(
        self,
        move_probs: list[tuple[str, float]],
        chosen_move: str,
    ) -> None:
        """Add a policy prediction.

        Args:
            move_probs: List of (move_uci, probability) tuples
            chosen_move: The actually chosen move (UCI)
        """
        # Find probability of the chosen move
        chosen_prob = 0.0
        for move, prob in move_probs:
            if move == chosen_move:
                chosen_prob = prob
                break

        # Top-1 accuracy: is the chosen move the highest probability move?
        if move_probs:
            top_move = max(move_probs, key=lambda x: x[1])
            top_prob = top_move[1]
            is_top1_correct = top_move[0] == chosen_move
        else:
            top_prob = 0.0
            is_top1_correct = False

        self.acc.add(top_prob, is_top1_correct, chosen_prob if chosen_prob > 0 else None)

    @property
    def count(self) -> int:
        """Return number of samples accumulated."""
        return self.acc.count

    def compute_metrics(self) -> PolicyCalibrationMetricsV1:
        """Compute policy calibration metrics."""
        return PolicyCalibrationMetricsV1(
            nll=round(self.acc.compute_nll(), 6),
            top1_ece=round(self.acc.compute_ece(), 6),
            histogram=self.acc.build_histogram(),
        )


def load_frozen_eval_manifest(manifest_path: Path) -> FrozenEvalManifestV1:
    """Load frozen eval manifest from file.

    Args:
        manifest_path: Path to frozen eval manifest JSON file.

    Returns:
        FrozenEvalManifestV1 instance.

    Raises:
        FileNotFoundError: If manifest file doesn't exist.
        ValueError: If manifest is invalid.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Frozen eval manifest not found: {manifest_path}")

    manifest_dict = json.loads(manifest_path.read_text(encoding="utf-8"))
    return FrozenEvalManifestV1.model_validate(manifest_dict)


def _load_shard_records(shard_path: Path) -> list[dict[str, Any]]:
    """Load all records from a JSONL shard file."""
    records = []
    with shard_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def run_calibration_evaluation(
    manifest_path: Path,
    model_dir: Path | None = None,
    policy_id: str = "baseline.uniform_random",
    outcome_head_id: str | None = None,
) -> CalibrationMetricsV1:
    """Run calibration evaluation over frozen eval manifest.

    Args:
        manifest_path: Path to frozen eval manifest.
        model_dir: Optional path to model checkpoint directory.
        policy_id: Policy identifier for baselines (default: uniform_random).
        outcome_head_id: Outcome head identifier if using learned model.

    Returns:
        CalibrationMetricsV1 artifact with per-bucket calibration metrics.
    """
    # Load manifest
    manifest = load_frozen_eval_manifest(manifest_path)
    manifest_dir = manifest_path.parent

    # Initialize accumulators per bucket
    canonical_buckets = get_canonical_skill_buckets()
    outcome_accs: dict[str, OutcomeCalibrationAccumulator] = {
        bucket: OutcomeCalibrationAccumulator() for bucket in canonical_buckets
    }
    policy_accs: dict[str, PolicyCalibrationAccumulator] = {
        bucket: PolicyCalibrationAccumulator() for bucket in canonical_buckets
    }
    samples_per_bucket: dict[str, int] = defaultdict(int)

    # Overall accumulators
    overall_outcome_acc = OutcomeCalibrationAccumulator()
    overall_policy_acc = PolicyCalibrationAccumulator()

    # Group records by shard for efficient loading
    records_by_shard: dict[str, list[dict]] = defaultdict(list)
    for record_ref in manifest.records:
        records_by_shard[record_ref.shard_id].append(
            {
                "record_key": record_ref.record_key,
                "skill_bucket_id": record_ref.skill_bucket_id,
            }
        )

    # Process each shard
    for shard_ref in [
        {"shard_id": sid, "path": f"shards/{sid}.jsonl"} for sid in records_by_shard.keys()
    ]:
        shard_id = shard_ref["shard_id"]
        shard_path = manifest_dir / shard_ref["path"]

        if not shard_path.exists():
            raise FileNotFoundError(f"Shard not found: {shard_path}")

        # Load all records from shard
        shard_records = _load_shard_records(shard_path)

        # Index by record key for lookup
        record_lookup: dict[str, dict] = {}
        for rec in shard_records:
            fen = rec.get("position", {}).get("fen", "")
            ply = rec.get("meta", {}).get("ply", 0)
            key = f"{fen}:{ply}"
            record_lookup[key] = rec

        # Process manifest records for this shard
        for ref in records_by_shard[shard_id]:
            record_key = ref["record_key"]
            skill_bucket = ref["skill_bucket_id"] or "unknown"

            if record_key not in record_lookup:
                continue  # Skip missing records

            record = record_lookup[record_key]

            # Extract data
            conditioning = record.get("conditioning", {})
            skill_bucket = conditioning.get("skillBucketId", skill_bucket)

            # Count sample
            samples_per_bucket[skill_bucket] += 1

            # Extract policy data
            policy_data = record.get("policy", {})
            top_moves = policy_data.get("topMoves", [])
            move_probs = [(m.get("uci", ""), m.get("p", 0)) for m in top_moves]

            # Extract chosen move
            chosen_move_obj = record.get("chosenMove", {})
            chosen_move = chosen_move_obj.get("uci") if chosen_move_obj else None

            # Add to policy accumulators
            if chosen_move and move_probs:
                policy_accs[skill_bucket].add(move_probs, chosen_move)
                overall_policy_acc.add(move_probs, chosen_move)

            # Extract outcome data
            game_result = record.get("meta", {}).get("gameResult")
            if game_result in ("win", "draw", "loss"):
                # Use uniform baseline probabilities (1/3 each) for baseline
                p_win = 1 / 3
                p_draw = 1 / 3
                p_loss = 1 / 3
                outcome_accs[skill_bucket].add(p_win, p_draw, p_loss, game_result)
                overall_outcome_acc.add(p_win, p_draw, p_loss, game_result)

    # Build per-bucket results
    by_elo_bucket: list[EloBucketCalibrationV1] = []
    for bucket in canonical_buckets:
        samples = samples_per_bucket.get(bucket, 0)
        outcome_metrics = None
        policy_metrics = None

        if outcome_accs[bucket].count > 0:
            outcome_metrics = outcome_accs[bucket].compute_metrics()
        if policy_accs[bucket].count > 0:
            policy_metrics = policy_accs[bucket].compute_metrics()

        by_elo_bucket.append(
            EloBucketCalibrationV1(
                elo_bucket=bucket,
                samples=samples,
                outcome_calibration=outcome_metrics,
                policy_calibration=policy_metrics,
            )
        )

    # Build overall metrics
    overall_outcome = None
    overall_policy = None
    if overall_outcome_acc.count > 0:
        overall_outcome = overall_outcome_acc.compute_metrics()
    if overall_policy_acc.count > 0:
        overall_policy = overall_policy_acc.compute_metrics()

    # Build artifact
    now = datetime.now(UTC)
    artifact_data: dict[str, Any] = {
        "version": "1.0",
        "generatedAt": now.isoformat(),
        "sourceManifestHash": manifest.manifest_hash or "",
        "policyId": policy_id,
        "outcomeHeadId": outcome_head_id,
        "overallSamples": sum(samples_per_bucket.values()),
        "byEloBucket": [b.model_dump(by_alias=True) for b in by_elo_bucket],
    }

    if overall_outcome:
        artifact_data["overallOutcomeCalibration"] = overall_outcome.model_dump(by_alias=True)
    if overall_policy:
        artifact_data["overallPolicyCalibration"] = overall_policy.model_dump(by_alias=True)

    # Compute determinism hash
    determinism_hash = "sha256:" + canonical_hash(artifact_data)

    return CalibrationMetricsV1(
        version="1.0",
        generated_at=now,
        source_manifest_hash=manifest.manifest_hash or "",
        policy_id=policy_id,
        outcome_head_id=outcome_head_id,
        overall_samples=sum(samples_per_bucket.values()),
        overall_outcome_calibration=overall_outcome,
        overall_policy_calibration=overall_policy,
        by_elo_bucket=by_elo_bucket,
        determinism_hash=determinism_hash,
    )
