"""Targeted tests for CLI eval command to raise coverage."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from renacechess.cli import main


def test_cli_eval_run_basic(tmp_path: Path, capsys) -> None:
    """Test CLI eval run command (basic, without accuracy)."""
    # Build a small dataset first
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    output_dir = tmp_path / "eval_output"

    # Build dataset
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "dataset",
            "build",
            "--pgn",
            str(pgn_path),
            "--out",
            str(dataset_dir),
            "--max-positions",
            "10",
        ],
    ):
        main()

    manifest_path = dataset_dir / "manifest.json"
    assert manifest_path.exists()

    # Run eval
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "eval",
            "run",
            "--dataset-manifest",
            str(manifest_path),
            "--policy",
            "baseline.first_legal",
            "--out",
            str(output_dir),
            "--max-records",
            "5",
        ],
    ):
        main()

    # Verify report was created
    report_path = output_dir / "eval_report.json"
    assert report_path.exists()

    # Verify report is valid JSON
    report_dict = json.loads(report_path.read_text())
    assert report_dict["schemaVersion"] == "eval_report.v1"
    assert "metrics" in report_dict


def test_cli_eval_run_with_accuracy(tmp_path: Path, capsys) -> None:
    """Test CLI eval run command with accuracy enabled."""
    # Build a small dataset first
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    output_dir = tmp_path / "eval_output"

    # Build dataset
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "dataset",
            "build",
            "--pgn",
            str(pgn_path),
            "--out",
            str(dataset_dir),
            "--max-positions",
            "10",
        ],
    ):
        main()

    manifest_path = dataset_dir / "manifest.json"
    assert manifest_path.exists()

    # Run eval with accuracy
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "eval",
            "run",
            "--dataset-manifest",
            str(manifest_path),
            "--policy",
            "baseline.first_legal",
            "--out",
            str(output_dir),
            "--compute-accuracy",
            "--top-k",
            "1,3",
            "--max-records",
            "5",
        ],
    ):
        main()

    # Verify report was created
    report_path = output_dir / "eval_report.json"
    assert report_path.exists()

    # Verify report is v2 with accuracy
    report_dict = json.loads(report_path.read_text())
    assert report_dict["schemaVersion"] == "eval_report.v2"
    assert "accuracy" in report_dict
    assert "totalRecordCount" in report_dict
    assert "labeledRecordCount" in report_dict


def test_cli_eval_run_accuracy_no_labels(tmp_path: Path, capsys) -> None:
    """Test CLI eval run with accuracy but no labeled records (should error)."""
    # Build a small dataset first
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    output_dir = tmp_path / "eval_output"

    # Build dataset
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "dataset",
            "build",
            "--pgn",
            str(pgn_path),
            "--out",
            str(dataset_dir),
            "--max-positions",
            "10",
        ],
    ):
        main()

    manifest_path = dataset_dir / "manifest.json"
    assert manifest_path.exists()

    # Remove chosenMove from records (simulate unlabeled dataset)
    shard_path = dataset_dir / "shards" / "shard_000.jsonl"
    if shard_path.exists():
        records = []
        with shard_path.open() as f:
            for line in f:
                record = json.loads(line)
                if "chosenMove" in record:
                    del record["chosenMove"]
                records.append(record)
        with shard_path.open("w") as f:
            for record in records:
                f.write(json.dumps(record, separators=(",", ":")) + "\n")

    # Run eval with accuracy (should fail)
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "eval",
            "run",
            "--dataset-manifest",
            str(manifest_path),
            "--policy",
            "baseline.first_legal",
            "--out",
            str(output_dir),
            "--compute-accuracy",
            "--max-records",
            "5",
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "no labeled records found" in captured.err.lower()


def test_cli_eval_invalid_subcommand(capsys) -> None:
    """Test CLI eval with invalid subcommand."""
    with patch.object(sys, "argv", ["renacechess", "eval", "invalid"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code in (1, 2)
        captured = capsys.readouterr()
        assert "eval" in captured.out.lower() or "eval" in captured.err.lower()


def test_cli_eval_run_invalid_top_k(tmp_path: Path, capsys) -> None:
    """Test CLI eval run with invalid top-k values."""
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    output_dir = tmp_path / "eval_output"

    # Build dataset
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "dataset",
            "build",
            "--pgn",
            str(pgn_path),
            "--out",
            str(dataset_dir),
            "--max-positions",
            "5",
        ],
    ):
        main()

    manifest_path = dataset_dir / "manifest.json"

    # Test invalid top-k (non-integer)
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "eval",
            "run",
            "--dataset-manifest",
            str(manifest_path),
            "--policy",
            "baseline.first_legal",
            "--out",
            str(output_dir),
            "--compute-accuracy",
            "--top-k",
            "1,abc",
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "top-k" in captured.err.lower() or "integer" in captured.err.lower()
