"""Tests for backward compatibility (M09)."""



from renacechess.contracts.models import EvalReportV3, EvalReportV4, EvalReportV5


def test_eval_report_v4_still_validates() -> None:
    """Test that v4 reports still validate (backward compatibility)."""
    # Create minimal v4 report
    report_data = {
        "schemaVersion": "eval_report.v4",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfigHash": "b" * 64,
        "policyId": "baseline.uniform_random",
        "evalConfigHash": "c" * 64,
        "overall": {
            "totalRecords": 100,
            "labeledRecords": 50,
            "recordsWithPolicy": 100,
        },
        "bySkillBucketId": {},
        "byTimeControlClass": {},
        "byTimePressureBucket": {},
    }

    report = EvalReportV4.model_validate(report_data)
    assert report.schema_version == "eval_report.v4"


def test_eval_report_v5_without_outcome_metrics() -> None:
    """Test that v5 reports can be created without outcome metrics (conditional)."""
    report_data = {
        "schemaVersion": "eval_report.v5",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfigHash": "b" * 64,
        "policyId": "baseline.uniform_random",
        "evalConfigHash": "c" * 64,
        "overall": {
            "totalRecords": 100,
            "labeledRecords": 50,
            "recordsWithPolicy": 100,
        },
        "bySkillBucketId": {},
        "byTimeControlClass": {},
        "byTimePressureBucket": {},
        "outcomeMetrics": None,
        "outcomeMetricsBySkill": None,
        "outcomeMetricsByTimeControl": None,
        "outcomeMetricsByTimePressure": None,
    }

    report = EvalReportV5.model_validate(report_data)
    assert report.schema_version == "eval_report.v5"
    assert report.outcome_metrics is None


def test_eval_report_v5_with_outcome_metrics() -> None:
    """Test that v5 reports can include outcome metrics."""
    report_data = {
        "schemaVersion": "eval_report.v5",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfigHash": "b" * 64,
        "policyId": "baseline.uniform_random",
        "evalConfigHash": "c" * 64,
        "overall": {
            "totalRecords": 100,
            "labeledRecords": 50,
            "recordsWithPolicy": 100,
        },
        "bySkillBucketId": {},
        "byTimeControlClass": {},
        "byTimePressureBucket": {},
        "outcomeMetrics": {
            "totalPredictions": 50,
            "crossEntropy": 0.5,
            "brierScore": 0.3,
            "ece": 0.1,
        },
    }

    report = EvalReportV5.model_validate(report_data)
    assert report.schema_version == "eval_report.v5"
    assert report.outcome_metrics is not None
    assert report.outcome_metrics.total_predictions == 50


def test_eval_report_v3_still_works() -> None:
    """Test that v3 reports still validate (no regression)."""
    report_data = {
        "schemaVersion": "eval_report.v3",
        "createdAt": "2024-01-01T00:00:00",
        "datasetDigest": "a" * 64,
        "assemblyConfigHash": "b" * 64,
        "policyId": "baseline.uniform_random",
        "evalConfigHash": "c" * 64,
        "overall": {
            "totalRecords": 100,
            "labeledRecords": 50,
            "recordsWithPolicy": 100,
        },
        "bySkillBucketId": {},
        "byTimeControlClass": {},
        "byTimePressureBucket": {},
    }

    report = EvalReportV3.model_validate(report_data)
    assert report.schema_version == "eval_report.v3"
