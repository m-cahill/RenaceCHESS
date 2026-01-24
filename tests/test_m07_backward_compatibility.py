"""Tests for M07 backward compatibility (v3 reports still validate)."""

from datetime import datetime

import pytest

from renacechess.contracts.models import (
    ConditionedAccuracyMetrics,
    ConditionedDistributionMetrics,
    ConditionedMetrics,
    ConditionedValidityMetrics,
    DistributionStats,
    EvalReportV3,
    EvalReportV4,
)


class TestV3BackwardCompatibility:
    """Test that v3 reports remain valid after M07 changes."""

    def test_eval_report_v3_without_hdi(self) -> None:
        """Test that EvalReportV3 can be created without HDI (backward compatible)."""
        # Create minimal v3 report (no HDI)
        overall = ConditionedMetrics(
            total_records=100,
            labeled_records=50,
            records_with_policy=100,
            accuracy=ConditionedAccuracyMetrics(
                top1="50.000000",
                top_k={"3": "60.000000"},
                coverage="50.000000",
            ),
            distribution=ConditionedDistributionMetrics(
                entropy=DistributionStats(mean="3.500000"),
                top_gap=DistributionStats(mean="0.200000"),
                legal_moves_count=DistributionStats(mean="20.000000"),
            ),
            validity=ConditionedValidityMetrics(
                illegal_rate="0.000000",
                unique_moves_emitted=10,
            ),
            hdi=None,  # v3 doesn't require HDI
        )

        report = EvalReportV3(
            schema_version="eval_report.v3",
            created_at=datetime.now(),
            dataset_digest="a" * 64,
            assembly_config_hash="b" * 64,
            policy_id="baseline.uniform_random",
            eval_config_hash="c" * 64,
            frozen_eval_manifest_hash=None,
            overall=overall,
            by_skill_bucket_id={},
            by_time_control_class={},
            by_time_pressure_bucket={},
        )

        assert report.schema_version == "eval_report.v3"
        assert report.overall.hdi is None

    def test_eval_report_v3_serialization(self) -> None:
        """Test that v3 reports serialize correctly."""
        overall = ConditionedMetrics(
            total_records=100,
            labeled_records=50,
            records_with_policy=100,
            hdi=None,  # No HDI in v3
        )

        report = EvalReportV3(
            schema_version="eval_report.v3",
            created_at=datetime.now(),
            dataset_digest="a" * 64,
            assembly_config_hash="b" * 64,
            policy_id="baseline.uniform_random",
            eval_config_hash="c" * 64,
            overall=overall,
        )

        # Serialize to dict
        report_dict = report.model_dump(mode="json", by_alias=True)
        assert report_dict["schemaVersion"] == "eval_report.v3"
        assert "hdi" not in report_dict["overall"] or report_dict["overall"]["hdi"] is None

        # Deserialize back
        report_loaded = EvalReportV3.model_validate(report_dict)
        assert report_loaded.schema_version == "eval_report.v3"
        assert report_loaded.overall.hdi is None


class TestV4ExtendsV3:
    """Test that v4 extends v3 correctly."""

    def test_eval_report_v4_with_hdi(self) -> None:
        """Test that EvalReportV4 includes HDI."""
        from renacechess.contracts.models import (
            HDIMetrics,
            HDIMetricsComponents,
            HDIOutcomeSensitivity,
        )

        hdi = HDIMetrics(
            value=0.73,
            spec_version=1,
            components=HDIMetricsComponents(
                entropy=0.82,
                top_gap_inverted=0.41,
                legal_move_pressure=0.67,
                outcome_sensitivity=HDIOutcomeSensitivity(
                    value=0.55,
                    source="proxy",
                    note="entropy * (1 - topGap); replaced when outcome head exists",
                ),
            ),
        )

        overall = ConditionedMetrics(
            total_records=100,
            labeled_records=50,
            records_with_policy=100,
            hdi=hdi,
        )

        report = EvalReportV4(
            schema_version="eval_report.v4",
            created_at=datetime.now(),
            dataset_digest="a" * 64,
            assembly_config_hash="b" * 64,
            policy_id="baseline.uniform_random",
            eval_config_hash="c" * 64,
            overall=overall,
        )

        assert report.schema_version == "eval_report.v4"
        assert report.overall.hdi is not None
        assert report.overall.hdi.value == 0.73
        assert report.overall.hdi.spec_version == 1

    def test_eval_report_v4_serialization(self) -> None:
        """Test that v4 reports serialize correctly."""
        from renacechess.contracts.models import (
            HDIMetrics,
            HDIMetricsComponents,
            HDIOutcomeSensitivity,
        )

        hdi = HDIMetrics(
            value=0.73,
            spec_version=1,
            components=HDIMetricsComponents(
                entropy=0.82,
                top_gap_inverted=0.41,
                legal_move_pressure=0.67,
                outcome_sensitivity=HDIOutcomeSensitivity(
                    value=0.55,
                    source="proxy",
                    note="entropy * (1 - topGap); replaced when outcome head exists",
                ),
            ),
        )

        overall = ConditionedMetrics(
            total_records=100,
            labeled_records=50,
            records_with_policy=100,
            hdi=hdi,
        )

        report = EvalReportV4(
            schema_version="eval_report.v4",
            created_at=datetime.now(),
            dataset_digest="a" * 64,
            assembly_config_hash="b" * 64,
            policy_id="baseline.uniform_random",
            eval_config_hash="c" * 64,
            overall=overall,
        )

        # Serialize to dict
        report_dict = report.model_dump(mode="json", by_alias=True)
        assert report_dict["schemaVersion"] == "eval_report.v4"
        assert "hdi" in report_dict["overall"]
        assert report_dict["overall"]["hdi"]["value"] == 0.73

        # Deserialize back
        report_loaded = EvalReportV4.model_validate(report_dict)
        assert report_loaded.schema_version == "eval_report.v4"
        assert report_loaded.overall.hdi is not None
        assert report_loaded.overall.hdi.value == 0.73
