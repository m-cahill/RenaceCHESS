"""Evaluation report generation."""

from datetime import datetime
from pathlib import Path
from typing import Any

from renacechess.contracts.models import (
    EvalMetricsV1,
    EvalReportSplitsV1,
    EvalReportV1,
    PolicyEntropyStats,
    TopKLegalCoverage,
)
from renacechess.determinism import canonical_json_dump


def build_eval_report(
    eval_results: dict[str, Any],
    created_at: datetime | None = None,
) -> EvalReportV1:
    """Build EvalReportV1 from evaluation results.

    Args:
        eval_results: Results dictionary from run_evaluation().
        created_at: Override creation timestamp (for determinism tests).

    Returns:
        EvalReportV1 instance.
    """
    if created_at is None:
        created_at = datetime.now()

    # Build overall metrics
    overall_metrics_dict = eval_results["overall_metrics"]
    overall_metrics = EvalMetricsV1(
        records_evaluated=overall_metrics_dict["records_evaluated"],
        illegal_move_rate=overall_metrics_dict["illegal_move_rate"],
        top_k_legal_coverage=TopKLegalCoverage(
            top1=overall_metrics_dict["top_k_legal_coverage"]["top1"],
            top3=overall_metrics_dict["top_k_legal_coverage"]["top3"],
        ),
        policy_entropy=PolicyEntropyStats(
            mean=overall_metrics_dict["policy_entropy"]["mean"],
            stddev=overall_metrics_dict["policy_entropy"].get("stddev"),
        ),
        unique_moves_emitted=overall_metrics_dict["unique_moves_emitted"],
    )

    # Build split metrics
    split_metrics_dict = eval_results.get("split_metrics", {})
    splits = None
    if split_metrics_dict:
        train_metrics = None
        val_metrics = None
        frozen_eval_metrics = None

        if "train" in split_metrics_dict:
            train_dict = split_metrics_dict["train"]
            train_metrics = EvalMetricsV1(
                records_evaluated=train_dict["records_evaluated"],
                illegal_move_rate=train_dict["illegal_move_rate"],
                top_k_legal_coverage=TopKLegalCoverage(
                    top1=train_dict["top_k_legal_coverage"]["top1"],
                    top3=train_dict["top_k_legal_coverage"]["top3"],
                ),
                policy_entropy=PolicyEntropyStats(
                    mean=train_dict["policy_entropy"]["mean"],
                    stddev=train_dict["policy_entropy"].get("stddev"),
                ),
                unique_moves_emitted=train_dict["unique_moves_emitted"],
            )

        if "val" in split_metrics_dict:
            val_dict = split_metrics_dict["val"]
            val_metrics = EvalMetricsV1(
                records_evaluated=val_dict["records_evaluated"],
                illegal_move_rate=val_dict["illegal_move_rate"],
                top_k_legal_coverage=TopKLegalCoverage(
                    top1=val_dict["top_k_legal_coverage"]["top1"],
                    top3=val_dict["top_k_legal_coverage"]["top3"],
                ),
                policy_entropy=PolicyEntropyStats(
                    mean=val_dict["policy_entropy"]["mean"],
                    stddev=val_dict["policy_entropy"].get("stddev"),
                ),
                unique_moves_emitted=val_dict["unique_moves_emitted"],
            )

        if "frozenEval" in split_metrics_dict:
            frozen_dict = split_metrics_dict["frozenEval"]
            frozen_eval_metrics = EvalMetricsV1(
                records_evaluated=frozen_dict["records_evaluated"],
                illegal_move_rate=frozen_dict["illegal_move_rate"],
                top_k_legal_coverage=TopKLegalCoverage(
                    top1=frozen_dict["top_k_legal_coverage"]["top1"],
                    top3=frozen_dict["top_k_legal_coverage"]["top3"],
                ),
                policy_entropy=PolicyEntropyStats(
                    mean=frozen_dict["policy_entropy"]["mean"],
                    stddev=frozen_dict["policy_entropy"].get("stddev"),
                ),
                unique_moves_emitted=frozen_dict["unique_moves_emitted"],
            )

        splits = EvalReportSplitsV1(
            train=train_metrics,
            val=val_metrics,
            frozen_eval=frozen_eval_metrics,
        )

    return EvalReportV1(
        schema_version="eval_report.v1",
        created_at=created_at,
        dataset_digest=eval_results["dataset_digest"],
        assembly_config_hash=eval_results["assembly_config_hash"],
        policy_id=eval_results["policy_id"],
        eval_config_hash=eval_results["eval_config_hash"],
        metrics=overall_metrics,
        splits=splits,
    )


def write_eval_report(report: EvalReportV1, output_path: Path) -> None:
    """Write evaluation report to file in canonical JSON format.

    Args:
        report: EvalReportV1 instance.
        output_path: Path to output file.
    """
    # Serialize to dict with aliases (camelCase JSON)
    report_dict = report.model_dump(mode="json", by_alias=True, exclude_none=True)

    # Write canonical JSON (sorted keys, no whitespace)
    json_bytes = canonical_json_dump(report_dict)
    json_str = json_bytes.decode("utf-8")

    output_path.write_text(json_str + "\n", encoding="utf-8")
