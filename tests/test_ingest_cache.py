"""Tests for cache management."""

from pathlib import Path

from renacechess.ingest.cache import CacheManager, compute_source_id


def test_compute_source_id() -> None:
    """Test deterministic source ID computation."""
    spec1 = {"preset": "standard_rated", "month": "2024-01"}
    spec2 = {"preset": "standard_rated", "month": "2024-01"}

    id1 = compute_source_id(spec1)
    id2 = compute_source_id(spec2)

    # Should be deterministic
    assert id1 == id2
    assert len(id1) == 16  # First 16 chars of hex hash

    # Different specs should produce different IDs
    spec3 = {"preset": "standard_rated", "month": "2024-02"}
    id3 = compute_source_id(spec3)
    assert id1 != id3


def test_cache_manager_initialization(tmp_path: Path) -> None:
    """Test cache manager creates directories."""
    cache = CacheManager(tmp_path)

    assert cache.cache_dir == tmp_path
    assert cache.sources_dir.exists()
    assert cache.receipts_dir.exists()
    assert cache.derived_dir.exists()


def test_cache_manager_paths(tmp_path: Path) -> None:
    """Test cache manager path methods."""
    cache = CacheManager(tmp_path)
    source_id = "abc123"

    source_dir = cache.get_source_dir(source_id)
    assert source_dir == tmp_path / "sources" / source_id

    receipt_path = cache.get_receipt_path(source_id)
    assert receipt_path == tmp_path / "receipts" / f"{source_id}.json"

    derived_dir = cache.get_derived_dir(source_id)
    assert derived_dir == tmp_path / "derived" / source_id


def test_atomic_write(tmp_path: Path) -> None:
    """Test atomic write functionality."""
    cache = CacheManager(tmp_path)
    target_path = tmp_path / "test" / "file.txt"
    data = b"test data"

    cache.atomic_write(target_path, data)

    assert target_path.exists()
    assert target_path.read_bytes() == data
    # Temp file should not exist
    assert not target_path.with_suffix(".txt.tmp").exists()


def test_atomic_write_json(tmp_path: Path) -> None:
    """Test atomic JSON write."""
    cache = CacheManager(tmp_path)
    target_path = tmp_path / "test.json"
    obj = {"key": "value", "number": 42}

    cache.atomic_write_json(target_path, obj)

    assert target_path.exists()
    loaded = target_path.read_text()
    assert '"key"' in loaded
    assert '"value"' in loaded
    assert '"number"' in loaded
    assert "42" in loaded
