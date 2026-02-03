"""Training infrastructure for outcome head models (M09)."""

import json
import random
from pathlib import Path
from typing import Any, Literal

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from renacechess.contracts.models import DatasetManifestV2
from renacechess.frozen_eval.compat import load_frozen_eval_record_keys
from renacechess.models.outcome_head_v1 import OutcomeHeadV1


def _get_game_result_from_record(
    record: dict[str, Any],
) -> Literal["win", "draw", "loss"] | None:
    """Extract game result from record (from mover's perspective).

    Args:
        record: Dataset record

    Returns:
        'win', 'draw', 'loss', or None if not available
    """
    # Check if game result is stored in meta
    meta = record.get("meta", {})
    if isinstance(meta, dict):
        game_result = meta.get("gameResult")
        if isinstance(game_result, str) and game_result in ("win", "draw", "loss"):
            return game_result  # type: ignore[return-value]

    # Check if game result is at top level
    game_result = record.get("gameResult")
    if isinstance(game_result, str) and game_result in ("win", "draw", "loss"):
        return game_result  # type: ignore[return-value]

    return None


def _map_pgn_result_to_wdl(
    pgn_result: str, side_to_move: str
) -> Literal["win", "draw", "loss"] | None:
    """Map PGN result string to W/D/L from mover's perspective.

    Args:
        pgn_result: PGN result string ('1-0', '0-1', '1/2-1/2', '*')
        side_to_move: 'white' or 'black'

    Returns:
        'win', 'draw', 'loss', or None if result is unknown
    """
    if pgn_result == "1-0":
        return "win" if side_to_move == "white" else "loss"
    elif pgn_result == "0-1":
        return "loss" if side_to_move == "white" else "win"
    elif pgn_result == "1/2-1/2":
        return "draw"
    else:
        return None  # Unknown result ('*' or other)


class OutcomeDataset(Dataset):
    """Dataset for outcome head training from JSONL shards."""

    def __init__(
        self,
        manifest_path: Path,
        frozen_eval_manifest_path: Path | None = None,
        seed: int = 42,
    ) -> None:
        """Initialize outcome dataset.

        Args:
            manifest_path: Path to dataset manifest v2
            frozen_eval_manifest_path: Path to frozen eval manifest (to exclude from training)
            seed: Random seed for determinism
        """
        self.manifest_path = manifest_path
        self.manifest_dir = manifest_path.parent
        self.seed = seed

        # Load manifest
        manifest_dict = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.manifest = DatasetManifestV2.model_validate(manifest_dict)

        # Load frozen eval record keys if provided (supports V1 and V2 manifests)
        self.frozen_eval_keys: set[str] = set()
        if frozen_eval_manifest_path is not None:
            frozen_record_keys = load_frozen_eval_record_keys(frozen_eval_manifest_path)
            self.frozen_eval_keys = set(frozen_record_keys.keys)

        # Load all training records
        self.records: list[dict[str, Any]] = []
        self._load_records()

    def _load_records(self) -> None:
        """Load training records from shards (excluding frozen eval)."""
        # Process shards in deterministic order
        for shard_ref in self.manifest.shard_refs:
            shard_path = self.manifest_dir / shard_ref.path
            if not shard_path.exists():
                continue

            # Process shard line-by-line
            with shard_path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    record = json.loads(line)

                    # Skip if in frozen eval
                    record_key = record.get("meta", {}).get("inputHash", "")
                    if record_key in self.frozen_eval_keys:
                        continue

                    # Skip if not in train split
                    split = self._get_record_split(record_key)
                    if split != "train":
                        continue

                    # Skip if no game result available
                    game_result = _get_game_result_from_record(record)
                    if game_result is None:
                        continue

                    self.records.append(record)

    def _get_record_split(self, record_key: str) -> str:
        """Get split assignment for record key.

        Args:
            record_key: Record key (e.g., "fen:ply")

        Returns:
            Split name ("train", "val", or "frozenEval")
        """
        # Use same logic as dataset builder
        import hashlib

        hash_bytes = hashlib.sha256(record_key.encode("utf-8")).digest()
        split_bucket = int.from_bytes(hash_bytes[:8], byteorder="big") % 100

        if split_bucket < 5:
            return "frozenEval"
        elif split_bucket < 15:
            return "val"
        else:
            return "train"

    def __len__(self) -> int:
        """Return dataset size."""
        return len(self.records)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        """Get training sample.

        Args:
            idx: Sample index

        Returns:
            Dictionary with features and label
        """
        record = self.records[idx]

        position = record["position"]
        conditioning = record["conditioning"]
        game_result = _get_game_result_from_record(record)

        # Map game result to class index: win=0, draw=1, loss=2
        if game_result == "win":
            outcome_class = 0
        elif game_result == "draw":
            outcome_class = 1
        elif game_result == "loss":
            outcome_class = 2
        else:
            raise ValueError(f"Invalid game result: {game_result}")

        return {
            "fen": position["fen"],
            "skill_bucket": conditioning.get("skillBucket", "unknown"),
            "time_control": conditioning.get("timeControlClass"),
            "outcome_class": outcome_class,
        }


def train_outcome_head(
    manifest_path: Path,
    frozen_eval_manifest_path: Path | None,
    output_dir: Path,
    epochs: int = 10,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    seed: int = 42,
) -> Path:
    """Train outcome head model.

    Args:
        manifest_path: Path to dataset manifest v2
        frozen_eval_manifest_path: Path to frozen eval manifest (to exclude)
        output_dir: Directory to save model and metadata
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        seed: Random seed for determinism

    Returns:
        Path to saved model file
    """
    # Set random seeds for determinism
    torch.manual_seed(seed)
    random.seed(seed)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset
    dataset = OutcomeDataset(manifest_path, frozen_eval_manifest_path, seed=seed)

    if len(dataset) == 0:
        raise ValueError("No training records found with game results")

    # Initialize model
    model = OutcomeHeadV1()

    # Create data loader (deterministic: no shuffle)
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False)

    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # Training loop
    model.train()
    for epoch in range(epochs):
        total_loss = 0.0
        num_samples = 0

        for batch in dataloader:
            # Extract features
            fen = batch["fen"][0]
            skill_bucket = batch["skill_bucket"][0]
            time_control = batch["time_control"][0]
            outcome_class = batch["outcome_class"][0]

            # Forward pass (get logits)
            logits = model.forward_logits(fen, skill_bucket, time_control)

            # Compute loss (cross-entropy)
            target = torch.tensor(outcome_class, dtype=torch.long)
            loss = criterion(logits.unsqueeze(0), target.unsqueeze(0))

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_samples += 1

        avg_loss = total_loss / num_samples if num_samples > 0 else 0.0
        print(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.4f}")

    # Save model
    model_path = output_dir / "outcome_head_v1.pt"
    torch.save(model.state_dict(), model_path)

    # Save metadata
    metadata = {
        "model_type": "OutcomeHeadV1",
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "seed": seed,
        "manifest_path": str(manifest_path),
        "frozen_eval_manifest_path": (
            str(frozen_eval_manifest_path) if frozen_eval_manifest_path else None
        ),
        "loss_function": "CrossEntropyLoss",
    }

    metadata_path = output_dir / "outcome_head_v1_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)

    return model_path
