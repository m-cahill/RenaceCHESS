"""Tests for M31 Full Training Run artifacts and infrastructure.

This module tests:
- TrainingConfigLockV1 schema and model
- TrainingRunReportV1 schema and model
- Training dataset v2 generator
- M31 training runner components

See docs/milestones/PhaseE/M31/M31_plan.md for the governing specification.
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

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
from renacechess.dataset.training_dataset_v2 import (
    M31_MIN_POSITIONS,
    M31_SELECTION_SEED,
    SKILL_BUCKETS,
    TRAINING_FEN_SEEDS,
    generate_training_dataset_v2,
    verify_training_dataset_v2,
)

# =============================================================================
# TrainingConfigLockV1 Schema Tests
# =============================================================================


class TestTrainingConfigLockV1Schema:
    """Tests for TrainingConfigLockV1 Pydantic model."""

    def test_minimal_valid_config_lock(self) -> None:
        """Test creating a minimal valid config lock."""
        now = datetime.now(UTC)

        policy_config = HeadConfigV1(
            model_type="BaselinePolicyV1",
            epochs=10,
            batch_size=32,
            learning_rate=0.001,
            seed=42,
        )

        outcome_config = HeadConfigV1(
            model_type="OutcomeHeadV1",
            epochs=10,
            batch_size=32,
            learning_rate=0.001,
            seed=42,
        )

        config_lock = TrainingConfigLockV1(
            version="1.0",
            created_at=now,
            code_commit_sha="a" * 40,
            dataset_manifest_hash="sha256:" + "b" * 64,
            frozen_eval_manifest_hash="sha256:" + "c" * 64,
            policy_config=policy_config,
            outcome_config=outcome_config,
            determinism_hash="sha256:" + "d" * 64,
        )

        assert config_lock.version == "1.0"
        assert config_lock.policy_config.epochs == 10
        assert config_lock.outcome_config.epochs == 10

    def test_full_config_lock_with_all_fields(self) -> None:
        """Test creating a config lock with all optional fields."""
        now = datetime.now(UTC)

        optimizer = OptimizerConfigV1(type="AdamW", weight_decay=0.01)
        scheduler = SchedulerConfigV1(enabled=False)

        policy_config = HeadConfigV1(
            model_type="BaselinePolicyV1",
            epochs=10,
            batch_size=256,
            learning_rate=0.001,
            seed=42,
            optimizer=optimizer,
            scheduler=scheduler,
            loss_function="CrossEntropyLoss",
            move_vocab_size=1000,
        )

        outcome_config = HeadConfigV1(
            model_type="OutcomeHeadV1",
            epochs=10,
            batch_size=256,
            learning_rate=0.001,
            seed=42,
            optimizer=optimizer,
            scheduler=scheduler,
        )

        env_reqs = EnvironmentRequirementsV1(
            device="auto",
            mixed_precision=False,
            deterministic=True,
        )

        checkpoint_policy = CheckpointPolicyV1(
            save_midpoint=True,
            save_final=True,
            output_dir="training_output",
        )

        source_templates = [
            SourceTemplateV1(
                path="training/configs/template_policy.yaml",
                hash="sha256:" + "e" * 64,
            ),
        ]

        config_lock = TrainingConfigLockV1(
            version="1.0",
            created_at=now,
            code_commit_sha="a" * 40,
            dataset_manifest_hash="sha256:" + "b" * 64,
            dataset_manifest_path="data/training/manifest.json",
            frozen_eval_manifest_hash="sha256:" + "c" * 64,
            frozen_eval_manifest_path="data/frozen_eval_v2/manifest.json",
            policy_config=policy_config,
            outcome_config=outcome_config,
            environment_requirements=env_reqs,
            checkpoint_policy=checkpoint_policy,
            source_templates=source_templates,
            audit_notes="M31 test config",
            determinism_hash="sha256:" + "d" * 64,
        )

        assert config_lock.environment_requirements is not None
        assert config_lock.environment_requirements.mixed_precision is False
        assert config_lock.checkpoint_policy is not None
        assert config_lock.checkpoint_policy.save_final is True
        assert len(config_lock.source_templates or []) == 1

    def test_config_lock_json_serialization(self) -> None:
        """Test that config lock serializes to JSON correctly with camelCase aliases."""
        now = datetime.now(UTC)

        policy_config = HeadConfigV1(
            model_type="BaselinePolicyV1",
            epochs=10,
            batch_size=32,
            learning_rate=0.001,
            seed=42,
        )

        outcome_config = HeadConfigV1(
            model_type="OutcomeHeadV1",
            epochs=10,
            batch_size=32,
            learning_rate=0.001,
            seed=42,
        )

        config_lock = TrainingConfigLockV1(
            version="1.0",
            created_at=now,
            code_commit_sha="a" * 40,
            dataset_manifest_hash="sha256:" + "b" * 64,
            frozen_eval_manifest_hash="sha256:" + "c" * 64,
            policy_config=policy_config,
            outcome_config=outcome_config,
            determinism_hash="sha256:" + "d" * 64,
        )

        json_dict = config_lock.model_dump(mode="json", by_alias=True)

        # Check camelCase aliases
        assert "createdAt" in json_dict
        assert "codeCommitSha" in json_dict
        assert "datasetManifestHash" in json_dict
        assert "frozenEvalManifestHash" in json_dict
        assert "policyConfig" in json_dict
        assert "outcomeConfig" in json_dict
        assert "determinismHash" in json_dict

        # Check nested camelCase
        assert "modelType" in json_dict["policyConfig"]
        assert "batchSize" in json_dict["policyConfig"]
        assert "learningRate" in json_dict["policyConfig"]


# =============================================================================
# TrainingRunReportV1 Schema Tests
# =============================================================================


class TestTrainingRunReportV1Schema:
    """Tests for TrainingRunReportV1 Pydantic model."""

    def test_minimal_valid_report(self) -> None:
        """Test creating a minimal valid training run report."""
        now = datetime.now(UTC)

        environment = ExecutionEnvironmentV1(
            gpu_name="NVIDIA GeForce RTX 5090",
            cuda_version="12.8",
            torch_version="2.10.0",
            python_version="3.12.0",
            os="Windows 10",
        )

        policy_summary = HeadRunSummaryV1(
            head_type="policy",
            epochs_completed=10,
            epochs_target=10,
            final_loss=0.5,
            status="success",
        )

        outcome_summary = HeadRunSummaryV1(
            head_type="outcome",
            epochs_completed=10,
            epochs_target=10,
            final_loss=0.3,
            status="success",
        )

        checkpoint = CheckpointReferenceV1(
            checkpoint_id="test-checkpoint-001",
            checkpoint_type="final",
            epoch=10,
            file_hash="sha256:" + "a" * 64,
            file_size_bytes=1024 * 1024 * 100,  # 100 MB
            created_at=now,
        )

        report = TrainingRunReportV1(
            version="1.0",
            run_id="m31-test-run",
            started_at=now,
            completed_at=now,
            status="success",
            config_lock_hash="sha256:" + "b" * 64,
            environment=environment,
            policy_run_summary=policy_summary,
            outcome_run_summary=outcome_summary,
            checkpoints=[checkpoint],
            determinism_hash="sha256:" + "c" * 64,
        )

        assert report.status == "success"
        assert len(report.checkpoints) == 1
        assert report.policy_run_summary.epochs_completed == 10

    def test_report_with_failure(self) -> None:
        """Test creating a report with failure status."""
        now = datetime.now(UTC)

        environment = ExecutionEnvironmentV1(
            gpu_name="CPU",
            cuda_version="N/A",
            torch_version="2.10.0",
            python_version="3.12.0",
            os="Linux",
        )

        policy_summary = HeadRunSummaryV1(
            head_type="policy",
            epochs_completed=5,
            epochs_target=10,
            final_loss=1.2,
            status="failed",
            error_message="Out of memory",
        )

        outcome_summary = HeadRunSummaryV1(
            head_type="outcome",
            epochs_completed=0,
            epochs_target=10,
            final_loss=0.0,
            status="aborted",
        )

        checkpoint = CheckpointReferenceV1(
            checkpoint_id="test-checkpoint-partial",
            checkpoint_type="epoch",
            epoch=5,
            file_hash="sha256:" + "a" * 64,
            file_size_bytes=1024 * 1024,
            created_at=now,
        )

        report = TrainingRunReportV1(
            version="1.0",
            run_id="m31-failed-run",
            started_at=now,
            completed_at=now,
            status="failed",
            config_lock_hash="sha256:" + "b" * 64,
            environment=environment,
            policy_run_summary=policy_summary,
            outcome_run_summary=outcome_summary,
            checkpoints=[checkpoint],
            failure_notes="Policy training failed due to OOM",
            determinism_hash="sha256:" + "c" * 64,
        )

        assert report.status == "failed"
        assert report.failure_notes is not None
        assert policy_summary.error_message == "Out of memory"

    def test_report_json_serialization(self) -> None:
        """Test that report serializes to JSON correctly with camelCase aliases."""
        now = datetime.now(UTC)

        environment = ExecutionEnvironmentV1(
            gpu_name="GPU",
            cuda_version="12.0",
            torch_version="2.0.0",
            python_version="3.11.0",
            os="Linux",
        )

        policy_summary = HeadRunSummaryV1(
            head_type="policy",
            epochs_completed=10,
            epochs_target=10,
            final_loss=0.5,
            status="success",
        )

        outcome_summary = HeadRunSummaryV1(
            head_type="outcome",
            epochs_completed=10,
            epochs_target=10,
            final_loss=0.3,
            status="success",
        )

        checkpoint = CheckpointReferenceV1(
            checkpoint_id="test",
            checkpoint_type="final",
            epoch=10,
            file_hash="sha256:" + "a" * 64,
            file_size_bytes=1000,
            created_at=now,
        )

        report = TrainingRunReportV1(
            version="1.0",
            run_id="test",
            started_at=now,
            completed_at=now,
            status="success",
            config_lock_hash="sha256:" + "b" * 64,
            environment=environment,
            policy_run_summary=policy_summary,
            outcome_run_summary=outcome_summary,
            checkpoints=[checkpoint],
            total_wall_clock_seconds=3600.0,
            total_wall_clock_formatted="1h 0m 0s",
            determinism_hash="sha256:" + "c" * 64,
        )

        json_dict = report.model_dump(mode="json", by_alias=True)

        # Check camelCase aliases
        assert "runId" in json_dict
        assert "startedAt" in json_dict
        assert "completedAt" in json_dict
        assert "configLockHash" in json_dict
        assert "policyRunSummary" in json_dict
        assert "outcomeRunSummary" in json_dict
        assert "totalWallClockSeconds" in json_dict


# =============================================================================
# Training Dataset V2 Generator Tests
# =============================================================================


class TestTrainingDatasetV2Generator:
    """Tests for the training dataset v2 generator."""

    def test_generator_constants(self) -> None:
        """Test that generator constants are correctly defined."""
        assert M31_MIN_POSITIONS == 50_000
        assert M31_SELECTION_SEED == 12345  # Different from frozen eval's 42
        assert len(SKILL_BUCKETS) == 7
        assert len(TRAINING_FEN_SEEDS) > 0

    def test_training_fens_are_distinct_from_frozen_eval(self) -> None:
        """Test that training FEN seeds don't overlap with frozen eval seeds."""
        from renacechess.frozen_eval.generator_v2 import FEN_SEEDS as FROZEN_EVAL_FENS

        training_set = set(TRAINING_FEN_SEEDS)
        frozen_eval_set = set(FROZEN_EVAL_FENS)

        # There should be minimal or no overlap
        overlap = training_set & frozen_eval_set
        # Allow some overlap in common openings, but most should be distinct
        assert len(overlap) < len(TRAINING_FEN_SEEDS) / 2, (
            f"Too much overlap between training and frozen eval FENs: {len(overlap)}"
        )

    def test_generate_small_training_dataset(self) -> None:
        """Test generating a small training dataset for validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "training_data"
            now = datetime(2026, 2, 3, 12, 0, 0, tzinfo=UTC)

            # Generate small dataset (minimum viable)
            manifest = generate_training_dataset_v2(
                output_dir=output_dir,
                target_positions=M31_MIN_POSITIONS,  # 50k minimum
                seed=M31_SELECTION_SEED,
                shard_size=10_000,
                created_at=now,
            )

            # Verify manifest
            assert manifest.schema_version == "v2"
            assert len(manifest.shard_refs) > 0

            # Verify total position count
            total_positions = sum(ref.records for ref in manifest.shard_refs)
            assert total_positions == M31_MIN_POSITIONS

            # Verify manifest file was written
            manifest_path = output_dir / "manifest.json"
            assert manifest_path.exists()

            # Verify shards were written
            shards_dir = output_dir / "shards"
            assert shards_dir.exists()
            shard_files = list(shards_dir.glob("*.jsonl"))
            assert len(shard_files) == len(manifest.shard_refs)

    def test_training_dataset_determinism(self) -> None:
        """Test that training dataset generation is deterministic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            now = datetime(2026, 2, 3, 12, 0, 0, tzinfo=UTC)

            # Generate twice with same seed
            output1 = Path(tmpdir) / "run1"
            manifest1 = generate_training_dataset_v2(
                output_dir=output1,
                target_positions=M31_MIN_POSITIONS,
                seed=M31_SELECTION_SEED,
                created_at=now,
            )

            output2 = Path(tmpdir) / "run2"
            manifest2 = generate_training_dataset_v2(
                output_dir=output2,
                target_positions=M31_MIN_POSITIONS,
                seed=M31_SELECTION_SEED,
                created_at=now,
            )

            # Digests should be identical
            assert manifest1.dataset_digest == manifest2.dataset_digest

            # Shard hashes should be identical
            for ref1, ref2 in zip(manifest1.shard_refs, manifest2.shard_refs, strict=True):
                assert ref1.hash == ref2.hash

    def test_verify_training_dataset(self) -> None:
        """Test verification of training dataset integrity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "training_data"
            now = datetime(2026, 2, 3, 12, 0, 0, tzinfo=UTC)

            generate_training_dataset_v2(
                output_dir=output_dir,
                target_positions=M31_MIN_POSITIONS,
                seed=M31_SELECTION_SEED,
                created_at=now,
            )

            manifest_path = output_dir / "manifest.json"

            # Verification should pass
            assert verify_training_dataset_v2(manifest_path) is True

    def test_training_dataset_splits(self) -> None:
        """Test that training dataset has split assignments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "training_data"
            now = datetime(2026, 2, 3, 12, 0, 0, tzinfo=UTC)

            manifest = generate_training_dataset_v2(
                output_dir=output_dir,
                target_positions=M31_MIN_POSITIONS,
                seed=M31_SELECTION_SEED,
                created_at=now,
            )

            # Check split assignments exist
            assert manifest.split_assignments is not None
            assert len(manifest.split_assignments.train) > 0
            assert len(manifest.split_assignments.val) > 0

            # All shards should be assigned
            total_shards = len(manifest.shard_refs)
            assert len(manifest.split_assignments.train) == total_shards

    def test_training_positions_have_game_result(self) -> None:
        """Test that training positions include game result for outcome head."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "training_data"
            now = datetime(2026, 2, 3, 12, 0, 0, tzinfo=UTC)

            generate_training_dataset_v2(
                output_dir=output_dir,
                target_positions=M31_MIN_POSITIONS,
                seed=M31_SELECTION_SEED,
                created_at=now,
            )

            # Read first shard and check for game result
            shard_path = output_dir / "shards" / "shard_000.jsonl"
            with shard_path.open() as f:
                first_line = f.readline()
                record = json.loads(first_line)

                # Should have game result in meta
                assert "meta" in record
                assert "gameResult" in record["meta"]
                assert record["meta"]["gameResult"] in ["win", "draw", "loss"]


# =============================================================================
# EpochMetricsV1 Tests
# =============================================================================


class TestEpochMetricsV1:
    """Tests for EpochMetricsV1 model."""

    def test_minimal_epoch_metrics(self) -> None:
        """Test creating minimal epoch metrics."""
        metrics = EpochMetricsV1(epoch=1, loss=0.5)
        assert metrics.epoch == 1
        assert metrics.loss == 0.5

    def test_full_epoch_metrics(self) -> None:
        """Test creating epoch metrics with all fields."""
        metrics = EpochMetricsV1(
            epoch=5,
            loss=0.25,
            accuracy=0.85,
            learning_rate=0.0005,
            wall_clock_seconds=120.5,
            vram_peak_gb=8.5,
        )

        assert metrics.epoch == 5
        assert metrics.accuracy == 0.85
        assert metrics.learning_rate == 0.0005
        assert metrics.wall_clock_seconds == 120.5
        assert metrics.vram_peak_gb == 8.5


# =============================================================================
# CheckpointReferenceV1 Tests
# =============================================================================


class TestCheckpointReferenceV1:
    """Tests for CheckpointReferenceV1 model."""

    def test_minimal_checkpoint_reference(self) -> None:
        """Test creating a minimal checkpoint reference."""
        now = datetime.now(UTC)

        ref = CheckpointReferenceV1(
            checkpoint_id="test-001",
            checkpoint_type="final",
            epoch=10,
            file_hash="sha256:" + "a" * 64,
            file_size_bytes=1024 * 1024 * 50,
            created_at=now,
        )

        assert ref.checkpoint_type == "final"
        assert ref.epoch == 10

    def test_full_checkpoint_reference(self) -> None:
        """Test creating a checkpoint reference with all fields."""
        now = datetime.now(UTC)

        ref = CheckpointReferenceV1(
            checkpoint_id="m31-policy-midpoint",
            checkpoint_type="midpoint",
            head_type="policy",
            epoch=5,
            step=5000,
            file_hash="sha256:" + "b" * 64,
            file_size_bytes=1024 * 1024 * 150,
            file_size_formatted="150.0 MB",
            file_path="/external/storage/checkpoints/m31-policy-midpoint.pt",
            created_at=now,
        )

        assert ref.head_type == "policy"
        assert ref.step == 5000
        assert ref.file_size_formatted == "150.0 MB"


# =============================================================================
# Integration Tests
# =============================================================================


class TestM31Integration:
    """Integration tests for M31 components working together."""

    def test_config_lock_to_report_hash_chain(self) -> None:
        """Test that report correctly references config lock hash."""
        now = datetime.now(UTC)

        # Create config lock
        policy_config = HeadConfigV1(
            model_type="BaselinePolicyV1",
            epochs=10,
            batch_size=32,
            learning_rate=0.001,
            seed=42,
        )

        outcome_config = HeadConfigV1(
            model_type="OutcomeHeadV1",
            epochs=10,
            batch_size=32,
            learning_rate=0.001,
            seed=42,
        )

        config_lock = TrainingConfigLockV1(
            version="1.0",
            created_at=now,
            code_commit_sha="a" * 40,
            dataset_manifest_hash="sha256:" + "b" * 64,
            frozen_eval_manifest_hash="sha256:" + "c" * 64,
            policy_config=policy_config,
            outcome_config=outcome_config,
            determinism_hash="sha256:" + "d" * 64,
        )

        # Create report referencing config lock
        environment = ExecutionEnvironmentV1(
            gpu_name="GPU",
            cuda_version="12.0",
            torch_version="2.0.0",
            python_version="3.12.0",
            os="Linux",
        )

        policy_summary = HeadRunSummaryV1(
            head_type="policy",
            epochs_completed=10,
            epochs_target=10,
            final_loss=0.5,
            status="success",
        )

        outcome_summary = HeadRunSummaryV1(
            head_type="outcome",
            epochs_completed=10,
            epochs_target=10,
            final_loss=0.3,
            status="success",
        )

        checkpoint = CheckpointReferenceV1(
            checkpoint_id="test",
            checkpoint_type="final",
            epoch=10,
            file_hash="sha256:" + "e" * 64,
            file_size_bytes=1000,
            created_at=now,
        )

        report = TrainingRunReportV1(
            version="1.0",
            run_id="test-run",
            started_at=now,
            completed_at=now,
            status="success",
            config_lock_hash=config_lock.determinism_hash,  # Reference config lock
            environment=environment,
            policy_run_summary=policy_summary,
            outcome_run_summary=outcome_summary,
            checkpoints=[checkpoint],
            determinism_hash="sha256:" + "f" * 64,
        )

        # Verify hash chain
        assert report.config_lock_hash == config_lock.determinism_hash

    def test_m31_epochs_are_locked_at_10(self) -> None:
        """Test that M31 epoch count is correctly locked at 10."""
        from renacechess.models.m31_training_runner import M31_EPOCHS

        assert M31_EPOCHS == 10
