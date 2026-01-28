"""Structural feature extractors for RenaceCHESS (M11).

This module provides deterministic, engine-free feature extraction
for piece-level and square-level structural cognition.

Governed by: docs/contracts/StructuralCognitionContract_v1.md
"""

from renacechess.features.context_bridge_v2 import (
    extract_structural_cognition,
    generate_structural_labels,
)
from renacechess.features.per_piece import extract_per_piece_features
from renacechess.features.square_map import extract_square_map_features

__all__ = [
    "extract_per_piece_features",
    "extract_square_map_features",
    "extract_structural_cognition",
    "generate_structural_labels",
]

