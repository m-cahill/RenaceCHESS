"""Runtime recalibration gating for M26.

This module provides the runtime wrapper for applying recalibration parameters
conditionally based on an explicit RecalibrationGateV1 artifact.

Per M26 locked decisions:
- Gate must be loaded from explicit file path (no env vars, no defaults)
- Provenance metadata lives outside Phase C contracts
- Default path (gate disabled) must be byte-identical to M25 baseline
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from renacechess.contracts.models import (
    RecalibrationGateV1,
    RecalibrationParametersV1,
)
from renacechess.determinism import canonical_hash
from renacechess.eval.recalibration_runner import (
    apply_temperature_scaling_to_probs,
)


class RuntimeRecalibrationMetadata:
    """Provenance metadata for runtime recalibration application.

    Lives outside Phase C contracts. Available for logs, debugging, or audits.
    Invisible to LLMs and coaching surfaces.
    """

    def __init__(
        self,
        applied: bool,
        gate_hash: str | None = None,
        parameters_hash: str | None = None,
        scope: Literal["outcome", "policy", "both"] | None = None,
    ):
        """Initialize metadata.

        Args:
            applied: Whether recalibration was applied
            gate_hash: SHA-256 hash of the gate artifact (if provided)
            parameters_hash: SHA-256 hash of the parameters artifact (if applied)
            scope: Which heads were recalibrated (if applied)
        """
        self.applied = applied
        self.gate_hash = gate_hash
        self.parameters_hash = parameters_hash
        self.scope = scope

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/debugging."""
        return {
            "applied": self.applied,
            "gateHash": self.gate_hash,
            "parametersHash": self.parameters_hash,
            "scope": self.scope,
        }


def load_recalibration_gate(gate_path: Path) -> RecalibrationGateV1:
    """Load RecalibrationGateV1 from file.

    Args:
        gate_path: Path to gate JSON file

    Returns:
        RecalibrationGateV1 instance

    Raises:
        FileNotFoundError: If gate file doesn't exist
        ValueError: If gate is invalid or enabled but parameters_ref is missing
    """
    if not gate_path.exists():
        raise FileNotFoundError(f"Recalibration gate not found: {gate_path}")

    gate_dict = gate_path.read_text(encoding="utf-8")
    gate = RecalibrationGateV1.model_validate_json(gate_dict)

    # Validate that if enabled, parameters_ref is provided
    if gate.enabled and not gate.parameters_ref:
        raise ValueError("RecalibrationGateV1.enabled=True requires parametersRef to be set")

    return gate


def apply_recalibration_if_enabled(
    probs: list[float],
    skill_bucket: str,
    gate: RecalibrationGateV1,
    params: RecalibrationParametersV1 | None = None,
) -> tuple[list[float], RuntimeRecalibrationMetadata]:
    """Apply recalibration to probabilities if gate is enabled.

    Args:
        probs: List of probabilities (should sum to ~1.0)
        skill_bucket: Canonical skill bucket ID
        gate: RecalibrationGateV1 artifact
        params: RecalibrationParametersV1 artifact (required if gate.enabled=True)

    Returns:
        Tuple of (scaled_probs, metadata)
        - If gate.enabled=False: returns input probs unchanged
        - If gate.enabled=True: returns temperature-scaled probs

    Raises:
        ValueError: If gate is enabled but params is None or bucket not found
    """
    # Compute gate hash for provenance
    # Use mode="json" to serialize datetime objects to strings for JSON serialization
    gate_dict = gate.model_dump(by_alias=True, mode="json")
    gate_hash = f"sha256:{canonical_hash(gate_dict)}"

    # If disabled, return unchanged with metadata
    if not gate.enabled:
        return (
            probs,
            RuntimeRecalibrationMetadata(
                applied=False,
                gate_hash=gate_hash,
                scope=None,
            ),
        )

    # Gate is enabled - validate params
    if params is None:
        raise ValueError(
            "RecalibrationGateV1.enabled=True requires RecalibrationParametersV1 to be provided"
        )

    # Find bucket parameters
    bucket_params = None
    for bp in params.by_elo_bucket:
        if bp.elo_bucket == skill_bucket:
            bucket_params = bp
            break

    if bucket_params is None:
        raise ValueError(
            f"RecalibrationParametersV1 does not contain parameters for bucket: {skill_bucket}"
        )

    # Compute parameters hash for provenance
    # Use mode="json" to serialize datetime objects to strings for JSON serialization
    params_dict = params.model_dump(by_alias=True, mode="json")
    params_hash = f"sha256:{canonical_hash(params_dict)}"

    # Apply temperature scaling based on scope
    # For now, we only handle policy probabilities here
    # Outcome recalibration is handled separately in outcome head path
    if gate.scope in ("policy", "both"):
        scaled_probs = apply_temperature_scaling_to_probs(probs, bucket_params.policy_temperature)
    else:
        scaled_probs = probs

    # Update gate with applied_at timestamp (for audit trail)
    gate.applied_at = datetime.now(UTC)

    return (
        scaled_probs,
        RuntimeRecalibrationMetadata(
            applied=True,
            gate_hash=gate_hash,
            parameters_hash=params_hash,
            scope=gate.scope,
        ),
    )


def apply_recalibration_to_outcome_if_enabled(
    p_win: float,
    p_draw: float,
    p_loss: float,
    skill_bucket: str,
    gate: RecalibrationGateV1,
    params: RecalibrationParametersV1 | None = None,
) -> tuple[tuple[float, float, float], RuntimeRecalibrationMetadata]:
    """Apply recalibration to outcome probabilities (W/D/L) if gate is enabled.

    Args:
        p_win: Win probability
        p_draw: Draw probability
        p_loss: Loss probability
        skill_bucket: Canonical skill bucket ID
        gate: RecalibrationGateV1 artifact
        params: RecalibrationParametersV1 artifact (required if gate.enabled=True)

    Returns:
        Tuple of ((scaled_p_win, scaled_p_draw, scaled_p_loss), metadata)
        - If gate.enabled=False: returns input probs unchanged
        - If gate.enabled=True: returns temperature-scaled probs

    Raises:
        ValueError: If gate is enabled but params is None or bucket not found
    """
    # Compute gate hash for provenance
    # Use mode="json" to serialize datetime objects to strings for JSON serialization
    gate_dict = gate.model_dump(by_alias=True, mode="json")
    gate_hash = f"sha256:{canonical_hash(gate_dict)}"

    # If disabled, return unchanged with metadata
    if not gate.enabled:
        return (
            (p_win, p_draw, p_loss),
            RuntimeRecalibrationMetadata(
                applied=False,
                gate_hash=gate_hash,
                scope=None,
            ),
        )

    # Gate is enabled - validate params
    if params is None:
        raise ValueError(
            "RecalibrationGateV1.enabled=True requires RecalibrationParametersV1 to be provided"
        )

    # Find bucket parameters
    bucket_params = None
    for bp in params.by_elo_bucket:
        if bp.elo_bucket == skill_bucket:
            bucket_params = bp
            break

    if bucket_params is None:
        raise ValueError(
            f"RecalibrationParametersV1 does not contain parameters for bucket: {skill_bucket}"
        )

    # Compute parameters hash for provenance
    # Use mode="json" to serialize datetime objects to strings for JSON serialization
    params_dict = params.model_dump(by_alias=True, mode="json")
    params_hash = f"sha256:{canonical_hash(params_dict)}"

    # Apply temperature scaling based on scope
    if gate.scope in ("outcome", "both"):
        probs = [p_win, p_draw, p_loss]
        scaled_probs = apply_temperature_scaling_to_probs(probs, bucket_params.outcome_temperature)
        scaled_p_win, scaled_p_draw, scaled_p_loss = (
            scaled_probs[0],
            scaled_probs[1],
            scaled_probs[2],
        )
    else:
        scaled_p_win, scaled_p_draw, scaled_p_loss = p_win, p_draw, p_loss

    # Update gate with applied_at timestamp (for audit trail)
    gate.applied_at = datetime.now(UTC)

    return (
        (scaled_p_win, scaled_p_draw, scaled_p_loss),
        RuntimeRecalibrationMetadata(
            applied=True,
            gate_hash=gate_hash,
            parameters_hash=params_hash,
            scope=gate.scope,
        ),
    )
