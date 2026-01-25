"""Outcome metrics computation for human W/D/L evaluation (M09).

This module provides metrics for evaluating outcome head predictions:
- Cross-entropy (log loss)
- Brier score
- Expected Calibration Error (ECE) with 10-bin equal-width calibration
"""

import math
from typing import Any


def compute_cross_entropy(
    predicted_probs: dict[str, float], true_outcome: str
) -> float:
    """Compute cross-entropy (log loss) for a single prediction.

    Args:
        predicted_probs: Dictionary with keys 'w', 'd', 'l' (probabilities)
        true_outcome: True outcome ('win', 'draw', 'loss')

    Returns:
        Cross-entropy value (non-negative, lower is better)
    """
    # Map true outcome to probability
    if true_outcome == "win":
        true_prob = predicted_probs.get("w", 0.0)
    elif true_outcome == "draw":
        true_prob = predicted_probs.get("d", 0.0)
    elif true_outcome == "loss":
        true_prob = predicted_probs.get("l", 0.0)
    else:
        raise ValueError(f"Invalid outcome: {true_outcome}")

    # Clamp to avoid log(0)
    true_prob = max(1e-10, min(1.0 - 1e-10, true_prob))

    # Cross-entropy: -log(p_true)
    return float(-math.log(true_prob))


def compute_brier_score(
    predicted_probs: dict[str, float], true_outcome: str
) -> float:
    """Compute Brier score for a single prediction.

    Args:
        predicted_probs: Dictionary with keys 'w', 'd', 'l' (probabilities)
        true_outcome: True outcome ('win', 'draw', 'loss')

    Returns:
        Brier score (non-negative, lower is better)
    """
    # Create one-hot encoding of true outcome
    true_probs = {"w": 0.0, "d": 0.0, "l": 0.0}
    if true_outcome == "win":
        true_probs["w"] = 1.0
    elif true_outcome == "draw":
        true_probs["d"] = 1.0
    elif true_outcome == "loss":
        true_probs["l"] = 1.0
    else:
        raise ValueError(f"Invalid outcome: {true_outcome}")

    # Brier score: sum((predicted - true)^2)
    brier = (
        (predicted_probs.get("w", 0.0) - true_probs["w"]) ** 2
        + (predicted_probs.get("d", 0.0) - true_probs["d"]) ** 2
        + (predicted_probs.get("l", 0.0) - true_probs["l"]) ** 2
    )

    return brier


class OutcomeMetricsAccumulator:
    """Accumulator for outcome evaluation metrics."""

    def __init__(self) -> None:
        """Initialize accumulator."""
        self.predictions: list[dict[str, float]] = []
        self.true_outcomes: list[str] = []
        self.cross_entropies: list[float] = []
        self.brier_scores: list[float] = []

    def add_prediction(
        self, predicted_probs: dict[str, float], true_outcome: str
    ) -> None:
        """Add a single prediction and true outcome.

        Args:
            predicted_probs: Dictionary with keys 'w', 'd', 'l' (probabilities)
            true_outcome: True outcome ('win', 'draw', 'loss')
        """
        self.predictions.append(predicted_probs)
        self.true_outcomes.append(true_outcome)

        # Compute metrics
        ce = compute_cross_entropy(predicted_probs, true_outcome)
        brier = compute_brier_score(predicted_probs, true_outcome)

        self.cross_entropies.append(ce)
        self.brier_scores.append(brier)

    def compute_metrics(self) -> dict[str, Any]:
        """Compute aggregate metrics.

        Returns:
            Dictionary with overall metrics
        """
        if len(self.predictions) == 0:
            return {
                "total_predictions": 0,
                "cross_entropy": None,
                "brier_score": None,
                "ece": None,
            }

        # Aggregate metrics
        avg_ce = (
            sum(self.cross_entropies) / len(self.cross_entropies)
            if self.cross_entropies
            else None
        )
        avg_brier = (
            sum(self.brier_scores) / len(self.brier_scores) if self.brier_scores else None
        )

        # Compute ECE (10-bin equal-width)
        ece = compute_ece(self.predictions, self.true_outcomes)

        return {
            "total_predictions": len(self.predictions),
            "cross_entropy": float(avg_ce) if avg_ce is not None else None,
            "brier_score": float(avg_brier) if avg_brier is not None else None,
            "ece": float(ece) if ece is not None else None,
        }


def compute_ece(
    predictions: list[dict[str, float]], true_outcomes: list[str], n_bins: int = 10
) -> float:
    """Compute Expected Calibration Error (ECE) with equal-width bins.

    Args:
        predictions: List of predicted probability dictionaries
        true_outcomes: List of true outcomes
        n_bins: Number of bins (default: 10)

    Returns:
        ECE value (non-negative, lower is better)
    """
    if len(predictions) == 0:
        return 0.0

    # Extract max probability (confidence) for each prediction
    confidences: list[float] = []
    accuracies: list[bool] = []

    for pred, true_outcome in zip(predictions, true_outcomes):
        # Get predicted class (highest probability)
        pred_class = max(pred.items(), key=lambda x: x[1])[0]
        if pred_class == "w":
            pred_outcome = "win"
        elif pred_class == "d":
            pred_outcome = "draw"
        else:
            pred_outcome = "loss"

        # Confidence is the max probability
        confidence = max(pred.values())
        confidences.append(confidence)
        accuracies.append(pred_outcome == true_outcome)

    # Create equal-width bins [0.0, 0.1), [0.1, 0.2), ..., [0.9, 1.0]
    # Edge case: 1.0 goes in last bin
    bin_edges = [i / n_bins for i in range(n_bins + 1)]
    bin_edges[-1] = 1.01  # Ensure 1.0 is included in last bin

    # Assign predictions to bins
    bin_indices: list[int] = []
    for conf in confidences:
        bin_idx = 0
        for i in range(len(bin_edges) - 1):
            if bin_edges[i] <= conf < bin_edges[i + 1]:
                bin_idx = i
                break
        bin_indices.append(min(max(bin_idx, 0), n_bins - 1))

    # Compute ECE: weighted average of |accuracy - confidence| per bin
    ece = 0.0
    total_samples = len(confidences)

    for bin_idx in range(n_bins):
        bin_items = [i for i in range(len(bin_indices)) if bin_indices[i] == bin_idx]
        bin_size = len(bin_items)

        if bin_size == 0:
            continue

        bin_accuracy = sum(accuracies[i] for i in bin_items) / bin_size
        bin_confidence = sum(confidences[i] for i in bin_items) / bin_size

        # Weight by bin size
        weight = bin_size / total_samples
        ece += weight * abs(bin_accuracy - bin_confidence)

    return float(ece)

