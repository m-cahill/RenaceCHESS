"""Tests for deterministic split assignment."""

from renacechess.dataset.split import compute_split_assignment


def test_split_determinism():
    """Test that split assignment is deterministic."""
    # Test known record keys
    key1 = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1:0"
    key2 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1:1"

    split1 = compute_split_assignment(key1)
    split2 = compute_split_assignment(key2)

    # Should be deterministic
    assert compute_split_assignment(key1) == split1
    assert compute_split_assignment(key2) == split2

    # Should return valid splits
    assert split1 in ["train", "val", "frozenEval"]
    assert split2 in ["train", "val", "frozenEval"]


def test_split_distribution():
    """Test that split distribution is approximately correct."""
    # Generate many keys and check distribution
    splits = {"train": 0, "val": 0, "frozenEval": 0}
    num_samples = 1000

    for i in range(num_samples):
        key = f"test_fen_{i}:{i}"
        split = compute_split_assignment(key)
        splits[split] += 1

    # Check approximate distribution (5% frozenEval, 10% val, 85% train)
    frozen_ratio = splits["frozenEval"] / num_samples
    val_ratio = splits["val"] / num_samples
    train_ratio = splits["train"] / num_samples

    # Allow some tolerance (within 5 percentage points)
    assert 0.0 <= frozen_ratio <= 0.10, f"frozenEval ratio {frozen_ratio} out of range"
    assert 0.05 <= val_ratio <= 0.15, f"val ratio {val_ratio} out of range"
    assert 0.80 <= train_ratio <= 0.95, f"train ratio {train_ratio} out of range"

