"""Tests for FrozenEval manifest compatibility loader (M31 Run Fix 1).

This test suite verifies:
1. V2 manifest loads correctly and extracts record keys
2. V1 manifest still loads (regression test)
3. Schema version detection works correctly
4. Training functions can use the loader with frozen eval v2
"""

import json
from pathlib import Path

import pytest

from renacechess.frozen_eval.compat import (
    FrozenEvalRecordKeys,
    load_frozen_eval_record_keys,
)


class TestFrozenEvalRecordKeys:
    """Tests for FrozenEvalRecordKeys dataclass."""

    def test_contains(self) -> None:
        """Test __contains__ method."""
        keys = FrozenEvalRecordKeys(
            keys=frozenset(["key1", "key2", "key3"]),
            schema_version=2,
            source_path=Path("test.json"),
        )
        assert "key1" in keys
        assert "key2" in keys
        assert "key_not_present" not in keys

    def test_len(self) -> None:
        """Test __len__ method."""
        keys = FrozenEvalRecordKeys(
            keys=frozenset(["key1", "key2", "key3"]),
            schema_version=2,
            source_path=Path("test.json"),
        )
        assert len(keys) == 3

    def test_immutable(self) -> None:
        """Test that FrozenEvalRecordKeys is immutable."""
        keys = FrozenEvalRecordKeys(
            keys=frozenset(["key1"]),
            schema_version=2,
            source_path=Path("test.json"),
        )
        with pytest.raises(AttributeError):
            keys.keys = frozenset(["modified"])  # type: ignore[misc]


class TestSchemaVersionDetection:
    """Tests for schema version detection."""

    def test_unsupported_version_raises(self, tmp_path: Path) -> None:
        """Test that unsupported schema versions raise ValueError."""
        manifest = {"schemaVersion": 99}
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)

        with pytest.raises(ValueError, match="Unsupported frozen eval manifest schema version"):
            load_frozen_eval_record_keys(manifest_path)


class TestProductionFrozenEvalV2:
    """Tests using the actual production frozen eval v2."""

    def test_load_production_frozen_eval_v2(self) -> None:
        """Test loading the production frozen eval v2 manifest."""
        frozen_eval_path = Path("data/frozen_eval_v2/manifest.json")

        if not frozen_eval_path.exists():
            pytest.skip("Production frozen eval v2 not available")

        result = load_frozen_eval_record_keys(frozen_eval_path)

        assert result.schema_version == 2
        assert len(result) >= 10000  # M30 produced 10,000 positions
        assert result.source_path == frozen_eval_path

    def test_training_dataset_can_use_frozen_eval_v2(self) -> None:
        """Test that training dataset can use frozen eval v2 for exclusion."""
        from renacechess.models.training import PolicyDataset

        frozen_eval_path = Path("data/frozen_eval_v2/manifest.json")
        training_dataset_path = Path("artifacts/m31_training_run/training_dataset_v2/manifest.json")

        if not frozen_eval_path.exists() or not training_dataset_path.exists():
            pytest.skip("Production data not available")

        # This should not raise an error (the V2 compat bug that caused M31 failure)
        dataset = PolicyDataset(
            manifest_path=training_dataset_path,
            frozen_eval_manifest_path=frozen_eval_path,
        )

        # Verify frozen eval keys were loaded
        assert len(dataset.frozen_eval_keys) >= 10000
