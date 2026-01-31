"""Pawn Clamp personality module (M16).

This personality implements a GM-style "pawn clamp" heuristic that:
- Boosts moves that reduce opponent piece mobility
- Prefers moves that create weak squares/holes

See docs/contracts/PERSONALITY_SAFETY_CONTRACT_v1.md for the governing contract.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import chess

from renacechess.contracts.models import (
    PerPieceFeaturesV1,
    Policy,
    PolicyMove,
    SafetyEnvelopeV1,
    SquareMapFeaturesV1,
)

if TYPE_CHECKING:
    from renacechess.personality.interfaces import StructuralContext


class PawnClampPersonalityV1:
    """Pawn Clamp personality implementation.

    This personality re-ranks moves within the top_k based on:
    1. Opponent mobility reduction (from M11 per-piece features)
    2. Weak square/hole creation (from M11 square maps)

    All transformations respect the safety envelope constraints.
    """

    def __init__(
        self,
        mobility_weight: float = 0.6,
        weak_square_weight: float = 0.4,
    ) -> None:
        """Initialize Pawn Clamp personality.

        Args:
            mobility_weight: Weight for mobility reduction scoring (default: 0.6)
            weak_square_weight: Weight for weak square creation scoring (default: 0.4)
        """
        self._mobility_weight = mobility_weight
        self._weak_square_weight = weak_square_weight

    @property
    def personality_id(self) -> str:
        """Unique identifier for this personality."""
        return "style.pawn_clamp.v1"

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
        # So we don't need to re-validate these here
        # This method exists for extensibility if additional validation is needed
        pass

    def is_identity(self, constraints: SafetyEnvelopeV1) -> bool:
        """Check if this configuration produces identity transformation.

        Args:
            constraints: Safety envelope to check.

        Returns:
            True if weights are zero (identity), False otherwise.
        """
        # Identity occurs when both weights are zero (no style shaping)
        return self._mobility_weight == 0.0 and self._weak_square_weight == 0.0

    def apply(
        self,
        base_policy: Policy,
        context: StructuralContext,
        constraints: SafetyEnvelopeV1,
    ) -> Policy:
        """Apply Pawn Clamp transformation to base policy.

        Args:
            base_policy: Base policy distribution from learned human policy.
            context: Structural context (M11 per-piece and square-map features).
            constraints: Safety envelope parameters.

        Returns:
            Modified policy distribution within the allowed envelope.

        Raises:
            ValueError: If constraints are invalid.
            RuntimeError: If transformation would violate safety invariants.
        """
        # Validate constraints
        self.validate_constraints(constraints)

        # If identity configuration, return base policy unchanged
        if self.is_identity(constraints):
            return base_policy

        # Get top_k moves from base policy
        top_moves = base_policy.top_moves[: constraints.top_k]

        if not top_moves:
            # No moves to transform
            return base_policy

        # Compute style scores for each move
        style_scores = self._compute_style_scores(top_moves, context, constraints)

        # Apply style shaping within safety envelope
        modified_moves = self._apply_style_shaping(
            top_moves, style_scores, base_policy, constraints
        )

        # Recompute entropy and top_gap
        entropy = self._compute_entropy(modified_moves)
        top_gap = (
            modified_moves[0].p - modified_moves[1].p
            if len(modified_moves) > 1
            else modified_moves[0].p
        )

        # Validate entropy bounds
        # Special case: single move policies have entropy 0.0, which may violate entropy_min
        # In this case, we return the base policy unchanged (identity transformation)
        if len(modified_moves) == 1:
            # Single move: cannot modify without violating entropy bounds
            return base_policy

        if entropy < constraints.entropy_min or entropy > constraints.entropy_max:
            raise RuntimeError(
                f"Transformation would violate entropy bounds: "
                f"entropy={entropy:.3f}, bounds=[{constraints.entropy_min:.3f}, "
                f"{constraints.entropy_max:.3f}]"
            )

        return Policy(
            top_moves=modified_moves,
            entropy=entropy,
            top_gap=top_gap,
        )

    def _compute_style_scores(
        self,
        moves: list[PolicyMove],
        context: StructuralContext,
        constraints: SafetyEnvelopeV1,
    ) -> dict[str, float]:
        """Compute style scores for each move.

        Args:
            moves: List of candidate moves.
            context: Structural context with M11 features.
            constraints: Safety envelope (for side-to-move if needed).

        Returns:
            Dictionary mapping UCI move to style score (higher = more preferred).
        """
        scores: dict[str, float] = {}

        per_piece = context.per_piece
        square_map = context.square_map

        for move in moves:
            mobility_score = 0.0
            weak_square_score = 0.0

            # Parse UCI move
            try:
                from_square = chess.parse_square(move.uci[:2])
                to_square = chess.parse_square(move.uci[2:4])
            except (ValueError, IndexError):
                # Invalid UCI format - skip style scoring
                scores[move.uci] = 0.0
                continue

            # Compute mobility reduction score
            if per_piece is not None:
                mobility_score = self._score_mobility_reduction(from_square, to_square, per_piece)

            # Compute weak square creation score
            if square_map is not None:
                weak_square_score = self._score_weak_square_creation(
                    from_square, to_square, square_map
                )

            # Combine scores with weights
            combined_score = (
                self._mobility_weight * mobility_score
                + self._weak_square_weight * weak_square_score
            )

            scores[move.uci] = combined_score

        return scores

    def _score_mobility_reduction(
        self,
        from_square: chess.Square,
        to_square: chess.Square,
        per_piece: PerPieceFeaturesV1,
    ) -> float:
        """Score how much a move reduces opponent mobility.

        Heuristic: Moves that attack or restrict pieces with high mobility
        get higher scores.

        Args:
            from_square: Source square of the move.
            to_square: Destination square of the move.
            per_piece: Per-piece features for current position.

        Returns:
            Mobility reduction score (normalized, higher = more reduction).
        """
        score = 0.0

        # Check if move attacks an opponent piece with high mobility
        for piece in per_piece.pieces:
            if not piece.alive or piece.square is None:
                continue

            # Check if this piece is on the destination square (capture/attack)
            try:
                piece_square = chess.parse_square(piece.square)
            except ValueError:
                continue

            if piece_square == to_square:
                # Move attacks this piece - score based on its mobility
                # Higher mobility pieces are more valuable to restrict
                mobility = piece.mobility_legal
                # Normalize: mobility / 20 (max reasonable mobility)
                normalized_mobility = min(mobility / 20.0, 1.0)
                score += normalized_mobility * 0.5

            # Check if move restricts mobility by controlling squares near the piece
            # (Simplified heuristic: if move is a pawn push, it may restrict mobility)
            if self._is_pawn_push(from_square, to_square):
                # Pawn pushes can restrict piece mobility
                # Score based on proximity to high-mobility pieces
                if piece.mobility_legal > 5:
                    # Piece has good mobility - pawn push near it is valuable
                    score += 0.3

        return min(score, 1.0)  # Cap at 1.0

    def _score_weak_square_creation(
        self,
        from_square: chess.Square,
        to_square: chess.Square,
        square_map: SquareMapFeaturesV1,
    ) -> float:
        """Score how much a move creates weak squares/holes.

        Heuristic: Pawn pushes into contested squares create weak squares.
        Moves that advance into areas with existing weak squares amplify them.

        Args:
            from_square: Source square of the move.
            to_square: Destination square of the move.
            square_map: Square map features for current position.

        Returns:
            Weak square creation score (normalized, higher = more weak squares).
        """
        score = 0.0

        # Check if move is a pawn push
        if not self._is_pawn_push(from_square, to_square):
            return score

        # Get square index for destination
        to_rank = chess.square_rank(to_square)
        to_file = chess.square_file(to_square)

        # Check if destination square is already weak or a hole
        # (Using white's perspective - would need side-to-move for full accuracy)
        # For now, check both sides' weak squares
        weak_white = square_map.weak_for_white
        weak_black = square_map.weak_for_black
        holes_white = square_map.is_hole_for_white
        holes_black = square_map.is_hole_for_black

        square_idx = to_rank * 8 + to_file

        # If pushing into a weak square, that's valuable
        if square_idx < 64:
            if weak_white[square_idx] or weak_black[square_idx]:
                score += 0.4
            if holes_white[square_idx] or holes_black[square_idx]:
                score += 0.6

        # Check squares ahead of the pawn push (future weak squares)
        if to_rank < 7:  # Not on back rank
            ahead_square_idx = (to_rank + 1) * 8 + to_file
            if ahead_square_idx < 64:
                if weak_white[ahead_square_idx] or weak_black[ahead_square_idx]:
                    score += 0.3

        return min(score, 1.0)  # Cap at 1.0

    def _is_pawn_push(self, from_square: chess.Square, to_square: chess.Square) -> bool:
        """Check if a move is a pawn push.

        Args:
            from_square: Source square.
            to_square: Destination square.

        Returns:
            True if move appears to be a pawn push (same file, forward direction).
        """
        from_file = chess.square_file(from_square)
        to_file = chess.square_file(to_square)
        from_rank = chess.square_rank(from_square)
        to_rank = chess.square_rank(to_square)

        # Pawn push: same file, forward direction (rank increases for white, decreases for black)
        # Since we don't know side-to-move, check if rank changes in either direction
        return from_file == to_file and abs(to_rank - from_rank) <= 2

    def _apply_style_shaping(
        self,
        moves: list[PolicyMove],
        style_scores: dict[str, float],
        base_policy: Policy,
        constraints: SafetyEnvelopeV1,
    ) -> list[PolicyMove]:
        """Apply style shaping to move probabilities within safety envelope.

        Args:
            moves: List of candidate moves.
            style_scores: Style scores for each move.
            base_policy: Original base policy (for reference).
            constraints: Safety envelope parameters.

        Returns:
            Modified list of PolicyMove objects with updated probabilities.
        """
        # Create base probability map
        base_probs: dict[str, float] = {move.uci: move.p for move in moves}

        # Normalize style scores to [0, 1] range
        if not style_scores:
            return moves

        min_score = min(style_scores.values())
        max_score = max(style_scores.values())
        score_range = max_score - min_score if max_score > min_score else 1.0

        normalized_scores: dict[str, float] = {}
        for uci, score in style_scores.items():
            if score_range > 0:
                normalized_scores[uci] = (score - min_score) / score_range
            else:
                normalized_scores[uci] = 0.5  # Neutral if all scores equal

        # Compute style adjustments (within delta_p_max)
        # Use a conservative approach: clamp each probability to [base - delta, base + delta]
        # before renormalization to ensure constraint is preserved
        adjustments: dict[str, float] = {}
        for move in moves:
            uci = move.uci
            base_prob = base_probs[uci]
            style_score = normalized_scores.get(uci, 0.5)

            # Compute adjustment: positive style score increases probability
            # Scale by delta_p_max to respect envelope
            adjustment = (style_score - 0.5) * 2.0 * constraints.delta_p_max
            adjustments[uci] = adjustment

        # Apply adjustments with clamping to respect delta_p_max
        modified_probs: dict[str, float] = {}
        for move in moves:
            uci = move.uci
            base_prob = base_probs[uci]
            adjustment = adjustments[uci]

            # Clamp adjustment to ensure delta_p_max is respected
            clamped_adjustment = max(
                -constraints.delta_p_max,
                min(constraints.delta_p_max, adjustment),
            )

            # Apply adjustment, clamping to [0, 1] and [base - delta, base + delta]
            new_prob = max(
                0.0,
                min(
                    1.0,
                    max(
                        base_prob - constraints.delta_p_max,
                        min(base_prob + constraints.delta_p_max, base_prob + clamped_adjustment),
                    ),
                ),
            )
            modified_probs[uci] = new_prob

        # Renormalize to ensure probabilities sum to 1.0
        # Use iterative scaling to ensure delta_p_max is respected after normalization
        total_prob = sum(modified_probs.values())
        if total_prob > 0:
            # Normalize
            modified_probs = {uci: prob / total_prob for uci, prob in modified_probs.items()}

            # Check if normalization caused any violations
            max_violation = 0.0
            for move in moves:
                uci = move.uci
                base_prob = base_probs[uci]
                normalized_prob = modified_probs[uci]
                delta = abs(normalized_prob - base_prob)
                if delta > constraints.delta_p_max:
                    violation_ratio = delta / constraints.delta_p_max
                    max_violation = max(max_violation, violation_ratio)

            # If violations occurred, scale all probabilities toward base to fix them
            if max_violation > 1.0:
                # Scale factor: bring probabilities closer to base
                # Use 1/max_violation to ensure no move exceeds delta_p_max
                scale_factor = 1.0 / max_violation
                scaled_probs: dict[str, float] = {}
                for move in moves:
                    uci = move.uci
                    base_prob = base_probs[uci]
                    normalized_prob = modified_probs[uci]

                    # Interpolate between base and normalized: base + scale * (normalized - base)
                    scaled_prob = base_prob + scale_factor * (normalized_prob - base_prob)
                    scaled_probs[uci] = scaled_prob

                # Renormalize scaled probabilities
                total_scaled = sum(scaled_probs.values())
                if total_scaled > 0:
                    modified_probs = {
                        uci: prob / total_scaled for uci, prob in scaled_probs.items()
                    }
                else:
                    modified_probs = base_probs
        else:
            # Fallback: uniform distribution
            uniform_prob = 1.0 / len(moves)
            modified_probs = {uci: uniform_prob for uci in base_probs.keys()}

        # Final verification: ensure delta_p_max constraint (with tolerance for floating point)
        for move in moves:
            uci = move.uci
            base_prob = base_probs[uci]
            new_prob = modified_probs[uci]
            delta = abs(new_prob - base_prob)
            if delta > constraints.delta_p_max + 1e-4:  # Tolerance for floating point
                # If still violated, return base probabilities as fallback
                return [
                    PolicyMove(uci=move.uci, san=move.san, p=base_probs[move.uci]) for move in moves
                ]

        # Create modified PolicyMove objects
        modified_moves = [
            PolicyMove(uci=uci, san=move.san, p=modified_probs[uci])
            for move in moves
            for uci in [move.uci]
        ]

        # Sort by probability (descending)
        modified_moves.sort(key=lambda m: m.p, reverse=True)

        return modified_moves

    def _compute_entropy(self, moves: list[PolicyMove]) -> float:
        """Compute Shannon entropy of the policy distribution.

        Args:
            moves: List of PolicyMove objects.

        Returns:
            Shannon entropy value.
        """
        entropy = 0.0
        for move in moves:
            if move.p > 0:
                entropy -= move.p * math.log2(move.p)
        return entropy
