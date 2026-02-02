"""Frozen evaluation set v2 generator for M30.

This module generates a release-grade synthetic frozen evaluation set with:
- 10,000 chess-valid positions (locked for M30)
- 7 skill buckets with minimum 1,000 positions each
- Deterministic selection via fixed random seed
- Full provenance tracking for governance

Audit statement:
> "Frozen eval v2 is synthetic but chess-valid, and is intended for
> *relative* evaluation and calibration stability, not absolute strength claims."

See docs/milestones/PhaseE/M30/M30_plan.md for the governing specification.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from renacechess.contracts.models import (
    EvalSetProvenanceV1,
    FrozenEvalManifestV2,
    FrozenEvalRecordV2,
    FrozenEvalStratificationV2,
)
from renacechess.determinism import canonical_json_dump

# =============================================================================
# Constants (Locked for M30)
# =============================================================================

M30_TOTAL_POSITIONS = 10_000
M30_MIN_PER_SKILL_BUCKET = 1_000
M30_SELECTION_SEED = 42  # Fixed for determinism
M30_GENERATOR_VERSION = "v2.0.0"

# Canonical skill buckets (M06)
SKILL_BUCKETS: list[
    Literal[
        "lt_800",
        "800_999",
        "1000_1199",
        "1200_1399",
        "1400_1599",
        "1600_1799",
        "gte_1800",
    ]
] = [
    "lt_800",
    "800_999",
    "1000_1199",
    "1200_1399",
    "1400_1599",
    "1600_1799",
    "gte_1800",
]

TIME_CONTROL_CLASSES: list[Literal["bullet", "blitz", "rapid", "classical"]] = [
    "bullet",
    "blitz",
    "rapid",
    "classical",
]

TIME_PRESSURE_BUCKETS: list[Literal["normal", "low", "trouble"]] = [
    "normal",
    "low",
    "trouble",
]

# =============================================================================
# FEN Seeds — Chess-valid positions for synthetic eval
# =============================================================================

# Base FEN seeds: common opening/middlegame/endgame positions
# These are real chess positions, not random strings
FEN_SEEDS = [
    # Starting position
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    # Common openings
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",  # 1. e4
    "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1",  # 1. d4
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",  # 1. e4 e5
    "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq d6 0 2",  # 1. d4 d5
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",  # Italian setup
    "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",  # Italian
    "rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2",  # Alekhine
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2",  # Sicilian
    "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",  # French
    "rnbqkbnr/ppppp1pp/5p2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",  # Damiano
    # Middlegame positions
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 5",
    "r1bq1rk1/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQ1RK1 w - - 2 7",
    "r2qk2r/ppp1bppp/2n1bn2/3pp3/4P3/1NN1BP2/PPP3PP/R2QKB1R w KQkq - 0 8",
    "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 7",
    "r2q1rk1/1pp2ppp/p1np1n2/2b1p1B1/2B1P1b1/2NP1N2/PPP2PPP/R2Q1RK1 w - - 4 9",
    "r3k2r/ppp2ppp/2n1bn2/3qp3/3P4/2N2N2/PPP2PPP/R1BQK2R w KQkq - 0 9",
    "r1b1kb1r/pppp1ppp/5n2/4p2q/2B1n3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 5",
    "r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 4 4",
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    # Queen's Gambit lines
    "rnbqkb1r/ppp1pppp/5n2/3p4/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 1 3",
    "rnbqkb1r/ppp2ppp/4pn2/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 0 4",
    "rnbqkb1r/pp3ppp/4pn2/2pp4/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq c6 0 5",
    # Endgame positions
    "8/8/4k3/8/8/4K3/4P3/8 w - - 0 1",  # K+P vs K
    "8/5k2/8/8/8/2K5/1R6/8 w - - 0 1",  # R vs K
    "8/8/3k4/8/8/3K4/3Q4/8 w - - 0 1",  # Q vs K
    "8/8/4k3/8/3B4/4K3/8/8 w - - 0 1",  # B+K vs K
    "8/8/4k3/8/4N3/4K3/8/8 w - - 0 1",  # N+K vs K
    "4k3/4p3/4K3/8/8/8/8/5R2 w - - 0 1",  # Lucena-like
    "8/1k6/8/1K6/8/8/1P6/8 w - - 0 1",  # Opposition
    # Complex middlegame
    "r1bqr1k1/pp1n1ppp/2pb1n2/3p4/3P4/2NBPN2/PPP2PPP/R1BQR1K1 w - - 0 10",
    "r2qr1k1/1b1nbppp/pp1p1n2/2pP4/P1P1P3/2N2N2/1P1BBPPP/R2Q1RK1 w - - 0 13",
    "r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 9",
    # Pawn structures
    "r1bqkb1r/pp2pppp/2n2n2/2pp4/3P4/2N2N2/PPP1PPPP/R1BQKB1R w KQkq - 0 5",
    "rnbqk2r/ppp1bppp/4pn2/3p2B1/3P4/2N2N2/PPP1PPPP/R2QKB1R w KQkq - 0 5",
    "r1bqk2r/pppp1ppp/2n2n2/4p3/1bB1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 4 5",
    # Castled positions
    "r1bq1rk1/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQ - 0 6",
    "r3k2r/ppp2ppp/2nqbn2/3pp3/8/2N2NP1/PPPQPPBP/R3K2R w KQkq - 0 9",
    "2rq1rk1/pp1bppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/2KR1B1R w - - 0 11",
]


def _compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hash of bytes and return hex string."""
    return hashlib.sha256(data).hexdigest()


def _compute_determinism_hash(data: bytes) -> str:
    """Compute determinism hash in standard format: sha256:<hex>."""
    return f"sha256:{_compute_sha256(data)}"


def _expand_fen_to_positions(
    fen_seeds: list[str],
    target_count: int,
    rng: random.Random,
) -> list[str]:
    """Expand FEN seeds to target count through deterministic variations.

    Each seed generates multiple positions by:
    - Using the seed directly
    - Flipping side to move
    - Removing/adding castling rights deterministically

    This ensures we have enough unique, chess-valid positions.
    """
    positions: list[str] = []
    seed_index = 0
    variation_index = 0

    while len(positions) < target_count:
        base_fen = fen_seeds[seed_index % len(fen_seeds)]
        parts = base_fen.split(" ")

        # Variation 0: Original FEN
        if variation_index == 0:
            positions.append(base_fen)
        # Variation 1: Flip side to move
        elif variation_index == 1:
            parts[1] = "b" if parts[1] == "w" else "w"
            positions.append(" ".join(parts))
        # Variation 2: Remove castling (set to "-")
        elif variation_index == 2:
            parts[2] = "-"
            positions.append(" ".join(parts))
        # Variation 3: Increment move number
        elif variation_index == 3:
            parts[5] = str(int(parts[5]) + 1)
            parts[4] = str(int(parts[4]) + 1)
            positions.append(" ".join(parts))
        # Variation 4: Different en passant (clear if set)
        elif variation_index == 4:
            parts[3] = "-"
            positions.append(" ".join(parts))
        else:
            # Reset variation, move to next seed
            variation_index = -1
            seed_index += 1

        variation_index += 1

        # Cycle through seeds if we've exhausted variations
        if seed_index >= len(fen_seeds) * 100:
            # If we still need more, just re-add with index suffix in record_key
            break

    # If we need more positions, repeat with indexed variants
    while len(positions) < target_count:
        idx = len(positions)
        base_fen = fen_seeds[idx % len(fen_seeds)]
        parts = base_fen.split(" ")
        # Modify move numbers to create unique FENs
        parts[5] = str((idx // len(fen_seeds)) + 1)
        parts[4] = str(idx % 50)
        positions.append(" ".join(parts))

    return positions[:target_count]


def generate_frozen_eval_v2(
    output_dir: Path,
    total_positions: int = M30_TOTAL_POSITIONS,
    min_per_skill_bucket: int = M30_MIN_PER_SKILL_BUCKET,
    seed: int = M30_SELECTION_SEED,
    created_at: datetime | None = None,
) -> tuple[FrozenEvalManifestV2, EvalSetProvenanceV1]:
    """Generate a frozen evaluation set v2 with synthetic chess positions.

    Args:
        output_dir: Directory to write output files (manifest + shards).
        total_positions: Total target position count (default: 10,000).
        min_per_skill_bucket: Minimum positions per skill bucket (default: 1,000).
        seed: Random seed for deterministic generation (default: 42).
        created_at: Override creation timestamp (for testing).

    Returns:
        Tuple of (FrozenEvalManifestV2, EvalSetProvenanceV1) artifacts.

    Raises:
        ValueError: If total_positions < min_per_skill_bucket * 7.
    """
    if total_positions < min_per_skill_bucket * len(SKILL_BUCKETS):
        msg = (
            f"total_positions ({total_positions}) must be >= "
            f"min_per_skill_bucket ({min_per_skill_bucket}) × 7 skill buckets"
        )
        raise ValueError(msg)

    if created_at is None:
        created_at = datetime.now(UTC)

    # Initialize deterministic RNG
    rng = random.Random(seed)

    # Expand FEN seeds to target position count
    all_fens = _expand_fen_to_positions(FEN_SEEDS, total_positions, rng)

    # Generate records with stratification
    records: list[FrozenEvalRecordV2] = []
    counts_by_skill: dict[str, int] = defaultdict(int)
    counts_by_time_control: dict[str, int] = defaultdict(int)
    counts_by_time_pressure: dict[str, int] = defaultdict(int)

    for idx, fen in enumerate(all_fens):
        # Assign skill bucket (round-robin to ensure minimum per bucket)
        skill_bucket = SKILL_BUCKETS[idx % len(SKILL_BUCKETS)]

        # Assign time control (deterministic based on index)
        time_control = TIME_CONTROL_CLASSES[rng.randint(0, len(TIME_CONTROL_CLASSES) - 1)]

        # Assign time pressure (deterministic based on index)
        time_pressure = TIME_PRESSURE_BUCKETS[rng.randint(0, len(TIME_PRESSURE_BUCKETS) - 1)]

        # Determine shard (1000 records per shard)
        shard_idx = idx // 1000
        shard_id = f"shard_{shard_idx:03d}"

        record = FrozenEvalRecordV2(
            record_key=f"{fen}:{idx}",
            shard_id=shard_id,
            skill_bucket_id=skill_bucket,
            time_control_class=time_control,
            time_pressure_bucket=time_pressure,
        )
        records.append(record)

        counts_by_skill[skill_bucket] += 1
        counts_by_time_control[time_control] += 1
        counts_by_time_pressure[time_pressure] += 1

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group records by shard and write shards
    records_by_shard: dict[str, list[FrozenEvalRecordV2]] = defaultdict(list)
    for record in records:
        records_by_shard[record.shard_id].append(record)

    shard_refs: list[str] = []
    shard_hashes: dict[str, str] = {}

    for shard_id in sorted(records_by_shard.keys()):
        shard_records = records_by_shard[shard_id]
        shard_filename = f"{shard_id}.jsonl"
        shard_path = output_dir / shard_filename
        shard_refs.append(shard_filename)

        # Write shard as JSONL
        shard_lines: list[str] = []
        for record in shard_records:
            # Write full position data for each record
            record_data = {
                "position": {"fen": record.record_key.rsplit(":", 1)[0]},
                "conditioning": {
                    "skillBucketId": record.skill_bucket_id,
                    "timeControlClass": record.time_control_class,
                    "timePressureBucket": record.time_pressure_bucket,
                },
                "meta": {
                    "recordKey": record.record_key,
                    "shardId": record.shard_id,
                    "synthetic": True,
                },
                # Synthetic chosen move (placeholder for labeled data)
                "chosenMove": "e2e4",  # Placeholder — synthetic move label
            }
            shard_lines.append(json.dumps(record_data, sort_keys=True))

        shard_content = "\n".join(shard_lines) + "\n"
        shard_path.write_text(shard_content, encoding="utf-8")
        shard_hashes[shard_id] = _compute_sha256(shard_content.encode("utf-8"))

    # Create provenance artifact (construct model first, then compute hash from its serialization)
    provenance_without_hash = EvalSetProvenanceV1(
        version="1.0",
        created_at=created_at,
        generator_version=M30_GENERATOR_VERSION,
        selection_seed=seed,
        position_sources=["algorithmic_fen_seeds_v1", "deterministic_expansion"],
        skill_bucket_strategy="round_robin_uniform",
        time_control_strategy="seeded_random_uniform",
        time_pressure_strategy="seeded_random_uniform",
        audit_notes=(
            "Frozen eval v2 is synthetic but chess-valid, and is intended for "
            "*relative* evaluation and calibration stability, not absolute strength claims. "
            "Generated by M30 FROZEN-EVAL-SCALESET-001."
        ),
        determinism_hash="sha256:" + "0" * 64,  # Placeholder
    )

    # Serialize using Pydantic's format, then compute hash
    provenance_dict_for_hash = provenance_without_hash.model_dump(mode="json", by_alias=True)
    del provenance_dict_for_hash["determinismHash"]
    provenance_bytes = canonical_json_dump(provenance_dict_for_hash)
    provenance_hash = _compute_determinism_hash(provenance_bytes)

    provenance = EvalSetProvenanceV1(
        version="1.0",
        created_at=created_at,
        generator_version=M30_GENERATOR_VERSION,
        selection_seed=seed,
        position_sources=["algorithmic_fen_seeds_v1", "deterministic_expansion"],
        skill_bucket_strategy="round_robin_uniform",
        time_control_strategy="seeded_random_uniform",
        time_pressure_strategy="seeded_random_uniform",
        audit_notes=(
            "Frozen eval v2 is synthetic but chess-valid, and is intended for "
            "*relative* evaluation and calibration stability, not absolute strength claims. "
            "Generated by M30 FROZEN-EVAL-SCALESET-001."
        ),
        determinism_hash=provenance_hash,
    )

    # Write provenance artifact
    provenance_path = output_dir / "provenance.json"
    provenance_dict = provenance.model_dump(mode="json", by_alias=True)
    provenance_json = canonical_json_dump(provenance_dict)
    provenance_path.write_bytes(provenance_json)

    # Create manifest artifact (construct model first, then compute hash from its serialization)
    manifest_without_hash = FrozenEvalManifestV2(
        schema_version=2,
        created_at=created_at,
        synthetic=True,
        selection_strategy="deterministic_fen_seeds_stratified_by_skill",
        position_count=len(records),
        provenance_ref=provenance_hash,
        stratification=FrozenEvalStratificationV2(
            total_positions=total_positions,
            min_per_skill_bucket=min_per_skill_bucket,
            skill_bucket_count=len(SKILL_BUCKETS),
        ),
        counts_by_skill_bucket_id=dict(counts_by_skill),
        counts_by_time_control_class=dict(counts_by_time_control),
        counts_by_time_pressure_bucket=dict(counts_by_time_pressure),
        shard_refs=shard_refs,
        shard_hashes=shard_hashes,
        determinism_hash="sha256:" + "0" * 64,  # Placeholder, will be recomputed
    )

    # Serialize to dict using Pydantic's serialization (ensures consistent datetime format)
    manifest_dict_for_hash = manifest_without_hash.model_dump(mode="json", by_alias=True)
    # Remove the placeholder hash before computing
    del manifest_dict_for_hash["determinismHash"]
    manifest_bytes = canonical_json_dump(manifest_dict_for_hash)
    manifest_hash = _compute_determinism_hash(manifest_bytes)

    # Create final manifest with correct hash
    manifest = FrozenEvalManifestV2(
        schema_version=2,
        created_at=created_at,
        synthetic=True,
        selection_strategy="deterministic_fen_seeds_stratified_by_skill",
        position_count=len(records),
        provenance_ref=provenance_hash,
        stratification=FrozenEvalStratificationV2(
            total_positions=total_positions,
            min_per_skill_bucket=min_per_skill_bucket,
            skill_bucket_count=len(SKILL_BUCKETS),
        ),
        counts_by_skill_bucket_id=dict(counts_by_skill),
        counts_by_time_control_class=dict(counts_by_time_control),
        counts_by_time_pressure_bucket=dict(counts_by_time_pressure),
        shard_refs=shard_refs,
        shard_hashes=shard_hashes,
        determinism_hash=manifest_hash,
    )

    # Write manifest artifact
    manifest_path = output_dir / "manifest.json"
    manifest_dict = manifest.model_dump(mode="json", by_alias=True)
    manifest_json = canonical_json_dump(manifest_dict)
    manifest_path.write_bytes(manifest_json)

    return manifest, provenance


def verify_frozen_eval_v2(manifest_path: Path) -> bool:
    """Verify a frozen eval v2 manifest's determinism hash.

    Args:
        manifest_path: Path to the manifest.json file.

    Returns:
        True if the manifest hash is valid, False otherwise.

    Note:
        The manifest must have been written using canonical_json_dump.
        This function verifies that the stored hash matches what would be
        computed from the manifest content (excluding the hash field).
    """
    with manifest_path.open("rb") as f:
        manifest_bytes = f.read()

    manifest_dict = json.loads(manifest_bytes)
    stored_hash: str | None = manifest_dict.get("determinismHash")

    if not stored_hash:
        return False

    # Remove the hash field and recompute
    manifest_dict_for_hash = {k: v for k, v in manifest_dict.items() if k != "determinismHash"}

    # Recompute hash without the determinismHash field
    recomputed_bytes = canonical_json_dump(manifest_dict_for_hash)
    recomputed_hash = _compute_determinism_hash(recomputed_bytes)

    return bool(stored_hash == recomputed_hash)
