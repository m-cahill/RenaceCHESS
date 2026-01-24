"""Edge case tests for dataset builder (M03 additions)."""

from pathlib import Path

import pytest

from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig


def test_config_mutually_exclusive_inputs():
    """Test that config raises error if both pgn_paths and receipt_paths are provided."""
    with pytest.raises(ValueError, match="mutually exclusive"):
        DatasetBuildConfig(
            pgn_paths=[Path("test.pgn")],
            receipt_paths=[Path("test.json")],
            output_dir=Path("out"),
        )


def test_config_no_inputs():
    """Test that config raises error if neither pgn_paths nor receipt_paths are provided."""
    with pytest.raises(ValueError, match="Must specify either"):
        DatasetBuildConfig(
            pgn_paths=None,
            receipt_paths=None,
            output_dir=Path("out"),
        )


def test_config_shard_size_validation():
    """Test that shard_size validation works."""
    # Valid shard size
    config = DatasetBuildConfig(
        pgn_paths=[Path("test.pgn")],
        output_dir=Path("out"),
        shard_size=100,
    )
    assert config.shard_size == 100

    # Invalid shard size (too small)
    with pytest.raises(ValueError, match="shard_size must be >= 1"):
        DatasetBuildConfig(
            pgn_paths=[Path("test.pgn")],
            output_dir=Path("out"),
            shard_size=0,
        )


def test_config_shard_size_warning(tmp_path: Path):
    """Test that small shard size triggers warning."""
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        DatasetBuildConfig(
            pgn_paths=[Path("test.pgn")],
            output_dir=tmp_path,
            shard_size=50,  # < 100
        )
        assert len(w) == 1
        assert "shard_size" in str(w[0].message).lower()


def test_build_dataset_empty_shard(tmp_path: Path):
    """Test building dataset with no positions (empty shard)."""
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path,
        shard_size=10,
        start_ply=1000,  # Way beyond any game length
        end_ply=2000,
    )

    # Should not raise error, but produce empty dataset
    build_dataset(config)

    manifest_path = tmp_path / "manifest.json"
    assert manifest_path.exists()
    # May have zero shards or one empty shard depending on implementation
    # For now, just verify it doesn't crash


def test_build_dataset_single_record_shard(tmp_path: Path):
    """Test building dataset with shard_size=1 (minimum)."""
    from datetime import datetime

    frozen_time = datetime(2024, 1, 1, 12, 0, 0)
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path,
        shard_size=1,  # Minimum shard size
        max_positions=5,
    )

    build_dataset(config, generated_at=frozen_time)

    # Should create multiple shards
    manifest_path = tmp_path / "manifest.json"
    assert manifest_path.exists()
    import json

    manifest = json.loads(manifest_path.read_text())
    assert len(manifest["shardRefs"]) >= 1
    # Each shard should have at most 1 record
    for shard_ref in manifest["shardRefs"]:
        assert shard_ref["records"] <= 1
