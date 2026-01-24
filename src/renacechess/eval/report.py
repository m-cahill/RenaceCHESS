"""Evaluation report generation."""

from datetime import datetime
from pathlib import Path
from typing import Any

from renacechess.contracts.models import (
    AccuracyMetrics,
    EvalMetricsV1,
    EvalMetricsV2,
    EvalReportSplitsV1,
    EvalReportSplitsV2,
    EvalReportV1,
    EvalReportV2,
    EvalReportV3,
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


def build_eval_report_v2(
    eval_results: dict[str, Any],
    created_at: datetime | None = None,
) -> EvalReportV2:
    """Build EvalReportV2 from evaluation results (with accuracy metrics).

    Args:
        eval_results: Results dictionary from run_evaluation() with accuracy enabled.
        created_at: Override creation timestamp (for determinism tests).

    Returns:
        EvalReportV2 instance.
    """
    if created_at is None:
        created_at = datetime.now()

    # Build overall metrics (v1 metrics unchanged)
    overall_metrics_dict = eval_results["overall_metrics"]
    overall_metrics_v1 = EvalMetricsV1(
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

    # Build accuracy metrics if available
    accuracy_metrics = None
    if "accuracy" in overall_metrics_dict:
        accuracy_dict = overall_metrics_dict["accuracy"]
        # Create AccuracyMetrics with coverage and dynamic top-K fields
        accuracy_data = {"coverage": accuracy_dict["coverage"]}
        # Add all top-K fields dynamically
        for key, value in accuracy_dict.items():
            if key.startswith("top") and key != "coverage":
                accuracy_data[key] = value
        accuracy_metrics = AccuracyMetrics(**accuracy_data)

    # Get total and labeled record counts
    total_record_count = eval_results.get("total_record_count", 0)
    labeled_record_count = overall_metrics_dict.get("labeled_record_count", 0)

    # Build split metrics (v2)
    split_metrics_dict = eval_results.get("split_metrics", {})
    splits = None
    if split_metrics_dict:
        train_metrics = None
        val_metrics = None
        frozen_eval_metrics = None

        def build_split_metrics_v2(split_dict: dict[str, Any]) -> EvalMetricsV2:
            """Helper to build v2 split metrics."""
            split_accuracy = None
            if "accuracy" in split_dict:
                acc_dict = split_dict["accuracy"]
                acc_data = {"coverage": acc_dict["coverage"]}
                for key, value in acc_dict.items():
                    if key.startswith("top") and key != "coverage":
                        acc_data[key] = value
                split_accuracy = AccuracyMetrics(**acc_data)

            return EvalMetricsV2(
                records_evaluated=split_dict["records_evaluated"],
                illegal_move_rate=split_dict["illegal_move_rate"],
                top_k_legal_coverage=TopKLegalCoverage(
                    top1=split_dict["top_k_legal_coverage"]["top1"],
                    top3=split_dict["top_k_legal_coverage"]["top3"],
                ),
                policy_entropy=PolicyEntropyStats(
                    mean=split_dict["policy_entropy"]["mean"],
                    stddev=split_dict["policy_entropy"].get("stddev"),
                ),
                unique_moves_emitted=split_dict["unique_moves_emitted"],
                total_record_count=split_dict.get("total_record_count", 0),
                labeled_record_count=split_dict.get("labeled_record_count", 0),
                accuracy=split_accuracy,
            )

        if "train" in split_metrics_dict:
            train_metrics = build_split_metrics_v2(split_metrics_dict["train"])

        if "val" in split_metrics_dict:
            val_metrics = build_split_metrics_v2(split_metrics_dict["val"])

        if "frozenEval" in split_metrics_dict:
            frozen_eval_metrics = build_split_metrics_v2(split_metrics_dict["frozenEval"])

        splits = EvalReportSplitsV2(
            train=train_metrics,
            val=val_metrics,
            frozen_eval=frozen_eval_metrics,
        )

    return EvalReportV2(
        schema_version="eval_report.v2",
        created_at=created_at,
        dataset_digest=eval_results["dataset_digest"],
        assembly_config_hash=eval_results["assembly_config_hash"],
        policy_id=eval_results["policy_id"],
        eval_config_hash=eval_results["eval_config_hash"],
        metrics=overall_metrics_v1,
        total_record_count=total_record_count,
        labeled_record_count=labeled_record_count,
        accuracy=accuracy_metrics,
        splits=splits,
    )


def write_eval_report(
    report: EvalReportV1 | EvalReportV2 | EvalReportV3, output_path: Path
) -> None:
    """Write evaluation report to file in canonical JSON format.

    Args:
        report: EvalReportV1, EvalReportV2, or EvalReportV3 instance.
        output_path: Path to output file.
    """
    # Serialize to dict with aliases (camelCase JSON)
    report_dict = report.model_dump(mode="json", by_alias=True, exclude_none=True)

    # Write canonical JSON (sorted keys, no whitespace)
    json_bytes = canonical_json_dump(report_dict)
    json_str = json_bytes.decode("utf-8")

    output_path.write_text(json_str + "\n", encoding="utf-8")
