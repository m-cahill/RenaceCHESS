"""Tests for ingest orchestration error paths and edge cases."""

from pathlib import Path

import pytest

from renacechess.ingest.cache import CacheManager, compute_source_id
from renacechess.ingest.ingest import ingest_from_url
from renacechess.ingest.receipt import load_receipt


def test_ingest_from_url_cache_hit(tmp_path: Path) -> None:
    """Test that cache hit path is used when receipt exists."""
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"

    # Create a test file
    source_file = tmp_path / "source.pgn"
    source_file.write_bytes(b"test content")

    # First ingestion
    ingest_from_url(str(source_file), output_dir, cache_dir)

    # Second ingestion should hit cache
    ingest_from_url(str(source_file), output_dir, cache_dir)

    # Verify receipt exists
    spec = {"url": str(source_file), "resolvedUri": None}
    source_id = compute_source_id(spec)
    cache = CacheManager(cache_dir)
    receipt = load_receipt(cache, source_id)
    assert receipt is not None
    assert receipt.source.uri == str(source_file)


def test_ingest_from_url_nonexistent_file(tmp_path: Path) -> None:
    """Test that nonexistent file raises FileNotFoundError."""
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"
    nonexistent = tmp_path / "nonexistent.pgn"

    with pytest.raises(FileNotFoundError, match="not found"):
        ingest_from_url(str(nonexistent), output_dir, cache_dir)


def test_ingest_from_url_unsupported_scheme(tmp_path: Path) -> None:
    """Test that unsupported URL scheme raises ValueError."""
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"

    with pytest.raises(ValueError, match="Unsupported URL scheme"):
        ingest_from_url("ftp://example.com/file.pgn", output_dir, cache_dir)


def test_ingest_from_url_decompress_missing_zstandard(tmp_path: Path) -> None:
    """Test that decompress without zstandard raises ImportError when zstd is None."""
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"

    # Create a test .zst file
    source_file = tmp_path / "source.pgn.zst"
    source_file.write_bytes(b"fake zst content")

    # Temporarily set zstd to None in decompress module
    from renacechess.ingest import decompress

    original_zstd = decompress.zstd
    try:
        decompress.zstd = None
        with pytest.raises(ImportError, match="zstandard"):
            ingest_from_url(str(source_file), output_dir, cache_dir, decompress=True)
    finally:
        decompress.zstd = original_zstd


def test_ingest_from_url_artifact_not_found_after_fetch(tmp_path: Path) -> None:
    """Test that missing artifact after fetch raises FileNotFoundError."""
    try:
        import zstandard  # noqa: F401
    except ImportError:
        pytest.skip("zstandard not available")

    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"

    # Create a test .zst file
    source_file = tmp_path / "source.pgn.zst"
    import zstandard as zstd

    cctx = zstd.ZstdCompressor()
    compressed = cctx.compress(b"test content")
    source_file.write_bytes(compressed)

    # First ingest normally (without decompress)
    ingest_from_url(str(source_file), output_dir, cache_dir)

    # Now try to decompress with a corrupted receipt path
    from renacechess.ingest.cache import CacheManager, compute_source_id
    from renacechess.ingest.receipt import load_receipt, save_receipt

    spec = {"url": str(source_file), "resolvedUri": None}
    source_id = compute_source_id(spec)
    cache = CacheManager(cache_dir)
    receipt = load_receipt(cache, source_id)

    # Corrupt the cache path to point to nonexistent file
    receipt.artifact.cache_path = "nonexistent/path.pgn.zst"
    save_receipt(receipt, cache, source_id)

    # Now try to decompress - should fail when looking for artifact
    with pytest.raises(FileNotFoundError, match="not found"):
        ingest_from_url(str(source_file), output_dir, cache_dir, decompress=True)


def test_ingest_from_url_decompress_non_zstd(tmp_path: Path) -> None:
    """Test that decompress on non-.zst file is skipped."""
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"

    # Create a test .pgn file (not .zst)
    source_file = tmp_path / "source.pgn"
    source_file.write_bytes(b"test pgn content")

    # Ingest with decompress=True (should be ignored for non-.zst)
    ingest_from_url(str(source_file), output_dir, cache_dir, decompress=True)

    # Verify receipt was created without derived artifact
    from renacechess.ingest.cache import CacheManager, compute_source_id
    from renacechess.ingest.receipt import load_receipt

    spec = {"url": str(source_file), "resolvedUri": None}
    source_id = compute_source_id(spec)
    cache = CacheManager(cache_dir)
    receipt = load_receipt(cache, source_id)

    assert receipt.derived is None  # No decompression for non-.zst


def test_ingest_from_url_absolute_path_fallback(tmp_path: Path) -> None:
    """Test that absolute path fallback works when relative path doesn't exist."""
    try:
        import zstandard  # noqa: F401
    except ImportError:
        pytest.skip("zstandard not available")

    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"

    # Create a test .zst file
    source_file = tmp_path / "source.pgn.zst"
    # Create a valid .zst file
    import zstandard as zstd

    cctx = zstd.ZstdCompressor()
    compressed = cctx.compress(b"test pgn content\n1. e4 e5\n")
    source_file.write_bytes(compressed)

    # Ingest first time (without decompress)
    ingest_from_url(str(source_file), output_dir, cache_dir)

    # Now modify receipt to have absolute path instead of relative
    from renacechess.ingest.cache import CacheManager, compute_source_id
    from renacechess.ingest.receipt import load_receipt, save_receipt

    spec = {"url": str(source_file), "resolvedUri": None}
    source_id = compute_source_id(spec)
    cache = CacheManager(cache_dir)
    receipt = load_receipt(cache, source_id)

    # Set cache_path to absolute path (simulating case where relative path doesn't work)
    receipt.artifact.cache_path = str(source_file)
    save_receipt(receipt, cache, source_id)

    # Now decompress should work with absolute path fallback
    ingest_from_url(str(source_file), output_dir, cache_dir, decompress=True)

    # Verify decompressed file exists
    receipt2 = load_receipt(cache, source_id)
    assert receipt2.derived is not None
    assert receipt2.derived.decompressed_sha256 is not None
