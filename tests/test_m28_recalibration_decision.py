"""Comprehensive test suite for M28 Runtime Recalibration Decision.

This module tests the decision framework for runtime recalibration activation:
- RuntimeRecalibrationActivationPolicyV1 schema/model
- RuntimeRecalibrationDecisionV1 schema/model
- Decision runner functionality
- CLI integration
- Determinism and validation

Per M28 locked decisions:
- M28 produces the decision framework, not hard-codes the final decision
- The actual decision value comes via a policy artifact
- Only per-Elo bucket and per-scope (policy/outcome/both) granularity
- Default policy is conservative: all buckets disabled
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from renacechess.contracts.models import (
    BucketActivationOverrideV1,
    BucketDecisionV1,
    RuntimeRecalibrationActivationPolicyV1,
    RuntimeRecalibrationDecisionV1,
    RuntimeRecalibrationDeltaV1,
    RuntimeRecalibrationReportV1,
    ValidationCheckV1,
    ValidationResultV1,
)
from renacechess.eval.recalibration_decision_runner import (
    CANONICAL_ELO_BUCKETS,
    _compute_bucket_decision,
    _determine_decision_outcome,
    _generate_human_summary,
    _validate_policy_against_evidence,
    create_conservative_policy,
    load_activation_policy,
    load_runtime_recalibration_delta,
    load_runtime_recalibration_report,
    run_recalibration_decision,
    save_decision,
    save_policy,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_report_data() -> dict[str, Any]:
    """Create sample RuntimeRecalibrationReportV1 data."""
    return {
        "version": "1.0",
        "generatedAt": "2026-02-02T10:00:00Z",
        "gateRef": "sha256:" + "a" * 64,
        "parametersRef": "sha256:" + "b" * 64,
        "datasetRef": "c" * 64,
        "totalSamples": 100,
        "baselineMetrics": {
            "outcomeEce": 0.15,
            "outcomeNll": 0.8,
            "outcomeBrier": 0.2,
            "policyNll": 2.5,
            "policyTop1Ece": 0.1,
            "meanEntropy": 2.0,
        },
        "recalibratedMetrics": {
            "outcomeEce": 0.12,
            "outcomeNll": 0.75,
            "outcomeBrier": 0.18,
            "policyNll": 2.4,
            "policyTop1Ece": 0.08,
            "meanEntropy": 2.1,
        },
        "determinismHash": "sha256:" + "d" * 64,
    }


@pytest.fixture
def sample_delta_data() -> dict[str, Any]:
    """Create sample RuntimeRecalibrationDeltaV1 data."""
    return {
        "version": "1.0",
        "generatedAt": "2026-02-02T10:01:00Z",
        "sourceReportHash": "sha256:" + "d" * 64,
        "byEloBucket": [
            {
                "bucketId": "1200_1399",
                "samples": 50,
                "metrics": {
                    "outcomeEceDelta": -0.03,
                    "outcomeNllDelta": -0.05,
                    "outcomeBrierDelta": -0.02,
                    "policyNllDelta": -0.1,
                    "policyTop1EceDelta": -0.02,
                    "entropyDelta": 0.1,
                    "top1Stability": 0.95,
                    "top3Stability": 0.98,
                    "top1FlipRate": 0.05,
                },
            },
            {
                "bucketId": "1400_1599",
                "samples": 50,
                "metrics": {
                    "outcomeEceDelta": 0.01,
                    "outcomeNllDelta": 0.02,
                    "outcomeBrierDelta": 0.01,
                    "policyNllDelta": 0.05,
                    "policyTop1EceDelta": 0.01,
                    "entropyDelta": -0.05,
                    "top1Stability": 0.90,
                    "top3Stability": 0.95,
                    "top1FlipRate": 0.10,
                },
            },
        ],
        "byTimePressureBucket": None,
        "overall": {
            "outcomeEceDelta": -0.01,
            "outcomeNllDelta": -0.015,
            "outcomeBrierDelta": -0.005,
            "policyNllDelta": -0.025,
            "policyTop1EceDelta": -0.005,
            "entropyDelta": 0.025,
            "top1Stability": 0.925,
            "top3Stability": 0.965,
            "top1FlipRate": 0.075,
        },
        "determinismHash": "sha256:" + "e" * 64,
    }


@pytest.fixture
def conservative_policy_data() -> dict[str, Any]:
    """Create conservative policy data (all disabled)."""
    return {
        "version": "1.0",
        "defaultEnabled": False,
        "scope": "both",
        "bucketOverrides": [],
        "createdAt": "2026-02-02T10:00:00Z",
        "notes": "Conservative default policy: all buckets disabled",
    }


@pytest.fixture
def activated_policy_data() -> dict[str, Any]:
    """Create activated policy data (all enabled)."""
    return {
        "version": "1.0",
        "defaultEnabled": True,
        "scope": "both",
        "bucketOverrides": [],
        "createdAt": "2026-02-02T10:00:00Z",
        "notes": "Activated policy: all buckets enabled",
    }


@pytest.fixture
def restricted_policy_data() -> dict[str, Any]:
    """Create restricted policy data (some enabled)."""
    return {
        "version": "1.0",
        "defaultEnabled": False,
        "scope": "outcome",
        "bucketOverrides": [
            {
                "bucketId": "1200_1399",
                "enabled": True,
                "scope": None,
                "reason": "Good calibration improvement in M27",
            },
            {
                "bucketId": "1400_1599",
                "enabled": True,
                "scope": "policy",
                "reason": "Policy-only enabled per testing",
            },
        ],
        "createdAt": "2026-02-02T10:00:00Z",
        "notes": "Restricted policy: only specific buckets enabled",
    }


@pytest.fixture
def temp_artifacts(
    tmp_path: Path,
    sample_report_data: dict[str, Any],
    sample_delta_data: dict[str, Any],
    conservative_policy_data: dict[str, Any],
) -> tuple[Path, Path, Path]:
    """Create temporary artifact files."""
    report_path = tmp_path / "report.json"
    delta_path = tmp_path / "delta.json"
    policy_path = tmp_path / "policy.json"

    report_path.write_text(json.dumps(sample_report_data), encoding="utf-8")
    delta_path.write_text(json.dumps(sample_delta_data), encoding="utf-8")
    policy_path.write_text(json.dumps(conservative_policy_data), encoding="utf-8")

    return report_path, delta_path, policy_path


# =============================================================================
# Schema/Model Tests
# =============================================================================


class TestRuntimeRecalibrationActivationPolicyV1:
    """Tests for RuntimeRecalibrationActivationPolicyV1 model."""

    def test_minimal_policy(self) -> None:
        """Test minimal policy with required fields only."""
        policy = RuntimeRecalibrationActivationPolicyV1(
            version="1.0",
            default_enabled=False,
            bucket_overrides=[],
        )
        assert policy.version == "1.0"
        assert policy.default_enabled is False
        assert policy.scope == "both"  # default
        assert policy.bucket_overrides == []

    def test_full_policy(self) -> None:
        """Test policy with all fields."""
        now = datetime.now(UTC)
        policy = RuntimeRecalibrationActivationPolicyV1(
            version="1.0",
            default_enabled=True,
            scope="outcome",
            bucket_overrides=[
                BucketActivationOverrideV1(
                    bucket_id="1200_1399",
                    enabled=False,
                    scope="policy",
                    reason="Test override",
                )
            ],
            created_at=now,
            notes="Test policy",
        )
        assert policy.default_enabled is True
        assert policy.scope == "outcome"
        assert len(policy.bucket_overrides) == 1
        assert policy.bucket_overrides[0].bucket_id == "1200_1399"
        assert policy.created_at == now
        assert policy.notes == "Test policy"

    def test_json_serialization(self, conservative_policy_data: dict[str, Any]) -> None:
        """Test JSON serialization with aliases."""
        policy = RuntimeRecalibrationActivationPolicyV1.model_validate(conservative_policy_data)
        dumped = policy.model_dump(by_alias=True, mode="json")
        assert "defaultEnabled" in dumped
        assert "bucketOverrides" in dumped
        assert dumped["defaultEnabled"] is False


class TestRuntimeRecalibrationDecisionV1:
    """Tests for RuntimeRecalibrationDecisionV1 model."""

    def test_minimal_decision(self) -> None:
        """Test minimal decision with required fields."""
        now = datetime.now(UTC)
        decision = RuntimeRecalibrationDecisionV1(
            version="1.0",
            generated_at=now,
            decision_outcome="rejected",
            source_report_hash="sha256:" + "a" * 64,
            source_delta_hash="sha256:" + "b" * 64,
            policy_hash="sha256:" + "c" * 64,
            activated_bucket_count=0,
            total_bucket_count=8,
            bucket_decisions=[
                BucketDecisionV1(
                    bucket_id="lt_800",
                    enabled=False,
                    scope="none",
                )
            ],
            validation_result=ValidationResultV1(
                valid=True,
                checks=[
                    ValidationCheckV1(check_name="test", passed=True),
                ],
            ),
            human_summary="Test summary",
            determinism_hash="sha256:" + "d" * 64,
        )
        assert decision.decision_outcome == "rejected"
        assert decision.activated_bucket_count == 0

    def test_json_serialization(self) -> None:
        """Test JSON serialization with aliases."""
        now = datetime.now(UTC)
        decision = RuntimeRecalibrationDecisionV1(
            version="1.0",
            generated_at=now,
            decision_outcome="activated",
            source_report_hash="sha256:" + "a" * 64,
            source_delta_hash="sha256:" + "b" * 64,
            policy_hash="sha256:" + "c" * 64,
            activated_bucket_count=8,
            total_bucket_count=8,
            bucket_decisions=[],
            validation_result=ValidationResultV1(valid=True, checks=[]),
            human_summary="All activated",
            determinism_hash="sha256:" + "d" * 64,
        )
        dumped = decision.model_dump(by_alias=True, mode="json")
        assert "decisionOutcome" in dumped
        assert "sourceReportHash" in dumped
        assert "bucketDecisions" in dumped


# =============================================================================
# Decision Runner Unit Tests
# =============================================================================


class TestConservativePolicy:
    """Tests for conservative policy creation."""

    def test_create_conservative_policy(self) -> None:
        """Test that conservative policy has all correct defaults."""
        policy = create_conservative_policy()
        assert policy.version == "1.0"
        assert policy.default_enabled is False
        assert policy.scope == "both"
        assert policy.bucket_overrides == []
        assert policy.notes is not None
        assert "conservative" in policy.notes.lower()


class TestLoadFunctions:
    """Tests for artifact loading functions."""

    def test_load_report(self, tmp_path: Path, sample_report_data: dict[str, Any]) -> None:
        """Test loading report artifact."""
        path = tmp_path / "report.json"
        path.write_text(json.dumps(sample_report_data), encoding="utf-8")

        report = load_runtime_recalibration_report(path)
        assert report.version == "1.0"
        assert report.total_samples == 100

    def test_load_report_not_found(self, tmp_path: Path) -> None:
        """Test error on missing report file."""
        with pytest.raises(FileNotFoundError):
            load_runtime_recalibration_report(tmp_path / "missing.json")

    def test_load_delta(self, tmp_path: Path, sample_delta_data: dict[str, Any]) -> None:
        """Test loading delta artifact."""
        path = tmp_path / "delta.json"
        path.write_text(json.dumps(sample_delta_data), encoding="utf-8")

        delta = load_runtime_recalibration_delta(path)
        assert delta.version == "1.0"
        assert len(delta.by_elo_bucket) == 2

    def test_load_policy(self, tmp_path: Path, conservative_policy_data: dict[str, Any]) -> None:
        """Test loading policy artifact."""
        path = tmp_path / "policy.json"
        path.write_text(json.dumps(conservative_policy_data), encoding="utf-8")

        policy = load_activation_policy(path)
        assert policy.default_enabled is False


class TestValidation:
    """Tests for policy validation."""

    def test_valid_policy(
        self,
        sample_report_data: dict[str, Any],
        sample_delta_data: dict[str, Any],
        conservative_policy_data: dict[str, Any],
    ) -> None:
        """Test validation of valid policy."""
        report = RuntimeRecalibrationReportV1.model_validate(sample_report_data)
        delta = RuntimeRecalibrationDeltaV1.model_validate(sample_delta_data)
        policy = RuntimeRecalibrationActivationPolicyV1.model_validate(conservative_policy_data)

        result = _validate_policy_against_evidence(policy, report, delta)
        assert result.valid is True
        assert len(result.checks) >= 4
        assert all(c.passed for c in result.checks)

    def test_invalid_bucket_id(
        self,
        sample_report_data: dict[str, Any],
        sample_delta_data: dict[str, Any],
    ) -> None:
        """Test validation fails for invalid bucket ID."""
        report = RuntimeRecalibrationReportV1.model_validate(sample_report_data)
        delta = RuntimeRecalibrationDeltaV1.model_validate(sample_delta_data)
        policy = RuntimeRecalibrationActivationPolicyV1(
            version="1.0",
            default_enabled=False,
            bucket_overrides=[
                BucketActivationOverrideV1(
                    bucket_id="invalid_bucket",
                    enabled=True,
                )
            ],
        )

        result = _validate_policy_against_evidence(policy, report, delta)
        assert result.valid is False
        assert result.errors is not None
        assert any("invalid" in e.lower() for e in result.errors)


class TestBucketDecision:
    """Tests for bucket decision computation."""

    def test_default_disabled(
        self,
        sample_delta_data: dict[str, Any],
        conservative_policy_data: dict[str, Any],
    ) -> None:
        """Test bucket decision with default disabled policy."""
        delta = RuntimeRecalibrationDeltaV1.model_validate(sample_delta_data)
        policy = RuntimeRecalibrationActivationPolicyV1.model_validate(conservative_policy_data)

        decision = _compute_bucket_decision("1200_1399", policy, delta)
        assert decision.enabled is False
        assert decision.scope == "none"
        assert decision.evidence_summary is not None

    def test_default_enabled(
        self,
        sample_delta_data: dict[str, Any],
        activated_policy_data: dict[str, Any],
    ) -> None:
        """Test bucket decision with default enabled policy."""
        delta = RuntimeRecalibrationDeltaV1.model_validate(sample_delta_data)
        policy = RuntimeRecalibrationActivationPolicyV1.model_validate(activated_policy_data)

        decision = _compute_bucket_decision("1200_1399", policy, delta)
        assert decision.enabled is True
        assert decision.scope == "both"

    def test_override_enabled(
        self,
        sample_delta_data: dict[str, Any],
        restricted_policy_data: dict[str, Any],
    ) -> None:
        """Test bucket decision with override enabled."""
        delta = RuntimeRecalibrationDeltaV1.model_validate(sample_delta_data)
        policy = RuntimeRecalibrationActivationPolicyV1.model_validate(restricted_policy_data)

        decision = _compute_bucket_decision("1200_1399", policy, delta)
        assert decision.enabled is True
        assert decision.scope == "outcome"  # Uses policy default since override scope is None
        assert decision.policy_reason is not None

    def test_override_with_scope(
        self,
        sample_delta_data: dict[str, Any],
        restricted_policy_data: dict[str, Any],
    ) -> None:
        """Test bucket decision with override scope."""
        delta = RuntimeRecalibrationDeltaV1.model_validate(sample_delta_data)
        policy = RuntimeRecalibrationActivationPolicyV1.model_validate(restricted_policy_data)

        decision = _compute_bucket_decision("1400_1599", policy, delta)
        assert decision.enabled is True
        assert decision.scope == "policy"  # Uses override scope

    def test_missing_bucket_in_delta(
        self,
        sample_delta_data: dict[str, Any],
        conservative_policy_data: dict[str, Any],
    ) -> None:
        """Test bucket decision for bucket not in delta."""
        delta = RuntimeRecalibrationDeltaV1.model_validate(sample_delta_data)
        policy = RuntimeRecalibrationActivationPolicyV1.model_validate(conservative_policy_data)

        decision = _compute_bucket_decision("lt_800", policy, delta)
        assert decision.evidence_summary is not None
        assert "no m27 data" in decision.evidence_summary.lower()


class TestDecisionOutcome:
    """Tests for decision outcome determination."""

    def test_rejected(self) -> None:
        """Test rejected outcome when no buckets enabled."""
        decisions = [
            BucketDecisionV1(bucket_id="lt_800", enabled=False, scope="none"),
            BucketDecisionV1(bucket_id="800_999", enabled=False, scope="none"),
        ]
        assert _determine_decision_outcome(decisions) == "rejected"

    def test_activated(self) -> None:
        """Test activated outcome when all buckets enabled."""
        decisions = [
            BucketDecisionV1(bucket_id="lt_800", enabled=True, scope="both"),
            BucketDecisionV1(bucket_id="800_999", enabled=True, scope="both"),
        ]
        assert _determine_decision_outcome(decisions) == "activated"

    def test_restricted(self) -> None:
        """Test restricted outcome when some buckets enabled."""
        decisions = [
            BucketDecisionV1(bucket_id="lt_800", enabled=True, scope="both"),
            BucketDecisionV1(bucket_id="800_999", enabled=False, scope="none"),
        ]
        assert _determine_decision_outcome(decisions) == "restricted"


class TestHumanSummary:
    """Tests for human summary generation."""

    def test_rejected_summary(self) -> None:
        """Test summary for rejected outcome."""
        policy = create_conservative_policy()
        summary = _generate_human_summary("rejected", 0, 8, policy)
        assert "REJECTED" in summary
        assert "unchanged" in summary.lower()

    def test_activated_summary(self) -> None:
        """Test summary for activated outcome."""
        policy = RuntimeRecalibrationActivationPolicyV1(
            version="1.0",
            default_enabled=True,
            scope="outcome",
            bucket_overrides=[],
        )
        summary = _generate_human_summary("activated", 8, 8, policy)
        assert "ACTIVATED" in summary
        assert "outcome" in summary.lower()

    def test_restricted_summary(self) -> None:
        """Test summary for restricted outcome."""
        policy = create_conservative_policy()
        summary = _generate_human_summary("restricted", 3, 8, policy)
        assert "RESTRICTED" in summary
        assert "3/8" in summary


# =============================================================================
# Integration Tests
# =============================================================================


class TestRunRecalibrationDecision:
    """Integration tests for run_recalibration_decision."""

    def test_conservative_policy_yields_rejected(
        self, temp_artifacts: tuple[Path, Path, Path]
    ) -> None:
        """Test conservative policy yields rejected decision."""
        report_path, delta_path, policy_path = temp_artifacts

        decision = run_recalibration_decision(report_path, delta_path, policy_path)

        assert decision.version == "1.0"
        assert decision.decision_outcome == "rejected"
        assert decision.activated_bucket_count == 0
        assert decision.total_bucket_count == len(CANONICAL_ELO_BUCKETS)
        assert decision.validation_result.valid is True

    def test_activated_policy_yields_activated(
        self,
        tmp_path: Path,
        sample_report_data: dict[str, Any],
        sample_delta_data: dict[str, Any],
        activated_policy_data: dict[str, Any],
    ) -> None:
        """Test activated policy yields activated decision."""
        report_path = tmp_path / "report.json"
        delta_path = tmp_path / "delta.json"
        policy_path = tmp_path / "policy.json"

        report_path.write_text(json.dumps(sample_report_data), encoding="utf-8")
        delta_path.write_text(json.dumps(sample_delta_data), encoding="utf-8")
        policy_path.write_text(json.dumps(activated_policy_data), encoding="utf-8")

        decision = run_recalibration_decision(report_path, delta_path, policy_path)

        assert decision.decision_outcome == "activated"
        assert decision.activated_bucket_count == len(CANONICAL_ELO_BUCKETS)

    def test_restricted_policy_yields_restricted(
        self,
        tmp_path: Path,
        sample_report_data: dict[str, Any],
        sample_delta_data: dict[str, Any],
        restricted_policy_data: dict[str, Any],
    ) -> None:
        """Test restricted policy yields restricted decision."""
        report_path = tmp_path / "report.json"
        delta_path = tmp_path / "delta.json"
        policy_path = tmp_path / "policy.json"

        report_path.write_text(json.dumps(sample_report_data), encoding="utf-8")
        delta_path.write_text(json.dumps(sample_delta_data), encoding="utf-8")
        policy_path.write_text(json.dumps(restricted_policy_data), encoding="utf-8")

        decision = run_recalibration_decision(report_path, delta_path, policy_path)

        assert decision.decision_outcome == "restricted"
        assert 0 < decision.activated_bucket_count < decision.total_bucket_count

    def test_determinism(self, temp_artifacts: tuple[Path, Path, Path]) -> None:
        """Test that decision is deterministic across runs."""
        report_path, delta_path, policy_path = temp_artifacts

        decision1 = run_recalibration_decision(report_path, delta_path, policy_path)
        decision2 = run_recalibration_decision(report_path, delta_path, policy_path)

        # Determinism hashes should match
        assert decision1.determinism_hash == decision2.determinism_hash

    def test_validation_failure_raises(
        self,
        tmp_path: Path,
        sample_report_data: dict[str, Any],
        sample_delta_data: dict[str, Any],
    ) -> None:
        """Test that validation failure raises ValueError."""
        report_path = tmp_path / "report.json"
        delta_path = tmp_path / "delta.json"
        policy_path = tmp_path / "policy.json"

        report_path.write_text(json.dumps(sample_report_data), encoding="utf-8")
        delta_path.write_text(json.dumps(sample_delta_data), encoding="utf-8")

        # Policy with invalid bucket ID
        invalid_policy = {
            "version": "1.0",
            "defaultEnabled": False,
            "bucketOverrides": [{"bucketId": "invalid_bucket_123", "enabled": True}],
        }
        policy_path.write_text(json.dumps(invalid_policy), encoding="utf-8")

        with pytest.raises(ValueError, match="validation failed"):
            run_recalibration_decision(report_path, delta_path, policy_path)


class TestSaveFunctions:
    """Tests for save functions."""

    def test_save_decision(self, tmp_path: Path, temp_artifacts: tuple[Path, Path, Path]) -> None:
        """Test saving decision artifact."""
        report_path, delta_path, policy_path = temp_artifacts
        decision = run_recalibration_decision(report_path, delta_path, policy_path)

        out_path = tmp_path / "decision.json"
        save_decision(decision, out_path)

        assert out_path.exists()
        loaded = json.loads(out_path.read_text(encoding="utf-8"))
        assert loaded["decisionOutcome"] == "rejected"

    def test_save_policy(self, tmp_path: Path) -> None:
        """Test saving policy artifact."""
        policy = create_conservative_policy()
        out_path = tmp_path / "policy.json"
        save_policy(policy, out_path)

        assert out_path.exists()
        loaded = json.loads(out_path.read_text(encoding="utf-8"))
        assert loaded["defaultEnabled"] is False


# =============================================================================
# CLI Integration Tests
# =============================================================================


class TestCLIIntegration:
    """CLI integration tests for M28 command."""

    def test_cli_decision_command_success(
        self, tmp_path: Path, temp_artifacts: tuple[Path, Path, Path]
    ) -> None:
        """Test CLI decision command succeeds."""
        import sys
        from io import StringIO

        from renacechess.cli import main

        report_path, delta_path, policy_path = temp_artifacts
        out_path = tmp_path / "decision_out.json"

        with mock.patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "eval",
                "runtime-recalibration-decision",
                "--report",
                str(report_path),
                "--delta",
                str(delta_path),
                "--policy",
                str(policy_path),
                "--out",
                str(out_path),
            ],
        ):
            with mock.patch("sys.stderr", new=StringIO()) as mock_stderr:
                main()

        assert out_path.exists()
        stderr_output = mock_stderr.getvalue()
        assert "REJECTED" in stderr_output

    def test_cli_decision_command_missing_report(
        self, tmp_path: Path, temp_artifacts: tuple[Path, Path, Path]
    ) -> None:
        """Test CLI decision command fails for missing report."""
        import sys

        from renacechess.cli import main

        _, delta_path, policy_path = temp_artifacts
        out_path = tmp_path / "decision_out.json"

        with mock.patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "eval",
                "runtime-recalibration-decision",
                "--report",
                str(tmp_path / "missing.json"),
                "--delta",
                str(delta_path),
                "--policy",
                str(policy_path),
                "--out",
                str(out_path),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_cli_decision_command_missing_delta(
        self, tmp_path: Path, temp_artifacts: tuple[Path, Path, Path]
    ) -> None:
        """Test CLI decision command fails for missing delta."""
        import sys

        from renacechess.cli import main

        report_path, _, policy_path = temp_artifacts
        out_path = tmp_path / "decision_out.json"

        with mock.patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "eval",
                "runtime-recalibration-decision",
                "--report",
                str(report_path),
                "--delta",
                str(tmp_path / "missing.json"),
                "--policy",
                str(policy_path),
                "--out",
                str(out_path),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_cli_decision_command_missing_policy(
        self, tmp_path: Path, temp_artifacts: tuple[Path, Path, Path]
    ) -> None:
        """Test CLI decision command fails for missing policy."""
        import sys

        from renacechess.cli import main

        report_path, delta_path, _ = temp_artifacts
        out_path = tmp_path / "decision_out.json"

        with mock.patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "eval",
                "runtime-recalibration-decision",
                "--report",
                str(report_path),
                "--delta",
                str(delta_path),
                "--policy",
                str(tmp_path / "missing.json"),
                "--out",
                str(out_path),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1


# =============================================================================
# Canonical Bucket Tests
# =============================================================================


class TestCanonicalBuckets:
    """Tests for canonical bucket handling."""

    def test_all_canonical_buckets_covered(self, temp_artifacts: tuple[Path, Path, Path]) -> None:
        """Test that all canonical buckets are included in decision."""
        report_path, delta_path, policy_path = temp_artifacts
        decision = run_recalibration_decision(report_path, delta_path, policy_path)

        bucket_ids = {bd.bucket_id for bd in decision.bucket_decisions}
        expected = set(CANONICAL_ELO_BUCKETS)
        assert bucket_ids == expected

    def test_canonical_buckets_match_m06(self) -> None:
        """Test that canonical buckets match M06 specification."""
        # Get all valid skill bucket IDs from the type
        import typing

        from renacechess.conditioning.buckets import SkillBucketId

        skill_buckets = typing.get_args(SkillBucketId)
        assert set(CANONICAL_ELO_BUCKETS) == set(skill_buckets)
