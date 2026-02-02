"""CLI entry point for RenaceCHESS."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from renacechess.contracts.models import (
    AdviceFactsV1,
    CoachingSurfaceEvaluationSummaryV1,
    CoachingSurfaceV1,
    EloBucketDeltaFactsV1,
    FrozenEvalManifestV1,
)

if TYPE_CHECKING:
    from renacechess.contracts.models import (
        RecalibrationGateV1,
        RecalibrationParametersV1,
    )
from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig
from renacechess.demo.pgn_overlay import generate_demo_payload
from renacechess.determinism import canonical_json_dump
from renacechess.eval.report import build_eval_report, build_eval_report_v2, write_eval_report
from renacechess.eval.runner import run_conditioned_evaluation, run_evaluation
from renacechess.frozen_eval import generate_frozen_eval_manifest, write_frozen_eval_manifest
from renacechess.ingest.ingest import ingest_from_lichess, ingest_from_url


def resolve_recalibration_gate_from_args(
    args: argparse.Namespace,
) -> tuple[
    RecalibrationGateV1 | None,
    RecalibrationParametersV1 | None,
]:
    """Resolve and validate recalibration gate and parameters from CLI arguments (M26).

    This function handles loading the gate file, validating it, and loading
    associated parameters if the gate is enabled. It does not execute evaluation.

    Args:
        args: Parsed CLI arguments (must have `recalibration_gate` attribute).

    Returns:
        Tuple of (gate, params):
        - If no gate provided: (None, None)
        - If gate disabled: (gate, None)
        - If gate enabled: (gate, params)

    Raises:
        SystemExit: If gate file is invalid, missing, or parameters cannot be loaded.
    """
    from renacechess.eval.recalibration_runner import load_recalibration_parameters
    from renacechess.eval.runtime_recalibration import load_recalibration_gate

    if not args.recalibration_gate:
        return None, None

    try:
        recalibration_gate = load_recalibration_gate(args.recalibration_gate)
        # If gate is enabled, load parameters
        if recalibration_gate.enabled:
            if not recalibration_gate.parameters_ref:
                print(
                    ("Error: RecalibrationGateV1.enabled=True requires parametersRef to be set"),
                    file=sys.stderr,
                )
                sys.exit(1)
            # Try to load parameters from path
            # (parameters_ref can be path or hash)
            params_path = Path(recalibration_gate.parameters_ref)
            if params_path.exists():
                recalibration_params = load_recalibration_parameters(params_path)
            else:
                print(
                    (f"Error: RecalibrationParametersV1 not found at: {params_path}"),
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            recalibration_params = None

        return recalibration_gate, recalibration_params
    except Exception as e:
        print(
            f"Error: Failed to load recalibration gate: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


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
    run_parser.add_argument(
        "--recalibration-gate",
        type=Path,
        help="Path to RecalibrationGateV1 JSON file (M26, optional, explicit file-based gate only)",
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

    # M27: Runtime recalibration evaluation command
    runtime_recal_parser = eval_subparsers.add_parser(
        "runtime-recalibration",
        help="Evaluate impact of runtime recalibration (M27)",
    )
    runtime_recal_parser.add_argument(
        "--gate",
        type=Path,
        required=True,
        help="Path to RecalibrationGateV1 JSON file",
    )
    runtime_recal_parser.add_argument(
        "--params",
        type=Path,
        required=True,
        help="Path to RecalibrationParametersV1 JSON file",
    )
    runtime_recal_parser.add_argument(
        "--frozen-eval-manifest",
        type=Path,
        required=True,
        help="Path to FrozenEvalManifestV1 JSON file",
    )
    runtime_recal_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory for report and delta artifacts",
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

    # Coach command (M22)
    coach_parser = subparsers.add_parser(
        "coach",
        help="Render coaching output from pre-computed facts (M22 surface exposure)",
    )
    coach_parser.add_argument(
        "--advice-facts",
        type=Path,
        required=True,
        help="Path to AdviceFactsV1 JSON file (REQUIRED)",
    )
    coach_parser.add_argument(
        "--delta-facts",
        type=Path,
        required=True,
        help="Path to EloBucketDeltaFactsV1 JSON file (REQUIRED)",
    )
    coach_parser.add_argument(
        "--tone",
        type=str,
        choices=["neutral", "encouraging", "concise"],
        default="neutral",
        help="Tone profile for coaching output (default: neutral)",
    )
    coach_parser.add_argument(
        "--out",
        type=Path,
        help="Output file for CoachingSurfaceV1 JSON (default: stdout)",
    )

    # M24: Calibration evaluation command
    calibration_parser = subparsers.add_parser(
        "calibration",
        help="Run calibration evaluation over frozen eval manifest (M24)",
    )
    calibration_parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to FrozenEvalManifestV1 JSON file (REQUIRED)",
    )
    calibration_parser.add_argument(
        "--policy-id",
        type=str,
        default="baseline.uniform_random",
        help="Policy identifier (default: baseline.uniform_random)",
    )
    calibration_parser.add_argument(
        "--outcome-head-id",
        type=str,
        help="Outcome head identifier (optional, uses baselines if not provided)",
    )
    calibration_parser.add_argument(
        "--model-dir",
        type=Path,
        help="Path to model checkpoint directory (optional, CI uses baselines only)",
    )
    calibration_parser.add_argument(
        "--out",
        type=Path,
        help="Output file for CalibrationMetricsV1 JSON (default: stdout)",
    )
    calibration_parser.add_argument(
        "--with-recalibration",
        type=Path,
        help="Path to RecalibrationParametersV1 JSON (M25: preview before/after, off by default)",
    )

    # M25: Recalibration command
    recalibration_parser = subparsers.add_parser(
        "recalibration",
        help="Fit and apply recalibration parameters (M25)",
    )
    recalibration_subparsers = recalibration_parser.add_subparsers(dest="recalibration_command")

    # Recalibration fit command
    recal_fit_parser = recalibration_subparsers.add_parser(
        "fit",
        help="Fit recalibration parameters using grid search (M25)",
    )
    recal_fit_parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to FrozenEvalManifestV1 JSON file (REQUIRED)",
    )
    recal_fit_parser.add_argument(
        "--calibration-metrics",
        type=Path,
        required=True,
        help="Path to CalibrationMetricsV1 JSON (before recalibration)",
    )
    recal_fit_parser.add_argument(
        "--policy-id",
        type=str,
        default="baseline.uniform_random",
        help="Policy identifier (default: baseline.uniform_random)",
    )
    recal_fit_parser.add_argument(
        "--outcome-head-id",
        type=str,
        help="Outcome head identifier (optional, uses baselines if not provided)",
    )
    recal_fit_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output file for RecalibrationParametersV1 JSON",
    )

    # Recalibration preview command
    recal_preview_parser = recalibration_subparsers.add_parser(
        "preview",
        help="Preview before/after calibration comparison (M25)",
    )
    recal_preview_parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to FrozenEvalManifestV1 JSON file (REQUIRED)",
    )
    recal_preview_parser.add_argument(
        "--calibration-metrics-before",
        type=Path,
        required=True,
        help="Path to CalibrationMetricsV1 JSON (before recalibration)",
    )
    recal_preview_parser.add_argument(
        "--recalibration-parameters",
        type=Path,
        required=True,
        help="Path to RecalibrationParametersV1 JSON",
    )
    recal_preview_parser.add_argument(
        "--policy-id",
        type=str,
        default="baseline.uniform_random",
        help="Policy identifier (default: baseline.uniform_random)",
    )
    recal_preview_parser.add_argument(
        "--outcome-head-id",
        type=str,
        help="Outcome head identifier (optional, uses baselines if not provided)",
    )
    recal_preview_parser.add_argument(
        "--out",
        type=Path,
        help="Output file for CalibrationDeltaArtifactV1 JSON (default: stdout)",
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

                    # M26: Load recalibration gate if provided
                    recalibration_gate, recalibration_params = resolve_recalibration_gate_from_args(
                        args
                    )

                    # Run conditioned evaluation (M07, M09, M26)
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
                        recalibration_gate=recalibration_gate,
                        recalibration_params=recalibration_params,
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
        elif args.eval_command == "runtime-recalibration":
            # M27: Runtime recalibration evaluation
            try:
                from renacechess.eval.runtime_recalibration_eval_runner import (
                    run_runtime_recalibration_evaluation,
                )

                if not args.gate.exists():
                    print(
                        f"Error: RecalibrationGateV1 not found: {args.gate}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                if not args.params.exists():
                    print(
                        f"Error: RecalibrationParametersV1 not found: {args.params}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                if not args.frozen_eval_manifest.exists():
                    print(
                        f"Error: FrozenEvalManifestV1 not found: {args.frozen_eval_manifest}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                recal_report, recal_delta = run_runtime_recalibration_evaluation(
                    manifest_path=args.frozen_eval_manifest,
                    gate_path=args.gate,
                    params_path=args.params,
                    output_dir=args.out,
                )

                # Print summary
                print("=== Runtime Recalibration Evaluation ===", file=sys.stderr)
                print(f"  Total samples: {recal_report.total_samples}", file=sys.stderr)
                print("", file=sys.stderr)

                print("Baseline Metrics:", file=sys.stderr)
                bm = recal_report.baseline_metrics
                print(f"  Outcome ECE: {bm.outcome_ece:.4f}", file=sys.stderr)
                print(f"  Outcome NLL: {bm.outcome_nll:.4f}", file=sys.stderr)
                print(f"  Policy NLL: {bm.policy_nll:.4f}", file=sys.stderr)
                print(f"  Mean Entropy: {bm.mean_entropy:.4f}", file=sys.stderr)
                print("", file=sys.stderr)

                print("Recalibrated Metrics:", file=sys.stderr)
                rm = recal_report.recalibrated_metrics
                print(f"  Outcome ECE: {rm.outcome_ece:.4f}", file=sys.stderr)
                print(f"  Outcome NLL: {rm.outcome_nll:.4f}", file=sys.stderr)
                print(f"  Policy NLL: {rm.policy_nll:.4f}", file=sys.stderr)
                print(f"  Mean Entropy: {rm.mean_entropy:.4f}", file=sys.stderr)
                print("", file=sys.stderr)

                print("Overall Deltas:", file=sys.stderr)
                od = recal_delta.overall
                ece_dir = "↓" if od.outcome_ece_delta < 0 else "↑"
                print(
                    f"  Outcome ECE: {od.outcome_ece_delta:+.4f} {ece_dir}",
                    file=sys.stderr,
                )
                nll_dir = "↓" if od.outcome_nll_delta < 0 else "↑"
                print(
                    f"  Outcome NLL: {od.outcome_nll_delta:+.4f} {nll_dir}",
                    file=sys.stderr,
                )
                print(f"  Top-1 Stability: {od.top1_stability:.1%}", file=sys.stderr)
                print(f"  Top-3 Stability: {od.top3_stability:.1%}", file=sys.stderr)
                print("", file=sys.stderr)

                report_path = args.out / "runtime-recalibration-report.json"
                delta_path = args.out / "runtime-recalibration-delta.json"
                print(f"Report written to: {report_path}", file=sys.stderr)
                print(f"Delta written to: {delta_path}", file=sys.stderr)
                print(f"Report hash: {recal_report.determinism_hash}", file=sys.stderr)
                print(f"Delta hash: {recal_delta.determinism_hash}", file=sys.stderr)

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
    elif args.command == "coach":
        # M22: Coaching surface CLI command
        # Imports here to avoid pulling coaching module until needed
        from renacechess.coaching.evaluation import evaluate_coaching_draft
        from renacechess.coaching.llm_client import DeterministicStubLLM, ToneProfile
        from renacechess.coaching.translation_harness import translate_facts_to_coaching

        # M22 uses M21 thresholds exactly (locked answer #3)
        fact_coverage_min = 0.5
        hallucination_rate_max = 0.2
        delta_faithfulness_min = 0.5

        # Load advice facts
        if not args.advice_facts.exists():
            print(
                f"Error: AdviceFacts file not found: {args.advice_facts}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Load delta facts
        if not args.delta_facts.exists():
            print(
                f"Error: EloBucketDeltaFacts file not found: {args.delta_facts}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Parse and validate advice facts
        try:
            advice_facts_dict = json.loads(args.advice_facts.read_text(encoding="utf-8"))
            advice_facts = AdviceFactsV1.model_validate(advice_facts_dict)
        except Exception as e:
            print(
                f"Error: Failed to load or validate AdviceFacts: {e}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Parse and validate delta facts
        try:
            delta_facts_dict = json.loads(args.delta_facts.read_text(encoding="utf-8"))
            delta_facts = EloBucketDeltaFactsV1.model_validate(delta_facts_dict)
        except Exception as e:
            print(
                f"Error: Failed to load or validate EloBucketDeltaFacts: {e}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Validate lineage: delta_facts must reference advice_facts hash
        if advice_facts.determinism_hash not in delta_facts.source_advice_facts_hashes:
            print(
                "Error: Lineage mismatch — AdviceFacts hash not found in "
                "DeltaFacts.sourceAdviceFactsHashes. "
                "Ensure artifacts are correctly paired.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Map CLI tone to ToneProfile (M22 locked: stub only)
        tone_map = {
            "neutral": ToneProfile.NEUTRAL,
            "encouraging": ToneProfile.ENCOURAGING,
            "concise": ToneProfile.CONCISE,
        }
        tone = tone_map[args.tone]

        # Generate coaching draft using stub LLM only (M22 locked answer #5)
        timestamp = datetime.now(UTC)
        try:
            draft = translate_facts_to_coaching(
                advice_facts=advice_facts,
                delta_facts=delta_facts,
                tone=tone,
                llm_client=DeterministicStubLLM(),  # Always stub, never network
                generated_at=timestamp,
            )
        except Exception as e:
            print(f"Error: Translation failed: {e}", file=sys.stderr)
            sys.exit(1)

        # Evaluate coaching draft
        try:
            evaluation = evaluate_coaching_draft(
                draft=draft,
                advice_facts=advice_facts,
                delta_facts=delta_facts,
                evaluated_at=timestamp,
            )
        except Exception as e:
            print(f"Error: Evaluation failed: {e}", file=sys.stderr)
            sys.exit(1)

        # Build evaluation summary
        eval_summary = CoachingSurfaceEvaluationSummaryV1(
            fact_coverage=evaluation.metrics.fact_coverage,
            hallucination_rate=evaluation.metrics.hallucination_rate,
            bucket_alignment=evaluation.metrics.bucket_alignment,
            delta_faithfulness=evaluation.metrics.delta_faithfulness,
            verbosity_score=evaluation.metrics.verbosity_score,
            passed=evaluation.passed,
            failure_reasons=evaluation.failure_reasons,
        )

        # Build coaching surface artifact
        surface = CoachingSurfaceV1(
            schema_version="coaching_surface.v1",
            generated_at=timestamp,
            coaching_text=draft.draft_text,
            skill_bucket=draft.skill_bucket,
            tone_profile=draft.tone_profile,
            evaluation_summary=eval_summary,
            source_advice_facts_hash=draft.source_advice_facts_hash,
            source_delta_facts_hash=draft.source_delta_facts_hash or delta_facts.determinism_hash,
            coaching_draft_hash=draft.determinism_hash,
            coaching_evaluation_hash=evaluation.determinism_hash,
        )

        # ALWAYS print evaluation summary (M22 guardrail: never suppress)
        print("=== Evaluation Summary ===", file=sys.stderr)
        print(f"Fact coverage: {eval_summary.fact_coverage * 100:.0f}%", file=sys.stderr)
        print(f"Hallucination rate: {eval_summary.hallucination_rate * 100:.0f}%", file=sys.stderr)
        delta_pass = "PASS" if eval_summary.delta_faithfulness >= 0.5 else "FAIL"
        print(f"Delta faithfulness: {delta_pass}", file=sys.stderr)
        bucket_pass = "PASS" if eval_summary.bucket_alignment else "FAIL"
        print(f"Bucket alignment: {bucket_pass}", file=sys.stderr)
        verb_ok = "OK" if 0.2 <= eval_summary.verbosity_score <= 0.8 else "WARN"
        print(f"Verbosity score: {verb_ok}", file=sys.stderr)
        overall_pass = "PASS" if eval_summary.passed else "FAIL"
        print(f"Overall: {overall_pass}", file=sys.stderr)
        if eval_summary.failure_reasons:
            print(f"Failure reasons: {', '.join(eval_summary.failure_reasons)}", file=sys.stderr)
        print("", file=sys.stderr)

        # Check thresholds (M21 thresholds, M22 locked answer #3)
        threshold_failures: list[str] = []
        if eval_summary.fact_coverage < fact_coverage_min:
            threshold_failures.append(
                f"factCoverage {eval_summary.fact_coverage:.2f} < {fact_coverage_min}"
            )
        if eval_summary.hallucination_rate >= hallucination_rate_max:
            threshold_failures.append(
                f"hallucinationRate {eval_summary.hallucination_rate:.2f} "
                f">= {hallucination_rate_max}"
            )
        if not eval_summary.bucket_alignment:
            threshold_failures.append("bucketAlignment is False")
        if eval_summary.delta_faithfulness < delta_faithfulness_min:
            threshold_failures.append(
                f"deltaFaithfulness {eval_summary.delta_faithfulness:.2f} "
                f"< {delta_faithfulness_min}"
            )

        # If thresholds fail, print warning but still output artifact (exit non-zero)
        exit_code = 0
        if threshold_failures:
            print("⚠️  Quality thresholds failed:", file=sys.stderr)
            for failure in threshold_failures:
                print(f"    - {failure}", file=sys.stderr)
            print("", file=sys.stderr)
            exit_code = 1

        # Print coaching text
        print("=== Coaching Draft ===", file=sys.stderr)
        print(draft.draft_text, file=sys.stderr)
        print("", file=sys.stderr)

        # Output CoachingSurfaceV1 as JSON
        # mode='json' ensures datetime objects are serialized as ISO strings
        surface_json = canonical_json_dump(surface.model_dump(by_alias=True, mode="json"))
        if args.out:
            args.out.write_bytes(surface_json)
            print(f"CoachingSurfaceV1 written to {args.out}", file=sys.stderr)
        else:
            print(surface_json.decode("utf-8"))

        # Exit with appropriate code (M22 guardrail: non-zero if thresholds fail)
        sys.exit(exit_code)
    elif args.command == "calibration":
        # M24: Calibration evaluation command
        from renacechess.eval.calibration_runner import run_calibration_evaluation

        try:
            if not args.manifest.exists():
                print(
                    f"Error: Frozen eval manifest not found: {args.manifest}",
                    file=sys.stderr,
                )
                print(
                    "  Hint: Use 'eval generate-frozen' to create a frozen eval manifest, "
                    "or use the CI fixture at tests/fixtures/frozen_eval/manifest.json",
                    file=sys.stderr,
                )
                sys.exit(1)

            # Run calibration evaluation
            metrics = run_calibration_evaluation(
                manifest_path=args.manifest,
                model_dir=args.model_dir,
                policy_id=args.policy_id,
                outcome_head_id=args.outcome_head_id,
            )

            # Serialize to JSON
            output_json = json.dumps(metrics.model_dump(by_alias=True), default=str, indent=2)

            # Write output
            if args.out:
                args.out.write_text(output_json, encoding="utf-8")
                print(f"Calibration metrics written to {args.out}", file=sys.stderr)
            else:
                print(output_json)

            print(
                f"  Overall samples: {metrics.overall_samples}",
                file=sys.stderr,
            )
            print(
                f"  Buckets evaluated: {len([b for b in metrics.by_elo_bucket if b.samples > 0])}",
                file=sys.stderr,
            )

            # M25: Optional preview with recalibration
            if args.with_recalibration:
                from renacechess.eval.recalibration_runner import (
                    compute_calibration_delta,
                    load_recalibration_parameters,
                    run_calibration_evaluation_with_recalibration,
                )

                try:
                    recal_params = load_recalibration_parameters(args.with_recalibration)
                    metrics_after = run_calibration_evaluation_with_recalibration(
                        manifest_path=args.manifest,
                        recalibration_params=recal_params,
                        model_dir=args.model_dir,
                        policy_id=args.policy_id,
                        outcome_head_id=args.outcome_head_id,
                    )
                    delta = compute_calibration_delta(metrics, metrics_after, recal_params)

                    # Print preview summary
                    print("\n=== Recalibration Preview ===", file=sys.stderr)
                    for bucket_deltas in delta.by_elo_bucket:
                        if not bucket_deltas:
                            continue
                        bucket = bucket_deltas[0].elo_bucket
                        print(f"\nElo bucket: {bucket}", file=sys.stderr)
                        for d in bucket_deltas:
                            direction = "↓" if d.improved else "↑"
                            print(
                                f"  {d.metric}: {d.before:.4f} → {d.after:.4f} "
                                f"(Δ {d.delta:+.4f}) {direction}",
                                file=sys.stderr,
                            )
                except Exception as e:
                    print(f"Warning: Recalibration preview failed: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "recalibration":
        # M25: Recalibration commands
        from renacechess.eval.recalibration_runner import (
            compute_calibration_delta,
            fit_recalibration_parameters,
            load_calibration_metrics,
            load_recalibration_parameters,
            run_calibration_evaluation_with_recalibration,
            save_calibration_delta,
            save_recalibration_parameters,
        )

        try:
            if args.recalibration_command == "fit":
                # Fit recalibration parameters
                if not args.manifest.exists():
                    print(
                        f"Error: Frozen eval manifest not found: {args.manifest}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                if not args.calibration_metrics.exists():
                    print(
                        f"Error: Calibration metrics not found: {args.calibration_metrics}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                metrics_before = load_calibration_metrics(args.calibration_metrics)
                params = fit_recalibration_parameters(
                    manifest_path=args.manifest,
                    calibration_metrics=metrics_before,
                    policy_id=args.policy_id,
                    outcome_head_id=args.outcome_head_id,
                )

                save_recalibration_parameters(params, args.out)
                print(f"Recalibration parameters written to {args.out}", file=sys.stderr)
                print(f"  Buckets fitted: {len(params.by_elo_bucket)}", file=sys.stderr)

            elif args.recalibration_command == "preview":
                # Preview before/after comparison
                if not args.manifest.exists():
                    print(
                        f"Error: Frozen eval manifest not found: {args.manifest}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                if not args.calibration_metrics_before.exists():
                    print(
                        f"Error: Calibration metrics (before) not found: "
                        f"{args.calibration_metrics_before}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                if not args.recalibration_parameters.exists():
                    print(
                        f"Error: Recalibration parameters not found: "
                        f"{args.recalibration_parameters}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                metrics_before = load_calibration_metrics(args.calibration_metrics_before)
                recal_params = load_recalibration_parameters(args.recalibration_parameters)

                metrics_after = run_calibration_evaluation_with_recalibration(
                    manifest_path=args.manifest,
                    recalibration_params=recal_params,
                    model_dir=None,  # CI uses baselines only
                    policy_id=args.policy_id,
                    outcome_head_id=args.outcome_head_id,
                )

                delta = compute_calibration_delta(metrics_before, metrics_after, recal_params)

                # Print preview summary
                print("=== Recalibration Preview ===", file=sys.stderr)
                for bucket_deltas in delta.by_elo_bucket:
                    if not bucket_deltas:
                        continue
                    bucket = bucket_deltas[0].elo_bucket
                    print(f"\nElo bucket: {bucket}", file=sys.stderr)
                    for d in bucket_deltas:
                        direction = "↓" if d.improved else "↑"
                        print(
                            f"  {d.metric}: {d.before:.4f} → {d.after:.4f} "
                            f"(Δ {d.delta:+.4f}) {direction}",
                            file=sys.stderr,
                        )

                # Serialize to JSON
                output_json = json.dumps(delta.model_dump(by_alias=True), default=str, indent=2)

                # Write output
                if args.out:
                    save_calibration_delta(delta, args.out)
                    print(f"\nCalibration delta written to {args.out}", file=sys.stderr)
                else:
                    print("\n" + output_json)

            else:
                recalibration_parser.print_help()
                sys.exit(1)

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
