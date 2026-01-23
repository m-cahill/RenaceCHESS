"""Tests for zstandard decompression."""

from pathlib import Path

import pytest

# Skip entire module if zstandard not available
try:
    import zstandard as zstd

    from renacechess.ingest.cache import CacheManager
    from renacechess.ingest.decompress import decompress_zst
except ImportError:
    pytestmark = pytest.mark.skip("zstandard not available")
    zstd = None  # type: ignore[assignment]
    CacheManager = None  # type: ignore[assignment,misc]
    decompress_zst = None  # type: ignore[assignment,misc]


def create_test_zst_file(path: Path, content: bytes) -> None:
    """Create a test .zst file with given content.

    Args:
        path: Path to create .zst file.
        content: Content to compress.
    """
    if zstd is None:
        pytest.skip("zstandard not available")
    cctx = zstd.ZstdCompressor()
    compressed = cctx.compress(content)
    path.write_bytes(compressed)


def test_decompress_zst(tmp_path: Path) -> None:
    """Test decompressing .zst file."""
    if zstd is None:
        pytest.skip("zstandard not available")
    # Create test compressed file
    test_content = b"test pgn content\n1. e4 e5\n"
    source_zst = tmp_path / "test.pgn.zst"
    create_test_zst_file(source_zst, test_content)

    cache = CacheManager(tmp_path / "cache")
    output_path, sha256, size_bytes = decompress_zst(source_zst, cache, "test_id", "test.pgn")

    # Verify output
    assert Path(output_path).exists()
    assert size_bytes == len(test_content)
    assert len(sha256) == 64  # SHA-256 hex length

    # Verify content
    decompressed_content = Path(output_path).read_bytes()
    assert decompressed_content == test_content

    # Verify hash matches
    from renacechess.determinism import stable_hash

    expected_hash = stable_hash(test_content)
    assert sha256 == expected_hash


def test_decompress_zst_nonexistent(tmp_path: Path) -> None:
    """Test decompressing nonexistent file raises error."""
    cache = CacheManager(tmp_path / "cache")
    nonexistent = tmp_path / "nonexistent.pgn.zst"

    with pytest.raises(FileNotFoundError):
        decompress_zst(nonexistent, cache, "test_id", "test.pgn")


def test_decompress_zst_invalid_extension(tmp_path: Path) -> None:
    """Test decompressing non-.zst file raises error."""
    # Create a regular file (not .zst)
    source_file = tmp_path / "test.pgn"
    source_file.write_bytes(b"test content")

    cache = CacheManager(tmp_path / "cache")

    with pytest.raises(ValueError, match="must have .zst extension"):
        decompress_zst(source_file, cache, "test_id", "test.pgn")


def test_decompress_zst_atomic_write(tmp_path: Path) -> None:
    """Test that decompression uses atomic writes."""
    test_content = b"test content"
    source_zst = tmp_path / "test.pgn.zst"
    create_test_zst_file(source_zst, test_content)

    cache = CacheManager(tmp_path / "cache")
    output_path, _, _ = decompress_zst(source_zst, cache, "test_id", "test.pgn")

    # Temp file should not exist
    output_file = Path(output_path)
    assert not output_file.with_suffix(".pgn.tmp").exists()


def test_decompress_zst_large_file(tmp_path: Path) -> None:
    """Test decompressing larger file (streaming)."""
    if zstd is None:
        pytest.skip("zstandard not available")
    # Create larger content (more than one chunk)
    large_content = b"test pgn content\n" * 1000
    source_zst = tmp_path / "large.pgn.zst"
    create_test_zst_file(source_zst, large_content)

    cache = CacheManager(tmp_path / "cache")
    output_path, sha256, size_bytes = decompress_zst(source_zst, cache, "test_id", "large.pgn")

    # Verify output
    assert size_bytes == len(large_content)
    decompressed_content = Path(output_path).read_bytes()
    assert decompressed_content == large_content

    # Verify hash
    from renacechess.determinism import stable_hash

    expected_hash = stable_hash(large_content)
    assert sha256 == expected_hash
