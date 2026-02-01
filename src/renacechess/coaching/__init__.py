"""Coaching module for RenaceCHESS (Phase C).

This module provides grounded, facts-only artifacts for LLM coaching translation.
See ADR-COACHING-001 for the governing principle: "LLMs translate facts, not invent."

M19: AdviceFacts — facts-only coaching substrate
M20: EloBucketDeltaFacts — cross-bucket comparison
M21: Translation harness + evaluation — LLM as pure translator
"""

from renacechess.coaching.advice_facts import build_advice_facts_v1
from renacechess.coaching.elo_bucket_deltas import build_elo_bucket_delta_facts_v1
from renacechess.coaching.evaluation import evaluate_coaching_draft
from renacechess.coaching.llm_client import (
    DeterministicStubLLM,
    LLMClient,
    LLMResponse,
    ToneProfile,
)
from renacechess.coaching.translation_harness import translate_facts_to_coaching

__all__ = [
    "build_advice_facts_v1",
    "build_elo_bucket_delta_facts_v1",
    # M21 exports
    "translate_facts_to_coaching",
    "evaluate_coaching_draft",
    "LLMClient",
    "DeterministicStubLLM",
    "LLMResponse",
    "ToneProfile",
]
