"""Tests for contract schemas and models."""

import json
from datetime import datetime
from pathlib import Path

import jsonschema
import pytest

from renacechess.contracts.models import (
    HDI,
    ContextBridgePayload,
    DatasetManifest,
    HDIComponents,
    HumanWDL,
    HumanWDLContainer,
    NarrativeSeed,
    Policy,
    PolicyMove,
    Position,
    PositionConditioning,
)
from renacechess.determinism import canonical_json_dump


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


def test_policy_move_model() -> None:
    """Test PolicyMove model."""
    move = PolicyMove(uci="e2e4", p=0.5)
    assert move.uci == "e2e4"
    assert move.p == 0.5
    assert move.san is None

    move_with_san = PolicyMove(uci="e2e4", san="e4", p=0.5)
    assert move_with_san.san == "e4"


def test_policy_model() -> None:
    """Test Policy model."""
    moves = [
        PolicyMove(uci="e2e4", san=None, p=0.6),
        PolicyMove(uci="d2d4", san=None, p=0.4),
    ]
    policy = Policy(top_moves=moves, entropy=0.97, top_gap=0.2)
    assert len(policy.top_moves) == 2
    assert policy.entropy == 0.97
    assert policy.top_gap == 0.2


def test_human_wdl_model() -> None:
    """Test HumanWDL model validation."""
    wdl = HumanWDL(w=0.5, d=0.3, loss=0.2)
    assert wdl.w + wdl.d + wdl.loss == pytest.approx(1.0)

    # Should raise if probabilities don't sum to 1
    with pytest.raises(ValueError, match="must sum to 1"):
        HumanWDL(w=0.5, d=0.3, loss=0.1)


def test_human_wdl_container_model() -> None:
    """Test HumanWDLContainer model."""
    pre = HumanWDL(w=0.5, d=0.3, loss=0.2)
    post_by_move = {
        "e2e4": HumanWDL(w=0.6, d=0.2, loss=0.2),
        "d2d4": HumanWDL(w=0.4, d=0.3, loss=0.3),
    }
    container = HumanWDLContainer(pre=pre, post_by_move=post_by_move)
    assert container.pre == pre
    assert len(container.post_by_move) == 2


def test_context_bridge_payload_model_to_json() -> None:
    """Test that ContextBridgePayload can be serialized to canonical JSON."""
    from renacechess.contracts.models import ContextBridgeMeta

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
                "e7e6": HumanWDL(w=0.4, d=0.3, loss=0.3),
            },
        ),
        hdi=HDI(
            value=0.65,
            components=HDIComponents(entropy=0.97, top_gap=0.2, wdl_sensitivity=0.1),
        ),
        narrative_seeds=[
            NarrativeSeed(
                type="confusing",
                severity="medium",
                facts=["Top-3 moves have near-equal probability"],
            )
        ],
        meta=ContextBridgeMeta(
            schema_version="v1",
            generated_at=datetime(2024, 1, 1, 12, 0, 0),
            input_hash="abc123",
        ),
    )

    # Serialize to dict with aliases (camelCase JSON), excluding None values
    payload_dict = payload.model_dump(mode="json", by_alias=True, exclude_none=True)

    # Should be JSON-serializable
    json_bytes = canonical_json_dump(payload_dict)
    assert json_bytes is not None

    # Validate against schema
    schema = load_schema("context_bridge")
    jsonschema.validate(payload_dict, schema)


def test_context_bridge_payload_schema_version() -> None:
    """Test that schema version is v1."""
    from renacechess.contracts.models import ContextBridgeMeta

    meta = ContextBridgeMeta(
        schema_version="v1",
        generated_at=datetime.now(),
        input_hash="test",
    )
    assert meta.schema_version == "v1"


def test_dataset_manifest_model() -> None:
    """Test DatasetManifest model."""
    from renacechess.contracts.models import (
        DatasetManifestSplitAssignments,
    )

    manifest = DatasetManifest(
        schema_version="v1",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        shard_refs=[],
        filter_config_hash="config123",
        split_assignments=DatasetManifestSplitAssignments(),
    )

    assert manifest.schema_version == "v1"
    assert len(manifest.shard_refs) == 0
    assert manifest.filter_config_hash == "config123"


def test_dataset_manifest_schema_validation() -> None:
    """Test that DatasetManifest validates against schema."""
    from renacechess.contracts.models import DatasetManifestSplitAssignments

    manifest = DatasetManifest(
        schemaVersion="v1",
        createdAt=datetime(2024, 1, 1, 12, 0, 0),
        shardRefs=[],
        filterConfigHash="config123",
        splitAssignments=DatasetManifestSplitAssignments(),
    )

    manifest_dict = manifest.model_dump(mode="json", by_alias=True)
    schema = load_schema("dataset_manifest")
    jsonschema.validate(manifest_dict, schema)
