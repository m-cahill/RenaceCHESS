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

