"""Synthetic fixtures for personality evaluation harness tests (M18)."""

from fixtures.personality_eval.synthetic_fixtures import (
    STANDARD_MOVES_5,
    STANDARD_MOVES_10,
    STANDARD_MOVES_20,
    PolicyFixture,
    SyntheticStructuralContext,
    create_empty_context,
    create_entropy_matched_policy,
    create_minimal_per_piece,
    create_minimal_square_map,
    create_peaked_policy,
    create_rich_context,
    create_two_peak_policy,
    create_uniform_policy,
    get_all_fixtures,
    get_entropy_matched_fixtures,
    get_simple_fixtures,
)

__all__ = [
    "PolicyFixture",
    "STANDARD_MOVES_5",
    "STANDARD_MOVES_10",
    "STANDARD_MOVES_20",
    "SyntheticStructuralContext",
    "create_empty_context",
    "create_entropy_matched_policy",
    "create_minimal_per_piece",
    "create_minimal_square_map",
    "create_peaked_policy",
    "create_rich_context",
    "create_two_peak_policy",
    "create_uniform_policy",
    "get_all_fixtures",
    "get_entropy_matched_fixtures",
    "get_simple_fixtures",
]
