"""Conditioned metrics computation for M06 evaluation reports.

This module implements stratified metric accumulation by conditioning axes
(skill bucket, time control class, time pressure bucket).
"""

from collections import defaultdict
from typing import Any

from renacechess.contracts.models import (
    ConditionedAccuracyMetrics,
    ConditionedDistributionMetrics,
    ConditionedMetrics,
    ConditionedValidityMetrics,
    DistributionStats,
)
from renacechess.eval.metrics import format_fixed_decimal


class ConditionedMetricsAccumulator:
    """Accumulates metrics stratified by conditioning axes.

    This accumulator maintains separate metric accumulators for each
    combination of conditioning values (skill bucket ID, time control class,
    time pressure bucket) and computes stratified statistics.
    """

    def __init__(self, compute_accuracy: bool = False, top_k_values: list[int] | None = None):
        """Initialize conditioned metrics accumulator.

        Args:
            compute_accuracy: Whether to compute accuracy metrics.
            top_k_values: List of K values for top-K accuracy (e.g., [1, 3, 5]).
        """
        self.compute_accuracy = compute_accuracy
        self.top_k_values = top_k_values or [1]

        # Overall metrics
        self.total_records = 0
        self.labeled_records = 0
        self.records_with_policy = 0

        # Accuracy tracking (label-only)
        self.correct_top1 = 0
        self.correct_by_k: dict[int, int] = {k: 0 for k in self.top_k_values}

        # Distribution tracking (all records with policy)
        self.entropy_values: list[float] = []
        self.top_gap_values: list[float] = []
        self.legal_moves_count_values: list[int] = []

        # Validity tracking
        self.illegal_count = 0
        self.unique_moves: set[str] = set()

        # Stratified accumulators
        self.by_skill_bucket_id: dict[str, "ConditionedMetricsAccumulator"] = defaultdict(
            lambda: ConditionedMetricsAccumulator(self.compute_accuracy, self.top_k_values)
        )
        self.by_time_control_class: dict[str, "ConditionedMetricsAccumulator"] = defaultdict(
            lambda: ConditionedMetricsAccumulator(self.compute_accuracy, self.top_k_values)
        )
        self.by_time_pressure_bucket: dict[str, "ConditionedMetricsAccumulator"] = defaultdict(
            lambda: ConditionedMetricsAccumulator(self.compute_accuracy, self.top_k_values)
        )

    def add_record(
        self,
        policy_output: str | None,
        legal_moves: list[str],
        chosen_move: str | None = None,
        policy_entropy: float | None = None,
        policy_top_gap: float | None = None,
        skill_bucket_id: str | None = None,
        time_control_class: str | None = None,
        time_pressure_bucket: str | None = None,
    ) -> None:
        """Add a record to the accumulator.

        Args:
            policy_output: Policy's predicted move (UCI).
            legal_moves: List of legal moves in UCI format.
            chosen_move: Ground-truth move (UCI), or None if unlabeled.
            policy_entropy: Policy entropy value.
            policy_top_gap: Policy top gap value.
            skill_bucket_id: M06 skill bucket ID.
            time_control_class: Time control class.
            time_pressure_bucket: Time pressure bucket.
        """
        self.total_records += 1

        # Track labeled records
        if chosen_move is not None:
            self.labeled_records += 1

        # Track records with policy
        if policy_output is not None:
            self.records_with_policy += 1

            # Distribution metrics (all records with policy)
            if policy_entropy is not None:
                self.entropy_values.append(policy_entropy)
            if policy_top_gap is not None:
                self.top_gap_values.append(policy_top_gap)
            self.legal_moves_count_values.append(len(legal_moves))

            # Validity metrics
            if policy_output not in legal_moves:
                self.illegal_count += 1
            self.unique_moves.add(policy_output)

            # Accuracy metrics (label-only)
            if self.compute_accuracy and chosen_move is not None:
                # Top-1 accuracy
                if policy_output == chosen_move:
                    self.correct_top1 += 1

                # Top-K accuracy (for now, same as top-1 since we only have single policy output)
                # TODO: Extend for actual top-K policy outputs
                for k in self.top_k_values:
                    if policy_output == chosen_move:
                        self.correct_by_k[k] += 1

        # Stratify by conditioning axes
        if skill_bucket_id:
            self.by_skill_bucket_id[skill_bucket_id].add_record(
                policy_output,
                legal_moves,
                chosen_move,
                policy_entropy,
                policy_top_gap,
                None,
                None,
                None,  # Don't recurse stratification
            )

        if time_control_class:
            self.by_time_control_class[time_control_class].add_record(
                policy_output,
                legal_moves,
                chosen_move,
                policy_entropy,
                policy_top_gap,
                None,
                None,
                None,
            )

        if time_pressure_bucket:
            self.by_time_pressure_bucket[time_pressure_bucket].add_record(
                policy_output,
                legal_moves,
                chosen_move,
                policy_entropy,
                policy_top_gap,
                None,
                None,
                None,
            )

    def build_metrics(self) -> ConditionedMetrics:
        """Build ConditionedMetrics from accumulated data.

        Returns:
            ConditionedMetrics instance with computed statistics.
        """
        # Accuracy metrics (label-only)
        accuracy = None
        if self.compute_accuracy and self.labeled_records > 0:
            top1 = self.correct_top1 / self.labeled_records
            top_k = {
                str(k): format_fixed_decimal(self.correct_by_k[k] / self.labeled_records)
                for k in self.top_k_values
            }
            coverage = self.labeled_records / self.total_records if self.total_records > 0 else 0.0

            accuracy = ConditionedAccuracyMetrics(
                top1=format_fixed_decimal(top1),
                top_k=top_k,
                coverage=format_fixed_decimal(coverage),
            )

        # Distribution metrics (all records with policy)
        distribution = None
        if self.records_with_policy > 0:
            entropy_stats = None
            if self.entropy_values:
                entropy_stats = DistributionStats(
                    mean=format_fixed_decimal(sum(self.entropy_values) / len(self.entropy_values)),
                    median=format_fixed_decimal(
                        sorted(self.entropy_values)[len(self.entropy_values) // 2]
                    )
                    if len(self.entropy_values) > 0
                    else None,
                )

            top_gap_stats = None
            if self.top_gap_values:
                top_gap_stats = DistributionStats(
                    mean=format_fixed_decimal(sum(self.top_gap_values) / len(self.top_gap_values)),
                    median=format_fixed_decimal(
                        sorted(self.top_gap_values)[len(self.top_gap_values) // 2]
                    )
                    if len(self.top_gap_values) > 0
                    else None,
                )

            legal_moves_stats = None
            if self.legal_moves_count_values:
                legal_moves_stats = DistributionStats(
                    mean=format_fixed_decimal(
                        sum(self.legal_moves_count_values) / len(self.legal_moves_count_values)
                    ),
                    median=format_fixed_decimal(
                        sorted(self.legal_moves_count_values)[
                            len(self.legal_moves_count_values) // 2
                        ]
                    )
                    if len(self.legal_moves_count_values) > 0
                    else None,
                )

            distribution = ConditionedDistributionMetrics(
                entropy=entropy_stats,
                top_gap=top_gap_stats,
                legal_moves_count=legal_moves_stats,
            )

        # Validity metrics
        validity = None
        if self.records_with_policy > 0:
            illegal_rate = self.illegal_count / self.records_with_policy

            validity = ConditionedValidityMetrics(
                illegal_rate=format_fixed_decimal(illegal_rate),
                unique_moves_emitted=len(self.unique_moves),
            )

        return ConditionedMetrics(
            total_records=self.total_records,
            labeled_records=self.labeled_records,
            records_with_policy=self.records_with_policy,
            accuracy=accuracy,
            distribution=distribution,
            validity=validity,
        )

    def build_stratified_metrics(self) -> dict[str, dict[str, ConditionedMetrics]]:
        """Build stratified metrics dictionaries.

        Returns:
            Dictionary with keys "bySkillBucketId", "byTimeControlClass", "byTimePressureBucket",
            each containing a dictionary of ConditionedMetrics by bucket/class/value.
        """
        return {
            "bySkillBucketId": {
                bucket_id: acc.build_metrics()
                for bucket_id, acc in self.by_skill_bucket_id.items()
            },
            "byTimeControlClass": {
                tc_class: acc.build_metrics()
                for tc_class, acc in self.by_time_control_class.items()
            },
            "byTimePressureBucket": {
                tp_bucket: acc.build_metrics()
                for tp_bucket, acc in self.by_time_pressure_bucket.items()
            },
        }

