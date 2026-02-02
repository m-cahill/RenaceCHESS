"""Evaluation runner for streaming evaluation over dataset manifests."""

import json
from pathlib import Path
from typing import Any

from renacechess.contracts.models import (
    DatasetManifestV2,
    PolicyMove,
    RecalibrationGateV1,
    RecalibrationParametersV1,
)
from renacechess.dataset.split import compute_split_assignment
from renacechess.eval.baselines import compute_policy_seed, create_policy_provider
from renacechess.eval.conditioned_metrics import ConditionedMetricsAccumulator
from renacechess.eval.metrics import MetricsAccumulator, format_fixed_decimal
from renacechess.eval.outcome_metrics import OutcomeMetricsAccumulator


def load_manifest(manifest_path: Path) -> DatasetManifestV2:
    """Load dataset manifest v2 from file.

    Args:
        manifest_path: Path to manifest.json file.

    Returns:
        DatasetManifestV2 instance.

    Raises:
        FileNotFoundError: If manifest file doesn't exist.
        ValueError: If manifest is not v2 or invalid.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    manifest_dict = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Validate schema version
    schema_version = manifest_dict.get("schemaVersion", "")
    if schema_version != "v2":
        raise ValueError(
            f"Expected manifest v2, got schema version: {schema_version}. "
            "M04 only supports v2 manifests."
        )

    return DatasetManifestV2.model_validate(manifest_dict)


def run_evaluation(
    manifest_path: Path,
    policy_id: str,
    eval_config: dict[str, Any],
    max_records: int | None = None,
    compute_accuracy: bool = False,
    top_k_values: list[int] | None = None,
    model_path: Path | None = None,
) -> dict[str, Any]:
    """Run evaluation over dataset manifest.

    Args:
        manifest_path: Path to dataset manifest v2.
        policy_id: Policy identifier (e.g., 'baseline.uniform_random').
        eval_config: Evaluation configuration dict (for hashing).
        max_records: Maximum number of records to evaluate (None = no limit).
        compute_accuracy: Whether to compute accuracy metrics (requires chosenMove labels).
        top_k_values: List of K values for top-K accuracy (e.g., [1, 3, 5]). Defaults to [1].

    Returns:
        Dictionary with evaluation results (ready for EvalReportV1 or EvalReportV2 construction).
    """
    # Load manifest
    manifest = load_manifest(manifest_path)
    manifest_dir = manifest_path.parent

    # Compute policy seed for deterministic RNG
    eval_config_hash = _compute_eval_config_hash(eval_config)
    policy_seed = compute_policy_seed(manifest.dataset_digest, policy_id, eval_config_hash)

    # Create policy provider
    policy = create_policy_provider(policy_id, seed=policy_seed, model_path=model_path)

    # Initialize accumulators with accuracy config
    top_k_vals = top_k_values if top_k_values is not None else [1]
    overall_accumulator = MetricsAccumulator(
        compute_accuracy=compute_accuracy, top_k_values=top_k_vals
    )
    split_accumulators: dict[str, MetricsAccumulator] = {
        "train": MetricsAccumulator(compute_accuracy=compute_accuracy, top_k_values=top_k_vals),
        "val": MetricsAccumulator(compute_accuracy=compute_accuracy, top_k_values=top_k_vals),
        "frozenEval": MetricsAccumulator(
            compute_accuracy=compute_accuracy, top_k_values=top_k_vals
        ),
    }

    # Track which shards belong to which splits (from manifest)
    shard_splits: dict[str, set[str]] = {}
    for split_name in ["train", "val", "frozenEval"]:
        shard_ids = getattr(manifest.split_assignments, split_name, [])
        for shard_id in shard_ids:
            if shard_id not in shard_splits:
                shard_splits[shard_id] = set()
            shard_splits[shard_id].add(split_name)

    # Process shards in order
    records_processed = 0
    for shard_ref in manifest.shard_refs:
        if max_records is not None and records_processed >= max_records:
            break

        shard_path = manifest_dir / shard_ref.path
        if not shard_path.exists():
            raise FileNotFoundError(f"Shard not found: {shard_path}")

        # Determine which splits this shard contains
        shard_split_names = shard_splits.get(shard_ref.shard_id, set())

        # Process shard line-by-line (streaming)
        with shard_path.open(encoding="utf-8") as f:
            for line in f:
                if max_records is not None and records_processed >= max_records:
                    break

                line = line.strip()
                if not line:
                    continue

                record = json.loads(line)

                # Compute split assignment for this record
                # Use FEN + ply from record if available, otherwise use record position
                fen = record.get("position", {}).get("fen", "")
                # Try to extract ply from meta if available, otherwise use 0
                ply = record.get("meta", {}).get("ply", 0)
                record_key = f"{fen}:{ply}"
                split = compute_split_assignment(record_key)

                # Predict moves
                predicted_moves = policy.predict(record)

                # Accumulate metrics
                overall_accumulator.add_record(record, predicted_moves)

                # Only accumulate per-split if this shard is assigned to that split
                if split in shard_split_names or not shard_split_names:
                    # If shard has no explicit split assignment, use computed split
                    if split in split_accumulators:
                        split_accumulators[split].add_record(record, predicted_moves)

                records_processed += 1

    # Compute final metrics
    overall_metrics = overall_accumulator.compute_metrics()
    split_metrics = {}
    for split_name, accumulator in split_accumulators.items():
        if accumulator.records_evaluated > 0:
            split_metrics[split_name] = accumulator.compute_metrics()

    # Add total record count and coverage for accuracy metrics
    if compute_accuracy:
        # Total records evaluated (may be less than dataset total if max_records is set)
        total_records_evaluated = overall_accumulator.records_evaluated
        overall_metrics["total_record_count"] = total_records_evaluated
        labeled_count = overall_metrics.get("labeled_record_count", 0)

        # Compute coverage
        if "accuracy" in overall_metrics:
            coverage = (
                (labeled_count / total_records_evaluated * 100.0)
                if total_records_evaluated > 0
                else 0.0
            )
            overall_metrics["accuracy"]["coverage"] = format_fixed_decimal(coverage)

        # Add total_record_count to split metrics too
        for split_name, split_dict in split_metrics.items():
            split_dict["total_record_count"] = split_accumulators[split_name].records_evaluated
            split_labeled = split_dict.get("labeled_record_count", 0)
            if "accuracy" in split_dict:
                split_coverage = (
                    (split_labeled / split_dict["total_record_count"] * 100.0)
                    if split_dict["total_record_count"] > 0
                    else 0.0
                )
                split_dict["accuracy"]["coverage"] = format_fixed_decimal(split_coverage)

    result: dict[str, Any] = {
        "dataset_digest": manifest.dataset_digest,
        "assembly_config_hash": manifest.assembly_config_hash,
        "policy_id": policy_id,
        "eval_config_hash": eval_config_hash,
        "overall_metrics": overall_metrics,
        "split_metrics": split_metrics,
    }

    # Add total record count for v2 reports (if accuracy is computed)
    if compute_accuracy:
        result["total_record_count"] = overall_accumulator.records_evaluated

    return result


def run_conditioned_evaluation(
    manifest_path: Path,
    policy_id: str,
    eval_config: dict[str, Any],
    max_records: int | None = None,
    compute_accuracy: bool = False,
    top_k_values: list[int] | None = None,
    frozen_eval_manifest_hash: str | None = None,
    model_path: Path | None = None,
    outcome_head_path: Path | None = None,
    recalibration_gate: RecalibrationGateV1 | None = None,
    recalibration_params: RecalibrationParametersV1 | None = None,
) -> dict[str, Any]:
    """Run evaluation with conditioned metrics (M06) and optional outcome head (M09).

    Args:
        manifest_path: Path to dataset manifest v2.
        policy_id: Policy identifier (e.g., 'baseline.uniform_random').
        eval_config: Evaluation configuration dict (for hashing).
        max_records: Maximum number of records to evaluate (None = no limit).
        compute_accuracy: Whether to compute accuracy metrics (requires chosenMove labels).
        top_k_values: List of K values for top-K accuracy (e.g., [1, 3, 5]). Defaults to [1].
        frozen_eval_manifest_hash: SHA-256 hash of frozen eval manifest (if frozen eval).
        model_path: Path to trained policy model (for learned.v1).
        outcome_head_path: Path to outcome head model directory (M09, optional).
        recalibration_gate: Optional RecalibrationGateV1 artifact (M26).
            If None or enabled=False, no recalibration applied.
        recalibration_params: Optional RecalibrationParametersV1 artifact (M26).
            Required if gate.enabled=True.

    Returns:
        Dictionary with evaluation results (ready for EvalReportV3/V4/V5 construction).
    """
    # Load manifest
    manifest = load_manifest(manifest_path)
    manifest_dir = manifest_path.parent

    # Compute policy seed for deterministic RNG
    eval_config_hash = _compute_eval_config_hash(eval_config)
    policy_seed = compute_policy_seed(manifest.dataset_digest, policy_id, eval_config_hash)

    # Create policy provider
    policy = create_policy_provider(policy_id, seed=policy_seed, model_path=model_path)

    # Load outcome head if provided (M09)
    outcome_head = None
    if outcome_head_path is not None:
        from renacechess.eval.outcome_head import LearnedOutcomeHeadV1

        model_file = outcome_head_path / "outcome_head_v1.pt"
        metadata_file = outcome_head_path / "outcome_head_v1_metadata.json"
        if not model_file.exists() or not metadata_file.exists():
            raise FileNotFoundError(
                f"Outcome head files not found in {outcome_head_path}. "
                "Expected: outcome_head_v1.pt and outcome_head_v1_metadata.json"
            )
        outcome_head = LearnedOutcomeHeadV1(model_file, metadata_file)

    # Initialize conditioned metrics accumulator
    top_k_vals = top_k_values if top_k_values is not None else [1]
    accumulator = ConditionedMetricsAccumulator(
        compute_accuracy=compute_accuracy, top_k_values=top_k_vals
    )

    # Initialize outcome metrics accumulators (M09)
    outcome_accumulator = OutcomeMetricsAccumulator() if outcome_head else None
    outcome_accumulators_by_skill: dict[str, OutcomeMetricsAccumulator] = {}
    outcome_accumulators_by_time_control: dict[str, OutcomeMetricsAccumulator] = {}
    outcome_accumulators_by_time_pressure: dict[str, OutcomeMetricsAccumulator] = {}

    # Process shards in order
    records_processed = 0
    for shard_ref in manifest.shard_refs:
        if max_records is not None and records_processed >= max_records:
            break

        shard_path = manifest_dir / shard_ref.path
        if not shard_path.exists():
            raise FileNotFoundError(f"Shard not found: {shard_path}")

        # Process shard line-by-line (streaming)
        with shard_path.open(encoding="utf-8") as f:
            for line in f:
                if max_records is not None and records_processed >= max_records:
                    break

                line = line.strip()
                if not line:
                    continue

                record = json.loads(line)

                # Extract conditioning metadata
                conditioning = record.get("conditioning", {})
                skill_bucket_id = conditioning.get("skillBucketId")
                time_control_class = conditioning.get("timeControlClass")
                time_pressure_bucket = conditioning.get("timePressureBucket")

                # Extract position and policy data
                position = record.get("position", {})
                legal_moves = position.get("legalMoves", [])

                # Extract chosen move (label)
                chosen_move_obj = record.get("chosenMove")
                chosen_move = chosen_move_obj.get("uci") if chosen_move_obj else None

                # Extract policy output
                predicted_moves = policy.predict(record)

                # Apply recalibration if gate is enabled (M26)
                from renacechess.eval.recalibration_integration import (
                    apply_runtime_recalibration_to_policy_moves,
                )

                predicted_moves, _recal_applied = (
                    apply_runtime_recalibration_to_policy_moves(
                        predicted_moves,
                        skill_bucket_id,
                        recalibration_gate,
                        recalibration_params,
                    )
                )

                policy_output = predicted_moves[0].uci if predicted_moves else None

                # Extract policy metrics
                policy_data = record.get("policy", {})
                policy_entropy = policy_data.get("entropy")
                policy_top_gap = policy_data.get("topGap")

                # Add record to accumulator
                accumulator.add_record(
                    policy_output=policy_output,
                    legal_moves=legal_moves,
                    chosen_move=chosen_move,
                    policy_entropy=policy_entropy,
                    policy_top_gap=policy_top_gap,
                    skill_bucket_id=skill_bucket_id,
                    time_control_class=time_control_class,
                    time_pressure_bucket=time_pressure_bucket,
                )

                # Compute outcome metrics if outcome head is provided (M09)
                if outcome_head is not None and outcome_accumulator is not None:
                    # Get game result from record (from mover's perspective)
                    game_result = _get_game_result_from_record(record)
                    if game_result is not None:
                        # Predict W/D/L
                        predicted_wdl = outcome_head.predict(record)

                        # Apply recalibration if gate is enabled (M26)
                        from renacechess.eval.recalibration_integration import (
                            apply_runtime_recalibration_to_outcome,
                        )

                        (scaled_w, scaled_d, scaled_l), _recal_applied = (
                            apply_runtime_recalibration_to_outcome(
                                predicted_wdl["w"],
                                predicted_wdl["d"],
                                predicted_wdl["l"],
                                skill_bucket_id,
                                recalibration_gate,
                                recalibration_params,
                            )
                        )
                        predicted_wdl = {"w": scaled_w, "d": scaled_d, "l": scaled_l}

                        # Add to overall accumulator
                        outcome_accumulator.add_prediction(predicted_wdl, game_result)

                        # Add to stratified accumulators
                        if skill_bucket_id:
                            if skill_bucket_id not in outcome_accumulators_by_skill:
                                outcome_accumulators_by_skill[skill_bucket_id] = (
                                    OutcomeMetricsAccumulator()
                                )
                            outcome_accumulators_by_skill[skill_bucket_id].add_prediction(
                                predicted_wdl, game_result
                            )

                        if time_control_class:
                            if time_control_class not in outcome_accumulators_by_time_control:
                                outcome_accumulators_by_time_control[time_control_class] = (
                                    OutcomeMetricsAccumulator()
                                )
                            outcome_accumulators_by_time_control[time_control_class].add_prediction(
                                predicted_wdl, game_result
                            )

                        if time_pressure_bucket:
                            if time_pressure_bucket not in outcome_accumulators_by_time_pressure:
                                outcome_accumulators_by_time_pressure[time_pressure_bucket] = (
                                    OutcomeMetricsAccumulator()
                                )
                            outcome_accumulators_by_time_pressure[
                                time_pressure_bucket
                            ].add_prediction(predicted_wdl, game_result)

                records_processed += 1

    # Build metrics
    overall_metrics = accumulator.build_metrics()
    stratified_metrics = accumulator.build_stratified_metrics()

    result: dict[str, Any] = {
        "dataset_digest": manifest.dataset_digest,
        "assembly_config_hash": manifest.assembly_config_hash,
        "policy_id": policy_id,
        "eval_config_hash": eval_config_hash,
        "frozen_eval_manifest_hash": frozen_eval_manifest_hash,
        "overall": overall_metrics,
        "by_skill_bucket_id": stratified_metrics["bySkillBucketId"],
        "by_time_control_class": stratified_metrics["byTimeControlClass"],
        "by_time_pressure_bucket": stratified_metrics["byTimePressureBucket"],
    }

    # Add outcome metrics if outcome head was used (M09)
    if outcome_accumulator is not None:
        outcome_metrics = outcome_accumulator.compute_metrics()
        result["outcome_metrics"] = outcome_metrics

        # Stratified outcome metrics
        result["outcome_metrics_by_skill"] = {
            skill: acc.compute_metrics() for skill, acc in outcome_accumulators_by_skill.items()
        }
        result["outcome_metrics_by_time_control"] = {
            tc: acc.compute_metrics() for tc, acc in outcome_accumulators_by_time_control.items()
        }
        result["outcome_metrics_by_time_pressure"] = {
            tp: acc.compute_metrics() for tp, acc in outcome_accumulators_by_time_pressure.items()
        }

    return result


def _get_game_result_from_record(record: dict[str, Any]) -> str | None:
    """Extract game result from record (from mover's perspective).

    Args:
        record: Dataset record

    Returns:
        'win', 'draw', 'loss', or None if not available
    """
    # Check if game result is stored in meta
    meta = record.get("meta", {})
    if isinstance(meta, dict):
        game_result = meta.get("gameResult")
        if isinstance(game_result, str):
            return game_result

    # Check if game result is at top level
    game_result = record.get("gameResult")
    if isinstance(game_result, str):
        return game_result

    return None


def _compute_eval_config_hash(eval_config: dict[str, Any]) -> str:
    """Compute stable hash of evaluation configuration.

    Args:
        eval_config: Evaluation configuration dict.

    Returns:
        SHA-256 hash (lowercase hex).
    """
    from renacechess.determinism import canonical_hash

    # Sort keys and exclude None values for stability
    config_clean = {k: v for k, v in sorted(eval_config.items()) if v is not None}
    return canonical_hash(config_clean)
