"""Tests for M08 learned policy model (BaselinePolicyV1)."""

import torch

from renacechess.models.baseline_v1 import BaselinePolicyV1


def test_baseline_policy_v1_initialization() -> None:
    """Test model initialization."""
    model = BaselinePolicyV1(move_vocab_size=100)
    assert model.move_vocab_size == 100
    assert len(model.move_vocab) == 0


def test_baseline_policy_v1_move_vocab() -> None:
    """Test move vocabulary building."""
    model = BaselinePolicyV1(move_vocab_size=10)

    # Add moves
    idx1 = model.add_move_to_vocab("e2e4")
    idx2 = model.add_move_to_vocab("d2d4")
    idx3 = model.add_move_to_vocab("e2e4")  # Duplicate

    assert idx1 == idx3  # Same move returns same index
    assert idx2 != idx1
    assert len(model.move_vocab) == 2


def test_baseline_policy_v1_encode_skill_bucket() -> None:
    """Test skill bucket encoding."""
    model = BaselinePolicyV1()

    assert model._encode_skill_bucket("lt_800") == 0
    assert model._encode_skill_bucket("1200_1399") == 3
    assert model._encode_skill_bucket("1200-1400") == 3  # Legacy format
    assert model._encode_skill_bucket("unknown") == 7
    assert model._encode_skill_bucket("invalid") == 7


def test_baseline_policy_v1_encode_time_control() -> None:
    """Test time control encoding."""
    model = BaselinePolicyV1()

    assert model._encode_time_control("blitz") == 1
    assert model._encode_time_control("rapid") == 2
    assert model._encode_time_control(None) == 4  # unknown
    assert model._encode_time_control("invalid") == 4


def test_baseline_policy_v1_forward() -> None:
    """Test forward pass (inference)."""
    model = BaselinePolicyV1(move_vocab_size=10)
    model.eval()

    # Add some moves to vocabulary
    model.add_move_to_vocab("e2e4")
    model.add_move_to_vocab("d2d4")

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    legal_moves = ["e2e4", "d2d4", "g1f3"]  # Third move not in vocab

    move_probs = model(fen, "1200_1399", "blitz", legal_moves)

    # Should return probabilities for all legal moves
    assert len(move_probs) == 3
    assert "e2e4" in move_probs
    assert "d2d4" in move_probs
    assert "g1f3" in move_probs

    # Probabilities should sum to 1.0
    total = sum(move_probs.values())
    assert abs(total - 1.0) < 1e-6

    # All probabilities should be non-negative
    for prob in move_probs.values():
        assert prob >= 0.0


def test_baseline_policy_v1_forward_logits() -> None:
    """Test forward_logits (for training)."""
    model = BaselinePolicyV1(move_vocab_size=10)
    model.train()

    # Add moves to vocabulary
    model.add_move_to_vocab("e2e4")
    model.add_move_to_vocab("d2d4")

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    legal_moves = ["e2e4", "d2d4"]

    legal_logits, legal_moves_filtered, legal_indices = model.forward_logits(
        fen, "1200_1399", "blitz", legal_moves
    )

    # Should return logits tensor
    assert isinstance(legal_logits, torch.Tensor)
    assert len(legal_logits) == 2
    assert len(legal_moves_filtered) == 2
    assert len(legal_indices) == 2


def test_baseline_policy_v1_empty_legal_moves() -> None:
    """Test handling of empty legal moves."""
    model = BaselinePolicyV1()
    model.eval()

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    legal_moves: list[str] = []

    move_probs = model(fen, "1200_1399", "blitz", legal_moves)

    assert len(move_probs) == 0


def test_baseline_policy_v1_deterministic() -> None:
    """Test that same inputs produce same outputs."""
    model1 = BaselinePolicyV1(move_vocab_size=10)
    model2 = BaselinePolicyV1(move_vocab_size=10)

    # Initialize with same weights
    model2.load_state_dict(model1.state_dict())

    # Add same moves in same order
    model1.add_move_to_vocab("e2e4")
    model1.add_move_to_vocab("d2d4")
    model2.add_move_to_vocab("e2e4")
    model2.add_move_to_vocab("d2d4")

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    legal_moves = ["e2e4", "d2d4"]

    model1.eval()
    model2.eval()

    probs1 = model1(fen, "1200_1399", "blitz", legal_moves)
    probs2 = model2(fen, "1200_1399", "blitz", legal_moves)

    # Should produce identical results
    for move in legal_moves:
        assert abs(probs1[move] - probs2[move]) < 1e-6


def test_baseline_policy_v1_probability_precision() -> None:
    """Regression test: ensure probabilities are clamped to [0, 1] and sum to 1.

    This test guards against floating-point precision issues that can cause
    tiny negative values after softmax computation.
    """
    model = BaselinePolicyV1(move_vocab_size=10)
    model.eval()

    # Add moves to vocabulary
    model.add_move_to_vocab("e2e4")
    model.add_move_to_vocab("d2d4")
    model.add_move_to_vocab("g1f3")

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    legal_moves = ["e2e4", "d2d4", "g1f3"]

    # Run multiple times with different seeds to catch edge cases
    for seed_offset in range(10):
        # Create a new model instance to vary initialization
        test_model = BaselinePolicyV1(move_vocab_size=10)
        test_model.eval()
        test_model.add_move_to_vocab("e2e4")
        test_model.add_move_to_vocab("d2d4")
        test_model.add_move_to_vocab("g1f3")

        move_probs = test_model(fen, "1200_1399", "blitz", legal_moves)

        # All probabilities must be non-negative (no tiny negatives)
        for move, prob in move_probs.items():
            assert prob >= 0.0, f"Probability for {move} is negative: {prob}"

        # All probabilities must be <= 1.0
        for move, prob in move_probs.items():
            assert prob <= 1.0, f"Probability for {move} exceeds 1.0: {prob}"

        # Probabilities must sum to 1.0 within tight epsilon
        total = sum(move_probs.values())
        assert abs(total - 1.0) < 1e-6, f"Probabilities sum to {total}, expected 1.0"

    # Test case: legal moves include moves not in vocabulary (covers remaining_moves path)
    test_model2 = BaselinePolicyV1(move_vocab_size=5)
    test_model2.eval()
    test_model2.add_move_to_vocab("e2e4")
    test_model2.add_move_to_vocab("d2d4")
    # Add moves not in vocabulary to trigger remaining_moves path
    legal_moves_with_unknown = ["e2e4", "d2d4", "g1f3", "b1c3", "f1c4"]
    move_probs2 = test_model2(fen, "1200_1399", "blitz", legal_moves_with_unknown)

    # Verify all moves have probabilities
    assert len(move_probs2) == len(legal_moves_with_unknown)
    # Verify probabilities are valid
    for move, prob in move_probs2.items():
        assert prob >= 0.0, f"Probability for {move} is negative: {prob}"
        assert prob <= 1.0, f"Probability for {move} exceeds 1.0: {prob}"
    # Verify sum is 1.0
    total2 = sum(move_probs2.values())
    assert abs(total2 - 1.0) < 1e-6, f"Probabilities sum to {total2}, expected 1.0"


def test_baseline_policy_v1_skill_bucket_legacy_formats() -> None:
    """Test skill bucket encoding with various legacy formats."""
    model = BaselinePolicyV1()

    # Test various legacy formats - cover all branches for branch coverage
    assert model._encode_skill_bucket("500-700") == 0  # low < 800
    assert model._encode_skill_bucket("800-999") == 1  # low < 1000
    assert model._encode_skill_bucket("900-950") == 1  # low < 1000 (different case)
    assert model._encode_skill_bucket("1000-1199") == 2  # low < 1200
    assert model._encode_skill_bucket("1100-1150") == 2  # low < 1200 (different case)
    assert model._encode_skill_bucket("1200-1399") == 3  # low < 1400
    assert model._encode_skill_bucket("1300-1350") == 3  # low < 1400 (different case)
    assert model._encode_skill_bucket("1400-1599") == 4  # low < 1600
    assert model._encode_skill_bucket("1500-1550") == 4  # low < 1600 (different case)
    assert model._encode_skill_bucket("1600-1799") == 5  # low < 1800
    assert model._encode_skill_bucket("1700-1750") == 5  # low < 1800 (different case)
    assert model._encode_skill_bucket("1800-2000") == 6  # else (low >= 1800)
    assert model._encode_skill_bucket("2000-2200") == 6  # else (low >= 1800)
    assert model._encode_skill_bucket("invalid-format") == 7  # ValueError in try/except
    assert model._encode_skill_bucket("") == 7  # No dash, falls through to unknown
    assert model._encode_skill_bucket("not-a-valid-format") == 7  # len(parts) != 2


def test_baseline_policy_v1_move_vocab_full() -> None:
    """Test move vocabulary when full."""
    model = BaselinePolicyV1(move_vocab_size=2)

    # Fill vocabulary
    model.add_move_to_vocab("e2e4")
    model.add_move_to_vocab("d2d4")

    # Adding more should hash to existing slots
    idx3 = model.add_move_to_vocab("g1f3")
    assert idx3 < model.move_vocab_size


def test_baseline_policy_v1_forward_logits_unknown_move() -> None:
    """Test forward_logits with move not in vocabulary (uses hash fallback)."""
    model = BaselinePolicyV1(move_vocab_size=10)
    model.eval()

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    legal_moves = ["a1a2"]  # Not in vocabulary, will hash to slot

    legal_logits, legal_moves_filtered, legal_indices = model.forward_logits(
        fen, "1200_1399", "blitz", legal_moves
    )

    # Hash fallback may return a logit if slot is available
    # Just verify it doesn't crash
    assert isinstance(legal_logits, torch.Tensor)


def test_baseline_policy_v1_get_move_index_hash_conflict() -> None:
    """Test get_move_index when hash conflicts occur."""
    model = BaselinePolicyV1(move_vocab_size=2)
    model.eval()

    # Fill vocabulary with specific moves
    model.add_move_to_vocab("e2e4")
    model.add_move_to_vocab("d2d4")

    # Try to get index for a move that hashes to an occupied slot
    # This tests the conflict detection branch (line 180-182)
    move = "a1a2"

    # If hash conflicts with existing move, should return None
    idx = model.get_move_index(move)
    # Result depends on hash collision, but should not crash
    assert idx is None or (isinstance(idx, int) and 0 <= idx < model.move_vocab_size)


def test_baseline_policy_v1_forward_no_legal_moves_in_vocab() -> None:
    """Test forward when no legal moves are in vocabulary (hash conflicts)."""
    model = BaselinePolicyV1(move_vocab_size=2)
    model.eval()

    # Fill vocabulary with specific moves
    model.add_move_to_vocab("e2e4")
    model.add_move_to_vocab("d2d4")

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    # Use moves that hash to occupied slots (will return None from get_move_index)
    # This tests the empty legal_indices path (line 234-236)
    # We need moves that hash to the same slots as e2e4 and d2d4
    legal_moves = ["a1a2", "b1c3"]

    move_probs = model(fen, "1200_1399", "blitz", legal_moves)

    # If all moves hash to occupied slots, should return uniform distribution
    # Otherwise, some moves may get logits via hash fallback
    assert len(move_probs) == len(legal_moves)
    # Probabilities should sum to 1.0
    total = sum(move_probs.values())
    assert abs(total - 1.0) < 1e-6
    # All probabilities should be non-negative
    for prob in move_probs.values():
        assert prob >= 0.0
