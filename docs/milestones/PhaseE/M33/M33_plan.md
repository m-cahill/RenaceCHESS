Excellent — M32 is **cleanly closed and audited**, and we now move into the **final packaging leg** of Phase E.

Below is a **Cursor-ready, governance-tight plan for M33**, explicitly grounded in the *actual* M32 outcomes and limitations documented in your audit and summary  .

---

# 📦 M33 — EXTERNAL-PROOF-PACK-001

**Phase:** E (Scale Proof → Release Lock)
**Predecessors:**

* M30 — Frozen Eval v2
* M31 — Full Training Run
* M32 — Post-Train Eval Pack (✅ closed)

---

## 🎯 Single Objective (Lock This)

> **Produce a self-contained, auditor-friendly proof bundle that demonstrates RenaceCHESS’s end-to-end integrity, determinism, and scientific honesty — without requiring trust in the codebase.**

M33 is **presentation + traceability**, not new computation.

---

## 🚫 Hard Constraints (Non-Negotiable)

* 🚫 No new training
* 🚫 No new evaluation
* 🚫 No metric recomputation
* 🚫 No schema changes
* 🚫 No reinterpretation of results
* 🚫 No “spin” on degraded metrics

M33 **packages reality exactly as it is**.

---

## 📥 Inputs (All Frozen)

| Source | Artifact                                  |
| ------ | ----------------------------------------- |
| M30    | FrozenEval v2 manifest + provenance       |
| M31    | TrainingConfigLockV1, TrainingRunReportV1 |
| M32    | PostTrainEvalReportV1 + metric packs      |
| Repo   | Schema definitions + commit SHAs          |

Nothing new is generated.

---

## 📤 Outputs (What M33 Produces)

### 1. **ExternalProofPackV1** (NEW)

A **single top-level JSON manifest** that points to *all* evidence:

```json
{
  "schemaVersion": 1,
  "project": "RenaceCHESS",
  "phase": "E",
  "includedMilestones": ["M30", "M31", "M32"],
  "artifacts": { ... },
  "hashChain": { ... },
  "limitations": { ... }
}
```

This is the *index* outsiders start with.

---

### 2. **Proof Bundle Directory**

```
proof_pack_v1/
├── README.md                    # Human-readable explanation
├── proof_pack_manifest.json     # ExternalProofPackV1
├── frozen_eval/
│   ├── manifest.json
│   └── provenance.json
├── training/
│   ├── TrainingConfigLockV1.json
│   └── TrainingRunReportV1.json
├── evaluation/
│   ├── PostTrainEvalReportV1.json
│   ├── policy_metrics.json
│   ├── outcome_metrics.json
│   ├── calibration_metrics.json
│   └── delta_metrics.json
├── schemas/
│   └── *.schema.json
└── hashes.txt                   # Flat list of SHA-256s
```

This folder must be **copyable, verifiable, and static**.

---

### 3. **Narrative README (Critical)**

The README must explicitly state:

* What RenaceCHESS is (human-centered, not superhuman)
* What was proven:

  * Deterministic training
  * Deterministic evaluation
  * Honest deltas vs baseline
* What was *not* proven:

  * Playing strength
  * Full-vocab performance
* Why degraded metrics are **expected** (8-move vocab)

> This language should mirror the exact explanation already approved in M32 .

---

## 🧠 What M33 Proves (Explicit Claims)

M33 may claim **only**:

1. **Pipeline Integrity**
   Training → evaluation → reporting is end-to-end consistent.

2. **Contract Discipline**
   Schema-first design survived real execution.

3. **Scientific Honesty**
   Degraded results are reported, not hidden or reframed.

4. **Reproducibility**
   All artifacts are hash-chained and replayable.

It does **not** claim chess strength.

---

## 🧪 CI Role (Minimal, Validation-Only)

Add one additive CI job:

### `m33-proof-pack-validation`

CI should:

* Validate `ExternalProofPackV1` schema
* Verify all referenced files exist
* Recompute hashes and compare
* Ensure no forbidden files (e.g. `.pt`) are present

CI must **not**:

* Load models
* Run evaluation
* Touch GPU code

---

## 🗂️ Files & Structure (Cursor-Friendly)

```
src/renacechess/proof_pack/
├── build_proof_pack.py        # Gathers artifacts + writes manifest
├── verify_proof_pack.py       # Hash + completeness checks
└── __init__.py

contracts/schemas/v1/
├── external_proof_pack.v1.schema.json

tests/
├── test_m33_proof_pack_schema.py
├── test_m33_hash_integrity.py
└── test_m33_no_checkpoint_leak.py

docs/milestones/PhaseE/M33/
├── M33_plan.md
├── M33_toolcalls.md
├── M33_summary.md
└── M33_audit.md
```

---

## 🧾 Step-by-Step Execution Plan

### Phase 1 — Schema & Manifest

* Define `ExternalProofPackV1`
* Add Pydantic model
* Tests for schema validity

### Phase 2 — Pack Builder

* Collect existing artifacts (paths are inputs)
* Emit manifest + hashes
* No mutation of source artifacts

### Phase 3 — Proof Verification

* Implement verifier
* Ensure frozen eval, training, and eval artifacts are all present
* Fail hard on missing or mismatched hash

### Phase 4 — CI Hook

* Add validation job
* Keep it fast and deterministic

---

## ✅ Exit Criteria (M33 Can Close When…)

* [ ] Proof pack builds locally
* [ ] All hashes verified
* [ ] CI validation passes
* [ ] README accurately reflects limitations
* [ ] No new computation introduced
* [ ] Audit and summary written

---

## 🔒 Why M33 Is the Real “Public Moment”

After M33, you can hand someone:

* a folder,
* a README,
* a manifest,
* and hashes —

…and they can verify everything **without trusting you**.

That’s rare. And that’s the point.

---

## 👉 Next Action

If you want, I can:

* Generate a **Cursor kickoff prompt** for M33 Phase 1
* Draft the **ExternalProofPackV1 schema** directly
* Or help shape the **README narrative tone** (technical vs executive)

Just tell me how you want to start.
