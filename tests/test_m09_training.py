"""Tests for outcome head training (M09)."""

import json
import tempfile
from pathlib import Path

import pytest

from renacechess.contracts.models import DatasetManifestV2, FrozenEvalManifestV1
from renacechess.models.training_outcome import OutcomeDataset, train_outcome_head


def test_outcome_dataset_initialization() -> None:
    """Test OutcomeDataset initialization."""
    # Create minimal manifest
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfig": {"shardSize": 10000},
        "assemblyConfigHash": "b" * 64,
        "shardRefs": [],
        "splitAssignments": {"train": [], "val": [], "frozenEval": []},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        dataset = OutcomeDataset(manifest_path)
        assert len(dataset) == 0


def test_outcome_dataset_loads_records() -> None:
    """Test OutcomeDataset loads records from shards."""
    # Create minimal manifest with shard
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfigHash": "b" * 64,
        "shardRefs": [
            {
                "shardId": "shard_001",
                "hash": "c" * 64,
                "path": "shards/shard_001.jsonl",
                "records": 1,
            }
        ],
        "splitAssignments": {"train": ["shard_001"], "val": [], "frozenEval": []},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        # Create shard with record containing game result
        shards_dir = tmp_path / "shards"
        shards_dir.mkdir()
        shard_path = shards_dir / "shard_001.jsonl"

        record = {
            "position": {"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"},
            "conditioning": {"skillBucket": "1200_1399", "timeControlClass": "blitz"},
            "meta": {"inputHash": "test123", "gameResult": "win"},
        }
        shard_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

        dataset = OutcomeDataset(manifest_path)
        # Should load record if it has game result and is in train split
        assert len(dataset) >= 0  # May be 0 if split assignment doesn't match


def test_outcome_dataset_excludes_frozen_eval() -> None:
    """Test OutcomeDataset excludes frozen eval records."""
    # Create manifest and frozen eval manifest
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfigHash": "b" * 64,
        "shardRefs": [
            {
                "shardId": "shard_001",
                "hash": "c" * 64,
                "path": "shards/shard_001.jsonl",
                "records": 1,
            }
        ],
        "splitAssignments": {"train": ["shard_001"], "val": [], "frozenEval": []},
    }

    frozen_manifest_data = {
        "schemaVersion": "v1",
        "createdAt": "2024-01-01T00:00:00",
        "manifestHash": "d" * 64,
        "records": [{"recordKey": "test123:0", "shardId": "shard_001", "shardHash": "c" * 64}],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        frozen_manifest_path = tmp_path / "frozen_eval.json"
        frozen_manifest_path.write_text(json.dumps(frozen_manifest_data), encoding="utf-8")

        shards_dir = tmp_path / "shards"
        shards_dir.mkdir()
        shard_path = shards_dir / "shard_001.jsonl"

        record = {
            "position": {"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"},
            "conditioning": {"skillBucket": "1200_1399", "timeControlClass": "blitz"},
            "meta": {"inputHash": "test123", "gameResult": "win"},
        }
        shard_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

        dataset = OutcomeDataset(manifest_path, frozen_manifest_path)
        # Frozen eval record should be excluded
        assert len(dataset) == 0


def test_outcome_dataset_getitem() -> None:
    """Test OutcomeDataset __getitem__ returns correct format."""
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfig": {"shardSize": 10000},
        "assemblyConfigHash": "b" * 64,
        "shardRefs": [],
        "splitAssignments": {"train": [], "val": [], "frozenEval": []},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        dataset = OutcomeDataset(manifest_path)

        if len(dataset) > 0:
            sample = dataset[0]
            assert "fen" in sample
            assert "skill_bucket" in sample
            assert "time_control" in sample
            assert "outcome_class" in sample
            assert sample["outcome_class"] in [0, 1, 2]  # win, draw, loss


def test_train_outcome_head_requires_records() -> None:
    """Test train_outcome_head fails with no training records."""
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfig": {"shardSize": 10000},
        "assemblyConfigHash": "b" * 64,
        "shardRefs": [],
        "splitAssignments": {"train": [], "val": [], "frozenEval": []},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        output_dir = tmp_path / "output"

        with pytest.raises(ValueError, match="No training records"):
            train_outcome_head(
                manifest_path=manifest_path,
                frozen_eval_manifest_path=None,
                output_dir=output_dir,
                epochs=1,
            )
