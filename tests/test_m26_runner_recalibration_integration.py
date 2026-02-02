"""M26: Unit tests for runner recalibration integration functions.

These tests exercise the pure integration functions extracted from eval/runner.py
to restore coverage without requiring datasets, CLI, or E2E tests.

See docs/milestones/PhaseD/M26/M26_plan.md for the governing plan.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from renacechess.contracts.models import (
    PolicyMove,
    RecalibrationGateV1,
    RecalibrationParametersV1,
)
from renacechess.eval.recalibration_integration import (
    apply_runtime_recalibration_to_outcome,
    apply_runtime_recalibration_to_policy_moves,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def recalibration_gate_disabled() -> RecalibrationGateV1:
    """Create a disabled recalibration gate."""
    return RecalibrationGateV1(
        version="1.0",
        enabled=False,
        parameters_ref=None,
        scope="both",
    )


@pytest.fixture
def recalibration_gate_enabled_policy_only(tmp_path: Path) -> RecalibrationGateV1:
    """Create an enabled gate with policy-only scope."""
    return RecalibrationGateV1(
        version="1.0",
        enabled=True,
        parameters_ref="sha256:" + "a" * 64,
        scope="policy",
    )


@pytest.fixture
def recalibration_gate_enabled_outcome_only(tmp_path: Path) -> RecalibrationGateV1:
    """Create an enabled gate with outcome-only scope."""
    return RecalibrationGateV1(
        version="1.0",
        enabled=True,
        parameters_ref="sha256:" + "a" * 64,
        scope="outcome",
    )


@pytest.fixture
def recalibration_gate_enabled_both(tmp_path: Path) -> RecalibrationGateV1:
    """Create an enabled gate with both scope."""
    return RecalibrationGateV1(
        version="1.0",
        enabled=True,
        parameters_ref="sha256:" + "a" * 64,
        scope="both",
    )


@pytest.fixture
def recalibration_parameters() -> RecalibrationParametersV1:
    """Create recalibration parameters with non-identity temperatures."""
    return RecalibrationParametersV1(
        version="1.0",
        generated_at="2026-02-01T00:00:00Z",
        source_calibration_metrics_hash="sha256:" + "a" * 64,
        source_manifest_hash="a" * 64,
        policy_id="baseline.uniform_random",
        outcome_head_id=None,
        determinism_hash="sha256:" + "b" * 64,
        by_elo_bucket=[
            {
                "elo_bucket": "lt_800",
                "outcome_temperature": 1.0,
                "policy_temperature": 2.0,  # Non-identity to ensure observable change
            },
            {
                "elo_bucket": "800_999",
                "outcome_temperature": 1.0,
                "policy_temperature": 2.0,
            },
        ],
    )


@pytest.fixture
def policy_moves() -> list[PolicyMove]:
    """Create policy moves with non-uniform probabilities."""
    return [
        PolicyMove(uci="e2e4", p=0.4),
        PolicyMove(uci="d2d4", p=0.3),
        PolicyMove(uci="g1f3", p=0.2),
        PolicyMove(uci="c2c4", p=0.1),
    ]


# =============================================================================
# Policy Moves Integration Tests
# =============================================================================


class TestApplyRuntimeRecalibrationToPolicyMoves:
    """Test apply_runtime_recalibration_to_policy_moves function."""

    def test_no_gate_returns_unchanged(
        self, policy_moves: list[PolicyMove]
    ) -> None:
        """No gate provided returns moves unchanged."""
        result_moves, was_applied = apply_runtime_recalibration_to_policy_moves(
            policy_moves, "lt_800", None, None
        )

        assert was_applied is False
        assert result_moves == policy_moves

    def test_gate_disabled_returns_unchanged(
        self,
        policy_moves: list[PolicyMove],
        recalibration_gate_disabled: RecalibrationGateV1,
    ) -> None:
        """Disabled gate returns moves unchanged."""
        result_moves, was_applied = apply_runtime_recalibration_to_policy_moves(
            policy_moves, "lt_800", recalibration_gate_disabled, None
        )

        assert was_applied is False
        assert result_moves == policy_moves

    def test_no_skill_bucket_returns_unchanged(
        self,
        policy_moves: list[PolicyMove],
        recalibration_gate_enabled_policy_only: RecalibrationGateV1,
        recalibration_parameters: RecalibrationParametersV1,
    ) -> None:
        """No skill bucket ID returns moves unchanged."""
        result_moves, was_applied = apply_runtime_recalibration_to_policy_moves(
            policy_moves, None, recalibration_gate_enabled_policy_only, recalibration_parameters
        )

        assert was_applied is False
        assert result_moves == policy_moves

    def test_gate_enabled_policy_scope_applies_scaling(
        self,
        policy_moves: list[PolicyMove],
        recalibration_gate_enabled_policy_only: RecalibrationGateV1,
        recalibration_parameters: RecalibrationParametersV1,
    ) -> None:
        """Enabled gate with policy scope applies recalibration."""
        result_moves, was_applied = apply_runtime_recalibration_to_policy_moves(
            policy_moves,
            "lt_800",
            recalibration_gate_enabled_policy_only,
            recalibration_parameters,
        )

        assert was_applied is True
        # With temperature=2.0, probabilities should be flattened
        assert result_moves[0].p < policy_moves[0].p  # Top prob should be lower
        # Moves should be re-sorted by probability
        assert result_moves[0].p >= result_moves[1].p
        assert result_moves[1].p >= result_moves[2].p

    def test_gate_enabled_both_scope_applies_scaling(
        self,
        policy_moves: list[PolicyMove],
        recalibration_gate_enabled_both: RecalibrationGateV1,
        recalibration_parameters: RecalibrationParametersV1,
    ) -> None:
        """Enabled gate with both scope applies recalibration to policy."""
        result_moves, was_applied = apply_runtime_recalibration_to_policy_moves(
            policy_moves,
            "lt_800",
            recalibration_gate_enabled_both,
            recalibration_parameters,
        )

        assert was_applied is True
        assert result_moves[0].p < policy_moves[0].p

    def test_gate_enabled_outcome_only_returns_unchanged(
        self,
        policy_moves: list[PolicyMove],
        recalibration_gate_enabled_outcome_only: RecalibrationGateV1,
        recalibration_parameters: RecalibrationParametersV1,
    ) -> None:
        """Enabled gate with outcome-only scope does not affect policy."""
        result_moves, was_applied = apply_runtime_recalibration_to_policy_moves(
            policy_moves,
            "lt_800",
            recalibration_gate_enabled_outcome_only,
            recalibration_parameters,
        )

        assert was_applied is False
        assert result_moves == policy_moves

    def test_empty_moves_list_returns_unchanged(
        self,
        recalibration_gate_enabled_policy_only: RecalibrationGateV1,
        recalibration_parameters: RecalibrationParametersV1,
    ) -> None:
        """Empty moves list returns unchanged."""
        empty_moves: list[PolicyMove] = []
        result_moves, was_applied = apply_runtime_recalibration_to_policy_moves(
            empty_moves,
            "lt_800",
            recalibration_gate_enabled_policy_only,
            recalibration_parameters,
        )

        assert was_applied is False
        assert result_moves == empty_moves


# =============================================================================
# Outcome Integration Tests
# =============================================================================


class TestApplyRuntimeRecalibrationToOutcome:
    """Test apply_runtime_recalibration_to_outcome function."""

    def test_no_gate_returns_unchanged(self) -> None:
        """No gate provided returns probabilities unchanged."""
        result_probs, was_applied = apply_runtime_recalibration_to_outcome(
            0.4, 0.3, 0.3, "lt_800", None, None
        )

        assert was_applied is False
        assert result_probs == (0.4, 0.3, 0.3)

    def test_gate_disabled_returns_unchanged(
        self, recalibration_gate_disabled: RecalibrationGateV1
    ) -> None:
        """Disabled gate returns probabilities unchanged."""
        result_probs, was_applied = apply_runtime_recalibration_to_outcome(
            0.4, 0.3, 0.3, "lt_800", recalibration_gate_disabled, None
        )

        assert was_applied is False
        assert result_probs == (0.4, 0.3, 0.3)

    def test_no_skill_bucket_returns_unchanged(
        self,
        recalibration_gate_enabled_outcome_only: RecalibrationGateV1,
        recalibration_parameters: RecalibrationParametersV1,
    ) -> None:
        """No skill bucket ID returns probabilities unchanged."""
        result_probs, was_applied = apply_runtime_recalibration_to_outcome(
            0.4, 0.3, 0.3, None, recalibration_gate_enabled_outcome_only, recalibration_parameters
        )

        assert was_applied is False
        assert result_probs == (0.4, 0.3, 0.3)

    def test_gate_enabled_outcome_scope_applies_scaling(
        self,
        recalibration_gate_enabled_outcome_only: RecalibrationGateV1,
        recalibration_parameters: RecalibrationParametersV1,
    ) -> None:
        """Enabled gate with outcome scope applies recalibration."""
        # With temperature=1.0 for outcome, probabilities should remain similar
        # but the function should still be called
        result_probs, was_applied = apply_runtime_recalibration_to_outcome(
            0.4,
            0.3,
            0.3,
            "lt_800",
            recalibration_gate_enabled_outcome_only,
            recalibration_parameters,
        )

        assert was_applied is True
        # Temperature=1.0 means no change, but function was called
        assert abs(result_probs[0] - 0.4) < 0.001
        assert abs(result_probs[1] - 0.3) < 0.001
        assert abs(result_probs[2] - 0.3) < 0.001

    def test_gate_enabled_both_scope_applies_scaling(
        self,
        recalibration_gate_enabled_both: RecalibrationGateV1,
        recalibration_parameters: RecalibrationParametersV1,
    ) -> None:
        """Enabled gate with both scope applies recalibration to outcome."""
        result_probs, was_applied = apply_runtime_recalibration_to_outcome(
            0.4, 0.3, 0.3, "lt_800", recalibration_gate_enabled_both, recalibration_parameters
        )

        assert was_applied is True
        # Temperature=1.0 means no change
        assert abs(result_probs[0] - 0.4) < 0.001

    def test_gate_enabled_policy_only_returns_unchanged(
        self,
        recalibration_gate_enabled_policy_only: RecalibrationGateV1,
        recalibration_parameters: RecalibrationParametersV1,
    ) -> None:
        """Enabled gate with policy-only scope does not affect outcome."""
        result_probs, was_applied = apply_runtime_recalibration_to_outcome(
            0.4,
            0.3,
            0.3,
            "lt_800",
            recalibration_gate_enabled_policy_only,
            recalibration_parameters,
        )

        assert was_applied is False
        assert result_probs == (0.4, 0.3, 0.3)

