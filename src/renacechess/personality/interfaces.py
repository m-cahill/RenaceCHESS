"""Interfaces for personality modules.

This module defines the protocol that all personality implementations must follow.
See docs/contracts/PERSONALITY_SAFETY_CONTRACT_v1.md for the governing contract.

Note: This is an interface-only module (M15). Implementations are deferred to M16+.
"""

from typing import Protocol

from renacechess.contracts.models import (
    PerPieceFeaturesV1,
    Policy,
    SafetyEnvelopeV1,
    SquareMapFeaturesV1,
)


class StructuralContext(Protocol):
    """Structural context for personality transformations.

    Provides read-only access to M11 structural cognition features.
    Personalities may use this context to inform style transformations
    but must never modify it.
    """

    @property
    def per_piece(self) -> PerPieceFeaturesV1 | None:
        """Per-piece structural features (32-slot tensor)."""
        ...

    @property
    def square_map(self) -> SquareMapFeaturesV1 | None:
        """Square-level structural maps (weak/strong/hole)."""
        ...


class PersonalityModuleV1(Protocol):
    """Protocol for personality modules that transform policy distributions.

    A personality module takes a base policy distribution, structural context,
    and safety constraints, and produces a modified policy distribution within
    the allowed envelope.

    Invariants (from Personality Safety Contract v1):
        1. Determinism: Same inputs → same outputs
        2. Base policy reachability: Identity configuration must exist
        3. Legality preservation: Cannot introduce illegal moves
        4. Probability conservation: Output sums to 1.0
        5. Envelope compliance: No move shifts beyond delta_p_max

    Note: This is an interface-only protocol (M15). Implementations deferred to M16+.
    """

    @property
    def personality_id(self) -> str:
        """Unique identifier for this personality.

        Format: '<category>.<name>.<version>'
        Example: 'style.pawn_clamp.v1'
        """
        ...

    def apply(
        self,
        base_policy: Policy,
        context: StructuralContext,
        constraints: SafetyEnvelopeV1,
    ) -> Policy:
        """Apply personality transformation to base policy.

        Args:
            base_policy: Base policy distribution from learned human policy.
            context: Structural context (M11 per-piece and square-map features).
            constraints: Safety envelope parameters (top_k, delta_p_max, etc.).

        Returns:
            Modified policy distribution within the allowed envelope.

        Raises:
            ValueError: If constraints are invalid or contradictory.
            RuntimeError: If transformation would violate safety invariants.
        """
        ...

    def validate_constraints(self, constraints: SafetyEnvelopeV1) -> None:
        """Validate that constraints are internally consistent.

        Args:
            constraints: Safety envelope to validate.

        Raises:
            ValueError: If constraints are invalid (e.g., entropy_min > entropy_max).
        """
        ...

    def is_identity(self, constraints: SafetyEnvelopeV1) -> bool:
        """Check if this configuration produces identity transformation.

        Per Personality Safety Contract v1, every personality must have at least
        one configuration where apply() returns the unmodified base policy.

        Args:
            constraints: Safety envelope to check.

        Returns:
            True if this configuration produces identity (no-op) transformation.
        """
        ...
