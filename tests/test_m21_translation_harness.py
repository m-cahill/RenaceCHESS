"""M21 Translation Harness Tests — Constraint-Driven, Not Prose Snapshots.

This test module validates the translation harness and evaluation pipeline.

Key test principles:
- Test CONSTRAINTS, not style
- Test DETERMINISM, not creativity
- Test FACT-GROUNDING, not prose quality
- No golden prose tests

See: COACHING_TRANSLATION_PROMPT_v1.md
"""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path

import pytest

from renacechess.coaching.evaluation import (
    FORBIDDEN_TERMS,
    _compute_fact_coverage,
    _count_sentences,
    _detect_forbidden_terms,
    _extract_percentages,
    _extract_uci_moves,
    evaluate_coaching_draft,
)
from renacechess.coaching.llm_client import (
    DeterministicStubLLM,
    LLMResponse,
    ToneProfile,
)
from renacechess.coaching.translation_harness import (
    translate_facts_to_coaching,
)
from renacechess.contracts.models import (
    AdviceFactsContextV1,
    AdviceFactsHDIV1,
    AdviceFactsMoveV1,
    AdviceFactsOutcomeV1,
    AdviceFactsPolicyV1,
    AdviceFactsPositionV1,
    AdviceFactsSourceContractsV1,
    AdviceFactsStructuralCognitionV1,
    AdviceFactsV1,
    CoachingDraftDeterminismMetadataV1,
    CoachingDraftV1,
    CoachingEvaluationV1,
    DifficultyDeltaV1,
    EloBucketDeltaFactsV1,
    EloBucketDeltaSourceContractsV1,
    OutcomeDeltaV1,
    PolicyDeltaV1,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def fixed_timestamp() -> datetime:
    """Fixed timestamp for determinism tests."""
    return datetime(2026, 2, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_advice_facts(fixed_timestamp: datetime) -> AdviceFactsV1:
    """Sample AdviceFactsV1 for testing."""
    return AdviceFactsV1(
        version="1.0",
        generated_at=fixed_timestamp,
        position=AdviceFactsPositionV1(
            fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1", side_to_move="black"
        ),
        context=AdviceFactsContextV1(
            skill_bucket="1200_1399", time_control_bucket="blitz", time_pressure_bucket="normal"
        ),
        policy=AdviceFactsPolicyV1(
            top_moves=[
                AdviceFactsMoveV1(uci="e7e5", san="e5", prob=0.35),
                AdviceFactsMoveV1(uci="c7c5", san="c5", prob=0.25),
                AdviceFactsMoveV1(uci="e7e6", san="e6", prob=0.15),
            ],
            recommended_move=AdviceFactsMoveV1(uci="e7e5", san="e5", prob=0.35),
        ),
        outcome=AdviceFactsOutcomeV1(p_win=0.45, p_draw=0.30, p_loss=0.25),
        hdi=AdviceFactsHDIV1(
            value=0.42,
            entropy=1.5,
            top_gap_inverted=0.3,
            legal_move_pressure=0.2,
            outcome_sensitivity=0.1,
        ),
        structural_cognition=AdviceFactsStructuralCognitionV1(
            mobility_delta=0.15, weak_squares_delta=-0.05, strong_squares_delta=0.0, summary=None
        ),
        explanation_hints=None,
        determinism_hash="sha256:" + "a" * 64,
        source_contract_versions=AdviceFactsSourceContractsV1(
            advice_facts_contract="v1",
            input_semantics_contract="v1.0",
            structural_cognition_contract="v1",
        ),
    )


@pytest.fixture
def sample_delta_facts(fixed_timestamp: datetime) -> EloBucketDeltaFactsV1:
    """Sample EloBucketDeltaFactsV1 for testing."""
    return EloBucketDeltaFactsV1(
        schema_version="elo_bucket_delta_facts.v1",
        generated_at=fixed_timestamp,
        baseline_bucket="1200_1399",
        comparison_bucket="1600_1799",
        source_advice_facts_hashes=["sha256:" + "a" * 64, "sha256:" + "b" * 64],
        policy_delta=PolicyDeltaV1(
            kl_divergence=0.25, total_variation=0.15, rank_flips=1, mass_shift_to_top=0.05
        ),
        outcome_delta=OutcomeDeltaV1(
            delta_p_win=0.10, delta_p_draw=-0.02, delta_p_loss=-0.08, win_rate_monotonic=True
        ),
        difficulty_delta=DifficultyDeltaV1(delta_hdi=-0.05),
        structural_delta=None,
        determinism_hash="sha256:" + "b" * 64,
        source_contract_versions=EloBucketDeltaSourceContractsV1(
            elo_bucket_delta_contract="v1", advice_facts_contract="v1"
        ),
    )


# =============================================================================
# LLM Client Tests
# =============================================================================


class TestDeterministicStubLLM:
    """Tests for DeterministicStubLLM."""

    def test_stub_returns_response(self, sample_advice_facts: AdviceFactsV1) -> None:
        """Stub returns a valid LLMResponse."""
        client = DeterministicStubLLM()
        response = client.translate_facts(
            advice_facts=sample_advice_facts,
            delta_facts=None,
            tone=ToneProfile.NEUTRAL,
            prompt_template_version="v1",
        )
        assert isinstance(response, LLMResponse)
        assert response.text
        assert response.model_id == "stub-v1"
        assert response.provider == "stub"
        assert response.temperature == 0.0

    def test_stub_is_deterministic(self, sample_advice_facts: AdviceFactsV1) -> None:
        """Same inputs produce identical outputs."""
        client = DeterministicStubLLM()
        response1 = client.translate_facts(
            advice_facts=sample_advice_facts,
            delta_facts=None,
            tone=ToneProfile.NEUTRAL,
            prompt_template_version="v1",
        )
        response2 = client.translate_facts(
            advice_facts=sample_advice_facts,
            delta_facts=None,
            tone=ToneProfile.NEUTRAL,
            prompt_template_version="v1",
        )
        assert response1.text == response2.text
        assert response1.prompt_hash == response2.prompt_hash

    def test_stub_varies_by_tone(self, sample_advice_facts: AdviceFactsV1) -> None:
        """Different tones produce different outputs."""
        client = DeterministicStubLLM()
        neutral = client.translate_facts(
            advice_facts=sample_advice_facts,
            delta_facts=None,
            tone=ToneProfile.NEUTRAL,
            prompt_template_version="v1",
        )
        encouraging = client.translate_facts(
            advice_facts=sample_advice_facts,
            delta_facts=None,
            tone=ToneProfile.ENCOURAGING,
            prompt_template_version="v1",
        )
        assert neutral.text != encouraging.text

    def test_stub_includes_delta_facts(
        self, sample_advice_facts: AdviceFactsV1, sample_delta_facts: EloBucketDeltaFactsV1
    ) -> None:
        """Stub response includes delta information when provided."""
        client = DeterministicStubLLM()
        response = client.translate_facts(
            advice_facts=sample_advice_facts,
            delta_facts=sample_delta_facts,
            tone=ToneProfile.NEUTRAL,
            prompt_template_version="v1",
        )
        # Should mention both bucket IDs
        assert sample_delta_facts.baseline_bucket in response.text
        assert sample_delta_facts.comparison_bucket in response.text

    def test_stub_references_moves_from_facts(self, sample_advice_facts: AdviceFactsV1) -> None:
        """Stub output references moves from the facts."""
        client = DeterministicStubLLM()
        response = client.translate_facts(
            advice_facts=sample_advice_facts,
            delta_facts=None,
            tone=ToneProfile.NEUTRAL,
            prompt_template_version="v1",
        )
        # Should mention at least the recommended move
        assert sample_advice_facts.policy.recommended_move.uci in response.text


# =============================================================================
# Translation Harness Tests
# =============================================================================


class TestTranslationHarness:
    """Tests for translation harness."""

    def test_produces_coaching_draft(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Translation produces a valid CoachingDraftV1."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        assert isinstance(draft, CoachingDraftV1)
        assert draft.schema_version == "coaching_draft.v1"
        assert draft.draft_text
        assert draft.skill_bucket == sample_advice_facts.context.skill_bucket

    def test_determinism_same_inputs_same_hash(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Same inputs produce identical determinism hash."""
        draft1 = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        draft2 = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        assert draft1.determinism_hash == draft2.determinism_hash
        assert draft1.draft_text == draft2.draft_text

    def test_records_source_hashes(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Draft records source fact hashes for lineage."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        assert draft.source_advice_facts_hash == sample_advice_facts.determinism_hash
        assert draft.source_delta_facts_hash is None

    def test_records_delta_hash_when_provided(
        self,
        sample_advice_facts: AdviceFactsV1,
        sample_delta_facts: EloBucketDeltaFactsV1,
        fixed_timestamp: datetime,
    ) -> None:
        """Draft records delta facts hash when provided."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            delta_facts=sample_delta_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        assert draft.source_delta_facts_hash == sample_delta_facts.determinism_hash

    def test_extracts_referenced_facts(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Draft includes referenced facts for traceability."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        assert len(draft.referenced_facts) > 0
        # Should include skill bucket, recommended move, win prob, HDI
        field_paths = [ref.field_path for ref in draft.referenced_facts]
        assert "context.skillBucket" in field_paths
        assert "policy.recommendedMove.uci" in field_paths

    def test_determinism_metadata_recorded(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Determinism metadata is recorded."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        meta = draft.determinism_metadata
        assert meta.model_id == "stub-v1"
        assert meta.provider == "stub"
        assert meta.temperature == 0.0
        assert meta.prompt_template_version == "v1"
        assert len(meta.prompt_hash) == 64  # SHA-256 hex

    def test_draft_validates_against_schema(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Draft can be serialized to JSON matching schema."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        # Pydantic model_dump should work without errors
        data = draft.model_dump(by_alias=True)
        assert data["schemaVersion"] == "coaching_draft.v1"
        assert data["draftText"]
        assert data["determinismHash"].startswith("sha256:")


# =============================================================================
# Evaluation Tests
# =============================================================================


class TestHallucinationDetection:
    """Tests for hallucination detection heuristics."""

    def test_detects_forbidden_terms(self) -> None:
        """Detects forbidden terms in text."""
        text = "The engine suggests this is the best move."
        found = _detect_forbidden_terms(text)
        assert "engine" in found

    def test_no_false_positives_on_clean_text(self) -> None:
        """No forbidden terms in clean text."""
        text = "This move is recommended for players at this level."
        found = _detect_forbidden_terms(text)
        assert len(found) == 0

    def test_detects_stockfish(self) -> None:
        """Detects Stockfish reference."""
        text = "Stockfish evaluates this as +0.5"
        found = _detect_forbidden_terms(text)
        assert "stockfish" in found

    def test_extracts_uci_moves(self) -> None:
        """Extracts UCI moves from text."""
        text = "Consider playing e2e4 or d2d4 in this position."
        moves = _extract_uci_moves(text)
        assert "e2e4" in moves
        assert "d2d4" in moves

    def test_extracts_percentages(self) -> None:
        """Extracts percentage values from text."""
        text = "Win probability is 45%, draw is 30%."
        pcts = _extract_percentages(text)
        assert 45 in pcts
        assert 30 in pcts


class TestEvaluationHarness:
    """Tests for coaching evaluation."""

    def test_evaluates_draft(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Evaluation produces valid artifact."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        evaluation = evaluate_coaching_draft(
            draft=draft,
            advice_facts=sample_advice_facts,
            evaluated_at=fixed_timestamp,
        )
        assert isinstance(evaluation, CoachingEvaluationV1)
        assert evaluation.schema_version == "coaching_evaluation.v1"

    def test_stub_output_passes_evaluation(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Stub output should pass evaluation (by design)."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        evaluation = evaluate_coaching_draft(
            draft=draft,
            advice_facts=sample_advice_facts,
            evaluated_at=fixed_timestamp,
        )
        # Stub should pass because it only references provided facts
        assert evaluation.passed is True
        assert len(evaluation.failure_reasons) == 0

    def test_detects_hallucinated_moves(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Detects moves not in source facts."""
        # Create a draft with a hallucinated move
        draft = CoachingDraftV1(
            schema_version="coaching_draft.v1",
            generated_at=fixed_timestamp,
            draft_text="The move a1a2 is best. Consider 1200_1399 level.",
            skill_bucket="1200_1399",
            tone_profile="neutral",
            referenced_facts=[],
            source_advice_facts_hash=sample_advice_facts.determinism_hash,
            source_delta_facts_hash=None,
            determinism_metadata=CoachingDraftDeterminismMetadataV1(
                prompt_template_version="v1",
                prompt_hash="a" * 64,
                model_id="test",
                temperature=0.0,
                provider="test",
            ),
            determinism_hash="sha256:" + "c" * 64,
        )
        evaluation = evaluate_coaching_draft(
            draft=draft,
            advice_facts=sample_advice_facts,
            evaluated_at=fixed_timestamp,
        )
        # Should detect a1a2 as unsupported
        assert "a1a2" in evaluation.hallucination_details.unsupported_moves

    def test_detects_forbidden_engine_terms(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Detects engine references."""
        draft = CoachingDraftV1(
            schema_version="coaching_draft.v1",
            generated_at=fixed_timestamp,
            draft_text="The engine says e7e5 is 1200_1399 level best.",
            skill_bucket="1200_1399",
            tone_profile="neutral",
            referenced_facts=[],
            source_advice_facts_hash=sample_advice_facts.determinism_hash,
            source_delta_facts_hash=None,
            determinism_metadata=CoachingDraftDeterminismMetadataV1(
                prompt_template_version="v1",
                prompt_hash="a" * 64,
                model_id="test",
                temperature=0.0,
                provider="test",
            ),
            determinism_hash="sha256:" + "d" * 64,
        )
        evaluation = evaluate_coaching_draft(
            draft=draft,
            advice_facts=sample_advice_facts,
            evaluated_at=fixed_timestamp,
        )
        assert "engine" in evaluation.hallucination_details.forbidden_terms_found

    def test_evaluation_determinism(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Same inputs produce identical evaluation hash."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        eval1 = evaluate_coaching_draft(
            draft=draft,
            advice_facts=sample_advice_facts,
            evaluated_at=fixed_timestamp,
        )
        eval2 = evaluate_coaching_draft(
            draft=draft,
            advice_facts=sample_advice_facts,
            evaluated_at=fixed_timestamp,
        )
        assert eval1.determinism_hash == eval2.determinism_hash

    def test_fact_coverage_metric(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Fact coverage is computed correctly."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        coverage = _compute_fact_coverage(draft, sample_advice_facts)
        # Stub should reference most facts
        assert coverage >= 0.5

    def test_evaluation_with_delta_facts(
        self,
        sample_advice_facts: AdviceFactsV1,
        sample_delta_facts: EloBucketDeltaFactsV1,
        fixed_timestamp: datetime,
    ) -> None:
        """Evaluation works with delta facts."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            delta_facts=sample_delta_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        evaluation = evaluate_coaching_draft(
            draft=draft,
            advice_facts=sample_advice_facts,
            delta_facts=sample_delta_facts,
            evaluated_at=fixed_timestamp,
        )
        assert evaluation.source_delta_facts_hash == sample_delta_facts.determinism_hash
        # Delta faithfulness should be high since stub mentions buckets
        assert evaluation.metrics.delta_faithfulness >= 0.5


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestSchemaValidation:
    """Tests for schema compliance."""

    def test_coaching_draft_validates(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """CoachingDraftV1 validates correctly."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        # Validate by reconstructing from dict
        data = draft.model_dump(by_alias=True)
        reconstructed = CoachingDraftV1(**data)
        assert reconstructed.determinism_hash == draft.determinism_hash

    def test_coaching_evaluation_validates(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """CoachingEvaluationV1 validates correctly."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        evaluation = evaluate_coaching_draft(
            draft=draft,
            advice_facts=sample_advice_facts,
            evaluated_at=fixed_timestamp,
        )
        # Validate by reconstructing from dict
        data = evaluation.model_dump(by_alias=True)
        reconstructed = CoachingEvaluationV1(**data)
        assert reconstructed.determinism_hash == evaluation.determinism_hash


# =============================================================================
# Import Boundary Guardrail Test (AST-Based)
# =============================================================================


class TestImportBoundary:
    """AST-based import boundary guardrail tests."""

    def test_translation_harness_imports_only_allowed_modules(self) -> None:
        """translation_harness.py imports only from allowed modules.

        Allowed:
        - renacechess.contracts.models
        - renacechess.coaching.*
        - stdlib
        """
        harness_path = Path("src/renacechess/coaching/translation_harness.py")
        source = harness_path.read_text()
        tree = ast.parse(source)

        allowed_prefixes = (
            "renacechess.contracts.models",
            "renacechess.coaching",
            # stdlib modules we use
            "datetime",
            "hashlib",
            "json",
            "typing",
            "__future__",
        )

        forbidden_prefixes = (
            "renacechess.models",
            "renacechess.eval",
            "renacechess.features",
            "renacechess.ingest",
            "renacechess.dataset",
            "renacechess.frozen_eval",
            "renacechess.personality",
        )

        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        # Check no forbidden imports
        for imp in imports:
            for forbidden in forbidden_prefixes:
                if imp.startswith(forbidden):
                    pytest.fail(f"translation_harness.py imports forbidden module: {imp}")

        # Verify at least one allowed import is present
        has_allowed = any(
            any(imp.startswith(allowed) for allowed in allowed_prefixes) for imp in imports
        )
        assert has_allowed, "translation_harness.py should import from allowed modules"

    def test_evaluation_imports_only_allowed_modules(self) -> None:
        """evaluation.py imports only from allowed modules."""
        eval_path = Path("src/renacechess/coaching/evaluation.py")
        source = eval_path.read_text()
        tree = ast.parse(source)

        forbidden_prefixes = (
            "renacechess.models",
            "renacechess.eval",
            "renacechess.features",
            "renacechess.ingest",
            "renacechess.dataset",
            "renacechess.frozen_eval",
            "renacechess.personality",
        )

        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        for imp in imports:
            for forbidden in forbidden_prefixes:
                if imp.startswith(forbidden):
                    pytest.fail(f"evaluation.py imports forbidden module: {imp}")


# =============================================================================
# Invariant Tests
# =============================================================================


class TestInvariants:
    """Tests for key invariants."""

    def test_forbidden_terms_set_is_non_empty(self) -> None:
        """Forbidden terms set must be populated."""
        assert len(FORBIDDEN_TERMS) >= 10, "FORBIDDEN_TERMS should have at least 10 terms"

    def test_draft_hash_format(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Draft hash uses correct format."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        assert draft.determinism_hash.startswith("sha256:")
        assert len(draft.determinism_hash) == 7 + 64  # "sha256:" + 64 hex chars

    def test_evaluation_hash_format(
        self, sample_advice_facts: AdviceFactsV1, fixed_timestamp: datetime
    ) -> None:
        """Evaluation hash uses correct format."""
        draft = translate_facts_to_coaching(
            advice_facts=sample_advice_facts,
            tone=ToneProfile.NEUTRAL,
            generated_at=fixed_timestamp,
        )
        evaluation = evaluate_coaching_draft(
            draft=draft,
            advice_facts=sample_advice_facts,
            evaluated_at=fixed_timestamp,
        )
        assert evaluation.determinism_hash.startswith("sha256:")
        assert len(evaluation.determinism_hash) == 7 + 64

    def test_tone_profile_enum_has_three_values(self) -> None:
        """ToneProfile enum has exactly 3 values (v1 requirement)."""
        assert len(ToneProfile) == 3
        assert ToneProfile.NEUTRAL.value == "neutral"
        assert ToneProfile.ENCOURAGING.value == "encouraging"
        assert ToneProfile.CONCISE.value == "concise"

    def test_count_sentences_handles_edge_cases(self) -> None:
        """Sentence counting handles edge cases."""
        assert _count_sentences("Hello.") == 1
        assert _count_sentences("Hello. World.") == 2
        assert _count_sentences("Hello! World? Yes.") == 3
        assert _count_sentences("") == 1  # Minimum 1
