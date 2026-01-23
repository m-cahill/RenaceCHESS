"""Test error paths in cache.py."""

from pathlib import Path
from unittest.mock import patch

import pytest

from renacechess.ingest.cache import CacheManager


def test_atomic_write_error_cleanup(tmp_path: Path) -> None:
    """Test that atomic_write cleans up temp file on error."""
    cache = CacheManager(tmp_path)
    target_path = tmp_path / "test" / "file.txt"
    data = b"test data"

    # Mock Path.replace to raise an exception
    with patch.object(Path, "replace", side_effect=OSError("Permission denied")):
        with pytest.raises(OSError):
            cache.atomic_write(target_path, data)

        # Verify temp file was cleaned up
        temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
        assert not temp_path.exists()

