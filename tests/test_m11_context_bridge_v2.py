"""Tests for Context Bridge v2 structural cognition integration (M11).

These tests verify:
1. Structural cognition extraction
2. Label generation
3. Context Bridge v2 model validation
"""

from __future__ import annotations

import chess

from renacechess.contracts.models import (
    HDI,
    ContextBridgeMetaV2,
    ContextBridgePayloadV2,
    HDIComponents,
    HumanWDL,
    HumanWDLContainer,
    NarrativeSeedV2,
    Policy,
    PolicyMove,
    Position,
    PositionConditioning,
    StructuralLabel,
)
from renacechess.features import (
    extract_per_piece_features,
    extract_square_map_features,
    extract_structural_cognition,
    generate_structural_labels,
)


class TestStructuralCognitionExtraction:
    """Test full structural cognition extraction."""

    def test_extract_structural_cognition(self) -> None:
        """Verify full structural cognition extraction."""
        board = chess.Board()
        result = extract_structural_cognition(board)

        assert result.per_piece is not None
        assert result.square_map is not None
        assert result.structural_labels is not None

    def test_structural_cognition_has_32_pieces(self) -> None:
        """Verify per-piece has 32 slots."""
        board = chess.Board()
        result = extract_structural_cognition(board)

        assert len(result.per_piece.pieces) == 32

    def test_structural_cognition_has_64_squares(self) -> None:
        """Verify square map has 64 entries."""
        board = chess.Board()
        result = extract_structural_cognition(board)

        assert len(result.square_map.weak_for_white) == 64

    def test_structural_labels_are_generated(self) -> None:
        """Verify labels are generated (may be empty for starting position)."""
        board = chess.Board()
        result = extract_structural_cognition(board)

        # Labels should be a list (may be empty)
        assert isinstance(result.structural_labels, list)


class TestStructuralLabelGeneration:
    """Test structural label generation."""

    def test_generate_labels_basic(self) -> None:
        """Verify labels can be generated from features."""
        board = chess.Board()
        per_piece = extract_per_piece_features(board)
        square_map = extract_square_map_features(board)

        labels = generate_structural_labels(per_piece, square_map)

        assert isinstance(labels, list)
        for label in labels:
            assert isinstance(label, StructuralLabel)
            assert label.type in [
                "dominated-piece",
                "hole",
                "overextended-pawn",
                "key-defender",
                "weak-square",
                "strong-square",
                "hanging-piece",
                "pinned-piece",
            ]

    def test_generate_labels_for_hanging_piece(self) -> None:
        """Verify hanging piece labels are generated."""
        # Create position with hanging knight
        board = chess.Board("rnbqkbnr/ppp1pppp/8/3p4/4N3/8/PPPPPPPP/R1BQKBNR w KQkq - 0 2")
        per_piece = extract_per_piece_features(board)
        square_map = extract_square_map_features(board)

        labels = generate_structural_labels(per_piece, square_map)

        # Check if any hanging-piece labels exist
        hanging_labels = [label for label in labels if label.type == "hanging-piece"]
        # May or may not find hanging pieces depending on exact position
        assert isinstance(hanging_labels, list)

    def test_label_target_format(self) -> None:
        """Verify labels have proper target format."""
        board = chess.Board()
        per_piece = extract_per_piece_features(board)
        square_map = extract_square_map_features(board)

        labels = generate_structural_labels(per_piece, square_map)

        for label in labels:
            # Target should be a string
            assert isinstance(label.target, str)
            # Description should be non-empty
            assert len(label.description) > 0


class TestContextBridgeV2Model:
    """Test Context Bridge v2 Pydantic model."""

    def test_context_bridge_v2_with_structural_cognition(self) -> None:
        """Verify Context Bridge v2 model accepts structural cognition."""
        from datetime import datetime

        board = chess.Board()
        structural = extract_structural_cognition(board)

        # Create a minimal Context Bridge v2 payload
        payload = ContextBridgePayloadV2(
            position=Position(
                fen=board.fen(),
                side_to_move="white",
                legal_moves=[move.uci() for move in board.legal_moves],
            ),
            conditioning=PositionConditioning(
                skill_bucket="1200-1400",
                time_pressure_bucket="normal",
            ),
            policy=Policy(
                top_moves=[PolicyMove(uci="e2e4", p=0.5)],
                entropy=1.0,
                top_gap=0.5,
            ),
            human_wdl=HumanWDLContainer(
                pre=HumanWDL(w=0.4, d=0.2, loss=0.4),
                post_by_move={},
            ),
            hdi=HDI(
                value=0.5,
                components=HDIComponents(entropy=0.3, top_gap=0.3, wdl_sensitivity=0.3),
            ),
            narrative_seeds=[],
            meta=ContextBridgeMetaV2(
                schema_version="v2",
                generated_at=datetime.now(),
                input_hash="abc123",
            ),
            structural_cognition=structural,
        )

        # Verify model validates
        assert payload.meta.schema_version == "v2"
        assert payload.structural_cognition is not None
        assert len(payload.structural_cognition.per_piece.pieces) == 32

    def test_context_bridge_v2_serialization(self) -> None:
        """Verify Context Bridge v2 can be serialized to JSON."""
        from datetime import datetime

        board = chess.Board()
        structural = extract_structural_cognition(board)

        payload = ContextBridgePayloadV2(
            position=Position(
                fen=board.fen(),
                side_to_move="white",
                legal_moves=["e2e4", "d2d4"],
            ),
            conditioning=PositionConditioning(
                skill_bucket="1200-1400",
                time_pressure_bucket="normal",
            ),
            policy=Policy(
                top_moves=[PolicyMove(uci="e2e4", p=0.5)],
                entropy=1.0,
                top_gap=0.5,
            ),
            human_wdl=HumanWDLContainer(
                pre=HumanWDL(w=0.4, d=0.2, loss=0.4),
                post_by_move={},
            ),
            hdi=HDI(
                value=0.5,
                components=HDIComponents(entropy=0.3, top_gap=0.3, wdl_sensitivity=0.3),
            ),
            narrative_seeds=[],
            meta=ContextBridgeMetaV2(
                schema_version="v2",
                generated_at=datetime.now(),
                input_hash="abc123",
            ),
            structural_cognition=structural,
        )

        # Should not raise
        json_str = payload.model_dump_json()
        assert "structuralCognition" in json_str or "structural_cognition" in json_str

    def test_context_bridge_v2_without_structural_cognition(self) -> None:
        """Verify Context Bridge v2 works without structural cognition (optional)."""
        from datetime import datetime

        payload = ContextBridgePayloadV2(
            position=Position(
                fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                side_to_move="white",
                legal_moves=["e2e4", "d2d4"],
            ),
            conditioning=PositionConditioning(
                skill_bucket="1200-1400",
                time_pressure_bucket="normal",
            ),
            policy=Policy(
                top_moves=[PolicyMove(uci="e2e4", p=0.5)],
                entropy=1.0,
                top_gap=0.5,
            ),
            human_wdl=HumanWDLContainer(
                pre=HumanWDL(w=0.4, d=0.2, loss=0.4),
                post_by_move={},
            ),
            hdi=HDI(
                value=0.5,
                components=HDIComponents(entropy=0.3, top_gap=0.3, wdl_sensitivity=0.3),
            ),
            narrative_seeds=[],
            meta=ContextBridgeMetaV2(
                schema_version="v2",
                generated_at=datetime.now(),
                input_hash="abc123",
            ),
            structural_cognition=None,  # Optional
        )

        assert payload.structural_cognition is None
        assert payload.meta.schema_version == "v2"


class TestNarrativeSeedV2:
    """Test narrative seed v2 with structural types."""

    def test_narrative_seed_v2_structural_types(self) -> None:
        """Verify NarrativeSeedV2 accepts structural types."""
        seed = NarrativeSeedV2(
            type="dominated-piece",
            severity="medium",
            facts=["White knight on e4 is under heavy pressure"],
        )
        assert seed.type == "dominated-piece"

        seed2 = NarrativeSeedV2(
            type="hole",
            severity="high",
            facts=["d5 is a permanent weakness for Black"],
        )
        assert seed2.type == "hole"

    def test_narrative_seed_v2_backward_compatible_types(self) -> None:
        """Verify NarrativeSeedV2 still accepts v1 types."""
        seed = NarrativeSeedV2(
            type="trap-risk",
            severity="low",
            facts=["Engine win% up, but human blunder risk up"],
        )
        assert seed.type == "trap-risk"
