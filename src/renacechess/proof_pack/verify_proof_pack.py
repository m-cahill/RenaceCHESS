"""Verifier for M33 external proof pack.

This module validates proof pack integrity by:
1. Validating manifest schema
2. Verifying all referenced files exist
3. Recomputing hashes and comparing against manifest
"""

import hashlib
import json
from pathlib import Path

from renacechess.contracts.models import ExternalProofPackV1
from renacechess.determinism import canonical_json_dump, compute_determinism_hash


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


class ProofPackVerificationError(Exception):
    """Raised when proof pack verification fails."""

    pass


def verify_proof_pack(proof_pack_dir: Path) -> tuple[bool, list[str]]:
    """Verify proof pack integrity.

    This function performs full verification:
    1. Validates manifest schema
    2. Verifies all referenced files exist
    3. Recomputes hashes for all included artifacts and compares

    Args:
        proof_pack_dir: Directory containing proof pack (must contain proof_pack_manifest.json).

    Returns:
        Tuple of (is_valid, list_of_errors). If valid, errors list is empty.

    Raises:
        FileNotFoundError: If manifest file is missing.
    """
    manifest_path = proof_pack_dir / "proof_pack_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    errors: list[str] = []

    # Load and validate manifest schema
    try:
        with manifest_path.open(encoding="utf-8") as f:
            manifest_dict = json.load(f)
        manifest = ExternalProofPackV1.model_validate(manifest_dict)
    except Exception as e:
        errors.append(f"Manifest schema validation failed: {e}")
        return False, errors

    # Verify determinism hash
    # Reconstruct the dict exactly as it was built (without determinismHash)
    manifest_dict_for_hash = {
        "schemaVersion": manifest.schema_version,
        "project": manifest.project,
        "phase": manifest.phase,
        "includedMilestones": manifest.included_milestones,
        "artifacts": manifest.artifacts.model_dump(mode="json"),
        "hashChain": manifest.hash_chain.model_dump(mode="json"),
        "limitations": manifest.limitations.model_dump(mode="json"),
    }
    expected_hash = compute_determinism_hash(manifest_dict_for_hash)
    if manifest.determinism_hash != expected_hash:
        errors.append(
            f"Manifest determinism hash mismatch: "
            f"expected {expected_hash}, got {manifest.determinism_hash}"
        )

    # Verify frozen eval artifacts
    frozen_eval_manifest_path = proof_pack_dir / manifest.artifacts.frozen_eval.manifest_path
    if not frozen_eval_manifest_path.exists():
        errors.append(f"Frozen eval manifest not found: {frozen_eval_manifest_path}")
    else:
        computed_hash = _compute_sha256_file(frozen_eval_manifest_path)
        if computed_hash != manifest.artifacts.frozen_eval.manifest_hash:
            errors.append(
                f"Frozen eval manifest hash mismatch: "
                f"expected {manifest.artifacts.frozen_eval.manifest_hash}, "
                f"computed {computed_hash}"
            )

    frozen_eval_provenance_path = proof_pack_dir / manifest.artifacts.frozen_eval.provenance_path
    if not frozen_eval_provenance_path.exists():
        errors.append(f"Frozen eval provenance not found: {frozen_eval_provenance_path}")
    else:
        computed_hash = _compute_sha256_file(frozen_eval_provenance_path)
        if computed_hash != manifest.artifacts.frozen_eval.provenance_hash:
            errors.append(
                f"Frozen eval provenance hash mismatch: "
                f"expected {manifest.artifacts.frozen_eval.provenance_hash}, "
                f"computed {computed_hash}"
            )

    # Verify training artifacts
    training_config_lock_path = proof_pack_dir / manifest.artifacts.training.config_lock_path
    if not training_config_lock_path.exists():
        errors.append(f"Training config lock not found: {training_config_lock_path}")
    else:
        computed_hash = _compute_sha256_file(training_config_lock_path)
        if computed_hash != manifest.artifacts.training.config_lock_hash:
            errors.append(
                f"Training config lock hash mismatch: "
                f"expected {manifest.artifacts.training.config_lock_hash}, "
                f"computed {computed_hash}"
            )

    training_run_report_path = proof_pack_dir / manifest.artifacts.training.run_report_path
    if not training_run_report_path.exists():
        errors.append(f"Training run report not found: {training_run_report_path}")
    else:
        computed_hash = _compute_sha256_file(training_run_report_path)
        if computed_hash != manifest.artifacts.training.run_report_hash:
            errors.append(
                f"Training run report hash mismatch: "
                f"expected {manifest.artifacts.training.run_report_hash}, "
                f"computed {computed_hash}"
            )

    # Verify evaluation artifacts
    post_train_eval_report_path = proof_pack_dir / manifest.artifacts.evaluation.report_path
    if not post_train_eval_report_path.exists():
        errors.append(f"Post-train eval report not found: {post_train_eval_report_path}")
    else:
        computed_hash = _compute_sha256_file(post_train_eval_report_path)
        if computed_hash != manifest.artifacts.evaluation.report_hash:
            errors.append(
                f"Post-train eval report hash mismatch: "
                f"expected {manifest.artifacts.evaluation.report_hash}, "
                f"computed {computed_hash}"
            )

    # Verify hash chain consistency
    if (
        manifest.hash_chain.frozen_eval_manifest_hash
        != manifest.artifacts.frozen_eval.manifest_hash
    ):
        errors.append("Hash chain frozen eval manifest hash mismatch")

    if (
        manifest.hash_chain.training_config_lock_hash
        != manifest.artifacts.training.config_lock_hash
    ):
        errors.append("Hash chain training config lock hash mismatch")

    if (
        manifest.hash_chain.training_run_report_hash
        != manifest.artifacts.training.run_report_hash
    ):
        errors.append("Hash chain training run report hash mismatch")

    if (
        manifest.hash_chain.post_train_eval_report_hash
        != manifest.artifacts.evaluation.report_hash
    ):
        errors.append("Hash chain post-train eval report hash mismatch")

    is_valid = len(errors) == 0
    return is_valid, errors

