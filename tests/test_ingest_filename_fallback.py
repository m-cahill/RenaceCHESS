"""Test filename fallback logic in ingest_from_url."""

from pathlib import Path
from unittest.mock import Mock

from renacechess.ingest.ingest import ingest_from_url


def test_ingest_from_url_empty_filename_gets_fallback(tmp_path: Path) -> None:
    """Test that URL with empty filename gets fallback name."""
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"

    # Create a test file
    source_file = tmp_path / "test.pgn"
    source_file.write_bytes(b"test content")

    # Test that .zst files get correct media type
    source_zst = tmp_path / "test.pgn.zst"
    source_zst.write_bytes(b"compressed")

    # Test that .zst files get correct media type
    ingest_from_url(str(source_zst), output_dir, cache_dir)

    # Verify receipt has correct media type
    from renacechess.ingest.cache import CacheManager, compute_source_id
    from renacechess.ingest.receipt import load_receipt

    spec = {"url": str(source_zst), "resolvedUri": None}
    source_id = compute_source_id(spec)
    cache = CacheManager(cache_dir)
    receipt = load_receipt(cache, source_id)

    assert receipt.artifact.media_type == "application/zstd"
    assert receipt.artifact.compression == "zstd"
