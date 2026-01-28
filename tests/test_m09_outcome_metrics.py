"""Tests for outcome metrics computation (M09)."""


from renacechess.eval.outcome_metrics import (
    OutcomeMetricsAccumulator,
    compute_brier_score,
    compute_cross_entropy,
    compute_ece,
)


def test_compute_cross_entropy() -> None:
    """Test cross-entropy computation."""
    # Perfect prediction
    pred = {"w": 1.0, "d": 0.0, "l": 0.0}
    ce = compute_cross_entropy(pred, "win")
    assert ce >= 0.0
    assert ce < 1e-6  # Should be very small for perfect prediction

    # Worst prediction
    pred = {"w": 0.0, "d": 0.0, "l": 1.0}
    ce = compute_cross_entropy(pred, "win")
    assert ce > 10.0  # Should be large

    # Uniform prediction
    pred = {"w": 1.0 / 3.0, "d": 1.0 / 3.0, "l": 1.0 / 3.0}
    ce = compute_cross_entropy(pred, "win")
    assert ce > 0.0
    assert ce < 2.0  # log(3) ≈ 1.1


def test_compute_brier_score() -> None:
    """Test Brier score computation."""
    # Perfect prediction
    pred = {"w": 1.0, "d": 0.0, "l": 0.0}
    brier = compute_brier_score(pred, "win")
    assert brier >= 0.0
    assert brier < 1e-6  # Should be very small

    # Worst prediction
    pred = {"w": 0.0, "d": 0.0, "l": 1.0}
    brier = compute_brier_score(pred, "win")
    assert brier > 1.0  # Should be large (at least 1.0 for worst case)

    # Uniform prediction
    pred = {"w": 1.0 / 3.0, "d": 1.0 / 3.0, "l": 1.0 / 3.0}
    brier = compute_brier_score(pred, "win")
    assert brier > 0.0
    assert brier < 1.0


def test_outcome_metrics_accumulator() -> None:
    """Test outcome metrics accumulator."""
    acc = OutcomeMetricsAccumulator()

    # Add some predictions
    acc.add_prediction({"w": 0.7, "d": 0.2, "l": 0.1}, "win")
    acc.add_prediction({"w": 0.3, "d": 0.4, "l": 0.3}, "draw")
    acc.add_prediction({"w": 0.1, "d": 0.2, "l": 0.7}, "loss")

    metrics = acc.compute_metrics()

    assert metrics["total_predictions"] == 3
    assert metrics["cross_entropy"] is not None
    assert metrics["brier_score"] is not None
    assert metrics["ece"] is not None

    assert metrics["cross_entropy"] >= 0.0
    assert metrics["brier_score"] >= 0.0
    assert 0.0 <= metrics["ece"] <= 1.0


def test_outcome_metrics_accumulator_empty() -> None:
    """Test outcome metrics accumulator with no predictions."""
    acc = OutcomeMetricsAccumulator()
    metrics = acc.compute_metrics()

    assert metrics["total_predictions"] == 0
    assert metrics["cross_entropy"] is None
    assert metrics["brier_score"] is None
    assert metrics["ece"] is None


def test_compute_ece() -> None:
    """Test Expected Calibration Error computation."""
    # Perfectly calibrated predictions
    predictions = [
        {"w": 0.9, "d": 0.05, "l": 0.05},
        {"w": 0.8, "d": 0.1, "l": 0.1},
        {"w": 0.7, "d": 0.15, "l": 0.15},
    ]
    true_outcomes = ["win", "win", "win"]

    ece = compute_ece(predictions, true_outcomes, n_bins=10)
    assert 0.0 <= ece <= 1.0

    # Empty predictions
    ece = compute_ece([], [])
    assert ece == 0.0


def test_compute_ece_bins() -> None:
    """Test ECE with different bin counts."""
    predictions = [
        {"w": 0.9, "d": 0.05, "l": 0.05},
        {"w": 0.1, "d": 0.1, "l": 0.8},
    ]
    true_outcomes = ["win", "loss"]

    ece_10 = compute_ece(predictions, true_outcomes, n_bins=10)
    ece_5 = compute_ece(predictions, true_outcomes, n_bins=5)

    assert 0.0 <= ece_10 <= 1.0
    assert 0.0 <= ece_5 <= 1.0


def test_cross_entropy_edge_cases() -> None:
    """Test cross-entropy handles edge cases."""
    # Very small probability
    pred = {"w": 1e-10, "d": 0.0, "l": 1.0 - 1e-10}
    ce = compute_cross_entropy(pred, "win")
    assert ce > 0.0
    assert ce < 100.0  # Should be clamped

    # Very large probability
    pred = {"w": 1.0 - 1e-10, "d": 0.0, "l": 1e-10}
    ce = compute_cross_entropy(pred, "win")
    assert ce >= 0.0
    assert ce < 1e-5  # Should be very small


def test_brier_score_all_outcomes() -> None:
    """Test Brier score for all outcome types."""
    for outcome in ["win", "draw", "loss"]:
        pred = {"w": 1.0, "d": 0.0, "l": 0.0}
        brier = compute_brier_score(pred, outcome)

        if outcome == "win":
            assert brier < 1e-6  # Perfect
        else:
            assert brier > 0.0  # Not perfect


def test_outcome_metrics_accumulator_stratified() -> None:
    """Test outcome metrics accumulator with multiple predictions."""
    acc = OutcomeMetricsAccumulator()

    # Add predictions for different outcomes
    for i in range(10):
        if i % 3 == 0:
            acc.add_prediction({"w": 0.7, "d": 0.2, "l": 0.1}, "win")
        elif i % 3 == 1:
            acc.add_prediction({"w": 0.2, "d": 0.6, "l": 0.2}, "draw")
        else:
            acc.add_prediction({"w": 0.1, "d": 0.2, "l": 0.7}, "loss")

    metrics = acc.compute_metrics()

    assert metrics["total_predictions"] == 10
    assert metrics["cross_entropy"] is not None
    assert metrics["brier_score"] is not None
    assert metrics["ece"] is not None
