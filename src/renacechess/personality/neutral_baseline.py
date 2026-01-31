"""Neutral Baseline personality module (M17).

This personality implements an identity-preserving transformation that:
- Returns the base policy unchanged
- Validates all safety envelope constraints
- Provides a ground-truth control for personality comparisons

The Neutral Baseline exists for experimental control: it proves the personality
system can be "enabled" without changing behavior, ensuring observed divergence
from other personalities is real, not systemic.

See docs/contracts/PERSONALITY_SAFETY_CONTRACT_v1.md for the governing contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from renacechess.contracts.models import (
    Policy,
    SafetyEnvelopeV1,
)

if TYPE_CHECKING:
    from renacechess.personality.interfaces import StructuralContext


class NeutralBaselinePersonalityV1:
    """Neutral Baseline personality implementation.

    This personality performs an identity transformation: it returns the base
    policy unchanged while still running all safety envelope validations.

    Purpose:
        - Experimental control for personality comparisons
        - Proves personality system can be enabled without behavioral change
        - Validates safety envelope constraints work correctly
        - Provides baseline for divergence metrics

    All invariants from the Personality Safety Contract v1 are respected:
        1. Determinism: Same inputs → same outputs (trivially true for identity)
        2. Base policy reachability: This *is* the identity configuration
        3. Legality preservation: Only returns moves from base policy
        4. Probability conservation: Sum unchanged (returns base policy)
        5. Envelope compliance: No moves shift (delta = 0 for all moves)
    """

    def __init__(self) -> None:
        """Initialize Neutral Baseline personality.

        No parameters required - this is a pure identity transformation.
        """
        pass

    @property
    def personality_id(self) -> str:
        """Unique identifier for this personality."""
        return "control.neutral_baseline.v1"

    def validate_constraints(self, constraints: SafetyEnvelopeV1) -> None:
        """Validate that constraints are internally consistent.

        Args:
            constraints: Safety envelope to validate.

        Raises:
            ValueError: If constraints are invalid.
        """
        # SafetyEnvelopeV1 Pydantic model already validates:
        # - top_k >= 1 (via Field ge=1)
        # - delta_p_max in [0.0, 1.0] (via Field ge=0.0, le=1.0)
        # - entropy_min <= entropy_max (via model_validator)
        # This method exists for protocol compliance
        pass

    def is_identity(self, constraints: SafetyEnvelopeV1) -> bool:
        """Check if this configuration produces identity transformation.

        The Neutral Baseline is *always* an identity transformation,
        regardless of constraints.

        Args:
            constraints: Safety envelope to check (unused, always identity).

        Returns:
            True always - Neutral Baseline is definitionally identity.
        """
        return True

    def apply(
        self,
        base_policy: Policy,
        context: StructuralContext,
        constraints: SafetyEnvelopeV1,
    ) -> Policy:
        """Apply identity transformation to base policy.

        This method returns the base policy unchanged while validating
        that the constraints are internally consistent.

        Args:
            base_policy: Base policy distribution from learned human policy.
            context: Structural context (unused - identity doesn't need features).
            constraints: Safety envelope parameters (validated but not applied).

        Returns:
            The base_policy unchanged.
        """
        # Validate constraints for protocol compliance
        # (demonstrates constraint path is exercised even for identity)
        self.validate_constraints(constraints)

        # Return base policy unchanged
        # This is the core identity property
        return base_policy
