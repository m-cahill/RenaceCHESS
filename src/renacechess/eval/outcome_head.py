"""Outcome head provider for evaluation (M09)."""

import json
from pathlib import Path
from typing import Any

import torch

from renacechess.models.outcome_head_v1 import OutcomeHeadV1


class LearnedOutcomeHeadV1:
    """Learned outcome head provider (M09).

    Loads a trained OutcomeHeadV1 model and provides W/D/L predictions.
    """

    def __init__(self, model_path: Path, metadata_path: Path) -> None:
        """Initialize learned outcome head provider.

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
        self.model = OutcomeHeadV1()

        # Load weights
        self.model.load_state_dict(torch.load(model_path, map_location="cpu"))
        self.model.eval()

    def predict(self, record: dict[str, Any]) -> dict[str, float]:
        """Predict W/D/L probabilities for a given position record.

        Args:
            record: Dataset record (Context Bridge payload dict).

        Returns:
            Dictionary with keys 'w', 'd', 'l' (win, draw, loss probabilities)
        """
        position = record["position"]
        conditioning = record["conditioning"]

        fen = position["fen"]
        skill_bucket = conditioning.get("skillBucket", "unknown")
        time_control = conditioning.get("timeControlClass")

        # Get predictions
        with torch.no_grad():
            wdl_probs: dict[str, float] = self.model(fen, skill_bucket, time_control)

        return wdl_probs

