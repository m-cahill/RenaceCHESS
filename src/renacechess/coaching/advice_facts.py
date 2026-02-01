"""AdviceFacts builder — deterministic facts-only artifact generator (M19).

This module provides a pure function that constructs AdviceFactsV1 from
pre-computed signals. It does NOT orchestrate provider calls.

Key invariants:
- Deterministic: same inputs → identical outputs (byte-stable JSON)
- Facts-only: no prose generation, no LLM calls
- Canonical ordering: topMoves by prob desc then UCI asc; keys alphabetically sorted

Float canonicalization:
- All floats are rounded to 6 decimal places before hashing
- This ensures determinism across platforms with different float representations

See: ADR-COACHING-001, ADVICE_FACTS_CONTRACT_v1.md
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from renacechess.contracts.models import (
    AdviceFactsContextV1,
    AdviceFactsHDIV1,
    AdviceFactsInputsV1,
    AdviceFactsMoveV1,
    AdviceFactsOutcomeV1,
    AdviceFactsPolicyV1,
    AdviceFactsPositionV1,
    AdviceFactsSourceContractsV1,
    AdviceFactsStructuralCognitionV1,
    AdviceFactsV1,
)

if TYPE_CHECKING:
    pass

# Constants
TOP_K: int = 5  # Default number of top moves to include
FLOAT_PRECISION: int = 6  # Decimal places for float canonicalization

# Contract versions
ADVICE_FACTS_CONTRACT_VERSION = "v1"
INPUT_SEMANTICS_CONTRACT_VERSION = "v1.0"
STRUCTURAL_COGNITION_CONTRACT_VERSION = "v1"


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


def _sort_moves(
    moves: list[tuple[str, float]], san_list: list[str] | None = None
) -> list[tuple[str, float, str | None]]:
    """Sort moves by probability descending, then UCI ascending for ties.

    Args:
        moves: List of (uci, prob) tuples
        san_list: Optional list of SAN strings (same order as moves)

    Returns:
        Sorted list of (uci, prob, san) tuples
    """
    # Pair with SAN if available
    combined: list[tuple[str, float, str | None]]
    if san_list and len(san_list) == len(moves):
        combined = [(uci, prob, san) for (uci, prob), san in zip(moves, san_list)]
    else:
        combined = [(uci, prob, None) for uci, prob in moves]

    # Sort: by prob descending, then by UCI ascending for ties
    return sorted(combined, key=lambda x: (-x[1], x[0]))


def build_advice_facts_v1(
    inputs: AdviceFactsInputsV1,
    generated_at: datetime | None = None,
) -> AdviceFactsV1:
    """Build AdviceFactsV1 from pre-computed signals.

    This is a pure function: given the same inputs and timestamp, it produces
    identical output (byte-stable JSON).

    Args:
        inputs: Pre-computed signals (policy, outcome, HDI, context, etc.)
        generated_at: Override timestamp (for determinism tests); uses UTC now if None

    Returns:
        AdviceFactsV1 artifact with determinism hash

    Example:
        >>> inputs = AdviceFactsInputsV1(
        ...     fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
        ...     sideToMove="black",
        ...     skillBucket="1200_1399",
        ...     topMoves=[("e7e5", 0.35), ("c7c5", 0.25), ("e7e6", 0.15)],
        ...     pWin=0.45, pDraw=0.30, pLoss=0.25,
        ...     hdiValue=0.42,
        ... )
        >>> facts = build_advice_facts_v1(inputs)
        >>> facts.version
        '1.0'
    """
    # Use provided timestamp or current UTC
    timestamp = generated_at or datetime.now(UTC)

    # Build position
    position = AdviceFactsPositionV1(
        fen=inputs.fen,
        side_to_move=inputs.side_to_move,
    )

    # Build context
    context = AdviceFactsContextV1(
        skill_bucket=inputs.skill_bucket,
        time_control_bucket=inputs.time_control_bucket,
        time_pressure_bucket=inputs.time_pressure_bucket,
    )

    # Sort and limit moves
    sorted_moves = _sort_moves(inputs.top_moves, inputs.top_moves_san)[:TOP_K]

    # Build top moves
    top_moves = [
        AdviceFactsMoveV1(
            uci=uci,
            san=san,
            prob=_round_float(prob),
        )
        for uci, prob, san in sorted_moves
    ]

    # Recommended move is the first (highest probability)
    recommended_move = top_moves[0]

    policy = AdviceFactsPolicyV1(
        top_moves=top_moves,
        recommended_move=recommended_move,
    )

    # Build outcome
    outcome = AdviceFactsOutcomeV1(
        p_win=_round_float(inputs.p_win),
        p_draw=_round_float(inputs.p_draw),
        p_loss=_round_float(inputs.p_loss),
    )

    # Build HDI
    hdi = AdviceFactsHDIV1(
        value=_round_float(inputs.hdi_value),
        entropy=_round_float(inputs.hdi_entropy) if inputs.hdi_entropy is not None else None,
        top_gap_inverted=(
            _round_float(inputs.hdi_top_gap_inverted)
            if inputs.hdi_top_gap_inverted is not None
            else None
        ),
        legal_move_pressure=(
            _round_float(inputs.hdi_legal_move_pressure)
            if inputs.hdi_legal_move_pressure is not None
            else None
        ),
        outcome_sensitivity=(
            _round_float(inputs.hdi_outcome_sensitivity)
            if inputs.hdi_outcome_sensitivity is not None
            else None
        ),
    )

    # Build structural cognition (optional)
    structural_cognition: AdviceFactsStructuralCognitionV1 | None = None
    has_structural = any(
        [
            inputs.mobility_delta is not None,
            inputs.weak_squares_delta is not None,
            inputs.strong_squares_delta is not None,
            inputs.structural_summary is not None,
        ]
    )
    if has_structural:
        structural_cognition = AdviceFactsStructuralCognitionV1(
            mobility_delta=(
                _round_float(inputs.mobility_delta) if inputs.mobility_delta is not None else None
            ),
            weak_squares_delta=(
                _round_float(inputs.weak_squares_delta)
                if inputs.weak_squares_delta is not None
                else None
            ),
            strong_squares_delta=(
                _round_float(inputs.strong_squares_delta)
                if inputs.strong_squares_delta is not None
                else None
            ),
            summary=inputs.structural_summary,
        )

    # Source contract versions
    source_contracts = AdviceFactsSourceContractsV1(
        advice_facts_contract=ADVICE_FACTS_CONTRACT_VERSION,
        input_semantics_contract=INPUT_SEMANTICS_CONTRACT_VERSION,
        structural_cognition_contract=(
            STRUCTURAL_COGNITION_CONTRACT_VERSION if has_structural else None
        ),
    )

    # Build the artifact without hash first (to compute hash)
    artifact_data = {
        "version": "1.0",
        "generatedAt": timestamp.isoformat(),
        "position": {
            "fen": position.fen,
            "sideToMove": position.side_to_move,
        },
        "context": {
            "skillBucket": context.skill_bucket,
            "timeControlBucket": context.time_control_bucket,
            "timePressureBucket": context.time_pressure_bucket,
        },
        "policy": {
            "topMoves": [
                {"uci": m.uci, "san": m.san, "prob": m.prob} for m in top_moves
            ],
            "recommendedMove": {
                "uci": recommended_move.uci,
                "san": recommended_move.san,
                "prob": recommended_move.prob,
            },
        },
        "outcome": {
            "pWin": outcome.p_win,
            "pDraw": outcome.p_draw,
            "pLoss": outcome.p_loss,
        },
        "hdi": {
            "value": hdi.value,
            "entropy": hdi.entropy,
            "topGapInverted": hdi.top_gap_inverted,
            "legalMovePressure": hdi.legal_move_pressure,
            "outcomeSensitivity": hdi.outcome_sensitivity,
        },
        "structuralCognition": (
            {
                "mobilityDelta": structural_cognition.mobility_delta,
                "weakSquaresDelta": structural_cognition.weak_squares_delta,
                "strongSquaresDelta": structural_cognition.strong_squares_delta,
                "summary": structural_cognition.summary,
            }
            if structural_cognition
            else None
        ),
        "explanationHints": None,  # Not populated in M19
        "sourceContractVersions": {
            "adviceFactsContract": source_contracts.advice_facts_contract,
            "inputSemanticsContract": source_contracts.input_semantics_contract,
            "structuralCognitionContract": source_contracts.structural_cognition_contract,
        },
    }

    # Compute determinism hash
    determinism_hash = _compute_determinism_hash(artifact_data)  # type: ignore[arg-type]

    # Build final artifact
    return AdviceFactsV1(
        version="1.0",
        generated_at=timestamp,
        position=position,
        context=context,
        policy=policy,
        outcome=outcome,
        hdi=hdi,
        structural_cognition=structural_cognition,
        explanation_hints=None,  # Placeholder for M20+
        determinism_hash=determinism_hash,
        source_contract_versions=source_contracts,
    )

