"""Tests for accuracy metrics computation (M05)."""

from renacechess.contracts.models import PolicyMove
from renacechess.eval.metrics import MetricsAccumulator


def test_accuracy_metrics_top1() -> None:
    """Test top-1 accuracy computation."""
    accumulator = MetricsAccumulator(compute_accuracy=True, top_k_values=[1])

    # Record 1: Policy predicts correct move (top-1)
    record1 = {
        "position": {"legalMoves": ["e2e4", "d2d4"]},
        "chosenMove": {"uci": "e2e4"},
    }
    predicted1 = [PolicyMove(uci="e2e4", p=0.6), PolicyMove(uci="d2d4", p=0.4)]
    accumulator.add_record(record1, predicted1)

    # Record 2: Policy predicts wrong move (top-1)
    record2 = {
        "position": {"legalMoves": ["e2e4", "d2d4"]},
        "chosenMove": {"uci": "e2e4"},
    }
    predicted2 = [PolicyMove(uci="d2d4", p=0.6), PolicyMove(uci="e2e4", p=0.4)]
    accumulator.add_record(record2, predicted2)

    # Record 3: Unlabeled (no chosenMove)
    record3 = {
        "position": {"legalMoves": ["e2e4", "d2d4"]},
    }
    predicted3 = [PolicyMove(uci="e2e4", p=0.6)]
    accumulator.add_record(record3, predicted3)

    metrics = accumulator.compute_metrics()

    assert metrics["labeled_record_count"] == 2
    assert "accuracy" in metrics
    assert metrics["accuracy"]["top1"] == "50.0000"  # 1 out of 2 correct


def test_accuracy_metrics_top3() -> None:
    """Test top-3 accuracy computation."""
    accumulator = MetricsAccumulator(compute_accuracy=True, top_k_values=[1, 3])

    # Record 1: Correct move is top-1
    record1 = {
        "position": {"legalMoves": ["e2e4", "d2d4", "g1f3", "b1c3"]},
        "chosenMove": {"uci": "e2e4"},
    }
    predicted1 = [
        PolicyMove(uci="e2e4", p=0.4),
        PolicyMove(uci="d2d4", p=0.3),
        PolicyMove(uci="g1f3", p=0.2),
        PolicyMove(uci="b1c3", p=0.1),
    ]
    accumulator.add_record(record1, predicted1)

    # Record 2: Correct move is top-3 (but not top-1)
    record2 = {
        "position": {"legalMoves": ["e2e4", "d2d4", "g1f3", "b1c3"]},
        "chosenMove": {"uci": "g1f3"},
    }
    predicted2 = [
        PolicyMove(uci="e2e4", p=0.4),
        PolicyMove(uci="d2d4", p=0.3),
        PolicyMove(uci="g1f3", p=0.2),
    ]
    accumulator.add_record(record2, predicted2)

    # Record 3: Correct move not in top-3
    record3 = {
        "position": {"legalMoves": ["e2e4", "d2d4", "g1f3", "b1c3"]},
        "chosenMove": {"uci": "b1c3"},
    }
    predicted3 = [
        PolicyMove(uci="e2e4", p=0.4),
        PolicyMove(uci="d2d4", p=0.3),
        PolicyMove(uci="g1f3", p=0.2),
    ]
    accumulator.add_record(record3, predicted3)

    metrics = accumulator.compute_metrics()

    assert metrics["labeled_record_count"] == 3
    assert metrics["accuracy"]["top1"] == "33.3333"  # 1 out of 3 correct
    assert metrics["accuracy"]["top3"] == "66.6667"  # 2 out of 3 correct


def test_accuracy_metrics_no_labeled_records() -> None:
    """Test accuracy metrics when no records are labeled."""
    accumulator = MetricsAccumulator(compute_accuracy=True, top_k_values=[1])

    # Add unlabeled records
    for i in range(5):
        record = {
            "position": {"legalMoves": ["e2e4", "d2d4"]},
        }
        predicted = [PolicyMove(uci="e2e4", p=0.6)]
        accumulator.add_record(record, predicted)

    metrics = accumulator.compute_metrics()

    assert metrics["labeled_record_count"] == 0
    assert "accuracy" in metrics
    assert metrics["accuracy"]["top1"] == "0.0000"


def test_accuracy_metrics_disabled() -> None:
    """Test that accuracy metrics are not computed when disabled."""
    accumulator = MetricsAccumulator(compute_accuracy=False)

    record = {
        "position": {"legalMoves": ["e2e4"]},
        "chosenMove": {"uci": "e2e4"},
    }
    predicted = [PolicyMove(uci="e2e4", p=1.0)]
    accumulator.add_record(record, predicted)

    metrics = accumulator.compute_metrics()

    assert "accuracy" not in metrics
    assert "labeled_record_count" not in metrics


def test_accuracy_metrics_coverage() -> None:
    """Test coverage computation."""
    accumulator = MetricsAccumulator(compute_accuracy=True, top_k_values=[1])

    # Add 5 labeled records
    for i in range(5):
        record = {
            "position": {"legalMoves": ["e2e4"]},
            "chosenMove": {"uci": "e2e4"},
        }
        predicted = [PolicyMove(uci="e2e4", p=1.0)]
        accumulator.add_record(record, predicted)

    # Add 5 unlabeled records
    for i in range(5):
        record = {
            "position": {"legalMoves": ["e2e4"]},
        }
        predicted = [PolicyMove(uci="e2e4", p=1.0)]
        accumulator.add_record(record, predicted)

    metrics = accumulator.compute_metrics()

    assert metrics["labeled_record_count"] == 5
    # Coverage will be computed in runner using total_record_count
    # Here we just verify labeled_count is correct

