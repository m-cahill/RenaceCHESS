Fantastic — M31 is **cleanly closed with execution success**. We’re in the fun part now.
Here’s a **Cursor-ready, governance-tight plan for M32** that builds directly on the artifacts you just produced.

---

# 📌 M32 — POST-TRAIN-EVAL-PACK-001

**Phase:** Phase E (Final)
**Predecessor:** M31 — Full Training Run (✅ executed)
**Successor:** M33 — External Proof Pack

---

## 🎯 Single Objective (Lock This In)

**M32 exists to evaluate the trained M31 model(s) against the frozen eval v2 set and produce a canonical, reproducible post-training evaluation pack.**

This is where we answer:

> *“What did training actually change, and can we prove it cleanly?”*

No new training. No tuning. No architecture changes.

---

## 🚫 Hard Constraints (Non-Negotiable)

* 🚫 **No retraining**
* 🚫 **No hyperparameter changes**
* 🚫 **No model edits**
* 🚫 **No calibration fitting**
* 🚫 **No runtime behavior changes**
* 🚫 **No CI execution of evaluation loops**

M32 is **read-only evaluation** over frozen artifacts.

---

## 📦 Inputs (All Already Exist)

| Artifact                 | Source        |
| ------------------------ | ------------- |
| Final policy checkpoint  | M31 execution |
| Final outcome checkpoint | M31 execution |
| Frozen eval set v2 (10k) | M30           |
| TrainingRunReportV1      | M31           |
| TrainingConfigLockV1     | M31           |
| Code commit SHA          | M31           |

---

## 📤 Outputs (What M32 Produces)

### 1. **PostTrainEvalReportV1** (NEW)

Canonical, schema-validated evaluation summary.

Includes:

* Model identifiers (policy + outcome)
* Frozen eval manifest hash
* Commit SHA
* Evaluation metrics (see below)
* Determinism hash

---

### 2. **Metric Packs (JSON, machine-readable)**

Each as a standalone artifact:

| Pack                     | Metrics                                  |
| ------------------------ | ---------------------------------------- |
| **PolicyEvalMetricsV1**  | Top-1 accuracy, top-k agreement, entropy |
| **OutcomeEvalMetricsV1** | W/D/L accuracy, Brier, NLL               |
| **CalibrationMetricsV1** | ECE, reliability bins                    |
| **DeltaMetricsV1**       | Trained vs baseline deltas               |

> ⚠️ **Important:**
> Calibration is *measured*, **not recalibrated**.
> Temperature scaling remains untouched.

---

### 3. **Frozen Eval Integrity Proof**

* Confirms:

  * No overlap with training set
  * Correct V2 loading via compat layer
  * Deterministic iteration order
* Emits:

  * Hashes
  * Record counts
  * Bucket coverage

---

## 🧠 What Gets Evaluated (Explicit Scope)

### Policy Head

* Agreement with frozen eval labels
* Distribution shape (entropy)
* Bucket-level behavior (skill bands)

### Outcome Head

* W/D/L accuracy
* Calibration quality (ECE, Brier, NLL)
* Skill-conditioned deltas

### Baseline Comparison

* Compare **trained** vs **untrained baseline**:

  * Same frozen eval
  * Same metrics
  * Same code path

This is the *proof* that training mattered (or didn’t).

---

## 🧪 CI Role (Validation Only)

Add **one additive CI job**:

### `m32-eval-pack-validation`

CI must:

* Validate all new schemas
* Validate artifact JSON against schemas
* Verify determinism hashes
* Ensure no execution of eval loops

CI must **not**:

* Load checkpoints
* Run evaluation
* Touch GPU code

---

## 🗂️ Files & Structure (Cursor-Friendly)

```
src/renacechess/eval/
├── post_train_eval.py        # Evaluation orchestrator
├── policy_metrics.py         # Policy metrics
├── outcome_metrics.py        # Outcome metrics
├── calibration_metrics.py    # ECE/Brier/NLL
├── delta_metrics.py          # Baseline vs trained
└── __init__.py

contracts/
├── schemas/v1/
│   ├── post_train_eval_report.v1.schema.json
│   ├── policy_eval_metrics.v1.schema.json
│   ├── outcome_eval_metrics.v1.schema.json
│   ├── calibration_metrics.v1.schema.json
│   └── delta_metrics.v1.schema.json
└── models.py (append Pydantic models)

tests/
├── test_m32_eval_metrics.py
├── test_m32_eval_report_schema.py
└── test_m32_delta_logic.py

docs/milestones/PhaseE/M32/
├── M32_plan.md
├── M32_toolcalls.md
├── M32_summary.md
└── M32_audit.md
```

---

## 🧾 Step-by-Step Execution Plan (What Cursor Should Do)

### Phase 1 — Schema Definition

* Define all M32 schemas first
* Add Pydantic models
* Enforce canonical JSON + hashing

### Phase 2 — Metric Implementations

* Implement metric calculators (pure functions)
* No side effects
* No checkpoint mutation

### Phase 3 — Evaluation Orchestrator

* Load checkpoints (local only)
* Load frozen eval v2 via compat loader
* Emit all metric packs + report

### Phase 4 — Tests

* Schema validation tests
* Deterministic metric tests (fixed inputs)
* Delta logic tests

### Phase 5 — CI Hook

* Add validation-only job
* Ensure zero GPU invocation

---

## ✅ Exit Criteria (M32 Can Close When…)

* [ ] All schemas exist and validate
* [ ] Evaluation runs end-to-end locally
* [ ] Trained vs baseline deltas are produced
* [ ] Frozen eval integrity proven
* [ ] CI green (validation only)
* [ ] Summary + audit written

---

## 🔒 Governance Notes (Why M32 Matters)

M32 is the **evidence layer**:

* M31 proved *we can train*
* **M32 proves what training did**
* M33 packages that proof for outsiders

After M32, the project is no longer “promising” — it’s **demonstrated**.

---

## 👉 Next Action

If you want, I can:

* Generate a **Cursor prompt** that starts M32 Phase 1 (schemas)
* Or draft the **exact schema definitions** for PostTrainEvalReportV1
* Or sanity-check which metrics are worth keeping vs noise

Just say the word.
