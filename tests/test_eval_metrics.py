"""Tests for evaluation metrics computation."""

from renacechess.contracts.models import PolicyMove
from renacechess.eval.metrics import (
    MetricsAccumulator,
    compute_shannon_entropy,
    format_fixed_decimal,
)


def test_metrics_accumulator_illegal_moves() -> None:
    """Test MetricsAccumulator illegal move detection."""
    accumulator = MetricsAccumulator()

    record = {
        "position": {
            "legalMoves": ["a2a3", "a2a4"],
        }
    }

    # Legal move
    moves_legal = [PolicyMove(uci="a2a3", san=None, p=1.0)]
    accumulator.add_record(record, moves_legal)
    assert accumulator.illegal_moves == 0

    # Illegal move
    moves_illegal = [PolicyMove(uci="e2e4", san=None, p=1.0)]  # Not in legalMoves
    accumulator.add_record(record, moves_illegal)
    assert accumulator.illegal_moves == 1


def test_metrics_accumulator_top_k_coverage() -> None:
    """Test MetricsAccumulator top-K legal coverage."""
    accumulator = MetricsAccumulator()

    record = {
        "position": {
            "legalMoves": ["a2a3", "a2a4", "b2b3"],
        }
    }

    # Top-1 legal
    moves = [
        PolicyMove(uci="a2a3", san=None, p=0.6),
        PolicyMove(uci="a2a4", san=None, p=0.4),
    ]
    accumulator.add_record(record, moves)
    assert accumulator.top1_legal == 1
    assert accumulator.top3_legal == 1

    # Top-1 illegal, but top-3 has legal
    moves2 = [
        PolicyMove(uci="e2e4", san=None, p=0.6),  # Illegal
        PolicyMove(uci="a2a3", san=None, p=0.4),  # Legal
    ]
    accumulator.add_record(record, moves2)
    assert accumulator.top1_legal == 1  # Still 1
    assert accumulator.top3_legal == 2  # Both records have top-3 coverage


def test_metrics_accumulator_entropy() -> None:
    """Test MetricsAccumulator entropy computation."""
    accumulator = MetricsAccumulator()

    record = {
        "position": {
            "legalMoves": ["a2a3", "a2a4"],
        }
    }

    # Uniform distribution (entropy = 1.0)
    moves = [
        PolicyMove(uci="a2a3", san=None, p=0.5),
        PolicyMove(uci="a2a4", san=None, p=0.5),
    ]
    accumulator.add_record(record, moves)

    metrics = accumulator.compute_metrics()
    assert metrics["records_evaluated"] == 1
    assert float(metrics["policy_entropy"]["mean"]) > 0.0


def test_metrics_accumulator_unique_moves() -> None:
    """Test MetricsAccumulator unique moves tracking."""
    accumulator = MetricsAccumulator()

    record = {
        "position": {
            "legalMoves": ["a2a3", "a2a4", "b2b3"],
        }
    }

    moves1 = [PolicyMove(uci="a2a3", san=None, p=1.0)]
    accumulator.add_record(record, moves1)

    moves2 = [PolicyMove(uci="a2a4", san=None, p=1.0)]
    accumulator.add_record(record, moves2)

    moves3 = [PolicyMove(uci="a2a3", san=None, p=1.0)]  # Duplicate
    accumulator.add_record(record, moves3)

    metrics = accumulator.compute_metrics()
    assert metrics["unique_moves_emitted"] == 2  # a2a3 and a2a4


def test_metrics_accumulator_merge() -> None:
    """Test MetricsAccumulator merge operation."""
    acc1 = MetricsAccumulator()
    acc2 = MetricsAccumulator()

    record = {
        "position": {
            "legalMoves": ["a2a3"],
        }
    }

    acc1.add_record(record, [PolicyMove(uci="a2a3", san=None, p=1.0)])
    acc2.add_record(record, [PolicyMove(uci="a2a3", san=None, p=1.0)])

    acc1.merge(acc2)

    metrics = acc1.compute_metrics()
    assert metrics["records_evaluated"] == 2


def test_compute_shannon_entropy() -> None:
    """Test Shannon entropy computation."""
    # Uniform distribution (2 moves, p=0.5 each) -> entropy = 1.0
    entropy = compute_shannon_entropy([0.5, 0.5])
    assert abs(entropy - 1.0) < 0.01

    # Deterministic (1 move, p=1.0) -> entropy = 0.0
    entropy = compute_shannon_entropy([1.0])
    assert abs(entropy - 0.0) < 0.01

    # Skewed distribution
    entropy = compute_shannon_entropy([0.9, 0.1])
    assert 0.0 < entropy < 1.0


def test_format_fixed_decimal() -> None:
    """Test fixed-decimal formatting for byte-stability."""
    assert format_fixed_decimal(3.4567) == "3.4567"
    assert format_fixed_decimal(0.0) == "0.0000"
    assert format_fixed_decimal(100.0) == "100.0000"
    assert format_fixed_decimal(0.12345, decimals=2) == "0.12"
