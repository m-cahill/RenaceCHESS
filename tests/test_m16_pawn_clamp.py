"""Tests for Pawn Clamp personality module (M16)."""

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
    # Create a few test pieces
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
                alive=slot_id < 4,  # Only first 4 pieces alive
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
    # Create 64-element lists (all False for simplicity)
    weak_white = [False] * 64
    weak_black = [False] * 64
    strong_white = [False] * 64
    strong_black = [False] * 64
    holes_white = [False] * 64
    holes_black = [False] * 64

    # Mark a few squares as weak for testing
    # Square e4 (rank 3, file 4) = 3*8 + 4 = 28
    weak_white[28] = True

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


def create_test_policy() -> Policy:
    """Create a test base policy."""
    moves = [
        PolicyMove(uci="e2e4", san="e4", p=0.4),
        PolicyMove(uci="d2d4", san="d4", p=0.3),
        PolicyMove(uci="e2e3", san="e3", p=0.2),
        PolicyMove(uci="g1f3", san="Nf3", p=0.1),
    ]
    return Policy(
        top_moves=moves,
        entropy=1.8,
        top_gap=0.1,
    )


class TestPawnClampPersonalityV1:
    """Test suite for PawnClampPersonalityV1."""

    def test_personality_id(self) -> None:
        """Test personality ID."""
        personality = PawnClampPersonalityV1()
        assert personality.personality_id == "style.pawn_clamp.v1"

    def test_identity_configuration(self) -> None:
        """Test that identity configuration exists."""
        # Zero weights should produce identity
        personality = PawnClampPersonalityV1(mobility_weight=0.0, weak_square_weight=0.0)
        constraints = SafetyEnvelopeV1()
        assert personality.is_identity(constraints)

        # Non-zero weights should not be identity
        personality = PawnClampPersonalityV1(mobility_weight=0.6, weak_square_weight=0.4)
        assert not personality.is_identity(constraints)

    def test_identity_transformation(self) -> None:
        """Test that identity configuration returns base policy unchanged."""
        personality = PawnClampPersonalityV1(mobility_weight=0.0, weak_square_weight=0.0)
        base_policy = create_test_policy()
        context = MockStructuralContext()
        constraints = SafetyEnvelopeV1()

        result = personality.apply(base_policy, context, constraints)

        # Should be identical to base policy
        assert len(result.top_moves) == len(base_policy.top_moves)
        for i, (result_move, base_move) in enumerate(zip(result.top_moves, base_policy.top_moves)):
            assert result_move.uci == base_move.uci
            assert abs(result_move.p - base_move.p) < 1e-6

    def test_validate_constraints(self) -> None:
        """Test constraint validation."""
        personality = PawnClampPersonalityV1()

        # Valid constraints should pass
        valid_constraints = SafetyEnvelopeV1(
            top_k=5, delta_p_max=0.15, entropy_min=0.5, entropy_max=3.0
        )
        personality.validate_constraints(valid_constraints)  # Should not raise

        # Invalid constraints are caught by Pydantic validation, not by validate_constraints
        # Test that Pydantic catches invalid top_k
        with pytest.raises(Exception):  # Pydantic ValidationError
            SafetyEnvelopeV1(top_k=0)

        # Test that Pydantic catches invalid delta_p_max
        with pytest.raises(Exception):  # Pydantic ValidationError
            SafetyEnvelopeV1(delta_p_max=1.5)

    def test_determinism(self) -> None:
        """Test that personality is deterministic."""
        personality = PawnClampPersonalityV1()
        base_policy = create_test_policy()
        per_piece = create_test_per_piece_features()
        square_map = create_test_square_map_features()
        context = MockStructuralContext(per_piece=per_piece, square_map=square_map)
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.1)

        # Apply twice with same inputs
        result1 = personality.apply(base_policy, context, constraints)
        result2 = personality.apply(base_policy, context, constraints)

        # Results should be identical
        assert len(result1.top_moves) == len(result2.top_moves)
        for move1, move2 in zip(result1.top_moves, result2.top_moves):
            assert move1.uci == move2.uci
            assert abs(move1.p - move2.p) < 1e-6

    def test_probability_conservation(self) -> None:
        """Test that output probabilities sum to 1.0."""
        personality = PawnClampPersonalityV1()
        base_policy = create_test_policy()
        context = MockStructuralContext()
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.1)

        result = personality.apply(base_policy, context, constraints)

        total_prob = sum(move.p for move in result.top_moves)
        assert abs(total_prob - 1.0) < 1e-6

    def test_envelope_compliance(self) -> None:
        """Test that no move shifts beyond delta_p_max."""
        personality = PawnClampPersonalityV1()
        base_policy = create_test_policy()
        per_piece = create_test_per_piece_features()
        square_map = create_test_square_map_features()
        context = MockStructuralContext(per_piece=per_piece, square_map=square_map)
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.1)

        result = personality.apply(base_policy, context, constraints)

        # Create base probability map
        base_probs = {move.uci: move.p for move in base_policy.top_moves}

        # Check each move in result
        for result_move in result.top_moves:
            if result_move.uci in base_probs:
                base_prob = base_probs[result_move.uci]
                delta = abs(result_move.p - base_prob)
                assert delta <= constraints.delta_p_max + 1e-6

    def test_entropy_bounds(self) -> None:
        """Test that output entropy respects bounds."""
        personality = PawnClampPersonalityV1()
        base_policy = create_test_policy()
        context = MockStructuralContext()
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.1, entropy_min=0.5, entropy_max=3.0)

        result = personality.apply(base_policy, context, constraints)

        assert constraints.entropy_min <= result.entropy <= constraints.entropy_max

    def test_top_k_constraint(self) -> None:
        """Test that only top_k moves are considered."""
        personality = PawnClampPersonalityV1()
        base_policy = create_test_policy()
        context = MockStructuralContext()
        constraints = SafetyEnvelopeV1(top_k=2, delta_p_max=0.1)

        result = personality.apply(base_policy, context, constraints)

        # Should only have top_k moves
        assert len(result.top_moves) <= constraints.top_k

    def test_legality_preservation(self) -> None:
        """Test that no illegal moves are introduced."""
        personality = PawnClampPersonalityV1()
        base_policy = create_test_policy()
        context = MockStructuralContext()
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.1)

        result = personality.apply(base_policy, context, constraints)

        # All moves in result should be from base policy (legal)
        base_uci_set = {move.uci for move in base_policy.top_moves}
        result_uci_set = {move.uci for move in result.top_moves}

        # Result should only contain moves from base policy
        assert result_uci_set.issubset(base_uci_set)

    def test_style_scoring_with_features(self) -> None:
        """Test that style scoring uses M11 features."""
        personality = PawnClampPersonalityV1(mobility_weight=0.6, weak_square_weight=0.4)
        base_policy = create_test_policy()
        per_piece = create_test_per_piece_features()
        square_map = create_test_square_map_features()
        context = MockStructuralContext(per_piece=per_piece, square_map=square_map)
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.15)

        result = personality.apply(base_policy, context, constraints)

        # Should have modified probabilities (not identity)
        assert len(result.top_moves) > 0

        # Check that probabilities changed (not all identical to base)
        base_probs = {move.uci: move.p for move in base_policy.top_moves}
        result_probs = {move.uci: move.p for move in result.top_moves}

        # At least one move should have different probability
        differences = [
            abs(result_probs[uci] - base_probs[uci]) for uci in result_probs if uci in base_probs
        ]
        assert any(diff > 1e-6 for diff in differences)

    def test_empty_context(self) -> None:
        """Test behavior with empty/None context."""
        personality = PawnClampPersonalityV1()
        base_policy = create_test_policy()
        context = MockStructuralContext(per_piece=None, square_map=None)
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.1)

        # Should still work (no style scoring, but should preserve base policy structure)
        result = personality.apply(base_policy, context, constraints)

        assert len(result.top_moves) > 0
        total_prob = sum(move.p for move in result.top_moves)
        assert abs(total_prob - 1.0) < 1e-6

    def test_single_move_policy(self) -> None:
        """Test behavior with single-move policy."""
        personality = PawnClampPersonalityV1()
        base_policy = Policy(
            top_moves=[PolicyMove(uci="e2e4", san="e4", p=1.0)],
            entropy=0.0,
            top_gap=1.0,
        )
        context = MockStructuralContext()
        # Use entropy_min=0.0 to allow single-move policies
        constraints = SafetyEnvelopeV1(top_k=1, delta_p_max=0.1, entropy_min=0.0, entropy_max=3.0)

        result = personality.apply(base_policy, context, constraints)

        # Single-move policies return unchanged (identity) to avoid entropy violation
        assert len(result.top_moves) == 1
        assert result.top_moves[0].uci == "e2e4"
        assert abs(result.top_moves[0].p - 1.0) < 1e-6  # Should remain 1.0

    def test_kl_divergence_measurement(self) -> None:
        """Test KL divergence computation for divergence metrics."""
        personality = PawnClampPersonalityV1()
        base_policy = create_test_policy()
        per_piece = create_test_per_piece_features()
        square_map = create_test_square_map_features()
        context = MockStructuralContext(per_piece=per_piece, square_map=square_map)
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.15)

        result = personality.apply(base_policy, context, constraints)

        # Compute KL divergence
        base_probs = {move.uci: move.p for move in base_policy.top_moves}
        result_probs = {move.uci: move.p for move in result.top_moves}

        kl_div = 0.0
        for uci in base_probs:
            base_p = base_probs[uci]
            result_p = result_probs.get(uci, 0.0)
            if base_p > 0 and result_p > 0:
                kl_div += base_p * math.log2(base_p / result_p)

        # KL divergence should be small (bounded transformation)
        assert kl_div >= 0.0
        assert kl_div < 0.5  # Should be well within bounds

    def test_total_variation_distance(self) -> None:
        """Test total variation distance computation."""
        personality = PawnClampPersonalityV1()
        base_policy = create_test_policy()
        per_piece = create_test_per_piece_features()
        square_map = create_test_square_map_features()
        context = MockStructuralContext(per_piece=per_piece, square_map=square_map)
        constraints = SafetyEnvelopeV1(top_k=4, delta_p_max=0.15)

        result = personality.apply(base_policy, context, constraints)

        # Compute TV distance
        base_probs = {move.uci: move.p for move in base_policy.top_moves}
        result_probs = {move.uci: move.p for move in result.top_moves}

        all_moves = set(base_probs.keys()) | set(result_probs.keys())
        tv_distance = 0.5 * sum(
            abs(result_probs.get(uci, 0.0) - base_probs.get(uci, 0.0)) for uci in all_moves
        )

        # TV distance should be bounded by delta_p_max * top_k
        max_tv = constraints.delta_p_max * constraints.top_k
        assert tv_distance <= max_tv + 1e-6
