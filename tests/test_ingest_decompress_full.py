"""Full coverage tests for decompress.py."""

from pathlib import Path

import pytest

from renacechess.ingest.cache import CacheManager
from renacechess.ingest.decompress import decompress_zst


def test_decompress_zst_full_coverage(tmp_path: Path) -> None:
    """Test full decompression path to cover all lines."""
    try:
        import zstandard  # type: ignore[import-not-found]
    except ImportError:
        pytest.skip("zstandard not available")

    cache = CacheManager(tmp_path / "cache")
    source_file = tmp_path / "source.pgn.zst"

    # Create a valid .zst file with substantial content
    import zstandard as zstd

    cctx = zstd.ZstdCompressor()
    test_content = b"test pgn content\n" * 100  # Make it large enough to trigger chunking
    compressed = cctx.compress(test_content)
    source_file.write_bytes(compressed)

    # Decompress - this should cover the full streaming path
    output_path, sha256, size = decompress_zst(source_file, cache, "test_id", "output.pgn")

    # Verify
    assert Path(output_path).exists()
    assert sha256 is not None
    assert len(sha256) == 64
    assert size == len(test_content)

    # Verify content matches
    decompressed_content = Path(output_path).read_bytes()
    assert decompressed_content == test_content

    # Verify it's in the derived directory
    assert "derived" in str(output_path)


def test_decompress_zst_error_cleanup_path(tmp_path: Path) -> None:
    """Test error cleanup path in decompress_zst."""
    try:
        import zstandard  # type: ignore[import-not-found]
    except ImportError:
        pytest.skip("zstandard not available")

    cache = CacheManager(tmp_path / "cache")
    source_file = tmp_path / "source.pgn.zst"

    # Create corrupted .zst file
    source_file.write_bytes(b"not valid zstd data")

    # Should raise exception and clean up temp file
    with pytest.raises(Exception):
        decompress_zst(source_file, cache, "test_id", "output.pgn")

    # Verify no temp file left
    derived_dir = cache.get_derived_dir("test_id")
    temp_files = list(derived_dir.glob("*.tmp")) if derived_dir.exists() else []
    assert len(temp_files) == 0

