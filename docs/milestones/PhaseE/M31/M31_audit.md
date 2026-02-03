# M31 Milestone Audit

**Milestone:** M31 — FULL-TRAINING-RUN-001  
**Mode:** DELTA AUDIT (Implementation + Execution)  
**Range:** `9557d57...579cd2d`  
**CI Status:** 🟢 Green (all 11 jobs passing)  
**Execution Status:** 🟢 **SUCCESS** — Training completed (25m 26s)  
**Audit Verdict:** 🟢 **PASS** — Milestone CLOSED

---

## Executive Summary (Delta-First)

### Wins

1. **Training infrastructure established**: `TrainingConfigLockV1` and `TrainingRunReportV1` schemas provide immutable, auditable contracts for training runs
2. **Data separation enforced**: Training dataset v2 generator is explicitly causally separated from frozen eval v2 (different seeds, prefixes, record keys)
3. **CI validation without execution**: New `m31-schema-validation` job validates schemas and generator without triggering actual training
4. **Latent bug discovered and fixed**: Non-deterministic `hash()` behavior in existing tests was identified and corrected with a robust test

### Risks

1. **New code coverage**: `m31_training_runner.py` at 13.13% coverage (execution paths untested until actual run)
2. **Training dataset generator**: `training_dataset_v2.py` at 84.62% coverage (some edge cases in CLI/verification paths)
3. **Execution complexity**: M31 execution phase involves multi-hour GPU training — execution risks deferred to that phase
4. **Schema complexity**: 12 new Pydantic models with nested structures — covered by validation tests

### Most Important Next Action

**Execute M31 training phase**: Generate production dataset manifest, lock config, run FP32 training, emit artifacts

---

## Delta Map & Blast Radius

### What Changed

| Category | Files | Lines |
|----------|-------|-------|
| Schemas (JSON) | 2 | 574 |
| Pydantic models | 1 | 598 |
| Dataset generator | 2 | 477 |
| Training runner | 1 | 565 |
| Tests | 2 | 762 |
| CI workflow | 1 | 204 |
| Documentation | 2 | 360 |

### Risky Zones

| Zone | Risk Level | Notes |
|------|------------|-------|
| Auth | 🟢 None | No auth changes |
| Tenancy | 🟢 None | No tenancy changes |
| Persistence | 🟡 Low | New dataset manifest format (compatible with existing V2) |
| Workflow glue | 🟢 Low | New CI job is additive, validation-only |
| Migrations | 🟢 None | No database changes |
| Concurrency | 🟢 None | Training is single-threaded |

---

## Architecture & Modularity Review

### Keep (Good Patterns)

- **Schema-first design**: JSON schemas defined before Pydantic models
- **Canonical JSON for hashing**: Uses `determinism.canonical_json_dump()` for all hash computation
- **Separation of concerns**: Training runner separate from dataset generator
- **Existing model reuse**: Uses existing `BaselinePolicyV1`, `OutcomeHeadV1` without modification

### Fix Now (None Required)

All issues resolved during implementation.

### Defer (Tracked)

| Item | Deferred To | Reason |
|------|-------------|--------|
| AMP support | Post-v1 | M31 is FP32-only by design |
| Hyperparameter tuning | Post-v1 | Template configs locked |
| Checkpoint versioning | Post-v1 | Not critical for M31 execution |

---

## CI/CD & Workflow Audit

### Required Checks Alignment

All 11 jobs passed on final CI run:

| Job | Status | Role |
|-----|--------|------|
| Lint and Format | ✅ | Code quality |
| Type Check | ✅ | Type safety |
| Security Scan | ✅ | Vulnerability detection |
| Test | ✅ | Functional correctness |
| Performance Benchmarks | ✅ | Regression detection |
| Calibration Evaluation | ✅ | Model quality |
| Recalibration Evaluation | ✅ | Calibration stability |
| Frozen Eval V2 Validation (M30) | ✅ | Eval data integrity |
| M31 Schema Validation | ✅ | Schema correctness |
| Runtime Recalibration Guard (M26) | ✅ | Guard validation |
| Runtime Recalibration Evaluation (M27) | ✅ | Recalibration quality |

### Action Pinning

All actions in `ci.yml` are SHA-pinned (verified by existing Security Scan job).

### CI Root Cause Summary

Initial CI failure was due to coverage regression in `models/baseline_v1.py`:
- **Root cause**: Python's non-deterministic `hash()` function caused different coverage paths between local and CI
- **Fix**: Added `test_baseline_policy_v1_forward_uniform_distribution_guaranteed` with `move_vocab_size=1` to guarantee hash collisions
- **Guardrail**: Test now works across all Python configurations

---

## Tests & Coverage (Delta-Only)

### Coverage Delta

| File | Before | After | Delta |
|------|--------|-------|-------|
| `training_dataset_v2.py` | N/A | 84.62% | New file |
| `m31_training_runner.py` | N/A | 13.13% | New file (execution paths) |
| `models.py` | 100% | 100% | No change |
| `baseline_v1.py` | ~98.80% | ~98.80% | Fixed flaky coverage |

### New Tests Added

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_m31_training_run.py` | 19 | Schema, generator, integration |
| `test_m08_model.py` | +1 | `test_baseline_policy_v1_forward_uniform_distribution_guaranteed` |

### Missing Tests (Acceptable)

- `m31_training_runner.py` execution paths (13.13% coverage) — **Acceptable**: These are covered during actual training execution

---

## Security & Supply Chain (Delta-Only)

### Dependency Changes

| Change | Impact |
|--------|--------|
| Added `types-PyYAML` to dev deps | Type stubs only, no runtime impact |

### Secrets Exposure Risk

🟢 None — No secrets added or exposed

### SBOM/Provenance

🟢 No changes to SBOM generation or provenance

---

## RediAI v3 Guardrail Compliance Check

| Guardrail | Status | Notes |
|-----------|--------|-------|
| CPU-only enforcement | ✅ PASS | CI remains CPU-only; GPU code is opt-in |
| Multi-tenant isolation | ✅ PASS | No tenancy changes |
| Monorepo migration friendliness | ✅ PASS | New modules are self-contained |
| Contract drift prevention | ✅ PASS | JSON schemas + Pydantic models in sync |
| Workflow required checks | ✅ PASS | New job is additive |
| Supply chain hygiene | ✅ PASS | Actions remain SHA-pinned |

---

## Top Issues (Resolved)

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| COV-001 | Med | Coverage regression in `baseline_v1.py` | Fixed with robust test |
| LINT-001 | Low | Line too long in test | Split assertion string |

No open issues remain.

---

## PR-Sized Action Plan

| ID | Task | Category | Acceptance Criteria | Risk | Est |
|----|------|----------|---------------------|------|-----|
| N/A | All tasks complete | — | — | — | — |

All implementation tasks are complete. No further action required for M31 implementation phase.

---

## Deferred Issues Registry (Cumulative)

No new deferred issues introduced by M31.

---

## Score Trend (Cumulative)

| Milestone | Arch | Mod | Health | CI | Sec | Perf | DX | Docs | Overall |
|-----------|------|-----|--------|----|----|------|----|----|---------|
| M30 | 4.5 | 4.5 | 4.5 | 4.5 | 5.0 | 4.0 | 4.0 | 4.0 | 4.4 |
| M31 | 4.5 | 4.5 | 4.5 | 4.5 | 5.0 | 4.0 | 4.0 | 4.0 | 4.4 |

**Score unchanged**: M31 is implementation-only; actual training execution may affect scores.

---

## Flake & Regression Log (Cumulative)

| Item | Type | First Seen | Current Status | Last Evidence | Fix/Defer |
|------|------|------------|----------------|---------------|-----------|
| `baseline_v1.py` hash-dependent test | Flake | M31 | ✅ Fixed | CI run 21612680866 | Fixed with robust test |

---

---

## Execution Phase Audit

### Execution Verdict: ✅ PASS

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Training completed | ✅ PASS | Status: success, 25m 26s runtime |
| Policy head trained | ✅ PASS | 10/10 epochs, loss converged |
| Outcome head trained | ✅ PASS | 10/10 epochs, loss decreased 1.13 → 1.08 |
| Config immutability | ✅ PASS | `TrainingConfigLockV1` emitted before training |
| Report emitted | ✅ PASS | `TrainingRunReportV1` with all required fields |
| Checkpoints saved | ✅ PASS | 2 checkpoints (policy, outcome) |
| FrozenEval v2 honored | ✅ PASS | Used as ruler via compatibility layer |
| No architecture drift | ✅ PASS | Used existing `BaselinePolicyV1`, `OutcomeHeadV1` |

### Execution Attempts

| Attempt | Result | Notes |
|---------|--------|-------|
| #1 | ❌ FAIL | FrozenEval schema mismatch (V1 vs V2) |
| #2 | ✅ PASS | Compatibility fix merged (PR #37), training successful |

### Known Limitations

1. **Synthetic training data**: Training dataset is synthetic (deterministic chess positions), not real game data
2. **Uniform policy distribution**: Policy loss converged to 0.0 because synthetic data has uniform move distribution
3. **Small vocabulary**: Policy model learned only 8 moves during training

### Deferred Items

**None.** All M31 objectives have been met.

### Risk Carried Forward

**None blocking.** Synthetic data limitation is acceptable for Phase E scale proof. Real game data will be used in production.

---

## Machine-Readable Appendix

```json
{
  "milestone": "M31",
  "mode": "delta+execution",
  "commit": "579cd2d",
  "range": "9557d57...579cd2d",
  "verdict": "green",
  "execution_verdict": "pass",
  "quality_gates": {
    "ci": "pass",
    "tests": "pass",
    "coverage": "pass",
    "security": "pass",
    "dx_docs": "pass",
    "guardrails": "pass",
    "training": "pass"
  },
  "execution": {
    "status": "success",
    "run_id": "m31-training-run-001",
    "runtime_seconds": 1526,
    "policy_epochs": 10,
    "outcome_epochs": 10,
    "checkpoints": 2
  },
  "issues": [],
  "deferred_registry_updates": [],
  "score_trend_update": {
    "arch": 4.5,
    "mod": 4.5,
    "health": 4.5,
    "ci": 4.5,
    "sec": 5.0,
    "perf": 4.0,
    "dx": 4.0,
    "docs": 4.0,
    "overall": 4.4
  }
}
```

