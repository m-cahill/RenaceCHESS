"""LLM client abstraction for coaching translation (M21).

This module provides an abstract interface for LLM translation and a deterministic
stub implementation for CI/testing. The stub ensures reproducible, non-flaky tests.

Key invariants:
- DeterministicStubLLM: same inputs → identical outputs (hash-stable)
- No network calls in CI path
- All responses are template-based, not generated

See: COACHING_TRANSLATION_PROMPT_v1.md
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from renacechess.contracts.models import AdviceFactsV1, EloBucketDeltaFactsV1


class ToneProfile(str, Enum):
    """Fixed tone profiles for v1 (non-extensible)."""

    NEUTRAL = "neutral"
    ENCOURAGING = "encouraging"
    CONCISE = "concise"


@dataclass(frozen=True)
class LLMResponse:
    """Response from LLM client.

    Attributes:
        text: Generated prose text
        model_id: Model identifier (e.g., "stub-v1", "gpt-4")
        prompt_hash: SHA-256 hash of the prompt sent
        temperature: Temperature setting used (0 for deterministic)
        provider: Provider name (e.g., "stub", "openai")
    """

    text: str
    model_id: str
    prompt_hash: str
    temperature: float
    provider: str


class LLMClient(ABC):
    """Abstract LLM client protocol for coaching translation.

    Implementations must:
    - Accept only facts from AdviceFactsV1 and EloBucketDeltaFactsV1
    - Return a structured LLMResponse with metadata
    - Record prompt hash for audit trail
    """

    @abstractmethod
    def translate_facts(
        self,
        advice_facts: AdviceFactsV1,
        delta_facts: EloBucketDeltaFactsV1 | None,
        tone: ToneProfile,
        prompt_template_version: str,
    ) -> LLMResponse:
        """Translate facts into coaching prose.

        Args:
            advice_facts: Pre-computed facts for the position
            delta_facts: Optional cross-bucket delta facts
            tone: Tone profile for output
            prompt_template_version: Version of prompt template being used

        Returns:
            LLMResponse with generated text and metadata
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name for metadata."""
        ...

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return model identifier for metadata."""
        ...


def _compute_prompt_hash(prompt: str) -> str:
    """Compute SHA-256 hash of prompt for audit trail."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


class DeterministicStubLLM(LLMClient):
    """Deterministic stub LLM for CI and testing.

    This stub produces template-based responses that are fully reproducible.
    Same inputs always produce identical outputs.

    The stub does NOT call any external API - it generates responses locally
    based on the input facts using a simple template system.
    """

    STUB_MODEL_ID = "stub-v1"
    STUB_PROVIDER = "stub"

    def __init__(self) -> None:
        """Initialize the stub LLM."""
        self._temperature = 0.0

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return self.STUB_PROVIDER

    @property
    def model_id(self) -> str:
        """Return model identifier."""
        return self.STUB_MODEL_ID

    def translate_facts(
        self,
        advice_facts: AdviceFactsV1,
        delta_facts: EloBucketDeltaFactsV1 | None,
        tone: ToneProfile,
        prompt_template_version: str,
    ) -> LLMResponse:
        """Generate deterministic coaching prose from facts.

        This stub creates template-based text that:
        - References only the provided facts
        - Uses no chess knowledge beyond what's in the facts
        - Is fully deterministic (same inputs → same output)
        """
        # Build the prompt that would be sent to a real LLM
        prompt = self._build_prompt(advice_facts, delta_facts, tone, prompt_template_version)
        prompt_hash = _compute_prompt_hash(prompt)

        # Generate deterministic response based on facts
        text = self._generate_stub_response(advice_facts, delta_facts, tone)

        return LLMResponse(
            text=text,
            model_id=self.STUB_MODEL_ID,
            prompt_hash=prompt_hash,
            temperature=self._temperature,
            provider=self.STUB_PROVIDER,
        )

    def _build_prompt(
        self,
        advice_facts: AdviceFactsV1,
        delta_facts: EloBucketDeltaFactsV1 | None,
        tone: ToneProfile,
        prompt_template_version: str,
    ) -> str:
        """Build the prompt that would be sent to an LLM.

        This constructs the full prompt string for hashing purposes.
        The stub doesn't actually send this anywhere.
        """
        parts = [
            f"PROMPT_VERSION: {prompt_template_version}",
            f"TONE: {tone.value}",
            f"SKILL_BUCKET: {advice_facts.context.skill_bucket}",
            f"FEN: {advice_facts.position.fen}",
            f"RECOMMENDED_MOVE: {advice_facts.policy.recommended_move.uci}",
            f"WIN_PROB: {advice_facts.outcome.p_win:.2f}",
            f"HDI: {advice_facts.hdi.value:.2f}",
        ]

        if delta_facts:
            parts.extend(
                [
                    f"DELTA_BASELINE: {delta_facts.baseline_bucket}",
                    f"DELTA_COMPARISON: {delta_facts.comparison_bucket}",
                    f"KL_DIVERGENCE: {delta_facts.policy_delta.kl_divergence:.4f}",
                ]
            )

        return "\n".join(parts)

    def _generate_stub_response(
        self,
        advice_facts: AdviceFactsV1,
        delta_facts: EloBucketDeltaFactsV1 | None,
        tone: ToneProfile,
    ) -> str:
        """Generate deterministic stub response based on facts only.

        The response:
        - References only values from the input facts
        - Uses controlled vocabulary matching structural facts
        - Varies slightly by tone profile
        """
        skill_bucket = advice_facts.context.skill_bucket
        recommended = advice_facts.policy.recommended_move
        win_prob_pct = round(advice_facts.outcome.p_win * 100)
        hdi_value = advice_facts.hdi.value

        # Build move list from facts only
        move_list = ", ".join(
            f"{m.uci} ({round(m.prob * 100)}%)" for m in advice_facts.policy.top_moves[:3]
        )

        # Difficulty description based on HDI value
        if hdi_value >= 0.7:
            difficulty = "challenging"
        elif hdi_value >= 0.4:
            difficulty = "moderate"
        else:
            difficulty = "straightforward"

        # Base response structure
        base_parts = [
            (
                f"In this position, players at the {skill_bucket} level "
                f"typically consider: {move_list}."
            ),
            f"The recommended move is {recommended.uci}.",
            (
                f"From this skill level's perspective, "
                f"the win probability is approximately {win_prob_pct}%."
            ),
            f"This position is {difficulty} (HDI: {hdi_value:.2f}).",
        ]

        # Add delta information if present
        if delta_facts:
            delta_win = round(delta_facts.outcome_delta.delta_p_win * 100)
            baseline = delta_facts.baseline_bucket
            comparison = delta_facts.comparison_bucket

            if delta_win > 0:
                delta_text = (
                    f"Compared to {baseline} players, {comparison} players "
                    f"have a {abs(delta_win)}% higher win rate in this position."
                )
            elif delta_win < 0:
                delta_text = (
                    f"Compared to {baseline} players, {comparison} players "
                    f"have a {abs(delta_win)}% lower win rate in this position."
                )
            else:
                delta_text = f"The win rate is similar between {baseline} and {comparison} players."
            base_parts.append(delta_text)

        # Add structural cognition if present
        struct = advice_facts.structural_cognition
        if struct and struct.mobility_delta is not None:
            if struct.mobility_delta > 0:
                base_parts.append("This move increases mobility.")
            elif struct.mobility_delta < 0:
                base_parts.append("This move reduces mobility.")

        # Apply tone modifications
        if tone == ToneProfile.ENCOURAGING:
            base_parts.insert(0, "Great position to consider!")
            base_parts.append("Keep analyzing positions like this to improve.")
        elif tone == ToneProfile.CONCISE:
            # Keep only essential parts for concise tone
            base_parts = base_parts[:3]

        return " ".join(base_parts)
