"""Context Bridge v2 integration with structural cognition features (M11).

This module provides utilities to generate structural labels and
integrate per-piece and square-map features into Context Bridge v2 payloads.

Governed by: docs/contracts/StructuralCognitionContract_v1.md
"""

from __future__ import annotations

import chess

from renacechess.contracts.models import (
    PerPieceFeaturesV1,
    SquareMapFeaturesV1,
    StructuralCognition,
    StructuralLabel,
)
from renacechess.features.per_piece import extract_per_piece_features
from renacechess.features.square_map import extract_square_map_features


def _square_to_index(square_name: str) -> int:
    """Convert square name to array index (a1=0, h8=63)."""
    file_idx = ord(square_name[0]) - ord("a")
    rank_idx = int(square_name[1]) - 1
    return rank_idx * 8 + file_idx


def _index_to_square(idx: int) -> str:
    """Convert array index to square name."""
    file_idx = idx % 8
    rank_idx = idx // 8
    return chr(ord("a") + file_idx) + str(rank_idx + 1)


def generate_structural_labels(
    per_piece: PerPieceFeaturesV1,
    square_map: SquareMapFeaturesV1,
) -> list[StructuralLabel]:
    """Generate semantic labels from structural features for LLM grounding.

    Args:
        per_piece: Per-piece structural features
        square_map: Square-level structural maps

    Returns:
        List of structural labels for narrative seeding
    """
    labels: list[StructuralLabel] = []

    # Generate piece-level labels
    for piece in per_piece.pieces:
        if not piece.alive:
            continue

        slot_name = f"{piece.piece_type}_{piece.starting_file}"

        # Hanging piece
        if piece.is_hanging:
            labels.append(
                StructuralLabel(
                    type="hanging-piece",
                    target=slot_name,
                    description=(
                        f"{piece.color.capitalize()} {piece.piece_type} on {piece.square} "
                        f"is hanging (attacked but not defended)"
                    ),
                )
            )

        # Pinned piece
        if piece.is_pinned:
            labels.append(
                StructuralLabel(
                    type="pinned-piece",
                    target=slot_name,
                    description=(
                        f"{piece.color.capitalize()} {piece.piece_type} on {piece.square} "
                        f"is pinned to the king"
                    ),
                )
            )

        # Dominated piece
        if piece.is_dominated:
            labels.append(
                StructuralLabel(
                    type="dominated-piece",
                    target=slot_name,
                    description=(
                        f"{piece.color.capitalize()} {piece.piece_type} on {piece.square} "
                        f"is under significant pressure (net defense: {piece.net_defense})"
                    ),
                )
            )

        # Key defender
        if piece.is_defender_of_king:
            labels.append(
                StructuralLabel(
                    type="key-defender",
                    target=slot_name,
                    description=(
                        f"{piece.color.capitalize()} {piece.piece_type} on {piece.square} "
                        f"is defending squares around the king"
                    ),
                )
            )

    # Generate square-level labels (holes and weak squares)
    for idx in range(64):
        square_name = _index_to_square(idx)

        # Holes for White
        if square_map.is_hole_for_white[idx]:
            labels.append(
                StructuralLabel(
                    type="hole",
                    target=square_name,
                    description=f"Hole on {square_name} for White (cannot be contested by pawns)",
                )
            )

        # Holes for Black
        if square_map.is_hole_for_black[idx]:
            labels.append(
                StructuralLabel(
                    type="hole",
                    target=square_name,
                    description=f"Hole on {square_name} for Black (cannot be contested by pawns)",
                )
            )

        # Weak squares for White (limit to central squares to avoid noise)
        if square_map.weak_for_white[idx]:
            rank = idx // 8
            file = idx % 8
            # Focus on central/important squares (ranks 3-6, files c-f)
            if 2 <= rank <= 5 and 2 <= file <= 5:
                labels.append(
                    StructuralLabel(
                        type="weak-square",
                        target=square_name,
                        description=f"Weak square {square_name} for White",
                    )
                )

        # Weak squares for Black (limit to central squares)
        if square_map.weak_for_black[idx]:
            rank = idx // 8
            file = idx % 8
            if 2 <= rank <= 5 and 2 <= file <= 5:
                labels.append(
                    StructuralLabel(
                        type="weak-square",
                        target=square_name,
                        description=f"Weak square {square_name} for Black",
                    )
                )

        # Strong squares for White (limit to central squares)
        if square_map.strong_for_white[idx]:
            rank = idx // 8
            file = idx % 8
            if 2 <= rank <= 5 and 2 <= file <= 5:
                labels.append(
                    StructuralLabel(
                        type="strong-square",
                        target=square_name,
                        description=f"Strong square {square_name} for White",
                    )
                )

        # Strong squares for Black (limit to central squares)
        if square_map.strong_for_black[idx]:
            rank = idx // 8
            file = idx % 8
            if 2 <= rank <= 5 and 2 <= file <= 5:
                labels.append(
                    StructuralLabel(
                        type="strong-square",
                        target=square_name,
                        description=f"Strong square {square_name} for Black",
                    )
                )

    return labels


def extract_structural_cognition(board: chess.Board) -> StructuralCognition:
    """Extract full structural cognition from a chess position.

    Args:
        board: A python-chess Board object

    Returns:
        StructuralCognition container with per-piece, square-map, and labels
    """
    per_piece = extract_per_piece_features(board)
    square_map = extract_square_map_features(board)
    labels = generate_structural_labels(per_piece, square_map)

    return StructuralCognition(
        per_piece=per_piece,
        square_map=square_map,
        structural_labels=labels,
    )
