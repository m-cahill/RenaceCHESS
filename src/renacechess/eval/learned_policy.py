"""Learned policy provider for evaluation (M08)."""

import json
from pathlib import Path
from typing import Any

import torch

from renacechess.contracts.models import PolicyMove
from renacechess.models.baseline_v1 import BaselinePolicyV1


class LearnedHumanPolicyV1:
    """Learned human policy provider (M08 baseline).

    Loads a trained BaselinePolicyV1 model and provides predictions
    via the PolicyProvider interface.
    """

    def __init__(self, model_path: Path, metadata_path: Path) -> None:
        """Initialize learned policy provider.

        Args:
            model_path: Path to saved model weights (.pt file)
            metadata_path: Path to model metadata JSON file
        """
        self.model_path = model_path
        self.metadata_path = metadata_path

        # Load metadata
        with metadata_path.open(encoding="utf-8") as f:
            self.metadata = json.load(f)

        # Initialize model
        move_vocab_size = self.metadata["move_vocab_size"]
        self.model = BaselinePolicyV1(move_vocab_size=move_vocab_size)

        # Load vocabulary
        move_vocab = self.metadata.get("move_vocab", [])
        for move in move_vocab:
            self.model.add_move_to_vocab(move)

        # Load weights
        self.model.load_state_dict(torch.load(model_path, map_location="cpu"))
        self.model.eval()

    def predict(self, record: dict) -> list[PolicyMove]:
        """Predict moves for a given position record.

        Args:
            record: Dataset record (Context Bridge payload dict).

        Returns:
            Ranked list of PolicyMove objects (sorted by probability, descending).
        """
        position = record["position"]
        conditioning = record["conditioning"]

        fen = position["fen"]
        legal_moves = position["legalMoves"]
        skill_bucket = conditioning.get("skillBucket", "unknown")
        time_control = conditioning.get("timeControlClass")

        # Get predictions
        with torch.no_grad():
            move_probs = self.model(fen, skill_bucket, time_control, legal_moves)

        # Convert to PolicyMove list, sorted by probability
        policy_moves = [
            PolicyMove(uci=move, san=None, p=prob)
            for move, prob in move_probs.items()
        ]
        policy_moves.sort(key=lambda x: x.p, reverse=True)

        return policy_moves

