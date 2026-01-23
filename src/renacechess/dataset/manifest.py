"""Dataset manifest generation."""

from datetime import datetime
from pathlib import Path
from typing import Literal

from renacechess.contracts.models import (
    DatasetManifest,
    DatasetManifestAssemblyConfigV2,
    DatasetManifestInputV2,
    DatasetManifestShardRef,
    DatasetManifestShardRefV2,
    DatasetManifestSplitAssignments,
    DatasetManifestV2,
)
from renacechess.dataset.config import DatasetBuildConfig
from renacechess.determinism import canonical_hash, canonical_json_dump


def generate_manifest(
    config: DatasetBuildConfig,
    shard_id: str,
    shard_path: Path,
    shard_hash: str,
    split_counts: dict[str, list[str]],
    generated_at: datetime | None = None,
) -> None:
    """Generate dataset manifest.

    Args:
        config: Build configuration.
        shard_id: Shard identifier.
        shard_path: Path to shard file.
        shard_hash: SHA-256 hash of shard content.
        split_counts: Dictionary mapping split names to lists of record keys.
        generated_at: Override creation timestamp (for testing).
    """
    # Compute filter config hash
    config_dict = config.to_dict()
    filter_config_hash = canonical_hash(config_dict)

    # Generate timestamp
    if generated_at is None:
        created_at = datetime.now()
    else:
        created_at = generated_at

    # Build shard reference
    # Use relative path from output_dir
    relative_path = shard_path.relative_to(config.output_dir)
    shard_ref = DatasetManifestShardRef(
        shard_id=shard_id,
        hash=shard_hash,
        path=str(relative_path),
    )

    # Build split assignments
    # For M01, we assign the entire shard to all splits (since it's one shard)
    # But we track which records belong to which split
    split_assignments = DatasetManifestSplitAssignments(
        train=[shard_id] if split_counts["train"] else [],
        val=[shard_id] if split_counts["val"] else [],
        frozen_eval=[shard_id] if split_counts["frozenEval"] else [],
    )

    # Build manifest
    manifest = DatasetManifest(
        schema_version="v1",
        created_at=created_at,
        shard_refs=[shard_ref],
        filter_config_hash=filter_config_hash,
        split_assignments=split_assignments,
    )

    # Write manifest
    manifest_path = config.output_dir / "manifest.json"
    manifest_dict = manifest.model_dump(mode="json", by_alias=True)
    manifest_json = canonical_json_dump(manifest_dict).decode("utf-8")
    manifest_path.write_text(manifest_json, encoding="utf-8")


def generate_manifest_v2(
    config: DatasetBuildConfig,
    shard_refs: list[tuple[str, Path, str, int]],  # (shard_id, path, hash, records)
    split_counts: dict[str, list[str]],
    shard_splits: dict[str, set[str]],  # shard_id -> set of split names
    input_info: list[tuple[str, str | None, str | None]],  # (type, digest, path)
    generated_at: datetime | None = None,
) -> None:
    """Generate dataset manifest v2.

    Args:
        config: Build configuration.
        shard_refs: List of (shard_id, path, hash, records) tuples.
        split_counts: Dictionary mapping split names to lists of record keys.
        input_info: List of (type, digest, path) tuples for inputs.
        generated_at: Override creation timestamp (for testing).
    """
    # Generate timestamp
    if generated_at is None:
        created_at = datetime.now()
    else:
        created_at = generated_at

    # Build assembly config (treat 0 as None for max_games/max_positions)
    max_games_val = (
        config.max_games if config.max_games is not None and config.max_games > 0 else None
    )
    max_positions_val = (
        config.max_positions
        if config.max_positions is not None and config.max_positions > 0
        else None
    )
    assembly_config = DatasetManifestAssemblyConfigV2(
        shard_size=config.shard_size,
        max_games=max_games_val,
        max_positions=max_positions_val,
        start_ply=config.start_ply,
        end_ply=config.end_ply,
    )

    # Compute assembly config hash
    assembly_config_dict = config.to_assembly_config_dict()
    assembly_config_hash = canonical_hash(assembly_config_dict)

    # Build shard references
    shard_refs_v2: list[DatasetManifestShardRefV2] = []
    shard_ids: set[str] = set()

    for shard_id, shard_path, shard_hash, record_count in shard_refs:
        # Use relative path from output_dir
        relative_path = shard_path.relative_to(config.output_dir)
        shard_refs_v2.append(
            DatasetManifestShardRefV2(
                shard_id=shard_id,
                hash=shard_hash,
                path=str(relative_path),
                records=record_count,
            )
        )
        shard_ids.add(shard_id)

    # Build split assignments (record-level, not shard-level)
    # Use shard_splits to determine which shards contain records for each split
    train_shards = sorted(
        shard_id for shard_id in shard_ids if "train" in shard_splits.get(shard_id, set())
    )
    val_shards = sorted(
        shard_id for shard_id in shard_ids if "val" in shard_splits.get(shard_id, set())
    )
    frozen_eval_shards = sorted(
        shard_id
        for shard_id in shard_ids
        if "frozenEval" in shard_splits.get(shard_id, set())
    )

    split_assignments = DatasetManifestSplitAssignments(
        train=train_shards,
        val=val_shards,
        frozen_eval=frozen_eval_shards,
    )

    # Build input references
    input_refs: list[DatasetManifestInputV2] = []
    for input_type, digest, path in input_info:
        receipt_id = None
        if input_type == "ingest_receipt" and path:
            # Extract receipt ID from path (filename without extension)
            receipt_id = Path(path).stem

        # Type narrowing for Literal type
        if input_type == "ingest_receipt":
            input_type_literal: Literal["ingest_receipt", "pgn_file"] = "ingest_receipt"
        else:
            input_type_literal = "pgn_file"

        input_refs.append(
            DatasetManifestInputV2(
                type=input_type_literal,
                digest=digest or "",
                receipt_id=receipt_id,
                path=path,
            )
        )

    # Compute dataset digest
    # Hash of: assemblyConfigHash + sorted input digests + schema versions
    input_digests_sorted = sorted([digest for _, digest, _ in input_info if digest])
    dataset_digest_parts = {
        "assemblyConfigHash": assembly_config_hash,
        "inputDigests": input_digests_sorted,
        "schemaVersions": ["v2"],  # Schema versions used
    }
    dataset_digest = canonical_hash(dataset_digest_parts)

    # Compute legacy filter_config_hash for compatibility
    config_dict = config.to_dict()
    filter_config_hash = canonical_hash(config_dict)

    # Build manifest v2
    manifest = DatasetManifestV2(
        schema_version="v2",
        created_at=created_at,
        shard_refs=shard_refs_v2,
        assembly_config_hash=assembly_config_hash,
        dataset_digest=dataset_digest,
        inputs=input_refs,
        assembly_config=assembly_config,
        split_assignments=split_assignments,
        filter_config_hash=filter_config_hash,  # Legacy compatibility
    )

    # Write manifest
    manifest_path = config.output_dir / "manifest.json"
    manifest_dict = manifest.model_dump(mode="json", by_alias=True, exclude_none=True)
    manifest_json = canonical_json_dump(manifest_dict).decode("utf-8")
    manifest_path.write_text(manifest_json, encoding="utf-8")
