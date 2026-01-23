"""Tests for CLI module."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from renacechess.cli import main


def test_cli_demo_command(tmp_path: Path, capsys) -> None:
    """Test CLI demo command."""
    sample_pgn = Path(__file__).parent / "data" / "sample.pgn"
    output_file = tmp_path / "demo.json"

    with patch.object(sys, "argv", ["renacechess", "demo", "--pgn", str(sample_pgn), "--out", str(output_file)]):
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

    with patch.object(sys, "argv", ["renacechess", "demo", "--pgn", str(sample_pgn), "--out", str(output_file), "--ply", "10"]):
        main()

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    payload = json.loads(content)
    assert "position" in payload

