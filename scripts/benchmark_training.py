#!/usr/bin/env python3
"""Training benchmark harness for RenaceCHESS (M14).

This script measures training throughput on local hardware for both policy
and outcome-head models. It is designed for local execution only and is
explicitly excluded from CI.

Usage:
    python scripts/benchmark_training.py \
        --manifest /path/to/manifest.json \
        --frozen-eval-manifest /path/to/frozen_eval_manifest.json \
        --output benchmark_results.json

Requirements:
    - Real dataset manifest (not synthetic data)
    - Frozen eval manifest (to verify no contamination)
    - Local GPU (optional, will fallback to CPU)

WARNING: This script is for benchmarking only. It does NOT produce
production-ready models and does NOT alter any PoC semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

import torch

# Import existing training infrastructure
from renacechess.contracts.models import DatasetManifestV2, FrozenEvalManifestV1
from renacechess.models.training import PolicyDataset, train_baseline_policy
from renacechess.models.training_outcome import OutcomeDataset, train_outcome_head

# --- Constants ---

# Benchmark configuration (small slice for timing, not full training)
DEFAULT_BENCHMARK_EPOCHS = 1
DEFAULT_BENCHMARK_BATCH_SIZE = 32
DEFAULT_BENCHMARK_MAX_SAMPLES = 1000  # Limit samples for benchmark timing
DEFAULT_BENCHMARK_STEPS = 100  # Max training steps for timing


# --- Type Definitions ---


class HardwareInfo(TypedDict):
    """Hardware detection results."""

    cuda_available: bool
    cuda_device_count: int
    cuda_device_name: str | None
    cuda_vram_gb: float | None
    cpu_count: int
    torch_version: str
    python_version: str


class BenchmarkResult(TypedDict):
    """Benchmark result for a single training type."""

    model_type: str
    samples_processed: int
    steps_completed: int
    total_time_seconds: float
    samples_per_second: float
    step_time_mean_ms: float
    step_time_p95_ms: float
    gpu_memory_peak_mb: float | None


class BenchmarkReport(TypedDict):
    """Complete benchmark report."""

    benchmark_version: str
    timestamp: str
    hardware: HardwareInfo
    manifest_path: str
    manifest_digest: str
    frozen_eval_manifest_path: str
    frozen_eval_overlap_check: str
    policy_benchmark: BenchmarkResult | None
    outcome_benchmark: BenchmarkResult | None
    warnings: list[str]


# --- Hardware Detection ---


def detect_hardware() -> HardwareInfo:
    """Detect available hardware for training.

    Returns:
        Hardware information dictionary.
    """
    import platform

    cuda_available = torch.cuda.is_available()
    cuda_device_count = torch.cuda.device_count() if cuda_available else 0
    cuda_device_name: str | None = None
    cuda_vram_gb: float | None = None

    if cuda_available and cuda_device_count > 0:
        cuda_device_name = torch.cuda.get_device_name(0)
        # Get VRAM in GB
        props = torch.cuda.get_device_properties(0)
        cuda_vram_gb = round(props.total_memory / (1024**3), 2)

    return HardwareInfo(
        cuda_available=cuda_available,
        cuda_device_count=cuda_device_count,
        cuda_device_name=cuda_device_name,
        cuda_vram_gb=cuda_vram_gb,
        cpu_count=torch.get_num_threads(),
        torch_version=torch.__version__,
        python_version=platform.python_version(),
    )


# --- Frozen Eval Overlap Check ---


def check_frozen_eval_overlap(
    manifest_path: Path,
    frozen_eval_manifest_path: Path,
) -> tuple[bool, set[str]]:
    """Check that training data does not overlap with frozen eval.

    This is a critical safety check to prevent frozen eval contamination.

    Args:
        manifest_path: Path to dataset manifest.
        frozen_eval_manifest_path: Path to frozen eval manifest.

    Returns:
        Tuple of (is_clean, overlapping_keys).
        is_clean is True if no overlap detected.
    """
    # Load dataset manifest
    manifest_dict = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = DatasetManifestV2.model_validate(manifest_dict)

    # Load frozen eval manifest
    frozen_dict = json.loads(frozen_eval_manifest_path.read_text(encoding="utf-8"))
    frozen_manifest = FrozenEvalManifestV1.model_validate(frozen_dict)

    # Build set of frozen eval record keys
    frozen_keys = {record.record_key for record in frozen_manifest.records}

    # Collect training record keys
    manifest_dir = manifest_path.parent
    training_keys: set[str] = set()

    for shard_ref in manifest.shard_refs:
        shard_path = manifest_dir / shard_ref.path
        if not shard_path.exists():
            continue

        with shard_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                record = json.loads(line)
                record_key = record.get("meta", {}).get("inputHash", "")
                if record_key:
                    training_keys.add(record_key)

    # Check for overlap
    overlap = frozen_keys & training_keys

    return len(overlap) == 0, overlap


def compute_manifest_digest(manifest_path: Path) -> str:
    """Compute SHA-256 digest of manifest file.

    Args:
        manifest_path: Path to manifest file.

    Returns:
        Hex-encoded SHA-256 digest.
    """
    content = manifest_path.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


# --- Benchmark Execution ---


def benchmark_policy_training(
    manifest_path: Path,
    frozen_eval_manifest_path: Path,
    max_samples: int = DEFAULT_BENCHMARK_MAX_SAMPLES,
    max_steps: int = DEFAULT_BENCHMARK_STEPS,
    seed: int = 42,
) -> BenchmarkResult:
    """Benchmark policy head training throughput.

    This uses the existing training infrastructure with constrained parameters.

    Args:
        manifest_path: Path to dataset manifest.
        frozen_eval_manifest_path: Path to frozen eval manifest.
        max_samples: Maximum samples to use.
        max_steps: Maximum training steps.
        seed: Random seed for determinism.

    Returns:
        Benchmark result dictionary.
    """
    # Set seeds for determinism
    torch.manual_seed(seed)
    random.seed(seed)

    # Reset GPU memory stats if available
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    # Load dataset (reusing existing infrastructure)
    dataset = PolicyDataset(manifest_path, frozen_eval_manifest_path, seed=seed)

    # Limit samples
    actual_samples = min(len(dataset), max_samples)
    if actual_samples == 0:
        raise ValueError("No training samples found in dataset")

    # Time the training loop
    step_times: list[float] = []
    samples_processed = 0

    # Build move vocabulary (subset)
    move_vocab: set[str] = set()
    for i in range(min(actual_samples, 500)):
        sample = dataset[i]
        move_vocab.update(sample["legal_moves"])
        move_vocab.add(sample["chosen_move"])

    # Initialize model
    from renacechess.models.baseline_v1 import BaselinePolicyV1

    model = BaselinePolicyV1(move_vocab_size=min(1000, len(move_vocab)))
    for move in sorted(move_vocab)[: min(1000, len(move_vocab))]:
        model.add_move_to_vocab(move)

    # Move to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    # Training setup
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    model.train()
    start_time = time.perf_counter()

    for step in range(min(max_steps, actual_samples)):
        step_start = time.perf_counter()

        sample = dataset[step % len(dataset)]
        fen = sample["fen"]
        skill_bucket = sample["skill_bucket"]
        time_control = sample["time_control"]
        legal_moves = sample["legal_moves"]
        chosen_move = sample["chosen_move"]

        # Forward pass
        legal_logits, legal_moves_filtered, _ = model.forward_logits(
            fen, skill_bucket, time_control, legal_moves
        )

        if len(legal_logits) == 0:
            continue

        try:
            target_idx = legal_moves_filtered.index(chosen_move)
        except ValueError:
            continue

        # Backward pass
        target = torch.tensor(target_idx, dtype=torch.long, device=device)
        loss = criterion(legal_logits.unsqueeze(0), target.unsqueeze(0))

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        step_end = time.perf_counter()
        step_times.append((step_end - step_start) * 1000)  # Convert to ms
        samples_processed += 1

    total_time = time.perf_counter() - start_time

    # Compute statistics
    step_times_sorted = sorted(step_times)
    p95_idx = int(len(step_times_sorted) * 0.95)

    gpu_memory_peak_mb: float | None = None
    if torch.cuda.is_available():
        gpu_memory_peak_mb = torch.cuda.max_memory_allocated() / (1024**2)

    return BenchmarkResult(
        model_type="BaselinePolicyV1",
        samples_processed=samples_processed,
        steps_completed=len(step_times),
        total_time_seconds=round(total_time, 3),
        samples_per_second=round(samples_processed / total_time, 2) if total_time > 0 else 0,
        step_time_mean_ms=round(sum(step_times) / len(step_times), 2) if step_times else 0,
        step_time_p95_ms=round(step_times_sorted[p95_idx], 2) if step_times_sorted else 0,
        gpu_memory_peak_mb=round(gpu_memory_peak_mb, 2) if gpu_memory_peak_mb else None,
    )


def benchmark_outcome_training(
    manifest_path: Path,
    frozen_eval_manifest_path: Path,
    max_samples: int = DEFAULT_BENCHMARK_MAX_SAMPLES,
    max_steps: int = DEFAULT_BENCHMARK_STEPS,
    seed: int = 42,
) -> BenchmarkResult:
    """Benchmark outcome head training throughput.

    This uses the existing training infrastructure with constrained parameters.

    Args:
        manifest_path: Path to dataset manifest.
        frozen_eval_manifest_path: Path to frozen eval manifest.
        max_samples: Maximum samples to use.
        max_steps: Maximum training steps.
        seed: Random seed for determinism.

    Returns:
        Benchmark result dictionary.
    """
    # Set seeds for determinism
    torch.manual_seed(seed)
    random.seed(seed)

    # Reset GPU memory stats if available
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    # Load dataset (reusing existing infrastructure)
    dataset = OutcomeDataset(manifest_path, frozen_eval_manifest_path, seed=seed)

    # Limit samples
    actual_samples = min(len(dataset), max_samples)
    if actual_samples == 0:
        raise ValueError("No training samples found in dataset (need records with game results)")

    # Initialize model
    from renacechess.models.outcome_head_v1 import OutcomeHeadV1

    model = OutcomeHeadV1()

    # Move to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    # Training setup
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # Time the training loop
    step_times: list[float] = []
    samples_processed = 0

    model.train()
    start_time = time.perf_counter()

    for step in range(min(max_steps, actual_samples)):
        step_start = time.perf_counter()

        sample = dataset[step % len(dataset)]
        fen = sample["fen"]
        skill_bucket = sample["skill_bucket"]
        time_control = sample["time_control"]
        outcome_class = sample["outcome_class"]

        # Forward pass
        logits = model.forward_logits(fen, skill_bucket, time_control)

        # Backward pass
        target = torch.tensor(outcome_class, dtype=torch.long, device=device)
        loss = criterion(logits.unsqueeze(0), target.unsqueeze(0))

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        step_end = time.perf_counter()
        step_times.append((step_end - step_start) * 1000)  # Convert to ms
        samples_processed += 1

    total_time = time.perf_counter() - start_time

    # Compute statistics
    step_times_sorted = sorted(step_times)
    p95_idx = int(len(step_times_sorted) * 0.95)

    gpu_memory_peak_mb: float | None = None
    if torch.cuda.is_available():
        gpu_memory_peak_mb = torch.cuda.max_memory_allocated() / (1024**2)

    return BenchmarkResult(
        model_type="OutcomeHeadV1",
        samples_processed=samples_processed,
        steps_completed=len(step_times),
        total_time_seconds=round(total_time, 3),
        samples_per_second=round(samples_processed / total_time, 2) if total_time > 0 else 0,
        step_time_mean_ms=round(sum(step_times) / len(step_times), 2) if step_times else 0,
        step_time_p95_ms=round(step_times_sorted[p95_idx], 2) if step_times_sorted else 0,
        gpu_memory_peak_mb=round(gpu_memory_peak_mb, 2) if gpu_memory_peak_mb else None,
    )


# --- Main ---


def run_benchmark(
    manifest_path: Path,
    frozen_eval_manifest_path: Path,
    output_path: Path | None = None,
    max_samples: int = DEFAULT_BENCHMARK_MAX_SAMPLES,
    max_steps: int = DEFAULT_BENCHMARK_STEPS,
    seed: int = 42,
    skip_policy: bool = False,
    skip_outcome: bool = False,
) -> BenchmarkReport:
    """Run full training benchmark suite.

    Args:
        manifest_path: Path to dataset manifest.
        frozen_eval_manifest_path: Path to frozen eval manifest.
        output_path: Optional path to write JSON results.
        max_samples: Maximum samples per benchmark.
        max_steps: Maximum training steps per benchmark.
        seed: Random seed for determinism.
        skip_policy: Skip policy benchmark.
        skip_outcome: Skip outcome benchmark.

    Returns:
        Complete benchmark report.
    """
    print("=" * 60)
    print("RenaceCHESS Training Benchmark (M14)")
    print("=" * 60)
    print()

    warnings: list[str] = []

    # 1. Detect hardware
    print("[1/4] Detecting hardware...")
    hardware = detect_hardware()
    print(f"  CUDA available: {hardware['cuda_available']}")
    if hardware["cuda_device_name"]:
        print(f"  GPU: {hardware['cuda_device_name']}")
        print(f"  VRAM: {hardware['cuda_vram_gb']} GB")
    else:
        print("  GPU: None (CPU-only mode)")
        warnings.append("Running on CPU only - GPU benchmarks not available")
    print(f"  PyTorch: {hardware['torch_version']}")
    print()

    # 2. Validate manifest paths
    print("[2/4] Validating manifests...")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Dataset manifest not found: {manifest_path}")
    if not frozen_eval_manifest_path.exists():
        raise FileNotFoundError(f"Frozen eval manifest not found: {frozen_eval_manifest_path}")

    manifest_digest = compute_manifest_digest(manifest_path)
    print(f"  Dataset manifest: {manifest_path.name} ({manifest_digest})")
    print()

    # 3. Check frozen eval overlap (CRITICAL)
    print("[3/4] Checking frozen eval contamination...")
    is_clean, overlapping_keys = check_frozen_eval_overlap(manifest_path, frozen_eval_manifest_path)

    if not is_clean:
        print(f"  ❌ CONTAMINATION DETECTED: {len(overlapping_keys)} overlapping records!")
        print("  Benchmark aborted to protect scientific integrity.")
        raise ValueError(
            f"Frozen eval contamination detected: {len(overlapping_keys)} records overlap. "
            "This would compromise training integrity. Aborting."
        )
    else:
        print("  ✅ No overlap detected - frozen eval is protected")
    print()

    # 4. Run benchmarks
    print("[4/4] Running training benchmarks...")
    print()

    policy_result: BenchmarkResult | None = None
    outcome_result: BenchmarkResult | None = None

    if not skip_policy:
        print("  [Policy Head Benchmark]")
        print(f"  Max samples: {max_samples}, Max steps: {max_steps}")
        try:
            policy_result = benchmark_policy_training(
                manifest_path,
                frozen_eval_manifest_path,
                max_samples=max_samples,
                max_steps=max_steps,
                seed=seed,
            )
            print(f"  ✅ Completed: {policy_result['samples_per_second']:.1f} samples/sec")
            print(f"     Step time (mean): {policy_result['step_time_mean_ms']:.2f} ms")
            print(f"     Step time (p95):  {policy_result['step_time_p95_ms']:.2f} ms")
            if policy_result["gpu_memory_peak_mb"]:
                print(f"     GPU memory peak:  {policy_result['gpu_memory_peak_mb']:.1f} MB")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            warnings.append(f"Policy benchmark failed: {e}")
        print()

    if not skip_outcome:
        print("  [Outcome Head Benchmark]")
        print(f"  Max samples: {max_samples}, Max steps: {max_steps}")
        try:
            outcome_result = benchmark_outcome_training(
                manifest_path,
                frozen_eval_manifest_path,
                max_samples=max_samples,
                max_steps=max_steps,
                seed=seed,
            )
            print(f"  ✅ Completed: {outcome_result['samples_per_second']:.1f} samples/sec")
            print(f"     Step time (mean): {outcome_result['step_time_mean_ms']:.2f} ms")
            print(f"     Step time (p95):  {outcome_result['step_time_p95_ms']:.2f} ms")
            if outcome_result["gpu_memory_peak_mb"]:
                print(f"     GPU memory peak:  {outcome_result['gpu_memory_peak_mb']:.1f} MB")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            warnings.append(f"Outcome benchmark failed: {e}")
        print()

    # Build report
    report = BenchmarkReport(
        benchmark_version="1.0.0",
        timestamp=datetime.now().isoformat(),
        hardware=hardware,
        manifest_path=str(manifest_path),
        manifest_digest=manifest_digest,
        frozen_eval_manifest_path=str(frozen_eval_manifest_path),
        frozen_eval_overlap_check="PASS" if is_clean else "FAIL",
        policy_benchmark=policy_result,
        outcome_benchmark=outcome_result,
        warnings=warnings,
    )

    # Write output if requested
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True)
        print(f"Results written to: {output_path}")

    print()
    print("=" * 60)
    print("Benchmark complete!")
    print("=" * 60)

    return report


def main() -> int:
    """Main entry point for benchmark script."""
    parser = argparse.ArgumentParser(
        description="RenaceCHESS Training Benchmark (M14)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run full benchmark with default settings
    python scripts/benchmark_training.py \\
        --manifest data/manifest.json \\
        --frozen-eval-manifest data/frozen_eval_manifest.json

    # Run with custom sample limit and output
    python scripts/benchmark_training.py \\
        --manifest data/manifest.json \\
        --frozen-eval-manifest data/frozen_eval_manifest.json \\
        --max-samples 500 \\
        --max-steps 50 \\
        --output results/benchmark.json

    # Run only policy benchmark
    python scripts/benchmark_training.py \\
        --manifest data/manifest.json \\
        --frozen-eval-manifest data/frozen_eval_manifest.json \\
        --skip-outcome

Note: This script is for LOCAL BENCHMARKING ONLY.
It does NOT produce production models and is excluded from CI.
        """,
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to dataset manifest (v2 format)",
    )
    parser.add_argument(
        "--frozen-eval-manifest",
        type=Path,
        required=True,
        help="Path to frozen eval manifest (for contamination check)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write JSON benchmark results (optional)",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=DEFAULT_BENCHMARK_MAX_SAMPLES,
        help=f"Maximum samples to benchmark (default: {DEFAULT_BENCHMARK_MAX_SAMPLES})",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=DEFAULT_BENCHMARK_STEPS,
        help=f"Maximum training steps (default: {DEFAULT_BENCHMARK_STEPS})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for determinism (default: 42)",
    )
    parser.add_argument(
        "--skip-policy",
        action="store_true",
        help="Skip policy head benchmark",
    )
    parser.add_argument(
        "--skip-outcome",
        action="store_true",
        help="Skip outcome head benchmark",
    )

    args = parser.parse_args()

    try:
        run_benchmark(
            manifest_path=args.manifest,
            frozen_eval_manifest_path=args.frozen_eval_manifest,
            output_path=args.output,
            max_samples=args.max_samples,
            max_steps=args.max_steps,
            seed=args.seed,
            skip_policy=args.skip_policy,
            skip_outcome=args.skip_outcome,
        )
        return 0
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())

