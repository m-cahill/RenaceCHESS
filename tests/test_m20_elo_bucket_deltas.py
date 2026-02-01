"""Tests for M20 Elo-bucket delta facts (EloBucketDeltaFactsV1).

Tests cover:
- Determinism (same inputs → same hash)
- Delta symmetry (A→B ≈ −(B→A) where applicable)
- Zero delta when buckets equal
- Stable ordering
- Float rounding enforcement
- Schema validation
- Pydantic model validation
"""

from datetime import UTC, datetime

import jsonschema
import pytest

from renacechess.coaching.elo_bucket_deltas import (
    FLOAT_PRECISION,
    _compute_kl_divergence,
    _compute_mass_shift_to_top,
    _compute_rank_flips,
    _compute_total_variation,
    _round_float,
    build_elo_bucket_delta_facts_v1,
)
from renacechess.contracts.models import (
    DifficultyDeltaV1,
    EloBucketDeltaFactsV1,
    EloBucketDeltaSourceContractsV1,
    OutcomeDeltaV1,
    OutcomeSummaryV1,
    PolicyDeltaV1,
    PolicySummaryMoveV1,
    PolicySummaryV1,
    StructuralEmphasisDeltaV1,
)

# Test fixtures
FIXED_TIMESTAMP = datetime(2026, 2, 1, 12, 0, 0, tzinfo=UTC)


def _make_policy_summary(moves: list[tuple[str, float]]) -> PolicySummaryV1:
    """Create a PolicySummaryV1 from (uci, prob) tuples."""
    return PolicySummaryV1(
        top_moves=[PolicySummaryMoveV1(uci=uci, prob=prob) for uci, prob in moves],
        top_k=len(moves),
    )


def _make_outcome_summary(p_win: float, p_draw: float, p_loss: float) -> OutcomeSummaryV1:
    """Create an OutcomeSummaryV1."""
    return OutcomeSummaryV1(p_win=p_win, p_draw=p_draw, p_loss=p_loss)


# =============================================================================
# Pydantic Model Tests
# =============================================================================


class TestPolicySummaryV1:
    """Tests for PolicySummaryV1 model."""

    def test_valid_policy_summary(self) -> None:
        """Test valid PolicySummaryV1 creation."""
        policy = _make_policy_summary([("e2e4", 0.4), ("d2d4", 0.3), ("c2c4", 0.2)])
        assert len(policy.top_moves) == 3
        assert policy.top_k == 3
        assert policy.top_moves[0].uci == "e2e4"
        assert policy.top_moves[0].prob == 0.4

    def test_minimum_one_move(self) -> None:
        """Test that at least one move is required."""
        policy = _make_policy_summary([("e2e4", 1.0)])
        assert len(policy.top_moves) == 1


class TestOutcomeSummaryV1:
    """Tests for OutcomeSummaryV1 model."""

    def test_valid_outcome_summary(self) -> None:
        """Test valid OutcomeSummaryV1 creation."""
        outcome = _make_outcome_summary(0.4, 0.3, 0.3)
        assert outcome.p_win == 0.4
        assert outcome.p_draw == 0.3
        assert outcome.p_loss == 0.3

    def test_outcome_probabilities_must_sum_to_one(self) -> None:
        """Test that outcome probabilities must sum to 1.0."""
        with pytest.raises(ValueError, match="must sum to 1.0"):
            _make_outcome_summary(0.5, 0.3, 0.3)  # Sum = 1.1


class TestPolicyDeltaV1:
    """Tests for PolicyDeltaV1 model."""

    def test_valid_policy_delta(self) -> None:
        """Test valid PolicyDeltaV1 creation."""
        delta = PolicyDeltaV1(
            kl_divergence=0.5,
            total_variation=0.3,
            rank_flips=2,
            mass_shift_to_top=0.1,
        )
        assert delta.kl_divergence == 0.5
        assert delta.total_variation == 0.3
        assert delta.rank_flips == 2
        assert delta.mass_shift_to_top == 0.1

    def test_kl_divergence_must_be_non_negative(self) -> None:
        """Test that KL divergence must be non-negative."""
        with pytest.raises(ValueError):
            PolicyDeltaV1(
                kl_divergence=-0.1,  # Invalid
                total_variation=0.3,
                rank_flips=2,
                mass_shift_to_top=0.1,
            )

    def test_total_variation_bounds(self) -> None:
        """Test that total variation is bounded [0, 1]."""
        with pytest.raises(ValueError):
            PolicyDeltaV1(
                kl_divergence=0.5,
                total_variation=1.5,  # Invalid
                rank_flips=2,
                mass_shift_to_top=0.1,
            )


class TestOutcomeDeltaV1:
    """Tests for OutcomeDeltaV1 model."""

    def test_valid_outcome_delta(self) -> None:
        """Test valid OutcomeDeltaV1 creation."""
        delta = OutcomeDeltaV1(
            delta_p_win=0.1,
            delta_p_draw=-0.05,
            delta_p_loss=-0.05,
            win_rate_monotonic=True,
        )
        assert delta.delta_p_win == 0.1
        assert delta.win_rate_monotonic is True


class TestDifficultyDeltaV1:
    """Tests for DifficultyDeltaV1 model."""

    def test_valid_difficulty_delta(self) -> None:
        """Test valid DifficultyDeltaV1 creation."""
        delta = DifficultyDeltaV1(delta_hdi=-0.1)
        assert delta.delta_hdi == -0.1


class TestStructuralEmphasisDeltaV1:
    """Tests for StructuralEmphasisDeltaV1 model."""

    def test_all_fields_optional(self) -> None:
        """Test that all structural delta fields are optional."""
        delta = StructuralEmphasisDeltaV1()
        assert delta.mobility_emphasis_delta is None
        assert delta.weak_square_sensitivity_delta is None
        assert delta.king_safety_weight_delta is None

    def test_partial_fields(self) -> None:
        """Test partial structural delta fields."""
        delta = StructuralEmphasisDeltaV1(mobility_emphasis_delta=0.1)
        assert delta.mobility_emphasis_delta == 0.1
        assert delta.weak_square_sensitivity_delta is None


class TestEloBucketDeltaSourceContractsV1:
    """Tests for EloBucketDeltaSourceContractsV1 model."""

    def test_valid_source_contracts(self) -> None:
        """Test valid source contracts creation."""
        contracts = EloBucketDeltaSourceContractsV1(
            elo_bucket_delta_contract="v1",
            advice_facts_contract="v1",
        )
        assert contracts.elo_bucket_delta_contract == "v1"
        assert contracts.advice_facts_contract == "v1"


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestRoundFloat:
    """Tests for float rounding."""

    def test_round_float_precision(self) -> None:
        """Test that floats are rounded to correct precision."""
        assert _round_float(0.123456789) == 0.123457
        assert _round_float(0.123456789, 4) == 0.1235

    def test_round_float_default_precision(self) -> None:
        """Test default precision is FLOAT_PRECISION."""
        value = 0.123456789123456789
        assert _round_float(value) == round(value, FLOAT_PRECISION)


class TestKLDivergence:
    """Tests for KL divergence computation."""

    def test_identical_distributions_zero_kl(self) -> None:
        """Test that identical distributions have near-zero KL divergence."""
        moves = [("e2e4", 0.4), ("d2d4", 0.3), ("c2c4", 0.3)]
        kl = _compute_kl_divergence(moves, moves)
        assert kl < 1e-9

    def test_different_distributions_positive_kl(self) -> None:
        """Test that different distributions have positive KL divergence."""
        baseline = [("e2e4", 0.8), ("d2d4", 0.2)]
        comparison = [("e2e4", 0.5), ("d2d4", 0.5)]
        kl = _compute_kl_divergence(baseline, comparison)
        assert kl > 0

    def test_kl_asymmetry(self) -> None:
        """Test that KL divergence is asymmetric."""
        baseline = [("e2e4", 0.9), ("d2d4", 0.1)]
        comparison = [("e2e4", 0.5), ("d2d4", 0.5)]
        kl_ab = _compute_kl_divergence(baseline, comparison)
        kl_ba = _compute_kl_divergence(comparison, baseline)
        # KL divergence is generally asymmetric
        assert kl_ab != kl_ba or (kl_ab == 0 and kl_ba == 0)


class TestTotalVariation:
    """Tests for Total Variation distance computation."""

    def test_identical_distributions_zero_tv(self) -> None:
        """Test that identical distributions have zero TV distance."""
        moves = [("e2e4", 0.4), ("d2d4", 0.3), ("c2c4", 0.3)]
        tv = _compute_total_variation(moves, moves)
        assert tv == 0.0

    def test_completely_different_distributions_max_tv(self) -> None:
        """Test that completely different distributions have TV = 1.0."""
        baseline = [("e2e4", 1.0)]
        comparison = [("d2d4", 1.0)]
        tv = _compute_total_variation(baseline, comparison)
        assert tv == 1.0

    def test_tv_bounded(self) -> None:
        """Test that TV is always in [0, 1]."""
        baseline = [("e2e4", 0.7), ("d2d4", 0.3)]
        comparison = [("e2e4", 0.3), ("d2d4", 0.7)]
        tv = _compute_total_variation(baseline, comparison)
        assert 0.0 <= tv <= 1.0


class TestRankFlips:
    """Tests for rank flip computation."""

    def test_identical_order_zero_flips(self) -> None:
        """Test that identical ordering has zero flips."""
        moves = [("e2e4", 0.5), ("d2d4", 0.3), ("c2c4", 0.2)]
        flips = _compute_rank_flips(moves, moves)
        assert flips == 0

    def test_reversed_order_max_flips(self) -> None:
        """Test that reversed ordering has maximum flips."""
        baseline = [("e2e4", 0.5), ("d2d4", 0.3), ("c2c4", 0.2)]
        comparison = [("c2c4", 0.5), ("d2d4", 0.3), ("e2e4", 0.2)]
        flips = _compute_rank_flips(baseline, comparison)
        # 3 moves, 3 pairwise comparisons, should have flips
        assert flips > 0

    def test_no_shared_moves_zero_flips(self) -> None:
        """Test that distributions with no shared moves have zero flips."""
        baseline = [("e2e4", 0.5), ("d2d4", 0.5)]
        comparison = [("c2c4", 0.5), ("g1f3", 0.5)]
        flips = _compute_rank_flips(baseline, comparison)
        assert flips == 0


class TestMassShiftToTop:
    """Tests for mass shift to top computation."""

    def test_identical_distributions_zero_shift(self) -> None:
        """Test that identical distributions have zero mass shift."""
        moves = [("e2e4", 0.5), ("d2d4", 0.5)]
        shift = _compute_mass_shift_to_top(moves, moves)
        assert shift == 0.0

    def test_more_concentrated_positive_shift(self) -> None:
        """Test that more concentrated comparison has positive shift."""
        baseline = [("e2e4", 0.5), ("d2d4", 0.5)]
        comparison = [("e2e4", 0.8), ("d2d4", 0.2)]
        shift = _compute_mass_shift_to_top(baseline, comparison)
        assert shift > 0

    def test_less_concentrated_negative_shift(self) -> None:
        """Test that less concentrated comparison has negative shift."""
        baseline = [("e2e4", 0.8), ("d2d4", 0.2)]
        comparison = [("e2e4", 0.5), ("d2d4", 0.5)]
        shift = _compute_mass_shift_to_top(baseline, comparison)
        assert shift < 0


# =============================================================================
# Builder Function Tests
# =============================================================================


class TestBuildEloBucketDeltaFactsV1:
    """Tests for build_elo_bucket_delta_facts_v1 function."""

    def test_basic_artifact_creation(self) -> None:
        """Test basic artifact creation."""
        baseline_policy = _make_policy_summary([("e2e4", 0.5), ("d2d4", 0.3), ("c2c4", 0.2)])
        comparison_policy = _make_policy_summary([("e2e4", 0.6), ("d2d4", 0.25), ("c2c4", 0.15)])

        baseline_outcome = _make_outcome_summary(0.4, 0.3, 0.3)
        comparison_outcome = _make_outcome_summary(0.5, 0.25, 0.25)

        artifact = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            baseline_policy=baseline_policy,
            comparison_policy=comparison_policy,
            baseline_outcome=baseline_outcome,
            comparison_outcome=comparison_outcome,
            baseline_hdi=0.6,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "a" * 64,
            comparison_advice_facts_hash="sha256:" + "b" * 64,
            generated_at=FIXED_TIMESTAMP,
        )

        assert artifact.schema_version == "elo_bucket_delta_facts.v1"
        assert artifact.baseline_bucket == "1200_1399"
        assert artifact.comparison_bucket == "1600_1799"
        assert artifact.determinism_hash.startswith("sha256:")

    def test_determinism_same_inputs_same_hash(self) -> None:
        """Test that same inputs produce identical hash."""
        baseline_policy = _make_policy_summary([("e2e4", 0.5), ("d2d4", 0.5)])
        comparison_policy = _make_policy_summary([("e2e4", 0.6), ("d2d4", 0.4)])
        baseline_outcome = _make_outcome_summary(0.4, 0.3, 0.3)
        comparison_outcome = _make_outcome_summary(0.5, 0.25, 0.25)

        artifact1 = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            baseline_policy=baseline_policy,
            comparison_policy=comparison_policy,
            baseline_outcome=baseline_outcome,
            comparison_outcome=comparison_outcome,
            baseline_hdi=0.6,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "a" * 64,
            comparison_advice_facts_hash="sha256:" + "b" * 64,
            generated_at=FIXED_TIMESTAMP,
        )

        artifact2 = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            baseline_policy=baseline_policy,
            comparison_policy=comparison_policy,
            baseline_outcome=baseline_outcome,
            comparison_outcome=comparison_outcome,
            baseline_hdi=0.6,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "a" * 64,
            comparison_advice_facts_hash="sha256:" + "b" * 64,
            generated_at=FIXED_TIMESTAMP,
        )

        assert artifact1.determinism_hash == artifact2.determinism_hash

    def test_delta_symmetry_policy(self) -> None:
        """Test that policy deltas have expected symmetry properties."""
        policy_a = _make_policy_summary([("e2e4", 0.6), ("d2d4", 0.4)])
        policy_b = _make_policy_summary([("e2e4", 0.4), ("d2d4", 0.6)])
        outcome = _make_outcome_summary(0.4, 0.3, 0.3)

        artifact_ab = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            baseline_policy=policy_a,
            comparison_policy=policy_b,
            baseline_outcome=outcome,
            comparison_outcome=outcome,
            baseline_hdi=0.5,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "a" * 64,
            comparison_advice_facts_hash="sha256:" + "b" * 64,
            generated_at=FIXED_TIMESTAMP,
        )

        artifact_ba = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1600_1799",
            comparison_bucket="1200_1399",
            baseline_policy=policy_b,
            comparison_policy=policy_a,
            baseline_outcome=outcome,
            comparison_outcome=outcome,
            baseline_hdi=0.5,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "b" * 64,
            comparison_advice_facts_hash="sha256:" + "a" * 64,
            generated_at=FIXED_TIMESTAMP,
        )

        # TV distance should be symmetric
        assert (
            abs(artifact_ab.policy_delta.total_variation - artifact_ba.policy_delta.total_variation)
            < 1e-6
        )

        # Mass shift should be negated
        assert (
            abs(
                artifact_ab.policy_delta.mass_shift_to_top
                + artifact_ba.policy_delta.mass_shift_to_top
            )
            < 1e-6
        )

    def test_delta_symmetry_outcome(self) -> None:
        """Test that outcome deltas are negated when swapping baseline/comparison."""
        policy = _make_policy_summary([("e2e4", 0.5), ("d2d4", 0.5)])
        outcome_a = _make_outcome_summary(0.4, 0.3, 0.3)
        outcome_b = _make_outcome_summary(0.5, 0.25, 0.25)

        artifact_ab = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            baseline_policy=policy,
            comparison_policy=policy,
            baseline_outcome=outcome_a,
            comparison_outcome=outcome_b,
            baseline_hdi=0.5,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "a" * 64,
            comparison_advice_facts_hash="sha256:" + "b" * 64,
            generated_at=FIXED_TIMESTAMP,
        )

        artifact_ba = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1600_1799",
            comparison_bucket="1200_1399",
            baseline_policy=policy,
            comparison_policy=policy,
            baseline_outcome=outcome_b,
            comparison_outcome=outcome_a,
            baseline_hdi=0.5,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "b" * 64,
            comparison_advice_facts_hash="sha256:" + "a" * 64,
            generated_at=FIXED_TIMESTAMP,
        )

        # Outcome deltas should be negated
        assert (
            abs(artifact_ab.outcome_delta.delta_p_win + artifact_ba.outcome_delta.delta_p_win)
            < 1e-6
        )
        assert (
            abs(artifact_ab.outcome_delta.delta_p_draw + artifact_ba.outcome_delta.delta_p_draw)
            < 1e-6
        )
        assert (
            abs(artifact_ab.outcome_delta.delta_p_loss + artifact_ba.outcome_delta.delta_p_loss)
            < 1e-6
        )

    def test_zero_delta_when_buckets_equal(self) -> None:
        """Test that comparing same bucket to itself produces zero deltas."""
        policy = _make_policy_summary([("e2e4", 0.5), ("d2d4", 0.3), ("c2c4", 0.2)])
        outcome = _make_outcome_summary(0.4, 0.3, 0.3)

        artifact = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1200_1399",
            baseline_policy=policy,
            comparison_policy=policy,
            baseline_outcome=outcome,
            comparison_outcome=outcome,
            baseline_hdi=0.5,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "a" * 64,
            comparison_advice_facts_hash="sha256:" + "a" * 64,
            generated_at=FIXED_TIMESTAMP,
        )

        # Policy deltas should be zero
        assert artifact.policy_delta.kl_divergence < 1e-9
        assert artifact.policy_delta.total_variation == 0.0
        assert artifact.policy_delta.rank_flips == 0
        assert artifact.policy_delta.mass_shift_to_top == 0.0

        # Outcome deltas should be zero
        assert artifact.outcome_delta.delta_p_win == 0.0
        assert artifact.outcome_delta.delta_p_draw == 0.0
        assert artifact.outcome_delta.delta_p_loss == 0.0

        # Difficulty delta should be zero
        assert artifact.difficulty_delta.delta_hdi == 0.0

    def test_structural_delta_omitted_when_not_provided(self) -> None:
        """Test that structural delta is None when not provided."""
        policy = _make_policy_summary([("e2e4", 0.5), ("d2d4", 0.5)])
        outcome = _make_outcome_summary(0.4, 0.3, 0.3)

        artifact = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            baseline_policy=policy,
            comparison_policy=policy,
            baseline_outcome=outcome,
            comparison_outcome=outcome,
            baseline_hdi=0.5,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "a" * 64,
            comparison_advice_facts_hash="sha256:" + "b" * 64,
            generated_at=FIXED_TIMESTAMP,
        )

        assert artifact.structural_delta is None

    def test_structural_delta_included_when_provided(self) -> None:
        """Test that structural delta is computed when both are provided."""
        policy = _make_policy_summary([("e2e4", 0.5), ("d2d4", 0.5)])
        outcome = _make_outcome_summary(0.4, 0.3, 0.3)

        baseline_structural = StructuralEmphasisDeltaV1(
            mobility_emphasis_delta=0.3,
            weak_square_sensitivity_delta=0.2,
        )
        comparison_structural = StructuralEmphasisDeltaV1(
            mobility_emphasis_delta=0.5,
            weak_square_sensitivity_delta=0.1,
        )

        artifact = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            baseline_policy=policy,
            comparison_policy=policy,
            baseline_outcome=outcome,
            comparison_outcome=outcome,
            baseline_hdi=0.5,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "a" * 64,
            comparison_advice_facts_hash="sha256:" + "b" * 64,
            baseline_structural=baseline_structural,
            comparison_structural=comparison_structural,
            generated_at=FIXED_TIMESTAMP,
        )

        assert artifact.structural_delta is not None
        assert artifact.structural_delta.mobility_emphasis_delta == 0.2  # 0.5 - 0.3
        assert artifact.structural_delta.weak_square_sensitivity_delta == -0.1  # 0.1 - 0.2

    def test_source_advice_facts_hashes_required(self) -> None:
        """Test that source hashes are included in artifact."""
        policy = _make_policy_summary([("e2e4", 0.5), ("d2d4", 0.5)])
        outcome = _make_outcome_summary(0.4, 0.3, 0.3)

        baseline_hash = "sha256:" + "a" * 64
        comparison_hash = "sha256:" + "b" * 64

        artifact = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            baseline_policy=policy,
            comparison_policy=policy,
            baseline_outcome=outcome,
            comparison_outcome=outcome,
            baseline_hdi=0.5,
            comparison_hdi=0.5,
            baseline_advice_facts_hash=baseline_hash,
            comparison_advice_facts_hash=comparison_hash,
            generated_at=FIXED_TIMESTAMP,
        )

        assert artifact.source_advice_facts_hashes == [baseline_hash, comparison_hash]

    def test_float_rounding_applied(self) -> None:
        """Test that float values are rounded to FLOAT_PRECISION."""
        # Use values that would differ without rounding
        policy = _make_policy_summary([("e2e4", 0.123456789), ("d2d4", 0.876543211)])
        outcome = _make_outcome_summary(0.4, 0.3, 0.3)

        artifact = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            baseline_policy=policy,
            comparison_policy=policy,
            baseline_outcome=outcome,
            comparison_outcome=outcome,
            baseline_hdi=0.123456789,
            comparison_hdi=0.987654321,
            baseline_advice_facts_hash="sha256:" + "a" * 64,
            comparison_advice_facts_hash="sha256:" + "b" * 64,
            generated_at=FIXED_TIMESTAMP,
        )

        # HDI delta should be rounded
        expected_delta = round(0.987654321 - 0.123456789, FLOAT_PRECISION)
        assert artifact.difficulty_delta.delta_hdi == expected_delta

    def test_win_rate_monotonic_true_when_win_increases(self) -> None:
        """Test win_rate_monotonic is True when higher bucket has higher win rate."""
        policy = _make_policy_summary([("e2e4", 0.5), ("d2d4", 0.5)])
        baseline_outcome = _make_outcome_summary(0.3, 0.4, 0.3)  # Lower win
        comparison_outcome = _make_outcome_summary(0.5, 0.3, 0.2)  # Higher win

        artifact = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            baseline_policy=policy,
            comparison_policy=policy,
            baseline_outcome=baseline_outcome,
            comparison_outcome=comparison_outcome,
            baseline_hdi=0.5,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "a" * 64,
            comparison_advice_facts_hash="sha256:" + "b" * 64,
            generated_at=FIXED_TIMESTAMP,
        )

        assert artifact.outcome_delta.win_rate_monotonic is True

    def test_win_rate_monotonic_false_when_win_decreases(self) -> None:
        """Test win_rate_monotonic is False when higher bucket has lower win rate."""
        policy = _make_policy_summary([("e2e4", 0.5), ("d2d4", 0.5)])
        baseline_outcome = _make_outcome_summary(0.5, 0.3, 0.2)  # Higher win
        comparison_outcome = _make_outcome_summary(0.3, 0.4, 0.3)  # Lower win

        artifact = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            baseline_policy=policy,
            comparison_policy=policy,
            baseline_outcome=baseline_outcome,
            comparison_outcome=comparison_outcome,
            baseline_hdi=0.5,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "a" * 64,
            comparison_advice_facts_hash="sha256:" + "b" * 64,
            generated_at=FIXED_TIMESTAMP,
        )

        assert artifact.outcome_delta.win_rate_monotonic is False


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestSchemaValidation:
    """Tests for JSON schema validation."""

    @pytest.fixture
    def schema(self) -> dict:
        """Load the JSON schema."""
        import json
        from pathlib import Path

        schema_path = (
            Path(__file__).parent.parent
            / "src"
            / "renacechess"
            / "contracts"
            / "schemas"
            / "v1"
            / "elo_bucket_deltas.v1.schema.json"
        )
        with open(schema_path) as f:
            return json.load(f)

    def test_artifact_validates_against_schema(self, schema: dict) -> None:
        """Test that generated artifact validates against JSON schema."""
        policy = _make_policy_summary([("e2e4", 0.5), ("d2d4", 0.3), ("c2c4", 0.2)])
        outcome = _make_outcome_summary(0.4, 0.3, 0.3)

        artifact = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            baseline_policy=policy,
            comparison_policy=policy,
            baseline_outcome=outcome,
            comparison_outcome=outcome,
            baseline_hdi=0.5,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "a" * 64,
            comparison_advice_facts_hash="sha256:" + "b" * 64,
            generated_at=FIXED_TIMESTAMP,
        )

        # Convert to dict using aliases
        artifact_dict = artifact.model_dump(mode="json", by_alias=True)

        # Should not raise
        jsonschema.validate(artifact_dict, schema)

    def test_artifact_with_structural_delta_validates(self, schema: dict) -> None:
        """Test that artifact with structural delta validates against schema."""
        policy = _make_policy_summary([("e2e4", 0.5), ("d2d4", 0.5)])
        outcome = _make_outcome_summary(0.4, 0.3, 0.3)

        artifact = build_elo_bucket_delta_facts_v1(
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            baseline_policy=policy,
            comparison_policy=policy,
            baseline_outcome=outcome,
            comparison_outcome=outcome,
            baseline_hdi=0.5,
            comparison_hdi=0.5,
            baseline_advice_facts_hash="sha256:" + "a" * 64,
            comparison_advice_facts_hash="sha256:" + "b" * 64,
            baseline_structural=StructuralEmphasisDeltaV1(mobility_emphasis_delta=0.3),
            comparison_structural=StructuralEmphasisDeltaV1(mobility_emphasis_delta=0.5),
            generated_at=FIXED_TIMESTAMP,
        )

        artifact_dict = artifact.model_dump(mode="json", by_alias=True)
        jsonschema.validate(artifact_dict, schema)


# =============================================================================
# Integration Tests
# =============================================================================


class TestEloBucketDeltaFactsV1Model:
    """Tests for EloBucketDeltaFactsV1 Pydantic model directly."""

    def test_valid_artifact_creation(self) -> None:
        """Test valid artifact creation via Pydantic model."""
        artifact = EloBucketDeltaFactsV1(
            schema_version="elo_bucket_delta_facts.v1",
            generated_at=FIXED_TIMESTAMP,
            baseline_bucket="1200_1399",
            comparison_bucket="1600_1799",
            source_advice_facts_hashes=["sha256:" + "a" * 64, "sha256:" + "b" * 64],
            policy_delta=PolicyDeltaV1(
                kl_divergence=0.5,
                total_variation=0.3,
                rank_flips=2,
                mass_shift_to_top=0.1,
            ),
            outcome_delta=OutcomeDeltaV1(
                delta_p_win=0.1,
                delta_p_draw=-0.05,
                delta_p_loss=-0.05,
                win_rate_monotonic=True,
            ),
            difficulty_delta=DifficultyDeltaV1(delta_hdi=-0.1),
            determinism_hash="sha256:" + "c" * 64,
            source_contract_versions=EloBucketDeltaSourceContractsV1(
                elo_bucket_delta_contract="v1",
                advice_facts_contract="v1",
            ),
        )

        assert artifact.baseline_bucket == "1200_1399"
        assert artifact.comparison_bucket == "1600_1799"
        assert len(artifact.source_advice_facts_hashes) == 2

    def test_determinism_hash_pattern(self) -> None:
        """Test that determinism hash must match pattern."""
        with pytest.raises(ValueError):
            EloBucketDeltaFactsV1(
                schema_version="elo_bucket_delta_facts.v1",
                generated_at=FIXED_TIMESTAMP,
                baseline_bucket="1200_1399",
                comparison_bucket="1600_1799",
                source_advice_facts_hashes=["sha256:" + "a" * 64, "sha256:" + "b" * 64],
                policy_delta=PolicyDeltaV1(
                    kl_divergence=0.5,
                    total_variation=0.3,
                    rank_flips=2,
                    mass_shift_to_top=0.1,
                ),
                outcome_delta=OutcomeDeltaV1(
                    delta_p_win=0.1,
                    delta_p_draw=-0.05,
                    delta_p_loss=-0.05,
                    win_rate_monotonic=True,
                ),
                difficulty_delta=DifficultyDeltaV1(delta_hdi=-0.1),
                determinism_hash="invalid-hash",  # Invalid pattern
                source_contract_versions=EloBucketDeltaSourceContractsV1(
                    elo_bucket_delta_contract="v1",
                    advice_facts_contract="v1",
                ),
            )

    def test_source_hashes_must_have_exactly_two(self) -> None:
        """Test that source_advice_facts_hashes must have exactly 2 entries."""
        with pytest.raises(ValueError):
            EloBucketDeltaFactsV1(
                schema_version="elo_bucket_delta_facts.v1",
                generated_at=FIXED_TIMESTAMP,
                baseline_bucket="1200_1399",
                comparison_bucket="1600_1799",
                source_advice_facts_hashes=["sha256:" + "a" * 64],  # Only 1
                policy_delta=PolicyDeltaV1(
                    kl_divergence=0.5,
                    total_variation=0.3,
                    rank_flips=2,
                    mass_shift_to_top=0.1,
                ),
                outcome_delta=OutcomeDeltaV1(
                    delta_p_win=0.1,
                    delta_p_draw=-0.05,
                    delta_p_loss=-0.05,
                    win_rate_monotonic=True,
                ),
                difficulty_delta=DifficultyDeltaV1(delta_hdi=-0.1),
                determinism_hash="sha256:" + "c" * 64,
                source_contract_versions=EloBucketDeltaSourceContractsV1(
                    elo_bucket_delta_contract="v1",
                    advice_facts_contract="v1",
                ),
            )
