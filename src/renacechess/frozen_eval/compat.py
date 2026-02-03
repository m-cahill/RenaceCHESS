"""FrozenEval manifest compatibility loader (M31 Run Fix 1).

This module provides a unified interface for loading frozen eval manifests
regardless of schema version (V1 or V2). It normalizes access to record keys
for training data exclusion.

Design:
- Detect schema version from JSON
- V1: Return records directly (inline in manifest)
- V2: Read shard files and extract record keys
- Return a set of record keys for training exclusion

This is a corrective patch for M31 execution, not a schema change.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FrozenEvalRecordKeys:
    """Normalized container for frozen eval record keys.

    This provides a unified interface for training functions to access
    record keys regardless of manifest version.
    """

    keys: frozenset[str]
    schema_version: int
    source_path: Path

    def __contains__(self, key: str) -> bool:
        """Check if a record key is in the frozen eval set."""
        return key in self.keys

    def __len__(self) -> int:
        """Return the number of record keys."""
        return len(self.keys)


def load_frozen_eval_record_keys(manifest_path: Path) -> FrozenEvalRecordKeys:
    """Load frozen eval record keys from a manifest (V1 or V2).

    This is the main entry point for training functions that need to
    exclude frozen eval records from training data.

    Args:
        manifest_path: Path to the frozen eval manifest JSON file.

    Returns:
        FrozenEvalRecordKeys containing all record keys for exclusion.

    Raises:
        ValueError: If the manifest has an unsupported schema version.
        FileNotFoundError: If the manifest or shard files don't exist.
    """
    manifest_dict = json.loads(manifest_path.read_text(encoding="utf-8"))

    schema_version = manifest_dict.get("schemaVersion", 1)

    if schema_version == 1:
        return _load_v1_record_keys(manifest_dict, manifest_path)
    elif schema_version == 2:
        return _load_v2_record_keys(manifest_dict, manifest_path)
    else:
        raise ValueError(f"Unsupported frozen eval manifest schema version: {schema_version}")


def _load_v1_record_keys(manifest_dict: dict, manifest_path: Path) -> FrozenEvalRecordKeys:
    """Load record keys from a V1 manifest (records inline)."""
    from renacechess.contracts.models import FrozenEvalManifestV1

    manifest = FrozenEvalManifestV1.model_validate(manifest_dict)
    keys = frozenset(record.record_key for record in manifest.records)

    return FrozenEvalRecordKeys(
        keys=keys,
        schema_version=1,
        source_path=manifest_path,
    )


def _load_v2_record_keys(manifest_dict: dict, manifest_path: Path) -> FrozenEvalRecordKeys:
    """Load record keys from a V2 manifest (records in shard files)."""
    from renacechess.contracts.models import FrozenEvalManifestV2

    manifest = FrozenEvalManifestV2.model_validate(manifest_dict)
    manifest_dir = manifest_path.parent

    keys: set[str] = set()

    for shard_ref in manifest.shard_refs:
        shard_path = manifest_dir / shard_ref
        if not shard_path.exists():
            raise FileNotFoundError(f"Shard file not found: {shard_path}")

        with open(shard_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                # V2 shard format: {"meta": {"recordKey": "..."}, ...}
                record_key = record.get("meta", {}).get("recordKey")
                if record_key:
                    keys.add(record_key)

    return FrozenEvalRecordKeys(
        keys=frozenset(keys),
        schema_version=2,
        source_path=manifest_path,
    )

