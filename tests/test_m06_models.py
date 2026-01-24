"""Tests for M06 Pydantic models (PositionConditioning, FrozenEvalManifest, EvalReportV3)."""

from datetime import datetime

import pytest

from renacechess.contracts.models import (
    ConditionedAccuracyMetrics,
    ConditionedMetrics,
    EvalReportV3,
    FrozenEvalManifestRecord,
    FrozenEvalManifestSourceRef,
    FrozenEvalManifestStratificationTargets,
    FrozenEvalManifestV1,
    PositionConditioning,
)


class TestPositionConditioningM06Extension:
    """Test PositionConditioning model with M06 extensions."""

    def test_position_conditioning_legacy_only(self) -> None:
        """Test that legacy fields still work without M06 fields."""
        cond = PositionConditioning(
            skill_bucket="1200-1400",
            time_pressure_bucket="NORMAL",
            time_control_class="blitz",
        )
        assert cond.skill_bucket == "1200-1400"
        assert cond.time_pressure_bucket == "NORMAL"
        assert cond.time_control_class == "blitz"
        assert cond.skill_bucket_id is None
        assert cond.skill_bucket_spec_version is None

    def test_position_conditioning_m06_fields(self) -> None:
        """Test PositionConditioning with M06-specific fields."""
        cond = PositionConditioning(
            skill_bucket="1200-1400",  # Legacy
            time_pressure_bucket="normal",  # M06 lowercase
            time_control_class="bullet",  # M06 value
            skill_bucket_id="1200_1399",  # M06 specific
            skill_bucket_spec_version=1,
            time_control_raw="180+2",
            time_control_spec_version=1,
            time_pressure_spec_version=1,
        )
        assert cond.skill_bucket == "1200-1400"
        assert cond.skill_bucket_id == "1200_1399"
        assert cond.skill_bucket_spec_version == 1
        assert cond.time_pressure_bucket == "normal"
        assert cond.time_control_class == "bullet"
        assert cond.time_control_raw == "180+2"

    def test_position_conditioning_m06_lowercase_time_pressure(self) -> None:
        """Test that M06 lowercase time pressure buckets are accepted."""
        for bucket in ["early", "normal", "low", "trouble", "unknown"]:
            cond = PositionConditioning(
                skill_bucket="test",
                time_pressure_bucket=bucket,  # type: ignore[arg-type]
            )
            assert cond.time_pressure_bucket == bucket

    def test_position_conditioning_m06_time_control_classes(self) -> None:
        """Test that M06 time control classes (bullet, unknown) are accepted."""
        for tc_class in ["bullet", "blitz", "rapid", "classical", "unknown"]:
            cond = PositionConditioning(
                skill_bucket="test",
                time_pressure_bucket="NORMAL",
                time_control_class=tc_class,  # type: ignore[arg-type]
            )
            assert cond.time_control_class == tc_class


class TestFrozenEvalManifestModels:
    """Test frozen eval manifest Pydantic models."""

    def test_frozen_eval_manifest_source_ref(self) -> None:
        """Test FrozenEvalManifestSourceRef model."""
        ref = FrozenEvalManifestSourceRef(
            dataset_digest="a" * 64,
            manifest_path="/path/to/manifest.json",
        )
        assert ref.dataset_digest == "a" * 64
        assert ref.manifest_path == "/path/to/manifest.json"

    def test_frozen_eval_manifest_record(self) -> None:
        """Test FrozenEvalManifestRecord model."""
        record = FrozenEvalManifestRecord(
            record_key="fen:123",
            shard_id="shard_000",
            shard_hash="b" * 64,
            skill_bucket_id="1200_1399",
            time_control_class="blitz",
            time_pressure_bucket="normal",
        )
        assert record.record_key == "fen:123"
        assert record.shard_id == "shard_000"
        assert record.skill_bucket_id == "1200_1399"

    def test_frozen_eval_manifest_v1(self) -> None:
        """Test FrozenEvalManifestV1 model."""
        manifest = FrozenEvalManifestV1(
            schema_version=1,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            source_manifest_ref=FrozenEvalManifestSourceRef(
                dataset_digest="a" * 64,
                manifest_path="/path/to/manifest.json",
            ),
            records=[
                FrozenEvalManifestRecord(
                    record_key="fen:1",
                    shard_id="shard_000",
                    shard_hash="b" * 64,
                    skill_bucket_id="1200_1399",
                    time_control_class="blitz",
                    time_pressure_bucket="normal",
                )
            ],
            stratification_targets=FrozenEvalManifestStratificationTargets(
                total_records=10000,
                min_per_skill_bucket=500,
            ),
            counts_by_skill_bucket_id={"1200_1399": 1},
            counts_by_time_control_class={"blitz": 1},
            counts_by_time_pressure_bucket={"normal": 1},
            manifest_hash="c" * 64,
        )
        assert manifest.schema_version == 1
        assert len(manifest.records) == 1
        assert manifest.stratification_targets.total_records == 10000


class TestEvalReportV3Models:
    """Test EvalReportV3 Pydantic models."""

    def test_conditioned_accuracy_metrics(self) -> None:
        """Test ConditionedAccuracyMetrics model."""
        metrics = ConditionedAccuracyMetrics(
            top1="0.500000",
            top_k={"3": "0.750000", "5": "0.850000"},
            coverage="0.950000",
        )
        assert metrics.top1 == "0.500000"
        assert metrics.top_k["3"] == "0.750000"
        assert metrics.coverage == "0.950000"

    def test_conditioned_metrics(self) -> None:
        """Test ConditionedMetrics model."""
        metrics = ConditionedMetrics(
            total_records=1000,
            labeled_records=950,
            records_with_policy=1000,
            accuracy=ConditionedAccuracyMetrics(
                top1="0.500000",
                top_k={"3": "0.750000"},
                coverage="0.950000",
            ),
        )
        assert metrics.total_records == 1000
        assert metrics.labeled_records == 950
        assert metrics.accuracy.top1 == "0.500000"

    def test_eval_report_v3_minimal(self) -> None:
        """Test EvalReportV3 model with minimal fields."""
        report = EvalReportV3(
            schema_version="eval_report.v3",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            dataset_digest="a" * 64,
            assembly_config_hash="b" * 64,
            policy_id="baseline.uniform_random",
            eval_config_hash="c" * 64,
            overall=ConditionedMetrics(
                total_records=1000,
                labeled_records=950,
                records_with_policy=1000,
            ),
        )
        assert report.schema_version == "eval_report.v3"
        assert report.policy_id == "baseline.uniform_random"
        assert report.overall.total_records == 1000

    def test_eval_report_v3_with_stratification(self) -> None:
        """Test EvalReportV3 model with stratified metrics."""
        overall_metrics = ConditionedMetrics(
            total_records=1000,
            labeled_records=950,
            records_with_policy=1000,
        )
        skill_metrics = {
            "1200_1399": ConditionedMetrics(
                total_records=500,
                labeled_records=475,
                records_with_policy=500,
            ),
            "1400_1599": ConditionedMetrics(
                total_records=500,
                labeled_records=475,
                records_with_policy=500,
            ),
        }

        report = EvalReportV3(
            schema_version="eval_report.v3",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            dataset_digest="a" * 64,
            assembly_config_hash="b" * 64,
            policy_id="baseline.uniform_random",
            eval_config_hash="c" * 64,
            overall=overall_metrics,
            by_skill_bucket_id=skill_metrics,
        )
        assert len(report.by_skill_bucket_id) == 2
        assert report.by_skill_bucket_id["1200_1399"].total_records == 500
