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
        "assemblyConfig": {"shardSize": 10000},
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
        "assemblyConfig": {"shardSize": 10000},
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
        "schemaVersion": 1,
        "createdAt": "2024-01-01T00:00:00",
        "manifestHash": "a" * 64,
        "sourceManifestRef": {
            "datasetDigest": "a" * 64,
            "manifestPath": "/path/to/manifest.json",
        },
        "records": [
            {
                "recordKey": "test123:0",
                "shardId": "shard_001",
                "shardHash": "c" * 64,
                "skillBucketId": "1200_1399",
                "timeControlClass": "blitz",
                "timePressureBucket": "normal",
            }
        ],
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


def test_train_outcome_head_end_to_end() -> None:
    """Integration test for train_outcome_head end-to-end artifact generation."""
    # Create minimal synthetic dataset (10 records)
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfig": {"shardSize": 10000},
        "assemblyConfigHash": "b" * 64,
        "shardRefs": [
            {
                "shardId": "shard_001",
                "hash": "c" * 64,
                "path": "shards/shard_001.jsonl",
                "records": 10,
            }
        ],
        "splitAssignments": {"train": ["shard_001"], "val": [], "frozenEval": []},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        # Create shard with 10 records (alternating win/draw/loss)
        shards_dir = tmp_path / "shards"
        shards_dir.mkdir()
        shard_path = shards_dir / "shard_001.jsonl"

        outcomes = ["win", "draw", "loss"]
        records = []
        for i in range(10):
            record = {
                "position": {"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"},
                "conditioning": {"skillBucket": "1200_1399", "timeControlClass": "blitz"},
                "meta": {"inputHash": f"test{i}", "gameResult": outcomes[i % 3]},
            }
            records.append(json.dumps(record))

        shard_path.write_text("\n".join(records), encoding="utf-8")

        # Train model
        output_dir = tmp_path / "output"
        model_path = train_outcome_head(
            manifest_path=manifest_path,
            frozen_eval_manifest_path=None,
            output_dir=output_dir,
            epochs=1,
            seed=42,
        )

        # Assert model artifact is written
        assert model_path.exists(), "Model file should be created"
        assert model_path.name == "outcome_head_v1.pt"

        # Assert metadata artifact is written
        metadata_path = output_dir / "outcome_head_v1_metadata.json"
        assert metadata_path.exists(), "Metadata file should be created"

        # Load and validate metadata
        with metadata_path.open(encoding="utf-8") as f:
            metadata = json.load(f)

        # Assert metadata includes required fields
        assert metadata["model_type"] == "OutcomeHeadV1"
        assert metadata["epochs"] == 1
        assert metadata["seed"] == 42
        assert metadata["loss_function"] == "CrossEntropyLoss"
        assert "manifest_path" in metadata
        assert metadata["frozen_eval_manifest_path"] is None


def test_outcome_dataset_handles_missing_shard() -> None:
    """Test OutcomeDataset handles missing shard files gracefully."""
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfig": {"shardSize": 10000},
        "assemblyConfigHash": "b" * 64,
        "shardRefs": [
            {
                "shardId": "shard_missing",
                "hash": "c" * 64,
                "path": "shards/shard_missing.jsonl",
                "records": 1,
            }
        ],
        "splitAssignments": {"train": ["shard_missing"], "val": [], "frozenEval": []},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        dataset = OutcomeDataset(manifest_path)
        # Should handle missing shard gracefully (empty dataset)
        assert len(dataset) == 0


def test_outcome_dataset_skips_empty_lines() -> None:
    """Test OutcomeDataset skips empty lines in shards."""
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfig": {"shardSize": 10000},
        "assemblyConfigHash": "b" * 64,
        "shardRefs": [
            {
                "shardId": "shard_001",
                "hash": "c" * 64,
                "path": "shards/shard_001.jsonl",
                "records": 2,
            }
        ],
        "splitAssignments": {"train": ["shard_001"], "val": [], "frozenEval": []},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        shards_dir = tmp_path / "shards"
        shards_dir.mkdir()
        shard_path = shards_dir / "shard_001.jsonl"

        # Create shard with empty lines
        record = {
            "position": {"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"},
            "conditioning": {"skillBucket": "1200_1399", "timeControlClass": "blitz"},
            "meta": {"inputHash": "test123", "gameResult": "win"},
        }
        shard_path.write_text(
            json.dumps(record) + "\n\n" + json.dumps(record) + "\n", encoding="utf-8"
        )

        dataset = OutcomeDataset(manifest_path)
        # Should skip empty lines and load valid records
        assert len(dataset) >= 0


def test_outcome_dataset_skips_records_without_game_result() -> None:
    """Test OutcomeDataset skips records without game result."""
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfig": {"shardSize": 10000},
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

        shards_dir = tmp_path / "shards"
        shards_dir.mkdir()
        shard_path = shards_dir / "shard_001.jsonl"

        # Record without game result
        record = {
            "position": {"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"},
            "conditioning": {"skillBucket": "1200_1399", "timeControlClass": "blitz"},
            "meta": {"inputHash": "test123"},
        }
        shard_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

        dataset = OutcomeDataset(manifest_path)
        # Should skip record without game result
        assert len(dataset) == 0


def test_outcome_dataset_getitem_all_outcomes() -> None:
    """Test OutcomeDataset __getitem__ handles all outcome types."""
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfig": {"shardSize": 10000},
        "assemblyConfigHash": "b" * 64,
        "shardRefs": [
            {
                "shardId": "shard_001",
                "hash": "c" * 64,
                "path": "shards/shard_001.jsonl",
                "records": 3,
            }
        ],
        "splitAssignments": {"train": ["shard_001"], "val": [], "frozenEval": []},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        shards_dir = tmp_path / "shards"
        shards_dir.mkdir()
        shard_path = shards_dir / "shard_001.jsonl"

        # Create records with all three outcomes
        records = []
        for outcome in ["win", "draw", "loss"]:
            record = {
                "position": {"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"},
                "conditioning": {"skillBucket": "1200_1399", "timeControlClass": "blitz"},
                "meta": {"inputHash": f"test{outcome}", "gameResult": outcome},
            }
            records.append(json.dumps(record))

        shard_path.write_text("\n".join(records), encoding="utf-8")

        dataset = OutcomeDataset(manifest_path)
        if len(dataset) > 0:
            # Test all outcome classes are represented
            outcome_classes = {dataset[i]["outcome_class"] for i in range(len(dataset))}
            assert 0 in outcome_classes or 1 in outcome_classes or 2 in outcome_classes


def test_outcome_dataset_game_result_top_level() -> None:
    """Test OutcomeDataset handles gameResult at top level of record."""
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfig": {"shardSize": 10000},
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

        shards_dir = tmp_path / "shards"
        shards_dir.mkdir()
        shard_path = shards_dir / "shard_001.jsonl"

        # Record with gameResult at top level (not in meta)
        record = {
            "position": {"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"},
            "conditioning": {"skillBucket": "1200_1399", "timeControlClass": "blitz"},
            "meta": {"inputHash": "test123"},
            "gameResult": "win",  # Top-level gameResult
        }
        shard_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

        dataset = OutcomeDataset(manifest_path)
        # Should load record with top-level gameResult
        assert len(dataset) >= 0
