"""CLI entry point for RenaceCHESS."""

import argparse
import sys
from pathlib import Path

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
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
