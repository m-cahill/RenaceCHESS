"""CLI entry point for RenaceCHESS."""

import argparse
import sys
from pathlib import Path

from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig
from renacechess.demo.pgn_overlay import generate_demo_payload
from renacechess.determinism import canonical_json_dump
from renacechess.eval.report import build_eval_report, build_eval_report_v2, write_eval_report
from renacechess.eval.runner import run_evaluation, run_conditioned_evaluation
from renacechess.frozen_eval import generate_frozen_eval_manifest, write_frozen_eval_manifest
from renacechess.ingest.ingest import ingest_from_lichess, ingest_from_url


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

    build_parser = dataset_subparsers.add_parser(
        "build",
        help=(
            "Build dataset shards from PGN files or ingest receipts "
            "(receipts recommended for provenance)"
        ),
    )
    # Mutually exclusive input sources
    input_group = build_parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--pgn",
        type=Path,
        action="append",
        help=(
            "Path to PGN file or directory (can be specified multiple times). "
            "For backward compatibility."
        ),
    )
    input_group.add_argument(
        "--receipt",
        type=Path,
        action="append",
        help=(
            "Path to ingest receipt JSON file (can be specified multiple times). "
            "Recommended for auditable provenance."
        ),
    )
    build_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory for shards and manifest",
    )
    build_parser.add_argument(
        "--shard-size",
        type=int,
        default=10000,
        help="Maximum number of records per shard (default: 10000)",
    )
    build_parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Cache directory for resolving relative receipt paths (optional)",
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

    # Eval command
    eval_parser = subparsers.add_parser("eval", help="Evaluate policy providers over datasets")
    eval_subparsers = eval_parser.add_subparsers(dest="eval_command")

    run_parser = eval_subparsers.add_parser("run", help="Run evaluation over a dataset manifest")
    run_parser.add_argument(
        "--dataset-manifest",
        type=Path,
        required=True,
        help="Path to dataset manifest v2 (manifest.json)",
    )
    run_parser.add_argument(
        "--policy",
        type=str,
        required=True,
        help="Policy identifier (e.g., 'baseline.uniform_random', 'baseline.first_legal')",
    )
    run_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory (will write eval_report.json)",
    )
    run_parser.add_argument(
        "--max-records",
        type=int,
        help="Maximum number of records to evaluate (default: no limit)",
    )
    run_parser.add_argument(
        "--created-at",
        type=str,
        help="Override creation timestamp (ISO 8601 format, for testing only)",
    )
    run_parser.add_argument(
        "--compute-accuracy",
        action="store_true",
        help="Compute ground-truth accuracy metrics (requires chosenMove labels in dataset)",
    )
    run_parser.add_argument(
        "--top-k",
        type=str,
        help="Comma-separated list of K values for top-K accuracy (e.g., '1,3,5'). Default: 1",
    )
    run_parser.add_argument(
        "--conditioned-metrics",
        action="store_true",
        help="Compute conditioned metrics stratified by skill/time (M06, generates eval_report.v3)",
    )
    run_parser.add_argument(
        "--frozen-eval-manifest",
        type=Path,
        help="Path to frozen eval manifest (M06, for frozen eval runs)",
    )

    # M06: Frozen eval generation command
    frozen_parser = eval_subparsers.add_parser(
        "generate-frozen",
        help="Generate frozen evaluation manifest from dataset (M06)",
    )
    frozen_parser.add_argument(
        "--dataset-manifest",
        type=Path,
        required=True,
        help="Path to source dataset manifest v2 (manifest.json)",
    )
    frozen_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output path for frozen eval manifest (e.g., data/frozen_eval/manifest.v1.json)",
    )
    frozen_parser.add_argument(
        "--target-records",
        type=int,
        default=10000,
        help="Target total record count (default: 10000)",
    )
    frozen_parser.add_argument(
        "--min-per-skill-bucket",
        type=int,
        default=500,
        help="Minimum records per skill bucket if available (default: 500)",
    )
    frozen_parser.add_argument(
        "--created-at",
        type=str,
        help="Override creation timestamp (ISO 8601 format, for testing only)",
    )

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest Lichess database exports")
    ingest_subparsers = ingest_parser.add_subparsers(dest="ingest_command")

    # Ingest lichess subcommand
    lichess_parser = ingest_subparsers.add_parser("lichess", help="Ingest Lichess monthly dump")
    lichess_parser.add_argument(
        "--month",
        type=str,
        required=True,
        help="Month in YYYY-MM format (e.g., 2024-01)",
    )
    lichess_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory for receipt and artifacts",
    )
    lichess_parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path.home() / ".renacechess" / "cache",
        help="Cache directory (default: ~/.renacechess/cache)",
    )
    lichess_parser.add_argument(
        "--decompress",
        action="store_true",
        help="Decompress .zst to .pgn",
    )

    # Ingest url subcommand
    url_parser = ingest_subparsers.add_parser("url", help="Ingest from explicit URL or file")
    url_parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="URL (http/https) or file path (file:// or local path)",
    )
    url_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory for receipt and artifacts",
    )
    url_parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path.home() / ".renacechess" / "cache",
        help="Cache directory (default: ~/.renacechess/cache)",
    )
    url_parser.add_argument(
        "--decompress",
        action="store_true",
        help="Decompress .zst to .pgn",
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
                # Validate mutually exclusive inputs
                if args.pgn and args.receipt:
                    print(
                        "Error: Cannot specify both --pgn and --receipt (mutually exclusive)",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                config = DatasetBuildConfig(
                    output_dir=args.out,
                    shard_size=args.shard_size,
                    pgn_paths=args.pgn,
                    receipt_paths=args.receipt,
                    cache_dir=args.cache_dir,
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
    elif args.command == "eval":
        if args.eval_command == "run":
            try:
                from datetime import datetime

                # Parse created_at if provided
                created_at = None
                if args.created_at:
                    created_at = datetime.fromisoformat(args.created_at.replace("Z", "+00:00"))

                # Parse top-K values
                top_k_values = None
                if args.top_k:
                    try:
                        top_k_values = [int(k.strip()) for k in args.top_k.split(",")]
                        if not all(k > 0 for k in top_k_values):
                            print(
                                "Error: All top-K values must be positive integers",
                                file=sys.stderr,
                            )
                            sys.exit(1)
                    except ValueError:
                        print(
                            "Error: --top-k must be comma-separated integers (e.g., '1,3,5')",
                            file=sys.stderr,
                        )
                        sys.exit(1)

                # Build eval config
                eval_config = {
                    "max_records": args.max_records,
                    "compute_accuracy": args.compute_accuracy,
                    "top_k_values": top_k_values,
                    "conditioned_metrics": args.conditioned_metrics,
                }

                # M06: Check for conditioned metrics mode
                if args.conditioned_metrics:
                    # Load frozen eval manifest hash if provided
                    frozen_eval_manifest_hash = None
                    if args.frozen_eval_manifest:
                        import json

                        frozen_manifest_dict = json.loads(
                            args.frozen_eval_manifest.read_text(encoding="utf-8")
                        )
                        frozen_eval_manifest_hash = frozen_manifest_dict.get("manifestHash")

                    # Run conditioned evaluation (M06)
                    eval_results = run_conditioned_evaluation(
                        manifest_path=args.dataset_manifest,
                        policy_id=args.policy,
                        eval_config=eval_config,
                        max_records=args.max_records,
                        compute_accuracy=args.compute_accuracy,
                        top_k_values=top_k_values,
                        frozen_eval_manifest_hash=frozen_eval_manifest_hash,
                    )

                    # Build EvalReportV3
                    from renacechess.contracts.models import EvalReportV1, EvalReportV2, EvalReportV3

                    report: EvalReportV1 | EvalReportV2 | EvalReportV3 = EvalReportV3(
                        schema_version="eval_report.v3",
                        created_at=created_at or datetime.now(),
                        dataset_digest=eval_results["dataset_digest"],
                        assembly_config_hash=eval_results["assembly_config_hash"],
                        policy_id=eval_results["policy_id"],
                        eval_config_hash=eval_results["eval_config_hash"],
                        frozen_eval_manifest_hash=eval_results.get("frozen_eval_manifest_hash"),
                        overall=eval_results["overall"],
                        by_skill_bucket_id=eval_results["by_skill_bucket_id"],
                        by_time_control_class=eval_results["by_time_control_class"],
                        by_time_pressure_bucket=eval_results["by_time_pressure_bucket"],
                    )
                else:
                    # Run standard evaluation (v1/v2)
                    eval_results = run_evaluation(
                        manifest_path=args.dataset_manifest,
                        policy_id=args.policy,
                        eval_config=eval_config,
                        max_records=args.max_records,
                        compute_accuracy=args.compute_accuracy,
                        top_k_values=top_k_values,
                    )

                    # Build report (v2 if accuracy enabled, v1 otherwise)
                    from renacechess.contracts.models import EvalReportV1, EvalReportV2

                    if args.compute_accuracy:
                        # Validate that labeled records exist
                        overall_metrics = eval_results.get("overall_metrics", {})
                        labeled_count = overall_metrics.get("labeled_record_count", 0)
                        if labeled_count == 0:
                            print(
                                "Error: --compute-accuracy requested but no labeled records found. "
                                "Dataset must include chosenMove labels.",
                                file=sys.stderr,
                            )
                            sys.exit(1)
                        report = build_eval_report_v2(eval_results, created_at=created_at)
                    else:
                        report = build_eval_report(eval_results, created_at=created_at)

                # Write report
                args.out.mkdir(parents=True, exist_ok=True)
                report_path = args.out / "eval_report.json"
                write_eval_report(report, report_path)

                print(f"Evaluation report written to {report_path}", file=sys.stderr)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        elif args.eval_command == "generate-frozen":
            try:
                from datetime import datetime

                # Parse created_at if provided
                created_at = None
                if args.created_at:
                    created_at = datetime.fromisoformat(args.created_at.replace("Z", "+00:00"))

                # Generate frozen eval manifest
                manifest = generate_frozen_eval_manifest(
                    source_manifest_path=args.dataset_manifest,
                    target_total_records=args.target_records,
                    min_per_skill_bucket=args.min_per_skill_bucket,
                    created_at=created_at,
                )

                # Write manifest
                write_frozen_eval_manifest(manifest, args.out)

                print(f"Frozen eval manifest written to {args.out}", file=sys.stderr)
                print(
                    f"  Total records: {len(manifest.records)}",
                    file=sys.stderr,
                )
                print(
                    f"  Manifest hash: {manifest.manifest_hash}",
                    file=sys.stderr,
                )

                # Report coverage shortfalls if any
                if manifest.coverage_shortfalls:
                    print(
                        f"\n⚠️  Coverage shortfalls ({len(manifest.coverage_shortfalls)}):",
                        file=sys.stderr,
                    )
                    for shortfall in manifest.coverage_shortfalls:
                        print(
                            f"    {shortfall.axis}={shortfall.value}: "
                            f"{shortfall.actual}/{shortfall.target}",
                            file=sys.stderr,
                        )
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            eval_parser.print_help()
            sys.exit(1)
    elif args.command == "ingest":
        if args.ingest_command == "lichess":
            try:
                ingest_from_lichess(
                    month=args.month,
                    output_dir=args.out,
                    cache_dir=args.cache_dir,
                    decompress=args.decompress,
                )
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        elif args.ingest_command == "url":
            try:
                ingest_from_url(
                    url=args.url,
                    output_dir=args.out,
                    cache_dir=args.cache_dir,
                    decompress=args.decompress,
                )
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            ingest_parser.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
