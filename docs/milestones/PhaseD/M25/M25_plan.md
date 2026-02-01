Excellent — M24 closed cleanly, and the documents you attached confirm we now have **measurement with teeth** and **no outstanding debt introduced**  .
That means M25 can finally do the thing Phase D exists for: **change behavior, but in a governed, reversible way**.

Below is a **Cursor-ready M25 plan**, written to slot directly into your existing milestone workflow.

---

# M25_plan — PHASE-D-RECALIBRATION-001

**Phase:** D — Data Expansion, Calibration & Quality
**Milestone intent:** Introduce **explicit, measurable probability recalibration** (starting with temperature scaling) using M24’s calibration metrics — without violating Phase C contracts or explanation safety.

---

## 0) Why M25 exists (clear positioning)

After M24, it is now *provably true* that RenaceCHESS can:

* Measure calibration error (ECE, Brier, NLL)
* Stratify by Elo bucket
* Do so deterministically and in CI

What is **not yet true**:

> “The probabilities we expose are *as calibrated as we know how to make them*.”

M25 exists to **improve calibration** — *not* to add new models, new coaching language, or new UX.

---

## 1) Scope definition

### ✅ In Scope (M25)

M25 introduces **controlled recalibration layers**:

1. **Temperature scaling** for:

   * Outcome head (W/D/L)
   * Policy head (move probabilities)
2. **Per-Elo-bucket parameters**
3. **Offline-only application** (evaluation + optional CLI preview)
4. **Before/after comparison artifacts**

---

### ❌ Explicitly Out of Scope

* No retraining
* No torch upgrade (TORCH-SEC-001 still deferred)
* No changes to AdviceFactsV1 / EloBucketDeltaFactsV1 / CoachingDraftV1
* No LLM prompt or behavior changes
* No UI or product surface commitments

---

## 2) Core deliverables

### A) RecalibrationParametersV1 (new contract)

Create a new schema:

```text
RecalibrationParametersV1
```

**Structure (per Elo bucket):**

* `elo_bucket`
* `outcome_temperature`
* `policy_temperature`
* `fit_method` (e.g. `grid_search`, `lbfgs`)
* `fit_metric` (ECE or NLL)
* `generated_at`
* `source_calibration_metrics_hash`

📌 **Important:**
This is a *pure parameter artifact*. It contains **no logic** and **no metrics**, only fitted parameters + provenance.

---

### B) Recalibration fitting runner (offline)

Add an offline runner that:

1. Consumes:

   * Frozen eval dataset
   * Frozen model (baseline)
   * CalibrationMetricsV1 (from M24)
2. Fits:

   * One temperature per bucket per head
3. Produces:

   * `recalibration_parameters.json`
4. Is:

   * Deterministic
   * CI-executable
   * Checkpoint-optional

Suggested location:

```
src/renacechess/eval/recalibration_runner.py
```

---

### C) Calibration improvement evaluation

Add a second evaluation pass that computes:

* **Pre-recalibration metrics** (from M24)
* **Post-recalibration metrics** (same metrics, same data)

Produce a **comparison artifact**:

```text
CalibrationDeltaV1
```

Fields:

* `elo_bucket`
* `metric`
* `before`
* `after`
* `delta`
* `improved: bool`

📌 No thresholds yet — *visibility only*.

---

### D) CI job: `recalibration-eval`

Add a new CI job that:

* Runs recalibration fitting
* Runs before/after evaluation
* Uploads:

  * `recalibration-parameters.json`
  * `calibration-delta.json`
* Fails only if:

  * runner crashes
  * schema invalid
  * determinism violated

This mirrors the **M24 measurement posture** .

---

### E) Optional CLI preview (non-default)

Add a CLI subcommand:

```
renacechess calibration preview --with-recalibration
```

Rules:

* Off by default
* Explicit flag required
* Prints:

  * Before vs after calibration summary
* Does **not** affect any existing CLI command paths

This keeps Phase C surfaces pristine.

---

## 3) Acceptance criteria (hard gates)

M25 is **closable only if**:

1. ✅ RecalibrationParametersV1 schema exists and validated
2. ✅ Deterministic recalibration runner passes in CI
3. ✅ Calibration deltas computed per Elo bucket
4. ✅ No Phase C contract changes
5. ✅ No runtime behavior changes (default path unchanged)
6. ✅ CI remains ≥90% coverage
7. ✅ No new deferrals without rationale

---

## 4) Guardrails (non-negotiable)

To prevent Phase D scope bleed:

* 🚫 Recalibration must **not** auto-apply at runtime
* 🚫 No silent probability modification
* 🚫 No thresholds that cause CI failure
* 🚫 No “smart” heuristics beyond temperature scaling in M25

M25 is **controlled, reversible adjustment only**.

---

## 5) Execution plan (Cursor-friendly)

**Branch:**
`m25-phase-d-recalibration-001`

### PR1 — Schemas

* Add RecalibrationParametersV1
* Add CalibrationDeltaV1
* Schema tests

### PR2 — Fitting runner

* Implement temperature scaling
* Determinism tests

### PR3 — Evaluation + CI

* Add `recalibration-eval` job
* Artifact upload
* Before/after comparison

### PR4 — Optional CLI preview + docs

* CLI flag (off by default)
* M25_plan / run / audit stubs

---

## 6) Why this ordering matters

This keeps Phase D honest:

* **M24**: “Can we measure calibration?” ✅
* **M25**: “Can we improve calibration in a provable way?” ⏳
* **M26**: “Should we apply it to users?” (future decision)

No leapfrogging. No hand-waving.

---

## 7) One-line positioning

> **M25 introduces the first behavior-changing improvement in RenaceCHESS — but only in a way that can be measured, reversed, and audited.**

---

## Authorization

This plan is **approved to hand off to Cursor** as-is.

If you want next, I can:

* Pre-draft `RecalibrationParametersV1`
* Suggest exact temperature-fitting algorithms (grid vs LBFGS)
* Or sketch **M26 (runtime gating & user exposure)** so Phase D stays tight

Just tell me how aggressive you want to be.
