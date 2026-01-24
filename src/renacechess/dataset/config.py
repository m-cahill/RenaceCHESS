"""Configuration for dataset building."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatasetBuildConfig:
    """Configuration for dataset build process."""

    output_dir: Path
    shard_size: int = 10000
    max_games: int | None = None
    max_positions: int | None = None
    start_ply: int | None = None
    end_ply: int | None = None
    # Input sources (mutually exclusive)
    pgn_paths: list[Path] | None = None
    receipt_paths: list[Path] | None = None
    cache_dir: Path | None = None  # For resolving relative receipt paths

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.shard_size < 1:
            raise ValueError(f"shard_size must be >= 1, got {self.shard_size}")
        if self.shard_size < 100:
            import warnings

            warnings.warn(
                f"shard_size ({self.shard_size}) is very small. Recommended minimum: 100.",
                UserWarning,
            )
        if self.pgn_paths is not None and self.receipt_paths is not None:
            raise ValueError("Cannot specify both pgn_paths and receipt_paths (mutually exclusive)")
        if self.pgn_paths is None and self.receipt_paths is None:
            raise ValueError("Must specify either pgn_paths or receipt_paths")

    def to_dict(self) -> dict:
        """Convert config to dictionary for hashing.

        Returns:
            Dictionary representation suitable for canonical JSON hashing.
        """
        result: dict = {
            "shard_size": self.shard_size,
            "max_games": self.max_games,
            "max_positions": self.max_positions,
            "start_ply": self.start_ply,
            "end_ply": self.end_ply,
        }
        if self.pgn_paths is not None:
            result["pgn_paths"] = sorted(str(p.resolve()) for p in self.pgn_paths)
        if self.receipt_paths is not None:
            result["receipt_paths"] = sorted(str(p.resolve()) for p in self.receipt_paths)
        return result

    def to_assembly_config_dict(self) -> dict:
        """Convert to assembly config dict for manifest v2.

        Returns:
            Dictionary matching DatasetManifestAssemblyConfigV2 structure.
        """
        return {
            "shardSize": self.shard_size,
            "maxGames": self.max_games,
            "maxPositions": self.max_positions,
            "startPly": self.start_ply,
            "endPly": self.end_ply,
        }
