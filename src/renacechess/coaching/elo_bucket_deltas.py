"""Elo-bucket delta facts builder — deterministic facts-only artifact generator (M20).

This module provides a pure function that computes Elo-bucket delta facts from
pre-computed policy/outcome/difficulty signals across two skill buckets.

Key invariants:
- Deterministic: same inputs → identical outputs (byte-stable JSON)
- Facts-only: no prose generation, no LLM calls, no advice
- Lineage required: must reference source AdviceFacts hashes

Float canonicalization:
- All floats are rounded to 6 decimal places before hashing
- This ensures determinism across platforms with different float representations

See: ELO_BUCKET_DELTA_FACTS_CONTRACT_v1.md
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from renacechess.contracts.models import (
    DifficultyDeltaV1,
    EloBucketDeltaFactsV1,
    EloBucketDeltaSourceContractsV1,
    OutcomeDeltaV1,
    OutcomeSummaryV1,
    PolicyDeltaV1,
    PolicySummaryV1,
    StructuralEmphasisDeltaV1,
)

if TYPE_CHECKING:
    pass

# Constants
FLOAT_PRECISION: int = 6  # Decimal places for float canonicalization

# Contract versions
ELO_BUCKET_DELTA_CONTRACT_VERSION = "v1"
ADVICE_FACTS_CONTRACT_VERSION = "v1"


def _round_float(value: float, precision: int = FLOAT_PRECISION) -> float:
    """Round float to specified precision for determinism."""
    return round(value, precision)


def _canonical_json(obj: dict[str, object]) -> str:
    """Produce canonical JSON with sorted keys and consistent formatting.

    Args:
        obj: Dictionary to serialize

    Returns:
        Canonical JSON string (sorted keys, no extra whitespace)
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _compute_determinism_hash(data: dict[str, object]) -> str:
    """Compute SHA-256 hash of canonical JSON for determinism verification.

    Args:
        data: Dictionary to hash (will be canonicalized)

    Returns:
        Hash string in format "sha256:<64-char-hex>"
    """
    canonical = _canonical_json(data)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _compute_kl_divergence(
    baseline_moves: list[tuple[str, float]],
    comparison_moves: list[tuple[str, float]],
) -> float:
    """Compute KL divergence from baseline to comparison distribution.

    Uses a small epsilon to handle zero probabilities.

    Args:
        baseline_moves: List of (uci, prob) tuples for baseline
        comparison_moves: List of (uci, prob) tuples for comparison

    Returns:
        KL divergence in bits (natural log, then converted)
    """
    epsilon = 1e-10

    # Build probability maps
    baseline_probs = {uci: prob for uci, prob in baseline_moves}
    comparison_probs = {uci: prob for uci, prob in comparison_moves}

    # Get union of all moves
    all_moves = set(baseline_probs.keys()) | set(comparison_probs.keys())

    kl = 0.0
    for move in all_moves:
        p = baseline_probs.get(move, epsilon)
        q = comparison_probs.get(move, epsilon)
        if p > epsilon:
            kl += p * math.log(p / q)

    # Convert from nats to bits
    return max(0.0, kl / math.log(2))


def _compute_total_variation(
    baseline_moves: list[tuple[str, float]],
    comparison_moves: list[tuple[str, float]],
) -> float:
    """Compute Total Variation distance between two distributions.

    TV = 0.5 * sum(|p_i - q_i|)

    Args:
        baseline_moves: List of (uci, prob) tuples for baseline
        comparison_moves: List of (uci, prob) tuples for comparison

    Returns:
        Total Variation distance in [0.0, 1.0]
    """
    baseline_probs = {uci: prob for uci, prob in baseline_moves}
    comparison_probs = {uci: prob for uci, prob in comparison_moves}

    all_moves = set(baseline_probs.keys()) | set(comparison_probs.keys())

    total_diff = 0.0
    for move in all_moves:
        p = baseline_probs.get(move, 0.0)
        q = comparison_probs.get(move, 0.0)
        total_diff += abs(p - q)

    return min(1.0, 0.5 * total_diff)


def _compute_rank_flips(
    baseline_moves: list[tuple[str, float]],
    comparison_moves: list[tuple[str, float]],
) -> int:
    """Count moves that have different rankings between distributions.

    A "rank flip" occurs when a move that ranks higher in one distribution
    ranks lower in the other (among moves present in both).

    Args:
        baseline_moves: List of (uci, prob) tuples for baseline (ordered)
        comparison_moves: List of (uci, prob) tuples for comparison (ordered)

    Returns:
        Number of pairwise rank inversions among shared moves
    """
    # Get ordered UCIs
    baseline_order = [uci for uci, _ in baseline_moves]
    comparison_order = [uci for uci, _ in comparison_moves]

    # Find shared moves
    shared = set(baseline_order) & set(comparison_order)
    if len(shared) < 2:
        return 0

    # Get relative rankings for shared moves
    baseline_ranks = {uci: i for i, uci in enumerate(baseline_order) if uci in shared}
    comparison_ranks = {uci: i for i, uci in enumerate(comparison_order) if uci in shared}

    # Count inversions (pairs where relative order differs)
    shared_list = list(shared)
    flips = 0
    for i, m1 in enumerate(shared_list):
        for m2 in shared_list[i + 1 :]:
            baseline_order_m1_first = baseline_ranks[m1] < baseline_ranks[m2]
            comparison_order_m1_first = comparison_ranks[m1] < comparison_ranks[m2]
            if baseline_order_m1_first != comparison_order_m1_first:
                flips += 1

    return flips


def _compute_mass_shift_to_top(
    baseline_moves: list[tuple[str, float]],
    comparison_moves: list[tuple[str, float]],
) -> float:
    """Compute probability mass shift toward top-1 move.

    Positive value means comparison has more mass on its top move.

    Args:
        baseline_moves: List of (uci, prob) tuples for baseline
        comparison_moves: List of (uci, prob) tuples for comparison

    Returns:
        Mass shift in [-1.0, 1.0]
    """
    baseline_top_prob = baseline_moves[0][1] if baseline_moves else 0.0
    comparison_top_prob = comparison_moves[0][1] if comparison_moves else 0.0

    return comparison_top_prob - baseline_top_prob


def build_elo_bucket_delta_facts_v1(
    *,
    baseline_bucket: str,
    comparison_bucket: str,
    baseline_policy: PolicySummaryV1,
    comparison_policy: PolicySummaryV1,
    baseline_outcome: OutcomeSummaryV1,
    comparison_outcome: OutcomeSummaryV1,
    baseline_hdi: float,
    comparison_hdi: float,
    baseline_advice_facts_hash: str,
    comparison_advice_facts_hash: str,
    baseline_structural: StructuralEmphasisDeltaV1 | None = None,
    comparison_structural: StructuralEmphasisDeltaV1 | None = None,
    generated_at: datetime | None = None,
) -> EloBucketDeltaFactsV1:
    """Build EloBucketDeltaFactsV1 from pre-computed signals.

    This is a pure function: given the same inputs and timestamp, it produces
    identical output (byte-stable JSON).

    Args:
        baseline_bucket: Baseline skill bucket ID (e.g., "1200_1399")
        comparison_bucket: Comparison skill bucket ID (e.g., "1600_1799")
        baseline_policy: Policy summary for baseline bucket
        comparison_policy: Policy summary for comparison bucket
        baseline_outcome: Outcome summary for baseline bucket
        comparison_outcome: Outcome summary for comparison bucket
        baseline_hdi: HDI value for baseline bucket
        comparison_hdi: HDI value for comparison bucket
        baseline_advice_facts_hash: Determinism hash from baseline AdviceFacts
        comparison_advice_facts_hash: Determinism hash from comparison AdviceFacts
        baseline_structural: Structural emphasis for baseline (optional)
        comparison_structural: Structural emphasis for comparison (optional)
        generated_at: Override timestamp (for determinism tests); uses UTC now if None

    Returns:
        EloBucketDeltaFactsV1 artifact with determinism hash
    """
    # Use provided timestamp or current UTC
    timestamp = generated_at or datetime.now(UTC)

    # Convert policy summaries to (uci, prob) lists
    baseline_moves = [(m.uci, m.prob) for m in baseline_policy.top_moves]
    comparison_moves = [(m.uci, m.prob) for m in comparison_policy.top_moves]

    # Compute policy deltas
    kl_div = _round_float(_compute_kl_divergence(baseline_moves, comparison_moves))
    tv_dist = _round_float(_compute_total_variation(baseline_moves, comparison_moves))
    rank_flips = _compute_rank_flips(baseline_moves, comparison_moves)
    mass_shift = _round_float(_compute_mass_shift_to_top(baseline_moves, comparison_moves))

    policy_delta = PolicyDeltaV1(
        kl_divergence=kl_div,
        total_variation=tv_dist,
        rank_flips=rank_flips,
        mass_shift_to_top=mass_shift,
    )

    # Compute outcome deltas
    delta_p_win = _round_float(comparison_outcome.p_win - baseline_outcome.p_win)
    delta_p_draw = _round_float(comparison_outcome.p_draw - baseline_outcome.p_draw)
    delta_p_loss = _round_float(comparison_outcome.p_loss - baseline_outcome.p_loss)

    # Check monotonicity: higher skill should generally correlate with higher win rate
    # Assuming comparison_bucket represents higher skill
    win_rate_monotonic = delta_p_win >= 0

    outcome_delta = OutcomeDeltaV1(
        delta_p_win=delta_p_win,
        delta_p_draw=delta_p_draw,
        delta_p_loss=delta_p_loss,
        win_rate_monotonic=win_rate_monotonic,
    )

    # Compute difficulty delta
    delta_hdi = _round_float(comparison_hdi - baseline_hdi)
    difficulty_delta = DifficultyDeltaV1(delta_hdi=delta_hdi)

    # Compute structural delta (optional)
    structural_delta: StructuralEmphasisDeltaV1 | None = None
    if baseline_structural is not None and comparison_structural is not None:
        mobility_delta: float | None = None
        weak_sq_delta: float | None = None
        king_safety_delta: float | None = None

        if (
            baseline_structural.mobility_emphasis_delta is not None
            and comparison_structural.mobility_emphasis_delta is not None
        ):
            mobility_delta = _round_float(
                comparison_structural.mobility_emphasis_delta
                - baseline_structural.mobility_emphasis_delta
            )

        if (
            baseline_structural.weak_square_sensitivity_delta is not None
            and comparison_structural.weak_square_sensitivity_delta is not None
        ):
            weak_sq_delta = _round_float(
                comparison_structural.weak_square_sensitivity_delta
                - baseline_structural.weak_square_sensitivity_delta
            )

        if (
            baseline_structural.king_safety_weight_delta is not None
            and comparison_structural.king_safety_weight_delta is not None
        ):
            king_safety_delta = _round_float(
                comparison_structural.king_safety_weight_delta
                - baseline_structural.king_safety_weight_delta
            )

        # Only include if at least one field is populated
        if any(v is not None for v in [mobility_delta, weak_sq_delta, king_safety_delta]):
            structural_delta = StructuralEmphasisDeltaV1(
                mobility_emphasis_delta=mobility_delta,
                weak_square_sensitivity_delta=weak_sq_delta,
                king_safety_weight_delta=king_safety_delta,
            )

    # Source contract versions
    source_contracts = EloBucketDeltaSourceContractsV1(
        elo_bucket_delta_contract=ELO_BUCKET_DELTA_CONTRACT_VERSION,
        advice_facts_contract=ADVICE_FACTS_CONTRACT_VERSION,
    )

    # Build artifact data for hashing
    artifact_data: dict[str, object] = {
        "schemaVersion": "elo_bucket_delta_facts.v1",
        "generatedAt": timestamp.isoformat(),
        "baselineBucket": baseline_bucket,
        "comparisonBucket": comparison_bucket,
        "sourceAdviceFactsHashes": [
            baseline_advice_facts_hash,
            comparison_advice_facts_hash,
        ],
        "policyDelta": {
            "klDivergence": policy_delta.kl_divergence,
            "totalVariation": policy_delta.total_variation,
            "rankFlips": policy_delta.rank_flips,
            "massShiftToTop": policy_delta.mass_shift_to_top,
        },
        "outcomeDelta": {
            "deltaPWin": outcome_delta.delta_p_win,
            "deltaPDraw": outcome_delta.delta_p_draw,
            "deltaPLoss": outcome_delta.delta_p_loss,
            "winRateMonotonic": outcome_delta.win_rate_monotonic,
        },
        "difficultyDelta": {
            "deltaHDI": difficulty_delta.delta_hdi,
        },
        "structuralDelta": (
            {
                "mobilityEmphasisDelta": structural_delta.mobility_emphasis_delta,
                "weakSquareSensitivityDelta": structural_delta.weak_square_sensitivity_delta,
                "kingSafetyWeightDelta": structural_delta.king_safety_weight_delta,
            }
            if structural_delta
            else None
        ),
        "sourceContractVersions": {
            "eloBucketDeltaContract": source_contracts.elo_bucket_delta_contract,
            "adviceFactsContract": source_contracts.advice_facts_contract,
        },
    }

    # Compute determinism hash
    determinism_hash = _compute_determinism_hash(artifact_data)

    # Build final artifact
    return EloBucketDeltaFactsV1(
        schema_version="elo_bucket_delta_facts.v1",
        generated_at=timestamp,
        baseline_bucket=baseline_bucket,
        comparison_bucket=comparison_bucket,
        source_advice_facts_hashes=[
            baseline_advice_facts_hash,
            comparison_advice_facts_hash,
        ],
        policy_delta=policy_delta,
        outcome_delta=outcome_delta,
        difficulty_delta=difficulty_delta,
        structural_delta=structural_delta,
        determinism_hash=determinism_hash,
        source_contract_versions=source_contracts,
    )
