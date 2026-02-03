Perfect. M06 is **cleanly closed**, the audit is green, and the deferrals are well-scoped. Based on the attached **M06 audit** and **M06 summary**, the correct next step is to **advance capability, not infrastructure**, while closing the two explicit M06 deferrals without letting them dominate the milestone .

Below is a **Cursor-ready M07 plan** that is:

* strictly PoC-core
* auditable end-to-end
* scoped to one conceptual advance
* compatible with your governance + CI discipline

---

# M07_plan — Human Difficulty Index (HDI) v1 + CLI Completion

## Milestone Identity

**Milestone:** M07
**Title:** Human Difficulty Index (HDI) v1 + Evaluation CLI Completion
**Phase:** PoC-Core
**Precondition:** M06 CLOSED / IMMUTABLE
**Branch:** `m07-hdi-v1`
**Status Goal:** CLOSED with audit artifacts

---

## Objective (Single Sentence)

Introduce a **deterministic, explainable Human Difficulty Index (HDI)** derived solely from existing evaluation signals, while completing deferred CLI and frozen-eval enforcement to make the evaluation stack *operationally complete*.

---

## Scope Definition

### In Scope

1. **Human Difficulty Index (HDI) v1**

   * Scalar difficulty score per position
   * Computed from *existing* signals only (no new models)
   * Stratified by conditioning axes (skill, time control, time pressure)

2. **HDI decomposition**

   * Component features exposed in reports
   * Clear attribution (entropy, move ambiguity, outcome sensitivity)

3. **Evaluation CLI completion**

   * Fully functional `--conditioned-metrics`
   * Fully enforced frozen-eval requirement for comparable runs

4. **Reporting & auditability**

   * HDI included in eval report v4 (additive)
   * Deterministic computation and golden tests

---

### Explicitly Out of Scope

* ❌ Training new policy models
* ❌ Engine (Stockfish) evaluation or labels
* ❌ Learning HDI weights from data
* ❌ Personality modeling
* ❌ UI or visualization
* ❌ Elo or rating recomputation

---

## Design Principles (Carry-Forward)

* **Derived, not learned** — HDI is a function, not a model
* **Human-centric** — measures cognitive difficulty, not optimality
* **Deterministic** — same inputs → same HDI
* **Explainable** — no black-box aggregation
* **Backward compatible** — all prior schemas remain valid

---

## Work Breakdown

---

### 1. Human Difficulty Index (HDI) v1

#### 1.1 HDI Definition

Define HDI as a normalized scalar in `[0.0, 1.0]` computed from:

| Component               | Source                             | Rationale             |
| ----------------------- | ---------------------------------- | --------------------- |
| Policy entropy          | existing policy output             | Measures ambiguity    |
| Top-gap (p1 − p2)       | policy distribution                | Measures decisiveness |
| Legal move count        | rules engine                       | Branching factor      |
| Human W/D/L sensitivity | outcome head (if present) or proxy | Consequence severity  |

**Rules:**

* All components must already exist in M06/M05 outputs
* No engine calls
* No learned weights (static coefficients only, documented)

---

#### 1.2 HDI Formula (Spec v1)

* Define a pure function:

  ```python
  compute_hdi_v1(features) -> float
  ```
* Normalize each component to `[0,1]`
* Combine via documented linear or capped sum
* Clamp final value to `[0,1]`

Add:

```json
"hdi": {
  "value": 0.73,
  "specVersion": 1,
  "components": {
    "entropy": 0.82,
    "topGap": 0.41,
    "legalMovePressure": 0.67,
    "outcomeSensitivity": 0.55
  }
}
```

---

### 2. Eval Report Schema v4 (Additive)

* New schema: `eval_report.v4.schema.json`
* v3 remains valid
* HDI included in:

  * `overall`
  * `bySkillBucketId`
  * `byTimeControlClass`
  * `byTimePressureBucket`

**No existing fields removed or renamed.**

---

### 3. CLI Completion (M06 Deferrals Closed)

#### 3.1 `--conditioned-metrics`

* Fully enable conditioned metrics aggregation
* Update CLI help text
* Add CLI smoke tests

#### 3.2 Frozen Eval Enforcement

* Any run claiming comparability **must** provide:

  ```bash
  --frozen-eval-manifest path/to/manifest.json
  ```
* CI fails if:

  * conditioned metrics requested without frozen eval
  * manifest hash mismatch

---

### 4. Testing & Verification

#### 4.1 Determinism Tests

* HDI golden tests (byte-stable)
* Repeated runs → identical HDI values

#### 4.2 Property Tests

* HDI increases with:

  * entropy ↑
  * top-gap ↓
* HDI stable under record ordering changes

#### 4.3 Regression Safety

* M05 and M06 reports still parse and validate
* Existing tests remain green

---

### 5. Documentation

Add:

* `docs/evaluation/M07_HDI.md`

  * What HDI is / is not
  * Interpretation guidance
  * Explicit non-claims

Update:

* Evaluation README to reference HDI availability

---

### 6. Audit & Closeout Artifacts

Cursor must generate:

* `M07_summary.md`
* `M07_audit.md`

Audit must explicitly assert:

* HDI is derived, not learned
* No engine dependency introduced
* CLI deferrals from M06 are fully closed
* CI enforcement strengthened, not weakened

---

## Exit Criteria (All Required)

* ✅ HDI computed deterministically
* ✅ HDI visible in eval report v4
* ✅ Conditioned CLI fully functional
* ✅ Frozen eval enforcement complete
* ✅ All tests green
* ✅ Backward compatibility preserved
* ✅ Audit + summary artifacts generated
* ✅ M07 marked CLOSED / IMMUTABLE

---

## Deferred Explicitly to M08+

* Training human policy baselines
* Outcome head learning
* Engine contrast
* Personality axes

---

## Governance Note

M07 completes the **evaluation substrate + difficulty abstraction**.
After this milestone, RenaceCHESS can **quantitatively say why a position is hard for humans**, not just whether a move was predicted correctly.

This is the last PoC milestone that does **not** introduce learning.

---

### Next Action

You can hand this plan directly to Cursor.

If you want, I can next:

* pre-answer Cursor’s likely clarifying questions for M07, or
* sketch the **M08 learning milestone** so we keep momentum without scope bleed.

Just say the word.













