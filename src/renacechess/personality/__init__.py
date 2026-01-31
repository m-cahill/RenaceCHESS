"""Personality module for RenaceCHESS style modulation.

This module provides bounded behavioral variation through style transformations
that modify probability mass within safe envelopes, without corrupting base
policy correctness or legality.

See docs/contracts/PERSONALITY_SAFETY_CONTRACT_v1.md for the governing contract.
"""

from renacechess.personality.neutral_baseline import NeutralBaselinePersonalityV1
from renacechess.personality.pawn_clamp import PawnClampPersonalityV1

__all__ = ["NeutralBaselinePersonalityV1", "PawnClampPersonalityV1"]
