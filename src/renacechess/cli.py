"""CLI entry point for RenaceCHESS."""

import argparse
import sys
from pathlib import Path

from renacechess.contracts.models import FrozenEvalManifestV1
from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig
from renacechess.demo.pgn_overlay import generate_demo_payload
from renacechess.determinism import canonical_json_dump
from renacechess.eval.report import build_eval_report, build_eval_report_v2, write_eval_report
from renacechess.eval.runner import run_conditioned_evaluation, run_evaluation
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
        help=(
            "Policy identifier (e.g., 'baseline.uniform_random', 'baseline.first_legal', "
            "'learned.v1')"
        ),
    )
    run_parser.add_argument(
        "--model-path",
        type=Path,
        help="Path to trained model file (required for 'learned.v1' policy)",
    )
    run_parser.add_argument(
        "--outcome-head-path",
        type=Path,
        help=(
            "Path to trained outcome head model directory "
            "(contains outcome_head_v1.pt and outcome_head_v1_metadata.json)"
        ),
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
        help=(
            "Compute conditioned metrics stratified by skill/time "
            "(M07, generates eval_report.v4 with HDI)"
        ),
    )
    run_parser.add_argument(
        "--frozen-eval-manifest",
        type=Path,
        help="Path to frozen eval manifest (M07, REQUIRED when --conditioned-metrics is used)",
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

    # Train policy command
    train_parser = subparsers.add_parser(
        "train-policy", help="Train learned human policy baseline (M08)"
    )
    train_parser.add_argument(
        "--dataset-manifest",
        type=Path,
        required=True,
        help="Path to dataset manifest v2",
    )
    train_parser.add_argument(
        "--frozen-eval-manifest",
        type=Path,
        help="Path to frozen eval manifest (to exclude from training)",
    )
    train_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory for model and metadata",
    )
    train_parser.add_argument(
        "--epochs",
        type=int,
        default=10,
        help="Number of training epochs (default: 10)",
    )
    train_parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size (default: 32)",
    )
    train_parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.001,
        help="Learning rate (default: 0.001)",
    )
    train_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for determinism (default: 42)",
    )

    # Train outcome head command
    train_outcome_parser = subparsers.add_parser(
        "train-outcome-head", help="Train learned human outcome head (W/D/L) (M09)"
    )
    train_outcome_parser.add_argument(
        "--dataset-manifest",
        type=Path,
        required=True,
        help="Path to dataset manifest v2",
    )
    train_outcome_parser.add_argument(
        "--frozen-eval-manifest",
        type=Path,
        help="Path to frozen eval manifest (to exclude from training)",
    )
    train_outcome_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory for model and metadata",
    )
    train_outcome_parser.add_argument(
        "--epochs",
        type=int,
        default=10,
        help="Number of training epochs (default: 10)",
    )
    train_outcome_parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size (default: 32)",
    )
    train_outcome_parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.001,
        help="Learning rate (default: 0.001)",
    )
    train_outcome_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for determinism (default: 42)",
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

                # M07: Check for conditioned metrics mode
                if args.conditioned_metrics:
                    # M07: Frozen eval manifest is REQUIRED when --conditioned-metrics is used
                    if not args.frozen_eval_manifest:
                        print(
                            "Error: --frozen-eval-manifest is REQUIRED when "
                            "--conditioned-metrics is used. "
                            "This ensures evaluation comparability.",
                            file=sys.stderr,
                        )
                        sys.exit(1)

                    # Load and validate frozen eval manifest
                    import json

                    try:
                        frozen_manifest_dict = json.loads(
                            args.frozen_eval_manifest.read_text(encoding="utf-8")
                        )
                        frozen_manifest = FrozenEvalManifestV1.model_validate(frozen_manifest_dict)
                        frozen_eval_manifest_hash = frozen_manifest.manifest_hash
                    except Exception as e:
                        print(
                            f"Error: Failed to load or validate frozen eval manifest: {e}",
                            file=sys.stderr,
                        )
                        sys.exit(1)

                    # Run conditioned evaluation (M07, M09)
                    outcome_head_path = getattr(args, "outcome_head_path", None)
                    eval_results = run_conditioned_evaluation(
                        manifest_path=args.dataset_manifest,
                        policy_id=args.policy,
                        eval_config=eval_config,
                        max_records=args.max_records,
                        compute_accuracy=args.compute_accuracy,
                        top_k_values=top_k_values,
                        frozen_eval_manifest_hash=frozen_eval_manifest_hash,
                        model_path=getattr(args, "model_path", None),
                        outcome_head_path=outcome_head_path,
                    )

                    # Validate frozen eval manifest hash matches (if provided in results)
                    if (
                        eval_results.get("frozen_eval_manifest_hash")
                        and eval_results["frozen_eval_manifest_hash"] != frozen_eval_manifest_hash
                    ):
                        print(
                            f"Error: Frozen eval manifest hash mismatch. "
                            f"Expected {frozen_eval_manifest_hash}, "
                            f"got {eval_results['frozen_eval_manifest_hash']}",
                            file=sys.stderr,
                        )
                        sys.exit(1)

                    # Build EvalReportV4 or V5 (M07 - includes HDI, M09 - includes outcome metrics)
                    from renacechess.contracts.models import (
                        EvalReportV1,
                        EvalReportV2,
                        EvalReportV3,
                        EvalReportV4,
                        EvalReportV5,
                        OutcomeMetrics,
                    )

                    # Check if outcome metrics are present (M09)
                    has_outcome_metrics = "outcome_metrics" in eval_results

                    if has_outcome_metrics:
                        # Build v5 report with outcome metrics
                        report_v5: (
                            EvalReportV1 | EvalReportV2 | EvalReportV3 | EvalReportV4 | EvalReportV5
                        ) = EvalReportV5(
                            schema_version="eval_report.v5",
                            created_at=created_at or datetime.now(),
                            dataset_digest=eval_results["dataset_digest"],
                            assembly_config_hash=eval_results["assembly_config_hash"],
                            policy_id=eval_results["policy_id"],
                            eval_config_hash=eval_results["eval_config_hash"],
                            frozen_eval_manifest_hash=frozen_eval_manifest_hash,
                            overall=eval_results["overall"],
                            by_skill_bucket_id=eval_results["by_skill_bucket_id"],
                            by_time_control_class=eval_results["by_time_control_class"],
                            by_time_pressure_bucket=eval_results["by_time_pressure_bucket"],
                            outcome_metrics=OutcomeMetrics(**eval_results["outcome_metrics"])
                            if eval_results.get("outcome_metrics")
                            else None,
                            outcome_metrics_by_skill={
                                k: OutcomeMetrics(**v)
                                for k, v in eval_results.get("outcome_metrics_by_skill", {}).items()
                            }
                            if eval_results.get("outcome_metrics_by_skill")
                            else None,
                            outcome_metrics_by_time_control={
                                k: OutcomeMetrics(**v)
                                for k, v in eval_results.get(
                                    "outcome_metrics_by_time_control", {}
                                ).items()
                            }
                            if eval_results.get("outcome_metrics_by_time_control")
                            else None,
                            outcome_metrics_by_time_pressure={
                                k: OutcomeMetrics(**v)
                                for k, v in eval_results.get(
                                    "outcome_metrics_by_time_pressure", {}
                                ).items()
                            }
                            if eval_results.get("outcome_metrics_by_time_pressure")
                            else None,
                        )
                        report = report_v5
                    else:
                        # Build v4 report (no outcome metrics)
                        report_v4: (
                            EvalReportV1 | EvalReportV2 | EvalReportV3 | EvalReportV4 | EvalReportV5
                        ) = EvalReportV4(
                            schema_version="eval_report.v4",
                            created_at=created_at or datetime.now(),
                            dataset_digest=eval_results["dataset_digest"],
                            assembly_config_hash=eval_results["assembly_config_hash"],
                            policy_id=eval_results["policy_id"],
                            eval_config_hash=eval_results["eval_config_hash"],
                            frozen_eval_manifest_hash=frozen_eval_manifest_hash,
                            overall=eval_results["overall"],
                            by_skill_bucket_id=eval_results["by_skill_bucket_id"],
                            by_time_control_class=eval_results["by_time_control_class"],
                            by_time_pressure_bucket=eval_results["by_time_pressure_bucket"],
                        )
                        report = report_v4
                else:
                    # Run standard evaluation (v1/v2)
                    eval_results = run_evaluation(
                        manifest_path=args.dataset_manifest,
                        policy_id=args.policy,
                        eval_config=eval_config,
                        max_records=args.max_records,
                        compute_accuracy=args.compute_accuracy,
                        top_k_values=top_k_values,
                        model_path=getattr(args, "model_path", None),
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
    elif args.command == "train-policy":
        try:
            from renacechess.models.training import train_baseline_policy

            frozen_eval_path = None
            if args.frozen_eval_manifest:
                frozen_eval_path = args.frozen_eval_manifest

            model_path = train_baseline_policy(
                manifest_path=args.dataset_manifest,
                frozen_eval_manifest_path=frozen_eval_path,
                output_dir=args.out,
                epochs=args.epochs,
                batch_size=args.batch_size,
                learning_rate=args.learning_rate,
                seed=args.seed,
            )

            print(f"Model trained and saved to {model_path}", file=sys.stderr)
            print(f"Metadata saved to {args.out / 'model_metadata.json'}", file=sys.stderr)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "train-outcome-head":
        try:
            from renacechess.models.training_outcome import train_outcome_head

            frozen_eval_path = None
            if args.frozen_eval_manifest:
                frozen_eval_path = args.frozen_eval_manifest

            model_path = train_outcome_head(
                manifest_path=args.dataset_manifest,
                frozen_eval_manifest_path=frozen_eval_path,
                output_dir=args.out,
                epochs=args.epochs,
                batch_size=args.batch_size,
                learning_rate=args.learning_rate,
                seed=args.seed,
            )

            print(f"Outcome head trained and saved to {model_path}", file=sys.stderr)
            print(
                f"Metadata saved to {args.out / 'outcome_head_v1_metadata.json'}", file=sys.stderr
            )
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
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
