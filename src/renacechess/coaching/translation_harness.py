"""Translation harness for LLM coaching (M21).

This module transforms facts into coaching prose via an LLM client.
The harness enforces the translation-only paradigm: LLMs are renderers, not thinkers.

Key invariants:
- Accepts ONLY AdviceFactsV1 and optionally EloBucketDeltaFactsV1
- Performs NO chess computation or fact enrichment
- Produces deterministic CoachingDraftV1 artifacts (with stub LLM)

See: COACHING_TRANSLATION_PROMPT_v1.md, ADR-COACHING-001
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from renacechess.coaching.llm_client import DeterministicStubLLM, LLMClient, ToneProfile
from renacechess.contracts.models import (
    CoachingDraftDeterminismMetadataV1,
    CoachingDraftReferencedFactV1,
    CoachingDraftV1,
)

if TYPE_CHECKING:
    from renacechess.contracts.models import AdviceFactsV1, EloBucketDeltaFactsV1

# Contract version
TRANSLATION_PROMPT_VERSION = "v1"


def _canonical_json(obj: dict[str, object]) -> str:
    """Produce canonical JSON with sorted keys for determinism."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _compute_determinism_hash(data: dict[str, object]) -> str:
    """Compute SHA-256 hash of canonical JSON."""
    canonical = _canonical_json(data)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _extract_referenced_facts(
    advice_facts: AdviceFactsV1,
    delta_facts: EloBucketDeltaFactsV1 | None,
) -> list[CoachingDraftReferencedFactV1]:
    """Extract a list of salient facts that should be referenced.

    This provides the baseline for fact coverage scoring in evaluation.
    """
    refs: list[CoachingDraftReferencedFactV1] = []

    # Position context
    refs.append(
        CoachingDraftReferencedFactV1(
            source_artifact="advice_facts",
            field_path="context.skillBucket",
            value_summary=advice_facts.context.skill_bucket,
        )
    )

    # Recommended move
    rec = advice_facts.policy.recommended_move
    refs.append(
        CoachingDraftReferencedFactV1(
            source_artifact="advice_facts",
            field_path="policy.recommendedMove.uci",
            value_summary=rec.uci,
        )
    )

    # Top moves (up to 3)
    for i, move in enumerate(advice_facts.policy.top_moves[:3]):
        refs.append(
            CoachingDraftReferencedFactV1(
                source_artifact="advice_facts",
                field_path=f"policy.topMoves[{i}].uci",
                value_summary=f"{move.uci} ({round(move.prob * 100)}%)",
            )
        )

    # Win probability
    refs.append(
        CoachingDraftReferencedFactV1(
            source_artifact="advice_facts",
            field_path="outcome.pWin",
            value_summary=f"{round(advice_facts.outcome.p_win * 100)}%",
        )
    )

    # HDI value
    refs.append(
        CoachingDraftReferencedFactV1(
            source_artifact="advice_facts",
            field_path="hdi.value",
            value_summary=f"{advice_facts.hdi.value:.2f}",
        )
    )

    # Structural cognition if present
    if advice_facts.structural_cognition:
        struct = advice_facts.structural_cognition
        if struct.mobility_delta is not None:
            refs.append(
                CoachingDraftReferencedFactV1(
                    source_artifact="advice_facts",
                    field_path="structuralCognition.mobilityDelta",
                    value_summary=f"{struct.mobility_delta:+.2f}",
                )
            )

    # Delta facts if present
    if delta_facts:
        refs.append(
            CoachingDraftReferencedFactV1(
                source_artifact="delta_facts",
                field_path="baselineBucket",
                value_summary=delta_facts.baseline_bucket,
            )
        )
        refs.append(
            CoachingDraftReferencedFactV1(
                source_artifact="delta_facts",
                field_path="comparisonBucket",
                value_summary=delta_facts.comparison_bucket,
            )
        )
        refs.append(
            CoachingDraftReferencedFactV1(
                source_artifact="delta_facts",
                field_path="outcomeDelta.deltaPWin",
                value_summary=f"{round(delta_facts.outcome_delta.delta_p_win * 100):+d}%",
            )
        )

    return refs


def translate_facts_to_coaching(
    advice_facts: AdviceFactsV1,
    delta_facts: EloBucketDeltaFactsV1 | None = None,
    tone: ToneProfile = ToneProfile.NEUTRAL,
    llm_client: LLMClient | None = None,
    generated_at: datetime | None = None,
) -> CoachingDraftV1:
    """Translate facts into coaching prose via LLM.

    This is the main entry point for the translation harness.

    Args:
        advice_facts: Pre-computed facts for the position (required)
        delta_facts: Optional cross-bucket delta facts
        tone: Tone profile for output (default: NEUTRAL)
        llm_client: LLM client to use (default: DeterministicStubLLM)
        generated_at: Override timestamp (for determinism tests)

    Returns:
        CoachingDraftV1 artifact with generated prose and metadata

    The harness:
    - Accepts only facts from M19/M20 artifacts
    - Calls the LLM client for translation
    - Records all metadata for audit trail
    - Produces a deterministic artifact (with stub LLM)
    """
    # Use provided timestamp or current UTC
    timestamp = generated_at or datetime.now(UTC)

    # Use provided client or default to stub
    client = llm_client or DeterministicStubLLM()

    # Call LLM for translation
    response = client.translate_facts(
        advice_facts=advice_facts,
        delta_facts=delta_facts,
        tone=tone,
        prompt_template_version=TRANSLATION_PROMPT_VERSION,
    )

    # Build determinism metadata
    determinism_metadata = CoachingDraftDeterminismMetadataV1(
        prompt_template_version=TRANSLATION_PROMPT_VERSION,
        prompt_hash=response.prompt_hash,
        model_id=response.model_id,
        temperature=response.temperature,
        provider=response.provider,
    )

    # Extract referenced facts for traceability
    referenced_facts = _extract_referenced_facts(advice_facts, delta_facts)

    # Build artifact data for hashing (without hash field)
    artifact_data: dict[str, object] = {
        "schemaVersion": "coaching_draft.v1",
        "generatedAt": timestamp.isoformat(),
        "draftText": response.text,
        "skillBucket": advice_facts.context.skill_bucket,
        "toneProfile": tone.value,
        "referencedFacts": [
            {
                "sourceArtifact": ref.source_artifact,
                "fieldPath": ref.field_path,
                "valueSummary": ref.value_summary,
            }
            for ref in referenced_facts
        ],
        "sourceAdviceFactsHash": advice_facts.determinism_hash,
        "sourceDeltaFactsHash": delta_facts.determinism_hash if delta_facts else None,
        "determinismMetadata": {
            "promptTemplateVersion": determinism_metadata.prompt_template_version,
            "promptHash": determinism_metadata.prompt_hash,
            "modelId": determinism_metadata.model_id,
            "temperature": determinism_metadata.temperature,
            "provider": determinism_metadata.provider,
        },
    }

    # Compute determinism hash
    determinism_hash = _compute_determinism_hash(artifact_data)

    # Build final artifact
    return CoachingDraftV1(
        schema_version="coaching_draft.v1",
        generated_at=timestamp,
        draft_text=response.text,
        skill_bucket=advice_facts.context.skill_bucket,
        tone_profile=tone.value,
        referenced_facts=referenced_facts,
        source_advice_facts_hash=advice_facts.determinism_hash,
        source_delta_facts_hash=delta_facts.determinism_hash if delta_facts else None,
        determinism_metadata=determinism_metadata,
        determinism_hash=determinism_hash,
    )
