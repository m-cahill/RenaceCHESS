"""Evaluation runner for streaming evaluation over dataset manifests."""

import json
from pathlib import Path
from typing import Any

from renacechess.contracts.models import DatasetManifestV2, EvalReportV3
from renacechess.dataset.split import compute_split_assignment
from renacechess.eval.baselines import compute_policy_seed, create_policy_provider
from renacechess.eval.conditioned_metrics import ConditionedMetricsAccumulator
from renacechess.eval.metrics import MetricsAccumulator, format_fixed_decimal


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
    policy = create_policy_provider(policy_id, seed=policy_seed)

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
) -> dict[str, Any]:
    """Run evaluation with conditioned metrics (M06).

    Args:
        manifest_path: Path to dataset manifest v2.
        policy_id: Policy identifier (e.g., 'baseline.uniform_random').
        eval_config: Evaluation configuration dict (for hashing).
        max_records: Maximum number of records to evaluate (None = no limit).
        compute_accuracy: Whether to compute accuracy metrics (requires chosenMove labels).
        top_k_values: List of K values for top-K accuracy (e.g., [1, 3, 5]). Defaults to [1].
        frozen_eval_manifest_hash: SHA-256 hash of frozen eval manifest (if frozen eval).

    Returns:
        Dictionary with evaluation results (ready for EvalReportV3 construction).
    """
    # Load manifest
    manifest = load_manifest(manifest_path)
    manifest_dir = manifest_path.parent

    # Compute policy seed for deterministic RNG
    eval_config_hash = _compute_eval_config_hash(eval_config)
    policy_seed = compute_policy_seed(manifest.dataset_digest, policy_id, eval_config_hash)

    # Create policy provider
    policy = create_policy_provider(policy_id, seed=policy_seed)

    # Initialize conditioned metrics accumulator
    top_k_vals = top_k_values if top_k_values is not None else [1]
    accumulator = ConditionedMetricsAccumulator(
        compute_accuracy=compute_accuracy, top_k_values=top_k_vals
    )

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

    return result


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
