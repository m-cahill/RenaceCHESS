Perfect — M26 gives us the **governance substrate**. M27 is where we finally *use it*, but in a way that stays Phase-D-safe and reversible.

Below is a **Cursor-ready M27 plan** you can hand off directly.

---

# 📌 M27 Plan — PHASE-D-RUNTIME-RECALIBRATION-EVALUATION-001

**Phase:** D (Data Expansion, Calibration & Quality)
**Status:** Planned
**Pre-reqs:** M26 closed ✅
**Mode:** Measurement-only, no default behavior changes

---

## 1. Milestone Objective

**Evaluate the real-world impact of runtime recalibration** (introduced in M26) under controlled conditions, without enabling it by default or changing Phase C contracts.

M27 answers one question only:

> **Does runtime recalibration *actually* improve human-facing prediction quality, and if so, where?**

This is an **evaluation milestone**, not an activation milestone.

---

## 2. Why M27 Exists (Motivation)

After M25 + M26, RenaceCHESS can:

* Fit recalibration parameters offline
* Apply them at runtime **safely and explicitly**
* Prove the default path is unchanged

What we *don’t yet know*:

* Whether runtime recalibration meaningfully improves:

  * Human W/D/L probability quality
  * Move-probability realism
  * Coaching signal stability
* Which Elo buckets benefit
* Whether any regressions appear in edge positions

M27 provides **evidence**, not policy.

---

## 3. Scope Definition

### ✅ In Scope

1. **Controlled runtime evaluation**

   * Explicit use of `RecalibrationGateV1(enabled=True)`
   * No default behavior changes

2. **Before/After comparison**

   * Baseline (no gate)
   * Recalibrated (gate enabled)

3. **Metrics collected**

   * Outcome head: ECE, NLL, Brier
   * Policy head: entropy shift, top-k stability
   * Delta metrics only (no new training)

4. **Per-bucket analysis**

   * Elo bucket × time pressure
   * Identify where recalibration helps vs hurts

5. **New evaluation artifacts**

   * `RuntimeRecalibrationReportV1`
   * `RuntimeRecalibrationDeltaV1`

6. **CI-verified reproducibility**

   * Deterministic runs
   * Artifact hashes recorded

---

### ❌ Out of Scope

* Default-on recalibration ❌
* UI/UX changes ❌
* LLM prompt changes ❌
* Phase C contract changes ❌
* New calibration methods ❌
* Training or fine-tuning ❌

---

## 4. Deliverables (Concrete)

### A. New Artifacts

#### 1. `RuntimeRecalibrationReportV1`

```json
{
  "schema_version": "v1",
  "gate_ref": "recalibration_gate.json",
  "parameters_ref": "recalibration_parameters.json",
  "dataset_ref": "frozen_eval_vX",
  "metrics": {
    "baseline": {...},
    "recalibrated": {...},
    "delta": {...}
  }
}
```

#### 2. `RuntimeRecalibrationDeltaV1`

* Per-bucket metric deltas
* Clearly signed (+/-) improvements

---

### B. New Runner

* `eval/runtime_recalibration_eval_runner.py`

  * Loads gate + params
  * Executes **paired runs**:

    * Gate disabled
    * Gate enabled
  * Emits delta artifacts

---

### C. CLI Additions (Non-Breaking)

New **explicit** command (no behavior change elsewhere):

```bash
renacechess eval runtime-recalibration \
  --gate path/to/gate.json \
  --params path/to/params.json \
  --dataset frozen_eval.json \
  --out artifacts/
```

⚠️ This command is **evaluation-only**.

---

## 5. CI / Validation Plan

### Required CI Jobs

1. **runtime-recalibration-eval**

   * Runs paired evaluation
   * Produces delta artifacts
   * Must be deterministic

2. **runtime-recalibration-sanity**

   * Asserts:

     * Metrics computed
     * No NaNs
     * No schema violations

3. **Existing Guard Job**

   * Must still pass
   * Default path unchanged

---

### Failure Conditions

CI fails if:

* Artifacts differ between identical runs
* Schema validation fails
* Metrics computation crashes
* Gate is applied without explicit enablement

CI **does not fail** on:

* Negative deltas (that’s the point of evaluation)

---

## 6. Tests to Add

### Unit Tests

* Metric delta computation
* Bucket aggregation logic
* Gate/params mismatch handling

### Integration Tests

* Full paired evaluation on small frozen fixture
* Artifact determinism check

### Explicit Non-Goals

* No E2E human UI tests
* No LLM tests

---

## 7. Architectural Constraints (Hard Rules)

* 🔒 Phase C contracts untouched
* 🔒 Default runtime path unchanged
* 🔒 Gate required to apply recalibration
* 🔒 No new dependencies
* 🔒 Deterministic artifacts only

---

## 8. Exit Criteria (Clear & Binary)

M27 is **DONE** when:

* ✅ Runtime recalibration impact is quantified
* ✅ Per-bucket deltas are produced
* ✅ No regressions are hidden or suppressed
* ✅ CI proves reproducibility
* ✅ No behavior changes without gate
* ✅ Audit + summary written

---

## 9. What M27 Unlocks (But Does NOT Do)

M27 **enables decision-making**, not decisions.

After M27, you can choose to:

* Proceed to controlled activation (M28)
* Restrict recalibration to certain buckets
* Abandon runtime recalibration entirely

All options remain open.

---

## 10. Cursor Handoff Summary (TL;DR)

> **Implement a paired runtime evaluation runner that compares baseline vs gated recalibration, emits delta artifacts, and proves whether runtime recalibration is worth considering — without changing default behavior.**

---

If you want, next I can:

* Seed `M27_plan.md` verbatim
* Draft the schemas for `RuntimeRecalibrationReportV1`
* Pre-write the CI job YAML
* Or sketch **M28 vs M29 fork options** depending on M27 outcomes
