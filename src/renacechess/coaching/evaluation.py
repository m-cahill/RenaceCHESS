"""Coaching evaluation harness (M21).

Offline evaluation of CoachingDraftV1 artifacts against source facts.
Scores drafts on factCoverage, hallucinationRate, bucketAlignment,
deltaFaithfulness, and verbosityScore.

Key invariants:
- No human users, no UI, no live API calls
- Deterministic: same inputs → identical outputs
- Rule-based hallucination detection (no embeddings, no second LLM)

See: COACHING_TRANSLATION_PROMPT_v1.md
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from renacechess.contracts.models import (
    CoachingEvaluationMetricsV1,
    CoachingEvaluationV1,
    HallucinationMetricsV1,
)

if TYPE_CHECKING:
    from renacechess.contracts.models import (
        AdviceFactsV1,
        CoachingDraftV1,
        EloBucketDeltaFactsV1,
    )

# =============================================================================
# Forbidden Terms (documented in COACHING_TRANSLATION_PROMPT_v1.md)
# =============================================================================

FORBIDDEN_TERMS: set[str] = {
    "engine",
    "stockfish",
    "leela",
    "centipawn",
    "tablebase",
    "eval",
    "evaluation",
    "computer",
    "silicon",
    "machine analysis",
    "engine move",
    "best move objectively",
    "optimal",
    "refuted",
    "refutation",
}

# Patterns for forbidden numeric formats (engine-style)
FORBIDDEN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"[+-]\d+\.\d+"),  # Engine-style evaluation (+0.7, -1.2)
    re.compile(r"mate in \d+", re.IGNORECASE),  # Mate announcements
    re.compile(r"cp\s*[+-]?\d+"),  # Centipawn notation
]

# Allowed structural vocabulary (must be in facts if used)
STRUCTURAL_VOCABULARY: set[str] = {
    "mobility",
    "king safety",
    "weak square",
    "strong square",
    "pawn structure",
    "development",
    "piece activity",
    "center control",
}

# UCI move pattern
UCI_PATTERN = re.compile(r"\b([a-h][1-8][a-h][1-8][qrbn]?)\b")

# Percentage pattern
PERCENTAGE_PATTERN = re.compile(r"(\d{1,3})%")

# Ideal verbosity bounds (in words)
VERBOSITY_MIN = 20
VERBOSITY_MAX = 150


def _canonical_json(obj: dict[str, object]) -> str:
    """Produce canonical JSON for determinism."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _compute_determinism_hash(data: dict[str, object]) -> str:
    """Compute SHA-256 hash of canonical JSON."""
    canonical = _canonical_json(data)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _count_sentences(text: str) -> int:
    """Count sentences in text (simple heuristic)."""
    # Split on sentence-ending punctuation
    sentences = re.split(r"[.!?]+", text)
    # Filter out empty strings
    return max(1, len([s for s in sentences if s.strip()]))


def _detect_forbidden_terms(text: str) -> list[str]:
    """Detect forbidden terms in text."""
    text_lower = text.lower()
    found = []
    for term in FORBIDDEN_TERMS:
        if term in text_lower:
            found.append(term)
    return found


def _detect_forbidden_patterns(text: str) -> list[str]:
    """Detect forbidden patterns (engine-style numbers, etc.)."""
    found = []
    for pattern in FORBIDDEN_PATTERNS:
        matches = pattern.findall(text)
        found.extend(matches)
    return found


def _extract_uci_moves(text: str) -> list[str]:
    """Extract all UCI-format moves from text."""
    return UCI_PATTERN.findall(text)


def _extract_percentages(text: str) -> list[int]:
    """Extract all percentage values from text."""
    matches = PERCENTAGE_PATTERN.findall(text)
    return [int(m) for m in matches]


def _get_valid_moves(
    advice_facts: AdviceFactsV1,
) -> set[str]:
    """Get set of valid UCI moves from facts."""
    moves = {m.uci for m in advice_facts.policy.top_moves}
    moves.add(advice_facts.policy.recommended_move.uci)
    return moves


def _get_valid_percentages(
    advice_facts: AdviceFactsV1,
    delta_facts: EloBucketDeltaFactsV1 | None,
) -> set[int]:
    """Get set of valid percentage values from facts (rounded)."""
    valid = set()

    # Outcome probabilities
    valid.add(round(advice_facts.outcome.p_win * 100))
    valid.add(round(advice_facts.outcome.p_draw * 100))
    valid.add(round(advice_facts.outcome.p_loss * 100))

    # Move probabilities
    for m in advice_facts.policy.top_moves:
        valid.add(round(m.prob * 100))

    # HDI as percentage
    valid.add(round(advice_facts.hdi.value * 100))

    # Delta facts if present
    if delta_facts:
        # Delta percentages (absolute values)
        delta_win = round(abs(delta_facts.outcome_delta.delta_p_win * 100))
        valid.add(delta_win)

    return valid


def _detect_unsupported_structural_claims(
    text: str,
    advice_facts: AdviceFactsV1,
) -> list[str]:
    """Detect structural vocabulary not supported by facts."""
    unsupported = []
    text_lower = text.lower()

    # Check if structural cognition is present
    has_structural = advice_facts.structural_cognition is not None

    for term in STRUCTURAL_VOCABULARY:
        if term in text_lower:
            # If no structural cognition, this is unsupported
            if not has_structural:
                unsupported.append(term)
            else:
                # Check if the specific structural field is present
                struct = advice_facts.structural_cognition
                if struct is None:
                    unsupported.append(term)
                elif term == "mobility" and struct.mobility_delta is None:
                    unsupported.append(term)
                elif term == "weak square" and struct.weak_squares_delta is None:
                    unsupported.append(term)
                elif term == "strong square" and struct.strong_squares_delta is None:
                    unsupported.append(term)

    return unsupported


def _compute_fact_coverage(
    draft: CoachingDraftV1,
    advice_facts: AdviceFactsV1,
) -> float:
    """Compute fraction of salient facts that are referenced.

    Salient facts:
    - Skill bucket
    - Recommended move
    - Win probability
    - HDI value
    """
    text_lower = draft.draft_text.lower()
    salient_count = 4  # skill bucket, recommended move, win prob, hdi
    found = 0

    # Check skill bucket
    if advice_facts.context.skill_bucket.lower() in text_lower:
        found += 1

    # Check recommended move
    rec = advice_facts.policy.recommended_move.uci
    if rec in draft.draft_text:
        found += 1

    # Check win probability (as percentage)
    win_pct = round(advice_facts.outcome.p_win * 100)
    if str(win_pct) in draft.draft_text:
        found += 1

    # Check HDI value
    hdi_str = f"{advice_facts.hdi.value:.2f}"
    if hdi_str in draft.draft_text:
        found += 1

    return found / salient_count if salient_count > 0 else 1.0


def _check_bucket_alignment(
    draft: CoachingDraftV1,
    advice_facts: AdviceFactsV1,
) -> bool:
    """Check if language matches the target skill bucket.

    Simple heuristic: bucket ID should appear in text.
    """
    return advice_facts.context.skill_bucket in draft.draft_text


def _compute_delta_faithfulness(
    draft: CoachingDraftV1,
    delta_facts: EloBucketDeltaFactsV1 | None,
) -> float:
    """Compute accuracy of Elo delta claims.

    Returns 1.0 if:
    - No delta facts (nothing to verify)
    - Delta facts referenced correctly (buckets mentioned)
    """
    if delta_facts is None:
        return 1.0

    text = draft.draft_text
    baseline_mentioned = delta_facts.baseline_bucket in text
    comparison_mentioned = delta_facts.comparison_bucket in text

    if baseline_mentioned and comparison_mentioned:
        return 1.0
    elif baseline_mentioned or comparison_mentioned:
        return 0.5
    else:
        return 0.0


def _compute_verbosity_score(text: str) -> float:
    """Compute verbosity score.

    0.0 = too short (< VERBOSITY_MIN words)
    0.5 = ideal (VERBOSITY_MIN to VERBOSITY_MAX words)
    1.0 = too long (> VERBOSITY_MAX words)
    """
    word_count = len(text.split())

    if word_count < VERBOSITY_MIN:
        # Too short: score decreases as we get further from min
        return max(0.0, word_count / VERBOSITY_MIN * 0.5)
    elif word_count <= VERBOSITY_MAX:
        # Ideal range
        return 0.5
    else:
        # Too long: score increases toward 1.0
        excess = word_count - VERBOSITY_MAX
        return min(1.0, 0.5 + excess / VERBOSITY_MAX * 0.5)


def evaluate_coaching_draft(
    draft: CoachingDraftV1,
    advice_facts: AdviceFactsV1,
    delta_facts: EloBucketDeltaFactsV1 | None = None,
    evaluated_at: datetime | None = None,
) -> CoachingEvaluationV1:
    """Evaluate a coaching draft against source facts.

    This is the main entry point for offline evaluation.

    Args:
        draft: The coaching draft to evaluate
        advice_facts: Source AdviceFactsV1 (must match draft's hash)
        delta_facts: Optional source EloBucketDeltaFactsV1
        evaluated_at: Override timestamp (for determinism tests)

    Returns:
        CoachingEvaluationV1 artifact with metrics and verdict

    Quality gates:
    - hallucinationRate < 0.2
    - factCoverage >= 0.5
    - bucketAlignment = True
    """
    timestamp = evaluated_at or datetime.now(UTC)

    # Detect hallucinations
    forbidden_terms = _detect_forbidden_terms(draft.draft_text)
    forbidden_patterns = _detect_forbidden_patterns(draft.draft_text)

    # Check moves
    mentioned_moves = _extract_uci_moves(draft.draft_text)
    valid_moves = _get_valid_moves(advice_facts)
    unsupported_moves = [m for m in mentioned_moves if m not in valid_moves]

    # Check percentages
    mentioned_pcts = _extract_percentages(draft.draft_text)
    valid_pcts = _get_valid_percentages(advice_facts, delta_facts)
    unsupported_pcts = [str(p) + "%" for p in mentioned_pcts if p not in valid_pcts]

    # Check structural claims
    unsupported_structural = _detect_unsupported_structural_claims(draft.draft_text, advice_facts)

    # Count sentences
    total_sentences = _count_sentences(draft.draft_text)

    # Count unsupported claims
    total_unsupported = (
        len(forbidden_terms)
        + len(forbidden_patterns)
        + len(unsupported_moves)
        + len(unsupported_pcts)
        + len(unsupported_structural)
    )

    # Hallucination rate
    hallucination_rate = min(1.0, total_unsupported / max(1, total_sentences))

    # Build hallucination metrics
    hallucination_details = HallucinationMetricsV1(
        forbidden_terms_found=forbidden_terms + forbidden_patterns,
        unsupported_moves=unsupported_moves,
        unsupported_percentages=unsupported_pcts,
        unsupported_structural_claims=unsupported_structural,
        total_unsupported_claims=total_unsupported,
        total_sentences=total_sentences,
    )

    # Compute other metrics
    fact_coverage = _compute_fact_coverage(draft, advice_facts)
    bucket_alignment = _check_bucket_alignment(draft, advice_facts)
    delta_faithfulness = _compute_delta_faithfulness(draft, delta_facts)
    verbosity_score = _compute_verbosity_score(draft.draft_text)

    # Build metrics
    metrics = CoachingEvaluationMetricsV1(
        fact_coverage=fact_coverage,
        hallucination_rate=hallucination_rate,
        bucket_alignment=bucket_alignment,
        delta_faithfulness=delta_faithfulness,
        verbosity_score=verbosity_score,
    )

    # Determine pass/fail
    failure_reasons: list[str] = []

    if hallucination_rate >= 0.2:
        failure_reasons.append(f"hallucinationRate {hallucination_rate:.2f} >= 0.2")
    if fact_coverage < 0.5:
        failure_reasons.append(f"factCoverage {fact_coverage:.2f} < 0.5")
    if not bucket_alignment:
        failure_reasons.append("bucketAlignment is False")

    passed = len(failure_reasons) == 0

    # Build artifact data for hashing
    artifact_data: dict[str, object] = {
        "schemaVersion": "coaching_evaluation.v1",
        "evaluatedAt": timestamp.isoformat(),
        "sourceDraftHash": draft.determinism_hash,
        "sourceAdviceFactsHash": draft.source_advice_facts_hash,
        "sourceDeltaFactsHash": draft.source_delta_facts_hash,
        "metrics": {
            "factCoverage": metrics.fact_coverage,
            "hallucinationRate": metrics.hallucination_rate,
            "bucketAlignment": metrics.bucket_alignment,
            "deltaFaithfulness": metrics.delta_faithfulness,
            "verbosityScore": metrics.verbosity_score,
        },
        "hallucinationDetails": {
            "forbiddenTermsFound": hallucination_details.forbidden_terms_found,
            "unsupportedMoves": hallucination_details.unsupported_moves,
            "unsupportedPercentages": hallucination_details.unsupported_percentages,
            "unsupportedStructuralClaims": hallucination_details.unsupported_structural_claims,
            "totalUnsupportedClaims": hallucination_details.total_unsupported_claims,
            "totalSentences": hallucination_details.total_sentences,
        },
        "passed": passed,
        "failureReasons": failure_reasons,
    }

    determinism_hash = _compute_determinism_hash(artifact_data)

    return CoachingEvaluationV1(
        schema_version="coaching_evaluation.v1",
        evaluated_at=timestamp,
        source_draft_hash=draft.determinism_hash,
        source_advice_facts_hash=draft.source_advice_facts_hash,
        source_delta_facts_hash=draft.source_delta_facts_hash,
        metrics=metrics,
        hallucination_details=hallucination_details,
        passed=passed,
        failure_reasons=failure_reasons,
        determinism_hash=determinism_hash,
    )
