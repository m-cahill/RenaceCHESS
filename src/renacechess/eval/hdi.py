"""Human Difficulty Index (HDI) computation for M07.

HDI v1 is a deterministic, explainable scalar measure of cognitive difficulty
for humans at a given skill/time level. It is computed from existing evaluation
signals (policy entropy, top-gap, legal move count, outcome sensitivity).

HDI v1 Formula (fixed, documented):
    HDI = clamp01(
        0.40 * norm_entropy +
        0.25 * norm_top_gap_inverted +
        0.20 * norm_legal_move_pressure +
        0.15 * norm_outcome_sensitivity
    )

Where:
    - norm_entropy: Normalized policy entropy (0-1)
    - norm_top_gap_inverted: 1 - normalized top gap (higher = more ambiguous)
    - norm_legal_move_pressure: Legal moves / 40 (capped at 1.0)
    - norm_outcome_sensitivity: Proxy (entropy * (1 - top_gap)) when no outcome head exists
"""

from typing import Any, Literal

# HDI v1 specification constants
HDI_SPEC_VERSION = 1

# Component weights (fixed, documented)
ENTROPY_WEIGHT = 0.40
TOP_GAP_INVERTED_WEIGHT = 0.25
LEGAL_MOVE_PRESSURE_WEIGHT = 0.20
OUTCOME_SENSITIVITY_WEIGHT = 0.15

# Normalization constants
MAX_HUMAN_RELEVANT_LEGAL_MOVES = 40
MAX_ENTROPY_BITS = 10.0  # Reasonable upper bound for chess policy entropy


def clamp01(value: float) -> float:
    """Clamp value to [0.0, 1.0] range.

    Args:
        value: Input value.

    Returns:
        Clamped value in [0.0, 1.0].
    """
    return max(0.0, min(1.0, value))


def normalize_entropy(entropy: float) -> float:
    """Normalize policy entropy to [0.0, 1.0].

    Args:
        entropy: Shannon entropy in bits.

    Returns:
        Normalized entropy in [0.0, 1.0].
    """
    return clamp01(entropy / MAX_ENTROPY_BITS)


def normalize_top_gap_inverted(top_gap: float) -> float:
    """Normalize and invert top gap (higher = more ambiguous).

    Args:
        top_gap: Top gap value (p1 - p2), typically in [0.0, 1.0].

    Returns:
        Inverted normalized gap: 1 - clamp01(top_gap).
    """
    return 1.0 - clamp01(top_gap)


def normalize_legal_move_pressure(legal_moves_count: int) -> float:
    """Normalize legal move count to [0.0, 1.0] using human-relevant ceiling.

    Args:
        legal_moves_count: Number of legal moves.

    Returns:
        Normalized pressure: clamp01(legal_moves_count / 40).
    """
    return clamp01(legal_moves_count / MAX_HUMAN_RELEVANT_LEGAL_MOVES)


def compute_outcome_sensitivity_proxy(
    entropy: float, top_gap: float
) -> tuple[float, Literal["proxy"]]:
    """Compute outcome sensitivity proxy when no outcome head exists.

    Proxy formula: entropy * (1 - top_gap)

    Args:
        entropy: Policy entropy (normalized or raw).
        top_gap: Top gap value.

    Returns:
        Tuple of (proxy value in [0.0, 1.0], "proxy" source tag).
    """
    norm_ent = normalize_entropy(entropy)
    norm_gap_inv = normalize_top_gap_inverted(top_gap)
    proxy_value = clamp01(norm_ent * norm_gap_inv)
    return proxy_value, "proxy"


def compute_hdi_v1(
    entropy: float,
    top_gap: float,
    legal_moves_count: int,
    outcome_sensitivity: float | None = None,
    outcome_sensitivity_source: Literal["proxy", "outcome_head"] | None = None,
) -> dict[str, Any]:
    """Compute Human Difficulty Index (HDI) v1.

    Args:
        entropy: Policy entropy in bits.
        top_gap: Top gap (p1 - p2).
        legal_moves_count: Number of legal moves.
        outcome_sensitivity: Outcome sensitivity value (if available from outcome head).
        outcome_sensitivity_source: Source of outcome sensitivity ("proxy" or "outcome_head").

    Returns:
        Dictionary with:
            - value: HDI scalar in [0.0, 1.0]
            - specVersion: HDI spec version (1)
            - components: Dictionary with component values and metadata
    """
    # Normalize components
    norm_ent = normalize_entropy(entropy)
    norm_gap_inv = normalize_top_gap_inverted(top_gap)
    norm_legal = normalize_legal_move_pressure(legal_moves_count)

    # Compute outcome sensitivity (use proxy if not provided)
    if outcome_sensitivity is None:
        norm_outcome, source = compute_outcome_sensitivity_proxy(entropy, top_gap)
        outcome_source = source
    else:
        norm_outcome = clamp01(outcome_sensitivity)
        outcome_source = outcome_sensitivity_source or "outcome_head"

    # Compute weighted HDI
    hdi_value = (
        ENTROPY_WEIGHT * norm_ent
        + TOP_GAP_INVERTED_WEIGHT * norm_gap_inv
        + LEGAL_MOVE_PRESSURE_WEIGHT * norm_legal
        + OUTCOME_SENSITIVITY_WEIGHT * norm_outcome
    )
    hdi_value = clamp01(hdi_value)

    # Build components dictionary
    components = {
        "entropy": norm_ent,
        "topGapInverted": norm_gap_inv,
        "legalMovePressure": norm_legal,
        "outcomeSensitivity": {
            "value": norm_outcome,
            "source": outcome_source,
            "note": (
                "entropy * (1 - topGap); replaced when outcome head exists"
                if outcome_source == "proxy"
                else "from outcome head"
            ),
        },
    }

    return {
        "value": hdi_value,
        "specVersion": HDI_SPEC_VERSION,
        "components": components,
    }

