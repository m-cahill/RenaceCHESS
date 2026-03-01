"""Shallow neural baseline model for human policy prediction (M08).

This module implements a minimal, interpretable baseline model that learns
to predict human move distributions from position features and conditioning.

LiveM01: Deterministic temperature scaling for skill-conditioned inference.
"""

import hashlib

import torch
import torch.nn as nn
from torch.nn import functional

# ─── Skill conditioning: deterministic temperature scaling (LiveM01) ──────────
# Higher temperature → flatter distribution (lower skill, more "random" play)
# Lower temperature  → sharper distribution (higher skill, more "focused" play)

_SKILL_TEMPERATURE_NAMED: dict[str, float] = {
    "beginner": 1.6,
    "intermediate": 1.2,
    "advanced": 0.9,
    "expert": 0.75,
    "master": 0.6,
}

_SKILL_TEMPERATURE_ELO: dict[str, float] = {
    "lt_800": 1.6,  # → beginner
    "800_999": 1.6,  # → beginner
    "1000_1199": 1.2,  # → intermediate
    "1200_1399": 1.2,  # → intermediate
    "1400_1599": 0.9,  # → advanced
    "1600_1799": 0.9,  # → advanced
    "1800_1999": 0.75,  # → expert
    "gte_1800": 0.75,  # → expert (legacy key)
    "gte_2000": 0.6,  # → master
}

_DEFAULT_TEMPERATURE = 1.6  # Unknown → beginner (safest default)


def temperature_for_skill(skill_id: str) -> float:
    """Return deterministic temperature for a skill identifier.

    Supports both named keys (beginner, intermediate, ...) and
    Elo-range keys (lt_800, 1200_1399, ...).

    Args:
        skill_id: Skill bucket identifier (named or Elo-range).

    Returns:
        Temperature scalar (> 0).
    """
    key = skill_id.lower().strip()
    if key in _SKILL_TEMPERATURE_NAMED:
        return _SKILL_TEMPERATURE_NAMED[key]
    if key in _SKILL_TEMPERATURE_ELO:
        return _SKILL_TEMPERATURE_ELO[key]
    return _DEFAULT_TEMPERATURE


class BaselinePolicyV1(nn.Module):
    """Shallow neural baseline for human policy prediction.

    Architecture:
    - Input: FEN encoding + conditioning features
    - Output: Probability distribution over legal moves
    - Conditioning: Skill bucket + time control class as categorical inputs

    This is a minimal baseline to prove learnability, not to achieve
    competitive strength.
    """

    def __init__(
        self,
        fen_vocab_size: int = 10000,  # Hash-based FEN vocabulary
        skill_bucket_vocab_size: int = 8,  # 7 buckets + unknown
        time_control_vocab_size: int = 5,  # bullet/blitz/rapid/classical/unknown
        move_vocab_size: int = 1000,  # Fixed vocabulary of most common UCI moves
        hidden_dim: int = 128,
    ) -> None:
        """Initialize baseline policy model.

        Args:
            fen_vocab_size: Size of FEN hash vocabulary
            skill_bucket_vocab_size: Number of skill bucket categories
            time_control_vocab_size: Number of time control categories
            move_vocab_size: Size of fixed move vocabulary
            hidden_dim: Hidden layer dimension
        """
        super().__init__()

        # Embedding layers
        self.fen_embedding = nn.Embedding(fen_vocab_size, hidden_dim // 2)
        self.skill_embedding = nn.Embedding(skill_bucket_vocab_size, hidden_dim // 4)
        self.time_control_embedding = nn.Embedding(time_control_vocab_size, hidden_dim // 4)

        # Combined feature dimension
        feature_dim = hidden_dim // 2 + hidden_dim // 4 + hidden_dim // 4

        # Shallow network
        self.fc1 = nn.Linear(feature_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, move_vocab_size)

        # Move vocabulary (UCI moves) - built during training
        self.move_vocab: dict[str, int] = {}
        self.move_vocab_inv: dict[int, str] = {}
        self.move_vocab_size = move_vocab_size

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
        # Map skill buckets to indices
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

    def add_move_to_vocab(self, move: str) -> int:
        """Add move to vocabulary if not present.

        Args:
            move: UCI move string

        Returns:
            Vocabulary index for this move
        """
        if move not in self.move_vocab:
            if len(self.move_vocab) >= self.move_vocab_size:
                # Vocabulary full: hash to existing slot
                hash_val = hash(move) % self.move_vocab_size
                return hash_val
            idx = len(self.move_vocab)
            self.move_vocab[move] = idx
            self.move_vocab_inv[idx] = move
            return idx
        return self.move_vocab[move]

    def get_move_index(self, move: str) -> int | None:
        """Get vocabulary index for move, or None if not in vocab.

        Args:
            move: UCI move string

        Returns:
            Vocabulary index or None
        """
        if move in self.move_vocab:
            return self.move_vocab[move]
        # Try hashing to vocab slot
        hash_val = hash(move) % self.move_vocab_size
        if hash_val in self.move_vocab_inv:
            # Slot occupied by different move - conflict
            return None
        return hash_val

    def forward_logits(
        self,
        fen: str,
        skill_bucket: str,
        time_control: str | None,
        legal_moves: list[str],
    ) -> tuple[torch.Tensor, list[str], list[int]]:
        """Forward pass returning logits (for training).

        Args:
            fen: FEN string
            skill_bucket: Skill bucket identifier
            time_control: Time control class or None
            legal_moves: List of legal UCI moves

        Returns:
            Tuple of (logits tensor for legal moves, legal moves list, legal indices)
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

        # Forward through network
        x = functional.relu(self.fc1(features))
        logits = self.fc2(x)  # Shape: [move_vocab_size]

        # Map legal moves to vocabulary indices
        legal_indices: list[int] = []
        legal_moves_filtered: list[str] = []

        for move in legal_moves:
            idx = self.get_move_index(move)
            if idx is not None:
                legal_indices.append(idx)
                legal_moves_filtered.append(move)

        if legal_indices:
            # Extract logits for legal moves
            legal_logits = logits[legal_indices]
            return legal_logits, legal_moves_filtered, legal_indices
        else:
            # No legal moves in vocabulary: return empty
            return torch.tensor([], dtype=torch.float32), [], []

    def forward(
        self,
        fen: str,
        skill_bucket: str,
        time_control: str | None,
        legal_moves: list[str],
    ) -> dict[str, float]:
        """Forward pass: predict move distribution.

        Args:
            fen: FEN string
            skill_bucket: Skill bucket identifier
            time_control: Time control class or None
            legal_moves: List of legal UCI moves

        Returns:
            Dictionary mapping UCI moves to probabilities
        """
        legal_logits, legal_moves_filtered, _ = self.forward_logits(
            fen, skill_bucket, time_control, legal_moves
        )

        move_probs: dict[str, float] = {}

        if len(legal_logits) > 0:
            # Temperature scaling on masked logits (LiveM01)
            temp = max(temperature_for_skill(skill_bucket), 1e-8)
            scaled_logits = legal_logits / temp

            # Softmax over temperature-scaled legal-move logits
            probs = functional.softmax(scaled_logits, dim=0)

            for i, move in enumerate(legal_moves_filtered):
                # Clamp to [0, 1] to prevent tiny negative values from floating point precision
                prob_value = float(probs[i].item())
                move_probs[move] = max(0.0, min(1.0, prob_value))

            # Handle moves not in vocabulary: assign uniform probability
            remaining_moves = [m for m in legal_moves if m not in move_probs]
            if remaining_moves:
                uniform_prob = (1.0 - sum(move_probs.values())) / len(remaining_moves)
                # Clamp uniform probability to [0, 1]
                uniform_prob = max(0.0, min(1.0, uniform_prob))
                for move in remaining_moves:
                    move_probs[move] = uniform_prob

            # Renormalize to ensure sum = 1.0
            total = sum(move_probs.values())
            if total > 0:
                for move in move_probs:
                    move_probs[move] /= total
                # Final clamp after renormalization to handle any remaining precision issues
                for move in move_probs:
                    move_probs[move] = max(0.0, min(1.0, move_probs[move]))
                # Final renormalization if clamping changed sum
                final_total = sum(move_probs.values())
                if final_total > 0:
                    for move in move_probs:
                        move_probs[move] /= final_total
        else:
            # No legal moves in vocabulary: uniform distribution
            move_probs = {
                move: 1.0 / len(legal_moves) if legal_moves else 0.0 for move in legal_moves
            }

        return move_probs
