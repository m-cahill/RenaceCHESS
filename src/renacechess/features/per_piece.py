"""Per-piece structural feature extractor (Structural Cognition Contract v1).

This module extracts piece-indexed structural features from a chess position.
All 32 piece slots are maintained in fixed order regardless of captures/promotions.

Governed by: docs/contracts/StructuralCognitionContract_v1.md
"""

from __future__ import annotations

import chess

from renacechess.contracts.models import PerPieceFeaturesV1, PieceFeatures

# Piece values for safe mobility calculation (no full SEE)
PIECE_VALUES: dict[chess.PieceType, int] = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 1000,  # Effectively infinite
}

# Fixed slot ordering per Structural Cognition Contract v1
# Slots 0-15: White, Slots 16-31: Black
SLOT_DEFINITIONS: list[tuple[chess.Color, chess.PieceType, str]] = [
    # White pieces (slots 0-15)
    (chess.WHITE, chess.KING, "e"),
    (chess.WHITE, chess.QUEEN, "d"),
    (chess.WHITE, chess.ROOK, "a"),
    (chess.WHITE, chess.ROOK, "h"),
    (chess.WHITE, chess.BISHOP, "c"),
    (chess.WHITE, chess.BISHOP, "f"),
    (chess.WHITE, chess.KNIGHT, "b"),
    (chess.WHITE, chess.KNIGHT, "g"),
    (chess.WHITE, chess.PAWN, "a"),
    (chess.WHITE, chess.PAWN, "b"),
    (chess.WHITE, chess.PAWN, "c"),
    (chess.WHITE, chess.PAWN, "d"),
    (chess.WHITE, chess.PAWN, "e"),
    (chess.WHITE, chess.PAWN, "f"),
    (chess.WHITE, chess.PAWN, "g"),
    (chess.WHITE, chess.PAWN, "h"),
    # Black pieces (slots 16-31)
    (chess.BLACK, chess.KING, "e"),
    (chess.BLACK, chess.QUEEN, "d"),
    (chess.BLACK, chess.ROOK, "a"),
    (chess.BLACK, chess.ROOK, "h"),
    (chess.BLACK, chess.BISHOP, "c"),
    (chess.BLACK, chess.BISHOP, "f"),
    (chess.BLACK, chess.KNIGHT, "b"),
    (chess.BLACK, chess.KNIGHT, "g"),
    (chess.BLACK, chess.PAWN, "a"),
    (chess.BLACK, chess.PAWN, "b"),
    (chess.BLACK, chess.PAWN, "c"),
    (chess.BLACK, chess.PAWN, "d"),
    (chess.BLACK, chess.PAWN, "e"),
    (chess.BLACK, chess.PAWN, "f"),
    (chess.BLACK, chess.PAWN, "g"),
    (chess.BLACK, chess.PAWN, "h"),
]

PIECE_TYPE_TO_STR: dict[chess.PieceType, str] = {
    chess.KING: "K",
    chess.QUEEN: "Q",
    chess.ROOK: "R",
    chess.BISHOP: "B",
    chess.KNIGHT: "N",
    chess.PAWN: "P",
}


def _square_to_str(sq: chess.Square) -> str:
    """Convert square index to algebraic notation."""
    return chess.square_name(sq)


def _count_attackers(board: chess.Board, square: chess.Square, by_color: chess.Color) -> int:
    """Count the number of pieces of a color attacking a square."""
    return len(board.attackers(by_color, square))


def _is_square_safe_for_piece(
    board: chess.Board,
    piece_square: chess.Square,
    dest_square: chess.Square,
    piece_type: chess.PieceType,
    piece_color: chess.Color,
) -> bool:
    """Determine if moving to dest_square is 'safe' per Structural Cognition Contract v1.

    A move is unsafe if:
    1. The destination is attacked by any enemy piece, AND
    2. The moving piece is not defended on that square by at least one
       friendly piece of equal or lower value.
    """
    enemy_color = not piece_color
    enemy_attackers = board.attackers(enemy_color, dest_square)

    if not enemy_attackers:
        # Not attacked = safe
        return True

    # Find our defenders on the destination (excluding the moving piece itself)
    our_defenders = board.attackers(piece_color, dest_square)
    # Remove the moving piece from defenders using SquareSet difference
    our_defenders = our_defenders.difference(chess.SquareSet([piece_square]))

    if not our_defenders:
        # Attacked and not defended = unsafe
        return False

    # Check if we have a defender of equal or lower value
    # our_defenders is a SquareSet, which is iterable
    piece_value = PIECE_VALUES[piece_type]
    for defender_sq in our_defenders:
        defender_piece = board.piece_at(defender_sq)
        if defender_piece and PIECE_VALUES[defender_piece.piece_type] <= piece_value:
            return True

    return False


def _compute_piece_mobility(board: chess.Board, piece_square: chess.Square) -> tuple[int, int]:
    """Compute legal and safe mobility for a piece.

    Returns:
        (mobility_legal, mobility_safe)
    """
    piece = board.piece_at(piece_square)
    if piece is None:
        return 0, 0

    legal_count = 0
    safe_count = 0

    for move in board.legal_moves:
        if move.from_square == piece_square:
            legal_count += 1
            if _is_square_safe_for_piece(
                board, piece_square, move.to_square, piece.piece_type, piece.color
            ):
                safe_count += 1

    return legal_count, safe_count


def _is_piece_pinned(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    """Check if a piece is pinned to its king."""
    king_square = board.king(color)
    if king_square is None:
        return False
    return board.is_pinned(color, square)


def _is_defender_of_king(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    """Check if a piece defends squares around the friendly king."""
    king_square = board.king(color)
    if king_square is None:
        return False

    piece = board.piece_at(square)
    if piece is None:
        return False

    # Get squares around the king
    king_file = chess.square_file(king_square)
    king_rank = chess.square_rank(king_square)

    for df in [-1, 0, 1]:
        for dr in [-1, 0, 1]:
            if df == 0 and dr == 0:
                continue
            f = king_file + df
            r = king_rank + dr
            if 0 <= f <= 7 and 0 <= r <= 7:
                adj_square = chess.square(f, r)
                if adj_square in board.attacks(square):
                    return True

    return False


def _is_attacker(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    """Check if a piece attacks enemy pieces or key central squares."""
    piece = board.piece_at(square)
    if piece is None:
        return False

    enemy_color = not color
    attacks = board.attacks(square)

    # Check if attacking any enemy pieces (attacks is a SquareSet, which is iterable)
    for attacked_sq in attacks:
        attacked_piece = board.piece_at(attacked_sq)
        if attacked_piece and attacked_piece.color == enemy_color:
            return True

    # Check if attacking key central squares (d4, d5, e4, e5)
    central_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    for central in central_squares:
        if central in attacks:
            return True

    return False


def _find_piece_for_slot(
    board: chess.Board,
    slot_color: chess.Color,
    slot_piece_type: chess.PieceType,
    starting_file: str,
    occupied_squares: set[chess.Square],
) -> chess.Square | None:
    """Find the piece matching a slot definition.

    This is a heuristic - we try to match pieces to their original starting positions.
    For a more accurate implementation, you'd track piece identity through the game.
    """
    file_idx = ord(starting_file) - ord("a")

    # Get all pieces of this type and color (returns SquareSet)
    piece_squares = board.pieces(slot_piece_type, slot_color)

    # First, try to find a piece on or near the starting file
    candidates = []
    for sq in piece_squares:
        if sq in occupied_squares:
            continue
        sq_file = chess.square_file(sq)
        distance = abs(sq_file - file_idx)
        candidates.append((distance, sq))

    if not candidates:
        return None

    # Sort by distance to starting file, then by square index for determinism
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][1]


def extract_per_piece_features(board: chess.Board) -> PerPieceFeaturesV1:
    """Extract per-piece structural features from a chess position.

    Args:
        board: A python-chess Board object

    Returns:
        PerPieceFeaturesV1 with 32 fixed slots of piece features
    """
    pieces: list[PieceFeatures] = []
    occupied_squares: set[chess.Square] = set()

    for slot_id, (slot_color, slot_piece_type, starting_file) in enumerate(SLOT_DEFINITIONS):
        color_str = "white" if slot_color == chess.WHITE else "black"
        piece_type_str = PIECE_TYPE_TO_STR[slot_piece_type]

        # Find piece for this slot
        piece_square = _find_piece_for_slot(
            board, slot_color, slot_piece_type, starting_file, occupied_squares
        )

        if piece_square is not None:
            occupied_squares.add(piece_square)

            # Compute features
            mobility_legal, mobility_safe = _compute_piece_mobility(board, piece_square)
            attacked_by = _count_attackers(board, piece_square, not slot_color)
            defended_by = _count_attackers(board, piece_square, slot_color)
            net_defense = defended_by - attacked_by

            # Check for promotion (pawn on back rank with different piece type)
            actual_piece = board.piece_at(piece_square)
            is_promoted = False
            promoted_to = None
            if slot_piece_type == chess.PAWN and actual_piece:
                if actual_piece.piece_type != chess.PAWN:
                    is_promoted = True
                    promoted_to = PIECE_TYPE_TO_STR.get(actual_piece.piece_type)

            piece_features = PieceFeatures(
                slot_id=slot_id,
                color=color_str,
                piece_type=piece_type_str,
                starting_file=starting_file,
                alive=True,
                square=_square_to_str(piece_square),
                is_promoted=is_promoted,
                promoted_to=promoted_to,
                mobility_legal=mobility_legal,
                mobility_safe=mobility_safe,
                attacked_by=attacked_by,
                defended_by=defended_by,
                net_defense=net_defense,
                is_hanging=attacked_by > 0 and defended_by == 0,
                is_pinned=_is_piece_pinned(board, piece_square, slot_color),
                is_restricted=mobility_legal < 3,
                is_dominated=net_defense < -1,
                is_attacker=_is_attacker(board, piece_square, slot_color),
                is_defender_of_king=_is_defender_of_king(board, piece_square, slot_color),
            )
        else:
            # Piece is captured - slot preserved with null values
            piece_features = PieceFeatures(
                slot_id=slot_id,
                color=color_str,
                piece_type=piece_type_str,
                starting_file=starting_file,
                alive=False,
                square=None,
                is_promoted=False,
                promoted_to=None,
                mobility_legal=0,
                mobility_safe=0,
                attacked_by=0,
                defended_by=0,
                net_defense=0,
                is_hanging=False,
                is_pinned=False,
                is_restricted=True,  # No mobility = restricted
                is_dominated=False,
                is_attacker=False,
                is_defender_of_king=False,
            )

        pieces.append(piece_features)

    return PerPieceFeaturesV1(schema_version="per_piece.v1", pieces=pieces)
