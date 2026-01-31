"""Personality Evaluation Harness (M18).

This module provides a deterministic, offline evaluation harness for measuring
bounded behavioral divergence between personality modules and the Neutral Baseline.

Key capabilities:
- Compute divergence metrics (KL divergence, Total Variation, Jensen-Shannon)
- Measure envelope utilization (delta_p_max usage, top_k binding)
- Generate structured JSON evaluation artifacts
- Support synthetic fixtures for testing

This harness does NOT integrate with the live eval runner. It is designed for
offline measurement and scientific comparison of personality effects.

See docs/personality/M18_PERSONALITY_EVAL_HARNESS.md for documentation.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from renacechess.contracts.models import (
    ComponentStatsV1,
    DivergenceMetricsV1,
    EnvelopeUtilizationV1,
    PersonalityEvalArtifactV1,
    Policy,
    PolicyStatsV1,
    SafetyEnvelopeV1,
    StructuralAttributionV1,
)

if TYPE_CHECKING:
    from renacechess.personality.interfaces import PersonalityModuleV1, StructuralContext


def compute_kl_divergence(p: dict[str, float], q: dict[str, float]) -> float:
    """Compute KL divergence D_KL(P || Q) in bits.

    Args:
        p: Distribution P (personality output).
        q: Distribution Q (baseline).

    Returns:
        KL divergence in bits. Returns 0.0 if distributions are identical.

    Note:
        Uses base-2 logarithm for bits. Handles zero probabilities with epsilon.
    """
    epsilon = 1e-10
    kl = 0.0

    for move, p_prob in p.items():
        q_prob = q.get(move, epsilon)
        if p_prob > epsilon:
            kl += p_prob * math.log2(p_prob / max(q_prob, epsilon))

    return max(0.0, kl)


def compute_total_variation(p: dict[str, float], q: dict[str, float]) -> float:
    """Compute Total Variation distance between distributions.

    Args:
        p: Distribution P (personality output).
        q: Distribution Q (baseline).

    Returns:
        Total Variation distance in [0.0, 1.0].
    """
    all_moves = set(p.keys()) | set(q.keys())
    tv = sum(abs(p.get(move, 0.0) - q.get(move, 0.0)) for move in all_moves) / 2.0
    return min(1.0, max(0.0, tv))


def compute_jensen_shannon(p: dict[str, float], q: dict[str, float]) -> float:
    """Compute Jensen-Shannon divergence between distributions.

    Args:
        p: Distribution P (personality output).
        q: Distribution Q (baseline).

    Returns:
        Jensen-Shannon divergence in [0.0, 1.0].
    """
    # Compute midpoint distribution M = (P + Q) / 2
    all_moves = set(p.keys()) | set(q.keys())
    m: dict[str, float] = {}
    for move in all_moves:
        m[move] = (p.get(move, 0.0) + q.get(move, 0.0)) / 2.0

    # JS = (KL(P||M) + KL(Q||M)) / 2
    kl_pm = compute_kl_divergence(p, m)
    kl_qm = compute_kl_divergence(q, m)
    js = (kl_pm + kl_qm) / 2.0

    # Normalize to [0, 1] (JS is bounded by log2(2) = 1 for base-2)
    return min(1.0, max(0.0, js))


def compute_entropy(policy: Policy) -> float:
    """Compute Shannon entropy of a policy distribution.

    Args:
        policy: Policy distribution.

    Returns:
        Shannon entropy in bits.
    """
    entropy = 0.0
    for move in policy.top_moves:
        if move.p > 0:
            entropy -= move.p * math.log2(move.p)
    return entropy


def policy_to_dist(policy: Policy) -> dict[str, float]:
    """Convert Policy to a dictionary distribution.

    Args:
        policy: Policy object.

    Returns:
        Dictionary mapping UCI move to probability.
    """
    return {move.uci: move.p for move in policy.top_moves}


def compute_determinism_hash(
    personality_id: str,
    baseline_id: str,
    config_hash: str,
    fixture_id: str | None,
    base_policy: Policy,
    output_policy: Policy,
) -> str:
    """Compute determinism hash for artifact verification.

    Args:
        personality_id: Personality being evaluated.
        baseline_id: Baseline personality ID.
        config_hash: Configuration hash.
        fixture_id: Fixture identifier.
        base_policy: Base policy input.
        output_policy: Output policy.

    Returns:
        SHA-256 hash of canonical JSON representation.
    """
    data = {
        "personalityId": personality_id,
        "baselineId": baseline_id,
        "configHash": config_hash,
        "fixtureId": fixture_id,
        "basePolicy": [{"uci": m.uci, "p": m.p} for m in base_policy.top_moves],
        "outputPolicy": [{"uci": m.uci, "p": m.p} for m in output_policy.top_moves],
    }
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def compute_config_hash(constraints: SafetyEnvelopeV1, **personality_params: float) -> str:
    """Compute configuration hash for traceability.

    Args:
        constraints: Safety envelope constraints.
        **personality_params: Additional personality parameters.

    Returns:
        SHA-256 hash of canonical JSON configuration.
    """
    config = {
        "constraints": {
            "topK": constraints.top_k,
            "deltaPMax": constraints.delta_p_max,
            "entropyMin": constraints.entropy_min,
            "entropyMax": constraints.entropy_max,
            "baseReachable": constraints.base_reachable,
        },
        "personalityParams": personality_params,
    }
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


class PersonalityEvalHarness:
    """Offline evaluation harness for personality modules.

    This harness evaluates a personality module against the Neutral Baseline
    and produces structured evaluation artifacts.

    Usage:
        harness = PersonalityEvalHarness(personality, baseline)
        artifact = harness.evaluate(base_policy, context, constraints)
    """

    def __init__(
        self,
        personality: PersonalityModuleV1,
        baseline: PersonalityModuleV1,
    ) -> None:
        """Initialize evaluation harness.

        Args:
            personality: Personality module to evaluate.
            baseline: Baseline personality for comparison (typically Neutral Baseline).
        """
        self._personality = personality
        self._baseline = baseline

    @property
    def personality_id(self) -> str:
        """Get personality ID."""
        return self._personality.personality_id

    @property
    def baseline_id(self) -> str:
        """Get baseline ID."""
        return self._baseline.personality_id

    def evaluate(
        self,
        base_policy: Policy,
        context: StructuralContext,
        constraints: SafetyEnvelopeV1,
        fixture_id: str | None = None,
        created_at: datetime | None = None,
        **personality_params: float,
    ) -> PersonalityEvalArtifactV1:
        """Evaluate personality and produce evaluation artifact.

        Args:
            base_policy: Base policy distribution.
            context: Structural context (M11 features).
            constraints: Safety envelope constraints.
            fixture_id: Identifier for the fixture (for traceability).
            created_at: Timestamp (for determinism tests, defaults to now).
            **personality_params: Additional personality parameters for config hash.

        Returns:
            PersonalityEvalArtifactV1 with complete metrics.
        """
        # Apply both personality and baseline
        personality_output = self._personality.apply(base_policy, context, constraints)
        baseline_output = self._baseline.apply(base_policy, context, constraints)

        # Convert to distributions for metric computation
        p_dist = policy_to_dist(personality_output)
        q_dist = policy_to_dist(baseline_output)

        # Compute divergence metrics
        divergence_metrics = self._compute_divergence_metrics(p_dist, q_dist)

        # Compute envelope utilization
        envelope_utilization = self._compute_envelope_utilization(
            base_policy, personality_output, constraints
        )

        # Compute policy stats
        policy_stats = self._compute_policy_stats(base_policy, personality_output)

        # Compute structural attribution (if context available)
        structural_attribution = self._compute_structural_attribution(
            base_policy, personality_output, context
        )

        # Compute hashes
        config_hash = compute_config_hash(constraints, **personality_params)
        determinism_hash = compute_determinism_hash(
            self.personality_id,
            self.baseline_id,
            config_hash,
            fixture_id,
            base_policy,
            personality_output,
        )

        return PersonalityEvalArtifactV1(
            schema_version="personality_eval_artifact.v1",
            created_at=created_at or datetime.now(UTC),
            personality_id=self.personality_id,
            baseline_id=self.baseline_id,
            config_hash=config_hash,
            determinism_hash=determinism_hash,
            fixture_id=fixture_id,
            divergence_metrics=divergence_metrics,
            envelope_utilization=envelope_utilization,
            structural_attribution=structural_attribution,
            policy_stats=policy_stats,
        )

    def _compute_divergence_metrics(
        self, p_dist: dict[str, float], q_dist: dict[str, float]
    ) -> DivergenceMetricsV1:
        """Compute divergence metrics between distributions.

        Args:
            p_dist: Personality output distribution.
            q_dist: Baseline distribution.

        Returns:
            DivergenceMetricsV1 with all divergence metrics.
        """
        # Compute probability deltas
        all_moves = set(p_dist.keys()) | set(q_dist.keys())
        deltas = [abs(p_dist.get(m, 0.0) - q_dist.get(m, 0.0)) for m in all_moves]
        max_delta = max(deltas) if deltas else 0.0
        mean_delta = sum(deltas) / len(deltas) if deltas else 0.0

        return DivergenceMetricsV1(
            kl_divergence=compute_kl_divergence(p_dist, q_dist),
            total_variation=compute_total_variation(p_dist, q_dist),
            jensen_shannon=compute_jensen_shannon(p_dist, q_dist),
            max_probability_delta=max_delta,
            mean_probability_delta=mean_delta,
        )

    def _compute_envelope_utilization(
        self,
        base_policy: Policy,
        output_policy: Policy,
        constraints: SafetyEnvelopeV1,
    ) -> EnvelopeUtilizationV1:
        """Compute envelope utilization statistics.

        Args:
            base_policy: Original base policy.
            output_policy: Personality output policy.
            constraints: Safety envelope constraints.

        Returns:
            EnvelopeUtilizationV1 with utilization statistics.
        """
        # Map base policy to dict for comparison
        base_dist = policy_to_dist(base_policy)
        output_dist = policy_to_dist(output_policy)

        # Compute max delta used
        all_moves = set(base_dist.keys()) | set(output_dist.keys())
        max_delta_used = 0.0
        for move in all_moves:
            base_p = base_dist.get(move, 0.0)
            output_p = output_dist.get(move, 0.0)
            delta = abs(output_p - base_p)
            max_delta_used = max(max_delta_used, delta)

        # Compute utilization percentage
        delta_p_max_used_pct = (
            (max_delta_used / constraints.delta_p_max * 100.0)
            if constraints.delta_p_max > 0
            else 0.0
        )

        # Check if top_k was binding
        moves_considered = len(output_policy.top_moves)
        top_k_binding = len(base_policy.top_moves) > constraints.top_k

        # Compute output entropy
        output_entropy = compute_entropy(output_policy)

        # Check entropy bounds
        entropy_in_bounds = constraints.entropy_min <= output_entropy <= constraints.entropy_max

        return EnvelopeUtilizationV1(
            delta_p_max_used_pct=min(100.0, delta_p_max_used_pct),
            delta_p_max_used_abs=min(constraints.delta_p_max, max_delta_used),
            delta_p_max_limit=constraints.delta_p_max,
            top_k_binding=top_k_binding,
            top_k_limit=constraints.top_k,
            moves_considered=moves_considered,
            entropy_in_bounds=entropy_in_bounds,
            output_entropy=output_entropy,
        )

    def _compute_policy_stats(self, base_policy: Policy, output_policy: Policy) -> PolicyStatsV1:
        """Compute policy distribution statistics.

        Args:
            base_policy: Original base policy.
            output_policy: Personality output policy.

        Returns:
            PolicyStatsV1 with distribution statistics.
        """
        base_entropy = compute_entropy(base_policy)
        output_entropy = compute_entropy(output_policy)

        return PolicyStatsV1(
            base_entropy=base_entropy,
            output_entropy=output_entropy,
            entropy_delta=output_entropy - base_entropy,
            move_count=len(output_policy.top_moves),
            base_top_gap=base_policy.top_gap,
            output_top_gap=output_policy.top_gap,
        )

    def _compute_structural_attribution(
        self,
        base_policy: Policy,
        output_policy: Policy,
        context: StructuralContext,
    ) -> StructuralAttributionV1 | None:
        """Compute structural attribution of divergence.

        This provides simple numeric attribution (not full statistical correlation).

        Args:
            base_policy: Original base policy.
            output_policy: Personality output policy.
            context: Structural context with M11 features.

        Returns:
            StructuralAttributionV1 if context available, None otherwise.
        """
        # If no structural context, return None
        if context.per_piece is None and context.square_map is None:
            return None

        # Compute style score components from context
        style_score_components: dict[str, ComponentStatsV1] = {}
        feature_deltas: dict[str, ComponentStatsV1] = {}

        # Per-piece features attribution
        if context.per_piece is not None:
            mobility_values = []
            tension_values = []
            for piece in context.per_piece.pieces:
                if piece.alive:
                    mobility_values.append(float(piece.mobility_legal))
                    tension_values.append(float(piece.net_defense))

            if mobility_values:
                style_score_components["mobility"] = ComponentStatsV1(
                    mean=sum(mobility_values) / len(mobility_values),
                    min=min(mobility_values),
                    max=max(mobility_values),
                )

            if tension_values:
                style_score_components["tension"] = ComponentStatsV1(
                    mean=sum(tension_values) / len(tension_values),
                    min=min(tension_values),
                    max=max(tension_values),
                )

        # Square map features attribution
        if context.square_map is not None:
            weak_count = sum(1 for b in context.square_map.weak_for_white if b)
            weak_count += sum(1 for b in context.square_map.weak_for_black if b)
            hole_count = sum(1 for b in context.square_map.is_hole_for_white if b)
            hole_count += sum(1 for b in context.square_map.is_hole_for_black if b)

            style_score_components["weakSquares"] = ComponentStatsV1(
                mean=float(weak_count), min=0.0, max=float(weak_count)
            )
            style_score_components["holes"] = ComponentStatsV1(
                mean=float(hole_count), min=0.0, max=float(hole_count)
            )

        # Compute feature deltas (probability changes per move)
        base_dist = policy_to_dist(base_policy)
        output_dist = policy_to_dist(output_policy)
        deltas = [output_dist.get(m, 0.0) - base_dist.get(m, 0.0) for m in base_dist.keys()]

        if deltas:
            feature_deltas["probabilityDelta"] = ComponentStatsV1(
                mean=sum(deltas) / len(deltas),
                min=min(deltas),
                max=max(deltas),
            )

        # Compute correlation proxy (simplified: normalized dot product)
        # This is a proxy for correlation without full statistical computation
        correlation_proxy = None
        if deltas and style_score_components:
            # Use mean mobility as proxy for style tendency
            if "mobility" in style_score_components:
                # Normalize delta by its magnitude
                delta_norm = math.sqrt(sum(d * d for d in deltas))
                if delta_norm > 1e-10:
                    # Simple proxy: sign of mean delta * style score presence
                    mean_delta = sum(deltas) / len(deltas)
                    correlation_proxy = mean_delta / delta_norm

        return StructuralAttributionV1(
            style_score_components=style_score_components if style_score_components else None,
            feature_deltas=feature_deltas if feature_deltas else None,
            correlation_proxy=correlation_proxy,
        )


def save_artifact(
    artifact: PersonalityEvalArtifactV1,
    output_path: Path,
) -> None:
    """Save evaluation artifact to JSON file.

    Args:
        artifact: Evaluation artifact to save.
        output_path: Path to output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(artifact.model_dump(by_alias=True), f, indent=2, default=str)


def load_artifact(input_path: Path) -> PersonalityEvalArtifactV1:
    """Load evaluation artifact from JSON file.

    Args:
        input_path: Path to input file.

    Returns:
        Loaded PersonalityEvalArtifactV1 artifact.
    """
    with open(input_path) as f:
        data = json.load(f)
    return PersonalityEvalArtifactV1.model_validate(data)
