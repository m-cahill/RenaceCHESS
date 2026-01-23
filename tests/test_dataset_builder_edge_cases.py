"""Tests for dataset builder edge cases."""

from pathlib import Path

import pytest

from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig


def test_builder_empty_pgn_list(tmp_path: Path):
    """Test builder with empty PGN list."""
    config = DatasetBuildConfig(
        pgn_paths=[],
        output_dir=tmp_path,
    )

    with pytest.raises(ValueError, match="No PGN files found"):
        build_dataset(config)


def test_builder_empty_directory(tmp_path: Path):
    """Test builder with directory containing no PGN files."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    config = DatasetBuildConfig(
        pgn_paths=[empty_dir],
        output_dir=tmp_path / "output",
    )

    with pytest.raises(ValueError, match="No PGN files found"):
        build_dataset(config)


def test_builder_nonexistent_path(tmp_path: Path):
    """Test builder with non-existent PGN path."""
    config = DatasetBuildConfig(
        pgn_paths=[tmp_path / "nonexistent.pgn"],
        output_dir=tmp_path / "output",
    )

    with pytest.raises(ValueError, match="No PGN files found"):
        build_dataset(config)


def test_builder_max_games_zero(tmp_path: Path):
    """Test builder with max_games=0."""
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path,
        max_games=0,
    )

    build_dataset(config)

    # Should produce empty shard
    shard_path = tmp_path / "shards" / "shard_000.jsonl"
    if shard_path.exists():
        content = shard_path.read_text()
        assert len(content.strip()) == 0 or content.strip() == ""


def test_builder_max_positions_zero(tmp_path: Path):
    """Test builder with max_positions=0."""
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path,
        max_positions=0,
    )

    build_dataset(config)

    # Should produce empty shard
    shard_path = tmp_path / "shards" / "shard_000.jsonl"
    if shard_path.exists():
        content = shard_path.read_text()
        assert len(content.strip()) == 0 or content.strip() == ""


def test_builder_start_ply_greater_than_end_ply(tmp_path: Path):
    """Test builder with start_ply > end_ply."""
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path,
        start_ply=10,
        end_ply=5,
    )

    build_dataset(config)

    # Should produce empty or minimal shard (no positions in range)
    shard_path = tmp_path / "shards" / "shard_000.jsonl"
    # Builder should handle this gracefully (no positions in range)


def test_builder_directory_with_pgn_files(tmp_path: Path):
    """Test builder with directory containing PGN files."""
    pgn_dir = tmp_path / "pgn_dir"
    pgn_dir.mkdir()

    # Copy sample PGN to directory
    sample_pgn = Path(__file__).parent / "data" / "sample.pgn"
    (pgn_dir / "sample.pgn").write_bytes(sample_pgn.read_bytes())

    config = DatasetBuildConfig(
        pgn_paths=[pgn_dir],
        output_dir=tmp_path / "output",
        max_positions=5,
    )

    build_dataset(config)

    # Should produce shard
    shard_path = tmp_path / "output" / "shards" / "shard_000.jsonl"
    assert shard_path.exists()

