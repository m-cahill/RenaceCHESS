"""Tests for decompression error paths."""

from pathlib import Path

import pytest

from renacechess.ingest.cache import CacheManager
from renacechess.ingest.decompress import decompress_zst


def test_decompress_zst_nonexistent_file(tmp_path: Path) -> None:
    """Test that nonexistent file raises FileNotFoundError."""
    cache = CacheManager(tmp_path / "cache")
    nonexistent = tmp_path / "nonexistent.pgn.zst"

    with pytest.raises(FileNotFoundError, match="not found"):
        decompress_zst(nonexistent, cache, "test_id", "output.pgn")


def test_decompress_zst_invalid_extension(tmp_path: Path) -> None:
    """Test that non-.zst file raises ValueError."""
    cache = CacheManager(tmp_path / "cache")
    source_file = tmp_path / "source.pgn"
    source_file.write_bytes(b"test content")

    with pytest.raises(ValueError, match="must have .zst extension"):
        decompress_zst(source_file, cache, "test_id", "output.pgn")


def test_decompress_zst_missing_zstandard(tmp_path: Path, monkeypatch) -> None:
    """Test that missing zstandard raises ImportError."""
    cache = CacheManager(tmp_path / "cache")
    source_file = tmp_path / "source.pgn.zst"
    source_file.write_bytes(b"fake zst content")

    # Mock zstandard to be None
    import sys

    if "renacechess.ingest.decompress" in sys.modules:

        import renacechess.ingest.decompress as decompress_module

        # Temporarily set zstd to None
        original_zstd = decompress_module.zstd
        decompress_module.zstd = None

        try:
            with pytest.raises(ImportError, match="zstandard"):
                decompress_zst(source_file, cache, "test_id", "output.pgn")
        finally:
            # Restore original
            decompress_module.zstd = original_zstd

