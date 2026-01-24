"""Tests for M07 Human Difficulty Index (HDI) computation."""

import pytest

from renacechess.eval.hdi import (
    clamp01,
    compute_hdi_v1,
    compute_outcome_sensitivity_proxy,
    normalize_entropy,
    normalize_legal_move_pressure,
    normalize_top_gap_inverted,
)


class TestHDINormalization:
    """Test HDI normalization functions."""

    def test_clamp01_basic(self) -> None:
        """Test clamp01 function."""
        assert clamp01(0.0) == 0.0
        assert clamp01(0.5) == 0.5
        assert clamp01(1.0) == 1.0
        assert clamp01(-1.0) == 0.0
        assert clamp01(2.0) == 1.0

    def test_normalize_entropy(self) -> None:
        """Test entropy normalization."""
        # Zero entropy
        assert normalize_entropy(0.0) == 0.0
        # Normal entropy (5 bits)
        assert 0.0 < normalize_entropy(5.0) < 1.0
        # High entropy (10 bits = max)
        assert normalize_entropy(10.0) == 1.0
        # Very high entropy (clamped)
        assert normalize_entropy(20.0) == 1.0
        # Negative (clamped)
        assert normalize_entropy(-1.0) == 0.0

    def test_normalize_top_gap_inverted(self) -> None:
        """Test top gap inversion and normalization."""
        # Zero gap (maximum ambiguity)
        assert normalize_top_gap_inverted(0.0) == 1.0
        # Large gap (low ambiguity)
        assert normalize_top_gap_inverted(1.0) == 0.0
        # Medium gap
        assert 0.0 < normalize_top_gap_inverted(0.5) < 1.0
        # Negative (clamped)
        assert normalize_top_gap_inverted(-0.1) == 1.0
        # > 1.0 (clamped)
        assert normalize_top_gap_inverted(2.0) == 0.0

    def test_normalize_legal_move_pressure(self) -> None:
        """Test legal move pressure normalization."""
        # Zero moves
        assert normalize_legal_move_pressure(0) == 0.0
        # 20 moves (half of max)
        assert normalize_legal_move_pressure(20) == 0.5
        # 40 moves (max human-relevant)
        assert normalize_legal_move_pressure(40) == 1.0
        # > 40 moves (clamped)
        assert normalize_legal_move_pressure(100) == 1.0
        # Negative (clamped)
        assert normalize_legal_move_pressure(-1) == 0.0


class TestOutcomeSensitivityProxy:
    """Test outcome sensitivity proxy computation."""

    def test_compute_outcome_sensitivity_proxy_basic(self) -> None:
        """Test basic outcome sensitivity proxy."""
        value, source = compute_outcome_sensitivity_proxy(entropy=5.0, top_gap=0.2)
        assert 0.0 <= value <= 1.0
        assert source == "proxy"

    def test_compute_outcome_sensitivity_proxy_zero_entropy(self) -> None:
        """Test proxy with zero entropy."""
        value, source = compute_outcome_sensitivity_proxy(entropy=0.0, top_gap=0.5)
        assert value == 0.0
        assert source == "proxy"

    def test_compute_outcome_sensitivity_proxy_zero_gap(self) -> None:
        """Test proxy with zero gap (maximum ambiguity)."""
        value, source = compute_outcome_sensitivity_proxy(entropy=5.0, top_gap=0.0)
        assert value > 0.0
        assert source == "proxy"

    def test_compute_outcome_sensitivity_proxy_high_entropy_high_gap(self) -> None:
        """Test proxy with high entropy and high gap."""
        value, source = compute_outcome_sensitivity_proxy(entropy=10.0, top_gap=1.0)
        # High entropy but low ambiguity -> lower sensitivity
        assert 0.0 <= value <= 1.0
        assert source == "proxy"


class TestHDIComputation:
    """Test HDI v1 computation."""

    def test_compute_hdi_v1_basic(self) -> None:
        """Test basic HDI computation."""
        hdi = compute_hdi_v1(
            entropy=5.0,
            top_gap=0.2,
            legal_moves_count=20,
        )
        assert "value" in hdi
        assert "specVersion" in hdi
        assert "components" in hdi
        assert hdi["specVersion"] == 1
        assert 0.0 <= hdi["value"] <= 1.0

    def test_compute_hdi_v1_components(self) -> None:
        """Test HDI component values."""
        hdi = compute_hdi_v1(
            entropy=5.0,
            top_gap=0.2,
            legal_moves_count=20,
        )
        components = hdi["components"]
        assert "entropy" in components
        assert "topGapInverted" in components
        assert "legalMovePressure" in components
        assert "outcomeSensitivity" in components

        # Check component ranges
        assert 0.0 <= components["entropy"] <= 1.0
        assert 0.0 <= components["topGapInverted"] <= 1.0
        assert 0.0 <= components["legalMovePressure"] <= 1.0
        assert "value" in components["outcomeSensitivity"]
        assert "source" in components["outcomeSensitivity"]
        assert "note" in components["outcomeSensitivity"]
        assert components["outcomeSensitivity"]["source"] == "proxy"

    def test_compute_hdi_v1_with_outcome_head(self) -> None:
        """Test HDI computation with outcome head (not proxy)."""
        hdi = compute_hdi_v1(
            entropy=5.0,
            top_gap=0.2,
            legal_moves_count=20,
            outcome_sensitivity=0.7,
            outcome_sensitivity_source="outcome_head",
        )
        components = hdi["components"]
        assert components["outcomeSensitivity"]["source"] == "outcome_head"
        assert components["outcomeSensitivity"]["value"] == 0.7

    def test_compute_hdi_v1_deterministic(self) -> None:
        """Test HDI computation is deterministic."""
        hdi1 = compute_hdi_v1(entropy=5.0, top_gap=0.2, legal_moves_count=20)
        hdi2 = compute_hdi_v1(entropy=5.0, top_gap=0.2, legal_moves_count=20)
        assert hdi1["value"] == hdi2["value"]
        assert hdi1["components"] == hdi2["components"]

    def test_compute_hdi_v1_zero_entropy(self) -> None:
        """Test HDI with zero entropy (clear position)."""
        hdi = compute_hdi_v1(entropy=0.0, top_gap=1.0, legal_moves_count=5)
        # Low difficulty: zero entropy, high gap, few moves
        assert hdi["value"] < 0.5

    def test_compute_hdi_v1_high_entropy(self) -> None:
        """Test HDI with high entropy (ambiguous position)."""
        hdi = compute_hdi_v1(entropy=10.0, top_gap=0.0, legal_moves_count=40)
        # High difficulty: high entropy, zero gap, many moves
        assert hdi["value"] > 0.5

    def test_compute_hdi_v1_property_entropy_increases(self) -> None:
        """Test property: HDI increases with entropy (all else equal)."""
        hdi_low = compute_hdi_v1(entropy=2.0, top_gap=0.3, legal_moves_count=15)
        hdi_high = compute_hdi_v1(entropy=8.0, top_gap=0.3, legal_moves_count=15)
        assert hdi_high["value"] > hdi_low["value"]

    def test_compute_hdi_v1_property_gap_decreases(self) -> None:
        """Test property: HDI increases as top gap decreases (all else equal)."""
        hdi_low_gap = compute_hdi_v1(entropy=5.0, top_gap=0.1, legal_moves_count=15)
        hdi_high_gap = compute_hdi_v1(entropy=5.0, top_gap=0.9, legal_moves_count=15)
        assert hdi_low_gap["value"] > hdi_high_gap["value"]

    def test_compute_hdi_v1_property_legal_moves_increases(self) -> None:
        """Test property: HDI increases with legal move count (all else equal)."""
        hdi_few = compute_hdi_v1(entropy=5.0, top_gap=0.3, legal_moves_count=5)
        hdi_many = compute_hdi_v1(entropy=5.0, top_gap=0.3, legal_moves_count=35)
        assert hdi_many["value"] > hdi_few["value"]

    def test_compute_hdi_v1_edge_cases(self) -> None:
        """Test edge cases."""
        # All zeros
        hdi = compute_hdi_v1(entropy=0.0, top_gap=0.0, legal_moves_count=0)
        assert 0.0 <= hdi["value"] <= 1.0

        # All max
        hdi = compute_hdi_v1(entropy=20.0, top_gap=0.0, legal_moves_count=100)
        assert 0.0 <= hdi["value"] <= 1.0

        # Negative values (clamped)
        hdi = compute_hdi_v1(entropy=-1.0, top_gap=-0.1, legal_moves_count=-5)
        assert 0.0 <= hdi["value"] <= 1.0

    def test_compute_hdi_v1_weights_sum(self) -> None:
        """Test that HDI formula uses correct weights."""
        # Create a case where we can verify weights
        # Use normalized values directly
        hdi = compute_hdi_v1(entropy=10.0, top_gap=0.0, legal_moves_count=40)
        # At max values, all components should be 1.0
        # HDI = 0.40*1.0 + 0.25*1.0 + 0.20*1.0 + 0.15*1.0 = 1.0
        assert abs(hdi["value"] - 1.0) < 1e-6


class TestHDIIntegration:
    """Test HDI integration with ConditionedMetricsAccumulator."""

    def test_conditioned_metrics_accumulator_includes_hdi(self) -> None:
        """Test that ConditionedMetricsAccumulator includes HDI in build_metrics."""
        from renacechess.eval.conditioned_metrics import ConditionedMetricsAccumulator

        accumulator = ConditionedMetricsAccumulator(compute_accuracy=False)
        # Add records with policy data
        accumulator.add_record(
            policy_output="e2e4",
            legal_moves=["e2e4", "e2e3", "d2d4"],
            policy_entropy=5.0,
            policy_top_gap=0.2,
        )
        accumulator.add_record(
            policy_output="e2e3",
            legal_moves=["e2e4", "e2e3", "d2d4"],
            policy_entropy=6.0,
            policy_top_gap=0.3,
        )

        metrics = accumulator.build_metrics()
        assert metrics.hdi is not None
        assert 0.0 <= metrics.hdi.value <= 1.0
        assert metrics.hdi.spec_version == 1
        assert metrics.hdi.components is not None

    def test_conditioned_metrics_accumulator_hdi_without_policy(self) -> None:
        """Test that HDI is None when no policy data available."""
        from renacechess.eval.conditioned_metrics import ConditionedMetricsAccumulator

        accumulator = ConditionedMetricsAccumulator(compute_accuracy=False)
        # Add record without policy data
        accumulator.add_record(
            policy_output=None,
            legal_moves=["e2e4", "e2e3"],
        )

        metrics = accumulator.build_metrics()
        assert metrics.hdi is None

    def test_conditioned_metrics_accumulator_hdi_stratified(self) -> None:
        """Test that HDI is computed for stratified metrics."""
        from renacechess.eval.conditioned_metrics import ConditionedMetricsAccumulator

        accumulator = ConditionedMetricsAccumulator(compute_accuracy=False)
        # Add records with different skill buckets
        accumulator.add_record(
            policy_output="e2e4",
            legal_moves=["e2e4", "e2e3"],
            policy_entropy=5.0,
            policy_top_gap=0.2,
            skill_bucket_id="1200_1399",
        )
        accumulator.add_record(
            policy_output="e2e3",
            legal_moves=["e2e4", "e2e3"],
            policy_entropy=6.0,
            policy_top_gap=0.3,
            skill_bucket_id="1400_1599",
        )

        stratified = accumulator.build_stratified_metrics()
        # Check overall
        overall = accumulator.build_metrics()
        assert overall.hdi is not None

        # Check stratified
        assert "1200_1399" in stratified["bySkillBucketId"]
        assert stratified["bySkillBucketId"]["1200_1399"].hdi is not None
        assert "1400_1599" in stratified["bySkillBucketId"]
        assert stratified["bySkillBucketId"]["1400_1599"].hdi is not None

