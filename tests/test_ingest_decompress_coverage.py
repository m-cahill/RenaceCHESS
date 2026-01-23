"""Targeted tests for decompress.py to raise coverage."""

from pathlib import Path

import pytest

from renacechess.ingest.cache import CacheManager
from renacechess.ingest.decompress import decompress_zst


def test_decompress_zst_full_path(tmp_path: Path) -> None:
    """Test full decompression path with valid .zst file."""
    try:
        import zstandard  # noqa: F401
    except ImportError:
        pytest.skip("zstandard not available")

    cache = CacheManager(tmp_path / "cache")
    source_file = tmp_path / "source.pgn.zst"

    # Create a valid .zst file
    import zstandard as zstd

    cctx = zstd.ZstdCompressor()
    test_content = b"test pgn content\n1. e4 e5\n2. Nf3 Nc6\n"
    compressed = cctx.compress(test_content)
    source_file.write_bytes(compressed)

    # Decompress
    output_path, sha256, size = decompress_zst(source_file, cache, "test_id", "output.pgn")

    # Verify
    assert Path(output_path).exists()
    assert sha256 is not None
    assert len(sha256) == 64  # SHA-256 hex length
    assert size == len(test_content)

    # Verify decompressed content
    decompressed_content = Path(output_path).read_bytes()
    assert decompressed_content == test_content


def test_decompress_zst_error_cleanup(tmp_path: Path) -> None:
    """Test that temp file is cleaned up on error."""
    try:
        import zstandard  # noqa: F401
    except ImportError:
        pytest.skip("zstandard not available")

    cache = CacheManager(tmp_path / "cache")
    source_file = tmp_path / "source.pgn.zst"

    # Create corrupted .zst file (invalid zstd data)
    source_file.write_bytes(b"not valid zstd data")

    # Decompress should fail and clean up temp file
    with pytest.raises(Exception):  # zstd will raise an error
        decompress_zst(source_file, cache, "test_id", "output.pgn")

    # Verify no temp file left behind
    temp_files = list(cache.get_derived_dir("test_id").glob("*.tmp"))
    assert len(temp_files) == 0

