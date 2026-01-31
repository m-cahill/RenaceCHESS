"""Training infrastructure for learned policy models (M08)."""

import json
import random
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from renacechess.contracts.models import DatasetManifestV2, FrozenEvalManifestV1
from renacechess.models.baseline_v1 import BaselinePolicyV1


class PolicyDataset(Dataset):
    """Dataset for policy training from JSONL shards."""

    def __init__(
        self,
        manifest_path: Path,
        frozen_eval_manifest_path: Path | None = None,
        seed: int = 42,
    ) -> None:
        """Initialize policy dataset.

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

        # Load frozen eval manifest if provided
        self.frozen_eval_keys: set[str] = set()
        if frozen_eval_manifest_path is not None:
            frozen_dict = json.loads(frozen_eval_manifest_path.read_text(encoding="utf-8"))
            frozen_manifest = FrozenEvalManifestV1.model_validate(frozen_dict)
            self.frozen_eval_keys = {record.record_key for record in frozen_manifest.records}

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

                    # Skip if no chosenMove (not labeled)
                    if "chosenMove" not in record or record["chosenMove"] is None:
                        continue

                    # Skip if in frozen eval
                    record_key = record.get("meta", {}).get("inputHash", "")
                    if record_key in self.frozen_eval_keys:
                        continue

                    # Skip if not in train split
                    # (We could also include val, but for M08 we'll use train only)
                    split = self._get_record_split(record_key)
                    if split != "train":
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
        chosen_move = record["chosenMove"]["uci"]

        return {
            "fen": position["fen"],
            "skill_bucket": conditioning.get("skillBucket", "unknown"),
            "time_control": conditioning.get("timeControlClass"),
            "legal_moves": position["legalMoves"],
            "chosen_move": chosen_move,
        }


def train_baseline_policy(
    manifest_path: Path,
    frozen_eval_manifest_path: Path | None,
    output_dir: Path,
    epochs: int = 10,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    seed: int = 42,
) -> Path:
    """Train baseline policy model.

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
    dataset = PolicyDataset(manifest_path, frozen_eval_manifest_path, seed=seed)

    if len(dataset) == 0:
        raise ValueError("No training records found")

    # Build move vocabulary from all training data
    move_vocab: set[str] = set()
    for i in range(len(dataset)):
        sample = dataset[i]
        legal_moves = sample["legal_moves"]
        move_vocab.update(legal_moves)
        move_vocab.add(sample["chosen_move"])

    move_vocab_size = min(1000, len(move_vocab))

    # Initialize model
    model = BaselinePolicyV1(move_vocab_size=move_vocab_size)

    # Build vocabulary in model
    for move in sorted(move_vocab)[:move_vocab_size]:
        model.add_move_to_vocab(move)

    # Create data loader
    # Note: For M08 minimal baseline, we'll use a simple approach
    # In production, you'd want proper batching, but for now we'll train one-by-one
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False)  # Deterministic: no shuffle

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
            legal_moves = batch["legal_moves"][0]
            chosen_move = batch["chosen_move"][0]

            # Forward pass (get logits)
            legal_logits, legal_moves_filtered, _ = model.forward_logits(
                fen, skill_bucket, time_control, legal_moves
            )

            if len(legal_logits) == 0:
                # No legal moves in vocabulary: skip
                continue

            # Find index of chosen move in legal moves
            try:
                target_idx = legal_moves_filtered.index(chosen_move)
            except ValueError:
                # Chosen move not in vocabulary: skip
                continue

            # Compute loss (cross-entropy)
            target = torch.tensor(target_idx, dtype=torch.long)
            loss = criterion(legal_logits.unsqueeze(0), target.unsqueeze(0))

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_samples += 1

        avg_loss = total_loss / num_samples if num_samples > 0 else 0.0
        print(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.4f}")

    # Save model
    model_path = output_dir / "model.pt"
    torch.save(model.state_dict(), model_path)

    # Save metadata
    metadata = {
        "model_type": "BaselinePolicyV1",
        "move_vocab_size": move_vocab_size,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "seed": seed,
        "manifest_path": str(manifest_path),
        "frozen_eval_manifest_path": (
            str(frozen_eval_manifest_path) if frozen_eval_manifest_path else None
        ),
        "move_vocab": list(model.move_vocab.keys()),
    }

    metadata_path = output_dir / "model_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)

    return model_path
