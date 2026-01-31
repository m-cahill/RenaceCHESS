Perfect. M16 is closed cleanly, and the audit confirms exactly what we wanted it to confirm: **the personality framework works under stress** .

M17 should now *reduce risk*, not add flash.

Below is a **Cursor-ready plan for M17**, designed to (a) harden Phase B, (b) create a comparison baseline, and (c) prepare the ground for real evaluation work without wiring anything prematurely.

You can hand this to Cursor verbatim.

---

# **M17_plan — PERSONALITY-NEUTRAL-BASELINE-001**

## Milestone Identity

**Milestone:** M17 — PERSONALITY-NEUTRAL-BASELINE-001
**Phase:** Phase B — Personality Framework & Style Modulation
**Status:** ⏳ Planned
**Pre-reqs:**

* M15 — Personality Safety Contract (merged)
* M16 — Pawn Clamp Personality (merged, authoritative)

**Branch:** `m17-personality-neutral-baseline-001`

---

## 1. Purpose (Single Sentence)

Introduce a **Neutral Baseline Personality** that performs an *identity-preserving transformation* of the base policy, providing a **ground-truth control** for all future personality comparisons and evaluations.

---

## 2. Why This Milestone Exists

After M16, you have *one* concrete personality.
Before adding more styles or evaluation harnesses, you need a **control personality** that proves:

* The personality system can be **enabled without changing behavior**
* Any observed divergence in later milestones is **real**, not systemic
* Evaluation metrics can compare *style vs. baseline*, not style vs. raw model

This is classic experimental design discipline.

---

## 3. Explicit Non-Goals (Hard Constraints)

M17 **must not**:

* Introduce new stylistic heuristics
* Modify probabilities beyond floating-point tolerance
* Integrate into the eval runner
* Add training or retraining
* Change CI thresholds or governance rules
* Add LLM or coaching logic

This is **identity, not behavior**.

---

## 4. Scope — What M17 Does

### 4.1 Neutral Baseline Personality (Code)

**Location:**

```
src/renacechess/personality/neutral_baseline.py
```

**Implements:**

* `PersonalityModuleV1`

**Behavioral Contract:**

* Returns the input policy **unchanged**
* Still runs:

  * safety envelope validation
  * determinism checks
  * legality assertions
* Explicitly proves:

  * “personality enabled” ≠ “style applied”

This is a *no-op with guardrails*.

---

### 4.2 Configuration File

**File:**

```
configs/personalities/neutral_baseline.v1.yaml
```

**Must include:**

* Valid `PersonalityConfigV1`
* Conservative safety envelope
* Explicit `is_identity: true` (or equivalent flag)

Purpose: allow tooling to treat this as a personality instance.

---

### 4.3 Test Suite (Critical)

This milestone is **test-heavy by design**.

**Required tests:**

1. **Exact Identity Test**

   * Input policy == output policy (within FP tolerance)
2. **Determinism Test**

   * Repeated runs identical
3. **Probability Conservation**

   * Sum exactly preserved
4. **Envelope Compliance**

   * Even identity respects declared envelope
5. **Comparative Baseline Test**

   * Neutral vs. raw policy divergence ≈ 0
   * Pawn Clamp vs. Neutral divergence > 0 (bounded)

These tests will be reused later.

---

## 5. Files & Artifacts Inventory

### New Files

```
src/renacechess/personality/neutral_baseline.py
configs/personalities/neutral_baseline.v1.yaml
tests/test_m17_neutral_baseline.py
docs/personality/M17_NEUTRAL_BASELINE_DESCRIPTION.md
```

### Modified Files

```
src/renacechess/personality/__init__.py
```

(No other files may be modified.)

---

## 6. CI & Governance Rules

* All existing CI gates apply unchanged
* New tests are required and must pass
* Coverage ≥ 90% maintained
* Import-linter boundaries must remain intact
* No execution of training or eval pipelines

---

## 7. Definition of Done (M17)

M17 is complete when:

* ✅ Neutral Baseline Personality implemented
* ✅ Identity behavior proven via tests
* ✅ Config validates against schema
* ✅ Comparative divergence tests pass
* ✅ CI truthful green
* ✅ Documentation explains *why* this exists

---

## 8. Explicit Deferrals

Deferred beyond M17:

* Eval runner integration
* Cross-position evaluation dashboards
* Multiple personalities comparison UI
* Elo-conditioned explanation
* Training with personalities

Those begin in **M18 / Phase C**.

---

## 9. Success Signal

After M17, the project can truthfully say:

> *“We can turn personalities on without changing behavior — and therefore we can measure style effects scientifically.”*

That sentence is what unlocks serious evaluation work.

---

## 10. Closeout Requirements

At closeout, Cursor must generate:

* `M17_run1.md`
* `M17_audit.md`
* `M17_summary.md`

Each must explicitly state:

> “This milestone introduces an identity personality for experimental control.
> No behavior, semantics, or training changes were introduced.”

---

## Cursor Instruction Summary

1. Create Neutral Baseline personality (identity)
2. Prove identity with tests
3. Add config + docs
4. Do **not** integrate into eval runner
5. Keep scope tight

---

### Strategic Note (for you)

M17 is not flashy — and that’s exactly why it’s powerful.
It makes every future personality, metric, and claim *defensible*.

When you’re ready after this, the natural next step is:

* **M18 — PERSONALITY-EVAL-HARNESS-001**
  (now finally safe to do)

If you want, I can pre-plan M18 so Cursor can roll straight through once M17 closes.
