"""Tests for AdviceFacts contract, schema, and determinism (M19).

These tests verify:
1. Schema validation (JSON Schema + Pydantic)
2. Determinism (same inputs → identical outputs)
3. Canonical ordering (moves sorted by prob desc, then UCI asc)
4. Float precision (6 decimal places)
5. Contract boundary compliance (dict inputs use aliases per CONTRACT_INPUT_SEMANTICS)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import jsonschema
import pytest

from renacechess.coaching.advice_facts import (
    TOP_K,
    _canonical_json,
    _round_float,
    _sort_moves,
    build_advice_facts_v1,
)
from renacechess.contracts.models import (
    AdviceFactsHDIV1,
    AdviceFactsInputsV1,
    AdviceFactsMoveV1,
    AdviceFactsOutcomeV1,
    AdviceFactsV1,
)

# Schema path
SCHEMA_PATH = (
    Path(__file__).parent.parent
    / "src/renacechess/contracts/schemas/v1/advice_facts.v1.schema.json"
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def minimal_inputs() -> AdviceFactsInputsV1:
    """Minimal valid inputs for AdviceFacts builder."""
    return AdviceFactsInputsV1(
        fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
        sideToMove="black",
        skillBucket="1200_1399",
        topMoves=[("e7e5", 0.35), ("c7c5", 0.28), ("e7e6", 0.15), ("d7d5", 0.12), ("g8f6", 0.05)],
        pWin=0.45,
        pDraw=0.30,
        pLoss=0.25,
        hdiValue=0.42,
    )


@pytest.fixture
def inputs_with_structural() -> AdviceFactsInputsV1:
    """Inputs with structural cognition data."""
    return AdviceFactsInputsV1(
        fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
        sideToMove="black",
        skillBucket="1200_1399",
        topMoves=[("e7e5", 0.35), ("c7c5", 0.28)],
        pWin=0.45,
        pDraw=0.30,
        pLoss=0.25,
        hdiValue=0.42,
        hdiEntropy=0.65,
        hdiTopGapInverted=0.38,
        hdiLegalMovePressure=0.22,
        hdiOutcomeSensitivity=0.18,
        mobilityDelta=2.5,
        weakSquaresDelta=-1.0,
        strongSquaresDelta=0.5,
        structuralSummary="Improved piece mobility after e5",
    )


@pytest.fixture
def fixed_timestamp() -> datetime:
    """Fixed timestamp for determinism tests."""
    return datetime(2026, 1, 31, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def advice_facts_schema() -> dict:
    """Load the AdviceFacts JSON Schema."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestSchemaValidation:
    """Tests for JSON Schema and Pydantic model validation."""

    def test_schema_file_exists(self) -> None:
        """Schema file exists at expected path."""
        assert SCHEMA_PATH.exists(), f"Schema not found at {SCHEMA_PATH}"

    def test_schema_is_valid_json(self, advice_facts_schema: dict) -> None:
        """Schema is valid JSON."""
        assert "$schema" in advice_facts_schema
        assert advice_facts_schema["title"] == "AdviceFactsV1"

    def test_minimal_artifact_validates(
        self,
        minimal_inputs: AdviceFactsInputsV1,
        fixed_timestamp: datetime,
        advice_facts_schema: dict,
    ) -> None:
        """Minimal artifact validates against JSON Schema."""
        facts = build_advice_facts_v1(minimal_inputs, generated_at=fixed_timestamp)

        # Convert to dict with aliases, excluding None values
        # (JSON Schema optional fields should be absent, not null)
        artifact_dict = json.loads(facts.model_dump_json(by_alias=True, exclude_none=True))

        # Validate against schema
        jsonschema.validate(artifact_dict, advice_facts_schema)

    def test_artifact_with_structural_validates(
        self,
        inputs_with_structural: AdviceFactsInputsV1,
        fixed_timestamp: datetime,
        advice_facts_schema: dict,
    ) -> None:
        """Artifact with structural cognition validates."""
        facts = build_advice_facts_v1(inputs_with_structural, generated_at=fixed_timestamp)
        # Exclude None values for schema validation
        artifact_dict = json.loads(facts.model_dump_json(by_alias=True, exclude_none=True))
        jsonschema.validate(artifact_dict, advice_facts_schema)

    def test_pydantic_model_roundtrip(
        self,
        minimal_inputs: AdviceFactsInputsV1,
        fixed_timestamp: datetime,
    ) -> None:
        """Pydantic model can serialize and deserialize."""
        facts = build_advice_facts_v1(minimal_inputs, generated_at=fixed_timestamp)

        # Serialize to JSON
        json_str = facts.model_dump_json(by_alias=True)

        # Deserialize back
        reconstructed = AdviceFactsV1.model_validate_json(json_str)

        # Verify key fields match
        assert reconstructed.version == facts.version
        assert reconstructed.position.fen == facts.position.fen
        assert reconstructed.determinism_hash == facts.determinism_hash


# =============================================================================
# Determinism Tests
# =============================================================================


class TestDeterminism:
    """Tests for deterministic artifact generation."""

    def test_same_inputs_same_output(
        self,
        minimal_inputs: AdviceFactsInputsV1,
        fixed_timestamp: datetime,
    ) -> None:
        """Same inputs produce identical outputs."""
        facts1 = build_advice_facts_v1(minimal_inputs, generated_at=fixed_timestamp)
        facts2 = build_advice_facts_v1(minimal_inputs, generated_at=fixed_timestamp)

        # Same hash
        assert facts1.determinism_hash == facts2.determinism_hash

        # Same JSON output
        json1 = facts1.model_dump_json(by_alias=True, exclude_none=True)
        json2 = facts2.model_dump_json(by_alias=True, exclude_none=True)
        assert json1 == json2

    def test_different_timestamp_different_hash(
        self,
        minimal_inputs: AdviceFactsInputsV1,
    ) -> None:
        """Different timestamps produce different hashes."""
        ts1 = datetime(2026, 1, 31, 12, 0, 0, tzinfo=UTC)
        ts2 = datetime(2026, 1, 31, 12, 0, 1, tzinfo=UTC)

        facts1 = build_advice_facts_v1(minimal_inputs, generated_at=ts1)
        facts2 = build_advice_facts_v1(minimal_inputs, generated_at=ts2)

        assert facts1.determinism_hash != facts2.determinism_hash

    def test_hash_format(
        self,
        minimal_inputs: AdviceFactsInputsV1,
        fixed_timestamp: datetime,
    ) -> None:
        """Hash is in expected format: sha256:<64-hex>."""
        facts = build_advice_facts_v1(minimal_inputs, generated_at=fixed_timestamp)

        assert facts.determinism_hash.startswith("sha256:")
        hex_part = facts.determinism_hash[7:]
        assert len(hex_part) == 64
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_float_precision_determinism(self) -> None:
        """Float rounding is deterministic."""
        # Values that might have floating-point representation issues
        values = [0.1, 0.2, 0.3, 1 / 3, 0.123456789]

        for val in values:
            rounded1 = _round_float(val)
            rounded2 = _round_float(val)
            assert rounded1 == rounded2, f"Non-deterministic rounding for {val}"

    def test_canonical_json_ordering(self) -> None:
        """Canonical JSON has sorted keys."""
        obj = {"zebra": 1, "alpha": 2, "beta": 3}
        canonical = _canonical_json(obj)

        # Keys should be in alphabetical order
        assert canonical == '{"alpha":2,"beta":3,"zebra":1}'


# =============================================================================
# Move Ordering Tests
# =============================================================================


class TestMoveOrdering:
    """Tests for canonical move ordering."""

    def test_sort_by_probability_descending(self) -> None:
        """Moves are sorted by probability descending."""
        moves = [("a2a3", 0.1), ("e2e4", 0.5), ("d2d4", 0.3)]
        sorted_moves = _sort_moves(moves)

        probs = [m[1] for m in sorted_moves]
        assert probs == sorted(probs, reverse=True)

    def test_sort_by_uci_for_ties(self) -> None:
        """Ties are broken by UCI ascending."""
        moves = [("e2e4", 0.25), ("d2d4", 0.25), ("c2c4", 0.25)]
        sorted_moves = _sort_moves(moves)

        # Same prob, so should be sorted by UCI
        ucis = [m[0] for m in sorted_moves]
        assert ucis == ["c2c4", "d2d4", "e2e4"]

    def test_sort_with_san(self) -> None:
        """SAN is preserved during sort."""
        moves = [("e2e4", 0.5), ("d2d4", 0.3)]
        sans = ["e4", "d4"]
        sorted_moves = _sort_moves(moves, sans)

        # e2e4 should be first (higher prob) with its SAN
        assert sorted_moves[0] == ("e2e4", 0.5, "e4")
        assert sorted_moves[1] == ("d2d4", 0.3, "d4")

    def test_top_k_limit(
        self,
        fixed_timestamp: datetime,
    ) -> None:
        """Builder limits to TOP_K moves."""
        many_moves = [(f"a{i}a{i + 1}", 0.1 - i * 0.01) for i in range(1, 8)]
        inputs = AdviceFactsInputsV1(
            fen="8/8/8/8/8/8/8/8 w - - 0 1",
            sideToMove="white",
            skillBucket="1200_1399",
            topMoves=many_moves,
            pWin=0.33,
            pDraw=0.34,
            pLoss=0.33,
            hdiValue=0.5,
        )

        facts = build_advice_facts_v1(inputs, generated_at=fixed_timestamp)

        assert len(facts.policy.top_moves) == TOP_K


# =============================================================================
# Float Precision Tests
# =============================================================================


class TestFloatPrecision:
    """Tests for float rounding and precision."""

    def test_round_float_precision(self) -> None:
        """Float rounding uses correct precision."""
        assert _round_float(0.123456789) == 0.123457
        assert _round_float(0.999999999) == 1.0
        assert _round_float(0.0000001) == 0.0

    def test_probabilities_rounded_in_artifact(
        self,
        fixed_timestamp: datetime,
    ) -> None:
        """Probabilities in artifact are rounded."""
        inputs = AdviceFactsInputsV1(
            fen="8/8/8/8/8/8/8/8 w - - 0 1",
            sideToMove="white",
            skillBucket="1200_1399",
            topMoves=[("e2e4", 0.123456789)],
            pWin=0.333333333,
            pDraw=0.333333333,
            pLoss=0.333333334,
            hdiValue=0.123456789,
        )

        facts = build_advice_facts_v1(inputs, generated_at=fixed_timestamp)

        # Check rounding
        assert facts.policy.top_moves[0].prob == 0.123457
        assert facts.hdi.value == 0.123457


# =============================================================================
# Contract Input Semantics Tests
# =============================================================================


class TestContractInputSemantics:
    """Tests for CONTRACT_INPUT_SEMANTICS v1 compliance."""

    def test_inputs_use_alias_keys(self) -> None:
        """AdviceFactsInputsV1 accepts alias (camelCase) keys per contract."""
        # Per CONTRACT_INPUT_SEMANTICS v1: dict inputs use camelCase aliases
        data = {
            "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
            "sideToMove": "white",  # alias
            "skillBucket": "1200_1399",  # alias
            "topMoves": [("e2e4", 0.5)],  # alias
            "pWin": 0.33,  # alias
            "pDraw": 0.34,  # alias
            "pLoss": 0.33,  # alias
            "hdiValue": 0.5,  # alias
        }

        inputs = AdviceFactsInputsV1.model_validate(data)
        assert inputs.side_to_move == "white"
        assert inputs.skill_bucket == "1200_1399"

    def test_output_serializes_with_aliases(
        self,
        minimal_inputs: AdviceFactsInputsV1,
        fixed_timestamp: datetime,
    ) -> None:
        """AdviceFactsV1 output uses camelCase aliases."""
        facts = build_advice_facts_v1(minimal_inputs, generated_at=fixed_timestamp)
        output = facts.model_dump(by_alias=True)

        # Check key aliases
        assert "sideToMove" in output["position"]
        assert "skillBucket" in output["context"]
        assert "topMoves" in output["policy"]
        assert "recommendedMove" in output["policy"]
        assert "pWin" in output["outcome"]
        assert "determinismHash" in output


# =============================================================================
# Structural Cognition Tests
# =============================================================================


class TestStructuralCognition:
    """Tests for optional structural cognition handling."""

    def test_structural_cognition_absent_when_no_inputs(
        self,
        minimal_inputs: AdviceFactsInputsV1,
        fixed_timestamp: datetime,
    ) -> None:
        """Structural cognition is None when not provided."""
        facts = build_advice_facts_v1(minimal_inputs, generated_at=fixed_timestamp)
        assert facts.structural_cognition is None

    def test_structural_cognition_present_when_provided(
        self,
        inputs_with_structural: AdviceFactsInputsV1,
        fixed_timestamp: datetime,
    ) -> None:
        """Structural cognition is populated when provided."""
        facts = build_advice_facts_v1(inputs_with_structural, generated_at=fixed_timestamp)

        assert facts.structural_cognition is not None
        assert facts.structural_cognition.mobility_delta == 2.5
        assert facts.structural_cognition.weak_squares_delta == -1.0
        assert facts.structural_cognition.strong_squares_delta == 0.5
        assert facts.structural_cognition.summary == "Improved piece mobility after e5"

    def test_source_contract_includes_structural(
        self,
        inputs_with_structural: AdviceFactsInputsV1,
        fixed_timestamp: datetime,
    ) -> None:
        """Source contracts include structural when present."""
        facts = build_advice_facts_v1(inputs_with_structural, generated_at=fixed_timestamp)

        assert facts.source_contract_versions.structural_cognition_contract == "v1"

    def test_source_contract_excludes_structural_when_absent(
        self,
        minimal_inputs: AdviceFactsInputsV1,
        fixed_timestamp: datetime,
    ) -> None:
        """Source contracts exclude structural when absent."""
        facts = build_advice_facts_v1(minimal_inputs, generated_at=fixed_timestamp)

        assert facts.source_contract_versions.structural_cognition_contract is None


# =============================================================================
# Pydantic Model Tests
# =============================================================================


class TestPydanticModels:
    """Tests for Pydantic model validation."""

    def test_outcome_probabilities_must_sum_to_one(self) -> None:
        """Outcome probabilities must sum to approximately 1.0."""
        with pytest.raises(ValueError, match="sum to 1.0"):
            AdviceFactsOutcomeV1(pWin=0.5, pDraw=0.5, pLoss=0.5)  # Sum = 1.5

    def test_outcome_probabilities_valid(self) -> None:
        """Valid outcome probabilities pass validation."""
        outcome = AdviceFactsOutcomeV1(pWin=0.4, pDraw=0.35, pLoss=0.25)
        assert outcome.p_win == 0.4
        assert outcome.p_draw == 0.35
        assert outcome.p_loss == 0.25

    def test_move_probability_bounds(self) -> None:
        """Move probability must be in [0, 1]."""
        with pytest.raises(ValueError):
            AdviceFactsMoveV1(uci="e2e4", prob=1.5)

        with pytest.raises(ValueError):
            AdviceFactsMoveV1(uci="e2e4", prob=-0.1)

    def test_hdi_value_bounds(self) -> None:
        """HDI value must be in [0, 1]."""
        with pytest.raises(ValueError):
            AdviceFactsHDIV1(value=1.5)

        with pytest.raises(ValueError):
            AdviceFactsHDIV1(value=-0.1)


# =============================================================================
# Explanation Hints Placeholder Tests
# =============================================================================


class TestExplanationHints:
    """Tests for explanation hints placeholder (M20+ feature)."""

    def test_explanation_hints_not_populated(
        self,
        minimal_inputs: AdviceFactsInputsV1,
        fixed_timestamp: datetime,
    ) -> None:
        """Explanation hints are not populated in M19."""
        facts = build_advice_facts_v1(minimal_inputs, generated_at=fixed_timestamp)
        assert facts.explanation_hints is None
