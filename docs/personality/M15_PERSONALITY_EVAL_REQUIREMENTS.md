# Personality Evaluation Requirements (M15)

**Version:** 1.0  
**Status:** ACTIVE  
**Effective:** M16+  
**Last Updated:** 2026-01-31

---

## 1. Purpose

This document defines **what future personality implementations must prove** before they can be considered production-ready.

These requirements are established in M15 (contract phase) and enforced starting with M16 (first implementation).

---

## 2. Evaluation Categories

### 2.1 Invariant Compliance

Every personality implementation **MUST** satisfy all invariants from the Personality Safety Contract v1:

| Invariant | Test Requirement |
|-----------|------------------|
| Determinism | Given identical inputs, verify byte-identical outputs across 100 invocations |
| Base policy reachability | Verify existence of identity configuration |
| Legality preservation | Verify all output moves are in `position.legalMoves` |
| Probability conservation | Verify `sum(output.topMoves[*].p) == 1.0` (within 1e-6 tolerance) |
| Envelope compliance | Verify no move shifts beyond `delta_p_max` |

**Test Type:** Unit tests with property-based testing where feasible.

---

### 2.2 Regression Tests

Every personality implementation **MUST** include regression tests proving:

| Metric | Requirement |
|--------|-------------|
| Base policy accuracy | No degradation vs baseline on frozen eval |
| Top-1 accuracy delta | Within ±2% of base policy on matched positions |
| Entropy bounds | Output entropy within [entropy_min, entropy_max] |
| Illegal move rate | 0% (hard requirement) |

**Test Type:** Integration tests against frozen eval set.

---

### 2.3 Divergence Measurement

Every personality **MUST** report divergence from base policy:

| Metric | Description |
|--------|-------------|
| KL Divergence | Mean KL(personality \|\| base) across test set |
| TV Distance | Total variation distance from base policy |
| Top-1 Agreement | Percentage where personality top-1 == base top-1 |
| Rank Correlation | Spearman correlation of move rankings |

**Test Type:** Metrics computed and logged in evaluation reports.

---

### 2.4 Deterministic Replayability

Personality transformations **MUST** be deterministically replayable:

| Requirement | Description |
|-------------|-------------|
| Seed control | No implicit randomness; all stochastic elements seeded |
| Config hash | Personality config produces stable hash |
| Output hash | Same inputs → same output hash |

**Test Type:** Golden file tests with version-pinned outputs.

---

### 2.5 Style Explainability via M11 Features

Personalities **MUST** be explainable through M11 structural cognition features:

| Requirement | Description |
|-------------|-------------|
| Feature citation | Document which M11 features inform style choices |
| Delta attribution | Explain probability shifts in terms of structural features |
| Narrative mapping | Map style behaviors to structural labels |

**Test Type:** Documentation + automated checks for feature usage.

---

## 3. Evaluation Report Schema

Personality evaluation reports **MUST** include:

```json
{
  "personalityId": "style.pawn_clamp.v1",
  "configHash": "<sha256>",
  "baselineComparison": {
    "basePolicyId": "baseline.learned_policy.v1",
    "frozenEvalManifestHash": "<sha256>",
    "positionsEvaluated": 1000
  },
  "invariantCompliance": {
    "determinism": true,
    "baseReachable": true,
    "legalityPreserved": true,
    "probabilityConserved": true,
    "envelopeCompliance": true
  },
  "divergenceMetrics": {
    "klDivergence": 0.05,
    "tvDistance": 0.08,
    "top1Agreement": 0.92,
    "rankCorrelation": 0.95
  },
  "regressionMetrics": {
    "basePolicyAccuracy": 0.42,
    "personalityAccuracy": 0.41,
    "accuracyDelta": -0.01,
    "illegalMoveRate": 0.0
  },
  "styleExplainability": {
    "featuresUsed": ["perPiece.mobility", "squareMap.weak"],
    "narrativeLabels": ["mobility-restriction", "weakness-exploitation"]
  }
}
```

---

## 4. Evaluation Phases

### 4.1 M16 — First Implementation

- Basic invariant compliance tests
- Regression tests against frozen eval
- Initial divergence measurements

### 4.2 M17 — Personality Library

- Cross-personality comparison
- Style distinctiveness metrics
- No mutual interference validation

### 4.3 M18 — Personality Evaluation Suite

- Full evaluation report schema
- Automated style explainability
- Benchmark suite for personality quality

---

## 5. Failure Criteria

A personality **FAILS** evaluation if:

1. ❌ Any invariant is violated
2. ❌ Illegal move rate > 0%
3. ❌ Accuracy degradation > 5% vs base policy
4. ❌ Entropy outside bounds for > 1% of positions
5. ❌ KL divergence > 0.5 (indicates too much deviation)
6. ❌ Non-deterministic output detected

---

## 6. Relationship to Other Documents

| Document | Relationship |
|----------|--------------|
| `PERSONALITY_SAFETY_CONTRACT_v1.md` | Defines invariants this document enforces |
| `StructuralCognitionContract_v1.md` | Defines features used for explainability |
| Frozen Eval Manifest | Provides test set for regression tests |

---

## 7. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-31 | Initial release (M15) |

---

**Document Authority:** RenaceCHESS Governance  
**Enforcement Starts:** M16

