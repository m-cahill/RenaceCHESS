"""Tests for CLI ingest commands (offline/deterministic)."""

from pathlib import Path

import pytest

from renacechess.ingest.ingest import ingest_from_url


def test_ingest_from_url_local_file(tmp_path: Path) -> None:
    """Test ingesting from local file path."""
    # Create test file
    source_file = tmp_path / "source.pgn"
    test_content = b"test pgn content\n1. e4 e5\n"
    source_file.write_bytes(test_content)

    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"

    # Ingest from local file
    ingest_from_url(str(source_file), output_dir, cache_dir)

    # Verify receipt was created
    receipt_files = list(output_dir.glob("*.json"))
    assert len(receipt_files) == 1

    # Verify cached artifact exists
    from renacechess.ingest.receipt import load_receipt
    from renacechess.ingest.cache import CacheManager

    cache = CacheManager(cache_dir)
    receipt = load_receipt(cache, receipt_files[0].stem)

    assert receipt.source.uri == str(source_file)
    assert receipt.artifact.sha256 is not None
    assert receipt.artifact.size_bytes == len(test_content)


def test_ingest_from_url_file_uri(tmp_path: Path) -> None:
    """Test ingesting from file:// URI."""
    # Create test file
    source_file = tmp_path / "source.pgn"
    test_content = b"test content"
    source_file.write_bytes(test_content)

    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"

    # Use file:// URI
    if Path.cwd().drive:
        # Windows
        uri = f"file:///{source_file.as_posix()}"
    else:
        # Unix
        uri = f"file://{source_file.as_posix()}"

    ingest_from_url(uri, output_dir, cache_dir)

    # Verify receipt
    receipt_files = list(output_dir.glob("*.json"))
    assert len(receipt_files) == 1


def test_ingest_cache_hit(tmp_path: Path) -> None:
    """Test that cache hit works (ingest same source twice)."""
    source_file = tmp_path / "source.pgn"
    test_content = b"test content"
    source_file.write_bytes(test_content)

    cache_dir = tmp_path / "cache"
    output_dir1 = tmp_path / "output1"
    output_dir2 = tmp_path / "output2"

    # First ingest
    ingest_from_url(str(source_file), output_dir1, cache_dir)
    receipt1_files = list(output_dir1.glob("*.json"))
    assert len(receipt1_files) == 1

    # Second ingest (should be cache hit)
    ingest_from_url(str(source_file), output_dir2, cache_dir)
    receipt2_files = list(output_dir2.glob("*.json"))
    assert len(receipt2_files) == 1

    # Both receipts should have same source_id
    assert receipt1_files[0].stem == receipt2_files[0].stem


def test_ingest_from_lichess_url_builder() -> None:
    """Test that lichess URL builder works correctly."""
    from renacechess.ingest import build_lichess_url

    # Verify URL building
    expected_url = build_lichess_url("standard_rated", "2024-01")
    assert expected_url == "https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst"

    # Test different months
    url2 = build_lichess_url("standard_rated", "2023-12")
    assert url2 == "https://database.lichess.org/standard/lichess_db_standard_rated_2023-12.pgn.zst"


def test_ingest_invalid_month_format() -> None:
    """Test that invalid month format raises error."""
    from renacechess.ingest.lichess import build_lichess_url

    with pytest.raises(ValueError):
        build_lichess_url("standard_rated", "invalid")

    with pytest.raises(ValueError):
        build_lichess_url("standard_rated", "2024-13")

