"""Tests for M06 frozen eval manifest generator."""

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from renacechess.frozen_eval.generator import (
    generate_frozen_eval_manifest,
    write_frozen_eval_manifest,
)


def test_generate_frozen_eval_manifest_minimal(tmp_path: Path) -> None:
    """Test frozen eval manifest generation with minimal dataset."""
    # Create minimal dataset structure
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    shards_dir = dataset_dir / "shards"
    shards_dir.mkdir()

    # Create shard with labeled records (need at least 1000 for generator)
    shard_path = shards_dir / "shard_000.jsonl"
    records = []
    for i in range(1000):
        record = {
            "position": {
                "fen": f"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 {i}",
                "sideToMove": "white",
                "legalMoves": ["e2e4"],
            },
            "conditioning": {
                "skillBucket": "1200-1400",
                "skillBucketId": "1200_1399" if i < 5 else "1400_1599",
                "timePressureBucket": "normal",
                "timeControlClass": "blitz",
            },
            "policy": {"topMoves": [{"uci": "e2e4", "p": 1.0}], "entropy": 0.0, "topGap": 0.0},
            "humanWDL": {"pre": {"w": 0.5, "d": 0.3, "l": 0.2}, "postByMove": {}},
            "hdi": {
                "value": 0.5,
                "components": {"entropy": 0.0, "topGap": 0.0, "wdlSensitivity": 0.0},
            },
            "narrativeSeeds": [],
            "meta": {
                "schemaVersion": "v1",
                "generatedAt": "2024-01-01T12:00:00",
                "inputHash": f"abc{i}",
            },
            "chosenMove": {"uci": "e2e4"},  # Labeled record
        }
        records.append(record)

    import json

    shard_content = "\n".join(json.dumps(r) for r in records)
    shard_path.write_text(shard_content, encoding="utf-8")

    # Create manifest v2
    from renacechess.determinism import stable_hash

    shard_hash = stable_hash(shard_path.read_bytes())

    manifest = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T12:00:00",
        "shardRefs": [
            {
                "shardId": "shard_000",
                "hash": shard_hash,
                "path": "shards/shard_000.jsonl",
                "records": 1000,
            }
        ],
        "assemblyConfigHash": "b" * 64,
        "datasetDigest": "c" * 64,
        "inputs": [],
        "assemblyConfig": {
            "shardSize": 10000,
            "maxGames": None,
            "maxPositions": None,
            "startPly": 0,
            "endPly": None,
        },
        "splitAssignments": {"train": ["shard_000"], "val": [], "frozenEval": []},
    }

    manifest_path = dataset_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    # Generate frozen eval manifest
    frozen_manifest = generate_frozen_eval_manifest(
        source_manifest_path=manifest_path,
        target_total_records=100,
        min_per_skill_bucket=10,
    )

    # Verify manifest structure
    assert frozen_manifest.schema_version == 1
    assert len(frozen_manifest.records) <= 100  # Should be close to target_total_records
    assert frozen_manifest.source_manifest_ref.dataset_digest == "c" * 64
    assert frozen_manifest.manifest_hash  # Should be computed
    assert len(frozen_manifest.manifest_hash) == 64  # SHA-256 hex string


def test_write_frozen_eval_manifest(tmp_path: Path) -> None:
    """Test writing frozen eval manifest to disk."""
    from renacechess.contracts.models import (
        FrozenEvalManifestRecord,
        FrozenEvalManifestSourceRef,
        FrozenEvalManifestV1,
    )

    # Create minimal manifest
    manifest = FrozenEvalManifestV1(
        schema_version=1,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        source_manifest_ref=FrozenEvalManifestSourceRef(
            dataset_digest="a" * 64,
            manifest_path="/path/to/manifest.json",
        ),
        records=[
            FrozenEvalManifestRecord(
                record_key="fen:1",
                shard_id="shard_000",
                shard_hash="b" * 64,
                skill_bucket_id="1200_1399",
                time_control_class="blitz",
                time_pressure_bucket="normal",
            )
        ],
        manifest_hash="c" * 64,
    )

    output_path = tmp_path / "frozen_manifest.json"
    write_frozen_eval_manifest(manifest, output_path)

    # Verify file exists and is valid JSON
    assert output_path.exists()
    import json

    manifest_dict = json.loads(output_path.read_text(encoding="utf-8"))
    assert manifest_dict["schemaVersion"] == 1
    assert len(manifest_dict["records"]) == 1


def test_generate_frozen_eval_manifest_insufficient_records(tmp_path: Path) -> None:
    """Test that generator fails if insufficient labeled records."""
    # Create dataset with < 1000 labeled records
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    shards_dir = dataset_dir / "shards"
    shards_dir.mkdir()

    shard_path = shards_dir / "shard_000.jsonl"
    # Create only 5 labeled records (below 1000 minimum)
    records = []
    for i in range(5):
        record = {
            "position": {
                "fen": f"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 {i}",
                "sideToMove": "white",
                "legalMoves": ["e2e4"],
            },
            "conditioning": {"skillBucket": "1200-1400", "skillBucketId": "1200_1399"},
            "policy": {"topMoves": [{"uci": "e2e4", "p": 1.0}], "entropy": 0.0, "topGap": 0.0},
            "humanWDL": {"pre": {"w": 0.5, "d": 0.3, "l": 0.2}, "postByMove": {}},
            "hdi": {
                "value": 0.5,
                "components": {"entropy": 0.0, "topGap": 0.0, "wdlSensitivity": 0.0},
            },
            "narrativeSeeds": [],
            "meta": {
                "schemaVersion": "v1",
                "generatedAt": "2024-01-01T12:00:00",
                "inputHash": f"abc{i}",
            },
            "chosenMove": {"uci": "e2e4"},
        }
        records.append(record)

    import json

    shard_content = "\n".join(json.dumps(r) for r in records)
    shard_path.write_text(shard_content, encoding="utf-8")

    from renacechess.determinism import stable_hash

    shard_hash = stable_hash(shard_path.read_bytes())

    manifest = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T12:00:00",
        "shardRefs": [
            {
                "shardId": "shard_000",
                "hash": shard_hash,
                "path": "shards/shard_000.jsonl",
                "records": 5,
            }
        ],
        "assemblyConfigHash": "b" * 64,
        "datasetDigest": "c" * 64,
        "inputs": [],
        "assemblyConfig": {
            "shardSize": 10000,
            "maxGames": None,
            "maxPositions": None,
            "startPly": 0,
            "endPly": None,
        },
        "splitAssignments": {"train": ["shard_000"], "val": [], "frozenEval": []},
    }

    manifest_path = dataset_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    # Should raise ValueError for insufficient records
    with pytest.raises(ValueError, match="Insufficient labeled records"):
        generate_frozen_eval_manifest(
            source_manifest_path=manifest_path,
            target_total_records=10000,
            min_per_skill_bucket=500,
        )
