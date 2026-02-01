"""Recalibration fitting runner for M25.

This module provides deterministic temperature scaling parameter fitting for
improving calibration of policy and outcome predictions.

Per M25 locked decisions:
- Grid search only (no LBFGS)
- Optimize NLL (report ECE secondarily)
- Temperature bounds: 0.25 - 3.0
- Per-Elo bucket parameters
- Offline-only (does not feed runtime logic)
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from renacechess.contracts.models import (
    CalibrationMetricsV1,
    CalibrationDeltaArtifactV1,
    CalibrationDeltaV1,
    EloBucketCalibrationV1,
    FrozenEvalManifestV1,
    OutcomeCalibrationMetricsV1,
    PolicyCalibrationMetricsV1,
    RecalibrationBucketParametersV1,
    RecalibrationParametersV1,
)
from renacechess.determinism import canonical_hash, canonical_json_dump
from renacechess.eval.calibration_runner import (
    OutcomeCalibrationAccumulator,
    PolicyCalibrationAccumulator,
    get_canonical_skill_buckets,
    load_frozen_eval_manifest,
    run_calibration_evaluation,
)

# Temperature grid for grid search (M25 locked decision)
TEMPERATURE_GRID = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0]

# Temperature bounds (M25 locked decision)
TEMPERATURE_MIN = 0.25
TEMPERATURE_MAX = 3.0


def apply_temperature_scaling_to_probs(probs: list[float], temperature: float) -> list[float]:
    """Apply temperature scaling to probabilities.

    Converts probabilities to logits, applies temperature, then converts back.

    Args:
        probs: List of probabilities (should sum to ~1.0)
        temperature: Temperature parameter (> 0)

    Returns:
        List of temperature-scaled probabilities (renormalized to sum to 1.0)
    """
    if not probs or temperature <= 0:
        return probs

    # Convert to logits (with numerical stability)
    logits = []
    for p in probs:
        if p <= 0:
            logits.append(-1e10)  # Very negative for zero probability
        else:
            logits.append(math.log(p))

    # Apply temperature scaling: logits_scaled = logits / temperature
    scaled_logits = [logit / temperature for logit in logits]

    # Convert back to probabilities via softmax
    # Numerical stability: subtract max before exp
    max_logit = max(scaled_logits)
    exp_logits = [math.exp(logit - max_logit) for logit in scaled_logits]
    sum_exp = sum(exp_logits)

    if sum_exp == 0:
        # Fallback to uniform
        return [1.0 / len(probs)] * len(probs)

    scaled_probs = [exp / sum_exp for exp in exp_logits]

    # Renormalize to ensure sum = 1.0
    total = sum(scaled_probs)
    if total > 0:
        scaled_probs = [p / total for p in scaled_probs]

    return scaled_probs


def _load_shard_records(shard_path: Path) -> list[dict[str, Any]]:
    """Load all records from a JSONL shard file."""
    records = []
    with shard_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _collect_predictions_for_fitting(
    manifest_path: Path,
    policy_id: str = "baseline.uniform_random",
    outcome_head_id: str | None = None,
) -> tuple[
    dict[str, list[tuple[list[tuple[str, float]], str]]],  # policy: bucket -> [(move_probs, chosen_move)]
    dict[str, list[tuple[float, float, float, Literal["win", "draw", "loss"]]]],  # outcome: bucket -> [(p_win, p_draw, p_loss, actual)]
]:
    """Collect raw predictions from baseline models for temperature fitting.

    Args:
        manifest_path: Path to frozen eval manifest
        policy_id: Policy identifier
        outcome_head_id: Outcome head identifier (None for baselines)

    Returns:
        Tuple of (policy_predictions, outcome_predictions) dictionaries keyed by bucket
    """
    manifest = load_frozen_eval_manifest(manifest_path)
    manifest_dir = manifest_path.parent

    canonical_buckets = get_canonical_skill_buckets()
    policy_predictions: dict[str, list[tuple[list[tuple[str, float]], str]]] = {
        bucket: [] for bucket in canonical_buckets
    }
    outcome_predictions: dict[str, list[tuple[float, float, float, Literal["win", "draw", "loss"]]]] = {
        bucket: [] for bucket in canonical_buckets
    }

    # Group records by shard
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

        shard_records = _load_shard_records(shard_path)
        record_lookup: dict[str, dict] = {}
        for rec in shard_records:
            fen = rec.get("position", {}).get("fen", "")
            ply = rec.get("meta", {}).get("ply", 0)
            key = f"{fen}:{ply}"
            record_lookup[key] = rec

        for ref in records_by_shard[shard_id]:
            record_key = ref["record_key"]
            skill_bucket = ref["skill_bucket_id"] or "unknown"

            if record_key not in record_lookup:
                continue

            record = record_lookup[record_key]
            conditioning = record.get("conditioning", {})
            skill_bucket = conditioning.get("skillBucketId", skill_bucket)

            # Extract policy data
            policy_data = record.get("policy", {})
            top_moves = policy_data.get("topMoves", [])
            move_probs = [(m.get("uci", ""), m.get("p", 0)) for m in top_moves]
            chosen_move_obj = record.get("chosenMove", {})
            chosen_move = chosen_move_obj.get("uci") if chosen_move_obj else None

            if chosen_move and move_probs:
                policy_predictions[skill_bucket].append((move_probs, chosen_move))

            # Extract outcome data (use uniform baseline for M25)
            game_result = record.get("meta", {}).get("gameResult")
            if game_result in ("win", "draw", "loss"):
                p_win = 1 / 3
                p_draw = 1 / 3
                p_loss = 1 / 3
                outcome_predictions[skill_bucket].append((p_win, p_draw, p_loss, game_result))

    return policy_predictions, outcome_predictions


def _fit_temperature_for_policy(
    predictions: list[tuple[list[tuple[str, float]], str]], temperature_grid: list[float]
) -> float:
    """Fit temperature for policy predictions using grid search (NLL optimization).

    Args:
        predictions: List of (move_probs, chosen_move) tuples
        temperature_grid: List of temperature values to try

    Returns:
        Best temperature (minimizes NLL)
    """
    if not predictions:
        return 1.0  # Default temperature

    best_temp = 1.0
    best_nll = float("inf")

    for temp in temperature_grid:
        if temp < TEMPERATURE_MIN or temp > TEMPERATURE_MAX:
            continue

        nll_sum = 0.0
        nll_count = 0

        for move_probs, chosen_move in predictions:
            # Extract probabilities
            probs = [p for _, p in move_probs]
            if not probs:
                continue

            # Apply temperature scaling
            scaled_probs = apply_temperature_scaling_to_probs(probs, temp)

            # Find probability of chosen move
            chosen_prob = 0.0
            for i, (move, _) in enumerate(move_probs):
                if move == chosen_move:
                    if i < len(scaled_probs):
                        chosen_prob = scaled_probs[i]
                    break

            # Compute NLL contribution
            if chosen_prob > 0:
                nll_sum += -math.log(chosen_prob)
                nll_count += 1

        avg_nll = nll_sum / nll_count if nll_count > 0 else float("inf")

        if avg_nll < best_nll:
            best_nll = avg_nll
            best_temp = temp

    return best_temp


def _fit_temperature_for_outcome(
    predictions: list[tuple[float, float, float, Literal["win", "draw", "loss"]]],
    temperature_grid: list[float],
) -> float:
    """Fit temperature for outcome predictions using grid search (NLL optimization).

    Args:
        predictions: List of (p_win, p_draw, p_loss, actual_outcome) tuples
        temperature_grid: List of temperature values to try

    Returns:
        Best temperature (minimizes NLL)
    """
    if not predictions:
        return 1.0  # Default temperature

    best_temp = 1.0
    best_nll = float("inf")

    for temp in temperature_grid:
        if temp < TEMPERATURE_MIN or temp > TEMPERATURE_MAX:
            continue

        nll_sum = 0.0
        nll_count = 0

        for p_win, p_draw, p_loss, actual_outcome in predictions:
            # Apply temperature scaling to W/D/L probabilities
            probs = [p_win, p_draw, p_loss]
            scaled_probs = apply_temperature_scaling_to_probs(probs, temp)

            # Get probability of actual outcome
            if actual_outcome == "win":
                prob_true = scaled_probs[0]
            elif actual_outcome == "draw":
                prob_true = scaled_probs[1]
            else:  # loss
                prob_true = scaled_probs[2]

            # Compute NLL contribution
            if prob_true > 0:
                nll_sum += -math.log(prob_true)
                nll_count += 1

        avg_nll = nll_sum / nll_count if nll_count > 0 else float("inf")

        if avg_nll < best_nll:
            best_nll = avg_nll
            best_temp = temp

    return best_temp


def fit_recalibration_parameters(
    manifest_path: Path,
    calibration_metrics: CalibrationMetricsV1,
    policy_id: str = "baseline.uniform_random",
    outcome_head_id: str | None = None,
) -> RecalibrationParametersV1:
    """Fit recalibration parameters using grid search (M25).

    Args:
        manifest_path: Path to frozen eval manifest
        calibration_metrics: CalibrationMetricsV1 artifact (before recalibration)
        policy_id: Policy identifier
        outcome_head_id: Outcome head identifier (None for baselines)

    Returns:
        RecalibrationParametersV1 artifact with fitted temperatures per bucket
    """
    # Collect predictions for fitting
    policy_preds, outcome_preds = _collect_predictions_for_fitting(
        manifest_path, policy_id, outcome_head_id
    )

    canonical_buckets = get_canonical_skill_buckets()
    by_elo_bucket: list[RecalibrationBucketParametersV1] = []

    # Fit per bucket
    for bucket in canonical_buckets:
        policy_temp = _fit_temperature_for_policy(policy_preds[bucket], TEMPERATURE_GRID)
        outcome_temp = _fit_temperature_for_outcome(outcome_preds[bucket], TEMPERATURE_GRID)

        by_elo_bucket.append(
            RecalibrationBucketParametersV1(
                elo_bucket=bucket,
                outcome_temperature=round(outcome_temp, 6),
                policy_temperature=round(policy_temp, 6),
                fit_method="grid_search",
                fit_metric="nll",
            )
        )

    # Build artifact
    now = datetime.now(UTC)
    artifact_data: dict[str, Any] = {
        "version": "1.0",
        "generatedAt": now.isoformat(),
        "sourceCalibrationMetricsHash": calibration_metrics.determinism_hash,
        "sourceManifestHash": calibration_metrics.source_manifest_hash,
        "policyId": policy_id,
        "outcomeHeadId": outcome_head_id,
        "byEloBucket": [b.model_dump(by_alias=True) for b in by_elo_bucket],
    }

    determinism_hash = "sha256:" + canonical_hash(artifact_data)

    return RecalibrationParametersV1(
        version="1.0",
        generated_at=now,
        source_calibration_metrics_hash=calibration_metrics.determinism_hash,
        source_manifest_hash=calibration_metrics.source_manifest_hash,
        policy_id=policy_id,
        outcome_head_id=outcome_head_id,
        by_elo_bucket=by_elo_bucket,
        determinism_hash=determinism_hash,
    )


def compute_calibration_delta(
    metrics_before: CalibrationMetricsV1,
    metrics_after: CalibrationMetricsV1,
    recalibration_params: RecalibrationParametersV1,
) -> CalibrationDeltaArtifactV1:
    """Compute before/after calibration delta (M25).

    Args:
        metrics_before: CalibrationMetricsV1 before recalibration
        metrics_after: CalibrationMetricsV1 after recalibration
        recalibration_params: RecalibrationParametersV1 used for recalibration

    Returns:
        CalibrationDeltaArtifactV1 with per-bucket, per-metric deltas
    """
    canonical_buckets = get_canonical_skill_buckets()
    by_elo_bucket: list[list[CalibrationDeltaV1]] = []

    # Build lookup for before/after metrics by bucket
    before_by_bucket: dict[str, Any] = {}
    after_by_bucket: dict[str, Any] = {}

    for bucket_metrics in metrics_before.by_elo_bucket:
        before_by_bucket[bucket_metrics.elo_bucket] = bucket_metrics

    for bucket_metrics in metrics_after.by_elo_bucket:
        after_by_bucket[bucket_metrics.elo_bucket] = bucket_metrics

    # Compute deltas per bucket
    for bucket in canonical_buckets:
        before = before_by_bucket.get(bucket)
        after = after_by_bucket.get(bucket)

        if not before or not after:
            continue

        deltas: list[CalibrationDeltaV1] = []

        # Outcome metrics
        if before.outcome_calibration and after.outcome_calibration:
            # ECE
            before_ece = before.outcome_calibration.ece
            after_ece = after.outcome_calibration.ece
            delta_ece = after_ece - before_ece
            deltas.append(
                CalibrationDeltaV1(
                    elo_bucket=bucket,
                    metric="outcome_ece",
                    before=before_ece,
                    after=after_ece,
                    delta=delta_ece,
                    improved=delta_ece < 0,
                )
            )

            # NLL
            before_nll = before.outcome_calibration.nll
            after_nll = after.outcome_calibration.nll
            delta_nll = after_nll - before_nll
            deltas.append(
                CalibrationDeltaV1(
                    elo_bucket=bucket,
                    metric="outcome_nll",
                    before=before_nll,
                    after=after_nll,
                    delta=delta_nll,
                    improved=delta_nll < 0,
                )
            )

            # Brier
            before_brier = before.outcome_calibration.brier_score
            after_brier = after.outcome_calibration.brier_score
            delta_brier = after_brier - before_brier
            deltas.append(
                CalibrationDeltaV1(
                    elo_bucket=bucket,
                    metric="outcome_brier",
                    before=before_brier,
                    after=after_brier,
                    delta=delta_brier,
                    improved=delta_brier < 0,
                )
            )

        # Policy metrics
        if before.policy_calibration and after.policy_calibration:
            # NLL
            before_nll = before.policy_calibration.nll
            after_nll = after.policy_calibration.nll
            delta_nll = after_nll - before_nll
            deltas.append(
                CalibrationDeltaV1(
                    elo_bucket=bucket,
                    metric="policy_nll",
                    before=before_nll,
                    after=after_nll,
                    delta=delta_nll,
                    improved=delta_nll < 0,
                )
            )

            # Top-1 ECE
            before_ece = before.policy_calibration.top1_ece
            after_ece = after.policy_calibration.top1_ece
            delta_ece = after_ece - before_ece
            deltas.append(
                CalibrationDeltaV1(
                    elo_bucket=bucket,
                    metric="policy_top1_ece",
                    before=before_ece,
                    after=after_ece,
                    delta=delta_ece,
                    improved=delta_ece < 0,
                )
            )

        if deltas:
            by_elo_bucket.append(deltas)

    # Build artifact
    now = datetime.now(UTC)
    artifact_data: dict[str, Any] = {
        "version": "1.0",
        "generatedAt": now.isoformat(),
        "sourceRecalibrationParametersHash": recalibration_params.determinism_hash,
        "sourceCalibrationMetricsBeforeHash": metrics_before.determinism_hash,
        "sourceCalibrationMetricsAfterHash": metrics_after.determinism_hash,
        "byEloBucket": [[d.model_dump(by_alias=True) for d in deltas] for deltas in by_elo_bucket],
    }

    determinism_hash = "sha256:" + canonical_hash(artifact_data)

    return CalibrationDeltaArtifactV1(
        version="1.0",
        generated_at=now,
        source_recalibration_parameters_hash=recalibration_params.determinism_hash,
        source_calibration_metrics_before_hash=metrics_before.determinism_hash,
        source_calibration_metrics_after_hash=metrics_after.determinism_hash,
        by_elo_bucket=by_elo_bucket,
        determinism_hash=determinism_hash,
    )


def run_calibration_evaluation_with_recalibration(
    manifest_path: Path,
    recalibration_params: RecalibrationParametersV1,
    model_dir: Path | None = None,
    policy_id: str = "baseline.uniform_random",
    outcome_head_id: str | None = None,
) -> CalibrationMetricsV1:
    """Run calibration evaluation with recalibration parameters applied (M25).

    This function re-runs calibration evaluation but applies temperature scaling
    to predictions according to the fitted recalibration parameters.

    Args:
        manifest_path: Path to frozen eval manifest
        recalibration_params: RecalibrationParametersV1 with fitted temperatures
        model_dir: Optional path to model checkpoint directory
        policy_id: Policy identifier
        outcome_head_id: Outcome head identifier (None for baselines)

    Returns:
        CalibrationMetricsV1 artifact (after recalibration)
    """
    # Build lookup for temperatures by bucket
    temp_by_bucket: dict[str, tuple[float, float]] = {}
    for bucket_params in recalibration_params.by_elo_bucket:
        temp_by_bucket[bucket_params.elo_bucket] = (
            bucket_params.outcome_temperature,
            bucket_params.policy_temperature,
        )

    # Collect predictions and apply temperature scaling
    policy_preds, outcome_preds = _collect_predictions_for_fitting(
        manifest_path, policy_id, outcome_head_id
    )

    canonical_buckets = get_canonical_skill_buckets()
    outcome_accs: dict[str, OutcomeCalibrationAccumulator] = {
        bucket: OutcomeCalibrationAccumulator() for bucket in canonical_buckets
    }
    policy_accs: dict[str, PolicyCalibrationAccumulator] = {
        bucket: PolicyCalibrationAccumulator() for bucket in canonical_buckets
    }

    # Apply temperature scaling and accumulate
    for bucket in canonical_buckets:
        outcome_temp, policy_temp = temp_by_bucket.get(bucket, (1.0, 1.0))

        # Policy predictions
        for move_probs, chosen_move in policy_preds[bucket]:
            probs = [p for _, p in move_probs]
            scaled_probs = apply_temperature_scaling_to_probs(probs, policy_temp)
            scaled_move_probs = [(move, scaled_probs[i] if i < len(scaled_probs) else 0.0) for i, (move, _) in enumerate(move_probs)]
            policy_accs[bucket].add(scaled_move_probs, chosen_move)

        # Outcome predictions
        for p_win, p_draw, p_loss, actual_outcome in outcome_preds[bucket]:
            probs = [p_win, p_draw, p_loss]
            scaled_probs = apply_temperature_scaling_to_probs(probs, outcome_temp)
            outcome_accs[bucket].add(scaled_probs[0], scaled_probs[1], scaled_probs[2], actual_outcome)

    # Build CalibrationMetricsV1 (reusing structure from calibration_runner)
    manifest = load_frozen_eval_manifest(manifest_path)
    by_elo_bucket: list[EloBucketCalibrationV1] = []
    samples_per_bucket: dict[str, int] = {
        bucket: len(policy_preds[bucket]) for bucket in canonical_buckets
    }

    for bucket in canonical_buckets:
        outcome_metrics = None
        policy_metrics = None

        if outcome_accs[bucket].count > 0:
            outcome_metrics = outcome_accs[bucket].compute_metrics()
        if policy_accs[bucket].count > 0:
            policy_metrics = policy_accs[bucket].compute_metrics()

        by_elo_bucket.append(
            EloBucketCalibrationV1(
                elo_bucket=bucket,
                samples=samples_per_bucket.get(bucket, 0),
                outcome_calibration=outcome_metrics,
                policy_calibration=policy_metrics,
            )
        )

    # Overall metrics (aggregate across buckets)
    overall_outcome_acc = OutcomeCalibrationAccumulator()
    overall_policy_acc = PolicyCalibrationAccumulator()

    for bucket in canonical_buckets:
        outcome_temp, policy_temp = temp_by_bucket.get(bucket, (1.0, 1.0))

        for move_probs, chosen_move in policy_preds[bucket]:
            probs = [p for _, p in move_probs]
            scaled_probs = apply_temperature_scaling_to_probs(probs, policy_temp)
            scaled_move_probs = [(move, scaled_probs[i] if i < len(scaled_probs) else 0.0) for i, (move, _) in enumerate(move_probs)]
            overall_policy_acc.add(scaled_move_probs, chosen_move)

        for p_win, p_draw, p_loss, actual_outcome in outcome_preds[bucket]:
            probs = [p_win, p_draw, p_loss]
            scaled_probs = apply_temperature_scaling_to_probs(probs, outcome_temp)
            overall_outcome_acc.add(scaled_probs[0], scaled_probs[1], scaled_probs[2], actual_outcome)

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


def load_calibration_metrics(metrics_path: Path) -> CalibrationMetricsV1:
    """Load CalibrationMetricsV1 from JSON file.

    Args:
        metrics_path: Path to calibration metrics JSON file.

    Returns:
        CalibrationMetricsV1 instance.

    Raises:
        FileNotFoundError: If metrics file doesn't exist.
        ValueError: If metrics are invalid.
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Calibration metrics not found: {metrics_path}")

    metrics_dict = json.loads(metrics_path.read_text(encoding="utf-8"))
    return CalibrationMetricsV1.model_validate(metrics_dict)


def save_recalibration_parameters(params: RecalibrationParametersV1, out_path: Path) -> None:
    """Save RecalibrationParametersV1 to JSON file.

    Args:
        params: RecalibrationParametersV1 instance.
        out_path: Output file path.
    """
    out_path.write_text(canonical_json_dump(params.model_dump(by_alias=True)), encoding="utf-8")


def load_recalibration_parameters(params_path: Path) -> RecalibrationParametersV1:
    """Load RecalibrationParametersV1 from JSON file.

    Args:
        params_path: Path to recalibration parameters JSON file.

    Returns:
        RecalibrationParametersV1 instance.

    Raises:
        FileNotFoundError: If parameters file doesn't exist.
        ValueError: If parameters are invalid.
    """
    if not params_path.exists():
        raise FileNotFoundError(f"Recalibration parameters not found: {params_path}")

    params_dict = json.loads(params_path.read_text(encoding="utf-8"))
    return RecalibrationParametersV1.model_validate(params_dict)


def save_calibration_delta(delta: CalibrationDeltaArtifactV1, out_path: Path) -> None:
    """Save CalibrationDeltaArtifactV1 to JSON file.

    Args:
        delta: CalibrationDeltaArtifactV1 instance.
        out_path: Output file path.
    """
    out_path.write_text(canonical_json_dump(delta.model_dump(by_alias=True)), encoding="utf-8")

