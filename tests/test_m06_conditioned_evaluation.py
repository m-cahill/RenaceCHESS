"""Tests for M06 conditioned evaluation runner."""

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from renacechess.contracts.models import EvalReportV3
from renacechess.eval.runner import run_conditioned_evaluation


def test_run_conditioned_evaluation_minimal(tmp_path: Path) -> None:
    """Test run_conditioned_evaluation with minimal dataset."""
    # Create minimal manifest and shard
    manifest_dir = tmp_path / "dataset"
    manifest_dir.mkdir()
    shards_dir = manifest_dir / "shards"
    shards_dir.mkdir()

    # Create minimal shard with one record
    shard_path = shards_dir / "shard_000.jsonl"
    record = {
        "position": {
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "sideToMove": "white",
            "legalMoves": ["e2e4", "e2e3", "d2d4"],
        },
        "conditioning": {
            "skillBucket": "1200-1400",
            "skillBucketId": "1200_1399",
            "skillBucketSpecVersion": 1,
            "timePressureBucket": "normal",
            "timePressureSpecVersion": 1,
            "timeControlClass": "blitz",
            "timeControlSpecVersion": 1,
        },
        "policy": {
            "topMoves": [{"uci": "e2e4", "p": 0.5}, {"uci": "e2e3", "p": 0.3}],
            "entropy": 1.5,
            "topGap": 0.2,
        },
        "humanWDL": {"pre": {"w": 0.5, "d": 0.3, "l": 0.2}, "postByMove": {}},
        "hdi": {"value": 0.5, "components": {"entropy": 1.5, "topGap": 0.2, "wdlSensitivity": 0.1}},
        "narrativeSeeds": [],
        "meta": {
            "schemaVersion": "v1",
            "generatedAt": "2024-01-01T12:00:00",
            "inputHash": "abc123",
        },
        "chosenMove": {"uci": "e2e4"},
    }

    import json

    shard_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    # Create minimal manifest v2
    manifest = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T12:00:00",
        "shardRefs": [
            {
                "shardId": "shard_000",
                "hash": "a" * 64,
                "path": "shards/shard_000.jsonl",
                "records": 1,
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
        "splitAssignments": {
            "train": ["shard_000"],
            "val": [],
            "frozenEval": [],
        },
    }

    manifest_path = manifest_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    # Run conditioned evaluation
    eval_results = run_conditioned_evaluation(
        manifest_path=manifest_path,
        policy_id="baseline.first_legal",
        eval_config={},
        compute_accuracy=True,
        top_k_values=[1, 3],
    )

    # Verify results structure
    assert "overall" in eval_results
    assert "by_skill_bucket_id" in eval_results
    assert "by_time_control_class" in eval_results
    assert "by_time_pressure_bucket" in eval_results
    assert eval_results["overall"].total_records == 1
    assert eval_results["overall"].labeled_records == 1


def test_run_conditioned_evaluation_with_frozen_manifest_hash(tmp_path: Path) -> None:
    """Test run_conditioned_evaluation with frozen eval manifest hash."""
    # Create minimal manifest and shard (same as above)
    manifest_dir = tmp_path / "dataset"
    manifest_dir.mkdir()
    shards_dir = manifest_dir / "shards"
    shards_dir.mkdir()

    shard_path = shards_dir / "shard_000.jsonl"
    record = {
        "position": {
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "sideToMove": "white",
            "legalMoves": ["e2e4"],
        },
        "conditioning": {
            "skillBucket": "1200-1400",
            "skillBucketId": "1200_1399",
            "timePressureBucket": "normal",
            "timeControlClass": "blitz",
        },
        "policy": {"topMoves": [{"uci": "e2e4", "p": 1.0}], "entropy": 0.0, "topGap": 0.0},
        "humanWDL": {"pre": {"w": 0.5, "d": 0.3, "l": 0.2}, "postByMove": {}},
        "hdi": {"value": 0.5, "components": {"entropy": 0.0, "topGap": 0.0, "wdlSensitivity": 0.0}},
        "narrativeSeeds": [],
        "meta": {
            "schemaVersion": "v1",
            "generatedAt": "2024-01-01T12:00:00",
            "inputHash": "abc123",
        },
    }

    import json

    shard_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    manifest = {
        "schemaVersion": "v2",
        "createdAt": "2024-01-01T12:00:00",
        "shardRefs": [
            {
                "shardId": "shard_000",
                "hash": "a" * 64,
                "path": "shards/shard_000.jsonl",
                "records": 1,
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

    manifest_path = manifest_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    # Run with frozen manifest hash
    frozen_hash = "d" * 64
    eval_results = run_conditioned_evaluation(
        manifest_path=manifest_path,
        policy_id="baseline.first_legal",
        eval_config={},
        frozen_eval_manifest_hash=frozen_hash,
    )

    assert eval_results["frozen_eval_manifest_hash"] == frozen_hash

