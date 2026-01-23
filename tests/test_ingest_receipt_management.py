"""Tests for receipt creation and management."""

from datetime import datetime
from pathlib import Path

import pytest

from renacechess.contracts.models import DerivedArtifactRefV1
from renacechess.ingest.cache import CacheManager
from renacechess.ingest.receipt import create_receipt, load_receipt, save_receipt
from renacechess.ingest.types import FetchResult


def test_create_receipt_minimal(tmp_path: Path) -> None:
    """Test creating minimal receipt."""
    cache = CacheManager(tmp_path)
    fetch_result = FetchResult(
        path=str(tmp_path / "artifact.pgn"),
        sha256="a" * 64,
        size_bytes=1000,
    )

    receipt = create_receipt(
        source_uri="file:///path/to/source.pgn",
        fetch_result=fetch_result,
        cache=cache,
        source_id="test123",
        media_type="application/x-chess-pgn",
    )

    assert receipt.schema_version == "v1"
    assert receipt.source.uri == "file:///path/to/source.pgn"
    assert receipt.artifact.sha256 == "a" * 64
    assert receipt.artifact.size_bytes == 1000
    assert receipt.derived is None


def test_create_receipt_with_metadata(tmp_path: Path) -> None:
    """Test creating receipt with HTTP metadata."""
    cache = CacheManager(tmp_path)
    fetch_result = FetchResult(
        path=str(tmp_path / "artifact.pgn.zst"),
        sha256="b" * 64,
        size_bytes=2000,
        etag='"etag123"',
        last_modified="Mon, 01 Jan 2024 12:00:00 GMT",
        content_length=2000,
    )

    receipt = create_receipt(
        source_uri="https://example.com/file.pgn.zst",
        fetch_result=fetch_result,
        cache=cache,
        source_id="test456",
        media_type="application/zstd",
        compression="zstd",
        resolved_uri="https://example.com/file.pgn.zst",
    )

    assert receipt.source.etag == '"etag123"'
    assert receipt.source.content_length == 2000
    assert receipt.artifact.compression == "zstd"
    assert receipt.source.resolved_uri == "https://example.com/file.pgn.zst"


def test_create_receipt_with_derived(tmp_path: Path) -> None:
    """Test creating receipt with derived artifact."""
    cache = CacheManager(tmp_path)
    fetch_result = FetchResult(
        path=str(tmp_path / "artifact.pgn.zst"),
        sha256="c" * 64,
        size_bytes=3000,
    )

    derived = DerivedArtifactRefV1(
        decompressed_path="cache/derived/test123/file.pgn",
        decompressed_sha256="d" * 64,
        decompressed_size_bytes=15000,
    )

    receipt = create_receipt(
        source_uri="file:///path/to/source.pgn.zst",
        fetch_result=fetch_result,
        cache=cache,
        source_id="test789",
        media_type="application/zstd",
        compression="zstd",
        derived=derived,
    )

    assert receipt.derived is not None
    assert receipt.derived.decompressed_sha256 == "d" * 64
    assert receipt.derived.decompressed_size_bytes == 15000


def test_create_receipt_with_timestamp_override(tmp_path: Path) -> None:
    """Test creating receipt with timestamp override (for testing)."""
    cache = CacheManager(tmp_path)
    fetch_result = FetchResult(
        path=str(tmp_path / "artifact.pgn"),
        sha256="e" * 64,
        size_bytes=1000,
    )

    fixed_time = datetime(2024, 1, 1, 12, 0, 0)

    receipt = create_receipt(
        source_uri="file:///path/to/source.pgn",
        fetch_result=fetch_result,
        cache=cache,
        source_id="test999",
        media_type="application/x-chess-pgn",
        created_at=fixed_time,
    )

    assert receipt.created_at == fixed_time


def test_save_and_load_receipt(tmp_path: Path) -> None:
    """Test saving and loading receipt."""
    cache = CacheManager(tmp_path)
    fetch_result = FetchResult(
        path=str(tmp_path / "artifact.pgn"),
        sha256="f" * 64,
        size_bytes=1000,
    )

    receipt = create_receipt(
        source_uri="file:///path/to/source.pgn",
        fetch_result=fetch_result,
        cache=cache,
        source_id="save_test",
        media_type="application/x-chess-pgn",
    )

    # Save receipt
    receipt_path = save_receipt(receipt, cache, "save_test")
    assert receipt_path.exists()

    # Load receipt
    loaded_receipt = load_receipt(cache, "save_test")

    assert loaded_receipt.schema_version == receipt.schema_version
    assert loaded_receipt.source.uri == receipt.source.uri
    assert loaded_receipt.artifact.sha256 == receipt.artifact.sha256
    assert loaded_receipt.created_at == receipt.created_at


def test_load_receipt_nonexistent(tmp_path: Path) -> None:
    """Test loading nonexistent receipt raises error."""
    cache = CacheManager(tmp_path)

    with pytest.raises(FileNotFoundError):
        load_receipt(cache, "nonexistent")
