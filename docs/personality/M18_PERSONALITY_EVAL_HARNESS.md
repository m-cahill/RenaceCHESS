# M18: Personality Evaluation Harness

## Overview

The Personality Evaluation Harness is a **deterministic, offline evaluation system** for measuring bounded behavioral divergence between personality modules and the Neutral Baseline.

This harness exists to answer the question:

> *"How much style did this personality introduce, where, and in what dimensions?"*

After M18, RenaceCHESS can truthfully say:

> *"We can deterministically measure, bound, and attribute stylistic divergence relative to a neutral control."*

---

## Purpose

### What M18 Does

1. **Measures Divergence**: Computes KL divergence, Total Variation distance, and Jensen-Shannon divergence between personality output and Neutral Baseline
2. **Tracks Envelope Utilization**: Measures how much of the safety envelope (delta_p_max, top_k) is used
3. **Provides Attribution**: Traces divergence back to M11 structural features (mobility, weak squares)
4. **Produces Artifacts**: Generates schema-validated JSON evaluation artifacts

### What M18 Does NOT Do

- ❌ Integrate with the live eval runner
- ❌ Touch training or frozen-eval data
- ❌ Modify models, weights, or schemas
- ❌ Add dashboards or UI
- ❌ Introduce LLM logic

---

## Core Components

### PersonalityEvalHarness

The main harness class that orchestrates evaluation.

```python
from renacechess.personality.eval_harness import PersonalityEvalHarness
from renacechess.personality.pawn_clamp import PawnClampPersonalityV1
from renacechess.personality.neutral_baseline import NeutralBaselinePersonalityV1

harness = PersonalityEvalHarness(
    personality=PawnClampPersonalityV1(),
    baseline=NeutralBaselinePersonalityV1(),
)

artifact = harness.evaluate(
    base_policy=policy,
    context=structural_context,
    constraints=safety_envelope,
    fixture_id="evaluation_001",
)
```

### Divergence Metrics

| Metric | Description | Range |
|--------|-------------|-------|
| `klDivergence` | KL divergence from baseline (bits) | [0, ∞) |
| `totalVariation` | Total Variation distance | [0, 1] |
| `jensenShannon` | Jensen-Shannon divergence | [0, 1] |
| `maxProbabilityDelta` | Maximum probability shift for any move | [0, 1] |
| `meanProbabilityDelta` | Mean absolute probability shift | [0, 1] |

### Envelope Utilization

| Metric | Description |
|--------|-------------|
| `deltaPMaxUsedPct` | Percentage of delta_p_max utilized [0, 100] |
| `topKBinding` | Whether top_k constraint was binding |
| `entropyInBounds` | Whether output entropy is within bounds |

### Structural Attribution

Simple numeric attribution (not statistical correlation):

| Component | Description |
|-----------|-------------|
| `styleScoreComponents` | Per-component style score statistics (mean, min, max) |
| `featureDeltas` | Per-feature delta statistics |
| `correlationProxy` | Normalized dot product (proxy for correlation) |

---

## Artifact Schema

Evaluation artifacts follow the `PersonalityEvalArtifactV1` schema:

```json
{
  "schemaVersion": "personality_eval_artifact.v1",
  "createdAt": "2026-01-31T12:00:00Z",
  "personalityId": "style.pawn_clamp.v1",
  "baselineId": "control.neutral_baseline.v1",
  "configHash": "abc123...",
  "determinismHash": "def456...",
  "fixtureId": "evaluation_001",
  "divergenceMetrics": {
    "klDivergence": 0.15,
    "totalVariation": 0.08,
    "jensenShannon": 0.05,
    "maxProbabilityDelta": 0.12,
    "meanProbabilityDelta": 0.04
  },
  "envelopeUtilization": {
    "deltaPMaxUsedPct": 80.0,
    "deltaPMaxLimit": 0.15,
    "topKBinding": false,
    "topKLimit": 5,
    "movesConsidered": 5,
    "entropyInBounds": true,
    "outputEntropy": 1.8
  },
  "structuralAttribution": {
    "styleScoreComponents": {
      "mobility": {"mean": 4.5, "min": 0.0, "max": 12.0},
      "weakSquares": {"mean": 2.0, "min": 0.0, "max": 4.0}
    },
    "correlationProxy": 0.25
  },
  "policyStats": {
    "baseEntropy": 2.0,
    "outputEntropy": 1.8,
    "entropyDelta": -0.2,
    "moveCount": 5
  }
}
```

---

## Test Fixtures

M18 uses synthetic fixtures only (no real Lichess data or frozen eval positions).

### Simple Fixtures

- **Uniform**: Equal probability across all moves
- **Peaked**: Single move with high probability
- **Two-Peak**: Two moves with elevated probability

### Entropy-Matched Fixtures

Synthetic distributions with controlled entropy levels matching typical human policy distributions:

- Low entropy (~0.5 bits): Very peaked
- Medium entropy (~1.5 bits): Moderately diffuse
- High entropy (~2.5 bits): Highly diffuse

---

## Key Invariants

1. **Neutral vs Neutral = Zero Divergence**
   - When both personality and baseline are Neutral Baseline, all divergence metrics must be exactly 0

2. **Determinism**
   - Same inputs must produce identical artifacts (verified via determinism_hash)

3. **Envelope Compliance**
   - delta_p_max_used_pct must never exceed 100%
   - All output policies must remain within safety bounds

4. **Valid Attribution**
   - Structural attribution is only computed when context is available
   - Returns None for empty context

---

## Usage

### Evaluate a Personality

```python
from renacechess.personality.eval_harness import (
    PersonalityEvalHarness,
    save_artifact,
)
from renacechess.personality.pawn_clamp import PawnClampPersonalityV1
from renacechess.personality.neutral_baseline import NeutralBaselinePersonalityV1
from renacechess.contracts.models import SafetyEnvelopeV1
from pathlib import Path

# Create harness
harness = PersonalityEvalHarness(
    PawnClampPersonalityV1(),
    NeutralBaselinePersonalityV1(),
)

# Evaluate
artifact = harness.evaluate(
    base_policy=policy,
    context=context,
    constraints=SafetyEnvelopeV1(),
    fixture_id="my_evaluation",
)

# Save artifact
save_artifact(artifact, Path("artifacts/personality_eval/result.json"))
```

### Compare Divergence

```python
# Zero divergence for Neutral vs Neutral
assert artifact.divergence_metrics.kl_divergence == 0.0
assert artifact.divergence_metrics.total_variation == 0.0

# Positive divergence for style personalities
assert artifact.divergence_metrics.kl_divergence >= 0.0
```

---

## Implementation Files

| File | Purpose |
|------|---------|
| `src/renacechess/personality/eval_harness.py` | Evaluation harness implementation |
| `src/renacechess/contracts/models.py` | Pydantic models (PersonalityEvalArtifactV1, etc.) |
| `src/renacechess/contracts/schemas/v1/personality_eval_artifact.v1.schema.json` | JSON Schema |
| `tests/test_m18_personality_eval_harness.py` | Comprehensive test suite |
| `tests/fixtures/personality_eval/` | Synthetic test fixtures |

---

## Governance

- **Schema Version**: `personality_eval_artifact.v1`
- **Backward Compatibility**: N/A (new artifact type)
- **Deferred to M19+**: Eval runner integration, position-level heatmaps, multi-personality dashboards

---

## Scientific Claim

After M18, RenaceCHESS supports the claim:

> *"We can deterministically measure, bound, and attribute stylistic divergence relative to a neutral control."*

This statement is the foundation for:
- Credible research claims about personality effects
- Safe runtime integration in future milestones
- Elo-appropriate explanation work in Phase C

---

**Milestone:** M18 — PERSONALITY-EVAL-HARNESS-001  
**Phase:** Phase B: Personality Framework & Style Modulation  
**Status:** Complete

