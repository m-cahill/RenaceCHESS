"""Tests for evaluation report v2 schema and models (M05)."""

import json
from datetime import datetime
from pathlib import Path

import jsonschema

from renacechess.contracts.models import (
    AccuracyMetrics,
    EvalMetricsV1,
    EvalMetricsV2,
    EvalReportV2,
    PolicyEntropyStats,
    TopKLegalCoverage,
)


def load_schema(schema_name: str) -> dict:
    """Load JSON schema from schemas directory."""
    schema_path = (
        Path(__file__).parent.parent
        / "src"
        / "renacechess"
        / "contracts"
        / "schemas"
        / "v1"
        / f"{schema_name}.schema.json"
    )
    return json.loads(schema_path.read_text())


def test_accuracy_metrics_model() -> None:
    """Test AccuracyMetrics model."""
    # With coverage only
    accuracy = AccuracyMetrics(coverage="81.0000")
    assert accuracy.coverage == "81.0000"

    # With dynamic top-K fields
    accuracy_dict = {"coverage": "81.0000", "top1": "42.0000", "top3": "67.0000"}
    accuracy = AccuracyMetrics(**accuracy_dict)
    assert accuracy.coverage == "81.0000"
    # Dynamic fields are stored via model_extra
    assert hasattr(accuracy, "top1") or "top1" in accuracy.model_dump()


def test_eval_metrics_v2_model() -> None:
    """Test EvalMetricsV2 model."""
    metrics = EvalMetricsV2(
        records_evaluated=100,
        illegal_move_rate="0.0000",
        top_k_legal_coverage=TopKLegalCoverage(top1="100.0000", top3="100.0000"),
        policy_entropy=PolicyEntropyStats(mean="3.5000"),
        unique_moves_emitted=50,
        total_record_count=100,
        labeled_record_count=81,
        accuracy=AccuracyMetrics(coverage="81.0000", top1="42.0000", top3="67.0000"),
    )

    assert metrics.total_record_count == 100
    assert metrics.labeled_record_count == 81
    assert metrics.accuracy is not None
    assert metrics.accuracy.coverage == "81.0000"


def test_eval_report_v2_model() -> None:
    """Test EvalReportV2 model."""
    report = EvalReportV2(
        schema_version="eval_report.v2",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        dataset_digest="a" * 64,
        assembly_config_hash="b" * 64,
        policy_id="baseline.first_legal",
        eval_config_hash="c" * 64,
        metrics=EvalMetricsV1(
            records_evaluated=100,
            illegal_move_rate="0.0000",
            top_k_legal_coverage=TopKLegalCoverage(top1="100.0000", top3="100.0000"),
            policy_entropy=PolicyEntropyStats(mean="3.5000"),
            unique_moves_emitted=50,
        ),
        total_record_count=100,
        labeled_record_count=81,
        accuracy=AccuracyMetrics(coverage="81.0000", top1="42.0000", top3="67.0000"),
    )

    assert report.schema_version == "eval_report.v2"
    assert report.total_record_count == 100
    assert report.labeled_record_count == 81
    assert report.accuracy is not None


def test_eval_report_v2_schema_validation() -> None:
    """Test that EvalReportV2 validates against schema."""
    report = EvalReportV2(
        schema_version="eval_report.v2",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        dataset_digest="a" * 64,
        assembly_config_hash="b" * 64,
        policy_id="baseline.first_legal",
        eval_config_hash="c" * 64,
        metrics=EvalMetricsV1(
            records_evaluated=100,
            illegal_move_rate="0.0000",
            top_k_legal_coverage=TopKLegalCoverage(top1="100.0000", top3="100.0000"),
            policy_entropy=PolicyEntropyStats(mean="3.5000"),
            unique_moves_emitted=50,
        ),
        total_record_count=100,
        labeled_record_count=81,
        accuracy=AccuracyMetrics(coverage="81.0000", top1="42.0000", top3="67.0000"),
    )

    report_dict = report.model_dump(mode="json", by_alias=True, exclude_none=True)
    schema = load_schema("eval_report.v2")
    jsonschema.validate(report_dict, schema)


def test_eval_report_v2_without_accuracy() -> None:
    """Test EvalReportV2 without accuracy (should still be valid)."""
    report = EvalReportV2(
        schema_version="eval_report.v2",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        dataset_digest="a" * 64,
        assembly_config_hash="b" * 64,
        policy_id="baseline.first_legal",
        eval_config_hash="c" * 64,
        metrics=EvalMetricsV1(
            records_evaluated=100,
            illegal_move_rate="0.0000",
            top_k_legal_coverage=TopKLegalCoverage(top1="100.0000", top3="100.0000"),
            policy_entropy=PolicyEntropyStats(mean="3.5000"),
            unique_moves_emitted=50,
        ),
        total_record_count=100,
        labeled_record_count=0,
        accuracy=None,
    )

    report_dict = report.model_dump(mode="json", by_alias=True, exclude_none=True)
    # accuracy should be excluded when None
    assert "accuracy" not in report_dict

    # Should still validate (accuracy is optional in schema)
    schema = load_schema("eval_report.v2")
    jsonschema.validate(report_dict, schema)
