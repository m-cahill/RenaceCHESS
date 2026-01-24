"""Tests for M08 training infrastructure."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig
from renacechess.models.training import PolicyDataset, train_baseline_policy


def test_policy_dataset_loading(tmp_path: Path) -> None:
    """Test PolicyDataset loads records correctly."""
    # Build a minimal dataset with labeled records
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"

    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=dataset_dir,
        max_positions=10,
        start_ply=0,
        end_ply=10,
    )
    build_dataset(config, generated_at=datetime(2024, 1, 1, 12, 0, 0))

    manifest_path = dataset_dir / "manifest.json"

    # Create dataset
    dataset = PolicyDataset(manifest_path, seed=42)

    # Should have some records
    assert len(dataset) > 0

    # Check sample structure
    sample = dataset[0]
    assert "fen" in sample
    assert "skill_bucket" in sample
    assert "time_control" in sample
    assert "legal_moves" in sample
    assert "chosen_move" in sample
    assert isinstance(sample["legal_moves"], list)
    assert len(sample["legal_moves"]) > 0


def test_policy_dataset_excludes_frozen_eval(tmp_path: Path) -> None:
    """Test PolicyDataset excludes frozen eval records."""
    # Build dataset
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"

    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=dataset_dir,
        max_positions=20,
        start_ply=0,
        end_ply=10,
    )
    build_dataset(config, generated_at=datetime(2024, 1, 1, 12, 0, 0))

    manifest_path = dataset_dir / "manifest.json"

    # Generate frozen eval manifest (use lowercase time pressure to avoid validation error)
    from renacechess.frozen_eval import generate_frozen_eval_manifest

    frozen_manifest = generate_frozen_eval_manifest(
        source_manifest_path=manifest_path,
        target_total_records=5,
        min_per_skill_bucket=1,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )

    frozen_path = tmp_path / "frozen_eval.json"
    frozen_dict = frozen_manifest.model_dump(mode="json", by_alias=True, exclude_none=True)
    frozen_path.write_text(json.dumps(frozen_dict, indent=2))

    # Create dataset with frozen eval
    dataset_with_frozen = PolicyDataset(manifest_path, frozen_eval_manifest_path=frozen_path)
    dataset_without_frozen = PolicyDataset(manifest_path)

    # Dataset with frozen eval should have fewer records
    assert len(dataset_with_frozen) < len(dataset_without_frozen)


@pytest.mark.slow
def test_train_baseline_policy_minimal(tmp_path: Path) -> None:
    """Test training baseline policy (minimal run)."""
    # Build a minimal dataset
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"

    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=dataset_dir,
        max_positions=20,
        start_ply=0,
        end_ply=10,
    )
    build_dataset(config, generated_at=datetime(2024, 1, 1, 12, 0, 0))

    manifest_path = dataset_dir / "manifest.json"
    output_dir = tmp_path / "model_output"

    # Train with minimal epochs
    model_path = train_baseline_policy(
        manifest_path=manifest_path,
        frozen_eval_manifest_path=None,
        output_dir=output_dir,
        epochs=1,  # Minimal for testing
        batch_size=1,
        learning_rate=0.001,
        seed=42,
    )

    # Verify model file exists
    assert model_path.exists()
    assert model_path.suffix == ".pt"

    # Verify metadata exists
    metadata_path = output_dir / "model_metadata.json"
    assert metadata_path.exists()

    # Verify metadata structure
    with metadata_path.open(encoding="utf-8") as f:
        metadata = json.load(f)

    assert metadata["model_type"] == "BaselinePolicyV1"
    assert "move_vocab_size" in metadata
    assert "epochs" in metadata
    assert "seed" in metadata
    assert metadata["seed"] == 42


def test_policy_dataset_no_records_error(tmp_path: Path) -> None:
    """Test PolicyDataset with no training records raises error."""
    # Create empty manifest
    manifest_path = tmp_path / "manifest.json"
    manifest_dict = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T12:00:00",
        "shardRefs": [],
        "splitAssignments": {"train": [], "val": [], "frozenEval": []},
        "assemblyConfig": {"shardSize": 10000},
        "assemblyConfigHash": "a" * 64,
        "datasetDigest": "b" * 64,
        "inputs": [],
    }
    manifest_path.write_text(json.dumps(manifest_dict))

    # Create dataset (should have 0 records)
    dataset = PolicyDataset(manifest_path, seed=42)
    assert len(dataset) == 0

    # Training should raise ValueError
    from renacechess.models.training import train_baseline_policy

    with pytest.raises(ValueError, match="No training records found"):
        train_baseline_policy(
            manifest_path=manifest_path,
            frozen_eval_manifest_path=None,
            output_dir=tmp_path / "output",
            epochs=1,
            batch_size=1,
            learning_rate=0.001,
            seed=42,
        )
