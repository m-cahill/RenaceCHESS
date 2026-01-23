"""Golden file regression tests for dataset building with v2 manifests and multi-shard support."""

import json
from datetime import datetime
from pathlib import Path

from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig
from renacechess.determinism import stable_hash


def test_dataset_build_v2_multi_shard(tmp_path: Path):
    """Test that dataset build with small shard size creates multiple shards."""
    frozen_time = datetime(2024, 1, 1, 12, 0, 0)

    # Build dataset with small shard size to force multiple shards
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path,
        shard_size=5,  # Small shard size
        max_positions=20,
        start_ply=0,
        end_ply=10,
    )
    build_dataset(config, generated_at=frozen_time)

    # Verify manifest exists and is v2
    manifest_path = tmp_path / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["schemaVersion"] == "v2"

    # Should have multiple shards
    shard_refs = manifest["shardRefs"]
    assert len(shard_refs) > 1

    # Verify each shard exists and has correct structure
    for shard_ref in shard_refs:
        shard_path = tmp_path / shard_ref["path"]
        assert shard_path.exists()
        assert shard_ref["records"] <= 5  # Should not exceed shard_size
        assert shard_ref["records"] > 0

        # Verify hash matches
        shard_content = shard_path.read_bytes()
        shard_hash = stable_hash(shard_content)
        assert shard_ref["hash"] == shard_hash

    # Verify assembly config
    assert manifest["assemblyConfig"]["shardSize"] == 5
    assert "assemblyConfigHash" in manifest
    assert "datasetDigest" in manifest


def test_dataset_build_v2_determinism(tmp_path: Path):
    """Test that building the same dataset twice produces identical v2 outputs."""
    frozen_time = datetime(2024, 1, 1, 12, 0, 0)

    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path,
        shard_size=10,
        max_positions=15,
    )

    # Build first time
    build_dataset(config, generated_at=frozen_time)
    manifest_path1 = tmp_path / "manifest.json"
    manifest_content1 = manifest_path1.read_bytes()
    manifest1 = json.loads(manifest_content1)
    shard_paths1 = [tmp_path / ref["path"] for ref in manifest1["shardRefs"]]
    shard_contents1 = {p: p.read_bytes() for p in shard_paths1}

    # Clean and rebuild
    for p in shard_paths1:
        if p.exists():
            p.unlink()
    if manifest_path1.exists():
        manifest_path1.unlink()

    # Build second time
    build_dataset(config, generated_at=frozen_time)
    manifest_path2 = tmp_path / "manifest.json"
    manifest_content2 = manifest_path2.read_bytes()
    manifest2 = json.loads(manifest_content2)
    shard_paths2 = [tmp_path / ref["path"] for ref in manifest2["shardRefs"]]
    shard_contents2 = {p: p.read_bytes() for p in shard_paths2}

    # Should be byte-identical
    assert manifest_content1 == manifest_content2
    assert len(shard_contents1) == len(shard_contents2)
    for path1, path2 in zip(sorted(shard_paths1), sorted(shard_paths2)):
        assert shard_contents1[path1] == shard_contents2[path2]


def test_dataset_build_v2_assembly_config_hash(tmp_path: Path):
    """Test that assembly config hash is deterministic and changes with config."""
    frozen_time = datetime(2024, 1, 1, 12, 0, 0)

    pgn_path = Path(__file__).parent / "data" / "sample.pgn"

    # Build with config A
    config_a = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path / "a",
        shard_size=10,
        max_positions=10,
    )
    build_dataset(config_a, generated_at=frozen_time)
    manifest_a = json.loads((tmp_path / "a" / "manifest.json").read_text())
    hash_a = manifest_a["assemblyConfigHash"]

    # Build with config B (different shard size)
    config_b = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path / "b",
        shard_size=20,  # Different shard size
        max_positions=10,
    )
    build_dataset(config_b, generated_at=frozen_time)
    manifest_b = json.loads((tmp_path / "b" / "manifest.json").read_text())
    hash_b = manifest_b["assemblyConfigHash"]

    # Hashes should be different
    assert hash_a != hash_b

    # But same config should produce same hash
    config_a2 = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path / "a2",
        shard_size=10,
        max_positions=10,
    )
    build_dataset(config_a2, generated_at=frozen_time)
    manifest_a2 = json.loads((tmp_path / "a2" / "manifest.json").read_text())
    hash_a2 = manifest_a2["assemblyConfigHash"]
    assert hash_a == hash_a2


def test_dataset_build_v2_dataset_digest(tmp_path: Path):
    """Test that dataset digest includes input digests and is stable."""
    frozen_time = datetime(2024, 1, 1, 12, 0, 0)

    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path,
        shard_size=10,
        max_positions=10,
    )
    build_dataset(config, generated_at=frozen_time)

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert "datasetDigest" in manifest
    assert len(manifest["datasetDigest"]) == 64

    # Dataset digest should include input digest
    assert len(manifest["inputs"]) == 1
    assert manifest["inputs"][0]["digest"] is not None
    assert len(manifest["inputs"][0]["digest"]) == 64
