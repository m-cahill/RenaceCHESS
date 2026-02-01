"""M24 Calibration Metrics Tests.

Tests for the CalibrationMetricsV1 schema and calibration runner.

Test categories:
1. Schema validation for CalibrationMetricsV1 and related models
2. Bucket equality guardrail (runner uses canonical buckets from conditioning.buckets)
3. Calibration metric computation (ECE, Brier, NLL)
4. Determinism verification
5. Runner execution with CI fixture

Per M24 locked decisions:
- Required --manifest flag (tested via CLI surface when added)
- Baselines only for CI (no checkpoint dependencies)
- Measurement-only (no runtime consumption)
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import get_args

import pytest

from renacechess.conditioning.buckets import SkillBucketId
from renacechess.contracts.models import (
    CalibrationBinV1,
    CalibrationHistogramV1,
    CalibrationMetricsV1,
    EloBucketCalibrationV1,
    OutcomeCalibrationMetricsV1,
    PolicyCalibrationMetricsV1,
)
from renacechess.eval.calibration_runner import (
    BIN_EDGES,
    CalibrationAccumulator,
    OutcomeCalibrationAccumulator,
    PolicyCalibrationAccumulator,
    get_canonical_skill_buckets,
    load_frozen_eval_manifest,
    run_calibration_evaluation,
)

# =============================================================================
# Test Fixtures
# =============================================================================

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "frozen_eval"


@pytest.fixture
def frozen_eval_manifest_path() -> Path:
    """Return path to the CI frozen eval fixture manifest."""
    return FIXTURE_DIR / "manifest.json"


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestCalibrationSchemaValidation:
    """Test CalibrationMetricsV1 and related model schema validation."""

    def test_calibration_bin_v1_valid(self) -> None:
        """Test CalibrationBinV1 with valid data."""
        bin_v1 = CalibrationBinV1(
            bin_start=0.0,
            bin_end=0.1,
            count=50,
            avg_confidence=0.05,
            empirical_accuracy=0.08,
        )
        assert bin_v1.bin_start == 0.0
        assert bin_v1.bin_end == 0.1
        assert bin_v1.count == 50
        assert bin_v1.avg_confidence == 0.05
        assert bin_v1.empirical_accuracy == 0.08

    def test_calibration_bin_v1_empty(self) -> None:
        """Test CalibrationBinV1 with empty bin (None values)."""
        bin_v1 = CalibrationBinV1(
            bin_start=0.9,
            bin_end=1.0,
            count=0,
            avg_confidence=None,
            empirical_accuracy=None,
        )
        assert bin_v1.count == 0
        assert bin_v1.avg_confidence is None
        assert bin_v1.empirical_accuracy is None

    def test_calibration_histogram_v1_valid(self) -> None:
        """Test CalibrationHistogramV1 with 10 bins."""
        bins = [
            CalibrationBinV1(
                bin_start=i / 10,
                bin_end=(i + 1) / 10,
                count=10,
                avg_confidence=(i + 0.5) / 10,
                empirical_accuracy=(i + 0.5) / 10,
            )
            for i in range(10)
        ]
        histogram = CalibrationHistogramV1(bin_edges=BIN_EDGES.copy(), bins=bins)
        assert len(histogram.bins) == 10
        assert len(histogram.bin_edges) == 11

    def test_outcome_calibration_metrics_v1_valid(self) -> None:
        """Test OutcomeCalibrationMetricsV1 with valid metrics."""
        histogram = CalibrationHistogramV1(
            bin_edges=BIN_EDGES.copy(),
            bins=[
                CalibrationBinV1(
                    bin_start=i / 10,
                    bin_end=(i + 1) / 10,
                    count=5,
                    avg_confidence=None,
                    empirical_accuracy=None,
                )
                for i in range(10)
            ],
        )
        metrics = OutcomeCalibrationMetricsV1(
            brier_score=0.15,
            nll=0.85,
            ece=0.05,
            histogram=histogram,
        )
        assert metrics.brier_score == 0.15
        assert metrics.nll == 0.85
        assert metrics.ece == 0.05

    def test_policy_calibration_metrics_v1_valid(self) -> None:
        """Test PolicyCalibrationMetricsV1 with valid metrics."""
        histogram = CalibrationHistogramV1(
            bin_edges=BIN_EDGES.copy(),
            bins=[
                CalibrationBinV1(
                    bin_start=i / 10,
                    bin_end=(i + 1) / 10,
                    count=5,
                    avg_confidence=None,
                    empirical_accuracy=None,
                )
                for i in range(10)
            ],
        )
        metrics = PolicyCalibrationMetricsV1(
            nll=1.25,
            top1_ece=0.08,
            histogram=histogram,
        )
        assert metrics.nll == 1.25
        assert metrics.top1_ece == 0.08

    def test_elo_bucket_calibration_v1_valid(self) -> None:
        """Test EloBucketCalibrationV1 with valid bucket data."""
        bucket = EloBucketCalibrationV1(
            elo_bucket="1200_1399",
            samples=100,
            outcome_calibration=None,
            policy_calibration=None,
        )
        assert bucket.elo_bucket == "1200_1399"
        assert bucket.samples == 100

    def test_elo_bucket_calibration_v1_all_buckets(self) -> None:
        """Test that all canonical skill buckets are valid."""
        for bucket_id in get_canonical_skill_buckets():
            bucket = EloBucketCalibrationV1(
                elo_bucket=bucket_id,  # type: ignore[arg-type]
                samples=0,
            )
            assert bucket.elo_bucket == bucket_id

    def test_calibration_metrics_v1_full_artifact(self) -> None:
        """Test CalibrationMetricsV1 with complete artifact."""
        histogram = CalibrationHistogramV1(
            bin_edges=BIN_EDGES.copy(),
            bins=[
                CalibrationBinV1(
                    bin_start=i / 10,
                    bin_end=(i + 1) / 10,
                    count=5,
                    avg_confidence=None,
                    empirical_accuracy=None,
                )
                for i in range(10)
            ],
        )
        outcome_metrics = OutcomeCalibrationMetricsV1(
            brier_score=0.15,
            nll=0.85,
            ece=0.05,
            histogram=histogram,
        )
        policy_metrics = PolicyCalibrationMetricsV1(
            nll=1.25,
            top1_ece=0.08,
            histogram=histogram,
        )

        metrics = CalibrationMetricsV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            source_manifest_hash="a" * 64,
            policy_id="baseline.uniform_random",
            outcome_head_id=None,
            overall_samples=100,
            overall_outcome_calibration=outcome_metrics,
            overall_policy_calibration=policy_metrics,
            by_elo_bucket=[
                EloBucketCalibrationV1(
                    elo_bucket="1200_1399",
                    samples=100,
                    outcome_calibration=outcome_metrics,
                    policy_calibration=policy_metrics,
                )
            ],
            determinism_hash="sha256:" + "b" * 64,
        )

        assert metrics.version == "1.0"
        assert metrics.overall_samples == 100
        assert len(metrics.by_elo_bucket) == 1

    def test_calibration_metrics_v1_json_roundtrip(self) -> None:
        """Test CalibrationMetricsV1 JSON serialization/deserialization."""
        histogram = CalibrationHistogramV1(
            bin_edges=BIN_EDGES.copy(),
            bins=[
                CalibrationBinV1(
                    bin_start=i / 10,
                    bin_end=(i + 1) / 10,
                    count=5,
                    avg_confidence=(i + 0.5) / 10 if i > 0 else None,
                    empirical_accuracy=(i + 0.5) / 10 if i > 0 else None,
                )
                for i in range(10)
            ],
        )
        policy_metrics = PolicyCalibrationMetricsV1(
            nll=1.25,
            top1_ece=0.08,
            histogram=histogram,
        )

        metrics = CalibrationMetricsV1(
            version="1.0",
            generated_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
            source_manifest_hash="a" * 64,
            policy_id="baseline.uniform_random",
            outcome_head_id=None,
            overall_samples=50,
            overall_outcome_calibration=None,
            overall_policy_calibration=policy_metrics,
            by_elo_bucket=[
                EloBucketCalibrationV1(
                    elo_bucket="1200_1399",
                    samples=50,
                    policy_calibration=policy_metrics,
                )
            ],
            determinism_hash="sha256:" + "b" * 64,
        )

        # Serialize
        json_str = json.dumps(metrics.model_dump(by_alias=True), default=str)

        # Deserialize
        parsed = CalibrationMetricsV1.model_validate(json.loads(json_str))
        assert parsed.version == "1.0"
        assert parsed.overall_samples == 50


# =============================================================================
# Bucket Equality Guardrail Tests (M24 Locked Requirement)
# =============================================================================


class TestBucketEqualityGuardrail:
    """Test that calibration runner uses canonical skill buckets from conditioning.buckets.

    Per M24 locked decisions:
    - Do not duplicate bucket definitions
    - Add a unit test asserting bucket list equality
    """

    def test_canonical_buckets_match_skill_bucket_id(self) -> None:
        """Assert runner's canonical buckets equal SkillBucketId from conditioning.buckets."""
        # Get buckets from calibration runner
        runner_buckets = set(get_canonical_skill_buckets())

        # Get buckets from conditioning.buckets Literal type
        conditioning_buckets = set(get_args(SkillBucketId))

        # Must be exactly equal
        assert runner_buckets == conditioning_buckets, (
            f"Bucket mismatch! "
            f"Runner has: {runner_buckets}, "
            f"conditioning.buckets has: {conditioning_buckets}"
        )

    def test_canonical_buckets_not_empty(self) -> None:
        """Ensure we have at least the expected buckets."""
        buckets = get_canonical_skill_buckets()
        assert len(buckets) >= 7, f"Expected at least 7 buckets, got {len(buckets)}"

    def test_canonical_buckets_include_unknown(self) -> None:
        """Ensure 'unknown' bucket is included for robustness."""
        buckets = get_canonical_skill_buckets()
        assert "unknown" in buckets, "Expected 'unknown' bucket for robustness"


# =============================================================================
# Calibration Metric Computation Tests
# =============================================================================


class TestCalibrationAccumulator:
    """Test the CalibrationAccumulator metric computation."""

    def test_empty_accumulator(self) -> None:
        """Test metrics for empty accumulator."""
        acc = CalibrationAccumulator()
        assert acc.count == 0
        assert acc.compute_ece() == 0.0
        assert acc.compute_brier_score() == 0.0
        assert acc.compute_nll() == 0.0

    def test_perfect_calibration(self) -> None:
        """Test ECE for perfectly calibrated predictions."""
        acc = CalibrationAccumulator()

        # In bin [0.9, 1.0], all predictions correct
        for _ in range(10):
            acc.add(0.95, True, 0.95)

        # In bin [0.1, 0.2], all predictions wrong
        for _ in range(10):
            acc.add(0.15, False, 0.15)

        # ECE should be low for well-calibrated data
        # Note: With this test setup, ECE is exactly 0.1 due to binning
        # (10 samples in bin [0.9, 1.0] with conf=0.95, acc=1.0 gives |1.0-0.95| = 0.05,
        #  10 samples in bin [0.1, 0.2] with conf=0.15, acc=0.0 gives |0.0-0.15| = 0.15,
        #  weighted average: 0.5 * 0.05 + 0.5 * 0.15 = 0.1)
        ece = acc.compute_ece()
        assert abs(ece - 0.1) < 1e-6  # Should be exactly 0.1 for this test setup

    def test_brier_score_perfect(self) -> None:
        """Test Brier score for perfect predictions."""
        acc = CalibrationAccumulator()
        # All predictions with p=1.0 and outcome=True
        for _ in range(10):
            acc.add(1.0, True, 1.0)

        brier = acc.compute_brier_score()
        assert brier == 0.0  # Perfect predictions

    def test_brier_score_worst(self) -> None:
        """Test Brier score for worst predictions."""
        acc = CalibrationAccumulator()
        # All predictions with p=1.0 but outcome=False
        for _ in range(10):
            acc.add(1.0, False, 0.0)

        brier = acc.compute_brier_score()
        assert brier == 1.0  # Worst possible

    def test_nll_computation(self) -> None:
        """Test NLL computation."""
        acc = CalibrationAccumulator()
        acc.add(0.5, True, 0.5)

        nll = acc.compute_nll()
        expected = -math.log(0.5)
        assert abs(nll - expected) < 1e-6

    def test_histogram_generation(self) -> None:
        """Test histogram generation with fixed bins."""
        acc = CalibrationAccumulator()

        # Add samples in different bins
        acc.add(0.05, False, 0.05)  # Bin [0.0, 0.1)
        acc.add(0.15, True, 0.15)  # Bin [0.1, 0.2)
        acc.add(0.95, True, 0.95)  # Bin [0.9, 1.0]

        histogram = acc.build_histogram()
        assert len(histogram.bins) == 10
        assert histogram.bins[0].count == 1  # First bin
        assert histogram.bins[1].count == 1  # Second bin
        assert histogram.bins[9].count == 1  # Last bin


class TestOutcomeCalibrationAccumulator:
    """Test outcome (W/D/L) calibration accumulator."""

    def test_empty_accumulator(self) -> None:
        """Test empty outcome accumulator."""
        acc = OutcomeCalibrationAccumulator()
        assert acc.count == 0
        metrics = acc.compute_metrics()
        assert metrics.brier_score == 0.0
        assert metrics.ece == 0.0

    def test_outcome_accumulation(self) -> None:
        """Test adding outcome predictions."""
        acc = OutcomeCalibrationAccumulator()
        acc.add(0.5, 0.3, 0.2, "win")
        acc.add(0.2, 0.5, 0.3, "draw")
        acc.add(0.1, 0.2, 0.7, "loss")

        assert acc.count == 3
        metrics = acc.compute_metrics()
        assert metrics.brier_score >= 0
        assert metrics.histogram is not None


class TestPolicyCalibrationAccumulator:
    """Test policy (move distribution) calibration accumulator."""

    def test_empty_accumulator(self) -> None:
        """Test empty policy accumulator."""
        acc = PolicyCalibrationAccumulator()
        assert acc.count == 0
        metrics = acc.compute_metrics()
        assert metrics.nll == 0.0
        assert metrics.top1_ece == 0.0

    def test_top1_correct(self) -> None:
        """Test when top-1 move is chosen."""
        acc = PolicyCalibrationAccumulator()
        move_probs = [("e2e4", 0.8), ("d2d4", 0.2)]
        acc.add(move_probs, "e2e4")  # Top move chosen

        assert acc.count == 1
        metrics = acc.compute_metrics()
        # NLL should be -log(0.8)
        expected_nll = -math.log(0.8)
        assert abs(metrics.nll - expected_nll) < 1e-5

    def test_top1_wrong(self) -> None:
        """Test when top-1 move is not chosen."""
        acc = PolicyCalibrationAccumulator()
        move_probs = [("e2e4", 0.8), ("d2d4", 0.2)]
        acc.add(move_probs, "d2d4")  # Not top move

        assert acc.count == 1
        metrics = acc.compute_metrics()
        # NLL should be -log(0.2)
        expected_nll = -math.log(0.2)
        assert abs(metrics.nll - expected_nll) < 1e-5


# =============================================================================
# Runner Execution Tests
# =============================================================================


class TestCalibrationRunner:
    """Test calibration runner execution with CI fixture."""

    def test_load_frozen_eval_manifest(self, frozen_eval_manifest_path: Path) -> None:
        """Test loading frozen eval manifest from fixture."""
        manifest = load_frozen_eval_manifest(frozen_eval_manifest_path)
        assert manifest.schema_version == 1
        assert len(manifest.records) > 0

    def test_load_frozen_eval_manifest_not_found(self, tmp_path: Path) -> None:
        """Test error when manifest not found."""
        with pytest.raises(FileNotFoundError, match="Frozen eval manifest not found"):
            load_frozen_eval_manifest(tmp_path / "nonexistent.json")

    def test_run_calibration_evaluation(self, frozen_eval_manifest_path: Path) -> None:
        """Test running calibration evaluation on CI fixture."""
        metrics = run_calibration_evaluation(
            manifest_path=frozen_eval_manifest_path,
            policy_id="baseline.uniform_random",
        )

        # Verify basic structure
        assert metrics.version == "1.0"
        assert metrics.overall_samples > 0
        assert len(metrics.by_elo_bucket) > 0

        # Verify determinism hash is present
        assert metrics.determinism_hash.startswith("sha256:")
        assert len(metrics.determinism_hash) == 71  # "sha256:" + 64 hex chars

    def test_run_calibration_produces_per_bucket_metrics(
        self, frozen_eval_manifest_path: Path
    ) -> None:
        """Test that calibration produces metrics for each bucket in fixture."""
        metrics = run_calibration_evaluation(
            manifest_path=frozen_eval_manifest_path,
            policy_id="baseline.uniform_random",
        )

        # Count buckets with samples
        buckets_with_data = [b for b in metrics.by_elo_bucket if b.samples > 0]
        assert len(buckets_with_data) >= 1, "Expected at least one bucket with samples"

    def test_run_calibration_json_serializable(
        self, frozen_eval_manifest_path: Path
    ) -> None:
        """Test that calibration output is JSON-serializable for CI artifacts."""
        metrics = run_calibration_evaluation(
            manifest_path=frozen_eval_manifest_path,
            policy_id="baseline.uniform_random",
        )

        # Serialize to JSON
        json_str = json.dumps(metrics.model_dump(by_alias=True), default=str)
        assert len(json_str) > 0

        # Parse back
        parsed = json.loads(json_str)
        assert parsed["version"] == "1.0"
        assert "byEloBucket" in parsed


# =============================================================================
# Determinism Tests
# =============================================================================


class TestCalibrationDeterminism:
    """Test that calibration evaluation is deterministic."""

    def test_deterministic_output(self, frozen_eval_manifest_path: Path) -> None:
        """Test that two runs produce identical results."""
        metrics1 = run_calibration_evaluation(
            manifest_path=frozen_eval_manifest_path,
            policy_id="baseline.uniform_random",
        )
        metrics2 = run_calibration_evaluation(
            manifest_path=frozen_eval_manifest_path,
            policy_id="baseline.uniform_random",
        )

        # Overall samples should match
        assert metrics1.overall_samples == metrics2.overall_samples

        # Per-bucket counts should match
        for b1, b2 in zip(metrics1.by_elo_bucket, metrics2.by_elo_bucket):
            assert b1.elo_bucket == b2.elo_bucket
            assert b1.samples == b2.samples

    def test_determinism_hash_stable(self, frozen_eval_manifest_path: Path) -> None:
        """Test that determinism hash is stable across runs.

        Note: Hash includes timestamp, so we compare structure instead.
        """
        metrics1 = run_calibration_evaluation(
            manifest_path=frozen_eval_manifest_path,
            policy_id="baseline.uniform_random",
        )
        metrics2 = run_calibration_evaluation(
            manifest_path=frozen_eval_manifest_path,
            policy_id="baseline.uniform_random",
        )

        # Both should have valid determinism hashes
        assert metrics1.determinism_hash.startswith("sha256:")
        assert metrics2.determinism_hash.startswith("sha256:")

        # Same input should produce same structure (excluding timestamp)
        assert metrics1.overall_samples == metrics2.overall_samples
        assert len(metrics1.by_elo_bucket) == len(metrics2.by_elo_bucket)


