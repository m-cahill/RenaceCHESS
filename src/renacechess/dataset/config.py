"""Configuration for dataset building."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatasetBuildConfig:
    """Configuration for dataset build process."""

    pgn_paths: list[Path]
    output_dir: Path
    max_games: int | None = None
    max_positions: int | None = None
    start_ply: int | None = None
    end_ply: int | None = None

    def to_dict(self) -> dict:
        """Convert config to dictionary for hashing.

        Returns:
            Dictionary representation suitable for canonical JSON hashing.
        """
        return {
            "max_games": self.max_games,
            "max_positions": self.max_positions,
            "start_ply": self.start_ply,
            "end_ply": self.end_ply,
            "pgn_paths": sorted(str(p.resolve()) for p in self.pgn_paths),
        }

