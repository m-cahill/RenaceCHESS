"""Tests for M25 recalibration functionality."""

import json
from pathlib import Path

import pytest

from renacechess.contracts.models import (
    CalibrationDeltaArtifactV1,
    CalibrationDeltaV1,
    CalibrationMetricsV1,
    RecalibrationBucketParametersV1,
    RecalibrationParametersV1,
)
from renacechess.eval.calibration_runner import (
    get_canonical_skill_buckets,
    run_calibration_evaluation,
)
from renacechess.eval.recalibration_runner import (
    TEMPERATURE_MAX,
    TEMPERATURE_MIN,
    apply_temperature_scaling_to_probs,
    compute_calibration_delta,
    fit_recalibration_parameters,
    load_calibration_metrics,
    load_recalibration_parameters,
    run_calibration_evaluation_with_recalibration,
    save_calibration_delta,
    save_recalibration_parameters,
)


class TestTemperatureScaling:
    """Test temperature scaling function."""

    def test_temperature_scaling_uniform_probs(self) -> None:
        """Test that uniform probabilities remain uniform after temperature scaling."""
        probs = [0.25, 0.25, 0.25, 0.25]
        scaled = apply_temperature_scaling_to_probs(probs, 2.0)
        # Uniform probs should remain uniform regardless of temperature
        assert all(abs(p - 0.25) < 1e-6 for p in scaled)

    def test_temperature_scaling_extreme_probs(self) -> None:
        """Test temperature scaling with extreme probabilities."""
        probs = [0.9, 0.05, 0.03, 0.02]
        # High temperature should make distribution more uniform
        scaled_high = apply_temperature_scaling_to_probs(probs, 3.0)
        # Low temperature should make distribution more peaked
        scaled_low = apply_temperature_scaling_to_probs(probs, 0.5)

        # High temp: max prob should decrease
        assert max(scaled_high) < max(probs)
        # Low temp: max prob should increase
        assert max(scaled_low) > max(probs)

    def test_temperature_scaling_preserves_sum(self) -> None:
        """Test that scaled probabilities sum to 1.0."""
        probs = [0.5, 0.3, 0.2]
        for temp in [0.5, 1.0, 2.0]:
            scaled = apply_temperature_scaling_to_probs(probs, temp)
            assert abs(sum(scaled) - 1.0) < 1e-6

    def test_temperature_scaling_empty_list(self) -> None:
        """Test temperature scaling with empty list."""
        assert apply_temperature_scaling_to_probs([], 1.0) == []

    def test_temperature_scaling_zero_probability(self) -> None:
        """Test temperature scaling with zero probabilities."""
        probs = [0.7, 0.3, 0.0]
        scaled = apply_temperature_scaling_to_probs(probs, 1.5)
        assert all(p >= 0 for p in scaled)
        assert abs(sum(scaled) - 1.0) < 1e-6


class TestRecalibrationParametersSchema:
    """Test RecalibrationParametersV1 schema validation."""

    def test_recalibration_bucket_parameters_valid(self) -> None:
        """Test valid RecalibrationBucketParametersV1."""
        params = RecalibrationBucketParametersV1(
            elo_bucket="1200_1399",
            outcome_temperature=1.5,
            policy_temperature=1.2,
            fit_method="grid_search",
            fit_metric="nll",
        )
        assert params.elo_bucket == "1200_1399"
        assert params.outcome_temperature == 1.5
        assert params.policy_temperature == 1.2

    def test_recalibration_bucket_parameters_bounds(self) -> None:
        """Test temperature bounds enforcement."""
        # Valid bounds
        params = RecalibrationBucketParametersV1(
            elo_bucket="1200_1399",
            outcome_temperature=TEMPERATURE_MIN,
            policy_temperature=TEMPERATURE_MAX,
            fit_method="grid_search",
            fit_metric="nll",
        )
        assert params.outcome_temperature == TEMPERATURE_MIN
        assert params.policy_temperature == TEMPERATURE_MAX

        # Invalid bounds (should raise)
        with pytest.raises(Exception):  # Pydantic validation error
            RecalibrationBucketParametersV1(
                elo_bucket="1200_1399",
                outcome_temperature=TEMPERATURE_MIN - 0.1,
                policy_temperature=1.0,
                fit_method="grid_search",
                fit_metric="nll",
            )

    def test_recalibration_parameters_v1_valid(self) -> None:
        """Test valid RecalibrationParametersV1."""
        from datetime import UTC, datetime

        params = RecalibrationParametersV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            source_calibration_metrics_hash="sha256:" + "a" * 64,
            source_manifest_hash="b" * 64,
            policy_id="baseline.uniform_random",
            outcome_head_id=None,
            by_elo_bucket=[
                RecalibrationBucketParametersV1(
                    elo_bucket="1200_1399",
                    outcome_temperature=1.5,
                    policy_temperature=1.2,
                    fit_method="grid_search",
                    fit_metric="nll",
                )
            ],
            determinism_hash="sha256:" + "c" * 64,
        )
        assert params.version == "1.0"
        assert len(params.by_elo_bucket) == 1

    def test_recalibration_parameters_json_roundtrip(self) -> None:
        """Test JSON serialization/deserialization."""
        from datetime import UTC, datetime

        params = RecalibrationParametersV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            source_calibration_metrics_hash="sha256:" + "a" * 64,
            source_manifest_hash="b" * 64,
            policy_id="baseline.uniform_random",
            outcome_head_id=None,
            by_elo_bucket=[
                RecalibrationBucketParametersV1(
                    elo_bucket="1200_1399",
                    outcome_temperature=1.5,
                    policy_temperature=1.2,
                    fit_method="grid_search",
                    fit_metric="nll",
                )
            ],
            determinism_hash="sha256:" + "c" * 64,
        )

        # Serialize
        json_str = json.dumps(params.model_dump(by_alias=True), default=str)
        data = json.loads(json_str)

        # Deserialize
        loaded = RecalibrationParametersV1.model_validate(data)
        assert loaded.version == params.version
        assert len(loaded.by_elo_bucket) == len(params.by_elo_bucket)
        assert loaded.by_elo_bucket[0].elo_bucket == params.by_elo_bucket[0].elo_bucket


class TestCalibrationDeltaSchema:
    """Test CalibrationDeltaV1 schema validation."""

    def test_calibration_delta_v1_valid(self) -> None:
        """Test valid CalibrationDeltaV1."""
        delta = CalibrationDeltaV1(
            elo_bucket="1200_1399",
            metric="outcome_ece",
            before=0.05,
            after=0.03,
            delta=-0.02,
            improved=True,
        )
        assert delta.elo_bucket == "1200_1399"
        assert delta.metric == "outcome_ece"
        assert delta.improved is True

    def test_calibration_delta_improved_logic(self) -> None:
        """Test that improved flag is correct for different metrics."""
        # ECE: negative delta = improvement
        delta1 = CalibrationDeltaV1(
            elo_bucket="1200_1399",
            metric="outcome_ece",
            before=0.05,
            after=0.03,
            delta=-0.02,
            improved=True,
        )
        assert delta1.improved is True

        # NLL: negative delta = improvement
        delta2 = CalibrationDeltaV1(
            elo_bucket="1200_1399",
            metric="outcome_nll",
            before=1.5,
            after=1.3,
            delta=-0.2,
            improved=True,
        )
        assert delta2.improved is True

        # Degradation
        delta3 = CalibrationDeltaV1(
            elo_bucket="1200_1399",
            metric="outcome_ece",
            before=0.03,
            after=0.05,
            delta=0.02,
            improved=False,
        )
        assert delta3.improved is False


class TestRecalibrationFitting:
    """Test recalibration parameter fitting."""

    @pytest.fixture
    def frozen_eval_manifest_path(self) -> Path:
        """Path to frozen eval manifest fixture."""
        return Path(__file__).parent / "fixtures" / "frozen_eval" / "manifest.json"

    @pytest.fixture
    def calibration_metrics(self, frozen_eval_manifest_path: Path) -> CalibrationMetricsV1:
        """Generate calibration metrics for testing."""
        return run_calibration_evaluation(
            manifest_path=frozen_eval_manifest_path,
            policy_id="baseline.uniform_random",
        )

    def test_fit_recalibration_parameters(
        self, frozen_eval_manifest_path: Path, calibration_metrics: CalibrationMetricsV1
    ) -> None:
        """Test fitting recalibration parameters."""
        params = fit_recalibration_parameters(
            manifest_path=frozen_eval_manifest_path,
            calibration_metrics=calibration_metrics,
            policy_id="baseline.uniform_random",
        )

        assert params.version == "1.0"
        assert len(params.by_elo_bucket) > 0
        assert params.source_calibration_metrics_hash == calibration_metrics.determinism_hash

        # Check all buckets have valid temperatures
        for bucket_params in params.by_elo_bucket:
            assert TEMPERATURE_MIN <= bucket_params.outcome_temperature <= TEMPERATURE_MAX
            assert TEMPERATURE_MIN <= bucket_params.policy_temperature <= TEMPERATURE_MAX
            assert bucket_params.fit_method == "grid_search"
            assert bucket_params.fit_metric == "nll"

    def test_fit_recalibration_parameters_deterministic(
        self, frozen_eval_manifest_path: Path, calibration_metrics: CalibrationMetricsV1
    ) -> None:
        """Test that fitting is deterministic."""
        params1 = fit_recalibration_parameters(
            manifest_path=frozen_eval_manifest_path,
            calibration_metrics=calibration_metrics,
            policy_id="baseline.uniform_random",
        )
        params2 = fit_recalibration_parameters(
            manifest_path=frozen_eval_manifest_path,
            calibration_metrics=calibration_metrics,
            policy_id="baseline.uniform_random",
        )

        # Temperatures should be identical
        for b1, b2 in zip(params1.by_elo_bucket, params2.by_elo_bucket):
            assert b1.elo_bucket == b2.elo_bucket
            assert b1.outcome_temperature == b2.outcome_temperature
            assert b1.policy_temperature == b2.policy_temperature


class TestRecalibrationApplication:
    """Test applying recalibration parameters."""

    @pytest.fixture
    def frozen_eval_manifest_path(self) -> Path:
        """Path to frozen eval manifest fixture."""
        return Path(__file__).parent / "fixtures" / "frozen_eval" / "manifest.json"

    @pytest.fixture
    def calibration_metrics(self, frozen_eval_manifest_path: Path) -> CalibrationMetricsV1:
        """Generate calibration metrics for testing."""
        return run_calibration_evaluation(
            manifest_path=frozen_eval_manifest_path,
            policy_id="baseline.uniform_random",
        )

    @pytest.fixture
    def recalibration_params(
        self, frozen_eval_manifest_path: Path, calibration_metrics: CalibrationMetricsV1
    ) -> RecalibrationParametersV1:
        """Generate recalibration parameters for testing."""
        return fit_recalibration_parameters(
            manifest_path=frozen_eval_manifest_path,
            calibration_metrics=calibration_metrics,
            policy_id="baseline.uniform_random",
        )

    def test_run_calibration_evaluation_with_recalibration(
        self,
        frozen_eval_manifest_path: Path,
        recalibration_params: RecalibrationParametersV1,
    ) -> None:
        """Test running calibration evaluation with recalibration applied."""
        metrics_after = run_calibration_evaluation_with_recalibration(
            manifest_path=frozen_eval_manifest_path,
            recalibration_params=recalibration_params,
            policy_id="baseline.uniform_random",
        )

        assert metrics_after.version == "1.0"
        assert len(metrics_after.by_elo_bucket) > 0
        assert metrics_after.determinism_hash.startswith("sha256:")

    def test_compute_calibration_delta(
        self,
        frozen_eval_manifest_path: Path,
        calibration_metrics: CalibrationMetricsV1,
        recalibration_params: RecalibrationParametersV1,
    ) -> None:
        """Test computing calibration delta."""
        metrics_after = run_calibration_evaluation_with_recalibration(
            manifest_path=frozen_eval_manifest_path,
            recalibration_params=recalibration_params,
            policy_id="baseline.uniform_random",
        )

        delta = compute_calibration_delta(
            metrics_before=calibration_metrics,
            metrics_after=metrics_after,
            recalibration_params=recalibration_params,
        )

        assert delta.version == "1.0"
        assert len(delta.by_elo_bucket) > 0
        assert delta.source_calibration_metrics_before_hash == calibration_metrics.determinism_hash
        assert delta.source_calibration_metrics_after_hash == metrics_after.determinism_hash

        # Check delta structure
        for bucket_deltas in delta.by_elo_bucket:
            assert len(bucket_deltas) > 0
            for d in bucket_deltas:
                assert d.elo_bucket in get_canonical_skill_buckets()
                assert d.metric in [
                    "outcome_ece",
                    "outcome_nll",
                    "outcome_brier",
                    "policy_nll",
                    "policy_top1_ece",
                ]
                assert d.delta == d.after - d.before
                # Improved should be True if delta < 0 (for ECE/NLL/Brier)
                if d.metric in [
                    "outcome_ece",
                    "outcome_nll",
                    "outcome_brier",
                    "policy_nll",
                    "policy_top1_ece",
                ]:
                    assert d.improved == (d.delta < 0)


class TestRecalibrationIO:
    """Test loading/saving recalibration artifacts."""

    def test_save_and_load_recalibration_parameters(self, tmp_path: Path) -> None:
        """Test saving and loading recalibration parameters."""
        from datetime import UTC, datetime

        params = RecalibrationParametersV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            source_calibration_metrics_hash="sha256:" + "a" * 64,
            source_manifest_hash="b" * 64,
            policy_id="baseline.uniform_random",
            outcome_head_id=None,
            by_elo_bucket=[
                RecalibrationBucketParametersV1(
                    elo_bucket="1200_1399",
                    outcome_temperature=1.5,
                    policy_temperature=1.2,
                    fit_method="grid_search",
                    fit_metric="nll",
                )
            ],
            determinism_hash="sha256:" + "c" * 64,
        )

        out_path = tmp_path / "params.json"
        save_recalibration_parameters(params, out_path)
        assert out_path.exists()

        loaded = load_recalibration_parameters(out_path)
        assert loaded.version == params.version
        assert len(loaded.by_elo_bucket) == len(params.by_elo_bucket)

    def test_load_calibration_metrics(self, tmp_path: Path) -> None:
        """Test loading calibration metrics."""
        from datetime import UTC, datetime

        from renacechess.contracts.models import EloBucketCalibrationV1

        metrics = CalibrationMetricsV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            source_manifest_hash="a" * 64,
            policy_id="baseline.uniform_random",
            outcome_head_id=None,
            overall_samples=100,
            overall_outcome_calibration=None,
            overall_policy_calibration=None,
            by_elo_bucket=[
                EloBucketCalibrationV1(
                    elo_bucket="1200_1399",
                    samples=50,
                    outcome_calibration=None,
                    policy_calibration=None,
                )
            ],
            determinism_hash="sha256:" + "b" * 64,
        )

        out_path = tmp_path / "metrics.json"
        out_path.write_text(
            json.dumps(metrics.model_dump(by_alias=True), default=str),
            encoding="utf-8",
        )

        loaded = load_calibration_metrics(out_path)
        assert loaded.version == metrics.version
        assert loaded.overall_samples == metrics.overall_samples

    def test_save_calibration_delta(self, tmp_path: Path) -> None:
        """Test saving calibration delta."""
        from datetime import UTC, datetime

        delta = CalibrationDeltaArtifactV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            source_recalibration_parameters_hash="sha256:" + "a" * 64,
            source_calibration_metrics_before_hash="sha256:" + "b" * 64,
            source_calibration_metrics_after_hash="sha256:" + "c" * 64,
            by_elo_bucket=[
                [
                    CalibrationDeltaV1(
                        elo_bucket="1200_1399",
                        metric="outcome_ece",
                        before=0.05,
                        after=0.03,
                        delta=-0.02,
                        improved=True,
                    )
                ]
            ],
            determinism_hash="sha256:" + "d" * 64,
        )

        out_path = tmp_path / "delta.json"
        save_calibration_delta(delta, out_path)
        assert out_path.exists()

        # Verify it can be loaded
        data = json.loads(out_path.read_text(encoding="utf-8"))
        loaded = CalibrationDeltaArtifactV1.model_validate(data)
        assert loaded.version == delta.version
        assert len(loaded.by_elo_bucket) == len(delta.by_elo_bucket)


class TestRecalibrationCLI:
    """Test recalibration CLI command integration."""

    @pytest.fixture
    def frozen_eval_manifest_path(self) -> Path:
        """Path to frozen eval manifest fixture."""
        return Path(__file__).parent / "fixtures" / "frozen_eval" / "manifest.json"

    def test_recalibration_fit_cli_requires_manifest(self, tmp_path: Path) -> None:
        """Test that recalibration fit CLI fails fast if --manifest is missing."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "renacechess.cli", "recalibration", "fit"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert result.returncode != 0
        assert "manifest" in result.stderr.lower() or "required" in result.stderr.lower()

    def test_recalibration_fit_cli_with_fixture(
        self, frozen_eval_manifest_path: Path, tmp_path: Path
    ) -> None:
        """Test recalibration fit CLI command with CI fixture."""
        import subprocess
        import sys

        # First run calibration to get metrics
        calibration_output = tmp_path / "calibration_metrics.json"
        cal_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "calibration",
                "--manifest",
                str(frozen_eval_manifest_path),
                "--out",
                str(calibration_output),
            ],
            capture_output=True,
            text=True,
        )

        assert cal_result.returncode == 0, f"Calibration failed: {cal_result.stderr}"
        assert calibration_output.exists()

        # Now run recalibration fit
        recal_output = tmp_path / "recalibration_params.json"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "recalibration",
                "fit",
                "--manifest",
                str(frozen_eval_manifest_path),
                "--calibration-metrics",
                str(calibration_output),
                "--policy-id",
                "baseline.uniform_random",
                "--out",
                str(recal_output),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Recalibration fit failed: {result.stderr}"
        assert recal_output.exists()

        # Verify output is valid JSON
        data = json.loads(recal_output.read_text(encoding="utf-8"))
        assert data["version"] == "1.0"
        assert "byEloBucket" in data

    def test_recalibration_evaluate_cli_requires_params(self, tmp_path: Path) -> None:
        """Test that recalibration evaluate CLI fails fast if --recalibration-params is missing."""
        import subprocess
        import sys

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "recalibration",
                "evaluate",
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert result.returncode != 0
        assert "recalibration" in result.stderr.lower() or "required" in result.stderr.lower()

    def test_calibration_cli_with_recalibration_flag(
        self, frozen_eval_manifest_path: Path, tmp_path: Path
    ) -> None:
        """Test calibration CLI with --with-recalibration flag (preview mode)."""
        import subprocess
        import sys

        # First create recalibration parameters
        calibration_output = tmp_path / "calibration_metrics.json"
        cal_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "calibration",
                "--manifest",
                str(frozen_eval_manifest_path),
                "--out",
                str(calibration_output),
            ],
            capture_output=True,
            text=True,
        )

        assert cal_result.returncode == 0

        recal_output = tmp_path / "recalibration_params.json"
        fit_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "recalibration",
                "fit",
                "--manifest",
                str(frozen_eval_manifest_path),
                "--calibration-metrics",
                str(calibration_output),
                "--policy-id",
                "baseline.uniform_random",
                "--out",
                str(recal_output),
            ],
            capture_output=True,
            text=True,
        )

        assert fit_result.returncode == 0

        # Test calibration with --with-recalibration flag
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "calibration",
                "--manifest",
                str(frozen_eval_manifest_path),
                "--with-recalibration",
                str(recal_output),
            ],
            capture_output=True,
            text=True,
        )

        # Should succeed and show before/after comparison
        assert result.returncode == 0
        # Preview output goes to stderr, not stdout
        assert "recalibration preview" in result.stderr.lower()
        # Check for arrow (→), delta symbol (Δ), or "delta" text
        # Windows may show escaped Unicode (\\u2192, \\u0394)
        assert (
            "→" in result.stderr
            or "\\u2192" in result.stderr
            or "delta" in result.stderr.lower()
            or "Δ" in result.stderr
        )

    def test_recalibration_fit_cli_manifest_not_found(self, tmp_path: Path) -> None:
        """Test that recalibration fit CLI fails with clear error if manifest not found."""
        import subprocess
        import sys

        fake_manifest = tmp_path / "nonexistent.json"
        fake_metrics = tmp_path / "metrics.json"
        fake_metrics.write_text("{}", encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "recalibration",
                "fit",
                "--manifest",
                str(fake_manifest),
                "--calibration-metrics",
                str(fake_metrics),
                "--out",
                str(tmp_path / "out.json"),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_recalibration_fit_cli_metrics_not_found(
        self, frozen_eval_manifest_path: Path, tmp_path: Path
    ) -> None:
        """Test that recalibration fit CLI fails if calibration metrics not found."""
        import subprocess
        import sys

        fake_metrics = tmp_path / "nonexistent_metrics.json"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "recalibration",
                "fit",
                "--manifest",
                str(frozen_eval_manifest_path),
                "--calibration-metrics",
                str(fake_metrics),
                "--out",
                str(tmp_path / "out.json"),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_recalibration_preview_cli(
        self, frozen_eval_manifest_path: Path, tmp_path: Path
    ) -> None:
        """Test recalibration preview CLI command."""
        import subprocess
        import sys

        # First create calibration metrics and recalibration parameters
        calibration_output = tmp_path / "calibration_metrics.json"
        cal_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "calibration",
                "--manifest",
                str(frozen_eval_manifest_path),
                "--out",
                str(calibration_output),
            ],
            capture_output=True,
            text=True,
        )

        assert cal_result.returncode == 0

        recal_output = tmp_path / "recalibration_params.json"
        fit_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "recalibration",
                "fit",
                "--manifest",
                str(frozen_eval_manifest_path),
                "--calibration-metrics",
                str(calibration_output),
                "--policy-id",
                "baseline.uniform_random",
                "--out",
                str(recal_output),
            ],
            capture_output=True,
            text=True,
        )

        assert fit_result.returncode == 0

        # Now test preview command
        delta_output = tmp_path / "delta.json"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "recalibration",
                "preview",
                "--manifest",
                str(frozen_eval_manifest_path),
                "--calibration-metrics-before",
                str(calibration_output),
                "--recalibration-parameters",
                str(recal_output),
                "--out",
                str(delta_output),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Preview failed: {result.stderr}"
        assert delta_output.exists()
        assert "recalibration preview" in result.stderr.lower()

        # Verify output is valid JSON
        data = json.loads(delta_output.read_text(encoding="utf-8"))
        assert data["version"] == "1.0"
        assert "byEloBucket" in data

    def test_recalibration_preview_cli_manifest_not_found(self, tmp_path: Path) -> None:
        """Test that recalibration preview CLI fails if manifest not found."""
        import subprocess
        import sys

        fake_manifest = tmp_path / "nonexistent.json"
        fake_metrics = tmp_path / "metrics.json"
        fake_metrics.write_text("{}", encoding="utf-8")
        fake_params = tmp_path / "params.json"
        fake_params.write_text("{}", encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "recalibration",
                "preview",
                "--manifest",
                str(fake_manifest),
                "--calibration-metrics-before",
                str(fake_metrics),
                "--recalibration-parameters",
                str(fake_params),
                "--out",
                str(tmp_path / "out.json"),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_recalibration_preview_cli_metrics_not_found(
        self, frozen_eval_manifest_path: Path, tmp_path: Path
    ) -> None:
        """Test that recalibration preview CLI fails if calibration metrics not found."""
        import subprocess
        import sys

        fake_metrics = tmp_path / "nonexistent_metrics.json"
        fake_params = tmp_path / "params.json"
        fake_params.write_text("{}", encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "recalibration",
                "preview",
                "--manifest",
                str(frozen_eval_manifest_path),
                "--calibration-metrics-before",
                str(fake_metrics),
                "--recalibration-parameters",
                str(fake_params),
                "--out",
                str(tmp_path / "out.json"),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_recalibration_preview_cli_params_not_found(
        self, frozen_eval_manifest_path: Path, tmp_path: Path
    ) -> None:
        """Test that recalibration preview CLI fails if recalibration parameters not found."""
        import subprocess
        import sys

        fake_metrics = tmp_path / "metrics.json"
        fake_metrics.write_text("{}", encoding="utf-8")
        fake_params = tmp_path / "nonexistent_params.json"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "recalibration",
                "preview",
                "--manifest",
                str(frozen_eval_manifest_path),
                "--calibration-metrics-before",
                str(fake_metrics),
                "--recalibration-parameters",
                str(fake_params),
                "--out",
                str(tmp_path / "out.json"),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_recalibration_invalid_command(self, tmp_path: Path) -> None:
        """Test that recalibration CLI fails with invalid command."""
        import subprocess
        import sys

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "renacechess.cli",
                "recalibration",
                "invalid_command",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
