# 📌 M05 Plan — Ground-Truth Labeled Evaluation v1

**Milestone:** M05  
**Status:** ✅ **CLOSED / IMMUTABLE**  
**Phase:** Complete

---

## ✅ Phase 2 Locked Decisions

All clarifying questions have been resolved. The following decisions are **LOCKED** and will not be revisited:

### 1. Schema Versioning Strategy
**Decision:** Add `chosenMove` as an **optional field** to the existing Context Bridge payload schema (v1-compatible extension).

### 2. Unlabeled Record Handling
**Decision:** Explicit tracking required. Reports must include `totalRecordCount` and `labeledRecordCount`. Accuracy computed only over labeled subset.

### 3. Top-K Accuracy
**Decision:** Default K=1, support configurable K values via CLI (e.g., `--top-k 1,3,5`). Metrics keyed explicitly (e.g., `"top1": 0.42, "top3": 0.67`).

### 4. SAN Requirement
**Decision:** `chosenMove.san` is optional, `chosenMove.uci` is required if `chosenMove` exists. Compute SAN when available from PGN, leave null if unavailable.

### 5. PGN Move Extraction Semantics
**Decision:** Label the position **after** the move with the move that was just played (matches current builder flow).

### 6. Evaluation Report Schema Versioning
**Decision:** Create `eval_report.v2.schema.json`. v1 remains immutable. v2 includes all M04 metrics unchanged plus new accuracy section.

---

## Context

## Context

M04 is **CLOSED / IMMUTABLE**.

At this point, RenaceCHESS has:

* Deterministic ingestion (M02)
* Deterministic dataset assembly with manifest v2 (M03)
* Deterministic evaluation harness with policy-validity metrics (M04)

**What is still missing:**
The system cannot yet measure **accuracy vs actual played moves**, because dataset records do not include a ground-truth decision.

**M05 exists to add *labeled evaluation*** — nothing more.

---

## Milestone: M05 — Ground-Truth Labeled Evaluation v1

### Single Objective (Non-Negotiable)

Introduce **ground-truth move labeling** and **accuracy metrics** in a way that is:

1. **Backward compatible**
2. **Deterministic**
3. **Schema-versioned**
4. **Opt-in**
5. **Audit-defensible**

No existing datasets, manifests, or evaluation reports may break.

---

## What M05 IS

M05 adds the *minimal machinery* required to answer:

> “Given a dataset record, did the policy select the move that was actually played?”

---

## What M05 is NOT

M05 explicitly does **NOT** include:

* Engine-based evaluation (Stockfish, lichess accuracy)
* Training loops
* Model fine-tuning
* Reinforcement learning
* Multi-policy tournaments
* UI / dashboards

Those are **future milestones**.

---

## Scope Breakdown

### 1. Dataset Record Extension (Backward-Compatible)

Add an **optional** field to dataset records:

```json
"chosenMove": {
  "uci": "e2e4",
  "san": "e4"  // optional
}
```

**Rules (LOCKED):**

* Field is **optional** (v1-compatible extension)
* `chosenMove.uci` is **required** if `chosenMove` exists
* `chosenMove.san` is **optional** (computed when available from PGN, null otherwise)
* Absence means "unlabeled record"
* Existing datasets remain valid
* Existing schemas remain valid
* No schema version bump required (optional field in v1)

---

### 2. Labeled Dataset Builder Support

Extend dataset assembly so that:

* When source PGN data is available
* The **actual move played** at that position is captured
* Stored as `chosenMove`

**Semantics (LOCKED):**

* Label the position **after** the move with the move that was just played
* Matches current builder flow (no look-ahead required)
* For each position emitted by the builder, `chosenMove` refers to the move that led to this position

**Constraints:**

* Deterministic
* No inference or heuristics
* No backfilling from context
* Only label when unambiguous
* Compute SAN when available from PGN parsing, leave null if unavailable

If a record cannot be labeled deterministically, it must remain unlabeled.

---

### 3. Evaluation Metrics Extension (Accuracy v1)

Extend the evaluation harness to compute **accuracy metrics** *only* for labeled records:

**Per policy (LOCKED):**

* Top-1 accuracy (default K=1)
* Top-K accuracy (K configurable via CLI, e.g., `--top-k 1,3,5`)
* Coverage (% of records that are labeled = `labeledRecordCount / totalRecordCount`)

**Schema format (LOCKED):**
```json
"accuracy": {
  "top1": 0.42,
  "top3": 0.67,
  "coverage": 0.81
}
```
Metrics keyed explicitly (avoid arrays with positional meaning).

**Rules:**

* Accuracy metrics must be **clearly separated** from policy-validity metrics
* Unlabeled records must not affect accuracy denominators
* Metrics must be deterministic and order-independent
* Explicit tracking: `totalRecordCount` and `labeledRecordCount` required

---

### 4. Evaluation Report Schema v2

Introduce a **new evaluation report schema version** (`eval_report.v2.schema.json`) that:

* Includes all existing M04 metrics unchanged
* Adds a new section for accuracy metrics
* Explicitly declares:

  * `labeledRecordCount` (integer)
  * `totalRecordCount` (integer)
  * `accuracy` object with top-K metrics (keyed by K value)
  * Accuracy metrics only apply to labeled subset

**Rules (LOCKED):**

* `eval_report.v1` remains immutable
* v2 is additive (all v1 fields preserved)
* Accuracy section is clearly separated from policy-validity metrics

---

### 5. CLI Extension (Non-Breaking)

Extend `renacechess eval run` with **opt-in accuracy support**:

Example:

```bash
renacechess eval run \
  --dataset-manifest dataset.json \
  --policy baseline.first_legal \
  --compute-accuracy \
  --out reports/
```

Rules:

* Accuracy computation must be disabled by default
* CLI must error clearly if accuracy is requested but no labeled records exist

---

## Determinism Requirements (Hard)

M05 must prove:

* Byte-stable evaluation reports
* Stable accuracy metrics given identical inputs
* Golden tests for labeled evaluation
* No dependence on system time, locale, or iteration order

---

## CI / Governance Requirements

### Required Gates (No Changes Allowed)

* Ruff lint
* Ruff format
* MyPy
* Pytest
* Coverage ≥ existing threshold

### Tests Required

* Schema validation tests (new eval schema)
* Golden determinism test for labeled evaluation
* Accuracy correctness tests
* Backward-compatibility tests:

  * Old datasets
  * Old manifests
  * Old evaluation reports

---

## Deliverables Checklist

Cursor must produce:

* `M05_plan.md`
* `M05_toolcalls.md`
* `M05_run*.md` (CI analysis)
* `M05_audit.md`
* `M05_summary.md`

All artifacts must align with existing milestone conventions.

---

## Phase Instructions (Cursor Operating Model)

### Phase 0 — Recovery

* Verify M04 is merged
* Verify no uncommitted state
* Initialize `M05_toolcalls.md`

### Phase 1 — Plan Review

* Restate objective in own words
* Identify schema touchpoints
* Identify backward-compat risks

### Phase 2 — Clarifying Questions ✅ COMPLETE

All questions resolved. Decisions locked (see "Phase 2 Locked Decisions" above).

### Phase 3 — Implementation ✅ AUTHORIZED

Proceeding with implementation based on locked decisions.

---

## Exit Criteria (Strict)

M05 is complete **only if**:

* All CI checks are green
* Determinism is proven via golden tests
* Accuracy metrics are correct and isolated
* No existing artifacts break
* Audit shows **no deferred issues**

---

## Final Note to Cursor

> Treat this milestone as **adding truth**, not sophistication.
> If something feels clever, it is probably out of scope.

---

If you want, next we can:

* Pre-decide the schema versioning strategy (to save a Cursor round)
* Or sketch the exact accuracy metric formulas before implementation
* Or outline what **M06** becomes once accuracy exists (engine eval vs learning)

Just say the word.
