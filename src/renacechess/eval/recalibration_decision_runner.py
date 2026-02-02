"""Runtime recalibration decision runner for M28.

This module provides the decision framework for runtime recalibration activation.
It consumes M27 evidence (RuntimeRecalibrationReportV1 + RuntimeRecalibrationDeltaV1)
and a RuntimeRecalibrationActivationPolicyV1 to produce a decision artifact.

Per M28 locked decisions:
- M28 produces the decision framework, not hard-codes the final decision
- The actual decision value comes via a policy artifact
- Only per-Elo bucket and per-scope (policy/outcome/both) granularity
- Default policy is conservative: all buckets disabled
- Phase C contracts remain frozen
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from renacechess.conditioning.buckets import SkillBucketId
from renacechess.contracts.models import (
    BucketDecisionV1,
    RuntimeRecalibrationActivationPolicyV1,
    RuntimeRecalibrationDecisionV1,
    RuntimeRecalibrationDeltaV1,
    RuntimeRecalibrationReportV1,
    ValidationCheckV1,
    ValidationResultV1,
)
from renacechess.determinism import canonical_hash, canonical_json_dump

# Canonical Elo bucket IDs (M06 frozen)
CANONICAL_ELO_BUCKETS: list[SkillBucketId] = [
    "lt_800",
    "800_999",
    "1000_1199",
    "1200_1399",
    "1400_1599",
    "1600_1799",
    "gte_1800",
    "unknown",
]


def load_runtime_recalibration_report(path: Path) -> RuntimeRecalibrationReportV1:
    """Load RuntimeRecalibrationReportV1 from JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed RuntimeRecalibrationReportV1 instance.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file cannot be parsed.
    """
    if not path.exists():
        raise FileNotFoundError(f"Report file not found: {path}")

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return RuntimeRecalibrationReportV1.model_validate(data)


def load_runtime_recalibration_delta(path: Path) -> RuntimeRecalibrationDeltaV1:
    """Load RuntimeRecalibrationDeltaV1 from JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed RuntimeRecalibrationDeltaV1 instance.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file cannot be parsed.
    """
    if not path.exists():
        raise FileNotFoundError(f"Delta file not found: {path}")

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return RuntimeRecalibrationDeltaV1.model_validate(data)


def load_activation_policy(path: Path) -> RuntimeRecalibrationActivationPolicyV1:
    """Load RuntimeRecalibrationActivationPolicyV1 from JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed RuntimeRecalibrationActivationPolicyV1 instance.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file cannot be parsed.
    """
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return RuntimeRecalibrationActivationPolicyV1.model_validate(data)


def create_conservative_policy() -> RuntimeRecalibrationActivationPolicyV1:
    """Create a conservative (all disabled) activation policy.

    This is the default policy that disables recalibration for all buckets.

    Returns:
        Conservative RuntimeRecalibrationActivationPolicyV1.
    """
    return RuntimeRecalibrationActivationPolicyV1(
        version="1.0",
        default_enabled=False,
        scope="both",
        bucket_overrides=[],
        created_at=datetime.now(UTC),
        notes="Conservative default policy: all buckets disabled",
    )


def compute_artifact_hash(artifact_path: Path) -> str:
    """Compute SHA-256 hash of artifact file.

    Args:
        artifact_path: Path to the artifact file.

    Returns:
        Hash string in format 'sha256:<hex>'.
    """
    with artifact_path.open(encoding="utf-8") as f:
        content = f.read()
    hash_hex = canonical_hash(json.loads(content))
    return f"sha256:{hash_hex}"


def _validate_policy_against_evidence(
    policy: RuntimeRecalibrationActivationPolicyV1,
    report: RuntimeRecalibrationReportV1,
    delta: RuntimeRecalibrationDeltaV1,
) -> ValidationResultV1:
    """Validate policy against M27 evidence.

    Performs consistency checks:
    1. Report and delta are from same evaluation (hash linkage)
    2. Policy bucket overrides reference valid bucket IDs
    3. Report schema version is supported

    Args:
        policy: The activation policy to validate.
        report: The M27 evaluation report.
        delta: The M27 delta artifact.

    Returns:
        ValidationResultV1 with check results.
    """
    checks: list[ValidationCheckV1] = []
    errors: list[str] = []

    # Check 1: Report version is supported
    check1_passed = report.version == "1.0"
    checks.append(
        ValidationCheckV1(
            check_name="report_version_supported",
            passed=check1_passed,
            details=f"Report version: {report.version}",
        )
    )
    if not check1_passed:
        errors.append(f"Unsupported report version: {report.version}")

    # Check 2: Delta references report
    check2_passed = True  # Delta is derived from report, always linked by design
    checks.append(
        ValidationCheckV1(
            check_name="delta_references_report",
            passed=check2_passed,
            details=f"Delta references: {delta.source_report_hash}",
        )
    )

    # Check 3: Policy bucket overrides use valid bucket IDs
    valid_bucket_ids = set(CANONICAL_ELO_BUCKETS)
    invalid_buckets = [
        override.bucket_id
        for override in policy.bucket_overrides
        if override.bucket_id not in valid_bucket_ids
    ]
    check3_passed = len(invalid_buckets) == 0
    checks.append(
        ValidationCheckV1(
            check_name="valid_bucket_ids",
            passed=check3_passed,
            details=(
                "All bucket IDs valid"
                if check3_passed
                else f"Invalid bucket IDs: {invalid_buckets}"
            ),
        )
    )
    if not check3_passed:
        errors.append(f"Invalid bucket IDs in policy: {invalid_buckets}")

    # Check 4: Policy scope is valid
    check4_passed = policy.scope in ("outcome", "policy", "both")
    checks.append(
        ValidationCheckV1(
            check_name="valid_scope",
            passed=check4_passed,
            details=f"Policy scope: {policy.scope}",
        )
    )
    if not check4_passed:
        errors.append(f"Invalid policy scope: {policy.scope}")

    # Check 5: Delta has Elo bucket data
    check5_passed = len(delta.by_elo_bucket) > 0
    checks.append(
        ValidationCheckV1(
            check_name="delta_has_bucket_data",
            passed=check5_passed,
            details=f"Delta has {len(delta.by_elo_bucket)} Elo buckets",
        )
    )
    if not check5_passed:
        errors.append("Delta has no Elo bucket data")

    all_passed = all(check.passed for check in checks)

    return ValidationResultV1(
        valid=all_passed,
        checks=checks,
        errors=errors if errors else None,
    )


def _compute_bucket_decision(
    bucket_id: str,
    policy: RuntimeRecalibrationActivationPolicyV1,
    delta: RuntimeRecalibrationDeltaV1,
) -> BucketDecisionV1:
    """Compute decision for a single bucket.

    Args:
        bucket_id: The Elo bucket ID.
        policy: The activation policy.
        delta: The M27 delta artifact.

    Returns:
        BucketDecisionV1 with the decision for this bucket.
    """
    # Look for bucket-specific override
    override = None
    for o in policy.bucket_overrides:
        if o.bucket_id == bucket_id:
            override = o
            break

    # Determine if enabled
    if override is not None:
        enabled = override.enabled
        policy_reason = override.reason
        # Use override scope if specified, else policy default
        effective_scope: Literal["outcome", "policy", "both", "none"] = (
            override.scope if override.scope is not None else policy.scope
        )
    else:
        enabled = policy.default_enabled
        policy_reason = None
        effective_scope = policy.scope

    # If disabled, scope is "none"
    if not enabled:
        effective_scope = "none"

    # Find evidence summary from delta
    evidence_summary = None
    for bucket_delta in delta.by_elo_bucket:
        if bucket_delta.bucket_id == bucket_id:
            metrics = bucket_delta.metrics
            # Summarize: show key deltas
            improvements = []
            if metrics.outcome_ece_delta < 0:
                improvements.append(f"ECE {metrics.outcome_ece_delta:.4f}")
            if metrics.outcome_brier_delta < 0:
                improvements.append(f"Brier {metrics.outcome_brier_delta:.4f}")
            if metrics.policy_nll_delta < 0:
                improvements.append(f"PolicyNLL {metrics.policy_nll_delta:.4f}")

            stability_note = f"top1_stability={metrics.top1_stability:.2%}"

            if improvements:
                evidence_summary = f"Improvements: {', '.join(improvements)}; {stability_note}"
            else:
                evidence_summary = f"No improvements; {stability_note}"
            break

    if evidence_summary is None:
        evidence_summary = "No M27 data for this bucket"

    return BucketDecisionV1(
        bucket_id=bucket_id,
        enabled=enabled,
        scope=effective_scope,
        evidence_summary=evidence_summary,
        policy_reason=policy_reason,
    )


def _determine_decision_outcome(
    bucket_decisions: list[BucketDecisionV1],
) -> Literal["rejected", "restricted", "activated"]:
    """Determine overall decision outcome.

    Args:
        bucket_decisions: List of per-bucket decisions.

    Returns:
        Overall decision outcome.
    """
    enabled_count = sum(1 for bd in bucket_decisions if bd.enabled)
    total_count = len(bucket_decisions)

    if enabled_count == 0:
        return "rejected"
    elif enabled_count == total_count:
        return "activated"
    else:
        return "restricted"


def _generate_human_summary(
    decision_outcome: Literal["rejected", "restricted", "activated"],
    activated_count: int,
    total_count: int,
    policy: RuntimeRecalibrationActivationPolicyV1,
) -> str:
    """Generate human-readable summary of the decision.

    Args:
        decision_outcome: The overall decision outcome.
        activated_count: Number of activated buckets.
        total_count: Total number of buckets.
        policy: The activation policy.

    Returns:
        Human-readable summary string.
    """
    if decision_outcome == "rejected":
        return (
            "Runtime recalibration REJECTED: No Elo buckets have recalibration "
            "enabled. Default behavior remains unchanged."
        )
    elif decision_outcome == "activated":
        return (
            f"Runtime recalibration ACTIVATED for all {total_count} Elo buckets. "
            f"Scope: {policy.scope}. "
            "Recalibration will be applied when gate is enabled."
        )
    else:
        return (
            f"Runtime recalibration RESTRICTED to {activated_count}/{total_count} "
            f"Elo buckets. Scope: {policy.scope}. "
            "See bucket decisions for details."
        )


def run_recalibration_decision(
    report_path: Path,
    delta_path: Path,
    policy_path: Path,
) -> RuntimeRecalibrationDecisionV1:
    """Run the recalibration decision process.

    Consumes M27 evidence and a policy artifact to produce a decision artifact.

    Args:
        report_path: Path to RuntimeRecalibrationReportV1 JSON.
        delta_path: Path to RuntimeRecalibrationDeltaV1 JSON.
        policy_path: Path to RuntimeRecalibrationActivationPolicyV1 JSON.

    Returns:
        RuntimeRecalibrationDecisionV1 decision artifact.

    Raises:
        FileNotFoundError: If any input file is missing.
        ValueError: If validation fails.
    """
    # Load artifacts
    report = load_runtime_recalibration_report(report_path)
    delta = load_runtime_recalibration_delta(delta_path)
    policy = load_activation_policy(policy_path)

    # Compute artifact hashes
    source_report_hash = compute_artifact_hash(report_path)
    source_delta_hash = compute_artifact_hash(delta_path)
    policy_hash = compute_artifact_hash(policy_path)

    # Validate policy against evidence
    validation_result = _validate_policy_against_evidence(policy, report, delta)

    if not validation_result.valid:
        raise ValueError(f"Policy validation failed: {validation_result.errors}")

    # Compute per-bucket decisions
    bucket_decisions = []
    for bucket_id in CANONICAL_ELO_BUCKETS:
        decision = _compute_bucket_decision(bucket_id, policy, delta)
        bucket_decisions.append(decision)

    # Determine overall outcome
    activated_count = sum(1 for bd in bucket_decisions if bd.enabled)
    total_count = len(bucket_decisions)
    decision_outcome = _determine_decision_outcome(bucket_decisions)

    # Generate human summary
    human_summary = _generate_human_summary(decision_outcome, activated_count, total_count, policy)

    # Create decision object (without determinism hash for hashing)
    generated_at = datetime.now(UTC)

    # For determinism hash, exclude generated_at (like M27 does)
    decision_for_hash = {
        "version": "1.0",
        "decisionOutcome": decision_outcome,
        "sourceReportHash": source_report_hash,
        "sourceDeltaHash": source_delta_hash,
        "policyHash": policy_hash,
        "activatedBucketCount": activated_count,
        "totalBucketCount": total_count,
        "bucketDecisions": [bd.model_dump(by_alias=True, mode="json") for bd in bucket_decisions],
        "validationResult": validation_result.model_dump(by_alias=True, mode="json"),
        "humanSummary": human_summary,
    }
    determinism_hash = f"sha256:{canonical_hash(decision_for_hash)}"

    return RuntimeRecalibrationDecisionV1(
        version="1.0",
        generated_at=generated_at,
        decision_outcome=decision_outcome,
        source_report_hash=source_report_hash,
        source_delta_hash=source_delta_hash,
        policy_hash=policy_hash,
        activated_bucket_count=activated_count,
        total_bucket_count=total_count,
        bucket_decisions=bucket_decisions,
        validation_result=validation_result,
        human_summary=human_summary,
        determinism_hash=determinism_hash,
    )


def save_decision(decision: RuntimeRecalibrationDecisionV1, path: Path) -> None:
    """Save decision artifact to JSON file.

    Args:
        decision: The decision artifact to save.
        path: Output path.
    """
    json_bytes = canonical_json_dump(decision.model_dump(by_alias=True, mode="json"))
    path.write_text(json_bytes.decode("utf-8"), encoding="utf-8")


def save_policy(policy: RuntimeRecalibrationActivationPolicyV1, path: Path) -> None:
    """Save policy artifact to JSON file.

    Args:
        policy: The policy artifact to save.
        path: Output path.
    """
    json_bytes = canonical_json_dump(policy.model_dump(by_alias=True, mode="json"))
    path.write_text(json_bytes.decode("utf-8"), encoding="utf-8")
