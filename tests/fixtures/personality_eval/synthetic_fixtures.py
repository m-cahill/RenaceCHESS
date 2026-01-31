"""Synthetic fixtures for personality evaluation harness tests (M18).

This module provides synthetic policies and structural contexts for testing
the personality evaluation harness without using real Lichess data or
frozen eval positions.

Two classes of fixtures are provided:
1. Simple distributions: uniform, single-peak, two-peak
2. Entropy-matched distributions: synthetic but plausible entropy levels
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from renacechess.contracts.models import (
    PerPieceFeaturesV1,
    PieceFeatures,
    Policy,
    PolicyMove,
    SquareMapFeaturesV1,
)


@dataclass
class SyntheticStructuralContext:
    """Simple implementation of StructuralContext for testing."""

    _per_piece: PerPieceFeaturesV1 | None = None
    _square_map: SquareMapFeaturesV1 | None = None

    @property
    def per_piece(self) -> PerPieceFeaturesV1 | None:
        """Per-piece structural features."""
        return self._per_piece

    @property
    def square_map(self) -> SquareMapFeaturesV1 | None:
        """Square-level structural maps."""
        return self._square_map


def create_uniform_policy(moves: list[str]) -> Policy:
    """Create a uniform distribution over the given moves.

    Args:
        moves: List of UCI move strings.

    Returns:
        Policy with uniform probabilities.
    """
    if not moves:
        return Policy(top_moves=[], entropy=0.0, top_gap=0.0)

    prob = 1.0 / len(moves)
    top_moves = [PolicyMove(uci=move, p=prob) for move in moves]

    # Compute entropy: -sum(p * log2(p)) = log2(n) for uniform
    entropy = math.log2(len(moves)) if len(moves) > 1 else 0.0

    # Top gap is 0 for uniform distribution
    top_gap = 0.0

    return Policy(top_moves=top_moves, entropy=entropy, top_gap=top_gap)


def create_peaked_policy(
    moves: list[str],
    peak_move: str,
    peak_prob: float = 0.6,
) -> Policy:
    """Create a single-peaked distribution.

    Args:
        moves: List of UCI move strings (must include peak_move).
        peak_move: UCI move to have highest probability.
        peak_prob: Probability for the peak move (default: 0.6).

    Returns:
        Policy with peaked distribution.

    Raises:
        ValueError: If peak_move not in moves.
    """
    if peak_move not in moves:
        raise ValueError(f"peak_move {peak_move} not in moves")

    if len(moves) == 1:
        return Policy(
            top_moves=[PolicyMove(uci=peak_move, p=1.0)],
            entropy=0.0,
            top_gap=1.0,
        )

    # Distribute remaining probability uniformly
    remaining_prob = 1.0 - peak_prob
    other_prob = remaining_prob / (len(moves) - 1)

    top_moves = []
    for move in moves:
        p = peak_prob if move == peak_move else other_prob
        top_moves.append(PolicyMove(uci=move, p=p))

    # Sort by probability descending
    top_moves.sort(key=lambda m: m.p, reverse=True)

    # Compute entropy
    entropy = 0.0
    for policy_move in top_moves:
        if policy_move.p > 0:
            entropy -= policy_move.p * math.log2(policy_move.p)

    # Compute top gap
    top_gap = top_moves[0].p - top_moves[1].p if len(top_moves) > 1 else top_moves[0].p

    return Policy(top_moves=top_moves, entropy=entropy, top_gap=top_gap)


def create_two_peak_policy(
    moves: list[str],
    peak1_move: str,
    peak2_move: str,
    peak1_prob: float = 0.4,
    peak2_prob: float = 0.35,
) -> Policy:
    """Create a two-peaked distribution.

    Args:
        moves: List of UCI move strings.
        peak1_move: First peak move.
        peak2_move: Second peak move.
        peak1_prob: Probability for first peak (default: 0.4).
        peak2_prob: Probability for second peak (default: 0.35).

    Returns:
        Policy with two-peaked distribution.
    """
    if peak1_move not in moves or peak2_move not in moves:
        raise ValueError("peak moves must be in moves list")

    if len(moves) <= 2:
        # Special case: only two moves
        top_moves = [
            PolicyMove(uci=peak1_move, p=peak1_prob / (peak1_prob + peak2_prob)),
            PolicyMove(uci=peak2_move, p=peak2_prob / (peak1_prob + peak2_prob)),
        ]
        top_moves.sort(key=lambda m: m.p, reverse=True)
        entropy = sum(-m.p * math.log2(m.p) for m in top_moves if m.p > 0)
        top_gap = abs(top_moves[0].p - top_moves[1].p)
        return Policy(top_moves=top_moves, entropy=entropy, top_gap=top_gap)

    remaining_prob = 1.0 - peak1_prob - peak2_prob
    other_prob = remaining_prob / (len(moves) - 2)

    top_moves = []
    for move in moves:
        if move == peak1_move:
            p = peak1_prob
        elif move == peak2_move:
            p = peak2_prob
        else:
            p = other_prob
        top_moves.append(PolicyMove(uci=move, p=p))

    top_moves.sort(key=lambda m: m.p, reverse=True)

    entropy = sum(-m.p * math.log2(m.p) for m in top_moves if m.p > 0)
    top_gap = top_moves[0].p - top_moves[1].p if len(top_moves) > 1 else top_moves[0].p

    return Policy(top_moves=top_moves, entropy=entropy, top_gap=top_gap)


def create_entropy_matched_policy(
    moves: list[str],
    target_entropy: float,
) -> Policy:
    """Create a policy with approximately the target entropy.

    Uses exponential decay from first move to create realistic-looking
    distributions with controlled entropy.

    Args:
        moves: List of UCI move strings.
        target_entropy: Target entropy in bits.

    Returns:
        Policy with entropy close to target.
    """
    if not moves:
        return Policy(top_moves=[], entropy=0.0, top_gap=0.0)

    if len(moves) == 1:
        return Policy(
            top_moves=[PolicyMove(uci=moves[0], p=1.0)],
            entropy=0.0,
            top_gap=1.0,
        )

    # Max entropy is log2(n)
    max_entropy = math.log2(len(moves))

    # Clamp target to valid range
    target_entropy = max(0.1, min(target_entropy, max_entropy))

    # Use exponential decay with tuned temperature
    # entropy = -sum(p_i * log2(p_i))
    # For exponential: p_i = exp(-i/T) / Z
    # Higher T = more uniform = higher entropy

    # Binary search for temperature that gives target entropy
    t_low, t_high = 0.1, 100.0
    for _ in range(50):  # Converge in 50 iterations
        t_mid = (t_low + t_high) / 2.0

        # Compute distribution
        unnorm = [math.exp(-i / t_mid) for i in range(len(moves))]
        z = sum(unnorm)
        probs = [p / z for p in unnorm]

        # Compute entropy
        entropy = sum(-p * math.log2(p) for p in probs if p > 0)

        if entropy < target_entropy:
            t_low = t_mid
        else:
            t_high = t_mid

    # Create policy with final temperature
    unnorm = [math.exp(-i / t_mid) for i in range(len(moves))]
    z = sum(unnorm)
    probs = [p / z for p in unnorm]

    top_moves = [PolicyMove(uci=moves[i], p=probs[i]) for i in range(len(moves))]
    top_moves.sort(key=lambda m: m.p, reverse=True)

    final_entropy = sum(-m.p * math.log2(m.p) for m in top_moves if m.p > 0)
    top_gap = top_moves[0].p - top_moves[1].p if len(top_moves) > 1 else top_moves[0].p

    return Policy(top_moves=top_moves, entropy=final_entropy, top_gap=top_gap)


def create_empty_context() -> SyntheticStructuralContext:
    """Create an empty structural context (no features).

    Returns:
        StructuralContext with no features.
    """
    return SyntheticStructuralContext()


def create_minimal_per_piece() -> PerPieceFeaturesV1:
    """Create minimal per-piece features for testing.

    Creates a 32-slot piece array with plausible values for a
    starting-like position.

    Returns:
        PerPieceFeaturesV1 with synthetic values.
    """
    pieces: list[PieceFeatures] = []

    # White pieces (slots 0-15)
    white_pieces = [
        ("K", "e", True, "e1", 2, 2, 0, 2, 2),
        ("Q", "d", True, "d1", 5, 4, 0, 1, 1),
        ("R", "a", True, "a1", 2, 2, 0, 0, 0),
        ("R", "h", True, "h1", 2, 2, 0, 0, 0),
        ("B", "c", True, "c1", 2, 2, 0, 1, 1),
        ("B", "f", True, "f1", 2, 2, 0, 1, 1),
        ("N", "b", True, "b1", 2, 2, 0, 1, 1),
        ("N", "g", True, "g1", 2, 2, 0, 1, 1),
        ("P", "a", True, "a2", 1, 1, 0, 0, 0),
        ("P", "b", True, "b2", 1, 1, 0, 0, 0),
        ("P", "c", True, "c2", 1, 1, 0, 0, 0),
        ("P", "d", True, "d2", 2, 2, 0, 1, 1),
        ("P", "e", True, "e2", 2, 2, 0, 1, 1),
        ("P", "f", True, "f2", 1, 1, 0, 0, 0),
        ("P", "g", True, "g2", 1, 1, 0, 0, 0),
        ("P", "h", True, "h2", 1, 1, 0, 0, 0),
    ]

    for slot_id, (pt, sf, alive, sq, mob_legal, mob_safe, atk, dfd, net) in enumerate(white_pieces):
        pieces.append(
            PieceFeatures(
                slot_id=slot_id,
                color="white",
                piece_type=pt,
                starting_file=sf,
                alive=alive,
                square=sq,
                is_promoted=False,
                promoted_to=None,
                mobility_legal=mob_legal,
                mobility_safe=mob_safe,
                attacked_by=atk,
                defended_by=dfd,
                net_defense=net,
                is_hanging=atk > 0 and dfd == 0,
                is_pinned=False,
                is_restricted=mob_legal < 3,
                is_dominated=net < -1,
                is_attacker=False,
                is_defender_of_king=False,
            )
        )

    # Black pieces (slots 16-31)
    black_pieces = [
        ("K", "e", True, "e8", 2, 2, 0, 2, 2),
        ("Q", "d", True, "d8", 5, 4, 0, 1, 1),
        ("R", "a", True, "a8", 2, 2, 0, 0, 0),
        ("R", "h", True, "h8", 2, 2, 0, 0, 0),
        ("B", "c", True, "c8", 2, 2, 0, 1, 1),
        ("B", "f", True, "f8", 2, 2, 0, 1, 1),
        ("N", "b", True, "b8", 2, 2, 0, 1, 1),
        ("N", "g", True, "g8", 2, 2, 0, 1, 1),
        ("P", "a", True, "a7", 1, 1, 0, 0, 0),
        ("P", "b", True, "b7", 1, 1, 0, 0, 0),
        ("P", "c", True, "c7", 1, 1, 0, 0, 0),
        ("P", "d", True, "d7", 2, 2, 0, 1, 1),
        ("P", "e", True, "e7", 2, 2, 0, 1, 1),
        ("P", "f", True, "f7", 1, 1, 0, 0, 0),
        ("P", "g", True, "g7", 1, 1, 0, 0, 0),
        ("P", "h", True, "h7", 1, 1, 0, 0, 0),
    ]

    for i, (pt, sf, alive, sq, mob_legal, mob_safe, atk, dfd, net) in enumerate(black_pieces):
        slot_id = 16 + i
        pieces.append(
            PieceFeatures(
                slot_id=slot_id,
                color="black",
                piece_type=pt,
                starting_file=sf,
                alive=alive,
                square=sq,
                is_promoted=False,
                promoted_to=None,
                mobility_legal=mob_legal,
                mobility_safe=mob_safe,
                attacked_by=atk,
                defended_by=dfd,
                net_defense=net,
                is_hanging=atk > 0 and dfd == 0,
                is_pinned=False,
                is_restricted=mob_legal < 3,
                is_dominated=net < -1,
                is_attacker=False,
                is_defender_of_king=False,
            )
        )

    return PerPieceFeaturesV1(schema_version="per_piece.v1", pieces=pieces)


def create_minimal_square_map() -> SquareMapFeaturesV1:
    """Create minimal square map features for testing.

    Returns:
        SquareMapFeaturesV1 with synthetic values.
    """
    # All squares start as not weak/strong/hole
    empty_64 = [False] * 64

    # Add some weak squares for testing
    weak_white = empty_64.copy()
    weak_white[20] = True  # e3 is weak for white
    weak_white[21] = True  # f3 is weak for white

    weak_black = empty_64.copy()
    weak_black[44] = True  # e6 is weak for black
    weak_black[45] = True  # f6 is weak for black

    # Add some holes
    holes_white = empty_64.copy()
    holes_white[28] = True  # e4 is a hole for white

    holes_black = empty_64.copy()
    holes_black[36] = True  # e5 is a hole for black

    return SquareMapFeaturesV1(
        schema_version="square_map.v1",
        weak_for_white=weak_white,
        strong_for_white=empty_64.copy(),
        weak_for_black=weak_black,
        strong_for_black=empty_64.copy(),
        is_hole_for_white=holes_white,
        is_hole_for_black=holes_black,
    )


def create_rich_context() -> SyntheticStructuralContext:
    """Create a rich structural context with both per-piece and square-map features.

    Returns:
        StructuralContext with synthetic M11 features.
    """
    return SyntheticStructuralContext(
        _per_piece=create_minimal_per_piece(),
        _square_map=create_minimal_square_map(),
    )


# Standard test move sets
STANDARD_MOVES_5 = ["e2e4", "d2d4", "g1f3", "c2c4", "e2e3"]
STANDARD_MOVES_10 = STANDARD_MOVES_5 + ["b1c3", "f2f4", "g2g3", "d2d3", "c2c3"]
STANDARD_MOVES_20 = STANDARD_MOVES_10 + [
    "a2a3",
    "a2a4",
    "b2b3",
    "b2b4",
    "f2f3",
    "g2g4",
    "h2h3",
    "h2h4",
    "b1a3",
    "g1h3",
]


@dataclass
class PolicyFixture:
    """A test fixture containing a policy and its metadata."""

    fixture_id: str
    policy: Policy
    fixture_type: Literal["uniform", "peaked", "two_peak", "entropy_matched"]
    description: str


def get_simple_fixtures() -> list[PolicyFixture]:
    """Get simple test fixtures (uniform, peaked, two-peak).

    Returns:
        List of PolicyFixture objects.
    """
    return [
        PolicyFixture(
            fixture_id="uniform_5",
            policy=create_uniform_policy(STANDARD_MOVES_5),
            fixture_type="uniform",
            description="Uniform distribution over 5 moves",
        ),
        PolicyFixture(
            fixture_id="uniform_10",
            policy=create_uniform_policy(STANDARD_MOVES_10),
            fixture_type="uniform",
            description="Uniform distribution over 10 moves",
        ),
        PolicyFixture(
            fixture_id="peaked_60",
            policy=create_peaked_policy(STANDARD_MOVES_5, "e2e4", 0.6),
            fixture_type="peaked",
            description="Single peak at e2e4 with 60% probability",
        ),
        PolicyFixture(
            fixture_id="peaked_80",
            policy=create_peaked_policy(STANDARD_MOVES_5, "e2e4", 0.8),
            fixture_type="peaked",
            description="Single peak at e2e4 with 80% probability",
        ),
        PolicyFixture(
            fixture_id="two_peak_40_35",
            policy=create_two_peak_policy(STANDARD_MOVES_5, "e2e4", "d2d4", 0.4, 0.35),
            fixture_type="two_peak",
            description="Two peaks at e2e4 (40%) and d2d4 (35%)",
        ),
    ]


def get_entropy_matched_fixtures() -> list[PolicyFixture]:
    """Get entropy-matched test fixtures.

    Typical human policy entropy ranges from ~0.5 (very peaked) to ~2.5 (diffuse).

    Returns:
        List of PolicyFixture objects with controlled entropy.
    """
    return [
        PolicyFixture(
            fixture_id="entropy_0.5_10",
            policy=create_entropy_matched_policy(STANDARD_MOVES_10, 0.5),
            fixture_type="entropy_matched",
            description="Low entropy (~0.5 bits) over 10 moves",
        ),
        PolicyFixture(
            fixture_id="entropy_1.5_10",
            policy=create_entropy_matched_policy(STANDARD_MOVES_10, 1.5),
            fixture_type="entropy_matched",
            description="Medium entropy (~1.5 bits) over 10 moves",
        ),
        PolicyFixture(
            fixture_id="entropy_2.5_10",
            policy=create_entropy_matched_policy(STANDARD_MOVES_10, 2.5),
            fixture_type="entropy_matched",
            description="High entropy (~2.5 bits) over 10 moves",
        ),
        PolicyFixture(
            fixture_id="entropy_1.0_20",
            policy=create_entropy_matched_policy(STANDARD_MOVES_20, 1.0),
            fixture_type="entropy_matched",
            description="Low entropy (~1.0 bits) over 20 moves",
        ),
        PolicyFixture(
            fixture_id="entropy_2.0_20",
            policy=create_entropy_matched_policy(STANDARD_MOVES_20, 2.0),
            fixture_type="entropy_matched",
            description="Medium entropy (~2.0 bits) over 20 moves",
        ),
    ]


def get_all_fixtures() -> list[PolicyFixture]:
    """Get all test fixtures.

    Returns:
        Combined list of simple and entropy-matched fixtures.
    """
    return get_simple_fixtures() + get_entropy_matched_fixtures()
