"""Determinism helpers for canonical JSON serialization and stable hashing."""

import hashlib
import json
from typing import Any


def canonical_json_dump(obj: Any) -> bytes:
    """Serialize object to canonical JSON bytes.

    Canonical format:
    - Sorted keys
    - No whitespace between separators
    - UTF-8 encoding
    - No trailing whitespace

    Args:
        obj: Object to serialize (must be JSON-serializable).

    Returns:
        Canonical JSON bytes.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def stable_hash(data: bytes) -> str:
    """Compute stable SHA-256 hash of data.

    Args:
        data: Bytes to hash.

    Returns:
        Hexadecimal hash string.
    """
    return hashlib.sha256(data).hexdigest()


def canonical_hash(obj: Any) -> str:
    """Compute stable hash of object via canonical JSON.

    Args:
        obj: Object to hash (must be JSON-serializable).

    Returns:
        Hexadecimal hash string.
    """
    return stable_hash(canonical_json_dump(obj))

