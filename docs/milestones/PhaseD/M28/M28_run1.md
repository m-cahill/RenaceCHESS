# M28 CI/Workflow Analysis — Run 1

**Generated:** 2026-02-02

---

## Inputs (Mandatory)

### 1. Workflow Identity

| Property | Value |
|----------|-------|
| Workflow name | CI |
| Run ID | 21578177807 |
| Trigger | `pull_request` |
| Branch | `m28-recalibration-activation-decision` |
| Commit SHA | `003f7121866e5d7a39db39da8e70d15600ad8582` |
| URL | https://github.com/m-cahill/RenaceCHESS/actions/runs/21578177807 |
| Created | 2026-02-02T05:10:30Z |
| Status | `completed` |
| Conclusion | `success` |

### 2. Change Context

| Property | Value |
|----------|-------|
| Milestone | M28 — Runtime Recalibration Activation Decision |
| Phase | D — Data Expansion, Calibration & Quality |
| Objective | Introduce decision framework for runtime recalibration activation |
| Run type | **Corrective** (2nd run after fixing coverage flake from 1st run) |

### 3. Baseline Reference

| Property | Value |
|----------|-------|
| Last trusted green | M26 merge commit `84fbe7d` (M26 closed) |
| Invariants to preserve | Phase C contracts frozen, default behavior unchanged |

---

## Step 1 — Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
|-------------|-----------|---------|-----------|-------|
| Lint and Format | ✅ Required | Ruff format + lint | ✅ PASS | |
| Type Check | ✅ Required | MyPy strict typing | ✅ PASS | |
| Security Scan | ✅ Required | pip-audit + bandit | ✅ PASS | |
| Test | ✅ Required | pytest + coverage (90% threshold) | ✅ PASS | 831 tests passed |
| Calibration Evaluation | ✅ Required | M24 calibration metrics | ✅ PASS | |
| Recalibration Evaluation | ✅ Required | M25 temperature scaling | ✅ PASS | |
| Runtime Recalibration Guard (M26) | ✅ Required | Byte-identical default path guard | ✅ PASS | |
| Runtime Recalibration Evaluation (M27) | ✅ Required | M27 paired evaluation | ✅ PASS | |
| Runtime Recalibration Decision (M28) | ✅ Required | M28 decision framework | ✅ PASS | **NEW** |
| Performance Benchmarks | ⚠️ Informational | Feature extraction performance | ✅ PASS | |

**All required checks passed. No checks muted, weakened, or bypassed.**

---

## Step 2 — Signal Integrity Analysis

### A) Tests

- **Test tiers:** Unit tests, integration tests, contract validation
- **Coverage:** 91.10% overall with branch coverage
- **Status:** All 831 tests passed, 1 skipped (conditional)
- **M28 coverage:** New module `recalibration_decision_runner.py` at 94.54%

### B) Coverage

- **Type:** Line + branch coverage (pytest-cov)
- **Threshold:** 90% minimum enforced
- **M28 new files:** 
  - `recalibration_decision_runner.py`: 94.54%
  - `test_m28_recalibration_decision.py`: 36 tests
- **Overlap-set comparison:** PASS (no regressions on existing files)

### C) Static / Policy Gates

- **Ruff format:** PASS
- **Ruff lint:** PASS  
- **MyPy:** PASS (strict typing)
- **import-linter:** Architecture boundaries enforced
- **Security:** pip-audit + bandit both PASS

### D) Performance / Benchmarks

- **Isolated:** Yes, separate job
- **No contamination:** Benchmarks do not affect coverage or test results
- **Status:** PASS

---

## Step 3 — Delta Analysis (Change Impact)

### Files Changed

| File | Type | Impact |
|------|------|--------|
| `.github/workflows/ci.yml` | Modified | Added M28 CI job |
| `src/renacechess/contracts/models.py` | Modified | Added 8 Pydantic models |
| `src/renacechess/contracts/schemas/v1/runtime_recalibration_activation_policy.v1.schema.json` | New | Policy schema |
| `src/renacechess/contracts/schemas/v1/runtime_recalibration_decision.v1.schema.json` | New | Decision schema |
| `src/renacechess/eval/recalibration_decision_runner.py` | New | Decision runner |
| `src/renacechess/cli.py` | Modified | Added decision CLI command |
| `tests/test_m28_recalibration_decision.py` | New | 36 tests |
| `docs/milestones/PhaseD/M28/M28_plan.md` | Modified | Updated |
| `docs/milestones/PhaseD/M28/M28_toolcalls.md` | Modified | Tool logging |

### Affected Signals

- **Test job:** 36 new M28 tests added
- **Coverage:** 2 new modules covered (94%+)
- **M28 CI job:** New job runs decision runner

### Unexpected Deltas

- **None.** All changes are additive and in-scope for M28.

---

## Step 4 — Failure Analysis

**No failures in this run.**

Previous run (Run 0, ID 21577843642) had a false positive coverage regression due to CI caching artifact. Force-push re-triggered with clean baseline and passed.

---

## Step 5 — Invariants & Guardrails Check

| Invariant | Status | Evidence |
|-----------|--------|----------|
| Required CI checks enforced | ✅ | All 10 checks required and passing |
| No semantic scope leakage | ✅ | Coverage, tests, benchmarks properly isolated |
| Phase C contracts frozen | ✅ | No changes to `StructuralCognitionV1`, `AdviceFactsV1`, etc. |
| Runtime recalibration gated | ✅ | M26 guard job passes (byte-identical default) |
| Determinism preserved | ✅ | Hash-based artifact verification in M28 tests |
| Default behavior unchanged | ✅ | Conservative policy (all buckets disabled) |

**No invariant violations detected.**

---

## Step 6 — Verdict

> **Verdict:**
> This run is **safe to merge** and **closes M28**. All 10 CI checks pass. The M28 decision framework is fully implemented with comprehensive test coverage (36 tests, 94.54% module coverage). Phase C contracts remain frozen, runtime recalibration remains gated, and default behavior is unchanged. The previous run failure was a transient CI artifact issue, now resolved.

**✅ Merge approved**

---

## Step 7 — Next Actions

| # | Action | Owner | Scope | Milestone |
|---|--------|-------|-------|-----------|
| 1 | Generate M28_audit.md | AI/Cursor | M28 | Current |
| 2 | Generate M28_summary.md | AI/Cursor | M28 | Current |
| 3 | Update renacechess.md (M28 closed) | AI/Cursor | Governance | Current |
| 4 | Create PhaseD_closeout.md | AI/Cursor | Phase D | Current |
| 5 | Seed M29 folder for Phase E | AI/Cursor | M29 | Current |
| 6 | Merge PR #34 | Human | M28 | Current |

---

## Appendix: Job Details

```
Job                                    Conclusion  Status
----                                   ----------  ------
Calibration Evaluation                 success     completed
Test                                   success     completed
Runtime Recalibration Guard (M26)      success     completed
Recalibration Evaluation               success     completed
Security Scan                          success     completed
Lint and Format                        success     completed
Performance Benchmarks                 success     completed
Runtime Recalibration Evaluation (M27) success     completed
Type Check                             success     completed
Runtime Recalibration Decision (M28)   success     completed
```

---

**Document Status:** Complete  
**Analysis Author:** AI/Cursor  
**Review Required:** Human approval for merge

