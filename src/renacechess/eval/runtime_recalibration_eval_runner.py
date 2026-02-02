"""Runtime recalibration evaluation runner for M27.

This module provides paired evaluation comparing baseline (gate disabled)
vs recalibrated (gate enabled) predictions.

Per M27 locked decisions:
- Use existing frozen eval fixture (tests/fixtures/frozen_eval/)
- Reuse M24 calibration infrastructure for calibration metrics
- Add policy delta metrics: entropy delta, top-k stability, rank flip rate
- Time pressure stratification only if present in dataset
- Self-contained CI job (no artifact downloads)
- Deterministic artifacts with canonical hashes
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from renacechess.contracts.models import (
    BucketDeltaV1,
    MetricsDeltaV1,
    RecalibrationGateV1,
    RecalibrationParametersV1,
    RuntimeCalibrationSnapshotV1,
    RuntimeRecalibrationDeltaV1,
    RuntimeRecalibrationReportV1,
)
from renacechess.determinism import canonical_hash, canonical_json_dump
from renacechess.eval.calibration_runner import (
    CalibrationAccumulator,
    get_canonical_skill_buckets,
    load_frozen_eval_manifest,
)
from renacechess.eval.recalibration_runner import (
    apply_temperature_scaling_to_probs,
    load_recalibration_parameters,
)
from renacechess.eval.runtime_recalibration import load_recalibration_gate


def _load_shard_records(shard_path: Path) -> list[dict[str, Any]]:
    """Load all records from a JSONL shard file."""
    records = []
    with shard_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


class RuntimeEvalAccumulator:
    """Accumulates metrics for runtime recalibration evaluation.

    Tracks calibration metrics plus policy-specific stability metrics.
    """

    def __init__(self) -> None:
        # Calibration accumulators
        self.outcome_calibration = CalibrationAccumulator()
        self.policy_calibration = CalibrationAccumulator()

        # Entropy tracking
        self.entropy_sum: float = 0.0
        self.entropy_count: int = 0

        # Stability tracking
        self.positions_evaluated: int = 0

    def add_outcome(
        self,
        p_win: float,
        p_draw: float,
        p_loss: float,
        actual: Literal["win", "draw", "loss"],
    ) -> None:
        """Add outcome prediction for calibration computation."""
        # Map actual to probability for NLL
        if actual == "win":
            prob_for_nll = p_win
            correct = p_win == max(p_win, p_draw, p_loss)
        elif actual == "draw":
            prob_for_nll = p_draw
            correct = p_draw == max(p_win, p_draw, p_loss)
        else:
            prob_for_nll = p_loss
            correct = p_loss == max(p_win, p_draw, p_loss)

        # Use max confidence as the top-1 prediction
        max_prob = max(p_win, p_draw, p_loss)
        self.outcome_calibration.add(max_prob, correct, prob_for_nll)

    def add_policy(
        self,
        top_moves: list[tuple[str, float]],
        chosen_move: str,
        entropy: float,
    ) -> None:
        """Add policy prediction for calibration computation."""
        if not top_moves:
            return

        # Top-1 confidence and correctness
        top1_move = top_moves[0][0]
        top1_prob = top_moves[0][1]
        correct = top1_move == chosen_move

        # Probability of chosen move for NLL
        prob_for_chosen = 0.0
        for move, prob in top_moves:
            if move == chosen_move:
                prob_for_chosen = prob
                break

        self.policy_calibration.add(top1_prob, correct, prob_for_chosen)

        # Track entropy
        self.entropy_sum += entropy
        self.entropy_count += 1
        self.positions_evaluated += 1

    def get_mean_entropy(self) -> float:
        """Return mean policy entropy."""
        if self.entropy_count == 0:
            return 0.0
        return self.entropy_sum / self.entropy_count

    def build_snapshot(self) -> RuntimeCalibrationSnapshotV1:
        """Build calibration snapshot from accumulated metrics."""
        return RuntimeCalibrationSnapshotV1(
            outcome_ece=self.outcome_calibration.compute_ece(),
            outcome_nll=self.outcome_calibration.compute_nll(),
            outcome_brier=self.outcome_calibration.compute_brier_score(),
            policy_nll=self.policy_calibration.compute_nll(),
            policy_top1_ece=self.policy_calibration.compute_ece(),
            mean_entropy=self.get_mean_entropy(),
        )


class StabilityTracker:
    """Tracks top-k stability between baseline and recalibrated predictions."""

    def __init__(self) -> None:
        self.top1_unchanged: int = 0
        self.top3_unchanged: int = 0
        self.total: int = 0

    def add(
        self,
        baseline_moves: list[tuple[str, float]],
        recalibrated_moves: list[tuple[str, float]],
    ) -> None:
        """Compare baseline and recalibrated top moves."""
        if not baseline_moves or not recalibrated_moves:
            return

        self.total += 1

        # Top-1 stability
        baseline_top1 = baseline_moves[0][0]
        recal_top1 = recalibrated_moves[0][0]
        if baseline_top1 == recal_top1:
            self.top1_unchanged += 1

        # Top-3 stability (set comparison)
        baseline_top3 = {m[0] for m in baseline_moves[:3]}
        recal_top3 = {m[0] for m in recalibrated_moves[:3]}
        if baseline_top3 == recal_top3:
            self.top3_unchanged += 1

    def get_top1_stability(self) -> float:
        """Fraction of positions where top-1 unchanged."""
        if self.total == 0:
            return 1.0
        return self.top1_unchanged / self.total

    def get_top3_stability(self) -> float:
        """Fraction of positions where top-3 unchanged."""
        if self.total == 0:
            return 1.0
        return self.top3_unchanged / self.total

    def get_top1_flip_rate(self) -> float:
        """Fraction of positions where top-1 changed."""
        return 1.0 - self.get_top1_stability()


def _compute_entropy(probs: list[float]) -> float:
    """Compute entropy of probability distribution."""
    entropy = 0.0
    for p in probs:
        if p > 0:
            entropy -= p * math.log(p)
    return entropy


def _apply_recalibration_to_policy(
    top_moves: list[tuple[str, float]],
    skill_bucket: str,
    params: RecalibrationParametersV1,
) -> list[tuple[str, float]]:
    """Apply temperature scaling to policy probabilities."""
    if not top_moves:
        return top_moves

    # Find bucket parameters
    bucket_params = None
    for bp in params.by_elo_bucket:
        if bp.elo_bucket == skill_bucket:
            bucket_params = bp
            break

    if bucket_params is None:
        return top_moves

    # Extract probabilities
    moves = [m[0] for m in top_moves]
    probs = [m[1] for m in top_moves]

    # Apply temperature scaling
    scaled_probs = apply_temperature_scaling_to_probs(probs, bucket_params.policy_temperature)

    # Rebuild list and sort by probability
    result = list(zip(moves, scaled_probs))
    result.sort(key=lambda x: x[1], reverse=True)
    return result


def _apply_recalibration_to_outcome(
    p_win: float,
    p_draw: float,
    p_loss: float,
    skill_bucket: str,
    params: RecalibrationParametersV1,
) -> tuple[float, float, float]:
    """Apply temperature scaling to outcome probabilities."""
    # Find bucket parameters
    bucket_params = None
    for bp in params.by_elo_bucket:
        if bp.elo_bucket == skill_bucket:
            bucket_params = bp
            break

    if bucket_params is None:
        return (p_win, p_draw, p_loss)

    # Apply temperature scaling
    probs = [p_win, p_draw, p_loss]
    scaled = apply_temperature_scaling_to_probs(probs, bucket_params.outcome_temperature)
    return (scaled[0], scaled[1], scaled[2])


def run_paired_evaluation(
    manifest_path: Path,
    gate: RecalibrationGateV1,
    params: RecalibrationParametersV1,
) -> tuple[
    dict[str, RuntimeEvalAccumulator],  # baseline by elo bucket
    dict[str, RuntimeEvalAccumulator],  # recalibrated by elo bucket
    dict[str, StabilityTracker],  # stability by elo bucket
    dict[str, RuntimeEvalAccumulator],  # baseline by time bucket (if present)
    dict[str, RuntimeEvalAccumulator],  # recalibrated by time bucket (if present)
    dict[str, StabilityTracker],  # stability by time bucket (if present)
    int,  # total samples
]:
    """Run paired evaluation comparing baseline vs recalibrated predictions.

    Args:
        manifest_path: Path to frozen eval manifest
        gate: RecalibrationGateV1 (should have enabled=True for recal run)
        params: RecalibrationParametersV1 with fitted temperatures

    Returns:
        Tuple of accumulators and trackers for each stratification axis
    """
    manifest = load_frozen_eval_manifest(manifest_path)
    manifest_dir = manifest_path.parent

    canonical_buckets = get_canonical_skill_buckets()

    # Initialize per-bucket accumulators
    baseline_by_elo: dict[str, RuntimeEvalAccumulator] = {
        b: RuntimeEvalAccumulator() for b in canonical_buckets
    }
    recal_by_elo: dict[str, RuntimeEvalAccumulator] = {
        b: RuntimeEvalAccumulator() for b in canonical_buckets
    }
    stability_by_elo: dict[str, StabilityTracker] = {
        b: StabilityTracker() for b in canonical_buckets
    }

    # Check if time pressure is present
    time_pressure_buckets = ["low", "normal", "trouble"]
    has_time_pressure = manifest.counts_by_time_pressure_bucket is not None

    baseline_by_time: dict[str, RuntimeEvalAccumulator] = {}
    recal_by_time: dict[str, RuntimeEvalAccumulator] = {}
    stability_by_time: dict[str, StabilityTracker] = {}

    if has_time_pressure:
        baseline_by_time = {b: RuntimeEvalAccumulator() for b in time_pressure_buckets}
        recal_by_time = {b: RuntimeEvalAccumulator() for b in time_pressure_buckets}
        stability_by_time = {b: StabilityTracker() for b in time_pressure_buckets}

    # Group records by shard
    records_by_shard: dict[str, list[dict]] = defaultdict(list)
    for record_ref in manifest.records:
        records_by_shard[record_ref.shard_id].append(
            {
                "record_key": record_ref.record_key,
                "skill_bucket_id": record_ref.skill_bucket_id,
                "time_pressure_bucket": record_ref.time_pressure_bucket,
            }
        )

    total_samples = 0

    # Process each shard
    for shard_id, record_refs in records_by_shard.items():
        shard_path = manifest_dir / "shards" / f"{shard_id}.jsonl"
        if not shard_path.exists():
            continue

        shard_records = _load_shard_records(shard_path)

        # Index by record key for lookup
        shard_by_key = {}
        for i, record in enumerate(shard_records):
            fen = record.get("position", {}).get("fen", "")
            key = f"{fen}:{i}"
            shard_by_key[key] = record

        # Process each record reference
        for ref in record_refs:
            record_key = ref["record_key"]
            skill_bucket = ref["skill_bucket_id"]
            time_bucket = ref.get("time_pressure_bucket")

            # Find record in shard
            if record_key not in shard_by_key:
                # Try to find by index
                idx = int(record_key.split(":")[-1]) if ":" in record_key else -1
                if 0 <= idx < len(shard_records):
                    record = shard_records[idx]
                else:
                    continue
            else:
                record = shard_by_key[record_key]

            total_samples += 1

            # Extract baseline predictions from fixture
            policy = record.get("policy", {})
            top_moves_raw = policy.get("topMoves", [])
            top_moves = [(m["uci"], m["p"]) for m in top_moves_raw]
            baseline_entropy = policy.get("entropy", 0.0)

            chosen_move = record.get("chosenMove", {}).get("uci", "")
            game_result = record.get("meta", {}).get("gameResult", "loss")

            # For outcome, use uniform baseline (1/3 each) since fixture doesn't have WDL
            baseline_p_win = 1.0 / 3.0
            baseline_p_draw = 1.0 / 3.0
            baseline_p_loss = 1.0 / 3.0

            # Apply recalibration
            recal_moves = _apply_recalibration_to_policy(top_moves, skill_bucket, params)
            recal_probs = [m[1] for m in recal_moves]
            recal_entropy = _compute_entropy(recal_probs)

            recal_p_win, recal_p_draw, recal_p_loss = _apply_recalibration_to_outcome(
                baseline_p_win, baseline_p_draw, baseline_p_loss, skill_bucket, params
            )

            # Accumulate baseline metrics
            if skill_bucket in baseline_by_elo:
                baseline_by_elo[skill_bucket].add_policy(top_moves, chosen_move, baseline_entropy)
                baseline_by_elo[skill_bucket].add_outcome(
                    baseline_p_win, baseline_p_draw, baseline_p_loss, game_result
                )

            # Accumulate recalibrated metrics
            if skill_bucket in recal_by_elo:
                recal_by_elo[skill_bucket].add_policy(recal_moves, chosen_move, recal_entropy)
                recal_by_elo[skill_bucket].add_outcome(
                    recal_p_win, recal_p_draw, recal_p_loss, game_result
                )

            # Track stability
            if skill_bucket in stability_by_elo:
                stability_by_elo[skill_bucket].add(top_moves, recal_moves)

            # Time pressure stratification
            if has_time_pressure and time_bucket in baseline_by_time:
                baseline_by_time[time_bucket].add_policy(top_moves, chosen_move, baseline_entropy)
                baseline_by_time[time_bucket].add_outcome(
                    baseline_p_win, baseline_p_draw, baseline_p_loss, game_result
                )
                recal_by_time[time_bucket].add_policy(recal_moves, chosen_move, recal_entropy)
                recal_by_time[time_bucket].add_outcome(
                    recal_p_win, recal_p_draw, recal_p_loss, game_result
                )
                stability_by_time[time_bucket].add(top_moves, recal_moves)

    return (
        baseline_by_elo,
        recal_by_elo,
        stability_by_elo,
        baseline_by_time,
        recal_by_time,
        stability_by_time,
        total_samples,
    )


def _compute_metrics_delta(
    baseline: RuntimeEvalAccumulator,
    recal: RuntimeEvalAccumulator,
    stability: StabilityTracker,
) -> MetricsDeltaV1:
    """Compute delta metrics between baseline and recalibrated."""
    baseline_snap = baseline.build_snapshot()
    recal_snap = recal.build_snapshot()

    return MetricsDeltaV1(
        outcome_ece_delta=recal_snap.outcome_ece - baseline_snap.outcome_ece,
        outcome_nll_delta=recal_snap.outcome_nll - baseline_snap.outcome_nll,
        outcome_brier_delta=recal_snap.outcome_brier - baseline_snap.outcome_brier,
        policy_nll_delta=recal_snap.policy_nll - baseline_snap.policy_nll,
        policy_top1_ece_delta=recal_snap.policy_top1_ece - baseline_snap.policy_top1_ece,
        entropy_delta=recal_snap.mean_entropy - baseline_snap.mean_entropy,
        top1_stability=stability.get_top1_stability(),
        top3_stability=stability.get_top3_stability(),
        top1_flip_rate=stability.get_top1_flip_rate(),
    )


def _aggregate_snapshots(
    accumulators: dict[str, RuntimeEvalAccumulator],
) -> RuntimeCalibrationSnapshotV1:
    """Aggregate calibration snapshots across all buckets."""
    # Create combined accumulator
    combined = RuntimeEvalAccumulator()

    for acc in accumulators.values():
        # Merge outcome calibration
        combined.outcome_calibration.predictions.extend(acc.outcome_calibration.predictions)
        combined.outcome_calibration.outcomes.extend(acc.outcome_calibration.outcomes)
        combined.outcome_calibration.nll_sum += acc.outcome_calibration.nll_sum
        combined.outcome_calibration.nll_count += acc.outcome_calibration.nll_count

        # Merge policy calibration
        combined.policy_calibration.predictions.extend(acc.policy_calibration.predictions)
        combined.policy_calibration.outcomes.extend(acc.policy_calibration.outcomes)
        combined.policy_calibration.nll_sum += acc.policy_calibration.nll_sum
        combined.policy_calibration.nll_count += acc.policy_calibration.nll_count

        # Merge entropy
        combined.entropy_sum += acc.entropy_sum
        combined.entropy_count += acc.entropy_count

    return combined.build_snapshot()


def _aggregate_stability(
    trackers: dict[str, StabilityTracker],
) -> StabilityTracker:
    """Aggregate stability trackers across all buckets."""
    combined = StabilityTracker()

    for tracker in trackers.values():
        combined.top1_unchanged += tracker.top1_unchanged
        combined.top3_unchanged += tracker.top3_unchanged
        combined.total += tracker.total

    return combined


def run_runtime_recalibration_evaluation(
    manifest_path: Path,
    gate_path: Path,
    params_path: Path,
    output_dir: Path,
) -> tuple[RuntimeRecalibrationReportV1, RuntimeRecalibrationDeltaV1]:
    """Run full runtime recalibration evaluation and generate artifacts.

    Args:
        manifest_path: Path to frozen eval manifest
        gate_path: Path to RecalibrationGateV1 JSON
        params_path: Path to RecalibrationParametersV1 JSON
        output_dir: Directory for output artifacts

    Returns:
        Tuple of (report, delta) artifacts
    """
    # Load inputs
    gate = load_recalibration_gate(gate_path)
    params = load_recalibration_parameters(params_path)
    manifest = load_frozen_eval_manifest(manifest_path)

    # Compute hashes for provenance
    gate_dict = gate.model_dump(by_alias=True, mode="json")
    gate_hash = f"sha256:{canonical_hash(gate_dict)}"

    params_dict = params.model_dump(by_alias=True, mode="json")
    params_hash = f"sha256:{canonical_hash(params_dict)}"

    dataset_hash = manifest.manifest_hash

    # Run paired evaluation
    (
        baseline_by_elo,
        recal_by_elo,
        stability_by_elo,
        baseline_by_time,
        recal_by_time,
        stability_by_time,
        total_samples,
    ) = run_paired_evaluation(manifest_path, gate, params)

    # Build aggregated snapshots
    baseline_snapshot = _aggregate_snapshots(baseline_by_elo)
    recal_snapshot = _aggregate_snapshots(recal_by_elo)

    # Build report
    report = RuntimeRecalibrationReportV1(
        version="1.0",
        generated_at=datetime.now(UTC),
        gate_ref=gate_hash,
        parameters_ref=params_hash,
        dataset_ref=dataset_hash,
        total_samples=total_samples,
        baseline_metrics=baseline_snapshot,
        recalibrated_metrics=recal_snapshot,
        determinism_hash="sha256:" + "0" * 64,  # Placeholder, computed after
    )

    # Compute report hash (exclude volatile fields for determinism)
    report_dict = report.model_dump(by_alias=True, mode="json")
    del report_dict["determinismHash"]  # Exclude hash from hash computation
    del report_dict["generatedAt"]  # Exclude timestamp for determinism
    report_hash = f"sha256:{canonical_hash(report_dict)}"
    report = report.model_copy(update={"determinism_hash": report_hash})

    # Build per-bucket deltas
    by_elo_bucket: list[BucketDeltaV1] = []
    for bucket_id in get_canonical_skill_buckets():
        if bucket_id in baseline_by_elo and baseline_by_elo[bucket_id].positions_evaluated > 0:
            by_elo_bucket.append(
                BucketDeltaV1(
                    bucket_id=bucket_id,
                    samples=baseline_by_elo[bucket_id].positions_evaluated,
                    metrics=_compute_metrics_delta(
                        baseline_by_elo[bucket_id],
                        recal_by_elo[bucket_id],
                        stability_by_elo[bucket_id],
                    ),
                )
            )

    # Time pressure deltas (if present)
    by_time_bucket: list[BucketDeltaV1] | None = None
    if baseline_by_time:
        by_time_bucket = []
        for bucket_id in ["low", "normal", "trouble"]:
            in_bucket = bucket_id in baseline_by_time
            has_samples = in_bucket and baseline_by_time[bucket_id].positions_evaluated > 0
            if has_samples:
                by_time_bucket.append(
                    BucketDeltaV1(
                        bucket_id=bucket_id,
                        samples=baseline_by_time[bucket_id].positions_evaluated,
                        metrics=_compute_metrics_delta(
                            baseline_by_time[bucket_id],
                            recal_by_time[bucket_id],
                            stability_by_time[bucket_id],
                        ),
                    )
                )

    # Overall delta
    overall_stability = _aggregate_stability(stability_by_elo)
    overall_baseline = RuntimeEvalAccumulator()
    overall_recal = RuntimeEvalAccumulator()

    for acc in baseline_by_elo.values():
        overall_baseline.outcome_calibration.predictions.extend(acc.outcome_calibration.predictions)
        overall_baseline.outcome_calibration.outcomes.extend(acc.outcome_calibration.outcomes)
        overall_baseline.outcome_calibration.nll_sum += acc.outcome_calibration.nll_sum
        overall_baseline.outcome_calibration.nll_count += acc.outcome_calibration.nll_count
        overall_baseline.policy_calibration.predictions.extend(acc.policy_calibration.predictions)
        overall_baseline.policy_calibration.outcomes.extend(acc.policy_calibration.outcomes)
        overall_baseline.policy_calibration.nll_sum += acc.policy_calibration.nll_sum
        overall_baseline.policy_calibration.nll_count += acc.policy_calibration.nll_count
        overall_baseline.entropy_sum += acc.entropy_sum
        overall_baseline.entropy_count += acc.entropy_count

    for acc in recal_by_elo.values():
        overall_recal.outcome_calibration.predictions.extend(acc.outcome_calibration.predictions)
        overall_recal.outcome_calibration.outcomes.extend(acc.outcome_calibration.outcomes)
        overall_recal.outcome_calibration.nll_sum += acc.outcome_calibration.nll_sum
        overall_recal.outcome_calibration.nll_count += acc.outcome_calibration.nll_count
        overall_recal.policy_calibration.predictions.extend(acc.policy_calibration.predictions)
        overall_recal.policy_calibration.outcomes.extend(acc.policy_calibration.outcomes)
        overall_recal.policy_calibration.nll_sum += acc.policy_calibration.nll_sum
        overall_recal.policy_calibration.nll_count += acc.policy_calibration.nll_count
        overall_recal.entropy_sum += acc.entropy_sum
        overall_recal.entropy_count += acc.entropy_count

    overall_delta = _compute_metrics_delta(overall_baseline, overall_recal, overall_stability)

    # Build delta artifact
    delta = RuntimeRecalibrationDeltaV1(
        version="1.0",
        generated_at=datetime.now(UTC),
        source_report_hash=report_hash,
        by_elo_bucket=by_elo_bucket,
        by_time_pressure_bucket=by_time_bucket,
        overall=overall_delta,
        determinism_hash="sha256:" + "0" * 64,  # Placeholder
    )

    # Compute delta hash (exclude volatile fields for determinism)
    delta_dict = delta.model_dump(by_alias=True, mode="json")
    del delta_dict["determinismHash"]
    del delta_dict["generatedAt"]  # Exclude timestamp for determinism
    delta_hash = f"sha256:{canonical_hash(delta_dict)}"
    delta = delta.model_copy(update={"determinism_hash": delta_hash})

    # Write artifacts
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "runtime-recalibration-report.json"
    report_path.write_text(
        canonical_json_dump(report.model_dump(by_alias=True, mode="json")).decode("utf-8"),
        encoding="utf-8",
    )

    delta_path = output_dir / "runtime-recalibration-delta.json"
    delta_path.write_text(
        canonical_json_dump(delta.model_dump(by_alias=True, mode="json")).decode("utf-8"),
        encoding="utf-8",
    )

    return report, delta
