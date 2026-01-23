"""Dataset builder for converting PGN files to JSONL shards."""

from datetime import datetime
from pathlib import Path

import chess
import chess.pgn

from renacechess.dataset.config import DatasetBuildConfig
from renacechess.dataset.receipt_reader import compute_pgn_digest, get_pgn_path_from_receipt
from renacechess.dataset.split import compute_split_assignment
from renacechess.demo.pgn_overlay import generate_payload_from_board
from renacechess.determinism import canonical_hash, canonical_json_dump, stable_hash


class ShardWriter:
    """Helper class for writing records to shards with size limits."""

    def __init__(self, shards_dir: Path, shard_size: int) -> None:
        """Initialize shard writer.

        Args:
            shards_dir: Directory for shard files.
            shard_size: Maximum records per shard.
        """
        self.shards_dir = shards_dir
        self.shard_size = shard_size
        self.current_shard_index = 0
        self.current_shard_records = 0
        self.current_shard_file = None
        self.shard_info: list[tuple[str, Path, int]] = []  # (shard_id, path, record_count)
        self.shard_splits: dict[str, set[str]] = {}  # shard_id -> set of split names

    def _get_shard_id(self, index: int) -> str:
        """Get shard ID for given index."""
        return f"shard_{index:03d}"

    def _open_new_shard(self) -> None:
        """Open a new shard file."""
        if self.current_shard_file is not None:
            self.current_shard_file.close()

        shard_id = self._get_shard_id(self.current_shard_index)
        shard_path = self.shards_dir / f"{shard_id}.jsonl"
        self.current_shard_file = shard_path.open("w", encoding="utf-8")
        self.current_shard_records = 0
        self.shard_info.append((shard_id, shard_path, 0))

    def write_record(self, record: dict, split: str) -> None:
        """Write a record to current shard, rolling to next shard if needed.

        Args:
            record: Record dict to write.
            split: Split name (train, val, or frozenEval) for this record.
        """
        if self.current_shard_file is None or self.current_shard_records >= self.shard_size:
            self._open_new_shard()
            # After _open_new_shard(), current_shard_file is guaranteed to be set
            assert self.current_shard_file is not None

        json_bytes = canonical_json_dump(record)
        json_str = json_bytes.decode("utf-8")
        self.current_shard_file.write(json_str)
        self.current_shard_file.write("\n")

        self.current_shard_records += 1
        # Update record count in shard_info
        shard_id, shard_path, _ = self.shard_info[-1]
        self.shard_info[-1] = (shard_id, shard_path, self.current_shard_records)

        # Track which splits this shard contains
        if shard_id not in self.shard_splits:
            self.shard_splits[shard_id] = set()
        self.shard_splits[shard_id].add(split)

    def close(self) -> None:
        """Close current shard file."""
        if self.current_shard_file is not None:
            self.current_shard_file.close()
            self.current_shard_file = None

    def get_shard_info(self) -> list[tuple[str, Path, int]]:
        """Get list of (shard_id, path, record_count) for all shards."""
        return self.shard_info.copy()

    def get_shard_splits(self) -> dict[str, set[str]]:
        """Get dictionary mapping shard_id to set of split names."""
        return self.shard_splits.copy()


def _collect_pgn_files_from_paths(pgn_paths: list[Path]) -> list[Path]:
    """Collect all PGN files from paths (files or directories).

    Args:
        pgn_paths: List of PGN file paths or directories.

    Returns:
        Sorted list of PGN file paths.
    """
    pgn_files: list[Path] = []
    for pgn_path in sorted(pgn_paths):
        if pgn_path.is_file():
            pgn_files.append(pgn_path)
        elif pgn_path.is_dir():
            pgn_files.extend(sorted(pgn_path.glob("*.pgn")))

    if not pgn_files:
        raise ValueError(f"No PGN files found in {pgn_paths}")

    return pgn_files


def _collect_pgn_files_from_receipts(
    receipt_paths: list[Path], cache_dir: Path | None = None
) -> list[tuple[Path, str, Path]]:
    """Collect PGN files from receipt paths.

    Args:
        receipt_paths: List of receipt file paths.
        cache_dir: Optional cache directory for resolving relative paths.

    Returns:
        List of (pgn_path, digest, receipt_path) tuples, sorted by receipt path.
    """
    pgn_info: list[tuple[Path, str, Path]] = []
    for receipt_path in sorted(receipt_paths):
        pgn_path, digest = get_pgn_path_from_receipt(receipt_path, cache_dir)
        pgn_info.append((pgn_path, digest, receipt_path))

    if not pgn_info:
        raise ValueError(f"No valid PGN files found from receipts {receipt_paths}")

    return pgn_info


def _process_pgn_file(
    pgn_path: Path,
    config: DatasetBuildConfig,
    shard_writer: ShardWriter,
    split_counts: dict[str, list[str]],
    generated_at: datetime | None,
    games_processed: int,
    positions_processed: int,
) -> tuple[int, int]:
    """Process a single PGN file and write records to shards.

    Args:
        pgn_path: Path to PGN file.
        config: Build configuration.
        shard_writer: Shard writer instance.
        split_counts: Dictionary to accumulate split assignments.
        generated_at: Override generation timestamp (for testing).
        games_processed: Current count of games processed.
        positions_processed: Current count of positions processed.

    Returns:
        Tuple of (new_games_processed, new_positions_processed).
    """
    with pgn_path.open() as f:
        while True:
            if config.max_games is not None and games_processed >= config.max_games:
                break

            game = chess.pgn.read_game(f)
            if game is None:
                break

            games_processed += 1

            # Process positions in this game
            board = game.board()
            ply = 0

            # Process initial position (ply 0) if within range
            if (config.start_ply is None or config.start_ply <= 0) and (
                config.end_ply is None or 0 < config.end_ply
            ):
                if config.max_positions is None or positions_processed < config.max_positions:
                    # Generate payload for initial position
                    if generated_at is None:
                        payload_generated_at = datetime.now()
                    else:
                        payload_generated_at = generated_at

                    payload = generate_payload_from_board(board, ply, payload_generated_at)

                    # Compute record key and split
                    fen = board.fen()
                    record_key = f"{fen}:{ply}"
                    split = compute_split_assignment(record_key)

                    # Write record to shard
                    shard_writer.write_record(payload, split)
                    split_counts[split].append(record_key)
                    positions_processed += 1

            # Process positions after each move
            for chess_move in game.mainline_moves():
                if config.max_positions is not None and positions_processed >= config.max_positions:
                    break

                # Advance board first
                board.push(chess_move)
                ply += 1

                # Check if we should process this position
                if config.start_ply is not None and ply < config.start_ply:
                    continue

                if config.end_ply is not None and ply >= config.end_ply:
                    break

                # Generate payload for this position
                if generated_at is None:
                    payload_generated_at = datetime.now()
                else:
                    payload_generated_at = generated_at

                payload = generate_payload_from_board(board, ply, payload_generated_at)

                # Compute record key and split
                fen = board.fen()
                record_key = f"{fen}:{ply}"
                split = compute_split_assignment(record_key)

                # Write record to shard
                shard_writer.write_record(payload, split)
                split_counts[split].append(record_key)
                positions_processed += 1

            if config.max_positions is not None and positions_processed >= config.max_positions:
                break

    return games_processed, positions_processed


def build_dataset(config: DatasetBuildConfig, generated_at: datetime | None = None) -> None:
    """Build dataset from PGN files or ingest receipts.

    Args:
        config: Build configuration.
        generated_at: Override generation timestamp (for testing).
    """
    # Create output directory
    config.output_dir.mkdir(parents=True, exist_ok=True)
    shards_dir = config.output_dir / "shards"
    shards_dir.mkdir(parents=True, exist_ok=True)

    # Initialize shard writer
    shard_writer = ShardWriter(shards_dir, config.shard_size)

    # Collect input sources and compute digests
    input_digests: list[str] = []
    input_info: list[tuple[str, str | None, str | None]] = []  # (type, digest, path)

    # Initialize counters and split tracking
    games_processed = 0
    positions_processed = 0
    split_counts: dict[str, list[str]] = {"train": [], "val": [], "frozenEval": []}

    if config.pgn_paths is not None:
        # Process PGN files directly
        pgn_files = _collect_pgn_files_from_paths(config.pgn_paths)
        for pgn_path in pgn_files:
            digest = compute_pgn_digest(pgn_path)
            input_digests.append(digest)
            input_info.append(("pgn_file", digest, str(pgn_path.resolve())))

        # Process all PGN files
        for pgn_file in pgn_files:
            games_processed, positions_processed = _process_pgn_file(
                pgn_file,
                config,
                shard_writer,
                split_counts,
                generated_at,
                games_processed,
                positions_processed,
            )

    elif config.receipt_paths is not None:
        # Process receipts
        pgn_info_list = _collect_pgn_files_from_receipts(config.receipt_paths, config.cache_dir)

        for pgn_path, digest, receipt_path in pgn_info_list:
            input_digests.append(digest)
            input_info.append(("ingest_receipt", digest, str(receipt_path.resolve())))

        # Process all PGN files from receipts

        for pgn_path, _, receipt_path in pgn_info_list:
            games_processed, positions_processed = _process_pgn_file(
                pgn_path,
                config,
                shard_writer,
                split_counts,
                generated_at,
                games_processed,
                positions_processed,
            )

    # Close shard writer
    shard_writer.close()

    # Compute shard hashes
    shard_refs: list[tuple[str, Path, str, int]] = []  # (shard_id, path, hash, records)
    for shard_id, shard_path, record_count in shard_writer.get_shard_info():
        shard_content = shard_path.read_bytes()
        shard_hash = stable_hash(shard_content)
        shard_refs.append((shard_id, shard_path, shard_hash, record_count))

    # Generate manifest v2
    from renacechess.dataset.manifest import generate_manifest_v2

    shard_splits = shard_writer.get_shard_splits()
    generate_manifest_v2(
        config=config,
        shard_refs=shard_refs,
        split_counts=split_counts,
        shard_splits=shard_splits,
        input_info=input_info,
        generated_at=generated_at,
    )
