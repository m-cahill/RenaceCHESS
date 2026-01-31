"""Tests for Neutral Baseline personality module (M17).

This test suite proves that NeutralBaselinePersonalityV1 is a true identity
transformation, providing experimental control for personality comparisons.

Key property being tested: The personality system can be enabled without
changing behavior, ensuring all observed divergence from other personalities
is real, not systemic.
"""

import math

import pytest

from renacechess.contracts.models import (
    PerPieceFeaturesV1,
    PieceFeatures,
    Policy,
    PolicyMove,
    SafetyEnvelopeV1,
    SquareMapFeaturesV1,
)
from renacechess.personality.neutral_baseline import NeutralBaselinePersonalityV1
from renacechess.personality.pawn_clamp import PawnClampPersonalityV1


class MockStructuralContext:
    """Mock structural context for testing."""

    def __init__(
        self,
        per_piece: PerPieceFeaturesV1 | None = None,
        square_map: SquareMapFeaturesV1 | None = None,
    ) -> None:
        """Initialize mock context.

        Args:
            per_piece: Per-piece features (optional).
            square_map: Square map features (optional).
        """
        self._per_piece = per_piece
        self._square_map = square_map

    @property
    def per_piece(self) -> PerPieceFeaturesV1 | None:
        """Get per-piece features."""
        return self._per_piece

    @property
    def square_map(self) -> SquareMapFeaturesV1 | None:
        """Get square map features."""
        return self._square_map


def create_test_per_piece_features() -> PerPieceFeaturesV1:
    """Create test per-piece features."""
    pieces: list[PieceFeatures] = []
    for slot_id in range(32):
        color = "white" if slot_id < 16 else "black"
        piece_type = "P" if slot_id >= 8 and slot_id < 16 else "K"
        starting_file = "e" if slot_id == 0 else "a"

        pieces.append(
            PieceFeatures(
                slot_id=slot_id,
                color=color,
                piece_type=piece_type,
                starting_file=starting_file,
                alive=slot_id < 4,
                square="e4" if slot_id == 0 else None,
                is_promoted=False,
                promoted_to=None,
                mobility_legal=5 if slot_id == 0 else 0,
                mobility_safe=3 if slot_id == 0 else 0,
                attacked_by=0,
                defended_by=1 if slot_id == 0 else 0,
                net_defense=1 if slot_id == 0 else 0,
                is_hanging=False,
                is_pinned=False,
                is_restricted=False,
                is_dominated=False,
                is_attacker=False,
                is_defender_of_king=False,
            )
        )

    return PerPieceFeaturesV1(schema_version="per_piece.v1", pieces=pieces)


def create_test_square_map_features() -> SquareMapFeaturesV1:
    """Create test square map features."""
    weak_white = [False] * 64
    weak_black = [False] * 64
    strong_white = [False] * 64
    strong_black = [False] * 64
    holes_white = [False] * 64
    holes_black = [False] * 64
    weak_white[28] = True  # e4 is weak

    return SquareMapFeaturesV1(
        schema_version="square_map.v1",
        weak_for_white=weak_white,
        strong_for_white=strong_white,
        weak_for_black=weak_black,
        strong_for_black=strong_black,
        is_hole_for_white=holes_white,
        is_hole_for_black=holes_black,
        control_diff_white=None,
        control_diff_black=None,
        pawn_contestable_white=None,
        pawn_contestable_black=None,
    )


def create_synthetic_policy() -> Policy:
    """Create a synthetic test policy with known properties.

    This policy is designed for mathematical clarity in divergence tests:
    - 4 moves with distinct probabilities
    - Total sums to 1.0
    - Entropy is calculable
    """
    moves = [
        PolicyMove(uci="e2e4", san="e4", p=0.4),
        PolicyMove(uci="d2d4", san="d4", p=0.3),
        PolicyMove(uci="e2e3", san="e3", p=0.2),
        PolicyMove(uci="g1f3", san="Nf3", p=0.1),
    ]
    # Entropy: -sum(p * log2(p)) ≈ 1.85
    entropy = -sum(m.p * math.log2(m.p) for m in moves if m.p > 0)
    return Policy(
        top_moves=moves,
        entropy=entropy,
        top_gap=0.1,
    )


class TestNeutralBaselinePersonalityV1:
    """Test suite for NeutralBaselinePersonalityV1."""

    # ==========================================================================
    # Test 1: Personality Identity
    # ==========================================================================

    def test_personality_id(self) -> None:
        """Test personality ID follows naming convention."""
        personality = NeutralBaselinePersonalityV1()
        assert personality.personality_id == "control.neutral_baseline.v1"
        # Format: <category>.<name>.<version>
        parts = personality.personality_id.split(".")
        assert len(parts) == 3
        assert parts[0] == "control"  # Category is 'control', not 'style'
        assert parts[2] == "v1"

    # ==========================================================================
    # Test 2: Identity Configuration
    # ==========================================================================

    def test_is_identity_always_true(self) -> None:
        """Test that is_identity() always returns True regardless of constraints."""
        personality = NeutralBaselinePersonalityV1()

        # With default constraints
        assert personality.is_identity(SafetyEnvelopeV1())

        # With tight constraints
        tight = SafetyEnvelopeV1(top_k=1, delta_p_max=0.01, entropy_min=0.0, entropy_max=5.0)
        assert personality.is_identity(tight)

        # With loose constraints
        loose = SafetyEnvelopeV1(top_k=20, delta_p_max=0.5, entropy_min=0.0, entropy_max=10.0)
        assert personality.is_identity(loose)

    # ==========================================================================
    # Test 3: Exact Identity Transformation
    # ==========================================================================

    def test_exact_identity_transformation(self) -> None:
        """Test that output policy equals input policy exactly (within FP tolerance)."""
        personality = NeutralBaselinePersonalityV1()
        base_policy = create_synthetic_policy()
        context = MockStructuralContext()
        constraints = SafetyEnvelopeV1()

        result = personality.apply(base_policy, context, constraints)

        # Policy object should be the same (returned unchanged)
        assert result is base_policy

        # Verify move-by-move equality (for documentation)
        assert len(result.top_moves) == len(base_policy.top_moves)
        for result_move, base_move in zip(result.top_moves, base_policy.top_moves):
            assert result_move.uci == base_move.uci
            assert result_move.san == base_move.san
            assert result_move.p == base_move.p  # Exact equality, not tolerance

        # Verify entropy and top_gap unchanged
        assert result.entropy == base_policy.entropy
        assert result.top_gap == base_policy.top_gap

    # ==========================================================================
    # Test 4: Determinism
    # ==========================================================================

    def test_determinism(self) -> None:
        """Test that personality produces identical results on repeated calls."""
        personality = NeutralBaselinePersonalityV1()
        base_policy = create_synthetic_policy()
        per_piece = create_test_per_piece_features()
        square_map = create_test_square_map_features()
        context = MockStructuralContext(per_piece=per_piece, square_map=square_map)
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.1)

        # Apply 3 times with identical inputs
        result1 = personality.apply(base_policy, context, constraints)
        result2 = personality.apply(base_policy, context, constraints)
        result3 = personality.apply(base_policy, context, constraints)

        # All results should be identical (and same object as base)
        assert result1 is base_policy
        assert result2 is base_policy
        assert result3 is base_policy

    # ==========================================================================
    # Test 5: Probability Conservation
    # ==========================================================================

    def test_probability_conservation(self) -> None:
        """Test that output probabilities sum to exactly the same as input."""
        personality = NeutralBaselinePersonalityV1()
        base_policy = create_synthetic_policy()
        context = MockStructuralContext()
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.1)

        result = personality.apply(base_policy, context, constraints)

        base_total = sum(move.p for move in base_policy.top_moves)
        result_total = sum(move.p for move in result.top_moves)

        assert result_total == base_total  # Exact equality for identity

    # ==========================================================================
    # Test 6: Envelope Compliance (trivial for identity)
    # ==========================================================================

    def test_envelope_compliance(self) -> None:
        """Test that no move shifts beyond delta_p_max (delta = 0 for identity)."""
        personality = NeutralBaselinePersonalityV1()
        base_policy = create_synthetic_policy()
        context = MockStructuralContext()
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.1)

        result = personality.apply(base_policy, context, constraints)

        # Delta should be exactly 0 for all moves
        for base_move, result_move in zip(base_policy.top_moves, result.top_moves):
            delta = abs(result_move.p - base_move.p)
            assert delta == 0.0  # Exact zero for identity

    # ==========================================================================
    # Test 7: Constraint Validation
    # ==========================================================================

    def test_validate_constraints(self) -> None:
        """Test that constraints are validated (via Pydantic)."""
        personality = NeutralBaselinePersonalityV1()

        # Valid constraints should pass
        valid = SafetyEnvelopeV1(top_k=5, delta_p_max=0.15, entropy_min=0.5, entropy_max=3.0)
        personality.validate_constraints(valid)  # Should not raise

        # Invalid constraints are caught by Pydantic validation
        with pytest.raises(Exception):  # Pydantic ValidationError
            SafetyEnvelopeV1(top_k=0)

        with pytest.raises(Exception):  # Pydantic ValidationError
            SafetyEnvelopeV1(delta_p_max=1.5)

    # ==========================================================================
    # Test 8: Comparative Baseline - Neutral vs Raw
    # ==========================================================================

    def test_neutral_vs_raw_divergence_zero(self) -> None:
        """Test that Neutral Baseline produces zero divergence from raw policy.

        This is the core experimental control property: applying the Neutral
        Baseline personality should produce output identical to input.
        """
        personality = NeutralBaselinePersonalityV1()
        base_policy = create_synthetic_policy()
        context = MockStructuralContext()
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.15)

        result = personality.apply(base_policy, context, constraints)

        # Compute divergence metrics
        base_probs = {m.uci: m.p for m in base_policy.top_moves}
        result_probs = {m.uci: m.p for m in result.top_moves}

        # KL divergence should be exactly 0
        kl_div = 0.0
        for uci, base_p in base_probs.items():
            result_p = result_probs.get(uci, 0.0)
            if base_p > 0 and result_p > 0:
                kl_div += base_p * math.log2(base_p / result_p)

        assert kl_div == 0.0  # Exact zero for identity

        # Total Variation distance should be exactly 0
        all_moves = set(base_probs.keys()) | set(result_probs.keys())
        tv_distance = 0.5 * sum(
            abs(result_probs.get(uci, 0.0) - base_probs.get(uci, 0.0)) for uci in all_moves
        )

        assert tv_distance == 0.0  # Exact zero for identity

    # ==========================================================================
    # Test 9: Comparative Baseline - Pawn Clamp vs Neutral
    # ==========================================================================

    def test_pawn_clamp_vs_neutral_divergence_positive(self) -> None:
        """Test that Pawn Clamp produces positive divergence from Neutral.

        This proves that the Neutral Baseline can detect real style effects:
        - Neutral produces zero divergence
        - Pawn Clamp produces positive (but bounded) divergence
        - The difference is attributable to style, not system noise
        """
        neutral = NeutralBaselinePersonalityV1()
        pawn_clamp = PawnClampPersonalityV1(mobility_weight=0.6, weak_square_weight=0.4)

        base_policy = create_synthetic_policy()
        per_piece = create_test_per_piece_features()
        square_map = create_test_square_map_features()
        context = MockStructuralContext(per_piece=per_piece, square_map=square_map)
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.15)

        # Apply both personalities
        neutral_result = neutral.apply(base_policy, context, constraints)
        pawn_clamp_result = pawn_clamp.apply(base_policy, context, constraints)

        # Neutral result is identical to base
        neutral_probs = {m.uci: m.p for m in neutral_result.top_moves}
        base_probs = {m.uci: m.p for m in base_policy.top_moves}

        for uci in base_probs:
            assert neutral_probs[uci] == base_probs[uci]

        # Pawn Clamp result should differ from Neutral/base
        pawn_clamp_probs = {m.uci: m.p for m in pawn_clamp_result.top_moves}

        # Compute Total Variation distance between Pawn Clamp and Neutral
        all_moves = set(neutral_probs.keys()) | set(pawn_clamp_probs.keys())
        tv_distance = 0.5 * sum(
            abs(pawn_clamp_probs.get(uci, 0.0) - neutral_probs.get(uci, 0.0)) for uci in all_moves
        )

        # Divergence should be > 0 (style has effect)
        assert tv_distance > 0.0, "Pawn Clamp should produce divergence from Neutral"

        # Divergence should be bounded by envelope
        max_tv = constraints.delta_p_max * constraints.top_k
        assert tv_distance <= max_tv + 1e-6, "Divergence should respect safety envelope"

    # ==========================================================================
    # Test 10: Context Independence
    # ==========================================================================

    def test_context_independence(self) -> None:
        """Test that Neutral Baseline ignores context (doesn't use features)."""
        personality = NeutralBaselinePersonalityV1()
        base_policy = create_synthetic_policy()
        constraints = SafetyEnvelopeV1()

        # Apply with no context
        empty_context = MockStructuralContext(per_piece=None, square_map=None)
        result_empty = personality.apply(base_policy, empty_context, constraints)

        # Apply with full context
        per_piece = create_test_per_piece_features()
        square_map = create_test_square_map_features()
        full_context = MockStructuralContext(per_piece=per_piece, square_map=square_map)
        result_full = personality.apply(base_policy, full_context, constraints)

        # Results should be identical (both are base policy)
        assert result_empty is base_policy
        assert result_full is base_policy

    # ==========================================================================
    # Test 11: Single Move Policy
    # ==========================================================================

    def test_single_move_policy(self) -> None:
        """Test identity behavior with single-move policy edge case."""
        personality = NeutralBaselinePersonalityV1()
        base_policy = Policy(
            top_moves=[PolicyMove(uci="e2e4", san="e4", p=1.0)],
            entropy=0.0,
            top_gap=1.0,
        )
        context = MockStructuralContext()
        constraints = SafetyEnvelopeV1(top_k=1, delta_p_max=0.1, entropy_min=0.0, entropy_max=3.0)

        result = personality.apply(base_policy, context, constraints)

        # Should return unchanged
        assert result is base_policy
        assert len(result.top_moves) == 1
        assert result.top_moves[0].uci == "e2e4"
        assert result.top_moves[0].p == 1.0

    # ==========================================================================
    # Test 12: Empty Policy Edge Case
    # ==========================================================================

    def test_empty_policy(self) -> None:
        """Test identity behavior with empty policy edge case."""
        personality = NeutralBaselinePersonalityV1()
        base_policy = Policy(
            top_moves=[],
            entropy=0.0,
            top_gap=0.0,
        )
        context = MockStructuralContext()
        constraints = SafetyEnvelopeV1()

        result = personality.apply(base_policy, context, constraints)

        # Should return unchanged (empty)
        assert result is base_policy
        assert len(result.top_moves) == 0

    # ==========================================================================
    # Test 13: Various Constraint Combinations
    # ==========================================================================

    @pytest.mark.parametrize(
        "top_k,delta_p_max,entropy_min,entropy_max",
        [
            (1, 0.01, 0.0, 0.1),  # Very tight
            (5, 0.15, 0.5, 3.0),  # Default-ish
            (20, 0.5, 0.0, 10.0),  # Very loose
            (3, 0.1, 1.0, 2.0),  # Medium
        ],
    )
    def test_identity_across_constraint_variations(
        self,
        top_k: int,
        delta_p_max: float,
        entropy_min: float,
        entropy_max: float,
    ) -> None:
        """Test that identity holds regardless of constraint configuration."""
        personality = NeutralBaselinePersonalityV1()
        base_policy = create_synthetic_policy()
        context = MockStructuralContext()
        constraints = SafetyEnvelopeV1(
            top_k=top_k,
            delta_p_max=delta_p_max,
            entropy_min=entropy_min,
            entropy_max=entropy_max,
        )

        result = personality.apply(base_policy, context, constraints)

        # Always returns base policy unchanged
        assert result is base_policy

    # ==========================================================================
    # Test 14: Protocol Compliance
    # ==========================================================================

    def test_protocol_compliance(self) -> None:
        """Test that NeutralBaselinePersonalityV1 satisfies PersonalityModuleV1."""
        personality = NeutralBaselinePersonalityV1()

        # Has personality_id property
        assert hasattr(personality, "personality_id")
        assert isinstance(personality.personality_id, str)

        # Has apply method with correct signature
        assert hasattr(personality, "apply")
        assert callable(personality.apply)

        # Has validate_constraints method
        assert hasattr(personality, "validate_constraints")
        assert callable(personality.validate_constraints)

        # Has is_identity method
        assert hasattr(personality, "is_identity")
        assert callable(personality.is_identity)

    # ==========================================================================
    # Test 15: Legality Preservation
    # ==========================================================================

    def test_legality_preservation(self) -> None:
        """Test that no illegal moves are introduced (trivial for identity)."""
        personality = NeutralBaselinePersonalityV1()
        base_policy = create_synthetic_policy()
        context = MockStructuralContext()
        constraints = SafetyEnvelopeV1()

        result = personality.apply(base_policy, context, constraints)

        # All moves in result are from base policy (identity)
        base_uci_set = {m.uci for m in base_policy.top_moves}
        result_uci_set = {m.uci for m in result.top_moves}

        assert result_uci_set == base_uci_set  # Exact equality for identity
