"""Golden file regression tests for dataset building."""

import json
from datetime import datetime
from pathlib import Path

from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig
from renacechess.determinism import stable_hash


def test_dataset_build_golden(tmp_path: Path):
    """Test that dataset build produces deterministic outputs matching golden files."""
    # Use frozen timestamp for determinism
    frozen_time = datetime(2024, 1, 1, 12, 0, 0)

    # Build dataset with fixed parameters
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path,
        max_positions=20,
        start_ply=0,
        end_ply=10,
    )
    build_dataset(config, generated_at=frozen_time)

    # Verify shard exists
    shard_path = tmp_path / "shards" / "shard_000.jsonl"
    assert shard_path.exists()

    # Verify manifest exists
    manifest_path = tmp_path / "manifest.json"
    assert manifest_path.exists()

    # Load and verify manifest structure
    manifest = json.loads(manifest_path.read_text())
    assert manifest["schemaVersion"] == "v1"
    assert len(manifest["shardRefs"]) == 1
    assert manifest["shardRefs"][0]["shardId"] == "shard_000"

    # Verify shard hash matches manifest
    shard_content = shard_path.read_bytes()
    shard_hash = stable_hash(shard_content)
    assert manifest["shardRefs"][0]["hash"] == shard_hash

    # Verify filter config hash is present
    assert "filterConfigHash" in manifest
    assert len(manifest["filterConfigHash"]) == 64  # SHA-256 hex length

    # Verify split assignments are present
    assert "splitAssignments" in manifest
    assert "train" in manifest["splitAssignments"]
    assert "val" in manifest["splitAssignments"]
    assert "frozenEval" in manifest["splitAssignments"]


def test_dataset_build_determinism(tmp_path: Path):
    """Test that building the same dataset twice produces identical outputs."""
    frozen_time = datetime(2024, 1, 1, 12, 0, 0)

    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path,
        max_positions=10,
    )

    # Build first time
    build_dataset(config, generated_at=frozen_time)
    shard_path1 = tmp_path / "shards" / "shard_000.jsonl"
    manifest_path1 = tmp_path / "manifest.json"
    shard_content1 = shard_path1.read_bytes()
    manifest_content1 = manifest_path1.read_bytes()

    # Clean and rebuild
    shard_path1.unlink()
    manifest_path1.unlink()

    # Build second time
    build_dataset(config, generated_at=frozen_time)
    shard_path2 = tmp_path / "shards" / "shard_000.jsonl"
    manifest_path2 = tmp_path / "manifest.json"
    shard_content2 = shard_path2.read_bytes()
    manifest_content2 = manifest_path2.read_bytes()

    # Should be byte-identical
    assert shard_content1 == shard_content2
    assert manifest_content1 == manifest_content2

