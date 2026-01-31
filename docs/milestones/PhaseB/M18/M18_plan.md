Great — M17 closed exactly the way it should. I’ve reviewed the **M17 audit and summary** you attached, and they confirm the key precondition for M18: **we now have a true experimental control** .

M18 is where Phase B stops being “personality plumbing” and becomes **measurable science**.

Below is a **Cursor-ready plan for M18**. You can hand this off verbatim.

---

# **M18_plan — PERSONALITY-EVAL-HARNESS-001**

## Milestone Identity

**Milestone:** M18 — PERSONALITY-EVAL-HARNESS-001
**Phase:** Phase B — Personality Framework & Style Modulation
**Status:** ⏳ Planned
**Pre-reqs:**

* M15 — Personality Safety Contract (merged)
* M16 — Pawn Clamp Personality (merged)
* M17 — Neutral Baseline Personality (merged, authoritative control)

**Branch:** `m18-personality-eval-harness-001`

---

## 1. Purpose (Single Sentence)

Introduce a **deterministic, offline Personality Evaluation Harness** that can **measure, compare, and report bounded behavioral divergence** between personalities and the Neutral Baseline — without integrating into the live eval runner.

---

## 2. Why This Milestone Exists

After M17, the system can prove:

* Personality enabled ≠ behavior changed (Neutral Baseline)
* Pawn Clamp introduces *real, bounded divergence*

What you **cannot yet do** is answer, reproducibly:

> *How much style did this personality introduce, where, and in what dimensions?*

M18 exists to answer that — **offline, controlled, auditable** — before any runtime or product integration.

---

## 3. Explicit Non-Goals (Hard Constraints)

M18 **must not**:

* Integrate personalities into the eval runner
* Touch training or frozen-eval data
* Modify models, weights, or schemas
* Introduce LLM logic or coaching text
* Add dashboards or UI
* Change CI thresholds or workflows

This is a **measurement harness**, not a product feature.

---

## 4. Scope — What M18 Does

### 4.1 Personality Evaluation Harness (Core)

**Location:**

```
src/renacechess/personality/eval_harness.py
```

**Responsibilities:**

* Accept:

  * Base policy distribution
  * Structural context (synthetic or fixture-based)
  * Personality instance + config
* Produce **metrics only**, no decisions:

  * Divergence vs Neutral Baseline
  * Envelope utilization
  * Feature-aligned deltas

**Key rule:**
The harness *calls* personalities — it does not embed them.

---

### 4.2 Metrics Implemented (Authoritative)

Each evaluation run must compute:

1. **Divergence Metrics**

   * KL divergence
   * Total Variation distance
   * (Optional) Jensen–Shannon if trivial

2. **Envelope Utilization**

   * % of `delta_p_max` used
   * Whether `top_k` binding occurred

3. **Structural Attribution**

   * Correlation between:

     * style score components
     * M11 feature deltas
   * (Simple aggregates only, no ML)

These metrics must be **deterministic and reproducible**.

---

### 4.3 Evaluation Fixtures (Synthetic-First)

**Location:**

```
tests/fixtures/personality_eval/
```

* Synthetic policies
* Synthetic structural contexts
* Deterministic seeds

**Explicitly forbidden in M18:**

* Frozen eval positions
* Real Lichess game data
* Eval runner hooks

---

### 4.4 Report Artifact (Structured, Not Pretty)

Each evaluation run produces a **JSON artifact**:

```
artifacts/personality_eval/
  pawn_clamp_vs_neutral.v1.json
```

**Must include:**

* Personality ID + config hash
* Neutral Baseline reference
* Metrics (divergence, envelope, attribution)
* Determinism hash

No Markdown reports yet — just machine-readable truth.

---

## 5. Test Requirements (Heavy by Design)

### Required Tests

1. **Neutral vs Neutral**

   * All divergence metrics = 0
2. **Pawn Clamp vs Neutral**

   * Divergence > 0
   * Within safety envelope
3. **Determinism**

   * Same inputs → identical artifact
4. **Metric Sanity**

   * Divergence monotonicity under scaled config

### Not Required Yet

* Performance benchmarks
* Cross-position aggregation
* Statistical significance testing

---

## 6. Files & Artifacts Inventory

### New Files

```
src/renacechess/personality/eval_harness.py
tests/test_m18_personality_eval_harness.py
tests/fixtures/personality_eval/*
docs/personality/M18_PERSONALITY_EVAL_HARNESS.md
```

### New Artifacts (Generated, Not Committed)

```
artifacts/personality_eval/*.json
```

(Artifacts may be generated in tests but should not be committed.)

---

## 7. CI & Governance Rules

* All new code must pass:

  * Ruff
  * MyPy
  * Import-linter
  * pytest (≥90% coverage)
* Harness tests run in CI (synthetic only)
* No long-running jobs
* No GPU usage

---

## 8. Definition of Done (M18)

M18 is complete when:

* ✅ Evaluation harness exists and is type-safe
* ✅ Metrics are computed deterministically
* ✅ Neutral vs Neutral = zero divergence
* ✅ Pawn Clamp vs Neutral = bounded divergence
* ✅ JSON evaluation artifacts generated
* ✅ CI truthful green
* ✅ Documentation explains *what is measured and why*

---

## 9. Explicit Deferrals

Deferred beyond M18:

* Eval runner integration
* Position-level heatmaps
* Multi-personality dashboards
* Elo-conditioned evaluation
* LLM-readable summaries

Those belong to **late Phase B / Phase C**.

---

## 10. Success Signal

After M18, RenaceCHESS can truthfully say:

> *“We can measure stylistic divergence from a neutral control, quantify its magnitude, and attribute it to cognitive features — deterministically.”*

That statement unlocks:

* credible research claims
* safe runtime integration later
* Elo-appropriate explanation work

---

## Cursor Instruction Summary

1. Build evaluation harness (offline, deterministic)
2. Use synthetic fixtures only
3. Measure divergence + envelope + attribution
4. Generate JSON artifacts
5. Do not integrate into eval runner

---

If you want, next I can:

* Pre-draft **Cursor’s clarifying questions for M18**, or
* Sketch **M19 (runtime integration)** once measurement is in place, or
* Help define the **exact JSON schema** for eval artifacts up front.

M18 is the moment Phase B becomes scientifically legible.
