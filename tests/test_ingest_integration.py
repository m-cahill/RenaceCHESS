"""Integration tests for ingestion (using fixtures)."""

from pathlib import Path

import pytest

from renacechess.ingest.cache import CacheManager
from renacechess.ingest.ingest import ingest_from_url
from renacechess.ingest.receipt import load_receipt


def sample_pgn_path() -> Path:
    """Get path to sample PGN fixture."""
    return Path(__file__).parent / "data" / "sample_lichess_small.pgn"


def create_zst_fixture(pgn_path: Path, zst_path: Path) -> None:
    """Create .zst fixture from PGN file if zstandard is available."""
    try:
        import zstandard as zstd

        content = pgn_path.read_bytes()
        cctx = zstd.ZstdCompressor()
        compressed = cctx.compress(content)
        zst_path.write_bytes(compressed)
    except ImportError:
        pytest.skip("zstandard not available")


def test_ingest_file_receipt_schema(tmp_path: Path) -> None:
    """Test that ingested file produces valid receipt with correct schema."""
    pgn_path = sample_pgn_path()
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"

    # Ingest from local path
    ingest_from_url(str(pgn_path), output_dir, cache_dir)

    # Verify receipt exists and is valid
    receipt_files = list(output_dir.glob("*.json"))
    assert len(receipt_files) == 1

    # Load and validate receipt
    cache = CacheManager(cache_dir)
    receipt = load_receipt(cache, receipt_files[0].stem)

    # Verify receipt structure
    assert receipt.schema_version == "v1"
    assert receipt.source.uri == str(pgn_path)
    assert receipt.artifact.sha256 is not None
    assert len(receipt.artifact.sha256) == 64
    assert receipt.artifact.size_bytes > 0
    assert receipt.artifact.media_type == "application/x-chess-pgn"

    # Verify receipt validates against schema
    import json

    import jsonschema

    receipt_dict = receipt.model_dump(mode="json", by_alias=True, exclude_none=True)
    schema_path = (
        Path(__file__).parent.parent
        / "src"
        / "renacechess"
        / "contracts"
        / "schemas"
        / "v1"
        / "ingest_receipt.schema.json"
    )
    schema = json.loads(schema_path.read_text())
    jsonschema.validate(receipt_dict, schema)

    # Verify SHA matches expected
    from renacechess.determinism import stable_hash

    expected_sha = stable_hash(pgn_path.read_bytes())
    assert receipt.artifact.sha256 == expected_sha


def test_ingest_zst_decompress(tmp_path: Path) -> None:
    """Test ingesting .zst fixture with decompression."""
    pgn_path = sample_pgn_path()
    zst_path = pgn_path.with_suffix(".pgn.zst")

    # Create .zst fixture if needed
    create_zst_fixture(pgn_path, zst_path)
    if not zst_path.exists():
        pytest.skip("zstandard not available to create fixture")

    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"

    # Ingest with decompression
    ingest_from_url(str(zst_path), output_dir, cache_dir, decompress=True)

    # Verify receipt
    receipt_files = list(output_dir.glob("*.json"))
    assert len(receipt_files) == 1

    cache = CacheManager(cache_dir)
    receipt = load_receipt(cache, receipt_files[0].stem)

    # Verify derived artifact exists
    assert receipt.derived is not None
    assert receipt.derived.decompressed_sha256 is not None
    assert len(receipt.derived.decompressed_sha256) == 64
    assert receipt.derived.decompressed_size_bytes > 0

    # Verify decompressed file exists and matches original
    decompressed_path = cache_dir / receipt.derived.decompressed_path
    assert decompressed_path.exists()

    decompressed_content = decompressed_path.read_bytes()
    original_content = pgn_path.read_bytes()

    assert decompressed_content == original_content

    # Verify decompressed SHA matches original
    from renacechess.determinism import stable_hash

    expected_decompressed_sha = stable_hash(original_content)
    assert receipt.derived.decompressed_sha256 == expected_decompressed_sha


def test_ingest_cache_hit_deterministic(tmp_path: Path) -> None:
    """Test that cache hit produces deterministic receipt."""
    pgn_path = sample_pgn_path()
    cache_dir = tmp_path / "cache"
    output_dir1 = tmp_path / "output1"
    output_dir2 = tmp_path / "output2"

    # First ingest
    ingest_from_url(str(pgn_path), output_dir1, cache_dir)
    receipt1_files = list(output_dir1.glob("*.json"))
    assert len(receipt1_files) == 1

    cache = CacheManager(cache_dir)
    receipt1 = load_receipt(cache, receipt1_files[0].stem)

    # Second ingest (cache hit)
    ingest_from_url(str(pgn_path), output_dir2, cache_dir)
    receipt2_files = list(output_dir2.glob("*.json"))
    assert len(receipt2_files) == 1

    receipt2 = load_receipt(cache, receipt2_files[0].stem)

    # Verify same source_id
    assert receipt1_files[0].stem == receipt2_files[0].stem

    # Verify receipts are identical (deterministic)
    assert receipt1.artifact.sha256 == receipt2.artifact.sha256
    assert receipt1.artifact.size_bytes == receipt2.artifact.size_bytes
    assert receipt1.source.uri == receipt2.source.uri

    # Verify no rewrite occurred (cache hit message should appear, but we can't easily test that)


def test_cli_ingest_smoke(tmp_path: Path) -> None:
    """Test CLI ingest command against fixture (smoke test)."""
    pgn_path = sample_pgn_path()
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"

    # Test ingest_from_url (which is what CLI calls)
    ingest_from_url(str(pgn_path), output_dir, cache_dir)

    # Verify output files exist
    receipt_files = list(output_dir.glob("*.json"))
    assert len(receipt_files) == 1

    # Verify receipt is parseable
    import json

    receipt_data = json.loads(receipt_files[0].read_text())
    assert receipt_data["schemaVersion"] == "v1"
    assert "source" in receipt_data
    assert "artifact" in receipt_data
    assert "provenance" in receipt_data

    # Verify cached artifact exists
    cache = CacheManager(cache_dir)
    receipt = load_receipt(cache, receipt_files[0].stem)
    artifact_path = cache_dir / receipt.artifact.cache_path
    assert artifact_path.exists()
