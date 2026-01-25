"""Outcome head model for human W/D/L prediction (M09).

This module implements a minimal, interpretable linear model that learns
to predict human win/draw/loss probabilities from position features and conditioning.
"""

import hashlib
from typing import Any

import torch
import torch.nn as nn
from torch.nn import functional


class OutcomeHeadV1(nn.Module):
    """Single linear layer for human outcome (W/D/L) prediction.

    Architecture:
    - Input: Same feature representation as M08 policy baseline
    - Output: 3 logits (Win, Draw, Loss)
    - Conditioning: Skill bucket + time control class as categorical inputs

    This is a minimal baseline to prove learnability, not to achieve
    competitive strength.
    """

    def __init__(
        self,
        fen_vocab_size: int = 10000,  # Hash-based FEN vocabulary
        skill_bucket_vocab_size: int = 8,  # 7 buckets + unknown
        time_control_vocab_size: int = 5,  # bullet/blitz/rapid/classical/unknown
        hidden_dim: int = 128,
    ) -> None:
        """Initialize outcome head model.

        Args:
            fen_vocab_size: Size of FEN hash vocabulary
            skill_bucket_vocab_size: Number of skill bucket categories
            time_control_vocab_size: Number of time control categories
            hidden_dim: Hidden dimension for embeddings (must match M08 policy baseline)
        """
        super().__init__()

        # Embedding layers (same as M08 policy baseline)
        self.fen_embedding = nn.Embedding(fen_vocab_size, hidden_dim // 2)
        self.skill_embedding = nn.Embedding(skill_bucket_vocab_size, hidden_dim // 4)
        self.time_control_embedding = nn.Embedding(time_control_vocab_size, hidden_dim // 4)

        # Combined feature dimension
        feature_dim = hidden_dim // 2 + hidden_dim // 4 + hidden_dim // 4

        # Single linear layer (logistic regression) -> 3 logits (W/D/L)
        self.fc_outcome = nn.Linear(feature_dim, 3)

    def _hash_fen(self, fen: str) -> int:
        """Hash FEN to vocabulary index.

        Args:
            fen: FEN string

        Returns:
            Vocabulary index (0 to fen_vocab_size-1)
        """
        hash_bytes = hashlib.sha256(fen.encode("utf-8")).digest()
        hash_int = int.from_bytes(hash_bytes[:4], byteorder="big")
        return hash_int % self.fen_embedding.num_embeddings

    def _encode_skill_bucket(self, skill_bucket: str) -> int:
        """Encode skill bucket to index.

        Args:
            skill_bucket: Skill bucket string (e.g., '1200-1400' or '1200_1399')

        Returns:
            Bucket index (0-7)
        """
        # Map skill buckets to indices (same as M08)
        bucket_map = {
            "lt_800": 0,
            "800_999": 1,
            "1000_1199": 2,
            "1200_1399": 3,
            "1400_1599": 4,
            "1600_1799": 5,
            "gte_1800": 6,
            "unknown": 7,
        }

        # Try direct match first
        if skill_bucket in bucket_map:
            return bucket_map[skill_bucket]

        # Try legacy format (e.g., "1200-1400")
        if "-" in skill_bucket:
            parts = skill_bucket.split("-")
            if len(parts) == 2:
                try:
                    low = int(parts[0])
                    if low < 800:
                        return 0
                    elif low < 1000:
                        return 1
                    elif low < 1200:
                        return 2
                    elif low < 1400:
                        return 3
                    elif low < 1600:
                        return 4
                    elif low < 1800:
                        return 5
                    else:
                        return 6
                except ValueError:
                    pass

        return 7  # unknown

    def _encode_time_control(self, time_control: str | None) -> int:
        """Encode time control to index.

        Args:
            time_control: Time control class or None

        Returns:
            Time control index (0-4)
        """
        if time_control is None:
            return 4  # unknown

        control_map = {
            "bullet": 0,
            "blitz": 1,
            "rapid": 2,
            "classical": 3,
            "unknown": 4,
        }

        return control_map.get(time_control, 4)

    def forward_logits(
        self,
        fen: str,
        skill_bucket: str,
        time_control: str | None,
    ) -> torch.Tensor:
        """Forward pass returning logits (for training).

        Args:
            fen: FEN string
            skill_bucket: Skill bucket identifier
            time_control: Time control class or None

        Returns:
            Tensor of shape [3] with logits for [Win, Draw, Loss]
        """
        # Encode inputs
        fen_idx = self._hash_fen(fen)
        skill_idx = self._encode_skill_bucket(skill_bucket)
        time_idx = self._encode_time_control(time_control)

        # Embeddings
        fen_emb = self.fen_embedding(torch.tensor(fen_idx, dtype=torch.long))
        skill_emb = self.skill_embedding(torch.tensor(skill_idx, dtype=torch.long))
        time_emb = self.time_control_embedding(torch.tensor(time_idx, dtype=torch.long))

        # Concatenate features
        features = torch.cat([fen_emb, skill_emb, time_emb])

        # Single linear layer -> 3 logits (W/D/L)
        logits: torch.Tensor = self.fc_outcome(features)  # Shape: [3]

        return logits

    def forward(
        self,
        fen: str,
        skill_bucket: str,
        time_control: str | None,
    ) -> dict[str, float]:
        """Forward pass: predict W/D/L probabilities.

        Args:
            fen: FEN string
            skill_bucket: Skill bucket identifier
            time_control: Time control class or None

        Returns:
            Dictionary with keys 'w', 'd', 'l' (win, draw, loss probabilities)
        """
        logits = self.forward_logits(fen, skill_bucket, time_control)

        # Softmax over 3 classes (W/D/L)
        probs = functional.softmax(logits, dim=0)

        # Clamp to [0, 1] to handle floating-point precision
        w = max(0.0, min(1.0, float(probs[0].item())))
        d = max(0.0, min(1.0, float(probs[1].item())))
        loss_prob = max(0.0, min(1.0, float(probs[2].item())))

        # Renormalize to ensure sum = 1.0
        total = w + d + loss_prob
        if total > 0:
            w /= total
            d /= total
            loss_prob /= total

        return {"w": w, "d": d, "l": loss_prob}
