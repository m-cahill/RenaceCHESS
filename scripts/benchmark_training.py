#!/usr/bin/env python3
"""Training benchmark harness for RenaceCHESS (M14 → M29).

This script measures training throughput on local hardware for both policy
and outcome-head models. It is designed for local execution only and is
explicitly excluded from CI.

M29 Extensions:
- Configurable batch sizes (64, 128, 256, 512)
- Configurable sample counts (1K sanity, 10K medium, 100K large)
- Precision mode support (FP32, AMP)
- Model head configurations (policy, policy+outcome)
- TrainingBenchmarkReportV1 artifact generation

Usage:
    # M14-style simple benchmark
    python scripts/benchmark_training.py \
        --manifest /path/to/manifest.json \
        --frozen-eval-manifest /path/to/frozen_eval_manifest.json \
        --output benchmark_results.json

    # M29-style full matrix benchmark
    python scripts/benchmark_training.py \
        --manifest /path/to/manifest.json \
        --frozen-eval-manifest /path/to/frozen_eval_manifest.json \
        --output benchmark_report.json \
        --m29-mode \
        --batch-sizes 64 128 256 512 \
        --sample-counts 1000 10000 100000 \
        --precision-modes fp32 amp \
        --model-heads policy policy+outcome

Requirements:
    - Real dataset manifest (not synthetic data)
    - Frozen eval manifest (to verify no contamination)
    - Local GPU (required for M29 mode)

WARNING: This script is for benchmarking only. It does NOT produce
production-ready models and does NOT alter any PoC semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, TypedDict

import torch

# Import existing training infrastructure
from renacechess.contracts.models import (
    BenchmarkMetricsV1,
    BenchmarkRunV1,
    DatasetInfoV1,
    DatasetManifestV2,
    EnvironmentMetadataV1,
    FrozenEvalManifestV1,
    TimeToTrainAssumptionsV1,
    TimeToTrainEstimateV1,
    TrainingBenchmarkReportV1,
)
from renacechess.determinism import compute_determinism_hash
from renacechess.models.training import PolicyDataset
from renacechess.models.training_outcome import OutcomeDataset

# --- Constants ---

# Benchmark configuration (small slice for timing, not full training)
DEFAULT_BENCHMARK_EPOCHS = 1
DEFAULT_BENCHMARK_BATCH_SIZE = 32
DEFAULT_BENCHMARK_MAX_SAMPLES = 1000  # Limit samples for benchmark timing
DEFAULT_BENCHMARK_STEPS = 100  # Max training steps for timing

# M29 locked configurations
M29_BATCH_SIZES: list[Literal[64, 128, 256, 512]] = [64, 128, 256, 512]
M29_SAMPLE_COUNTS: dict[Literal["sanity", "medium", "large"], Literal[1000, 10000, 100000]] = {
    "sanity": 1000,
    "medium": 10000,
    "large": 100000,
}
M29_PRECISION_MODES: list[Literal["fp32", "amp"]] = ["fp32", "amp"]
M29_MODEL_HEADS: list[Literal["policy", "policy+outcome"]] = ["policy", "policy+outcome"]


# --- Type Definitions (M14 legacy) ---


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
    """Complete benchmark report (M14 format)."""

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


def detect_environment_metadata() -> EnvironmentMetadataV1:
    """Detect environment metadata for M29 benchmark report.

    Returns:
        EnvironmentMetadataV1 model.
    """
    cuda_available = torch.cuda.is_available()

    if not cuda_available:
        raise RuntimeError("M29 benchmarks require GPU. CUDA not available.")

    # GPU info
    gpu_name = torch.cuda.get_device_name(0)
    props = torch.cuda.get_device_properties(0)
    vram_gb = round(props.total_memory / (1024**3), 2)

    # CUDA version
    cuda_version = torch.version.cuda or "unknown"

    # Driver version (attempt to get via nvidia-smi, fallback to unknown)
    driver_version: str | None = None
    try:
        import subprocess

        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            driver_version = result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        driver_version = None

    # OS info
    os_info = f"{platform.system()} {platform.release()}"

    # CPU info
    cpu_name: str | None = None
    try:
        if platform.system() == "Windows":
            cpu_name = platform.processor()
        else:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        cpu_name = line.split(":")[1].strip()
                        break
    except (FileNotFoundError, OSError):
        pass

    return EnvironmentMetadataV1(
        gpuName=gpu_name,
        vramGb=vram_gb,
        cudaVersion=cuda_version,
        driverVersion=driver_version,
        torchVersion=torch.__version__,
        pythonVersion=platform.python_version(),
        os=os_info,
        cpuName=cpu_name,
        cpuCores=torch.get_num_threads(),
        ramGb=None,  # Optional, not collected by default
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
    return hashlib.sha256(content).hexdigest()


# --- M29 Benchmark Execution ---


def run_m29_benchmark_run(
    manifest_path: Path,
    frozen_eval_manifest_path: Path,
    batch_size: Literal[64, 128, 256, 512],
    sample_count: Literal[1000, 10000, 100000],
    sample_count_label: Literal["sanity", "medium", "large"],
    precision_mode: Literal["fp32", "amp"],
    model_heads: Literal["policy", "policy+outcome"],
    seed: int = 42,
) -> BenchmarkRunV1:
    """Execute a single M29 benchmark run with specific configuration.

    Args:
        manifest_path: Path to dataset manifest.
        frozen_eval_manifest_path: Path to frozen eval manifest.
        batch_size: Training batch size.
        sample_count: Number of positions to use.
        sample_count_label: Human-readable label (sanity/medium/large).
        precision_mode: FP32 or AMP.
        model_heads: Which heads to train (policy or policy+outcome).
        seed: Random seed for determinism.

    Returns:
        BenchmarkRunV1 model with results.
    """
    run_id = f"batch{batch_size}_samples{sample_count}_{precision_mode}_{model_heads.replace('+', '_')}"

    print(f"  [{run_id}]")
    print(f"    Batch size: {batch_size}, Samples: {sample_count} ({sample_count_label})")
    print(f"    Precision: {precision_mode}, Heads: {model_heads}")

    # Set seeds for determinism
    torch.manual_seed(seed)
    random.seed(seed)

    # Reset GPU memory stats
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.empty_cache()

    device = torch.device("cuda")

    try:
        # Load datasets
        policy_dataset = PolicyDataset(manifest_path, frozen_eval_manifest_path, seed=seed)

        actual_samples = min(len(policy_dataset), sample_count)
        if actual_samples == 0:
            raise ValueError("No training samples found in dataset")

        # Calculate number of steps
        num_steps = actual_samples // batch_size
        if num_steps == 0:
            num_steps = 1

        # Build move vocabulary
        move_vocab: set[str] = set()
        for i in range(min(actual_samples, 500)):
            sample = policy_dataset[i]
            move_vocab.update(sample["legal_moves"])
            move_vocab.add(sample["chosen_move"])

        # Initialize models
        from renacechess.models.baseline_v1 import BaselinePolicyV1
        from renacechess.models.outcome_head_v1 import OutcomeHeadV1

        policy_model = BaselinePolicyV1(move_vocab_size=min(1000, len(move_vocab)))
        for move in sorted(move_vocab)[: min(1000, len(move_vocab))]:
            policy_model.add_move_to_vocab(move)
        policy_model = policy_model.to(device)

        outcome_model: OutcomeHeadV1 | None = None
        if model_heads == "policy+outcome":
            outcome_dataset = OutcomeDataset(manifest_path, frozen_eval_manifest_path, seed=seed)
            outcome_model = OutcomeHeadV1().to(device)

        # Training setup
        policy_criterion = torch.nn.CrossEntropyLoss()
        policy_optimizer = torch.optim.Adam(policy_model.parameters(), lr=0.001)

        outcome_criterion: torch.nn.CrossEntropyLoss | None = None
        outcome_optimizer: torch.optim.Adam | None = None
        if outcome_model is not None:
            outcome_criterion = torch.nn.CrossEntropyLoss()
            outcome_optimizer = torch.optim.Adam(outcome_model.parameters(), lr=0.001)

        # AMP setup
        use_amp = precision_mode == "amp"
        scaler = torch.amp.GradScaler("cuda") if use_amp else None

        # Timing metrics
        step_times: list[float] = []
        data_load_times: list[float] = []
        forward_times: list[float] = []
        backward_times: list[float] = []
        optimizer_times: list[float] = []

        samples_processed = 0

        policy_model.train()
        if outcome_model is not None:
            outcome_model.train()

        start_time = time.perf_counter()

        for step in range(num_steps):
            step_start = time.perf_counter()

            # Data loading
            data_start = time.perf_counter()
            batch_samples = []
            for b in range(batch_size):
                idx = (step * batch_size + b) % len(policy_dataset)
                batch_samples.append(policy_dataset[idx])
            data_load_times.append(time.perf_counter() - data_start)

            # Process each sample in batch (simplified, not true batching)
            for sample in batch_samples:
                fen = sample["fen"]
                skill_bucket = sample["skill_bucket"]
                time_control = sample["time_control"]
                legal_moves = sample["legal_moves"]
                chosen_move = sample["chosen_move"]

                # Forward pass (policy)
                forward_start = time.perf_counter()
                with torch.amp.autocast("cuda", enabled=use_amp):
                    legal_logits, legal_moves_filtered, _ = policy_model.forward_logits(
                        fen, skill_bucket, time_control, legal_moves
                    )

                    if len(legal_logits) == 0:
                        continue

                    try:
                        target_idx = legal_moves_filtered.index(chosen_move)
                    except ValueError:
                        continue

                    target = torch.tensor(target_idx, dtype=torch.long, device=device)
                    policy_loss = policy_criterion(legal_logits.unsqueeze(0), target.unsqueeze(0))

                    # Outcome head if enabled
                    if outcome_model is not None and outcome_criterion is not None:
                        outcome_class = sample.get("outcome_class", 1)  # Default to draw
                        outcome_logits = outcome_model.forward_logits(fen, skill_bucket, time_control)
                        outcome_target = torch.tensor(outcome_class, dtype=torch.long, device=device)
                        outcome_loss = outcome_criterion(
                            outcome_logits.unsqueeze(0), outcome_target.unsqueeze(0)
                        )
                        total_loss = policy_loss + outcome_loss
                    else:
                        total_loss = policy_loss

                forward_times.append(time.perf_counter() - forward_start)

                # Backward pass
                backward_start = time.perf_counter()
                policy_optimizer.zero_grad()
                if outcome_optimizer is not None:
                    outcome_optimizer.zero_grad()

                if scaler is not None:
                    scaler.scale(total_loss).backward()
                else:
                    total_loss.backward()
                backward_times.append(time.perf_counter() - backward_start)

                # Optimizer step
                optimizer_start = time.perf_counter()
                if scaler is not None:
                    scaler.step(policy_optimizer)
                    if outcome_optimizer is not None:
                        scaler.step(outcome_optimizer)
                    scaler.update()
                else:
                    policy_optimizer.step()
                    if outcome_optimizer is not None:
                        outcome_optimizer.step()
                optimizer_times.append(time.perf_counter() - optimizer_start)

                samples_processed += 1

            step_end = time.perf_counter()
            step_times.append((step_end - step_start) * 1000)  # ms

        total_time = time.perf_counter() - start_time

        # Compute statistics
        step_times_sorted = sorted(step_times)
        p95_idx = int(len(step_times_sorted) * 0.95) if step_times_sorted else 0

        # GPU metrics
        vram_peak_gb = torch.cuda.max_memory_allocated() / (1024**3)
        vram_total_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)

        # Time breakdown percentages
        total_data_time = sum(data_load_times)
        total_forward_time = sum(forward_times)
        total_backward_time = sum(backward_times)
        total_optimizer_time = sum(optimizer_times)
        total_measured = total_data_time + total_forward_time + total_backward_time + total_optimizer_time

        metrics = BenchmarkMetricsV1(
            stepsCompleted=len(step_times),
            samplesProcessed=samples_processed,
            totalTimeSeconds=round(total_time, 3),
            stepsPerSecond=round(len(step_times) / total_time, 2) if total_time > 0 else 0,
            samplesPerSecond=round(samples_processed / total_time, 2) if total_time > 0 else 0,
            stepTimeMeanMs=round(sum(step_times) / len(step_times), 2) if step_times else 0,
            stepTimeP95Ms=round(step_times_sorted[p95_idx], 2) if step_times_sorted else 0,
            vramPeakGb=round(vram_peak_gb, 2),
            vramPeakPercent=round((vram_peak_gb / vram_total_gb) * 100, 1),
            dataLoadTimePercent=round((total_data_time / total_measured) * 100, 1)
            if total_measured > 0
            else 0,
            forwardTimePercent=round((total_forward_time / total_measured) * 100, 1)
            if total_measured > 0
            else 0,
            backwardTimePercent=round((total_backward_time / total_measured) * 100, 1)
            if total_measured > 0
            else 0,
            optimizerTimePercent=round((total_optimizer_time / total_measured) * 100, 1)
            if total_measured > 0
            else 0,
        )

        print(f"    ✅ {metrics.samples_per_second:.1f} samples/sec, VRAM peak: {vram_peak_gb:.1f} GB")

        return BenchmarkRunV1(
            runId=run_id,
            batchSize=batch_size,
            sampleCount=sample_count,
            sampleCountLabel=sample_count_label,
            precisionMode=precision_mode,
            modelHeads=model_heads,
            metrics=metrics,
            status="success",
        )

    except torch.cuda.OutOfMemoryError as e:
        print(f"    ❌ OOM: {e}")
        # Create minimal metrics for OOM case
        metrics = BenchmarkMetricsV1(
            stepsCompleted=0,
            totalTimeSeconds=0,
        )
        return BenchmarkRunV1(
            runId=run_id,
            batchSize=batch_size,
            sampleCount=sample_count,
            sampleCountLabel=sample_count_label,
            precisionMode=precision_mode,
            modelHeads=model_heads,
            metrics=metrics,
            status="oom",
            errorMessage=str(e),
        )

    except Exception as e:
        print(f"    ❌ Error: {e}")
        metrics = BenchmarkMetricsV1(
            stepsCompleted=0,
            totalTimeSeconds=0,
        )
        return BenchmarkRunV1(
            runId=run_id,
            batchSize=batch_size,
            sampleCount=sample_count,
            sampleCountLabel=sample_count_label,
            precisionMode=precision_mode,
            modelHeads=model_heads,
            metrics=metrics,
            status="error",
            errorMessage=str(e),
        )


def compute_time_to_train_estimate(
    runs: list[BenchmarkRunV1],
    target_dataset_size: int = 10_000_000,  # 10M positions default
    target_epochs: int = 10,
    preferred_batch_size: int = 256,
    preferred_precision: Literal["fp32", "amp"] = "fp32",
) -> TimeToTrainEstimateV1:
    """Compute time-to-train estimate from benchmark runs.

    This is explicitly labeled as a heuristic, not a guarantee.

    Args:
        runs: List of completed benchmark runs.
        target_dataset_size: Target dataset size for full training.
        target_epochs: Target number of epochs.
        preferred_batch_size: Preferred batch size for estimate.
        preferred_precision: Preferred precision mode.

    Returns:
        TimeToTrainEstimateV1 model.
    """
    # Find the best matching run for the estimate
    successful_runs = [r for r in runs if r.status == "success"]

    if not successful_runs:
        # No successful runs - return low confidence estimate
        return TimeToTrainEstimateV1(
            assumptions=TimeToTrainAssumptionsV1(
                targetDatasetSize=target_dataset_size,
                targetEpochs=target_epochs,
                batchSize=preferred_batch_size,
                precisionMode=preferred_precision,
            ),
            projectedTimeHours=0,
            projectedTimeFormatted="Unable to estimate (no successful runs)",
            confidenceLevel="low",
            sensitivityNotes=["No successful benchmark runs to base estimate on"],
        )

    # Find runs matching preferred configuration
    matching_runs = [
        r
        for r in successful_runs
        if r.batch_size == preferred_batch_size and r.precision_mode == preferred_precision
    ]

    # Fall back to largest batch size with preferred precision
    if not matching_runs:
        matching_runs = [r for r in successful_runs if r.precision_mode == preferred_precision]

    # Fall back to any successful run
    if not matching_runs:
        matching_runs = successful_runs

    # Use the run with highest sample count for best scaling estimate
    best_run = max(matching_runs, key=lambda r: r.sample_count)

    # Calculate projected time
    samples_per_second = best_run.metrics.samples_per_second or 1
    total_samples = target_dataset_size * target_epochs
    projected_seconds = total_samples / samples_per_second
    projected_hours = projected_seconds / 3600

    # Format time
    hours = int(projected_hours)
    minutes = int((projected_hours - hours) * 60)
    formatted = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    # Determine confidence level
    if best_run.sample_count >= 100000:
        confidence: Literal["low", "medium", "high"] = "high"
    elif best_run.sample_count >= 10000:
        confidence = "medium"
    else:
        confidence = "low"

    sensitivity_notes = [
        f"Based on {best_run.sample_count} samples at batch size {best_run.batch_size}",
        f"Actual time may vary with dataset size and I/O patterns",
        f"Estimate assumes linear scaling (conservative)",
    ]

    if best_run.batch_size != preferred_batch_size:
        sensitivity_notes.append(
            f"Estimate based on batch size {best_run.batch_size}, not preferred {preferred_batch_size}"
        )

    return TimeToTrainEstimateV1(
        assumptions=TimeToTrainAssumptionsV1(
            targetDatasetSize=target_dataset_size,
            targetEpochs=target_epochs,
            batchSize=best_run.batch_size,
            precisionMode=best_run.precision_mode,
        ),
        projectedTimeHours=round(projected_hours, 2),
        projectedTimeFormatted=formatted,
        confidenceLevel=confidence,
        sensitivityNotes=sensitivity_notes,
    )


def run_m29_benchmark(
    manifest_path: Path,
    frozen_eval_manifest_path: Path,
    output_path: Path,
    batch_sizes: list[Literal[64, 128, 256, 512]] | None = None,
    sample_counts: list[Literal[1000, 10000, 100000]] | None = None,
    precision_modes: list[Literal["fp32", "amp"]] | None = None,
    model_heads_list: list[Literal["policy", "policy+outcome"]] | None = None,
    target_dataset_size: int = 10_000_000,
    target_epochs: int = 10,
    seed: int = 42,
) -> TrainingBenchmarkReportV1:
    """Run full M29 benchmark matrix.

    Args:
        manifest_path: Path to dataset manifest.
        frozen_eval_manifest_path: Path to frozen eval manifest.
        output_path: Path to write JSON results.
        batch_sizes: List of batch sizes to test (default: [64, 128, 256, 512]).
        sample_counts: List of sample counts to test (default: [1000, 10000, 100000]).
        precision_modes: List of precision modes to test (default: [fp32, amp]).
        model_heads_list: List of head configurations to test (default: [policy, policy+outcome]).
        target_dataset_size: Target dataset size for time estimate.
        target_epochs: Target epochs for time estimate.
        seed: Random seed for determinism.

    Returns:
        TrainingBenchmarkReportV1 model.
    """
    # Use defaults if not specified
    if batch_sizes is None:
        batch_sizes = M29_BATCH_SIZES
    if sample_counts is None:
        sample_counts = list(M29_SAMPLE_COUNTS.values())
    if precision_modes is None:
        precision_modes = M29_PRECISION_MODES
    if model_heads_list is None:
        model_heads_list = M29_MODEL_HEADS

    print("=" * 70)
    print("RenaceCHESS GPU Training Benchmark (M29)")
    print("=" * 70)
    print()

    warnings: list[str] = []

    # 1. Detect environment
    print("[1/4] Detecting environment...")
    try:
        environment = detect_environment_metadata()
        print(f"  GPU: {environment.gpu_name}")
        print(f"  VRAM: {environment.vram_gb} GB")
        print(f"  CUDA: {environment.cuda_version}")
        print(f"  PyTorch: {environment.torch_version}")
    except RuntimeError as e:
        print(f"  ❌ {e}")
        raise
    print()

    # 2. Validate manifests
    print("[2/4] Validating manifests...")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Dataset manifest not found: {manifest_path}")
    if not frozen_eval_manifest_path.exists():
        raise FileNotFoundError(f"Frozen eval manifest not found: {frozen_eval_manifest_path}")

    manifest_hash = "sha256:" + compute_manifest_digest(manifest_path)
    frozen_hash = "sha256:" + compute_manifest_digest(frozen_eval_manifest_path)
    print(f"  Dataset manifest: {manifest_path.name}")
    print(f"  Frozen eval manifest: {frozen_eval_manifest_path.name}")
    print()

    # 3. Check frozen eval overlap
    print("[3/4] Checking frozen eval contamination...")
    is_clean, overlapping_keys = check_frozen_eval_overlap(manifest_path, frozen_eval_manifest_path)

    if not is_clean:
        print(f"  ❌ CONTAMINATION DETECTED: {len(overlapping_keys)} overlapping records!")
        raise ValueError(f"Frozen eval contamination: {len(overlapping_keys)} records overlap.")
    else:
        print("  ✅ No overlap detected")

    dataset_info = DatasetInfoV1(
        manifestHash=manifest_hash,
        manifestPath=str(manifest_path),
        frozenEvalManifestHash=frozen_hash,
        overlapCheckPassed=is_clean,
    )
    print()

    # 4. Run benchmark matrix
    print("[4/4] Running benchmark matrix...")
    print(f"  Batch sizes: {batch_sizes}")
    print(f"  Sample counts: {sample_counts}")
    print(f"  Precision modes: {precision_modes}")
    print(f"  Model heads: {model_heads_list}")
    print()

    runs: list[BenchmarkRunV1] = []

    for model_heads in model_heads_list:
        for precision_mode in precision_modes:
            for sample_count in sample_counts:
                # Get label for sample count
                sample_label: Literal["sanity", "medium", "large"]
                if sample_count == 1000:
                    sample_label = "sanity"
                elif sample_count == 10000:
                    sample_label = "medium"
                else:
                    sample_label = "large"

                for batch_size in batch_sizes:
                    run = run_m29_benchmark_run(
                        manifest_path=manifest_path,
                        frozen_eval_manifest_path=frozen_eval_manifest_path,
                        batch_size=batch_size,
                        sample_count=sample_count,
                        sample_count_label=sample_label,
                        precision_mode=precision_mode,
                        model_heads=model_heads,
                        seed=seed,
                    )
                    runs.append(run)

                    # Clear GPU cache between runs
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

    # 5. Compute time-to-train estimate
    print()
    print("Computing time-to-train estimate...")
    estimate = compute_time_to_train_estimate(
        runs=runs,
        target_dataset_size=target_dataset_size,
        target_epochs=target_epochs,
        preferred_batch_size=256,
        preferred_precision="fp32",
    )
    print(f"  Projected time: {estimate.projected_time_formatted}")
    print(f"  Confidence: {estimate.confidence_level}")
    print()

    # Build report
    report = TrainingBenchmarkReportV1(
        version="1.0",
        generatedAt=datetime.now(UTC),
        environment=environment,
        datasetInfo=dataset_info,
        runMatrix=runs,
        timeToTrainEstimate=estimate,
        warnings=warnings,
        determinismHash="sha256:" + "0" * 64,  # Placeholder, computed below
    )

    # Compute determinism hash
    report_dict = report.model_dump(mode="json", by_alias=True, exclude={"determinism_hash"})
    determinism_hash = compute_determinism_hash(report_dict)
    report = report.model_copy(update={"determinism_hash": determinism_hash})

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json", by_alias=True), f, indent=2)
    print(f"Results written to: {output_path}")

    print()
    print("=" * 70)
    print("M29 Benchmark complete!")
    print("=" * 70)

    return report


# --- M14 Legacy Functions (preserved for backward compatibility) ---


def benchmark_policy_training(
    manifest_path: Path,
    frozen_eval_manifest_path: Path,
    max_samples: int = DEFAULT_BENCHMARK_MAX_SAMPLES,
    max_steps: int = DEFAULT_BENCHMARK_STEPS,
    seed: int = 42,
) -> BenchmarkResult:
    """Benchmark policy head training throughput (M14 legacy).

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
    """Benchmark outcome head training throughput (M14 legacy).

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
    """Run full training benchmark suite (M14 legacy).

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

    manifest_digest = compute_manifest_digest(manifest_path)[:16]
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
        description="RenaceCHESS Training Benchmark (M14 / M29)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # M14-style simple benchmark
    python scripts/benchmark_training.py \\
        --manifest data/manifest.json \\
        --frozen-eval-manifest data/frozen_eval_manifest.json

    # M29-style full matrix benchmark (GPU required)
    python scripts/benchmark_training.py \\
        --manifest data/manifest.json \\
        --frozen-eval-manifest data/frozen_eval_manifest.json \\
        --output benchmark_report.json \\
        --m29-mode

    # M29 with custom configuration
    python scripts/benchmark_training.py \\
        --manifest data/manifest.json \\
        --frozen-eval-manifest data/frozen_eval_manifest.json \\
        --output benchmark_report.json \\
        --m29-mode \\
        --batch-sizes 64 128 256 \\
        --sample-counts 1000 10000 \\
        --precision-modes fp32 \\
        --model-heads policy

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
        help="Path to write JSON benchmark results (optional for M14, required for M29)",
    )

    # M29 mode
    parser.add_argument(
        "--m29-mode",
        action="store_true",
        help="Run M29-style full matrix benchmark (GPU required)",
    )
    parser.add_argument(
        "--batch-sizes",
        type=int,
        nargs="+",
        choices=[64, 128, 256, 512],
        default=None,
        help="Batch sizes to test (M29 mode, default: 64 128 256 512)",
    )
    parser.add_argument(
        "--sample-counts",
        type=int,
        nargs="+",
        choices=[1000, 10000, 100000],
        default=None,
        help="Sample counts to test (M29 mode, default: 1000 10000 100000)",
    )
    parser.add_argument(
        "--precision-modes",
        type=str,
        nargs="+",
        choices=["fp32", "amp"],
        default=None,
        help="Precision modes to test (M29 mode, default: fp32 amp)",
    )
    parser.add_argument(
        "--model-heads",
        type=str,
        nargs="+",
        choices=["policy", "policy+outcome"],
        default=None,
        help="Model head configurations to test (M29 mode, default: policy policy+outcome)",
    )
    parser.add_argument(
        "--target-dataset-size",
        type=int,
        default=10_000_000,
        help="Target dataset size for time-to-train estimate (M29 mode, default: 10M)",
    )
    parser.add_argument(
        "--target-epochs",
        type=int,
        default=10,
        help="Target epochs for time-to-train estimate (M29 mode, default: 10)",
    )

    # M14 legacy options
    parser.add_argument(
        "--max-samples",
        type=int,
        default=DEFAULT_BENCHMARK_MAX_SAMPLES,
        help=f"Maximum samples to benchmark (M14 mode, default: {DEFAULT_BENCHMARK_MAX_SAMPLES})",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=DEFAULT_BENCHMARK_STEPS,
        help=f"Maximum training steps (M14 mode, default: {DEFAULT_BENCHMARK_STEPS})",
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
        help="Skip policy head benchmark (M14 mode)",
    )
    parser.add_argument(
        "--skip-outcome",
        action="store_true",
        help="Skip outcome head benchmark (M14 mode)",
    )

    args = parser.parse_args()

    try:
        if args.m29_mode:
            # M29 mode requires GPU and output path
            if args.output is None:
                parser.error("--output is required for M29 mode")

            run_m29_benchmark(
                manifest_path=args.manifest,
                frozen_eval_manifest_path=args.frozen_eval_manifest,
                output_path=args.output,
                batch_sizes=args.batch_sizes,
                sample_counts=args.sample_counts,
                precision_modes=args.precision_modes,
                model_heads_list=args.model_heads,
                target_dataset_size=args.target_dataset_size,
                target_epochs=args.target_epochs,
                seed=args.seed,
            )
        else:
            # M14 legacy mode
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
    except RuntimeError as e:
        print(f"RUNTIME ERROR: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
