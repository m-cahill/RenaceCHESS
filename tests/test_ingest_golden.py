"""Golden file regression test for ingest receipts."""

from datetime import datetime
from pathlib import Path

import pytest

from renacechess.determinism import canonical_json_dump
from renacechess.ingest.cache import CacheManager
from renacechess.ingest.ingest import ingest_from_url
from renacechess.ingest.receipt import load_receipt


def sample_pgn_path() -> Path:
    """Get path to sample PGN fixture."""
    return Path(__file__).parent / "data" / "sample_lichess_small.pgn"


def test_ingest_receipt_golden(tmp_path: Path) -> None:
    """Test that ingest receipt matches golden file (with frozen timestamp)."""
    pgn_path = sample_pgn_path()
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output"

    # Ingest with frozen timestamp for determinism
    # Note: We can't easily freeze the timestamp in ingest_from_url,
    # so we'll create the receipt manually with a fixed timestamp
    from renacechess.ingest.cache import compute_source_id
    from renacechess.ingest.fetch import FileFetcher
    from renacechess.ingest.receipt import create_receipt, save_receipt

    cache = CacheManager(cache_dir)
    fetcher = FileFetcher(cache)

    # Compute source_id
    spec = {"url": str(pgn_path), "resolvedUri": None}
    source_id = compute_source_id(spec)

    # Fetch
    fetch_result = fetcher.fetch(str(pgn_path), source_id, "sample_lichess_small.pgn")

    # Create receipt with frozen timestamp
    fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=None)
    receipt = create_receipt(
        source_uri=str(pgn_path),
        fetch_result=fetch_result,
        cache=cache,
        source_id=source_id,
        media_type="application/x-chess-pgn",
        created_at=fixed_time,
    )

    # Save receipt
    save_receipt(receipt, cache, source_id)

    # Copy to output
    import shutil

    receipt_path = cache.get_receipt_path(source_id)
    output_receipt_path = output_dir / f"{source_id}.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(receipt_path, output_receipt_path)

    # Serialize to canonical JSON
    receipt_dict = receipt.model_dump(mode="json", by_alias=True, exclude_none=True)
    canonical_json = canonical_json_dump(receipt_dict).decode("utf-8")

    # Load golden file if it exists, otherwise create it
    golden_path = Path(__file__).parent / "golden" / "ingest_receipt.v1.json"
    golden_path.parent.mkdir(parents=True, exist_ok=True)

    if golden_path.exists():
        # Compare with golden
        golden_content = golden_path.read_text(encoding="utf-8")
        # Parse both to compare (JSON may have different formatting)
        import json

        golden_dict = json.loads(golden_content)
        receipt_dict_parsed = json.loads(canonical_json)

        # Compare key fields (excluding timestamps and paths which may vary by platform)
        assert receipt_dict_parsed["schemaVersion"] == golden_dict["schemaVersion"]
        # URI may differ by platform (Windows vs Unix paths), so compare only filename
        receipt_uri = receipt_dict_parsed["source"]["uri"]
        golden_uri = golden_dict["source"]["uri"]
        # Extract filename from both paths (handle both Windows and Unix)
        receipt_filename = Path(receipt_uri).name
        golden_filename = Path(golden_uri).name
        assert receipt_filename == golden_filename, (
            f"Filename mismatch: {receipt_filename} != {golden_filename}"
        )
        assert receipt_dict_parsed["artifact"]["sha256"] == golden_dict["artifact"]["sha256"]
        assert receipt_dict_parsed["artifact"]["sizeBytes"] == golden_dict["artifact"]["sizeBytes"]
    else:
        # Create golden file (first run)
        golden_path.write_text(canonical_json, encoding="utf-8")
        pytest.skip(f"Created golden file at {golden_path}. Re-run test to verify.")


def test_ingest_receipt_deterministic(tmp_path: Path) -> None:
    """Test that receipts are deterministic (same input produces same receipt)."""
    pgn_path = sample_pgn_path()
    cache_dir1 = tmp_path / "cache1"
    cache_dir2 = tmp_path / "cache2"
    output_dir1 = tmp_path / "output1"
    output_dir2 = tmp_path / "output2"

    # Ingest twice with different cache dirs but same source
    ingest_from_url(str(pgn_path), output_dir1, cache_dir1)
    ingest_from_url(str(pgn_path), output_dir2, cache_dir2)

    # Load receipts
    receipt1_files = list(output_dir1.glob("*.json"))
    receipt2_files = list(output_dir2.glob("*.json"))
    assert len(receipt1_files) == 1
    assert len(receipt2_files) == 1

    cache1 = CacheManager(cache_dir1)
    cache2 = CacheManager(cache_dir2)

    receipt1 = load_receipt(cache1, receipt1_files[0].stem)
    receipt2 = load_receipt(cache2, receipt2_files[0].stem)

    # Verify source_id is same (deterministic)
    assert receipt1_files[0].stem == receipt2_files[0].stem

    # Verify artifact hashes are same
    assert receipt1.artifact.sha256 == receipt2.artifact.sha256
    assert receipt1.artifact.size_bytes == receipt2.artifact.size_bytes
