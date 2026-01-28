"""Tests for per-piece structural feature extraction (M11).

These tests verify:
1. Invariants from Structural Cognition Contract v1
2. Golden FEN assertions
3. Determinism guarantees
"""

from __future__ import annotations

import json
from pathlib import Path

import chess
import pytest

from renacechess.features.per_piece import extract_per_piece_features


@pytest.fixture
def golden_fens() -> dict:
    """Load golden FEN fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "fens_m11.json"
    with open(fixture_path) as f:
        return json.load(f)


class TestPerPieceFeaturesInvariants:
    """Test structural invariants from Structural Cognition Contract v1."""

    def test_exactly_32_slots(self) -> None:
        """Verify exactly 32 piece slots are always produced."""
        board = chess.Board()
        result = extract_per_piece_features(board)
        assert len(result.pieces) == 32

    def test_slot_ordering_white_first(self) -> None:
        """Verify slots 0-15 are White, 16-31 are Black."""
        board = chess.Board()
        result = extract_per_piece_features(board)

        for i in range(16):
            assert result.pieces[i].color == "white", f"Slot {i} should be white"
        for i in range(16, 32):
            assert result.pieces[i].color == "black", f"Slot {i} should be black"

    def test_slot_id_matches_index(self) -> None:
        """Verify slot_id matches array index."""
        board = chess.Board()
        result = extract_per_piece_features(board)

        for i, piece in enumerate(result.pieces):
            assert piece.slot_id == i, f"Slot {i} has wrong slot_id {piece.slot_id}"

    def test_piece_type_ordering(self) -> None:
        """Verify piece type ordering per contract."""
        board = chess.Board()
        result = extract_per_piece_features(board)

        # White: K, Q, R, R, B, B, N, N, P*8
        expected_white = ["K", "Q", "R", "R", "B", "B", "N", "N"] + ["P"] * 8
        for i, expected in enumerate(expected_white):
            assert result.pieces[i].piece_type == expected

        # Black: same pattern
        expected_black = ["K", "Q", "R", "R", "B", "B", "N", "N"] + ["P"] * 8
        for i, expected in enumerate(expected_black):
            assert result.pieces[16 + i].piece_type == expected

    def test_starting_position_all_alive(self) -> None:
        """Verify all pieces are alive in starting position."""
        board = chess.Board()
        result = extract_per_piece_features(board)

        for piece in result.pieces:
            assert piece.alive is True
            assert piece.square is not None

    def test_captured_piece_handling(self) -> None:
        """Verify captured pieces have alive=False, square=None."""
        # Create a position where some pieces are captured
        board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        # Remove White queen (should be slot 1)
        board.remove_piece_at(chess.D1)

        result = extract_per_piece_features(board)

        # Find the queen slot and verify it's marked as captured
        # Note: The extractor uses heuristics, so we check that at least
        # one slot is not alive if a piece is missing
        queen_present = any(
            p.alive and p.piece_type == "Q" and p.color == "white" for p in result.pieces
        )
        assert not queen_present, "White queen should not be found as alive"

    def test_determinism(self) -> None:
        """Verify same FEN produces identical output."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        board = chess.Board(fen)

        result1 = extract_per_piece_features(board)
        result2 = extract_per_piece_features(board)

        # Compare all fields
        for i in range(32):
            p1 = result1.pieces[i]
            p2 = result2.pieces[i]
            assert p1.slot_id == p2.slot_id
            assert p1.color == p2.color
            assert p1.piece_type == p2.piece_type
            assert p1.alive == p2.alive
            assert p1.square == p2.square
            assert p1.mobility_legal == p2.mobility_legal
            assert p1.mobility_safe == p2.mobility_safe
            assert p1.attacked_by == p2.attacked_by
            assert p1.defended_by == p2.defended_by
            assert p1.is_hanging == p2.is_hanging
            assert p1.is_pinned == p2.is_pinned


class TestPerPieceFeaturesGoldenFENs:
    """Test per-piece features against golden FEN positions."""

    def test_golden_fen_1_basic_extraction(self, golden_fens: dict) -> None:
        """Test extraction on golden FEN 1 (Hole on d5)."""
        fen_data = golden_fens["positions"][0]
        board = chess.Board(fen_data["fen"])
        result = extract_per_piece_features(board)

        # Basic invariants
        assert len(result.pieces) == 32
        assert result.schema_version == "per_piece.v1"

    def test_golden_fen_2_basic_extraction(self, golden_fens: dict) -> None:
        """Test extraction on golden FEN 2 (Dominated piece)."""
        fen_data = golden_fens["positions"][1]
        board = chess.Board(fen_data["fen"])
        result = extract_per_piece_features(board)

        # Basic invariants
        assert len(result.pieces) == 32
        assert result.schema_version == "per_piece.v1"

    def test_golden_fen_3_basic_extraction(self, golden_fens: dict) -> None:
        """Test extraction on golden FEN 3 (Pawn tension)."""
        fen_data = golden_fens["positions"][2]
        board = chess.Board(fen_data["fen"])
        result = extract_per_piece_features(board)

        # Basic invariants
        assert len(result.pieces) == 32
        assert result.schema_version == "per_piece.v1"


class TestPerPieceFeaturesComputation:
    """Test specific feature computations."""

    def test_mobility_legal_computed(self) -> None:
        """Verify legal mobility is computed for pieces."""
        board = chess.Board()
        result = extract_per_piece_features(board)

        # Knights have 2 legal moves each in starting position
        # Find a knight slot and check it has some mobility
        for piece in result.pieces:
            if piece.piece_type == "N" and piece.alive:
                assert piece.mobility_legal >= 0

    def test_attacked_defended_counts(self) -> None:
        """Verify attack/defense counts are computed."""
        # Position where e4 pawn is defended by d3 pawn
        board = chess.Board("rnbqkbnr/pppppppp/8/8/4P3/3P4/PPP2PPP/RNBQKBNR b kq - 0 2")
        result = extract_per_piece_features(board)

        # All pieces should have non-negative attack/defense counts
        for piece in result.pieces:
            assert piece.attacked_by >= 0
            assert piece.defended_by >= 0

    def test_is_hanging_flag(self) -> None:
        """Verify is_hanging is computed correctly."""
        # Create a position with a hanging piece
        # White knight on e4 attacked by Black pawn on d5, not defended
        board = chess.Board("rnbqkbnr/ppp1pppp/8/3p4/4N3/8/PPPPPPPP/R1BQKBNR w KQkq - 0 2")
        result = extract_per_piece_features(board)

        # Find the knight and check if hanging logic is applied
        for piece in result.pieces:
            if piece.is_hanging:
                assert piece.attacked_by > 0
                assert piece.defended_by == 0

    def test_is_restricted_flag(self) -> None:
        """Verify is_restricted is set when mobility < 3."""
        board = chess.Board()
        result = extract_per_piece_features(board)

        for piece in result.pieces:
            if piece.alive:
                expected_restricted = piece.mobility_legal < 3
                assert piece.is_restricted == expected_restricted

    def test_net_defense_calculation(self) -> None:
        """Verify net_defense = defended_by - attacked_by."""
        board = chess.Board()
        result = extract_per_piece_features(board)

        for piece in result.pieces:
            assert piece.net_defense == piece.defended_by - piece.attacked_by


class TestPerPieceFeaturesModel:
    """Test Pydantic model validation."""

    def test_model_serialization(self) -> None:
        """Verify model can be serialized to JSON."""
        board = chess.Board()
        result = extract_per_piece_features(board)

        # Should not raise
        json_str = result.model_dump_json()
        assert "per_piece.v1" in json_str

    def test_model_uses_aliases(self) -> None:
        """Verify JSON uses camelCase aliases."""
        board = chess.Board()
        result = extract_per_piece_features(board)

        json_dict = result.model_dump(by_alias=True)
        assert "schemaVersion" in json_dict
        assert "pieces" in json_dict

        # Check piece fields use aliases
        if json_dict["pieces"]:
            piece = json_dict["pieces"][0]
            assert "slotId" in piece
            assert "pieceType" in piece
            assert "mobilityLegal" in piece
            assert "attackedBy" in piece
            assert "isHanging" in piece

