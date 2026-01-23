"""Tests for CLI ingest command error handling."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from renacechess.cli import main


def test_cli_ingest_missing_subcommand(capsys) -> None:
    """Test that ingest command without subcommand shows help."""
    with patch.object(sys, "argv", ["renacechess", "ingest"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ingest" in captured.out.lower() or "ingest" in captured.err.lower()


def test_cli_ingest_lichess_missing_month(tmp_path: Path, capsys) -> None:
    """Test that lichess command with missing --month shows error."""
    with patch.object(sys, "argv", ["renacechess", "ingest", "lichess", "--out", str(tmp_path)]):
        with pytest.raises(SystemExit):
            main()
        # argparse will show error about missing required argument


def test_cli_ingest_lichess_missing_out(tmp_path: Path, capsys) -> None:
    """Test that lichess command with missing --out shows error."""
    with patch.object(sys, "argv", ["renacechess", "ingest", "lichess", "--month", "2024-01"]):
        with pytest.raises(SystemExit):
            main()
        # argparse will show error about missing required argument


def test_cli_ingest_url_missing_url(tmp_path: Path, capsys) -> None:
    """Test that url command with missing --url shows error."""
    with patch.object(sys, "argv", ["renacechess", "ingest", "url", "--out", str(tmp_path)]):
        with pytest.raises(SystemExit):
            main()
        # argparse will show error about missing required argument


def test_cli_ingest_url_missing_out(tmp_path: Path, capsys) -> None:
    """Test that url command with missing --out shows error."""
    with patch.object(sys, "argv", ["renacechess", "ingest", "url", "--url", "file:///test.pgn"]):
        with pytest.raises(SystemExit):
            main()
        # argparse will show error about missing required argument


def test_cli_ingest_lichess_invalid_month(tmp_path: Path, capsys) -> None:
    """Test that lichess command with invalid month format raises error."""
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "ingest",
            "lichess",
            "--month",
            "invalid",
            "--out",
            str(tmp_path),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "error" in captured.err.lower() or "invalid" in captured.err.lower()


def test_cli_ingest_url_nonexistent_file(tmp_path: Path, capsys) -> None:
    """Test that url command with nonexistent file raises error."""
    nonexistent = tmp_path / "nonexistent.pgn"
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "ingest",
            "url",
            "--url",
            str(nonexistent),
            "--out",
            str(tmp_path),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "error" in captured.err.lower() or "not found" in captured.err.lower()


def test_cli_ingest_invalid_subcommand(capsys) -> None:
    """Test that invalid ingest subcommand shows error."""
    with patch.object(sys, "argv", ["renacechess", "ingest", "invalid"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        # argparse returns exit code 2 for invalid arguments
        assert exc_info.value.code in (1, 2)
        captured = capsys.readouterr()
        assert "invalid" in captured.err.lower() or "ingest" in captured.out.lower()


def test_cli_ingest_lichess_exception_handling(tmp_path: Path, capsys, monkeypatch) -> None:
    """Test that lichess command exception handling works."""
    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "ingest",
            "lichess",
            "--month",
            "invalid-month",
            "--out",
            str(tmp_path),
        ],
    ):
        # Use invalid month to trigger ValueError in build_lichess_url
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()


def test_cli_ingest_url_exception_handling(tmp_path: Path, capsys) -> None:
    """Test that url command exception handling works."""
    nonexistent = tmp_path / "nonexistent.pgn"

    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "ingest",
            "url",
            "--url",
            str(nonexistent),
            "--out",
            str(tmp_path),
        ],
    ):
        # Use nonexistent file to trigger FileNotFoundError
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()


def test_cli_no_command(capsys) -> None:
    """Test that no command shows help."""
    with patch.object(sys, "argv", ["renacechess"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "renacechess" in captured.out.lower() or "renacechess" in captured.err.lower()
