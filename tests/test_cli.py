"""Tests for CLI module."""

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from renacechess.cli import main


def test_cli_demo_command(tmp_path: Path, capsys) -> None:
    """Test CLI demo command."""
    sample_pgn = Path(__file__).parent / "data" / "sample.pgn"
    output_file = tmp_path / "demo.json"

    with patch.object(
        sys,
        "argv",
        ["renacechess", "demo", "--pgn", str(sample_pgn), "--out", str(output_file)],
    ):
        main()

    # Check that output file was created
    assert output_file.exists()

    # Check that it's valid JSON
    content = output_file.read_text(encoding="utf-8")
    payload = json.loads(content)

    # Verify structure
    assert "position" in payload
    assert "policy" in payload
    assert "meta" in payload
    assert payload["meta"]["schemaVersion"] == "v1"


def test_cli_demo_command_stdout(tmp_path: Path, capsys) -> None:
    """Test CLI demo command with stdout output."""
    sample_pgn = Path(__file__).parent / "data" / "sample.pgn"

    with patch.object(sys, "argv", ["renacechess", "demo", "--pgn", str(sample_pgn)]):
        main()

    captured = capsys.readouterr()
    # Should output JSON to stdout
    payload = json.loads(captured.out)
    assert "position" in payload


def test_cli_demo_command_empty_pgn(tmp_path: Path, capsys) -> None:
    """Test CLI demo command with empty PGN."""
    empty_pgn = tmp_path / "empty.pgn"
    empty_pgn.write_text("")

    with patch.object(sys, "argv", ["renacechess", "demo", "--pgn", str(empty_pgn)]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "Error" in captured.err


def test_cli_help(capsys) -> None:
    """Test CLI help command."""
    with patch.object(sys, "argv", ["renacechess", "--help"]):
        with pytest.raises(SystemExit):
            main()

    captured = capsys.readouterr()
    assert "RenaceCHESS" in captured.out


def test_cli_demo_command_with_ply(tmp_path: Path) -> None:
    """Test CLI demo command with custom ply."""
    sample_pgn = Path(__file__).parent / "data" / "sample.pgn"
    output_file = tmp_path / "demo.json"

    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "demo",
            "--pgn",
            str(sample_pgn),
            "--out",
            str(output_file),
            "--ply",
            "10",
        ],
    ):
        main()

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    payload = json.loads(content)
    assert "position" in payload


def test_cli_train_outcome_head_command(tmp_path: Path, capsys, monkeypatch) -> None:
    """Test CLI train-outcome-head command wiring (M10)."""
    # Create minimal manifest fixture
    manifest_path = tmp_path / "manifest.json"
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfig": {"shardSize": 10000},
        "assemblyConfigHash": "b" * 64,
        "shardRefs": [],
        "splitAssignments": {"train": [], "val": [], "frozenEval": []},
    }
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Track if train_outcome_head was called with correct args
    call_args = {}

    def mock_train_outcome_head(
        manifest_path: Path,
        frozen_eval_manifest_path: Path | None,
        output_dir: Path,
        epochs: int,
        batch_size: int,
        learning_rate: float,
        seed: int,
    ) -> Path:
        """Mock training function that writes sentinel files."""
        call_args["manifest_path"] = manifest_path
        call_args["frozen_eval_manifest_path"] = frozen_eval_manifest_path
        call_args["output_dir"] = output_dir
        call_args["epochs"] = epochs
        call_args["batch_size"] = batch_size
        call_args["learning_rate"] = learning_rate
        call_args["seed"] = seed

        # Write sentinel files to verify output handling
        model_file = output_dir / "outcome_head_v1.pt"
        metadata_file = output_dir / "outcome_head_v1_metadata.json"
        model_file.write_bytes(b"fake_model_data")
        metadata_file.write_text(json.dumps({"model_type": "OutcomeHeadV1"}), encoding="utf-8")

        return model_file

    # Monkeypatch the training function
    monkeypatch.setattr(
        "renacechess.models.training_outcome.train_outcome_head", mock_train_outcome_head
    )

    # Execute CLI command
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "train-outcome-head",
            "--dataset-manifest",
            str(manifest_path),
            "--out",
            str(output_dir),
            "--epochs",
            "2",
            "--batch-size",
            "32",
            "--learning-rate",
            "0.001",
            "--seed",
            "42",
        ],
    ):
        main()

    # Verify training function was called with correct args
    assert call_args["manifest_path"] == manifest_path
    assert call_args["frozen_eval_manifest_path"] is None
    assert call_args["output_dir"] == output_dir
    assert call_args["epochs"] == 2
    assert call_args["batch_size"] == 32
    assert call_args["learning_rate"] == 0.001
    assert call_args["seed"] == 42

    # Verify sentinel files were created
    assert (output_dir / "outcome_head_v1.pt").exists()
    assert (output_dir / "outcome_head_v1_metadata.json").exists()

    # Verify stderr output
    captured = capsys.readouterr()
    assert "Outcome head trained and saved" in captured.err
    assert "Metadata saved" in captured.err


def test_cli_train_outcome_head_with_frozen_eval(tmp_path: Path, capsys, monkeypatch) -> None:
    """Test CLI train-outcome-head command with frozen eval manifest (M10)."""
    # Create minimal manifest fixtures
    manifest_path = tmp_path / "manifest.json"
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfig": {"shardSize": 10000},
        "assemblyConfigHash": "b" * 64,
        "shardRefs": [],
        "splitAssignments": {"train": [], "val": [], "frozenEval": []},
    }
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    frozen_eval_path = tmp_path / "frozen_eval.json"
    frozen_eval_data = {
        "schemaVersion": "v1",
        "createdAt": "2024-01-01T00:00:00",
        "manifestHash": "c" * 64,
        "records": [],
    }
    frozen_eval_path.write_text(json.dumps(frozen_eval_data), encoding="utf-8")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    call_args = {}

    def mock_train_outcome_head(
        manifest_path: Path,
        frozen_eval_manifest_path: Path | None,
        output_dir: Path,
        epochs: int,
        batch_size: int,
        learning_rate: float,
        seed: int,
    ) -> Path:
        """Mock training function."""
        call_args["frozen_eval_manifest_path"] = frozen_eval_manifest_path
        model_file = output_dir / "outcome_head_v1.pt"
        model_file.write_bytes(b"fake_model_data")
        return model_file

    monkeypatch.setattr(
        "renacechess.models.training_outcome.train_outcome_head", mock_train_outcome_head
    )

    # Execute CLI command with frozen eval
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "train-outcome-head",
            "--dataset-manifest",
            str(manifest_path),
            "--frozen-eval-manifest",
            str(frozen_eval_path),
            "--out",
            str(output_dir),
        ],
    ):
        main()

    # Verify frozen eval path was passed
    assert call_args["frozen_eval_manifest_path"] == frozen_eval_path


def test_cli_train_outcome_head_error_handling(tmp_path: Path, capsys, monkeypatch) -> None:
    """Test CLI train-outcome-head command error handling (M10)."""
    manifest_path = tmp_path / "manifest.json"
    manifest_data = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfig": {"shardSize": 10000},
        "assemblyConfigHash": "b" * 64,
        "shardRefs": [],
        "splitAssignments": {"train": [], "val": [], "frozenEval": []},
    }
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    def mock_train_outcome_head(*args: Any, **kwargs: Any) -> Path:
        """Mock training function that raises an error."""
        raise ValueError("Training failed")

    monkeypatch.setattr(
        "renacechess.models.training_outcome.train_outcome_head", mock_train_outcome_head
    )

    # Execute CLI command and expect error exit
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "train-outcome-head",
            "--dataset-manifest",
            str(manifest_path),
            "--out",
            str(output_dir),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    # Verify error message
    captured = capsys.readouterr()
    assert "Error" in captured.err
    assert "Training failed" in captured.err
