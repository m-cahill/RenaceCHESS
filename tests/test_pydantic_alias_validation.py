"""Tests for Pydantic alias validation forward-compatibility."""

from renacechess.contracts.models import (
    HumanWDL,
    Position,
    PositionConditioning,
)


def test_position_accepts_both_alias_and_name():
    """Test that Position accepts both camelCase (alias) and snake_case (name)."""
    # Test with alias (camelCase)
    pos1 = Position(
        fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        sideToMove="white",
        legalMoves=["e2e4", "d2d4"],
    )
    assert pos1.side_to_move == "white"

    # Test with name (snake_case)
    pos2 = Position(
        fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        side_to_move="white",
        legal_moves=["e2e4", "d2d4"],
    )
    assert pos2.side_to_move == "white"

    # Both should be equivalent
    assert pos1.fen == pos2.fen
    assert pos1.side_to_move == pos2.side_to_move


def test_human_wdl_accepts_both_alias_and_name():
    """Test that HumanWDL accepts both alias and name for 'loss' field."""
    # Test with alias
    wdl1 = HumanWDL(w=0.5, d=0.3, l=0.2)
    assert wdl1.loss == 0.2

    # Test with name
    wdl2 = HumanWDL(w=0.5, d=0.3, loss=0.2)
    assert wdl2.loss == 0.2

    # Both should be equivalent
    assert wdl1.w == wdl2.w
    assert wdl1.d == wdl2.d
    assert wdl1.loss == wdl2.loss


def test_position_conditioning_accepts_both_alias_and_name():
    """Test that PositionConditioning accepts both alias and name."""
    # Test with alias
    cond1 = PositionConditioning(
        skillBucket="1200-1400",
        timePressureBucket="NORMAL",
        timeControlClass="blitz",
    )
    assert cond1.skill_bucket == "1200-1400"

    # Test with name
    cond2 = PositionConditioning(
        skill_bucket="1200-1400",
        time_pressure_bucket="NORMAL",
        time_control_class="blitz",
    )
    assert cond2.skill_bucket == "1200-1400"

    # Both should be equivalent
    assert cond1.skill_bucket == cond2.skill_bucket


def test_json_serialization_uses_aliases():
    """Test that JSON serialization uses camelCase aliases."""
    pos = Position(
        fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        side_to_move="white",
        legal_moves=["e2e4"],
    )

    # Serialize with aliases
    json_dict = pos.model_dump(mode="json", by_alias=True)
    assert "sideToMove" in json_dict
    assert "legalMoves" in json_dict
    assert "side_to_move" not in json_dict
    assert "legal_moves" not in json_dict

    # Serialize without aliases
    json_dict_no_alias = pos.model_dump(mode="json", by_alias=False)
    assert "side_to_move" in json_dict_no_alias
    assert "legal_moves" in json_dict_no_alias
    assert "sideToMove" not in json_dict_no_alias
    assert "legalMoves" not in json_dict_no_alias

