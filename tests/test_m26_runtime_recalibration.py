"""Tests for M26 runtime recalibration gating."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from renacechess.contracts.models import (
    RecalibrationBucketParametersV1,
    RecalibrationGateV1,
    RecalibrationParametersV1,
)
from renacechess.eval.runtime_recalibration import (
    RuntimeRecalibrationMetadata,
    apply_recalibration_if_enabled,
    apply_recalibration_to_outcome_if_enabled,
    load_recalibration_gate,
)


class TestRecalibrationGateV1:
    """Tests for RecalibrationGateV1 contract."""

    def test_gate_disabled(self) -> None:
        """Gate with enabled=False is valid."""
        gate = RecalibrationGateV1(
            version="1.0",
            enabled=False,
            scope="both",
        )
        assert gate.enabled is False
        assert gate.parameters_ref is None

    def test_gate_enabled_with_params_ref(self) -> None:
        """Gate with enabled=True and parameters_ref is valid."""
        gate = RecalibrationGateV1(
            version="1.0",
            enabled=True,
            parameters_ref="path/to/params.json",
            scope="both",
        )
        assert gate.enabled is True
        assert gate.parameters_ref == "path/to/params.json"

    def test_gate_enabled_without_params_ref_invalid(self) -> None:
        """Gate with enabled=True but no parameters_ref is invalid."""
        with pytest.raises(ValueError, match="enabled=True requires parametersRef"):
            RecalibrationGateV1(
                version="1.0",
                enabled=True,
                parameters_ref=None,
                scope="both",
            )

    def test_gate_scope_values(self) -> None:
        """Gate scope accepts outcome, policy, or both."""
        for scope in ["outcome", "policy", "both"]:
            gate = RecalibrationGateV1(
                version="1.0",
                enabled=False,
                scope=scope,
            )
            assert gate.scope == scope


class TestLoadRecalibrationGate:
    """Tests for loading RecalibrationGateV1 from file."""

    def test_load_gate_disabled(self, tmp_path: Path) -> None:
        """Load gate with enabled=False."""
        gate_file = tmp_path / "gate.json"
        gate_file.write_text(
            '{"version": "1.0", "enabled": false, "scope": "both"}',
            encoding="utf-8",
        )

        gate = load_recalibration_gate(gate_file)
        assert gate.enabled is False

    def test_load_gate_enabled(self, tmp_path: Path) -> None:
        """Load gate with enabled=True."""
        gate_file = tmp_path / "gate.json"
        gate_file.write_text(
            '{"version": "1.0", "enabled": true, "parametersRef": "params.json", "scope": "both"}',
            encoding="utf-8",
        )

        gate = load_recalibration_gate(gate_file)
        assert gate.enabled is True
        assert gate.parameters_ref == "params.json"

    def test_load_gate_missing_file(self, tmp_path: Path) -> None:
        """Loading non-existent gate file raises FileNotFoundError."""
        gate_file = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_recalibration_gate(gate_file)

    def test_load_gate_enabled_without_params_ref(self, tmp_path: Path) -> None:
        """Loading gate with enabled=True but no parametersRef raises ValueError."""
        gate_file = tmp_path / "gate.json"
        gate_file.write_text(
            '{"version": "1.0", "enabled": true, "scope": "both"}',
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="enabled=True requires parametersRef"):
            load_recalibration_gate(gate_file)


class TestApplyRecalibrationIfEnabled:
    """Tests for apply_recalibration_if_enabled wrapper."""

    def test_gate_disabled_no_change(self) -> None:
        """Gate disabled returns input probabilities unchanged."""
        gate = RecalibrationGateV1(version="1.0", enabled=False, scope="both")
        probs = [0.5, 0.3, 0.2]

        scaled_probs, metadata = apply_recalibration_if_enabled(probs, "1200-1400", gate, None)

        assert scaled_probs == probs
        assert metadata.applied is False
        assert metadata.gate_hash is not None
        assert metadata.parameters_hash is None

    def test_gate_enabled_applies_scaling(self) -> None:
        """Gate enabled applies temperature scaling."""
        gate = RecalibrationGateV1(
            version="1.0",
            enabled=True,
            parameters_ref="params.json",
            scope="policy",
        )
        params = RecalibrationParametersV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            source_calibration_metrics_hash="sha256:" + "0" * 64,
            source_manifest_hash="0" * 64,
            policy_id="baseline.uniform_random",
            by_elo_bucket=[
                RecalibrationBucketParametersV1(
                    elo_bucket="1200-1400",
                    outcome_temperature=1.0,
                    policy_temperature=0.5,  # Sharper (lower temp)
                    fit_method="grid_search",
                    fit_metric="nll",
                )
            ],
            determinism_hash="sha256:" + "0" * 64,
        )

        # Non-uniform probabilities (temperature scaling requires non-uniform input
        # to observe changes)
        probs = [0.4, 0.3, 0.2, 0.1]

        scaled_probs, metadata = apply_recalibration_if_enabled(probs, "1200-1400", gate, params)

        # With temperature 0.5, probabilities should be sharper (more peaked)
        assert scaled_probs != probs
        assert abs(sum(scaled_probs) - 1.0) < 1e-6
        assert metadata.applied is True
        assert metadata.parameters_hash is not None
        assert metadata.scope == "policy"

    def test_gate_enabled_missing_params_raises(self) -> None:
        """Gate enabled but params=None raises ValueError."""
        gate = RecalibrationGateV1(
            version="1.0",
            enabled=True,
            parameters_ref="params.json",
            scope="both",
        )

        with pytest.raises(ValueError, match="requires RecalibrationParametersV1"):
            apply_recalibration_if_enabled([0.5, 0.5], "1200-1400", gate, None)

    def test_gate_enabled_missing_bucket_raises(self) -> None:
        """Gate enabled but bucket not in params raises ValueError."""
        gate = RecalibrationGateV1(
            version="1.0",
            enabled=True,
            parameters_ref="params.json",
            scope="both",
        )
        params = RecalibrationParametersV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            source_calibration_metrics_hash="sha256:" + "0" * 64,
            source_manifest_hash="0" * 64,
            policy_id="baseline.uniform_random",
            by_elo_bucket=[
                RecalibrationBucketParametersV1(
                    elo_bucket="1600-1800",  # Different bucket
                    outcome_temperature=1.0,
                    policy_temperature=1.0,
                    fit_method="grid_search",
                    fit_metric="nll",
                )
            ],
            determinism_hash="sha256:" + "0" * 64,
        )

        with pytest.raises(ValueError, match="does not contain parameters for bucket"):
            apply_recalibration_if_enabled([0.5, 0.5], "1200-1400", gate, params)

    def test_gate_scope_policy_only(self) -> None:
        """Gate with scope=policy only applies to policy probabilities."""
        gate = RecalibrationGateV1(
            version="1.0",
            enabled=True,
            parameters_ref="params.json",
            scope="policy",
        )
        params = RecalibrationParametersV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            source_calibration_metrics_hash="sha256:" + "0" * 64,
            source_manifest_hash="0" * 64,
            policy_id="baseline.uniform_random",
            by_elo_bucket=[
                RecalibrationBucketParametersV1(
                    elo_bucket="1200-1400",
                    outcome_temperature=2.0,  # Different temp
                    policy_temperature=0.5,
                    fit_method="grid_search",
                    fit_metric="nll",
                )
            ],
            determinism_hash="sha256:" + "0" * 64,
        )

        # Non-uniform probabilities (temperature scaling requires non-uniform input
        # to observe changes)
        probs = [0.4, 0.3, 0.2, 0.1]

        scaled_probs, metadata = apply_recalibration_if_enabled(probs, "1200-1400", gate, params)

        # Should use policy_temperature (0.5), not outcome_temperature (2.0)
        # With temp 0.5, probabilities should be sharper (more peaked)
        assert scaled_probs != probs
        assert metadata.scope == "policy"


class TestApplyRecalibrationToOutcomeIfEnabled:
    """Tests for apply_recalibration_to_outcome_if_enabled wrapper."""

    def test_gate_disabled_no_change(self) -> None:
        """Gate disabled returns input probabilities unchanged."""
        gate = RecalibrationGateV1(version="1.0", enabled=False, scope="both")
        p_win, p_draw, p_loss = 0.4, 0.3, 0.3

        (scaled_w, scaled_d, scaled_l), metadata = apply_recalibration_to_outcome_if_enabled(
            p_win, p_draw, p_loss, "1200-1400", gate, None
        )

        assert (scaled_w, scaled_d, scaled_l) == (p_win, p_draw, p_loss)
        assert metadata.applied is False

    def test_gate_enabled_applies_scaling(self) -> None:
        """Gate enabled applies temperature scaling to outcome probabilities."""
        gate = RecalibrationGateV1(
            version="1.0",
            enabled=True,
            parameters_ref="params.json",
            scope="outcome",
        )
        params = RecalibrationParametersV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            source_calibration_metrics_hash="sha256:" + "0" * 64,
            source_manifest_hash="0" * 64,
            policy_id="baseline.uniform_random",
            by_elo_bucket=[
                RecalibrationBucketParametersV1(
                    elo_bucket="1200-1400",
                    outcome_temperature=0.5,  # Sharper
                    policy_temperature=1.0,
                    fit_method="grid_search",
                    fit_metric="nll",
                )
            ],
            determinism_hash="sha256:" + "0" * 64,
        )

        p_win, p_draw, p_loss = 0.4, 0.3, 0.3

        (scaled_w, scaled_d, scaled_l), metadata = apply_recalibration_to_outcome_if_enabled(
            p_win, p_draw, p_loss, "1200-1400", gate, params
        )

        assert (scaled_w, scaled_d, scaled_l) != (p_win, p_draw, p_loss)
        assert abs(scaled_w + scaled_d + scaled_l - 1.0) < 1e-6
        assert metadata.applied is True
        assert metadata.scope == "outcome"

    def test_gate_scope_outcome_only(self) -> None:
        """Gate with scope=outcome only applies to outcome probabilities."""
        gate = RecalibrationGateV1(
            version="1.0",
            enabled=True,
            parameters_ref="params.json",
            scope="outcome",
        )
        params = RecalibrationParametersV1(
            version="1.0",
            generated_at=datetime.now(UTC),
            source_calibration_metrics_hash="sha256:" + "0" * 64,
            source_manifest_hash="0" * 64,
            policy_id="baseline.uniform_random",
            by_elo_bucket=[
                RecalibrationBucketParametersV1(
                    elo_bucket="1200-1400",
                    outcome_temperature=0.5,
                    policy_temperature=2.0,  # Different temp
                    fit_method="grid_search",
                    fit_metric="nll",
                )
            ],
            determinism_hash="sha256:" + "0" * 64,
        )

        p_win, p_draw, p_loss = 0.4, 0.3, 0.3

        (scaled_w, scaled_d, scaled_l), metadata = apply_recalibration_to_outcome_if_enabled(
            p_win, p_draw, p_loss, "1200-1400", gate, params
        )

        # Should use outcome_temperature (0.5), not policy_temperature (2.0)
        assert (scaled_w, scaled_d, scaled_l) != (p_win, p_draw, p_loss)
        assert metadata.scope == "outcome"


class TestRuntimeRecalibrationMetadata:
    """Tests for RuntimeRecalibrationMetadata."""

    def test_metadata_not_applied(self) -> None:
        """Metadata for non-applied recalibration."""
        metadata = RuntimeRecalibrationMetadata(
            applied=False,
            gate_hash="sha256:abc123",
            scope=None,
        )

        assert metadata.applied is False
        assert metadata.gate_hash == "sha256:abc123"
        assert metadata.parameters_hash is None
        assert metadata.scope is None

    def test_metadata_applied(self) -> None:
        """Metadata for applied recalibration."""
        metadata = RuntimeRecalibrationMetadata(
            applied=True,
            gate_hash="sha256:abc123",
            parameters_hash="sha256:def456",
            scope="both",
        )

        assert metadata.applied is True
        assert metadata.gate_hash == "sha256:abc123"
        assert metadata.parameters_hash == "sha256:def456"
        assert metadata.scope == "both"

    def test_metadata_to_dict(self) -> None:
        """Metadata converts to dictionary."""
        metadata = RuntimeRecalibrationMetadata(
            applied=True,
            gate_hash="sha256:abc123",
            parameters_hash="sha256:def456",
            scope="policy",
        )

        d = metadata.to_dict()
        assert d == {
            "applied": True,
            "gateHash": "sha256:abc123",
            "parametersHash": "sha256:def456",
            "scope": "policy",
        }
