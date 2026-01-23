"""Cache management for ingested artifacts."""

import json
from pathlib import Path
from typing import Any

from renacechess.determinism import canonical_hash


def compute_source_id(spec: dict[str, Any]) -> str:
    """Compute deterministic source ID from specification.

    Args:
        spec: Source specification dict (preset/url, month, resolvedUri).

    Returns:
        First 16 characters of SHA-256 hash (hex).
    """
    return canonical_hash(spec)[:16]


class CacheManager:
    """Manages cache layout and atomic writes."""

    def __init__(self, cache_dir: Path) -> None:
        """Initialize cache manager.

        Args:
            cache_dir: Root cache directory.
        """
        self.cache_dir = Path(cache_dir)
        self.sources_dir = self.cache_dir / "sources"
        self.receipts_dir = self.cache_dir / "receipts"
        self.derived_dir = self.cache_dir / "derived"

        # Create directories
        self.sources_dir.mkdir(parents=True, exist_ok=True)
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        self.derived_dir.mkdir(parents=True, exist_ok=True)

    def get_source_dir(self, source_id: str) -> Path:
        """Get directory for a source ID.

        Args:
            source_id: Source identifier.

        Returns:
            Path to source directory.
        """
        return self.sources_dir / source_id

    def get_receipt_path(self, source_id: str) -> Path:
        """Get receipt path for a source ID.

        Args:
            source_id: Source identifier.

        Returns:
            Path to receipt file.
        """
        return self.receipts_dir / f"{source_id}.json"

    def get_derived_dir(self, source_id: str) -> Path:
        """Get directory for derived artifacts (e.g., decompressed).

        Args:
            source_id: Source identifier.

        Returns:
            Path to derived directory.
        """
        return self.derived_dir / source_id

    def atomic_write(self, path: Path, data: bytes) -> None:
        """Write data atomically (write to temp file, then rename).

        Args:
            path: Target file path.
            path.parent.mkdir(parents=True, exist_ok=True)
            data: Data to write.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        try:
            temp_path.write_bytes(data)
            temp_path.replace(path)
        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise

    def atomic_write_json(self, path: Path, obj: Any) -> None:
        """Write JSON object atomically.

        Args:
            path: Target file path.
            obj: JSON-serializable object.
        """
        json_bytes = json.dumps(obj, sort_keys=True, indent=2).encode("utf-8")
        self.atomic_write(path, json_bytes)
