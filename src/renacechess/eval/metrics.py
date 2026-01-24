"""Metrics computation for policy evaluation."""

import math
from typing import Any

from renacechess.contracts.models import PolicyMove


class MetricsAccumulator:
    """Accumulator for evaluation metrics."""

    def __init__(self) -> None:
        """Initialize empty accumulator."""
        self.records_evaluated = 0
        self.illegal_moves = 0
        self.top1_legal = 0
        self.top3_legal = 0
        self.entropy_sum = 0.0
        self.entropy_count = 0
        self.all_moves: set[str] = set()

    def add_record(self, record: dict, predicted_moves: list[PolicyMove]) -> None:
        """Add a single record's evaluation results.

        Args:
            record: Dataset record (Context Bridge payload dict).
            predicted_moves: Policy predictions for this record.
        """
        self.records_evaluated += 1

        legal_moves = set(record["position"]["legalMoves"])

        # Check for illegal moves
        if predicted_moves:
            top_move = predicted_moves[0].uci
            if top_move not in legal_moves:
                self.illegal_moves += 1

            # Track all predicted moves
            for move in predicted_moves:
                self.all_moves.add(move.uci)

            # Top-1 legal coverage
            if top_move in legal_moves:
                self.top1_legal += 1

            # Top-3 legal coverage
            top3_moves = {move.uci for move in predicted_moves[:3]}
            if top3_moves & legal_moves:  # Intersection
                self.top3_legal += 1

        # Compute entropy if probabilities are available
        if predicted_moves and all(move.p > 0 for move in predicted_moves):
            entropy = compute_shannon_entropy([move.p for move in predicted_moves])
            self.entropy_sum += entropy
            self.entropy_count += 1

    def compute_metrics(self) -> dict[str, Any]:
        """Compute final metrics from accumulated data.

        Returns:
            Dictionary with computed metrics.
        """
        illegal_rate = (
            (self.illegal_moves / self.records_evaluated * 100.0)
            if self.records_evaluated > 0
            else 0.0
        )
        top1_coverage = (
            (self.top1_legal / self.records_evaluated * 100.0)
            if self.records_evaluated > 0
            else 0.0
        )
        top3_coverage = (
            (self.top3_legal / self.records_evaluated * 100.0)
            if self.records_evaluated > 0
            else 0.0
        )
        mean_entropy = (self.entropy_sum / self.entropy_count) if self.entropy_count > 0 else 0.0

        return {
            "records_evaluated": self.records_evaluated,
            "illegal_move_rate": format_fixed_decimal(illegal_rate),
            "top_k_legal_coverage": {
                "top1": format_fixed_decimal(top1_coverage),
                "top3": format_fixed_decimal(top3_coverage),
            },
            "policy_entropy": {
                "mean": format_fixed_decimal(mean_entropy) if mean_entropy > 0 else "N/A",
                "stddev": None,  # TODO: compute stddev if needed
            },
            "unique_moves_emitted": len(self.all_moves),
        }

    def merge(self, other: "MetricsAccumulator") -> None:
        """Merge another accumulator into this one.

        Args:
            other: Another MetricsAccumulator to merge.
        """
        self.records_evaluated += other.records_evaluated
        self.illegal_moves += other.illegal_moves
        self.top1_legal += other.top1_legal
        self.top3_legal += other.top3_legal
        self.entropy_sum += other.entropy_sum
        self.entropy_count += other.entropy_count
        self.all_moves.update(other.all_moves)


def compute_shannon_entropy(probabilities: list[float]) -> float:
    """Compute Shannon entropy of a probability distribution.

    Args:
        probabilities: List of probabilities (should sum to ~1.0).

    Returns:
        Shannon entropy in bits.
    """
    entropy = 0.0
    for p in probabilities:
        if p > 0:
            entropy -= p * math.log2(p)
    return max(0.0, entropy)


def format_fixed_decimal(value: float, decimals: int = 4) -> str:
    """Format float as fixed-decimal string for byte-stability.

    Args:
        value: Float value to format.
        decimals: Number of decimal places.

    Returns:
        Fixed-decimal string (e.g., '3.4567').
    """
    return f"{value:.{decimals}f}"
