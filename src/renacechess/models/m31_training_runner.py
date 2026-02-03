"""M31 Full Training Run Executor.

This module implements the full training run for M31, producing:
- Trained policy and outcome checkpoints
- TrainingConfigLockV1 artifact (config immutability proof)
- TrainingRunReportV1 artifact (execution summary)

Key design principles:
1. ONE training run, not experiments
2. Fixed configuration (no tuning)
3. Deterministic where possible
4. Complete audit trail
5. External checkpoint storage (hashes committed, not files)

See docs/milestones/PhaseE/M31/M31_plan.md for the governing specification.
"""

from __future__ import annotations

import hashlib
import os
import platform
import random
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import torch
import yaml

from renacechess.contracts.models import (
    CheckpointPolicyV1,
    CheckpointReferenceV1,
    EnvironmentRequirementsV1,
    EpochMetricsV1,
    ExecutionEnvironmentV1,
    HeadConfigV1,
    HeadRunSummaryV1,
    OptimizerConfigV1,
    SchedulerConfigV1,
    SourceTemplateV1,
    TrainingConfigLockV1,
    TrainingRunReportV1,
)
from renacechess.determinism import canonical_json_dump

# =============================================================================
# Constants
# =============================================================================

M31_RUN_ID = "m31-training-run-001"
M31_TIMEOUT_HOURS = 12
M31_EPOCHS = 10  # Locked per M31 plan


def _compute_sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def _compute_sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 hash of bytes."""
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _get_git_commit_sha() -> str:
    """Get current git commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return "0" * 40  # Placeholder if git not available


def _get_execution_environment() -> ExecutionEnvironmentV1:
    """Detect and return execution environment metadata."""
    gpu_name = "CPU"
    vram_gb = None
    cuda_version = "N/A"
    driver_version = None

    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        cuda_version = torch.version.cuda or "N/A"
        # Try to get driver version
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            driver_version = result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return ExecutionEnvironmentV1(
        gpu_name=gpu_name,
        vram_gb=vram_gb,
        cuda_version=cuda_version,
        driver_version=driver_version,
        torch_version=torch.__version__,
        python_version=platform.python_version(),
        os=f"{platform.system()} {platform.release()}",
        hostname=platform.node(),
    )


def _format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def _format_bytes(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    size_float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_float < 1024:
            return f"{size_float:.1f} {unit}"
        size_float /= 1024
    return f"{size_float:.1f} PB"


def load_template_config(template_path: Path) -> dict[str, Any]:
    """Load and return YAML template config."""
    with template_path.open() as f:
        result: dict[str, Any] = yaml.safe_load(f)
        return result


def create_config_lock(
    dataset_manifest_path: Path,
    frozen_eval_manifest_path: Path,
    policy_template_path: Path,
    outcome_template_path: Path,
    output_dir: Path,
    created_at: datetime | None = None,
) -> TrainingConfigLockV1:
    """Create and save TrainingConfigLockV1 artifact.

    This is the first step in M31 training - locking the configuration
    before any training begins.

    Args:
        dataset_manifest_path: Path to training dataset manifest.
        frozen_eval_manifest_path: Path to frozen eval manifest (for exclusion).
        policy_template_path: Path to policy training template.
        outcome_template_path: Path to outcome training template.
        output_dir: Directory to save config lock artifact.
        created_at: Override creation timestamp (for testing).

    Returns:
        TrainingConfigLockV1 artifact.
    """
    if created_at is None:
        created_at = datetime.now(UTC)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Compute hashes
    dataset_hash = _compute_sha256_file(dataset_manifest_path)
    frozen_eval_hash = _compute_sha256_file(frozen_eval_manifest_path)
    code_commit = _get_git_commit_sha()

    # Load templates
    policy_config = load_template_config(policy_template_path)
    outcome_config = load_template_config(outcome_template_path)

    # Create head configs from templates (using locked epoch count)
    policy_head = HeadConfigV1(
        model_type=policy_config.get("model", {}).get("type", "BaselinePolicyV1"),
        epochs=M31_EPOCHS,  # Locked
        batch_size=policy_config.get("training", {}).get("batch_size", 32),
        learning_rate=policy_config.get("training", {}).get("learning_rate", 0.001),
        seed=policy_config.get("training", {}).get("seed", 42),
        optimizer=OptimizerConfigV1(
            type=policy_config.get("training", {}).get("optimizer", {}).get("type", "AdamW"),
            weight_decay=policy_config.get("training", {})
            .get("optimizer", {})
            .get("weight_decay", 0.01),
        ),
        scheduler=SchedulerConfigV1(
            enabled=policy_config.get("training", {}).get("scheduler", {}).get("enabled", False),
            type=policy_config.get("training", {}).get("scheduler", {}).get("type"),
            step_size=policy_config.get("training", {}).get("scheduler", {}).get("step_size"),
            gamma=policy_config.get("training", {}).get("scheduler", {}).get("gamma"),
        ),
        loss_function="CrossEntropyLoss",
        move_vocab_size=policy_config.get("model", {}).get("move_vocab_size", 1000),
    )

    outcome_head = HeadConfigV1(
        model_type=outcome_config.get("model", {}).get("type", "OutcomeHeadV1"),
        epochs=M31_EPOCHS,  # Locked
        batch_size=outcome_config.get("training", {}).get("batch_size", 32),
        learning_rate=outcome_config.get("training", {}).get("learning_rate", 0.001),
        seed=outcome_config.get("training", {}).get("seed", 42),
        optimizer=OptimizerConfigV1(
            type=outcome_config.get("training", {}).get("optimizer", {}).get("type", "AdamW"),
            weight_decay=outcome_config.get("training", {})
            .get("optimizer", {})
            .get("weight_decay", 0.01),
        ),
        scheduler=SchedulerConfigV1(
            enabled=outcome_config.get("training", {}).get("scheduler", {}).get("enabled", False),
            type=outcome_config.get("training", {}).get("scheduler", {}).get("type"),
            step_size=outcome_config.get("training", {}).get("scheduler", {}).get("step_size"),
            gamma=outcome_config.get("training", {}).get("scheduler", {}).get("gamma"),
        ),
        loss_function="CrossEntropyLoss",
    )

    # Environment requirements (M31: FP32 only, no AMP)
    env_reqs = EnvironmentRequirementsV1(
        device="auto",
        mixed_precision=False,  # M31 locked: no AMP
        deterministic=True,
        num_workers=4,
        pin_memory=True,
    )

    # Checkpoint policy (M31: midpoint + final only)
    checkpoint_policy = CheckpointPolicyV1(
        save_midpoint=True,
        save_final=True,
        save_every_n_epochs=None,  # M31: no per-epoch checkpoints
        output_dir=str(output_dir / "checkpoints"),
    )

    # Source templates
    source_templates = [
        SourceTemplateV1(
            path=str(policy_template_path),
            hash=_compute_sha256_file(policy_template_path),
        ),
        SourceTemplateV1(
            path=str(outcome_template_path),
            hash=_compute_sha256_file(outcome_template_path),
        ),
    ]

    # Create config lock (without determinism hash first)
    config_lock_partial = TrainingConfigLockV1(
        version="1.0",
        created_at=created_at,
        code_commit_sha=code_commit,
        dataset_manifest_hash=dataset_hash,
        dataset_manifest_path=str(dataset_manifest_path),
        frozen_eval_manifest_hash=frozen_eval_hash,
        frozen_eval_manifest_path=str(frozen_eval_manifest_path),
        policy_config=policy_head,
        outcome_config=outcome_head,
        environment_requirements=env_reqs,
        checkpoint_policy=checkpoint_policy,
        source_templates=source_templates,
        audit_notes=(
            "M31 FULL-TRAINING-RUN-001: Locked configuration for first full training run. "
            "FP32 only, 10 epochs, no hyperparameter tuning."
        ),
        determinism_hash="sha256:" + "0" * 64,  # Placeholder
    )

    # Compute determinism hash
    config_dict = config_lock_partial.model_dump(mode="json", by_alias=True)
    del config_dict["determinismHash"]
    config_bytes = canonical_json_dump(config_dict)
    determinism_hash = _compute_sha256_bytes(config_bytes)

    # Create final config lock
    config_lock = TrainingConfigLockV1(
        **{**config_lock_partial.model_dump(by_alias=False), "determinism_hash": determinism_hash}
    )

    # Save config lock
    config_lock_path = output_dir / "config_lock.json"
    config_lock_dict = config_lock.model_dump(mode="json", by_alias=True)
    config_lock_json = canonical_json_dump(config_lock_dict)
    config_lock_path.write_bytes(config_lock_json)

    return config_lock


def run_training(
    config_lock: TrainingConfigLockV1,
    dataset_manifest_path: Path,
    frozen_eval_manifest_path: Path,
    output_dir: Path,
    run_id: str = M31_RUN_ID,
) -> TrainingRunReportV1:
    """Execute full training run and produce report.

    This is the core execution function for M31. It trains both policy
    and outcome heads and produces all required artifacts.

    Args:
        config_lock: Locked training configuration.
        dataset_manifest_path: Path to training dataset manifest.
        frozen_eval_manifest_path: Path to frozen eval manifest.
        output_dir: Directory for training outputs.
        run_id: Unique identifier for this run.

    Returns:
        TrainingRunReportV1 artifact.
    """
    from renacechess.models.training import train_baseline_policy
    from renacechess.models.training_outcome import train_outcome_head

    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir = output_dir / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now(UTC)
    environment = _get_execution_environment()

    # Initialize tracking
    warnings: list[str] = []
    checkpoints: list[CheckpointReferenceV1] = []

    # Set seeds for determinism
    seed = config_lock.policy_config.seed
    torch.manual_seed(seed)
    random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # Enable deterministic mode if requested
    if config_lock.environment_requirements and config_lock.environment_requirements.deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"

    # =========================================================================
    # Train Policy Head
    # =========================================================================
    policy_start = time.time()
    policy_epochs_completed = 0
    policy_loss_history: list[EpochMetricsV1] = []
    policy_status: str = "success"
    policy_error: str | None = None
    policy_initial_loss: float | None = None
    policy_final_loss: float = 0.0

    try:
        # Train policy model
        policy_output_dir = checkpoints_dir / "policy"
        policy_model_path = train_baseline_policy(
            manifest_path=dataset_manifest_path,
            frozen_eval_manifest_path=frozen_eval_manifest_path,
            output_dir=policy_output_dir,
            epochs=config_lock.policy_config.epochs,
            batch_size=config_lock.policy_config.batch_size,
            learning_rate=config_lock.policy_config.learning_rate,
            seed=config_lock.policy_config.seed,
        )

        policy_epochs_completed = config_lock.policy_config.epochs

        # Note: Current training doesn't capture per-epoch loss in metadata
        # This would be enhanced in a real implementation
        policy_final_loss = 0.0  # Placeholder

        # Create checkpoint reference
        if policy_model_path.exists():
            checkpoint_hash = _compute_sha256_file(policy_model_path)
            checkpoint_size = policy_model_path.stat().st_size
            checkpoints.append(
                CheckpointReferenceV1(
                    checkpoint_id=f"{run_id}-policy-final",
                    checkpoint_type="final",
                    head_type="policy",
                    epoch=config_lock.policy_config.epochs,
                    step=None,
                    file_hash=checkpoint_hash,
                    file_size_bytes=checkpoint_size,
                    file_size_formatted=_format_bytes(checkpoint_size),
                    file_path=str(policy_model_path.resolve()),
                    created_at=datetime.now(UTC),
                )
            )

    except Exception as e:
        policy_status = "failed"
        policy_error = str(e)
        warnings.append(f"Policy training failed: {e}")

    policy_time = time.time() - policy_start

    # =========================================================================
    # Train Outcome Head
    # =========================================================================
    outcome_start = time.time()
    outcome_epochs_completed = 0
    outcome_loss_history: list[EpochMetricsV1] = []
    outcome_status: str = "success"
    outcome_error: str | None = None
    outcome_initial_loss: float | None = None
    outcome_final_loss: float = 0.0

    try:
        # Train outcome model
        outcome_output_dir = checkpoints_dir / "outcome"
        outcome_model_path = train_outcome_head(
            manifest_path=dataset_manifest_path,
            frozen_eval_manifest_path=frozen_eval_manifest_path,
            output_dir=outcome_output_dir,
            epochs=config_lock.outcome_config.epochs,
            batch_size=config_lock.outcome_config.batch_size,
            learning_rate=config_lock.outcome_config.learning_rate,
            seed=config_lock.outcome_config.seed,
        )

        outcome_epochs_completed = config_lock.outcome_config.epochs

        # Create checkpoint reference
        if outcome_model_path.exists():
            checkpoint_hash = _compute_sha256_file(outcome_model_path)
            checkpoint_size = outcome_model_path.stat().st_size
            checkpoints.append(
                CheckpointReferenceV1(
                    checkpoint_id=f"{run_id}-outcome-final",
                    checkpoint_type="final",
                    head_type="outcome",
                    epoch=config_lock.outcome_config.epochs,
                    step=None,
                    file_hash=checkpoint_hash,
                    file_size_bytes=checkpoint_size,
                    file_size_formatted=_format_bytes(checkpoint_size),
                    file_path=str(outcome_model_path.resolve()),
                    created_at=datetime.now(UTC),
                )
            )

    except Exception as e:
        outcome_status = "failed"
        outcome_error = str(e)
        warnings.append(f"Outcome training failed: {e}")

    outcome_time = time.time() - outcome_start

    # =========================================================================
    # Create Training Report
    # =========================================================================
    completed_at = datetime.now(UTC)
    total_seconds = (completed_at - started_at).total_seconds()

    # Determine overall status
    if policy_status == "success" and outcome_status == "success":
        overall_status = "success"
    elif policy_status == "failed" or outcome_status == "failed":
        overall_status = "failed"
    else:
        overall_status = "aborted"

    # Create summaries
    policy_summary = HeadRunSummaryV1(
        head_type="policy",
        epochs_completed=policy_epochs_completed,
        epochs_target=config_lock.policy_config.epochs,
        final_loss=policy_final_loss,
        initial_loss=policy_initial_loss,
        loss_history=policy_loss_history if policy_loss_history else None,
        samples_processed=None,  # Would need to track in training
        training_time_seconds=policy_time,
        status=policy_status,
        error_message=policy_error,
    )

    outcome_summary = HeadRunSummaryV1(
        head_type="outcome",
        epochs_completed=outcome_epochs_completed,
        epochs_target=config_lock.outcome_config.epochs,
        final_loss=outcome_final_loss,
        initial_loss=outcome_initial_loss,
        loss_history=outcome_loss_history if outcome_loss_history else None,
        samples_processed=None,
        training_time_seconds=outcome_time,
        status=outcome_status,
        error_message=outcome_error,
    )

    # Compute config lock hash
    config_lock_hash = config_lock.determinism_hash

    # Create report (without determinism hash first)
    report_partial = TrainingRunReportV1(
        version="1.0",
        run_id=run_id,
        started_at=started_at,
        completed_at=completed_at,
        status=overall_status,
        config_lock_hash=config_lock_hash,
        config_lock_path=str(output_dir / "config_lock.json"),
        environment=environment,
        policy_run_summary=policy_summary,
        outcome_run_summary=outcome_summary,
        checkpoints=checkpoints
        if checkpoints
        else [
            # Placeholder if no checkpoints (shouldn't happen in success case)
            CheckpointReferenceV1(
                checkpoint_id=f"{run_id}-placeholder",
                checkpoint_type="final",
                epoch=0,
                file_hash="sha256:" + "0" * 64,
                file_size_bytes=0,
                created_at=completed_at,
            )
        ],
        metrics_log_path=str(output_dir / "training_metrics.jsonl"),
        total_wall_clock_seconds=total_seconds,
        total_wall_clock_formatted=_format_duration(total_seconds),
        warnings=warnings if warnings else None,
        failure_notes=(
            f"Policy: {policy_error}; Outcome: {outcome_error}"
            if overall_status != "success"
            else None
        ),
        audit_notes=(
            f"M31 training run completed with status={overall_status}. "
            f"Policy: {policy_epochs_completed}/{config_lock.policy_config.epochs} epochs. "
            f"Outcome: {outcome_epochs_completed}/{config_lock.outcome_config.epochs} epochs."
        ),
        determinism_hash="sha256:" + "0" * 64,  # Placeholder
    )

    # Compute determinism hash
    report_dict = report_partial.model_dump(mode="json", by_alias=True)
    del report_dict["determinismHash"]
    report_bytes = canonical_json_dump(report_dict)
    determinism_hash = _compute_sha256_bytes(report_bytes)

    # Create final report
    report = TrainingRunReportV1(
        **{**report_partial.model_dump(by_alias=False), "determinism_hash": determinism_hash}
    )

    # Save report
    report_path = output_dir / "training_run_report.json"
    report_dict = report.model_dump(mode="json", by_alias=True)
    report_json = canonical_json_dump(report_dict)
    report_path.write_bytes(report_json)

    return report
