"""Square-level structural map extractor (Structural Cognition Contract v1).

This module extracts square-level structural maps for weak/strong/hole analysis.
All maps are side-relative and have exactly 64 entries (a1=0 to h8=63).

Governed by: docs/contracts/StructuralCognitionContract_v1.md
"""

from __future__ import annotations

import chess

from renacechess.contracts.models import SquareMapFeaturesV1


def _square_index(sq: chess.Square) -> int:
    """Convert chess.Square to array index (a1=0, h8=63)."""
    # chess.Square is already 0-63 with a1=0
    return sq


def _count_attackers_at_square(board: chess.Board, square: chess.Square, color: chess.Color) -> int:
    """Count attackers of a given color on a square."""
    return len(board.attackers(color, square))


def _compute_control_differential(board: chess.Board) -> tuple[list[int], list[int]]:
    """Compute control differential for both sides.

    Returns:
        (control_diff_white, control_diff_black) where:
        - control_diff_white[sq] = white_attackers - black_attackers
        - control_diff_black[sq] = black_attackers - white_attackers
    """
    control_white = [0] * 64
    control_black = [0] * 64

    for sq in chess.SQUARES:
        white_attackers = _count_attackers_at_square(board, sq, chess.WHITE)
        black_attackers = _count_attackers_at_square(board, sq, chess.BLACK)
        idx = _square_index(sq)
        control_white[idx] = white_attackers - black_attackers
        control_black[idx] = black_attackers - white_attackers

    return control_white, control_black


def _compute_pawn_contestability(board: chess.Board) -> tuple[list[bool], list[bool]]:
    """Compute which squares can be contested by pawns.

    A square is pawn-contestable for side S if any pawn of side S could
    legally move or capture to that square in the future (ignoring checks).

    Returns:
        (pawn_contestable_white, pawn_contestable_black)
    """
    contestable_white = [False] * 64
    contestable_black = [False] * 64

    # Get all pawns (returns SquareSet, which is iterable)
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)

    # For White pawns (move up the board)
    for pawn_sq in white_pawns:
        pawn_file = chess.square_file(pawn_sq)
        pawn_rank = chess.square_rank(pawn_sq)

        # Squares this pawn can potentially reach via advance or capture
        for target_rank in range(pawn_rank + 1, 8):  # Can only go up
            # Advance squares (same file)
            advance_sq = chess.square(pawn_file, target_rank)
            contestable_white[_square_index(advance_sq)] = True

            # Capture squares (diagonal files)
            for df in [-1, 1]:
                capture_file = pawn_file + df
                if 0 <= capture_file <= 7:
                    capture_sq = chess.square(capture_file, target_rank)
                    contestable_white[_square_index(capture_sq)] = True

    # For Black pawns (move down the board)
    for pawn_sq in black_pawns:
        pawn_file = chess.square_file(pawn_sq)
        pawn_rank = chess.square_rank(pawn_sq)

        # Squares this pawn can potentially reach via advance or capture
        for target_rank in range(pawn_rank - 1, -1, -1):  # Can only go down
            # Advance squares (same file)
            advance_sq = chess.square(pawn_file, target_rank)
            contestable_black[_square_index(advance_sq)] = True

            # Capture squares (diagonal files)
            for df in [-1, 1]:
                capture_file = pawn_file + df
                if 0 <= capture_file <= 7:
                    capture_sq = chess.square(capture_file, target_rank)
                    contestable_black[_square_index(capture_sq)] = True

    return contestable_white, contestable_black


def _compute_holes(
    control_diff: list[int],
    pawn_contestable: list[bool],
) -> list[bool]:
    """Compute holes for a side.

    A hole for side S is a square where:
    - pawn_contestable_by_S == false
    - control_diff_for_S < 0

    Args:
        control_diff: Control differential for this side
        pawn_contestable: Pawn contestability for this side

    Returns:
        64-element list of booleans indicating holes
    """
    holes = [False] * 64
    for idx in range(64):
        if not pawn_contestable[idx] and control_diff[idx] < 0:
            holes[idx] = True
    return holes


def _compute_weak_squares(
    control_diff: list[int],
    pawn_contestable: list[bool],
) -> list[bool]:
    """Compute weak squares for a side.

    Weak for S: control_diff_for_S < 0 AND pawn_contestable_by_S == false

    Args:
        control_diff: Control differential for this side
        pawn_contestable: Pawn contestability for this side

    Returns:
        64-element list of booleans indicating weak squares
    """
    weak = [False] * 64
    for idx in range(64):
        if control_diff[idx] < 0 and not pawn_contestable[idx]:
            weak[idx] = True
    return weak


def _compute_strong_squares(
    control_diff: list[int],
    pawn_contestable: list[bool],
) -> list[bool]:
    """Compute strong squares for a side.

    Strong for S: control_diff_for_S > 0 AND pawn_contestable_by_S == true

    Args:
        control_diff: Control differential for this side
        pawn_contestable: Pawn contestability for this side

    Returns:
        64-element list of booleans indicating strong squares
    """
    strong = [False] * 64
    for idx in range(64):
        if control_diff[idx] > 0 and pawn_contestable[idx]:
            strong[idx] = True
    return strong


def extract_square_map_features(board: chess.Board) -> SquareMapFeaturesV1:
    """Extract square-level structural maps from a chess position.

    Args:
        board: A python-chess Board object

    Returns:
        SquareMapFeaturesV1 with 64-element maps for weak/strong/hole analysis
    """
    # Compute control differentials
    control_white, control_black = _compute_control_differential(board)

    # Compute pawn contestability
    pawn_contestable_white, pawn_contestable_black = _compute_pawn_contestability(board)

    # Compute holes
    holes_white = _compute_holes(control_white, pawn_contestable_white)
    holes_black = _compute_holes(control_black, pawn_contestable_black)

    # Compute weak squares
    weak_white = _compute_weak_squares(control_white, pawn_contestable_white)
    weak_black = _compute_weak_squares(control_black, pawn_contestable_black)

    # Compute strong squares
    strong_white = _compute_strong_squares(control_white, pawn_contestable_white)
    strong_black = _compute_strong_squares(control_black, pawn_contestable_black)

    return SquareMapFeaturesV1(
        schema_version="square_map.v1",
        weak_for_white=weak_white,
        strong_for_white=strong_white,
        weak_for_black=weak_black,
        strong_for_black=strong_black,
        is_hole_for_white=holes_white,
        is_hole_for_black=holes_black,
        control_diff_white=control_white,
        control_diff_black=control_black,
        pawn_contestable_white=pawn_contestable_white,
        pawn_contestable_black=pawn_contestable_black,
    )

