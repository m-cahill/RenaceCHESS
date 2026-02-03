"""Builder for M33 external proof pack.

This module gathers artifacts from M30, M31, and M32 and packages them
into a self-contained proof bundle for external auditors.
"""

import hashlib
import json
import shutil
from pathlib import Path

from renacechess.contracts.models import (
    ArtifactsV1,
    CheckpointMetadataV1,
    EvaluationArtifactsV1,
    ExternalProofPackV1,
    FrozenEvalArtifactsV1,
    HashChainV1,
    LimitationsV1,
    ScopeLimitationV1,
    SyntheticEvalSetLimitationV1,
    TrainingArtifactsV1,
    TrainingVocabularyLimitationV1,
)
from renacechess.determinism import compute_determinism_hash


def _compute_sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file.

    Args:
        path: Path to file.

    Returns:
        Hash string in format 'sha256:<hex>'.
    """
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def _copy_file_to_pack(
    source: Path, dest_dir: Path, relative_path: str
) -> tuple[Path, str]:
    """Copy a file to proof pack directory and compute hash.

    Args:
        source: Source file path.
        dest_dir: Destination directory in proof pack.
        relative_path: Relative path within proof pack.

    Returns:
        Tuple of (destination path, hash).
    """
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    dest_path = dest_dir / relative_path
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest_path)

    hash_value = _compute_sha256_file(dest_path)
    return dest_path, hash_value


def _load_json(path: Path) -> dict[str, object]:
    """Load JSON file.

    Args:
        path: Path to JSON file.

    Returns:
        Parsed JSON as dict.
    """
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_proof_pack(
    output_dir: Path,
    frozen_eval_manifest_path: Path,
    frozen_eval_provenance_path: Path,
    training_config_lock_path: Path,
    training_run_report_path: Path,
    post_train_eval_report_path: Path,
) -> ExternalProofPackV1:
    """Build external proof pack from M30-M32 artifacts.

    This function gathers all artifacts, copies them to the proof pack directory,
    computes hashes, and generates the manifest. It does NOT include checkpoint
    files (those are external storage only).

    Args:
        output_dir: Directory where proof pack will be created (e.g., proof_pack_v1/).
        frozen_eval_manifest_path: Path to frozen eval v2 manifest (M30).
        frozen_eval_provenance_path: Path to frozen eval v2 provenance (M30).
        training_config_lock_path: Path to training config lock (M31).
        training_run_report_path: Path to training run report (M31).
        post_train_eval_report_path: Path to post-train eval report (M32).

    Returns:
        ExternalProofPackV1 manifest.

    Raises:
        FileNotFoundError: If any required artifact is missing.
        ValueError: If artifact validation fails.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load artifacts to extract checkpoint metadata
    training_run_report = _load_json(training_run_report_path)
    post_train_eval_report = _load_json(post_train_eval_report_path)

    # Extract checkpoint metadata from training run report
    checkpoints_data = training_run_report.get("checkpoints", [])
    policy_checkpoint = next(
        (c for c in checkpoints_data if c.get("headType") == "policy"), None
    )
    outcome_checkpoint = next(
        (c for c in checkpoints_data if c.get("headType") == "outcome"), None
    )

    if not policy_checkpoint or not outcome_checkpoint:
        raise ValueError("Training run report missing checkpoint metadata")

    # Copy frozen eval artifacts
    frozen_eval_manifest_dest, frozen_eval_manifest_hash = _copy_file_to_pack(
        frozen_eval_manifest_path, output_dir, "frozen_eval/manifest.json"
    )
    frozen_eval_provenance_dest, frozen_eval_provenance_hash = _copy_file_to_pack(
        frozen_eval_provenance_path, output_dir, "frozen_eval/provenance.json"
    )

    # Copy training artifacts
    training_config_lock_dest, training_config_lock_hash = _copy_file_to_pack(
        training_config_lock_path, output_dir, "training/config_lock.json"
    )
    training_run_report_dest, training_run_report_hash = _copy_file_to_pack(
        training_run_report_path, output_dir, "training/training_run_report.json"
    )

    # Copy evaluation artifacts
    post_train_eval_report_dest, post_train_eval_report_hash = _copy_file_to_pack(
        post_train_eval_report_path, output_dir, "evaluation/post_train_eval_report.json"
    )

    # Build checkpoint metadata (files not included)
    checkpoint_metadata = {
        "policy": CheckpointMetadataV1(
            hash=policy_checkpoint["fileHash"],
            file_size_bytes=policy_checkpoint["fileSizeBytes"],
            expected_filename=Path(policy_checkpoint["filePath"]).name,
            external_storage=True,
        ),
        "outcome": CheckpointMetadataV1(
            hash=outcome_checkpoint["fileHash"],
            file_size_bytes=outcome_checkpoint["fileSizeBytes"],
            expected_filename=Path(outcome_checkpoint["filePath"]).name,
            external_storage=True,
        ),
    }

    # Build artifacts structure
    artifacts = ArtifactsV1(
        frozen_eval=FrozenEvalArtifactsV1(
            manifest_path="frozen_eval/manifest.json",
            provenance_path="frozen_eval/provenance.json",
            manifest_hash=frozen_eval_manifest_hash,
            provenance_hash=frozen_eval_provenance_hash,
        ),
        training=TrainingArtifactsV1(
            config_lock_path="training/config_lock.json",
            run_report_path="training/training_run_report.json",
            config_lock_hash=training_config_lock_hash,
            run_report_hash=training_run_report_hash,
            checkpoints=checkpoint_metadata,
        ),
        evaluation=EvaluationArtifactsV1(
            report_path="evaluation/post_train_eval_report.json",
            report_hash=post_train_eval_report_hash,
        ),
    )

    # Build hash chain
    hash_chain = HashChainV1(
        frozen_eval_manifest_hash=frozen_eval_manifest_hash,
        training_config_lock_hash=training_config_lock_hash,
        training_run_report_hash=training_run_report_hash,
        post_train_eval_report_hash=post_train_eval_report_hash,
    )

    # Extract training vocabulary info from config lock
    config_lock = _load_json(training_config_lock_path)
    policy_config = config_lock.get("policyConfig", {})
    move_vocab_size = policy_config.get("moveVocabSize", 8)

    # Build limitations
    limitations = LimitationsV1(
        training_vocabulary=TrainingVocabularyLimitationV1(
            move_count=move_vocab_size,
            explanation=(
                f"Training used a constrained vocabulary of {move_vocab_size} moves. "
                "This causes expected degradation in evaluation metrics compared to baseline "
                "because the trained model is specialized to a narrow move distribution, "
                "while the baseline has uniform probability over the vocabulary and occasionally "
                "matches correct moves by chance. Infrastructure validation objective achieved; "
                "production training will use full move vocabulary."
            ),
        ),
        synthetic_eval_set=SyntheticEvalSetLimitationV1(
            is_synthetic=True,
            explanation=(
                "Frozen eval v2 is a synthetic, chess-valid evaluation set generated "
                "algorithmically from curated FEN seeds. It is intended for relative evaluation "
                "and calibration stability, not absolute strength claims. All positions are "
                "chess-valid but not drawn from real game data."
            ),
        ),
        scope=ScopeLimitationV1(
            proven=[
                "Pipeline integrity: Training → evaluation → reporting is end-to-end consistent",
                "Contract discipline: Schema-first design survived real execution",
                "Scientific honesty: Degraded results are reported, not hidden or reframed",
                "Reproducibility: All artifacts are hash-chained and replayable",
            ],
            not_proven=[
                "Chess playing strength (training vocabulary too constrained)",
                "Full-vocab performance (only 8 moves trained)",
                "Absolute model quality (synthetic eval set, not real games)",
            ],
        ),
    )

    # Build manifest dict first (without determinism hash)
    manifest_dict = {
        "schemaVersion": 1,
        "project": "RenaceCHESS",
        "phase": "E",
        "includedMilestones": ["M30", "M31", "M32"],
        "artifacts": artifacts.model_dump(mode="json"),
        "hashChain": hash_chain.model_dump(mode="json"),
        "limitations": limitations.model_dump(mode="json"),
    }

    # Compute determinism hash from canonical JSON
    determinism_hash = compute_determinism_hash(manifest_dict)

    # Build manifest with computed hash
    manifest = ExternalProofPackV1(
        schema_version=1,
        project="RenaceCHESS",
        phase="E",
        included_milestones=["M30", "M31", "M32"],
        artifacts=artifacts,
        hash_chain=hash_chain,
        limitations=limitations,
        determinism_hash=determinism_hash,
    )

    # Write manifest to proof pack
    manifest_path = output_dir / "proof_pack_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(
            manifest.model_dump(mode="json"),
            f,
            indent=2,
            ensure_ascii=False,
        )

    # Generate README
    _generate_readme(output_dir, manifest, move_vocab_size)

    # Copy required schemas
    _copy_schemas(output_dir)

    return manifest


def _generate_readme(output_dir: Path, manifest: ExternalProofPackV1, move_vocab_size: int) -> None:
    """Generate README.md for proof pack.

    Args:
        output_dir: Proof pack directory.
        manifest: Proof pack manifest.
        move_vocab_size: Training vocabulary size.
    """
    from datetime import datetime

    readme_template_path = Path(__file__).parent / "README_TEMPLATE.md"
    readme_template = readme_template_path.read_text(encoding="utf-8")

    # Replace placeholders (using string replacement to avoid brace escaping issues)
    readme_content = readme_template.replace("{generated_date}", datetime.now().strftime("%Y-%m-%d"))
    readme_content = readme_content.replace("{move_vocab_size}", str(move_vocab_size))

    readme_path = output_dir / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")


def _copy_schemas(output_dir: Path) -> None:
    """Copy required schemas to proof pack.

    Args:
        output_dir: Proof pack directory.
    """
    import shutil

    schemas_dir = output_dir / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    # List of schemas required to validate all artifacts
    required_schemas = [
        "external_proof_pack.v1.schema.json",
        "frozen_eval_manifest.v2.schema.json",
        "eval_set_provenance.v1.schema.json",
        "training_config_lock.v1.schema.json",
        "training_run_report.v1.schema.json",
        "post_train_eval_report.v1.schema.json",
        "policy_eval_metrics.v1.schema.json",
        "outcome_eval_metrics.v1.schema.json",
        "delta_metrics.v1.schema.json",
    ]

    schemas_source_dir = Path(__file__).parent.parent / "contracts" / "schemas" / "v1"

    for schema_name in required_schemas:
        source = schemas_source_dir / schema_name
        if source.exists():
            dest = schemas_dir / schema_name
            shutil.copy2(source, dest)
        else:
            raise FileNotFoundError(f"Required schema not found: {source}")

