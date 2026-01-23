"""Tests for CLI dataset build command."""

import json
import subprocess
import sys
from pathlib import Path


def test_cli_dataset_build(tmp_path: Path):
    """Test CLI dataset build command."""
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    output_dir = tmp_path / "dataset_output"

    # Run CLI command
    subprocess.run(
        [
            sys.executable,
            "-m",
            "renacechess.cli",
            "dataset",
            "build",
            "--pgn",
            str(pgn_path),
            "--out",
            str(output_dir),
            "--max-positions",
            "10",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    # Verify output directory was created
    assert output_dir.exists()

    # Verify shard exists
    shard_path = output_dir / "shards" / "shard_000.jsonl"
    assert shard_path.exists()

    # Verify manifest exists
    manifest_path = output_dir / "manifest.json"
    assert manifest_path.exists()

    # Verify manifest is valid JSON
    manifest = json.loads(manifest_path.read_text())
    assert manifest["schemaVersion"] == "v1"


def test_cli_dataset_build_with_filters(tmp_path: Path):
    """Test CLI dataset build with ply filters."""
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    output_dir = tmp_path / "dataset_output_filtered"

    # Run CLI command with filters
    subprocess.run(
        [
            sys.executable,
            "-m",
            "renacechess.cli",
            "dataset",
            "build",
            "--pgn",
            str(pgn_path),
            "--out",
            str(output_dir),
            "--start-ply",
            "2",
            "--end-ply",
            "8",
            "--max-positions",
            "5",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    # Verify output was created
    assert output_dir.exists()
    shard_path = output_dir / "shards" / "shard_000.jsonl"
    assert shard_path.exists()

    # Verify JSONL has records
    with shard_path.open() as f:
        lines = [line for line in f if line.strip()]
        assert len(lines) > 0
        assert len(lines) <= 5  # max-positions limit

