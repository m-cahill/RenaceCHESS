"""Tests for chosenMove field in Context Bridge payload (M05)."""

import json
from datetime import datetime
from pathlib import Path

import jsonschema

from renacechess.contracts.models import (
    HDI,
    ChosenMove,
    ContextBridgeMeta,
    ContextBridgePayload,
    HDIComponents,
    HumanWDL,
    HumanWDLContainer,
    Policy,
    PolicyMove,
    Position,
    PositionConditioning,
)


def load_schema(schema_name: str) -> dict:
    """Load JSON schema from schemas directory."""
    schema_path = (
        Path(__file__).parent.parent
        / "src"
        / "renacechess"
        / "contracts"
        / "schemas"
        / "v1"
        / f"{schema_name}.schema.json"
    )
    return json.loads(schema_path.read_text())


def test_chosen_move_model() -> None:
    """Test ChosenMove model."""
    move = ChosenMove(uci="e2e4")
    assert move.uci == "e2e4"
    assert move.san is None

    move_with_san = ChosenMove(uci="e2e4", san="e4")
    assert move_with_san.uci == "e2e4"
    assert move_with_san.san == "e4"


def test_context_bridge_payload_with_chosen_move() -> None:
    """Test ContextBridgePayload with chosenMove field."""
    payload = ContextBridgePayload(
        position=Position(
            fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
            side_to_move="black",
            legal_moves=["e7e6", "e7e5"],
        ),
        conditioning=PositionConditioning(
            skill_bucket="1200-1400",
            time_pressure_bucket="NORMAL",
        ),
        policy=Policy(
            top_moves=[
                PolicyMove(uci="e7e5", san=None, p=0.6),
                PolicyMove(uci="e7e6", san=None, p=0.4),
            ],
            entropy=0.97,
            top_gap=0.2,
        ),
        human_wdl=HumanWDLContainer(
            pre=HumanWDL(w=0.5, d=0.3, loss=0.2),
            post_by_move={
                "e7e5": HumanWDL(w=0.6, d=0.2, loss=0.2),
            },
        ),
        hdi=HDI(
            value=0.65,
            components=HDIComponents(entropy=0.97, top_gap=0.2, wdl_sensitivity=0.1),
        ),
        narrative_seeds=[],
        meta=ContextBridgeMeta(
            schema_version="v1",
            generated_at=datetime(2024, 1, 1, 12, 0, 0),
            input_hash="abc123",
        ),
        chosen_move=ChosenMove(uci="e7e5", san="e5"),
    )

    assert payload.chosen_move is not None
    assert payload.chosen_move.uci == "e7e5"
    assert payload.chosen_move.san == "e5"

    # Serialize to dict
    payload_dict = payload.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert "chosenMove" in payload_dict
    assert payload_dict["chosenMove"]["uci"] == "e7e5"
    assert payload_dict["chosenMove"]["san"] == "e5"

    # Validate against schema
    schema = load_schema("context_bridge")
    jsonschema.validate(payload_dict, schema)


def test_context_bridge_payload_without_chosen_move() -> None:
    """Test ContextBridgePayload without chosenMove (backward compatibility)."""
    payload = ContextBridgePayload(
        position=Position(
            fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
            side_to_move="black",
            legal_moves=["e7e6", "e7e5"],
        ),
        conditioning=PositionConditioning(
            skill_bucket="1200-1400",
            time_pressure_bucket="NORMAL",
        ),
        policy=Policy(
            top_moves=[
                PolicyMove(uci="e7e5", san=None, p=0.6),
            ],
            entropy=0.97,
            top_gap=0.2,
        ),
        human_wdl=HumanWDLContainer(
            pre=HumanWDL(w=0.5, d=0.3, loss=0.2),
            post_by_move={},
        ),
        hdi=HDI(
            value=0.65,
            components=HDIComponents(entropy=0.97, top_gap=0.2, wdl_sensitivity=0.1),
        ),
        narrative_seeds=[],
        meta=ContextBridgeMeta(
            schema_version="v1",
            generated_at=datetime(2024, 1, 1, 12, 0, 0),
            input_hash="abc123",
        ),
        chosen_move=None,
    )

    assert payload.chosen_move is None

    # Serialize to dict (chosenMove should be excluded when None)
    payload_dict = payload.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert "chosenMove" not in payload_dict

    # Validate against schema (should still work)
    schema = load_schema("context_bridge")
    jsonschema.validate(payload_dict, schema)


def test_chosen_move_schema_optional() -> None:
    """Test that chosenMove is optional in schema."""
    schema = load_schema("context_bridge")

    # Payload without chosenMove should validate
    payload_dict = {
        "position": {
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "sideToMove": "white",
            "legalMoves": ["e2e4"],
        },
        "conditioning": {
            "skillBucket": "1200-1400",
            "timePressureBucket": "NORMAL",
        },
        "policy": {
            "topMoves": [{"uci": "e2e4", "p": 1.0}],
            "entropy": 0.0,
            "topGap": 1.0,
        },
        "humanWDL": {
            "pre": {"w": 0.5, "d": 0.3, "l": 0.2},
            "postByMove": {},
        },
        "hdi": {
            "value": 0.5,
            "components": {"entropy": 0.0, "topGap": 1.0, "wdlSensitivity": 0.0},
        },
        "narrativeSeeds": [],
        "meta": {
            "schemaVersion": "v1",
            "generatedAt": "2024-01-01T12:00:00",
            "inputHash": "test",
        },
    }

    # Should validate (chosenMove is optional)
    jsonschema.validate(payload_dict, schema)

    # Payload with chosenMove should also validate
    payload_dict["chosenMove"] = {"uci": "e2e4", "san": "e4"}
    jsonschema.validate(payload_dict, schema)

    # chosenMove with only UCI (no SAN) should validate
    payload_dict["chosenMove"] = {"uci": "e2e4"}
    jsonschema.validate(payload_dict, schema)

