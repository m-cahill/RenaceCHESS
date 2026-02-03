"""Tests for M33 external proof pack builder and verifier."""

import json
from pathlib import Path

import pytest

from renacechess.contracts.models import ExternalProofPackV1
from renacechess.proof_pack.build_proof_pack import build_proof_pack
from renacechess.proof_pack.verify_proof_pack import (
    ProofPackVerificationError,
    verify_proof_pack,
)


class TestBuildProofPack:
    """Tests for proof pack builder."""

    def test_build_proof_pack_creates_manifest(
        self,
        tmp_path: Path,
        frozen_eval_manifest_path: Path,
        frozen_eval_provenance_path: Path,
        training_config_lock_path: Path,
        training_run_report_path: Path,
        post_train_eval_report_path: Path,
    ) -> None:
        """Test that build_proof_pack creates manifest."""
        output_dir = tmp_path / "proof_pack_v1"

        manifest = build_proof_pack(
            output_dir=output_dir,
            frozen_eval_manifest_path=frozen_eval_manifest_path,
            frozen_eval_provenance_path=frozen_eval_provenance_path,
            training_config_lock_path=training_config_lock_path,
            training_run_report_path=training_run_report_path,
            post_train_eval_report_path=post_train_eval_report_path,
        )

        assert isinstance(manifest, ExternalProofPackV1)
        assert manifest.schema_version == 1
        assert manifest.project == "RenaceCHESS"
        assert manifest.phase == "E"
        assert manifest.included_milestones == ["M30", "M31", "M32"]

    def test_build_proof_pack_copies_artifacts(
        self,
        tmp_path: Path,
        frozen_eval_manifest_path: Path,
        frozen_eval_provenance_path: Path,
        training_config_lock_path: Path,
        training_run_report_path: Path,
        post_train_eval_report_path: Path,
    ) -> None:
        """Test that build_proof_pack copies all artifacts."""
        output_dir = tmp_path / "proof_pack_v1"

        manifest = build_proof_pack(
            output_dir=output_dir,
            frozen_eval_manifest_path=frozen_eval_manifest_path,
            frozen_eval_provenance_path=frozen_eval_provenance_path,
            training_config_lock_path=training_config_lock_path,
            training_run_report_path=training_run_report_path,
            post_train_eval_report_path=post_train_eval_report_path,
        )

        # Check frozen eval artifacts
        assert (output_dir / "frozen_eval/manifest.json").exists()
        assert (output_dir / "frozen_eval/provenance.json").exists()

        # Check training artifacts
        assert (output_dir / "training/config_lock.json").exists()
        assert (output_dir / "training/training_run_report.json").exists()

        # Check evaluation artifacts
        assert (output_dir / "evaluation/post_train_eval_report.json").exists()

        # Check manifest
        assert (output_dir / "proof_pack_manifest.json").exists()

        # Check README
        assert (output_dir / "README.md").exists()

        # Check schemas
        assert (output_dir / "schemas").exists()
        assert (output_dir / "schemas/external_proof_pack.v1.schema.json").exists()

    def test_build_proof_pack_computes_hashes(
        self,
        tmp_path: Path,
        frozen_eval_manifest_path: Path,
        frozen_eval_provenance_path: Path,
        training_config_lock_path: Path,
        training_run_report_path: Path,
        post_train_eval_report_path: Path,
    ) -> None:
        """Test that build_proof_pack computes correct hashes."""
        output_dir = tmp_path / "proof_pack_v1"

        manifest = build_proof_pack(
            output_dir=output_dir,
            frozen_eval_manifest_path=frozen_eval_manifest_path,
            frozen_eval_provenance_path=frozen_eval_provenance_path,
            training_config_lock_path=training_config_lock_path,
            training_run_report_path=training_run_report_path,
            post_train_eval_report_path=post_train_eval_report_path,
        )

        # Hashes should be present
        assert manifest.artifacts.frozen_eval.manifest_hash.startswith("sha256:")
        assert manifest.artifacts.frozen_eval.provenance_hash.startswith("sha256:")
        assert manifest.artifacts.training.config_lock_hash.startswith("sha256:")
        assert manifest.artifacts.training.run_report_hash.startswith("sha256:")
        assert manifest.artifacts.evaluation.report_hash.startswith("sha256:")

    def test_build_proof_pack_includes_checkpoint_metadata(
        self,
        tmp_path: Path,
        frozen_eval_manifest_path: Path,
        frozen_eval_provenance_path: Path,
        training_config_lock_path: Path,
        training_run_report_path: Path,
        post_train_eval_report_path: Path,
    ) -> None:
        """Test that build_proof_pack includes checkpoint metadata."""
        output_dir = tmp_path / "proof_pack_v1"

        manifest = build_proof_pack(
            output_dir=output_dir,
            frozen_eval_manifest_path=frozen_eval_manifest_path,
            frozen_eval_provenance_path=frozen_eval_provenance_path,
            training_config_lock_path=training_config_lock_path,
            training_run_report_path=training_run_report_path,
            post_train_eval_report_path=post_train_eval_report_path,
        )

        # Checkpoint metadata should be present
        assert "policy" in manifest.artifacts.training.checkpoints
        assert "outcome" in manifest.artifacts.training.checkpoints

        policy_checkpoint = manifest.artifacts.training.checkpoints["policy"]
        assert policy_checkpoint.hash.startswith("sha256:")
        assert policy_checkpoint.file_size_bytes > 0
        assert policy_checkpoint.external_storage is True

        outcome_checkpoint = manifest.artifacts.training.checkpoints["outcome"]
        assert outcome_checkpoint.hash.startswith("sha256:")
        assert outcome_checkpoint.file_size_bytes > 0
        assert outcome_checkpoint.external_storage is True

    def test_build_proof_pack_includes_limitations(
        self,
        tmp_path: Path,
        frozen_eval_manifest_path: Path,
        frozen_eval_provenance_path: Path,
        training_config_lock_path: Path,
        training_run_report_path: Path,
        post_train_eval_report_path: Path,
    ) -> None:
        """Test that build_proof_pack includes limitations."""
        output_dir = tmp_path / "proof_pack_v1"

        manifest = build_proof_pack(
            output_dir=output_dir,
            frozen_eval_manifest_path=frozen_eval_manifest_path,
            frozen_eval_provenance_path=frozen_eval_provenance_path,
            training_config_lock_path=training_config_lock_path,
            training_run_report_path=training_run_report_path,
            post_train_eval_report_path=post_train_eval_report_path,
        )

        # Limitations should be present
        assert manifest.limitations.training_vocabulary.move_count > 0
        assert len(manifest.limitations.training_vocabulary.explanation) > 0
        assert manifest.limitations.synthetic_eval_set.is_synthetic is True
        assert len(manifest.limitations.scope.proven) > 0
        assert len(manifest.limitations.scope.not_proven) > 0

    def test_build_proof_pack_computes_determinism_hash(
        self,
        tmp_path: Path,
        frozen_eval_manifest_path: Path,
        frozen_eval_provenance_path: Path,
        training_config_lock_path: Path,
        training_run_report_path: Path,
        post_train_eval_report_path: Path,
    ) -> None:
        """Test that build_proof_pack computes determinism hash."""
        output_dir = tmp_path / "proof_pack_v1"

        manifest = build_proof_pack(
            output_dir=output_dir,
            frozen_eval_manifest_path=frozen_eval_manifest_path,
            frozen_eval_provenance_path=frozen_eval_provenance_path,
            training_config_lock_path=training_config_lock_path,
            training_run_report_path=training_run_report_path,
            post_train_eval_report_path=post_train_eval_report_path,
        )

        assert manifest.determinism_hash.startswith("sha256:")
        assert len(manifest.determinism_hash) == 71  # "sha256:" + 64 hex chars

    def test_build_proof_pack_fails_on_missing_artifact(
        self,
        tmp_path: Path,
        frozen_eval_manifest_path: Path,
        frozen_eval_provenance_path: Path,
        training_config_lock_path: Path,
        training_run_report_path: Path,
        post_train_eval_report_path: Path,
    ) -> None:
        """Test that build_proof_pack fails if artifact is missing."""
        output_dir = tmp_path / "proof_pack_v1"
        missing_path = tmp_path / "missing.json"

        with pytest.raises(FileNotFoundError):
            build_proof_pack(
                output_dir=output_dir,
                frozen_eval_manifest_path=missing_path,
                frozen_eval_provenance_path=frozen_eval_provenance_path,
                training_config_lock_path=training_config_lock_path,
                training_run_report_path=training_run_report_path,
                post_train_eval_report_path=post_train_eval_report_path,
            )


class TestVerifyProofPack:
    """Tests for proof pack verifier."""

    def test_verify_proof_pack_passes_valid_pack(
        self,
        tmp_path: Path,
        frozen_eval_manifest_path: Path,
        frozen_eval_provenance_path: Path,
        training_config_lock_path: Path,
        training_run_report_path: Path,
        post_train_eval_report_path: Path,
    ) -> None:
        """Test that verify_proof_pack passes valid pack."""
        output_dir = tmp_path / "proof_pack_v1"

        # Build pack
        build_proof_pack(
            output_dir=output_dir,
            frozen_eval_manifest_path=frozen_eval_manifest_path,
            frozen_eval_provenance_path=frozen_eval_provenance_path,
            training_config_lock_path=training_config_lock_path,
            training_run_report_path=training_run_report_path,
            post_train_eval_report_path=post_train_eval_report_path,
        )

        # Verify
        is_valid, errors = verify_proof_pack(output_dir)

        if not is_valid:
            print(f"Verification errors: {errors}")
        assert is_valid is True, f"Verification failed: {errors}"
        assert len(errors) == 0

    def test_verify_proof_pack_fails_missing_manifest(
        self, tmp_path: Path
    ) -> None:
        """Test that verify_proof_pack fails if manifest is missing."""
        output_dir = tmp_path / "proof_pack_v1"
        output_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            verify_proof_pack(output_dir)

    def test_verify_proof_pack_fails_missing_artifact(
        self,
        tmp_path: Path,
        frozen_eval_manifest_path: Path,
        frozen_eval_provenance_path: Path,
        training_config_lock_path: Path,
        training_run_report_path: Path,
        post_train_eval_report_path: Path,
    ) -> None:
        """Test that verify_proof_pack fails if artifact is missing."""
        output_dir = tmp_path / "proof_pack_v1"

        # Build pack
        build_proof_pack(
            output_dir=output_dir,
            frozen_eval_manifest_path=frozen_eval_manifest_path,
            frozen_eval_provenance_path=frozen_eval_provenance_path,
            training_config_lock_path=training_config_lock_path,
            training_run_report_path=training_run_report_path,
            post_train_eval_report_path=post_train_eval_report_path,
        )

        # Remove an artifact
        (output_dir / "frozen_eval/manifest.json").unlink()

        # Verify
        is_valid, errors = verify_proof_pack(output_dir)

        assert is_valid is False
        assert len(errors) > 0
        assert any("not found" in error.lower() for error in errors)

    def test_verify_proof_pack_fails_hash_mismatch(
        self,
        tmp_path: Path,
        frozen_eval_manifest_path: Path,
        frozen_eval_provenance_path: Path,
        training_config_lock_path: Path,
        training_run_report_path: Path,
        post_train_eval_report_path: Path,
    ) -> None:
        """Test that verify_proof_pack fails on hash mismatch."""
        output_dir = tmp_path / "proof_pack_v1"

        # Build pack
        build_proof_pack(
            output_dir=output_dir,
            frozen_eval_manifest_path=frozen_eval_manifest_path,
            frozen_eval_provenance_path=frozen_eval_provenance_path,
            training_config_lock_path=training_config_lock_path,
            training_run_report_path=training_run_report_path,
            post_train_eval_report_path=post_train_eval_report_path,
        )

        # Corrupt an artifact
        artifact_path = output_dir / "frozen_eval/manifest.json"
        artifact_path.write_text("corrupted", encoding="utf-8")

        # Verify
        is_valid, errors = verify_proof_pack(output_dir)

        assert is_valid is False
        assert len(errors) > 0
        assert any("hash mismatch" in error.lower() for error in errors)

    def test_verify_proof_pack_fails_invalid_manifest_schema(
        self, tmp_path: Path
    ) -> None:
        """Test that verify_proof_pack fails on invalid manifest schema."""
        output_dir = tmp_path / "proof_pack_v1"
        output_dir.mkdir()

        # Create invalid manifest
        manifest_path = output_dir / "proof_pack_manifest.json"
        manifest_path.write_text('{"invalid": "schema"}', encoding="utf-8")

        # Verify
        is_valid, errors = verify_proof_pack(output_dir)

        assert is_valid is False
        assert len(errors) > 0
        assert any("validation" in error.lower() for error in errors)


# Fixtures


@pytest.fixture
def frozen_eval_manifest_path() -> Path:
    """Path to frozen eval v2 manifest."""
    return Path("data/frozen_eval_v2/manifest.json")


@pytest.fixture
def frozen_eval_provenance_path() -> Path:
    """Path to frozen eval v2 provenance."""
    return Path("data/frozen_eval_v2/provenance.json")


@pytest.fixture
def training_config_lock_path() -> Path:
    """Path to training config lock."""
    return Path("artifacts/m31_training_run/config_lock.json")


@pytest.fixture
def training_run_report_path() -> Path:
    """Path to training run report."""
    return Path("artifacts/m31_training_run/training_run_report.json")


@pytest.fixture
def post_train_eval_report_path() -> Path:
    """Path to post-train eval report."""
    return Path("artifacts/m32_post_train_eval/post_train_eval_report.json")

