"""Deterministic split assignment logic."""

import hashlib
from typing import Literal


def compute_split_assignment(record_key: str) -> Literal["train", "val", "frozenEval"]:
    """Compute deterministic split assignment for a record key.

    Split allocation:
    - 0-4   => frozenEval (5%)
    - 5-14  => val       (10%)
    - 15-99 => train     (85%)

    Args:
        record_key: Composite key (e.g., "fen:ply").

    Returns:
        Split assignment: "train", "val", or "frozenEval".
    """
    # Compute hash and take first 8 hex chars as integer
    hash_bytes = hashlib.sha256(record_key.encode("utf-8")).digest()
    bucket = int(hash_bytes[:8].hex(), 16) % 100

    if bucket < 5:
        return "frozenEval"
    elif bucket < 15:
        return "val"
    else:
        return "train"
