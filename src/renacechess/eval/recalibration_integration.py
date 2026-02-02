"""M26: Pure integration function for applying runtime recalibration to evaluation results.

This module provides a pure, testable function that applies recalibration to policy
and outcome predictions based on a gate and parameters. It contains no file I/O,
no CLI dependencies, and no dataset dependencies.

See docs/milestones/PhaseD/M26/M26_plan.md for the governing plan.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from renacechess.contracts.models import (
        PolicyMove,
        RecalibrationGateV1,
        RecalibrationParametersV1,
    )


def apply_runtime_recalibration_to_policy_moves(
    policy_moves: list[PolicyMove],
    skill_bucket_id: str | None,
    gate: RecalibrationGateV1 | None,
    params: RecalibrationParametersV1 | None,
) -> tuple[list[PolicyMove], bool]:
    """Apply runtime recalibration to policy moves if gate is enabled and scoped.

    This is a pure function that takes policy moves and returns recalibrated moves
    (or unchanged moves if recalibration is not applied). No file I/O or external
    dependencies.

    Args:
        policy_moves: List of PolicyMove objects with probabilities.
        skill_bucket_id: Canonical skill bucket ID (e.g., "lt_800").
        gate: RecalibrationGateV1 artifact (None = no recalibration).
        params: RecalibrationParametersV1 artifact (required if gate.enabled=True).

    Returns:
        Tuple of (recalibrated_policy_moves, was_applied):
        - If gate is None or disabled: returns input moves unchanged, was_applied=False
        - If gate is enabled and scoped to policy/both: returns scaled moves, was_applied=True
        - If gate is enabled but scope is outcome-only: returns input moves unchanged, was_applied=False
    """
    from renacechess.eval.runtime_recalibration import (
        apply_recalibration_if_enabled,
    )

    # No-op if gate is not provided or disabled
    if gate is None or not gate.enabled or skill_bucket_id is None:
        return policy_moves, False

    # No-op if scope is outcome-only
    if gate.scope not in ["policy", "both"]:
        return policy_moves, False

    # Extract probabilities
    move_probs = [move.p for move in policy_moves]
    if not move_probs:
        return policy_moves, False

    # Apply recalibration
    scaled_probs, _metadata = apply_recalibration_if_enabled(
        move_probs,
        skill_bucket_id,
        gate,
        params,
    )

    # Update PolicyMove objects with scaled probabilities
    from renacechess.contracts.models import PolicyMove

    recalibrated_moves = [
        PolicyMove(uci=move.uci, san=move.san, p=scaled_probs[i])
        for i, move in enumerate(policy_moves)
    ]

    # Re-sort by probability (descending)
    recalibrated_moves.sort(key=lambda x: x.p, reverse=True)

    return recalibrated_moves, True


def apply_runtime_recalibration_to_outcome(
    p_win: float,
    p_draw: float,
    p_loss: float,
    skill_bucket_id: str | None,
    gate: RecalibrationGateV1 | None,
    params: RecalibrationParametersV1 | None,
) -> tuple[tuple[float, float, float], bool]:
    """Apply runtime recalibration to outcome probabilities if gate is enabled and scoped.

    This is a pure function that takes outcome probabilities and returns recalibrated
    probabilities (or unchanged probabilities if recalibration is not applied).

    Args:
        p_win: Probability of win.
        p_draw: Probability of draw.
        p_loss: Probability of loss.
        skill_bucket_id: Canonical skill bucket ID (e.g., "lt_800").
        gate: RecalibrationGateV1 artifact (None = no recalibration).
        params: RecalibrationParametersV1 artifact (required if gate.enabled=True).

    Returns:
        Tuple of ((p_win, p_draw, p_loss), was_applied):
        - If gate is None or disabled: returns input probabilities unchanged, was_applied=False
        - If gate is enabled and scoped to outcome/both: returns scaled probabilities, was_applied=True
        - If gate is enabled but scope is policy-only: returns input probabilities unchanged, was_applied=False
    """
    from renacechess.eval.runtime_recalibration import (
        apply_recalibration_to_outcome_if_enabled,
    )

    # No-op if gate is not provided or disabled
    if gate is None or not gate.enabled or skill_bucket_id is None:
        return (p_win, p_draw, p_loss), False

    # No-op if scope is policy-only
    if gate.scope not in ["outcome", "both"]:
        return (p_win, p_draw, p_loss), False

    # Apply recalibration
    (scaled_w, scaled_d, scaled_l), _metadata = (
        apply_recalibration_to_outcome_if_enabled(
            p_win,
            p_draw,
            p_loss,
            skill_bucket_id,
            gate,
            params,
        )
    )

    return (scaled_w, scaled_d, scaled_l), True

