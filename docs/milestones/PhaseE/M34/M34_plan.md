# 🔒 M34 — RELEASE-LOCK-001 (Phase E Closeout)

**Phase:** E (Scale Proof, Training Run, Release Lock)  
**Predecessors:**
- M29 — GPU Benchmarking (✅ closed)
- M30 — Frozen Eval v2 (✅ closed)
- M31 — Full Training Run (✅ closed)
- M32 — Post-Train Eval Pack (✅ closed)
- M33 — External Proof Pack (✅ closed)

---

## 🎯 Single Objective (Lock This)

> **Formally lock RenaceCHESS v1 as a *truthful, auditable, immutable research release*.**

M34 **adds no new capability**. It only freezes, tags, and certifies what already exists.

This milestone makes future dishonesty impossible.

---

## 🚫 Hard Constraints (Non-Negotiable)

* 🚫 No new features
* 🚫 No new schemas
* 🚫 No new dependencies
* 🚫 No code changes (except release infrastructure)
* 🚫 No reinterpretation of results
* 🚫 No "spin" on limitations

M34 **freezes reality exactly as it is**.

---

## 📥 Inputs (All Frozen)

| Source | Artifact |
|--------|----------|
| M30 | FrozenEval v2 manifest + provenance |
| M31 | TrainingConfigLockV1, TrainingRunReportV1 |
| M32 | PostTrainEvalReportV1 + metric packs |
| M33 | ExternalProofPackV1 + proof_pack_v1/ |
| Repo | All v1 schemas + commit SHAs |

Nothing new is generated. Everything is already committed.

---

## 📤 Outputs (What M34 Produces)

### 1. **Contract Registry** (NEW)

`contracts/CONTRACT_REGISTRY_v1.json` — Immutable inventory of all v1 contracts:

```json
{
  "schemaVersion": 1,
  "frozenAt": "2026-02-03T...",
  "contracts": [
    {
      "filename": "frozen_eval_manifest.v2.schema.json",
      "schemaHash": "sha256:...",
      "introducedMilestone": "M30",
      "purpose": "Frozen evaluation set manifest v2",
      "pydanticModel": "FrozenEvalManifestV2"
    },
    ...
  ]
}
```

### 2. **Release Artifacts**

* ✅ **Annotated Git tag:** `v1.0.0-renacechess`
* ✅ **Release notes:** `RELEASE_NOTES_v1.md`
* ✅ **Phase E closeout:** `docs/phases/PhaseE_closeout.md`
* ✅ **Updated governance:** `renacechess.md` (M34 entry, Phase E status)

### 3. **CI Release Gates** (NEW)

Three new release-blocking CI jobs:

1. **`release-dependency-freeze`** — Fails if dependencies change
2. **`release-contract-freeze`** — Fails if v1 contracts change
3. **`release-proof-pack-verification`** — Verifies M33 proof pack integrity

---

## 🧠 What M34 Proves (Explicit Claims)

M34 may claim **only**:

1. **Immutable Release**
   All v1 contracts are frozen and cannot drift.

2. **Complete Audit Trail**
   Every artifact is hash-verified and traceable.

3. **Research-Grade Release**
   This is a complete, reproducible research system, not a product.

4. **Future-Proof Evolution**
   Any future changes require explicit v2+ versioning.

It does **not** claim:
* Production readiness
* Commercial viability
* Performance superiority
* Feature completeness

---

## 🧪 CI Role (Release Enforcement)

### New Release Gates

1. **`release-dependency-freeze`**
   - Validates `pyproject.toml` and `requirements*.txt` unchanged
   - Fails on any dependency addition/modification

2. **`release-contract-freeze`**
   - Validates `contracts/schemas/v1/*.json` unchanged
   - Validates `contracts/models.py` v1 models unchanged
   - Compares schema hashes against registry

3. **`release-proof-pack-verification`**
   - Verifies `proof_pack_v1/` exists
   - Validates proof pack manifest hash
   - Ensures all referenced artifacts present

### Explicitly NOT Added

* No performance checks
* No training/eval runs
* No GPU jobs
* No new test suites

CI becomes a **legal-style enforcement layer**, not a test runner.

---

## 🗂️ Files & Structure

```
contracts/
├── CONTRACT_REGISTRY_v1.json          # NEW — Immutable contract inventory
└── schemas/v1/                         # FROZEN — No changes allowed

src/renacechess/contracts/
├── registry.py                         # NEW — Registry generator/validator
└── models.py                           # FROZEN — v1 models unchanged

.github/workflows/
└── ci.yml                              # MODIFIED — Add release gates

docs/
├── phases/
│   └── PhaseE_closeout.md              # NEW — Phase E formal closeout
├── milestones/PhaseE/M34/
│   ├── M34_plan.md                    # This document
│   ├── M34_toolcalls.md               # Execution log
│   ├── M34_summary.md                 # Post-merge narrative
│   └── M34_audit.md                   # Formal closeout audit
└── RELEASE_NOTES_v1.md                # NEW — v1 release notes

renacechess.md                          # MODIFIED — M34 entry, Phase E status
README.md                               # MODIFIED — Add "What this is/is not"
```

---

## 🧾 Step-by-Step Execution Plan

### Phase 1 — Planning & Scaffolding ✅

* [x] Create M34 directory structure
* [x] Draft M34 plan document
* [x] Initialize toolcalls log
* [ ] Draft contract registry structure
* [ ] Add CI release gates (failing initially)

### Phase 2 — Release Preparation

* [ ] Generate contract registry from existing schemas
* [ ] Finalize README updates
* [ ] Draft release notes
* [ ] Lock contract registry (commit with hash)

### Phase 3 — Tag & Lock

* [ ] Create annotated git tag `v1.0.0-renacechess`
* [ ] Verify tag → commit → CI alignment
* [ ] Enable branch protection (if not already)

### Phase 4 — Closeout

* [ ] Generate `M34_summary.md`
* [ ] Generate `M34_audit.md`
* [ ] Update `renacechess.md` (M34 entry, Phase E closed)
* [ ] Generate `PhaseE_closeout.md`
* [ ] Declare Phase E **CLOSED**

---

## ✅ Exit Criteria (M34 Can Close When…)

* [ ] Contract registry generated and committed
* [ ] All v1 schemas inventoried with hashes
* [ ] CI release gates added and passing
* [ ] Git tag `v1.0.0-renacechess` created
* [ ] Release notes written
* [ ] Phase E closeout document written
* [ ] `renacechess.md` updated (M34 closed, Phase E closed)
* [ ] README updated with "What this is/is not"
* [ ] Proof pack verified in CI
* [ ] All documentation finalized
* [ ] Audit and summary written
* [ ] No open deferred issues

---

## 🔒 Why M34 Is the Real "Public Moment"

After M34, you can hand someone:

* a git tag,
* a proof pack,
* a contract registry,
* and hashes —

…and they can verify everything **without trusting you**.

That's rare. And that's the point.

---

## 📋 Phase E Definition of Done

Phase E is **DONE** when *all* of the following are true:

| Requirement | Status |
|-------------|--------|
| M29–M34 closed | 🚧 In Progress |
| CI green with release gates | ⏳ Pending |
| v1 tag exists | ⏳ Pending |
| Contracts frozen | ⏳ Pending |
| Proof pack built & verified | ✅ Complete (M33) |
| Phase E closeout written | ⏳ Pending |
| No open deferred issues | ✅ Verified |

Only then may Phase E be marked **CLOSED**.

---

## 👉 Next Action

Proceed with Phase 1 implementation:
1. Create contract registry generator
2. Add CI release gates
3. Test gates fail correctly (as intended)

