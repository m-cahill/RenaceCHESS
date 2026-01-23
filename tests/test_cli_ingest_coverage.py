"""Targeted tests for CLI ingest command to raise coverage."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from renacechess.cli import main


def test_cli_ingest_lichess_success(tmp_path: Path, capsys, monkeypatch) -> None:
    """Test CLI ingest lichess command success path."""
    # Mock ingest_from_lichess to avoid network calls
    with patch("renacechess.cli.ingest_from_lichess") as mock_ingest:
        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "ingest",
                "lichess",
                "--month",
                "2024-01",
                "--out",
                str(tmp_path),
                "--cache-dir",
                str(tmp_path / "cache"),
            ],
        ):
            main()
            mock_ingest.assert_called_once()
            captured = capsys.readouterr()
            # Should not have error output
            assert "Error:" not in captured.err


def test_cli_ingest_url_success(tmp_path: Path, capsys) -> None:
    """Test CLI ingest url command success path."""
    source_file = tmp_path / "test.pgn"
    source_file.write_bytes(b"test content")

    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "ingest",
            "url",
            "--url",
            str(source_file),
            "--out",
            str(tmp_path / "out"),
            "--cache-dir",
            str(tmp_path / "cache"),
        ],
    ):
        main()
        captured = capsys.readouterr()
        # Should not have error output
        assert "Error:" not in captured.err


def test_cli_ingest_lichess_with_decompress(tmp_path: Path, capsys, monkeypatch) -> None:
    """Test CLI ingest lichess with decompress flag."""
    # Mock ingest_from_lichess to avoid network calls
    with patch("renacechess.cli.ingest_from_lichess") as mock_ingest:
        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "ingest",
                "lichess",
                "--month",
                "2024-01",
                "--out",
                str(tmp_path),
                "--cache-dir",
                str(tmp_path / "cache"),
                "--decompress",
            ],
        ):
            main()
            mock_ingest.assert_called_once()
            # Verify decompress=True was passed
            call_kwargs = mock_ingest.call_args[1]
            assert call_kwargs["decompress"] is True


def test_cli_ingest_url_with_decompress(tmp_path: Path, capsys) -> None:
    """Test CLI ingest url with decompress flag."""
    try:
        import zstandard  # noqa: F401
    except ImportError:
        pytest.skip("zstandard not available")

    # Create a valid .zst file
    import zstandard as zstd

    source_file = tmp_path / "test.pgn.zst"
    cctx = zstd.ZstdCompressor()
    compressed = cctx.compress(b"test pgn content")
    source_file.write_bytes(compressed)

    with patch.object(
        sys,
        "argv",
        [
            "renacechess",
            "ingest",
            "url",
            "--url",
            str(source_file),
            "--out",
            str(tmp_path / "out"),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--decompress",
        ],
    ):
        main()
        captured = capsys.readouterr()
        # Should not have error output
        assert "Error:" not in captured.err


def test_cli_ingest_invalid_subcommand(capsys) -> None:
    """Test CLI ingest with invalid subcommand."""
    with patch.object(sys, "argv", ["renacechess", "ingest", "invalid"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        # argparse returns exit code 2 for invalid arguments
        assert exc_info.value.code in (1, 2)
        captured = capsys.readouterr()
        # Should show help or error
        assert "ingest" in captured.out.lower() or "ingest" in captured.err.lower()
