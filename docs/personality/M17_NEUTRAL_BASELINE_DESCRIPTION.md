# M17 Neutral Baseline Personality — Description

**Milestone:** M17 — PERSONALITY-NEUTRAL-BASELINE-001  
**Phase:** Phase B: Personality Framework & Style Modulation  
**Status:** Implemented

---

## Purpose

The **Neutral Baseline Personality** provides a **ground-truth experimental control** for the personality framework.

### The Scientific Claim

After M17, the project can truthfully state:

> *"We can enable the personality system without changing behavior, and we can prove it."*

This claim is what makes future personality evaluation legitimate.

---

## Why This Exists

Before M17, the project had one concrete personality (Pawn Clamp from M16). Before adding more styles or evaluation harnesses, a **control personality** was needed to prove:

1. **The personality system can be enabled without changing behavior**
   - Observed divergence in later milestones is *real*, not systemic noise

2. **Evaluation metrics compare style vs. baseline**
   - Not style vs. raw model with unmeasured system effects

3. **Classic experimental design discipline**
   - You need a control group before measuring treatment effects

---

## Behavioral Contract

The `NeutralBaselinePersonalityV1` implements the `PersonalityModuleV1` protocol with identity semantics:

### What It Does

- **Returns the input policy unchanged**
- **Validates safety envelope constraints** (demonstrates constraint path is exercised)
- **Provides baseline for divergence metrics** (KL divergence ≈ 0, TV distance = 0)

### What It Does NOT Do

- **Does not modify probabilities** (not even by floating-point epsilon)
- **Does not use structural context** (ignores M11 features entirely)
- **Does not apply style heuristics** (no re-ranking, no shaping)

---

## Identity Properties (Testable)

The Neutral Baseline satisfies all of these invariants:

| Property | Description | Test Method |
|----------|-------------|-------------|
| Exact Identity | `output == input` within FP tolerance | Direct comparison |
| Determinism | Same inputs → same outputs | Repeated application |
| Probability Conservation | Sum exactly preserved | Sum comparison |
| Zero Divergence | KL div = 0, TV distance = 0 | Metric computation |
| Context Independence | Result unchanged by context | Empty vs full context |

---

## Comparative Testing

The Neutral Baseline enables comparative divergence testing:

### Test 1: Neutral vs. Raw Policy

```
divergence(Neutral(policy), policy) ≈ 0
```

This proves the personality system adds no noise.

### Test 2: Style vs. Neutral

```
divergence(PawnClamp(policy), Neutral(policy)) > 0
divergence(PawnClamp(policy), Neutral(policy)) ≤ envelope
```

This proves observed style effects are real.

---

## Implementation Details

### Personality ID

```
control.neutral_baseline.v1
```

Category is `control` (not `style`) to indicate this is an experimental control, not a style.

### is_identity() Behavior

```python
def is_identity(self, constraints: SafetyEnvelopeV1) -> bool:
    return True  # Always identity, regardless of constraints
```

Unlike style personalities where `is_identity()` depends on configuration (e.g., zero weights), the Neutral Baseline is *definitionally* identity.

### Configuration

The config file (`configs/personalities/neutral_baseline.v1.yaml`) contains a valid `PersonalityConfigV1` but no tunable parameters. The safety envelope is validated but not applied.

---

## Relationship to Other Milestones

| Milestone | Relationship |
|-----------|--------------|
| M15 | Provides the `PersonalityModuleV1` protocol and `SafetyEnvelopeV1` schema |
| M16 | Provides the `PawnClampPersonalityV1` for comparative testing |
| M18+ | Will integrate both Neutral and Pawn Clamp into eval harness |

---

## What M17 Enables

With the Neutral Baseline in place, future milestones can:

1. **M18 — Personality Eval Harness**
   - Compare personalities against Neutral baseline
   - Measure divergence scientifically

2. **M19+ — Additional Personalities**
   - Each new personality is measured against Neutral
   - Style effects are distinguishable from system effects

3. **Phase C — Coaching**
   - Coaching explanations can cite style differences
   - Differences are trustworthy because they're measured against control

---

## Files

| File | Purpose |
|------|---------|
| `src/renacechess/personality/neutral_baseline.py` | Implementation |
| `configs/personalities/neutral_baseline.v1.yaml` | Configuration |
| `tests/test_m17_neutral_baseline.py` | Test suite (15 tests) |
| `docs/personality/M17_NEUTRAL_BASELINE_DESCRIPTION.md` | This document |

---

## Summary

The Neutral Baseline is not flashy—and that's exactly why it's powerful. It makes every future personality, metric, and claim *defensible*.

> **"Identity, not behavior."**  
> — M17 Design Principle

---

**Document Created:** 2026-01-31  
**Milestone:** M17 — PERSONALITY-NEUTRAL-BASELINE-001

