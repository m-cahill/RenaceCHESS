"""M27: Tests for runtime recalibration evaluation.

These tests validate the RuntimeRecalibrationReportV1 and RuntimeRecalibrationDeltaV1
artifacts produced by the runtime recalibration evaluation runner.

Per M27 locked decisions:
- Use existing frozen eval fixture
- Reuse M24 calibration infrastructure
- Add policy delta metrics (entropy delta, top-k stability)
- Time pressure stratification only if present in dataset
- Self-contained (no artifact downloads)
- Deterministic artifacts with canonical hashes
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from renacechess.contracts.models import (
    BucketDeltaV1,
    MetricsDeltaV1,
    RecalibrationGateV1,
    RecalibrationParametersV1,
    RuntimeCalibrationSnapshotV1,
    RuntimeRecalibrationDeltaV1,
    RuntimeRecalibrationReportV1,
)


# =============================================================================
# Fixture Paths
# =============================================================================

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "frozen_eval"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"
GATE_PATH = FIXTURE_DIR / "recalibration_gate.json"
PARAMS_PATH = FIXTURE_DIR / "recalibration_params.json"


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestRuntimeRecalibrationReportV1Schema:
    """Test RuntimeRecalibrationReportV1 Pydantic model."""

    def test_valid_report_construction(self) -> None:
        """Test that a valid report can be constructed."""
        from datetime import UTC, datetime

        snapshot = RuntimeCalibrationSnapshotV1(
            outcome_ece=0.1,
            outcome_nll=0.5,
            outcome_brier=0.2,
            policy_nll=1.2,
            policy_top1_ece=0.15,
            mean_entropy=1.5,
        )

        report = RuntimeRecalibrationReportV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            gate_ref="sha256:" + "a" * 64,
            parameters_ref="sha256:" + "b" * 64,
            dataset_ref="c" * 64,
            total_samples=100,
            baseline_metrics=snapshot,
            recalibrated_metrics=snapshot,
            determinism_hash="sha256:" + "d" * 64,
        )

        assert report.version == "1.0"
        assert report.total_samples == 100
        assert report.baseline_metrics.outcome_ece == 0.1

    def test_report_json_serialization(self) -> None:
        """Test that report can be serialized to JSON."""
        from datetime import UTC, datetime

        snapshot = RuntimeCalibrationSnapshotV1(
            outcome_ece=0.1,
            outcome_nll=0.5,
            outcome_brier=0.2,
            policy_nll=1.2,
            policy_top1_ece=0.15,
            mean_entropy=1.5,
        )

        report = RuntimeRecalibrationReportV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            gate_ref="sha256:" + "a" * 64,
            parameters_ref="sha256:" + "b" * 64,
            dataset_ref="c" * 64,
            total_samples=100,
            baseline_metrics=snapshot,
            recalibrated_metrics=snapshot,
            determinism_hash="sha256:" + "d" * 64,
        )

        json_str = report.model_dump_json(by_alias=True)
        data = json.loads(json_str)

        assert data["version"] == "1.0"
        assert data["totalSamples"] == 100
        assert "baselineMetrics" in data
        assert "recalibratedMetrics" in data

    def test_report_alias_mapping(self) -> None:
        """Test that camelCase aliases work correctly."""
        from datetime import UTC, datetime

        snapshot = RuntimeCalibrationSnapshotV1(
            outcome_ece=0.1,
            outcome_nll=0.5,
            outcome_brier=0.2,
            policy_nll=1.2,
            policy_top1_ece=0.15,
            mean_entropy=1.5,
        )

        report = RuntimeRecalibrationReportV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            gate_ref="sha256:" + "a" * 64,
            parameters_ref="sha256:" + "b" * 64,
            dataset_ref="c" * 64,
            total_samples=100,
            baseline_metrics=snapshot,
            recalibrated_metrics=snapshot,
            determinism_hash="sha256:" + "d" * 64,
        )

        dumped = report.model_dump(by_alias=True)
        assert "generatedAt" in dumped
        assert "gateRef" in dumped
        assert "parametersRef" in dumped
        assert "datasetRef" in dumped
        assert "totalSamples" in dumped
        assert "baselineMetrics" in dumped
        assert "recalibratedMetrics" in dumped
        assert "determinismHash" in dumped


class TestRuntimeRecalibrationDeltaV1Schema:
    """Test RuntimeRecalibrationDeltaV1 Pydantic model."""

    def test_valid_delta_construction(self) -> None:
        """Test that a valid delta can be constructed."""
        from datetime import UTC, datetime

        metrics_delta = MetricsDeltaV1(
            outcome_ece_delta=-0.05,
            outcome_nll_delta=-0.1,
            outcome_brier_delta=-0.02,
            policy_nll_delta=-0.15,
            policy_top1_ece_delta=-0.03,
            entropy_delta=0.1,
            top1_stability=0.95,
            top3_stability=0.98,
            top1_flip_rate=0.05,
        )

        bucket_delta = BucketDeltaV1(
            bucket_id="lt_800",
            samples=10,
            metrics=metrics_delta,
        )

        delta = RuntimeRecalibrationDeltaV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            source_report_hash="sha256:" + "a" * 64,
            by_elo_bucket=[bucket_delta],
            by_time_pressure_bucket=None,
            overall=metrics_delta,
            determinism_hash="sha256:" + "b" * 64,
        )

        assert delta.version == "1.0"
        assert len(delta.by_elo_bucket) == 1
        assert delta.by_time_pressure_bucket is None
        assert delta.overall.top1_stability == 0.95

    def test_delta_with_time_pressure(self) -> None:
        """Test delta with time pressure buckets present."""
        from datetime import UTC, datetime

        metrics_delta = MetricsDeltaV1(
            outcome_ece_delta=-0.05,
            outcome_nll_delta=-0.1,
            outcome_brier_delta=-0.02,
            policy_nll_delta=-0.15,
            policy_top1_ece_delta=-0.03,
            entropy_delta=0.1,
            top1_stability=0.95,
            top3_stability=0.98,
            top1_flip_rate=0.05,
        )

        elo_bucket = BucketDeltaV1(bucket_id="lt_800", samples=10, metrics=metrics_delta)
        time_bucket = BucketDeltaV1(bucket_id="low", samples=5, metrics=metrics_delta)

        delta = RuntimeRecalibrationDeltaV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            source_report_hash="sha256:" + "a" * 64,
            by_elo_bucket=[elo_bucket],
            by_time_pressure_bucket=[time_bucket],
            overall=metrics_delta,
            determinism_hash="sha256:" + "b" * 64,
        )

        assert delta.by_time_pressure_bucket is not None
        assert len(delta.by_time_pressure_bucket) == 1
        assert delta.by_time_pressure_bucket[0].bucket_id == "low"

    def test_metrics_delta_bounds(self) -> None:
        """Test that stability metrics are bounded [0, 1]."""
        # Valid values
        metrics = MetricsDeltaV1(
            outcome_ece_delta=0.0,
            outcome_nll_delta=0.0,
            outcome_brier_delta=0.0,
            policy_nll_delta=0.0,
            policy_top1_ece_delta=0.0,
            entropy_delta=0.0,
            top1_stability=0.0,
            top3_stability=1.0,
            top1_flip_rate=0.5,
        )
        assert metrics.top1_stability == 0.0
        assert metrics.top3_stability == 1.0

        # Invalid: out of bounds
        with pytest.raises(ValueError):
            MetricsDeltaV1(
                outcome_ece_delta=0.0,
                outcome_nll_delta=0.0,
                outcome_brier_delta=0.0,
                policy_nll_delta=0.0,
                policy_top1_ece_delta=0.0,
                entropy_delta=0.0,
                top1_stability=-0.1,  # Invalid
                top3_stability=1.0,
                top1_flip_rate=0.5,
            )

        with pytest.raises(ValueError):
            MetricsDeltaV1(
                outcome_ece_delta=0.0,
                outcome_nll_delta=0.0,
                outcome_brier_delta=0.0,
                policy_nll_delta=0.0,
                policy_top1_ece_delta=0.0,
                entropy_delta=0.0,
                top1_stability=0.5,
                top3_stability=1.5,  # Invalid
                top1_flip_rate=0.5,
            )


# =============================================================================
# Runner Tests
# =============================================================================


class TestRuntimeRecalibrationEvalRunner:
    """Tests for the runtime recalibration evaluation runner."""

    @pytest.fixture
    def output_dir(self) -> Path:
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_fixtures_exist(self) -> None:
        """Verify test fixtures exist."""
        assert MANIFEST_PATH.exists(), f"Manifest not found: {MANIFEST_PATH}"
        assert GATE_PATH.exists(), f"Gate not found: {GATE_PATH}"
        assert PARAMS_PATH.exists(), f"Params not found: {PARAMS_PATH}"

    def test_gate_fixture_valid(self) -> None:
        """Test that gate fixture is valid."""
        gate_data = json.loads(GATE_PATH.read_text(encoding="utf-8"))
        gate = RecalibrationGateV1.model_validate(gate_data)
        assert gate.version == "1.0"
        assert gate.enabled is True
        assert gate.scope == "both"

    def test_params_fixture_valid(self) -> None:
        """Test that params fixture is valid."""
        params_data = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
        params = RecalibrationParametersV1.model_validate(params_data)
        assert params.version == "1.0"
        assert len(params.by_elo_bucket) >= 7  # At least 7 canonical buckets

    def test_run_evaluation_produces_artifacts(self, output_dir: Path) -> None:
        """Test that running evaluation produces both artifacts."""
        from renacechess.eval.runtime_recalibration_eval_runner import (
            run_runtime_recalibration_evaluation,
        )

        report, delta = run_runtime_recalibration_evaluation(
            manifest_path=MANIFEST_PATH,
            gate_path=GATE_PATH,
            params_path=PARAMS_PATH,
            output_dir=output_dir,
        )

        # Check artifacts were created
        report_path = output_dir / "runtime-recalibration-report.json"
        delta_path = output_dir / "runtime-recalibration-delta.json"
        assert report_path.exists()
        assert delta_path.exists()

        # Validate report
        assert report.version == "1.0"
        assert report.total_samples > 0

        # Validate delta
        assert delta.version == "1.0"
        assert len(delta.by_elo_bucket) > 0

    def test_determinism_two_runs_identical(self, output_dir: Path) -> None:
        """Test that two runs produce identical hashes."""
        from renacechess.eval.runtime_recalibration_eval_runner import (
            run_runtime_recalibration_evaluation,
        )

        # First run
        report1, delta1 = run_runtime_recalibration_evaluation(
            manifest_path=MANIFEST_PATH,
            gate_path=GATE_PATH,
            params_path=PARAMS_PATH,
            output_dir=output_dir,
        )

        # Second run (different output dir)
        with tempfile.TemporaryDirectory() as tmpdir2:
            output_dir2 = Path(tmpdir2)
            report2, delta2 = run_runtime_recalibration_evaluation(
                manifest_path=MANIFEST_PATH,
                gate_path=GATE_PATH,
                params_path=PARAMS_PATH,
                output_dir=output_dir2,
            )

            # Hashes should match (excluding generated_at which differs)
            # The determinism hash is computed from content excluding the hash field itself
            assert report1.determinism_hash == report2.determinism_hash
            assert delta1.determinism_hash == delta2.determinism_hash

    def test_stability_metrics_sanity(self, output_dir: Path) -> None:
        """Test that stability metrics are within expected ranges."""
        from renacechess.eval.runtime_recalibration_eval_runner import (
            run_runtime_recalibration_evaluation,
        )

        report, delta = run_runtime_recalibration_evaluation(
            manifest_path=MANIFEST_PATH,
            gate_path=GATE_PATH,
            params_path=PARAMS_PATH,
            output_dir=output_dir,
        )

        # Stability should be in [0, 1]
        assert 0.0 <= delta.overall.top1_stability <= 1.0
        assert 0.0 <= delta.overall.top3_stability <= 1.0
        assert 0.0 <= delta.overall.top1_flip_rate <= 1.0

        # Flip rate should be 1 - stability
        assert abs(delta.overall.top1_flip_rate - (1.0 - delta.overall.top1_stability)) < 1e-9

        # Entropy delta should be finite
        assert delta.overall.entropy_delta != float("inf")
        assert delta.overall.entropy_delta != float("-inf")

    def test_time_pressure_stratification_present(self, output_dir: Path) -> None:
        """Test that time pressure stratification is included when present in fixture."""
        from renacechess.eval.runtime_recalibration_eval_runner import (
            run_runtime_recalibration_evaluation,
        )

        # The frozen eval fixture has time pressure buckets
        manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        has_time_pressure = "countsByTimePressureBucket" in manifest_data

        report, delta = run_runtime_recalibration_evaluation(
            manifest_path=MANIFEST_PATH,
            gate_path=GATE_PATH,
            params_path=PARAMS_PATH,
            output_dir=output_dir,
        )

        if has_time_pressure:
            assert delta.by_time_pressure_bucket is not None
            assert len(delta.by_time_pressure_bucket) > 0
        else:
            # Should be None, not empty list
            assert delta.by_time_pressure_bucket is None


# =============================================================================
# Policy Delta Metrics Tests
# =============================================================================


class TestPolicyDeltaMetrics:
    """Tests for policy-specific delta metrics."""

    def test_entropy_delta_computed(self) -> None:
        """Test that entropy delta is computed correctly."""
        from renacechess.eval.runtime_recalibration_eval_runner import _compute_entropy

        # Uniform distribution has higher entropy
        uniform_probs = [0.2, 0.2, 0.2, 0.2, 0.2]
        uniform_entropy = _compute_entropy(uniform_probs)

        # Peaked distribution has lower entropy
        peaked_probs = [0.8, 0.05, 0.05, 0.05, 0.05]
        peaked_entropy = _compute_entropy(peaked_probs)

        assert uniform_entropy > peaked_entropy

    def test_stability_tracker(self) -> None:
        """Test stability tracker for top-k moves."""
        from renacechess.eval.runtime_recalibration_eval_runner import StabilityTracker

        tracker = StabilityTracker()

        # Same top-1
        tracker.add(
            [("e2e4", 0.5), ("d2d4", 0.3), ("g1f3", 0.2)],
            [("e2e4", 0.4), ("d2d4", 0.35), ("g1f3", 0.25)],
        )
        assert tracker.top1_unchanged == 1
        assert tracker.top3_unchanged == 1

        # Different top-1
        tracker.add(
            [("e2e4", 0.5), ("d2d4", 0.3), ("g1f3", 0.2)],
            [("d2d4", 0.45), ("e2e4", 0.35), ("g1f3", 0.2)],
        )
        assert tracker.top1_unchanged == 1  # Still 1, second was different
        assert tracker.top3_unchanged == 2  # Same set

        # Different top-3 set
        tracker.add(
            [("e2e4", 0.5), ("d2d4", 0.3), ("g1f3", 0.2)],
            [("e2e4", 0.5), ("d2d4", 0.3), ("c2c4", 0.2)],  # g1f3 -> c2c4
        )
        assert tracker.top3_unchanged == 2  # Still 2, third had different set

        assert tracker.total == 3
        assert tracker.get_top1_stability() == 2 / 3
        assert tracker.get_top3_stability() == 2 / 3


# =============================================================================
# Calibration Snapshot Tests
# =============================================================================


class TestEdgeCases:
    """Edge case tests for additional coverage."""

    def test_accumulator_with_no_moves(self) -> None:
        """Test accumulator handles empty policy moves."""
        from renacechess.eval.runtime_recalibration_eval_runner import RuntimeEvalAccumulator

        acc = RuntimeEvalAccumulator()

        # Add policy with empty moves - should not crash
        acc.add_policy([], "e2e4", 0.0)

        # Entropy count should still be 0 (no moves added)
        assert acc.entropy_count == 0
        assert acc.positions_evaluated == 0

    def test_stability_tracker_with_empty_moves(self) -> None:
        """Test stability tracker handles empty move lists."""
        from renacechess.eval.runtime_recalibration_eval_runner import StabilityTracker

        tracker = StabilityTracker()

        # Empty moves - should not crash or count
        tracker.add([], [("e2e4", 0.5)])
        tracker.add([("e2e4", 0.5)], [])
        tracker.add([], [])

        assert tracker.total == 0

    def test_entropy_computation_edge_cases(self) -> None:
        """Test entropy with edge case probabilities."""
        from renacechess.eval.runtime_recalibration_eval_runner import _compute_entropy

        # Empty list
        assert _compute_entropy([]) == 0.0

        # Single element
        assert _compute_entropy([1.0]) == 0.0

        # Zero probability (should be skipped)
        assert _compute_entropy([1.0, 0.0]) == 0.0

    def test_recalibration_with_missing_bucket(self) -> None:
        """Test recalibration gracefully handles missing bucket."""
        from renacechess.contracts.models import RecalibrationParametersV1
        from renacechess.eval.runtime_recalibration_eval_runner import (
            _apply_recalibration_to_policy,
        )

        # Create minimal params without "unknown_bucket"
        params = RecalibrationParametersV1.model_validate({
            "version": "1.0",
            "generatedAt": "2026-01-01T00:00:00Z",
            "sourceCalibrationMetricsHash": "sha256:" + "0" * 64,
            "sourceManifestHash": "0" * 64,
            "policyId": "test",
            "byEloBucket": [],
            "determinismHash": "sha256:" + "0" * 64,
        })

        top_moves = [("e2e4", 0.5), ("d2d4", 0.3)]

        # Should return unchanged when bucket not found
        result = _apply_recalibration_to_policy(top_moves, "unknown_bucket", params)
        assert result == top_moves


class TestRuntimeCalibrationSnapshotV1:
    """Tests for RuntimeCalibrationSnapshotV1."""

    def test_valid_snapshot(self) -> None:
        """Test valid snapshot construction."""
        snapshot = RuntimeCalibrationSnapshotV1(
            outcome_ece=0.1,
            outcome_nll=0.5,
            outcome_brier=0.2,
            policy_nll=1.2,
            policy_top1_ece=0.15,
            mean_entropy=1.5,
        )
        assert snapshot.outcome_ece == 0.1
        assert snapshot.mean_entropy == 1.5

    def test_snapshot_bounds_validation(self) -> None:
        """Test that ECE and Brier are bounded [0, 1]."""
        # ECE out of bounds
        with pytest.raises(ValueError):
            RuntimeCalibrationSnapshotV1(
                outcome_ece=1.5,  # Invalid
                outcome_nll=0.5,
                outcome_brier=0.2,
                policy_nll=1.2,
                policy_top1_ece=0.15,
                mean_entropy=1.5,
            )

        # Brier out of bounds
        with pytest.raises(ValueError):
            RuntimeCalibrationSnapshotV1(
                outcome_ece=0.1,
                outcome_nll=0.5,
                outcome_brier=1.5,  # Invalid
                policy_nll=1.2,
                policy_top1_ece=0.15,
                mean_entropy=1.5,
            )

    def test_snapshot_alias_mapping(self) -> None:
        """Test camelCase aliases."""
        snapshot = RuntimeCalibrationSnapshotV1(
            outcome_ece=0.1,
            outcome_nll=0.5,
            outcome_brier=0.2,
            policy_nll=1.2,
            policy_top1_ece=0.15,
            mean_entropy=1.5,
        )
        dumped = snapshot.model_dump(by_alias=True)
        assert "outcomeEce" in dumped
        assert "outcomeNll" in dumped
        assert "outcomeBrier" in dumped
        assert "policyNll" in dumped
        assert "policyTop1Ece" in dumped
        assert "meanEntropy" in dumped

