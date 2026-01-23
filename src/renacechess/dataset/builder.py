"""Dataset builder for converting PGN files to JSONL shards."""

from datetime import datetime
from pathlib import Path

import chess
import chess.pgn

from renacechess.dataset.config import DatasetBuildConfig
from renacechess.dataset.split import compute_split_assignment
from renacechess.demo.pgn_overlay import generate_payload_from_board
from renacechess.determinism import canonical_json_dump, stable_hash


def build_dataset(config: DatasetBuildConfig, generated_at: datetime | None = None) -> None:
    """Build dataset from PGN files.

    Args:
        config: Build configuration.
        generated_at: Override generation timestamp (for testing).
    """
    # Create output directory
    config.output_dir.mkdir(parents=True, exist_ok=True)
    shards_dir = config.output_dir / "shards"
    shards_dir.mkdir(parents=True, exist_ok=True)

    # Collect all PGN files (sorted for determinism)
    pgn_files: list[Path] = []
    for pgn_path in sorted(config.pgn_paths):
        if pgn_path.is_file():
            pgn_files.append(pgn_path)
        elif pgn_path.is_dir():
            pgn_files.extend(sorted(pgn_path.glob("*.pgn")))

    if not pgn_files:
        raise ValueError(f"No PGN files found in {config.pgn_paths}")

    # Initialize counters
    games_processed = 0
    positions_processed = 0
    split_counts: dict[str, list[str]] = {"train": [], "val": [], "frozenEval": []}

    # Single shard for M01
    shard_id = "shard_000"
    shard_path = shards_dir / f"{shard_id}.jsonl"
    shard_records: list[dict] = []

    # Process all games deterministically
    for pgn_file in pgn_files:
        if config.max_games is not None and games_processed >= config.max_games:
            break

        with pgn_file.open() as f:
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

                        # Store record
                        shard_records.append(payload)
                        split_counts[split].append(record_key)
                        positions_processed += 1

                # Process positions after each move
                for chess_move in game.mainline_moves():
                    if (
                        config.max_positions is not None
                        and positions_processed >= config.max_positions
                    ):
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

                    # Store record
                    shard_records.append(payload)
                    split_counts[split].append(record_key)
                    positions_processed += 1

                if config.max_positions is not None and positions_processed >= config.max_positions:
                    break

    # Write shard JSONL file
    with shard_path.open("w", encoding="utf-8") as f:
        for record in shard_records:
            json_bytes = canonical_json_dump(record)
            json_str = json_bytes.decode("utf-8")
            f.write(json_str)
            f.write("\n")

    # Compute shard hash
    shard_content = shard_path.read_bytes()
    shard_hash = stable_hash(shard_content)

    # Generate manifest
    from renacechess.dataset.manifest import generate_manifest

    generate_manifest(
        config=config,
        shard_id=shard_id,
        shard_path=shard_path,
        shard_hash=shard_hash,
        split_counts=split_counts,
        generated_at=generated_at,
    )
