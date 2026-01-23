"""Tests for ingest receipt schema and models."""

import json
from datetime import datetime
from pathlib import Path

import jsonschema
import pytest

from renacechess.contracts.models import (
    ArtifactRefV1,
    DerivedArtifactRefV1,
    IngestReceiptV1,
    ProvenanceV1,
    SourceArtifactRefV1,
)
from renacechess.determinism import canonical_json_dump


def load_schema(schema_name: str) -> dict:
    """Load JSON schema from schemas directory."""
    schema_path = (
        Path(__file__).parent.parent
        / "src"
        / "renacechess"
        / "contracts"
        / "schemas"
        / "v1"
        / f"{schema_name}.schema.json"
    )
    return json.loads(schema_path.read_text())


def test_source_artifact_ref_v1_model() -> None:
    """Test SourceArtifactRefV1 model."""
    source = SourceArtifactRefV1(
        uri="https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst",
        resolved_uri="https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst",
        etag='"abc123"',
        last_modified=datetime(2024, 1, 1, 12, 0, 0),
        content_length=1000000,
    )
    assert source.uri.startswith("https://")
    assert source.etag == '"abc123"'
    assert source.content_length == 1000000

    # Test with minimal required fields
    source_minimal = SourceArtifactRefV1(uri="file:///path/to/file.pgn")
    assert source_minimal.resolved_uri is None
    assert source_minimal.etag is None


def test_artifact_ref_v1_model() -> None:
    """Test ArtifactRefV1 model."""
    artifact = ArtifactRefV1(
        cache_path="cache/sources/abc123/file.pgn.zst",
        sha256="a" * 64,
        size_bytes=1000000,
        media_type="application/zstd",
        compression="zstd",
    )
    assert artifact.sha256 == "a" * 64
    assert artifact.size_bytes == 1000000
    assert artifact.compression == "zstd"

    # Test without compression
    artifact_no_compression = ArtifactRefV1(
        cache_path="cache/sources/abc123/file.pgn",
        sha256="b" * 64,
        size_bytes=2000000,
        media_type="application/x-chess-pgn",
        compression=None,
    )
    assert artifact_no_compression.compression is None


def test_derived_artifact_ref_v1_model() -> None:
    """Test DerivedArtifactRefV1 model."""
    derived = DerivedArtifactRefV1(
        decompressed_path="cache/derived/abc123/file.pgn",
        decompressed_sha256="c" * 64,
        decompressed_size_bytes=5000000,
    )
    assert derived.decompressed_sha256 == "c" * 64
    assert derived.decompressed_size_bytes == 5000000


def test_provenance_v1_model() -> None:
    """Test ProvenanceV1 model."""
    provenance = ProvenanceV1(
        tool_version="0.1.0",
        platform="linux-x86_64",
        python_version="3.11.0",
    )
    assert provenance.tool_version == "0.1.0"
    assert provenance.platform == "linux-x86_64"

    # Test minimal provenance
    provenance_minimal = ProvenanceV1(tool_version="0.1.0")
    assert provenance_minimal.platform is None
    assert provenance_minimal.python_version is None


def test_ingest_receipt_v1_model() -> None:
    """Test IngestReceiptV1 model."""
    receipt = IngestReceiptV1(
        schema_version="v1",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        source=SourceArtifactRefV1(
            uri="https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst"
        ),
        artifact=ArtifactRefV1(
            cache_path="cache/sources/abc123/file.pgn.zst",
            sha256="a" * 64,
            size_bytes=1000000,
            media_type="application/zstd",
            compression="zstd",
        ),
        derived=None,
        provenance=ProvenanceV1(tool_version="0.1.0"),
    )
    assert receipt.schema_version == "v1"
    assert receipt.derived is None

    # Test with derived artifact
    receipt_with_derived = IngestReceiptV1(
        schema_version="v1",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        source=SourceArtifactRefV1(uri="file:///path/to/file.pgn.zst"),
        artifact=ArtifactRefV1(
            cache_path="cache/sources/abc123/file.pgn.zst",
            sha256="a" * 64,
            size_bytes=1000000,
            media_type="application/zstd",
            compression="zstd",
        ),
        derived=DerivedArtifactRefV1(
            decompressed_path="cache/derived/abc123/file.pgn",
            decompressed_sha256="c" * 64,
            decompressed_size_bytes=5000000,
        ),
        provenance=ProvenanceV1(tool_version="0.1.0"),
    )
    assert receipt_with_derived.derived is not None
    assert receipt_with_derived.derived.decompressed_sha256 == "c" * 64


def test_ingest_receipt_v1_schema_validation() -> None:
    """Test that IngestReceiptV1 validates against schema (roundtrip)."""
    receipt = IngestReceiptV1(
        schema_version="v1",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        source=SourceArtifactRefV1(
            uri="https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst",
            resolved_uri="https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst",
            etag='"abc123"',
        ),
        artifact=ArtifactRefV1(
            cache_path="cache/sources/abc123/file.pgn.zst",
            sha256="a" * 64,
            size_bytes=1000000,
            media_type="application/zstd",
            compression="zstd",
        ),
        derived=DerivedArtifactRefV1(
            decompressed_path="cache/derived/abc123/file.pgn",
            decompressed_sha256="c" * 64,
            decompressed_size_bytes=5000000,
        ),
        provenance=ProvenanceV1(
            tool_version="0.1.0",
            platform="linux-x86_64",
            python_version="3.11.0",
        ),
    )

    # Serialize to dict with aliases (camelCase JSON)
    receipt_dict = receipt.model_dump(mode="json", by_alias=True, exclude_none=True)

    # Should be JSON-serializable
    json_bytes = canonical_json_dump(receipt_dict)
    assert json_bytes is not None

    # Validate against schema
    schema = load_schema("ingest_receipt")
    jsonschema.validate(receipt_dict, schema)


def test_ingest_receipt_v1_minimal_schema_validation() -> None:
    """Test that minimal IngestReceiptV1 validates against schema."""
    receipt = IngestReceiptV1(
        schema_version="v1",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        source=SourceArtifactRefV1(uri="file:///path/to/file.pgn"),
        artifact=ArtifactRefV1(
            cache_path="cache/sources/abc123/file.pgn",
            sha256="a" * 64,
            size_bytes=1000000,
            media_type="application/x-chess-pgn",
        ),
        derived=None,
        provenance=ProvenanceV1(tool_version="0.1.0"),
    )

    receipt_dict = receipt.model_dump(mode="json", by_alias=True, exclude_none=True)
    schema = load_schema("ingest_receipt")
    jsonschema.validate(receipt_dict, schema)


def test_ingest_receipt_v1_sha256_validation() -> None:
    """Test that sha256 field validates pattern."""
    # Valid sha256 (64 hex chars)
    artifact = ArtifactRefV1(
        cache_path="cache/sources/abc123/file.pgn",
        sha256="a" * 64,
        size_bytes=1000000,
        media_type="application/x-chess-pgn",
    )
    assert artifact.sha256 == "a" * 64

    # Invalid sha256 (too short) - Pydantic should catch this via pattern
    with pytest.raises(Exception):  # Pydantic validation error
        ArtifactRefV1(
            cache_path="cache/sources/abc123/file.pgn",
            sha256="abc",  # Too short
            size_bytes=1000000,
            media_type="application/x-chess-pgn",
        )
