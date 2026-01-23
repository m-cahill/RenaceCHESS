"""Tests for fetch operations (offline/deterministic)."""

from pathlib import Path

import pytest

from renacechess.ingest.cache import CacheManager
from renacechess.ingest.fetch import FileFetcher


def test_file_fetcher_local_path(tmp_path: Path) -> None:
    """Test FileFetcher with local file path."""
    # Create test file
    source_file = tmp_path / "source.pgn"
    test_data = b"test pgn content"
    source_file.write_bytes(test_data)

    cache = CacheManager(tmp_path / "cache")
    fetcher = FileFetcher(cache)

    result = fetcher.fetch(str(source_file), "test_id", "file.pgn")

    assert result.size_bytes == len(test_data)
    assert len(result.sha256) == 64  # SHA-256 hex length
    assert Path(result.path).exists()
    assert Path(result.path).read_bytes() == test_data


def test_file_fetcher_file_uri(tmp_path: Path) -> None:
    """Test FileFetcher with file:// URI."""
    source_file = tmp_path / "source.pgn"
    test_data = b"test pgn content"
    source_file.write_bytes(test_data)

    cache = CacheManager(tmp_path / "cache")
    fetcher = FileFetcher(cache)

    # Windows paths need special handling for file:// URIs
    if Path.cwd().drive:
        # Windows: file:///C:/path/to/file
        uri = f"file:///{source_file.as_posix()}"
    else:
        # Unix: file:///path/to/file
        uri = f"file://{source_file.as_posix()}"

    result = fetcher.fetch(uri, "test_id", "file.pgn")

    assert result.size_bytes == len(test_data)
    assert Path(result.path).exists()


def test_file_fetcher_nonexistent_file(tmp_path: Path) -> None:
    """Test FileFetcher raises error for nonexistent file."""
    cache = CacheManager(tmp_path / "cache")
    fetcher = FileFetcher(cache)

    with pytest.raises(FileNotFoundError):
        fetcher.fetch(str(tmp_path / "nonexistent.pgn"), "test_id", "file.pgn")


def test_file_fetcher_invalid_scheme(tmp_path: Path) -> None:
    """Test FileFetcher raises error for invalid URI scheme."""
    cache = CacheManager(tmp_path / "cache")
    fetcher = FileFetcher(cache)

    with pytest.raises(ValueError, match="FileFetcher only supports"):
        fetcher.fetch("https://example.com/file.pgn", "test_id", "file.pgn")


def test_file_fetcher_atomic_write(tmp_path: Path) -> None:
    """Test that FileFetcher uses atomic writes."""
    source_file = tmp_path / "source.pgn"
    test_data = b"test content"
    source_file.write_bytes(test_data)

    cache = CacheManager(tmp_path / "cache")
    fetcher = FileFetcher(cache)

    result = fetcher.fetch(str(source_file), "test_id", "file.pgn")

    # Temp file should not exist
    cache_path = Path(result.path)
    assert not cache_path.with_suffix(".pgn.tmp").exists()
