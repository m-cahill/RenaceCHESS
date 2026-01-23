"""Dataset manifest generation."""

from datetime import datetime
from pathlib import Path

from renacechess.contracts.models import (
    DatasetManifest,
    DatasetManifestShardRef,
    DatasetManifestSplitAssignments,
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
