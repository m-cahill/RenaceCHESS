Great — with **M23 cleanly closed**, M24 can finally be the **first “real” Phase D milestone**, not more runway prep.

Below is a **Cursor-ready, audit-aware M24 plan**, explicitly grounded in the **M23 audit and summary you attached**  .

---

# M24_plan — PHASE-D-CALIBRATION-001

**Phase:** D — Data Expansion, Calibration & Quality
**Milestone intent:** Introduce **human-aligned calibration and evaluation signals** *without* changing frozen Phase C contracts or surfaces.

---

## 0) Why M24 exists (clear justification)

M23 ensured Phase D starts with:

* truthful CI
* security + perf visibility
* documented deferrals (TORCH-SEC-001, CLI-COV-001)

What Phase D **does not yet have** is any notion of:

> *“Are these probabilities well-calibrated for humans at each Elo bucket?”*

M24 answers that question **without touching**:

* AdviceFactsV1
* EloBucketDeltaFactsV1
* CoachingDraftV1
* CLI surface

This keeps Phase C pristine and uses Phase D *as intended*: **quality & calibration**.

---

## 1) Scope definition

### ✅ In Scope (M24)

M24 adds **offline calibration + evaluation artifacts only**:

1. **Calibration metrics** for:

   * move probability distributions
   * W/D/L outcome probabilities
2. **Per-Elo bucket breakdown**
3. **Deterministic evaluation artifacts**
4. **CI-verified evaluation runs**

No new user-facing behavior.

---

### ❌ Explicitly Out of Scope

* No new coaching language
* No LLM changes
* No UI / CLI expansion
* No retraining
* No torch upgrade (still deferred per TORCH-SEC-001)

---

## 2) Core deliverables

### A) CalibrationMetricsV1 (new artifact, read-only)

Create a new schema:

```text
CalibrationMetricsV1
```

Captured **per Elo bucket**, including:

* Expected Calibration Error (ECE)
* Brier score (outcomes)
* Negative log-likelihood (policy head)
* Sample count
* Confidence histogram (binned)

**Key rule:**
📌 *This artifact is diagnostic only — it feeds no runtime logic.*

---

### B) Calibration evaluation runner

Add an **offline evaluation runner** that:

1. Consumes:

   * frozen model
   * frozen eval dataset
2. Produces:

   * `calibration_metrics.json`
3. Is:

   * deterministic
   * seed-locked
   * CI-executable

Location suggestion:

```
src/renacechess/eval/calibration_runner.py
```

---

### C) Elo-bucket calibration stratification

Calibration must be computed **per Elo bucket**, not pooled.

Buckets should match existing Phase C buckets exactly
(no new taxonomy introduced).

Output example:

```json
{
  "elo_bucket": "1200-1399",
  "ece": 0.041,
  "brier": 0.182,
  "nll": 1.92,
  "samples": 18342
}
```

---

### D) CI job: `calibration-eval`

Add a new CI job:

* Runs calibration runner
* Uploads artifacts
* **Does not gate on thresholds yet**
* Fails only if:

  * runner crashes
  * output schema invalid
  * determinism violated

This mirrors the **benchmark posture from M23** .

---

### E) Documentation & governance artifacts

Create:

* `docs/milestones/PhaseD/M24/M24_plan.md`
* `docs/milestones/PhaseD/M24/M24_run1.md`
* `docs/milestones/PhaseD/M24/M24_audit.md`
* `docs/milestones/PhaseD/M24/M24_summary.md`

Include:

* calibration intent
* non-use in runtime logic
* how this enables later human evaluation

---

## 3) Acceptance criteria (very explicit)

M24 is **closable** only if:

1. ✅ `CalibrationMetricsV1` schema exists and is validated
2. ✅ Calibration runner executes deterministically in CI
3. ✅ Metrics are produced for **every Elo bucket**
4. ✅ No Phase C contract changes
5. ✅ CI remains ≥90% coverage
6. ✅ No new deferrals added without rationale

---

## 4) Guardrails (important)

To prevent Phase D creep:

* 🚫 Calibration metrics **must not** be consumed by:

  * AdviceFacts
  * DeltaFacts
  * CoachingDraft
* 🚫 No “auto-correction” or “temperature scaling” yet
* 🚫 No threshold-based CI failures

M24 is **measurement only**.

---

## 5) Suggested PR / execution order (Cursor-friendly)

**Single milestone branch:**
`m24-phase-d-calibration-001`

### PR1 — Schemas

* Add `CalibrationMetricsV1`
* Unit tests for schema validation

### PR2 — Runner

* Implement calibration runner
* Determinism tests

### PR3 — CI integration

* Add `calibration-eval` job
* Artifact upload

### PR4 — Docs & audit

* M24 plan, run, audit stubs

---

## 6) Why this sequencing matters

This ordering ensures:

* M24 answers *“Are we well-calibrated?”*
* M25 can answer *“Should we recalibrate?”*
* M26+ can safely introduce:

  * human feedback
  * thresholding
  * UX surfacing

Without M24, Phase D would be guessing.

---

## 7) One-line milestone positioning

> **M24 introduces the first quantitative notion of human-alignment quality — without changing a single user-visible behavior.**

---

### ✅ Authorization

This plan is **ready to hand off to Cursor**.

If you want next, I can:

* pre-draft `CalibrationMetricsV1`
* sketch the CI job YAML
* or propose **M25 (recalibration / temperature scaling)** so Phase D stays coherent

Just say the word.




