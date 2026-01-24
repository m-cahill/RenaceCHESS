"""Tests for M08 learned policy provider."""

import json
import tempfile
from pathlib import Path

import torch

from renacechess.contracts.models import PolicyMove
from renacechess.eval.learned_policy import LearnedHumanPolicyV1
from renacechess.models.baseline_v1 import BaselinePolicyV1


def test_learned_policy_v1_initialization(tmp_path: Path) -> None:
    """Test learned policy provider initialization."""
    # Create a minimal model
    model = BaselinePolicyV1(move_vocab_size=10)
    model.add_move_to_vocab("e2e4")
    model.add_move_to_vocab("d2d4")

    # Save model
    model_path = tmp_path / "model.pt"
    torch.save(model.state_dict(), model_path)

    # Save metadata
    metadata = {
        "model_type": "BaselinePolicyV1",
        "move_vocab_size": 10,
        "move_vocab": ["e2e4", "d2d4"],
    }
    metadata_path = tmp_path / "model_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f)

    # Load policy
    policy = LearnedHumanPolicyV1(model_path, metadata_path)

    assert policy.model_path == model_path
    assert policy.metadata_path == metadata_path
    assert policy.metadata["model_type"] == "BaselinePolicyV1"


def test_learned_policy_v1_predict(tmp_path: Path) -> None:
    """Test learned policy prediction."""
    # Create a minimal model
    model = BaselinePolicyV1(move_vocab_size=10)
    model.add_move_to_vocab("e2e4")
    model.add_move_to_vocab("d2d4")

    # Save model
    model_path = tmp_path / "model.pt"
    torch.save(model.state_dict(), model_path)

    # Save metadata
    metadata = {
        "model_type": "BaselinePolicyV1",
        "move_vocab_size": 10,
        "move_vocab": ["e2e4", "d2d4"],
    }
    metadata_path = tmp_path / "model_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f)

    # Load policy
    policy = LearnedHumanPolicyV1(model_path, metadata_path)

    # Create test record
    record = {
        "position": {
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "legalMoves": ["e2e4", "d2d4", "g1f3"],
        },
        "conditioning": {
            "skillBucket": "1200_1399",
            "timeControlClass": "blitz",
        },
    }

    # Predict
    moves = policy.predict(record)

    # Should return PolicyMove objects
    assert len(moves) > 0
    assert all(isinstance(m, PolicyMove) for m in moves)

    # Should be sorted by probability (descending)
    for i in range(len(moves) - 1):
        assert moves[i].p >= moves[i + 1].p

    # Probabilities should sum to approximately 1.0
    total = sum(m.p for m in moves)
    assert abs(total - 1.0) < 1e-5


def test_learned_policy_v1_empty_legal_moves(tmp_path: Path) -> None:
    """Test learned policy with empty legal moves."""
    # Create a minimal model
    model = BaselinePolicyV1(move_vocab_size=10)

    # Save model
    model_path = tmp_path / "model.pt"
    torch.save(model.state_dict(), model_path)

    # Save metadata
    metadata = {
        "model_type": "BaselinePolicyV1",
        "move_vocab_size": 10,
        "move_vocab": [],
    }
    metadata_path = tmp_path / "model_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f)

    # Load policy
    policy = LearnedHumanPolicyV1(model_path, metadata_path)

    # Create test record with no legal moves
    record = {
        "position": {
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "legalMoves": [],
        },
        "conditioning": {
            "skillBucket": "1200_1399",
            "timeControlClass": "blitz",
        },
    }

    # Predict
    moves = policy.predict(record)

    assert len(moves) == 0

