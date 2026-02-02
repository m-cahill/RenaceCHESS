# 📌 Milestone Summary — M30: FROZEN-EVAL-SCALESET-001

**Project:** RenaceCHESS  
**Phase:** Phase E (Scale, Proof & Release Lock)  
**Milestone:** M30 — FROZEN-EVAL-SCALESET-001 (10k Synthetic Frozen Eval Set v2)  
**Timeframe:** 2026-02-02 → 2026-02-02  
**Status:** ✅ Closed (CI Green — Pending Merge Authorization)  

---

## 1. Milestone Objective

M30 establishes a **release-grade frozen evaluation set** for Phase E scale testing and calibration stability verification.

**Problem addressed:**
- The existing v1 frozen eval fixture (70 records) was a synthetic test artifact, insufficient for statistically meaningful calibration metrics (ECE, Brier, NLL)
- No production v2 dataset manifest exists yet (confirmed in M29 audit)
- M30 was explicitly forbidden from creating new ingestion pipelines (Phase isolation)

**Solution:**
- Generate a **10,000-position synthetic frozen eval set** that is:
  - Chess-valid (real positions, not random tensors)
  - Deterministically reproducible (fixed seed, canonical hashes)
  - Stratified by skill bucket (7 buckets, min 1,000 each)
  - Clearly labeled as synthetic for audit clarity

> **Audit statement:** "Frozen eval v2 is synthetic but chess-valid, and is intended for *relative* evaluation and calibration stability, not absolute strength claims."

---

## 2. Scope Definition

### In Scope

| Category | Items |
|----------|-------|
| **Schemas** | `FrozenEvalManifestV2`, `EvalSetProvenanceV1`, `FrozenEvalRecordV2`, `FrozenEvalStratificationV2` |
| **Modules** | `src/renacechess/frozen_eval/generator_v2.py` |
| **Artifacts** | `data/frozen_eval_v2/manifest.json`, `provenance.json`, 10 shard files |
| **CI** | `frozen-eval-v2-validation` job (schema + hash + shard integrity) |
| **Tests** | 29 new tests in `tests/test_m30_frozen_eval_v2.py` |
| **Governance** | `renacechess.md` milestone entry, versioned contracts section |

### Out of Scope

| Exclusion | Rationale |
|-----------|-----------|
| Production PGN ingestion | Explicitly forbidden by M30 plan |
| Real Lichess dataset | No production v2 manifest exists |
| Time-control stratification | Deferred (locked: skill-only stratification) |
| Multi-dimensional stratification | Deferred (avoids explosion complexity) |
| Evaluation runs in CI | Locked: CI limited to schema + hash validation |
| FrozenEvalManifestV1 modification | V2 is a clean replacement, V1 untouched |

---

## 3. Work Executed

### Schema & Models

- **4 new Pydantic models** added to `src/renacechess/contracts/models.py`:
  - `EvalSetProvenanceV1` — provenance/lineage artifact
  - `FrozenEvalRecordV2` — strict record schema (no "unknown" skill bucket)
  - `FrozenEvalStratificationV2` — stratification config
  - `FrozenEvalManifestV2` — release-grade manifest

- **2 JSON schemas** created:
  - `frozen_eval_manifest.v2.schema.json`
  - `eval_set_provenance.v1.schema.json`

### Generator Module

- Created `src/renacechess/frozen_eval/generator_v2.py`:
  - 40 curated FEN seeds (openings, middlegames, endgames)
  - Deterministic expansion to 10k positions
  - Round-robin skill bucket assignment (ensures minimum 1,000 per bucket)
  - Seeded random time control/pressure assignment
  - Provenance artifact generation with audit notes
  - Manifest generation with determinism hash

### Generated Dataset

- **Location:** `data/frozen_eval_v2/`
- **Contents:**
  - `manifest.json` — 10,000 positions, determinism hash verified
  - `provenance.json` — generator version, seed, audit notes
  - `shard_000.jsonl` through `shard_009.jsonl` — 1,000 positions each

### Stratification Results

| Skill Bucket | Count |
|--------------|-------|
| `lt_800` | 1,429 |
| `800_999` | 1,429 |
| `1000_1199` | 1,429 |
| `1200_1399` | 1,429 |
| `1400_1599` | 1,428 |
| `1600_1799` | 1,428 |
| `gte_1800` | 1,428 |
| **Total** | **10,000** |

### CI Integration

- Added `frozen-eval-v2-validation` job to `.github/workflows/ci.yml`:
  - Schema validation (FrozenEvalManifestV2, EvalSetProvenanceV1)
  - Determinism hash verification
  - Shard hash verification (all 10 shards)
  - Skill bucket minimum validation (≥1,000 each)
  - Position count validation (exactly 10,000)

---

## 4. Validation & Evidence

### Test Suite

| Metric | Value |
|--------|-------|
| New tests | 29 |
| Total tests | 901 passed, 1 skipped |
| Test file | `tests/test_m30_frozen_eval_v2.py` |

**Test categories:**
- Schema validation (FrozenEvalManifestV2, EvalSetProvenanceV1, FrozenEvalRecordV2)
- Generator correctness (position count, bucket distribution, shard creation)
- Determinism verification (same seed → same hash)
- Committed artifact validation (manifest exists, schema valid, hash valid)
- Constants verification (10k positions, 1k minimum, 7 buckets)

### Determinism Verification

```
Manifest hash: sha256:00a13e916d6b0a8770688e8623097f67b3224c4b32c64ce133785fda0a58e11f
verify_frozen_eval_v2() → True
```

**Note:** Hash regenerated after cross-platform line ending fix (commit 473be1c).

### Lint & Type Check

```
ruff check → All checks passed!
```

---

## 5. CI / Automation Impact

### New CI Job

| Job Name | Purpose | Gates |
|----------|---------|-------|
| `frozen-eval-v2-validation` | Validate M30 artifacts | Schema, hash, shard integrity, bucket minimums, position count |

### CI Posture (Locked Decision)

- **NO evaluation runs in CI** — only schema + hash validation
- Evaluation cost grows with set size; M31/M32 are the correct execution points

### Existing Jobs

- All existing jobs unaffected
- M26 runtime recalibration guard job continues to pass
- M27/M28 evaluation jobs remain functional

---

## 6. Issues & Exceptions

> **No new issues were introduced during this milestone.**

### Resolved During Implementation

| Issue | Resolution |
|-------|------------|
| Datetime serialization mismatch in hash computation | Fixed by using Pydantic's `model_dump(mode="json")` before hash computation |
| Unused variable `positions_per_bucket` | Removed after Ruff lint |

---

## 7. Deferred Work

| Deferred Item | Reason | Status |
|---------------|--------|--------|
| Time-control stratification enforcement | Locked decision: skill-only for M30 | New deferral |
| Time-pressure stratification enforcement | Locked decision: skill-only for M30 | New deferral |
| Real Lichess data eval set | No production v2 manifest; belongs in M31+ | Pre-existing |

**Deferred Issues Registry:** No active deferred issues (registry clean as of M29).

---

## 8. Governance Outcomes

### What Changed

| Before M30 | After M30 |
|------------|-----------|
| 70-record synthetic fixture (test-only) | 10,000-position release-grade eval set |
| No stratification guarantees | 7 skill buckets with 1,000+ minimum each |
| No provenance artifact | Full provenance with audit notes |
| No determinism verification | SHA-256 hash verification in CI |

### What Is Now Provably True

1. **Frozen eval v2 is deterministic** — same seed + timestamp → identical hash
2. **All skill buckets are represented** — minimum 1,000 positions each
3. **Shards are immutable** — hash verification prevents tampering
4. **Synthetic nature is explicit** — `synthetic: true` flag + audit notes

---

## 9. Exit Criteria Evaluation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| FrozenEvalManifestV2 schema defined | ✅ Met | `models.py`, JSON schema |
| EvalSetProvenanceV1 schema defined | ✅ Met | `models.py`, JSON schema |
| 10,000 positions generated | ✅ Met | `manifest.positionCount: 10000` |
| 7 skill buckets with min 1,000 each | ✅ Met | All buckets: 1,428-1,429 |
| Determinism hash verified | ✅ Met | `verify_frozen_eval_v2() → True` |
| CI validation job added | ✅ Met | `frozen-eval-v2-validation` job |
| No evaluation runs in CI | ✅ Met | Job limited to schema + hash |
| Tests passing | ✅ Met | 29 new tests, 901 total passing |

---

## 10. Final Verdict

**✅ Milestone objectives met. CI verification complete. Awaiting merge authorization.**

**CI Run:** 21610395623  
**All 10 jobs passed**, including the new `frozen-eval-v2-validation` job.

The frozen eval v2 set is:
- Correctly sized (10,000 positions)
- Properly stratified (7 buckets, 1,000+ each)
- Deterministically reproducible (fixed seed, verified hash)
- Clearly labeled as synthetic (audit compliance)
- CI-validated (schema + hash + shard integrity)

---

## 11. Authorized Next Step

**Immediate:**
- ✅ PR created (#35)
- ✅ CI run completed (21610395623)
- ⏳ Await merge authorization (per workflow rules)

**After M30 closure:**
- M31 (FULL-TRAINING-RUN-001) — Use frozen eval v2 as the calibration ruler
- M32 (POST-TRAIN-EVAL-PACK-001) — Compare trained model against frozen eval v2

---

## 12. Canonical References

| Artifact | Location |
|----------|----------|
| M30 Plan | `docs/milestones/PhaseE/M30/M30_plan.md` |
| Tool Calls Log | `docs/milestones/PhaseE/M30/M30_toolcalls.md` |
| Manifest Schema | `src/renacechess/contracts/schemas/v1/frozen_eval_manifest.v2.schema.json` |
| Provenance Schema | `src/renacechess/contracts/schemas/v1/eval_set_provenance.v1.schema.json` |
| Generator | `src/renacechess/frozen_eval/generator_v2.py` |
| Frozen Eval Data | `data/frozen_eval_v2/` |
| Tests | `tests/test_m30_frozen_eval_v2.py` |
| CI Workflow | `.github/workflows/ci.yml` (frozen-eval-v2-validation job) |
| Source of Truth | `renacechess.md` (M30 entry) |

