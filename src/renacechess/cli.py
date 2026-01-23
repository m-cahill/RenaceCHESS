"""CLI entry point for RenaceCHESS."""

import argparse
import sys
from pathlib import Path

from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig
from renacechess.demo.pgn_overlay import generate_demo_payload
from renacechess.determinism import canonical_json_dump


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="RenaceCHESS — Cognitive Human Evaluation & Skill Simulation"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Generate demo payload from PGN")
    demo_parser.add_argument(
        "--pgn",
        type=Path,
        required=True,
        help="Path to PGN file",
    )
    demo_parser.add_argument(
        "--out",
        type=Path,
        help="Output JSON file path (default: stdout)",
    )
    demo_parser.add_argument(
        "--ply",
        type=int,
        default=6,
        help="Target ply number (default: 6)",
    )

    # Dataset build command
    dataset_parser = subparsers.add_parser("dataset", help="Build dataset from PGN files")
    dataset_subparsers = dataset_parser.add_subparsers(dest="dataset_command")

    build_parser = dataset_subparsers.add_parser("build", help="Build dataset shards")
    build_parser.add_argument(
        "--pgn",
        type=Path,
        required=True,
        action="append",
        help="Path to PGN file or directory (can be specified multiple times)",
    )
    build_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory for shards and manifest",
    )
    build_parser.add_argument(
        "--max-games",
        type=int,
        help="Maximum number of games to process (global limit)",
    )
    build_parser.add_argument(
        "--max-positions",
        type=int,
        help="Maximum number of positions to process (global limit)",
    )
    build_parser.add_argument(
        "--start-ply",
        type=int,
        help="Start processing from this ply number (inclusive)",
    )
    build_parser.add_argument(
        "--end-ply",
        type=int,
        help="Stop processing at this ply number (exclusive)",
    )

    args = parser.parse_args()

    if args.command == "demo":
        try:
            payload = generate_demo_payload(args.pgn, ply=args.ply)
            json_bytes = canonical_json_dump(payload)
            json_str = json_bytes.decode("utf-8")

            if args.out:
                args.out.write_text(json_str, encoding="utf-8")
                print(f"Demo payload written to {args.out}", file=sys.stderr)
            else:
                print(json_str)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "dataset":
        if args.dataset_command == "build":
            try:
                config = DatasetBuildConfig(
                    pgn_paths=args.pgn,
                    output_dir=args.out,
                    max_games=args.max_games,
                    max_positions=args.max_positions,
                    start_ply=args.start_ply,
                    end_ply=args.end_ply,
                )
                build_dataset(config)
                print(f"Dataset built successfully in {args.out}", file=sys.stderr)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            dataset_parser.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
