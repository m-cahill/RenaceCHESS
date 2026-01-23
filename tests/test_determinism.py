"""Tests for determinism helpers."""

import json

import pytest

from renacechess.determinism import canonical_hash, canonical_json_dump, stable_hash


def test_canonical_json_dump_stable() -> None:
    """Test that canonical JSON dump is stable across runs."""
    obj = {"c": 3, "a": 1, "b": 2, "d": {"z": 26, "y": 25}}
    result1 = canonical_json_dump(obj)
    result2 = canonical_json_dump(obj)

    assert result1 == result2
    # Should be sorted keys
    decoded = json.loads(result1.decode("utf-8"))
    assert list(decoded.keys()) == ["a", "b", "c", "d"]


def test_canonical_json_dump_format() -> None:
    """Test that canonical JSON has no extra whitespace."""
    obj = {"a": 1, "b": 2}
    result = canonical_json_dump(obj)
    decoded = result.decode("utf-8")

    # Should have no spaces after colons/commas
    assert " " not in decoded
    assert decoded == '{"a":1,"b":2}'


def test_stable_hash() -> None:
    """Test that stable hash is deterministic."""
    data = b"test data"
    hash1 = stable_hash(data)
    hash2 = stable_hash(data)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length


def test_canonical_hash() -> None:
    """Test that canonical hash is deterministic."""
    obj1 = {"c": 3, "a": 1, "b": 2}
    obj2 = {"a": 1, "b": 2, "c": 3}  # Different key order

    hash1 = canonical_hash(obj1)
    hash2 = canonical_hash(obj2)

    # Should be identical despite different key order
    assert hash1 == hash2


def test_canonical_hash_different_objects() -> None:
    """Test that different objects produce different hashes."""
    obj1 = {"a": 1, "b": 2}
    obj2 = {"a": 1, "b": 3}

    hash1 = canonical_hash(obj1)
    hash2 = canonical_hash(obj2)

    assert hash1 != hash2

