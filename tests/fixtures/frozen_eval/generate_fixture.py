#!/usr/bin/env python3
"""Generate frozen eval CI fixture for M24 calibration testing.

This script generates a minimal, deterministic frozen eval fixture for CI.
Run once to regenerate fixture files; committed files are the source of truth.

Usage:
    python tests/fixtures/frozen_eval/generate_fixture.py
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

# Skill buckets from conditioning.buckets (M06)
SKILL_BUCKETS = [
    "lt_800",
    "800_999",
    "1000_1199",
    "1200_1399",
    "1400_1599",
    "1600_1799",
    "gte_1800",
]

# Sample FENs for variety (deterministic)
SAMPLE_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
    "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
]

GAME_RESULTS = ["win", "draw", "loss"]
TIME_CONTROL_CLASSES = ["bullet", "blitz", "rapid"]
TIME_PRESSURE_BUCKETS = ["normal", "low", "trouble"]


def generate_record(idx: int, skill_bucket: str) -> dict:
    """Generate a single calibration record."""
    fen_idx = idx % len(SAMPLE_FENS)
    result_idx = idx % len(GAME_RESULTS)
    tc_idx = idx % len(TIME_CONTROL_CLASSES)
    tp_idx = idx % len(TIME_PRESSURE_BUCKETS)

    # Generate deterministic move probabilities
    # Seed based on idx for reproducibility
    import random

    rng = random.Random(idx * 12345)

    legal_moves = ["e2e4", "d2d4", "g1f3", "c2c4", "e2e3"]
    move_probs = [rng.random() for _ in legal_moves]
    total = sum(move_probs)
    move_probs = [p / total for p in move_probs]
    move_probs.sort(reverse=True)

    chosen_idx = rng.randint(0, len(legal_moves) - 1)

    return {
        "position": {
            "fen": SAMPLE_FENS[fen_idx],
            "sideToMove": "white" if " w " in SAMPLE_FENS[fen_idx] else "black",
            "legalMoves": legal_moves,
        },
        "conditioning": {
            "skillBucketId": skill_bucket,
            "timeControlClass": TIME_CONTROL_CLASSES[tc_idx],
            "timePressureBucket": TIME_PRESSURE_BUCKETS[tp_idx],
        },
        "policy": {
            "topMoves": [
                {"uci": move, "p": round(prob, 6)}
                for move, prob in zip(legal_moves, move_probs)
            ],
            "entropy": round(rng.uniform(0.5, 2.5), 6),
            "topGap": round(move_probs[0] - move_probs[1] if len(move_probs) > 1 else 0, 6),
        },
        "chosenMove": {"uci": legal_moves[chosen_idx]},
        "meta": {
            "ply": idx,
            "gameResult": GAME_RESULTS[result_idx],
        },
    }


def generate_fixture() -> None:
    """Generate the complete frozen eval fixture."""
    fixture_dir = Path(__file__).parent
    shards_dir = fixture_dir / "shards"
    shards_dir.mkdir(exist_ok=True)

    # Generate records: 10 per skill bucket = 70 total
    records_per_bucket = 10
    all_records: list[dict] = []
    manifest_records: list[dict] = []

    for bucket_idx, skill_bucket in enumerate(SKILL_BUCKETS):
        for i in range(records_per_bucket):
            idx = bucket_idx * records_per_bucket + i
            record = generate_record(idx, skill_bucket)
            all_records.append(record)

            # Create manifest record entry
            fen = record["position"]["fen"]
            ply = record["meta"]["ply"]
            manifest_records.append(
                {
                    "recordKey": f"{fen}:{ply}",
                    "shardId": "shard_000",
                    "shardHash": "",  # Will be filled after writing shard
                    "skillBucketId": skill_bucket,
                    "timeControlClass": record["conditioning"]["timeControlClass"],
                    "timePressureBucket": record["conditioning"]["timePressureBucket"],
                }
            )

    # Write shard file
    shard_path = shards_dir / "shard_000.jsonl"
    shard_content = "\n".join(json.dumps(r, sort_keys=True) for r in all_records)
    shard_path.write_text(shard_content, encoding="utf-8")

    # Compute shard hash
    shard_hash = hashlib.sha256(shard_path.read_bytes()).hexdigest()

    # Update manifest records with shard hash
    for rec in manifest_records:
        rec["shardHash"] = shard_hash

    # Count by bucket
    counts_by_skill = {}
    counts_by_tc = {}
    counts_by_tp = {}
    for rec in manifest_records:
        skill = rec["skillBucketId"]
        tc = rec["timeControlClass"]
        tp = rec["timePressureBucket"]
        counts_by_skill[skill] = counts_by_skill.get(skill, 0) + 1
        counts_by_tc[tc] = counts_by_tc.get(tc, 0) + 1
        counts_by_tp[tp] = counts_by_tp.get(tp, 0) + 1

    # Create frozen eval manifest
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    manifest = {
        "schemaVersion": 1,
        "createdAt": now.isoformat(),
        "sourceManifestRef": {
            "datasetDigest": "a" * 64,  # Synthetic for fixture
            "manifestPath": "tests/fixtures/frozen_eval/source_manifest.json",
        },
        "records": manifest_records,
        "stratificationTargets": {
            "totalRecords": len(all_records),
            "minPerSkillBucket": records_per_bucket,
        },
        "countsBySkillBucketId": counts_by_skill,
        "countsByTimeControlClass": counts_by_tc,
        "countsByTimePressureBucket": counts_by_tp,
    }

    # Compute manifest hash
    manifest_json = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    manifest_hash = hashlib.sha256(manifest_json.encode()).hexdigest()
    manifest["manifestHash"] = manifest_hash

    # Write manifest
    manifest_path = fixture_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    print(f"Generated frozen eval fixture:")
    print(f"  - {len(all_records)} records")
    print(f"  - {len(SKILL_BUCKETS)} skill buckets")
    print(f"  - Shard: {shard_path}")
    print(f"  - Manifest: {manifest_path}")
    print(f"  - Manifest hash: {manifest_hash}")


if __name__ == "__main__":
    generate_fixture()


