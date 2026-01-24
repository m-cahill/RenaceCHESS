"""Baseline policy providers for evaluation."""

import hashlib
import random
from pathlib import Path
from typing import Any

from renacechess.contracts.models import PolicyMove


class UniformRandomLegalPolicy:
    """Uniform random policy that selects from legal moves only.

    Uses deterministic seeded RNG for reproducibility.
    """

    def __init__(self, seed: int | None = None) -> None:
        """Initialize uniform random policy.

        Args:
            seed: Random seed for determinism. If None, uses system time.
        """
        self.seed = seed
        self._rng = random.Random(seed)

    def predict(self, record: dict) -> list[PolicyMove]:
        """Predict uniform random move from legal moves.

        Args:
            record: Dataset record (Context Bridge payload dict).

        Returns:
            Ranked list of PolicyMove objects (all moves have equal probability).
        """
        legal_moves = record["position"]["legalMoves"]
        if not legal_moves:
            return []

        # Shuffle deterministically (seed already set)
        moves_shuffled = legal_moves.copy()
        self._rng.shuffle(moves_shuffled)

        # Assign uniform probability
        prob = 1.0 / len(moves_shuffled)
        return [PolicyMove(uci=move, san=None, p=prob) for move in moves_shuffled]


class FirstLegalPolicy:
    """Simple deterministic baseline that always picks the first legal move."""

    def predict(self, record: dict) -> list[PolicyMove]:
        """Predict first legal move (deterministic).

        Args:
            record: Dataset record (Context Bridge payload dict).

        Returns:
            Ranked list with single PolicyMove (first legal move, probability 1.0).
        """
        legal_moves = record["position"]["legalMoves"]
        if not legal_moves:
            return []

        # Sort for determinism (legal moves should already be sorted, but ensure)
        sorted_moves = sorted(legal_moves)
        return [PolicyMove(uci=sorted_moves[0], san=None, p=1.0)]


def create_policy_provider(
    policy_id: str, seed: int | None = None, model_path: Path | None = None
) -> Any:
    """Create a policy provider by ID.

    Args:
        policy_id: Policy identifier (e.g., 'baseline.uniform_random', 'learned.v1').
        seed: Random seed for policies that use randomness.
        model_path: Path to trained model (required for learned policies).

    Returns:
        Policy provider instance.

    Raises:
        ValueError: If policy_id is unknown or model_path is missing for learned policies.
    """
    if policy_id == "baseline.uniform_random":
        return UniformRandomLegalPolicy(seed=seed)
    elif policy_id == "baseline.first_legal":
        return FirstLegalPolicy()
    elif policy_id == "learned.v1":
        if model_path is None:
            raise ValueError("model_path required for learned.v1 policy")
        from renacechess.eval.learned_policy import LearnedHumanPolicyV1

        # Metadata path is assumed to be next to model file
        metadata_path = model_path.parent / "model_metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Model metadata not found: {metadata_path}")
        return LearnedHumanPolicyV1(model_path, metadata_path)
    else:
        raise ValueError(f"Unknown policy ID: {policy_id}")


def compute_policy_seed(dataset_digest: str, policy_id: str, eval_config_hash: str) -> int:
    """Compute deterministic seed for policy from dataset and config.

    Args:
        dataset_digest: Dataset digest from manifest.
        policy_id: Policy identifier.
        eval_config_hash: Evaluation config hash.

    Returns:
        Integer seed for deterministic RNG.
    """
    seed_str = f"{dataset_digest}:{policy_id}:{eval_config_hash}"
    seed_bytes = seed_str.encode("utf-8")
    seed_hash = hashlib.sha256(seed_bytes).hexdigest()
    # Use first 8 hex digits as seed (fits in int32)
    return int(seed_hash[:8], 16)
