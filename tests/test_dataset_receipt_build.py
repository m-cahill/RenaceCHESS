"""Tests for dataset building from ingest receipts."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig
from renacechess.dataset.receipt_reader import (
    compute_pgn_digest,
    get_pgn_path_from_receipt,
    load_receipt_from_path,
)
from renacechess.contracts.models import (
    ArtifactRefV1,
    DerivedArtifactRefV1,
    IngestReceiptV1,
    ProvenanceV1,
    SourceArtifactRefV1,
)
from renacechess.determinism import stable_hash


def test_load_receipt_from_path(tmp_path: Path):
    """Test loading a receipt from a file path."""
    # Create a minimal receipt
    receipt = IngestReceiptV1(
        schema_version="v1",
        created_at=datetime.now(),
        source=SourceArtifactRefV1(
            uri="file:///test.pgn",
            resolved_uri=None,
            etag=None,
            last_modified=None,
            content_length=None,
        ),
        artifact=ArtifactRefV1(
            cache_path="test.pgn",
            sha256="a" * 64,
            size_bytes=100,
            media_type="application/x-chess-pgn",
            compression=None,
        ),
        derived=None,
        provenance=ProvenanceV1(
            tool_version="0.1.0",
            platform="test",
            python_version="3.11.0",
        ),
    )

    # Save receipt
    receipt_path = tmp_path / "receipt.json"
    receipt_dict = receipt.model_dump(mode="json", by_alias=True, exclude_none=True)
    receipt_path.write_text(json.dumps(receipt_dict, indent=2))

    # Load receipt
    loaded = load_receipt_from_path(receipt_path)
    assert loaded.schema_version == "v1"
    assert loaded.artifact.sha256 == "a" * 64


def test_get_pgn_path_from_receipt_with_decompressed(tmp_path: Path):
    """Test getting PGN path from receipt with decompressed artifact."""
    # Create a PGN file
    pgn_path = tmp_path / "test.pgn"
    pgn_path.write_text("1. e4 e5\n")

    # Create receipt with decompressed path
    receipt = IngestReceiptV1(
        schema_version="v1",
        created_at=datetime.now(),
        source=SourceArtifactRefV1(
            uri="file:///test.pgn.zst",
            resolved_uri=None,
            etag=None,
            last_modified=None,
            content_length=None,
        ),
        artifact=ArtifactRefV1(
            cache_path="test.pgn.zst",
            sha256="b" * 64,
            size_bytes=50,
            media_type="application/zstd",
            compression="zstd",
        ),
        derived=DerivedArtifactRefV1(
            decompressed_path=str(pgn_path),
            decompressed_sha256=compute_pgn_digest(pgn_path),
            decompressed_size_bytes=pgn_path.stat().st_size,
        ),
        provenance=ProvenanceV1(
            tool_version="0.1.0",
            platform="test",
            python_version="3.11.0",
        ),
    )

    # Save receipt
    receipt_path = tmp_path / "receipt.json"
    receipt_dict = receipt.model_dump(mode="json", by_alias=True, exclude_none=True)
    receipt_path.write_text(json.dumps(receipt_dict, indent=2))

    # Get PGN path (should use decompressed)
    resolved_path, digest = get_pgn_path_from_receipt(receipt_path)
    assert resolved_path == pgn_path
    assert digest == receipt.derived.decompressed_sha256


def test_get_pgn_path_from_receipt_compressed_error(tmp_path: Path):
    """Test that receipt pointing to compressed file without decompressed path raises error."""
    receipt = IngestReceiptV1(
        schema_version="v1",
        created_at=datetime.now(),
        source=SourceArtifactRefV1(
            uri="file:///test.pgn.zst",
            resolved_uri=None,
            etag=None,
            last_modified=None,
            content_length=None,
        ),
        artifact=ArtifactRefV1(
            cache_path="test.pgn.zst",
            sha256="c" * 64,
            size_bytes=50,
            media_type="application/zstd",
            compression="zstd",
        ),
        derived=None,  # No decompressed path
        provenance=ProvenanceV1(
            tool_version="0.1.0",
            platform="test",
            python_version="3.11.0",
        ),
    )

    # Save receipt
    receipt_path = tmp_path / "receipt.json"
    receipt_dict = receipt.model_dump(mode="json", by_alias=True, exclude_none=True)
    receipt_path.write_text(json.dumps(receipt_dict, indent=2))

    # Should raise ValueError
    with pytest.raises(ValueError, match="compressed PGN"):
        get_pgn_path_from_receipt(receipt_path)


def test_dataset_build_from_receipt(tmp_path: Path):
    """Test building dataset from an ingest receipt."""
    frozen_time = datetime(2024, 1, 1, 12, 0, 0)

    # Create a PGN file
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    pgn_digest = compute_pgn_digest(pgn_path)

    # Create receipt pointing to PGN (use absolute path for cache_path)
    receipt = IngestReceiptV1(
        schema_version="v1",
        created_at=datetime.now(),
        source=SourceArtifactRefV1(
            uri=f"file:///{pgn_path}",
            resolved_uri=None,
            etag=None,
            last_modified=None,
            content_length=None,
        ),
        artifact=ArtifactRefV1(
            cache_path=str(pgn_path.resolve()),  # Use absolute path
            sha256=pgn_digest,
            size_bytes=pgn_path.stat().st_size,
            media_type="application/x-chess-pgn",
            compression=None,
        ),
        derived=None,
        provenance=ProvenanceV1(
            tool_version="0.1.0",
            platform="test",
            python_version="3.11.0",
        ),
    )

    # Save receipt
    receipt_path = tmp_path / "receipt.json"
    receipt_dict = receipt.model_dump(mode="json", by_alias=True, exclude_none=True)
    receipt_path.write_text(json.dumps(receipt_dict, indent=2))

    # Build dataset from receipt
    config = DatasetBuildConfig(
        receipt_paths=[receipt_path],
        output_dir=tmp_path / "dataset",
        shard_size=10,
        max_positions=10,
    )
    build_dataset(config, generated_at=frozen_time)

    # Verify manifest
    manifest_path = tmp_path / "dataset" / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["schemaVersion"] == "v2"
    assert len(manifest["inputs"]) == 1
    assert manifest["inputs"][0]["type"] == "ingest_receipt"
    assert manifest["inputs"][0]["digest"] == pgn_digest


def test_compute_pgn_digest_line_ending_normalization(tmp_path: Path):
    """Test that PGN digest normalizes line endings."""
    # Create PGN with Windows line endings
    pgn_win = tmp_path / "test_win.pgn"
    pgn_win.write_bytes(b"1. e4 e5\r\n2. Nf3 Nc6\r\n")

    # Create PGN with Unix line endings
    pgn_unix = tmp_path / "test_unix.pgn"
    pgn_unix.write_bytes(b"1. e4 e5\n2. Nf3 Nc6\n")

    # Create PGN with mixed line endings
    pgn_mixed = tmp_path / "test_mixed.pgn"
    pgn_mixed.write_bytes(b"1. e4 e5\r\n2. Nf3 Nc6\n")

    # All should produce the same digest after normalization
    digest_win = compute_pgn_digest(pgn_win)
    digest_unix = compute_pgn_digest(pgn_unix)
    digest_mixed = compute_pgn_digest(pgn_mixed)

    assert digest_win == digest_unix == digest_mixed

