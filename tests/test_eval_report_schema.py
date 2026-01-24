"""Tests for evaluation report schema validation."""

import json
from datetime import datetime
from pathlib import Path

import jsonschema

from renacechess.contracts.models import (
    EvalMetricsV1,
    EvalReportSplitsV1,
    EvalReportV1,
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


def test_eval_report_v1_schema_validation() -> None:
    """Test that EvalReportV1 validates against schema (roundtrip)."""
    report = EvalReportV1(
        schema_version="eval_report.v1",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        dataset_digest="a" * 64,
        assembly_config_hash="b" * 64,
        policy_id="baseline.uniform_random",
        eval_config_hash="c" * 64,
        metrics=EvalMetricsV1(
            records_evaluated=1000,
            illegal_move_rate="0.0000",
            top_k_legal_coverage=TopKLegalCoverage(top1="100.0000", top3="100.0000"),
            policy_entropy=PolicyEntropyStats(mean="3.4567", stddev="0.1234"),
            unique_moves_emitted=50,
        ),
        splits=EvalReportSplitsV1(
            train=EvalMetricsV1(
                records_evaluated=800,
                illegal_move_rate="0.0000",
                top_k_legal_coverage=TopKLegalCoverage(top1="100.0000", top3="100.0000"),
                policy_entropy=PolicyEntropyStats(mean="3.4500"),
                unique_moves_emitted=45,
            ),
            val=EvalMetricsV1(
                records_evaluated=150,
                illegal_move_rate="0.0000",
                top_k_legal_coverage=TopKLegalCoverage(top1="100.0000", top3="100.0000"),
                policy_entropy=PolicyEntropyStats(mean="3.4800"),
                unique_moves_emitted=30,
            ),
            frozen_eval=EvalMetricsV1(
                records_evaluated=50,
                illegal_move_rate="0.0000",
                top_k_legal_coverage=TopKLegalCoverage(top1="100.0000", top3="100.0000"),
                policy_entropy=PolicyEntropyStats(mean="3.4400"),
                unique_moves_emitted=20,
            ),
        ),
    )

    # Serialize to dict with aliases (camelCase JSON)
    report_dict = report.model_dump(mode="json", by_alias=True, exclude_none=True)

    # Validate against schema
    schema = load_schema("eval_report.v1")
    jsonschema.validate(report_dict, schema)


def test_eval_report_v1_minimal_schema_validation() -> None:
    """Test that minimal EvalReportV1 validates against schema."""
    report = EvalReportV1(
        schema_version="eval_report.v1",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        dataset_digest="a" * 64,
        assembly_config_hash="b" * 64,
        policy_id="baseline.first_legal",
        eval_config_hash="c" * 64,
        metrics=EvalMetricsV1(
            records_evaluated=100,
            illegal_move_rate="0.0000",
            top_k_legal_coverage=TopKLegalCoverage(top1="100.0000", top3="100.0000"),
            policy_entropy=PolicyEntropyStats(mean="N/A"),
            unique_moves_emitted=1,
        ),
    )

    # Serialize to dict with aliases (camelCase JSON)
    report_dict = report.model_dump(mode="json", by_alias=True, exclude_none=True)

    # Validate against schema
    schema = load_schema("eval_report.v1")
    jsonschema.validate(report_dict, schema)
