# M24 Audit — Phase D Calibration Metrics

**Milestone:** M24 — PHASE-D-CALIBRATION-001  
**Phase:** D (Data Expansion, Calibration & Quality)  
**Date:** 2026-02-01  
**Status:** ✅ Complete  
**Audit Mode:** DELTA AUDIT  
**Baseline:** M23 (main branch)  
**Current SHA:** `029e611` (final commit)

---

## Milestone Objective

M24 introduced human-aligned calibration and evaluation signals without changing frozen Phase C contracts. This milestone establishes Phase D's first quality measurement layer, enabling future recalibration work.

---

## Deliverables Verification

| Deliverable | Status | Evidence |
|-------------|--------|----------|
| CalibrationMetricsV1 schema | ✅ Complete | `src/renacechess/contracts/models.py`, `src/renacechess/contracts/schemas/v1/calibration_metrics.v1.schema.json` |
| Calibration evaluation runner | ✅ Complete | `src/renacechess/eval/calibration_runner.py` |
| Per-Elo bucket stratification | ✅ Complete | Uses `SkillBucketId` from `conditioning/buckets.py` |
| CI calibration job | ✅ Complete | `.github/workflows/ci.yml` — `calibration-eval` job |
| CLI integration | ✅ Complete | `src/renacechess/cli.py` — `calibration` subcommand |
| Test coverage | ✅ Complete | `tests/test_m24_calibration.py` — 30 tests, 653 lines |

---

## Architecture & Modularity Review

### Boundary Violations

**None.** M24 maintains strict boundaries:

- ✅ No Phase C contract changes (AdviceFactsV1, EloBucketDeltaFactsV1, CoachingDraftV1 untouched)
- ✅ No runtime behavior changes (measurement-only, no recalibration)
- ✅ Uses existing contracts (`FrozenEvalManifestV1`, `SkillBucketId`)
- ✅ New module (`eval/calibration_runner.py`) is downstream-only

### Coupling Analysis

**Clean separation:**
- Calibration runner imports only from:
  - `contracts.models` (allowed)
  - `conditioning.buckets` (allowed)
  - `eval.baselines` (allowed)
  - `eval.interfaces` (allowed)
- No circular dependencies introduced
- CLI integration is thin wrapper (no business logic)

### Keep / Fix / Defer

| Category | Items |
|----------|-------|
| **Keep** | CalibrationMetricsV1 schema, calibration runner, Elo bucket stratification, CI job, test suite |
| **Fix Now** | None |
| **Defer** | None |

---

## CI/CD & Workflow Audit

### CI Root Cause Summary

**Run 1 (21557859901):** Coverage data type mismatch — baseline and head used different coverage modes  
**Run 2 (21569452167):** Lint error (unused variable) + coverage data type conflict in final test run  
**Run 3 (21569555120):** ✅ **FULLY GREEN** — All fixes verified

### Required Checks

| Check | Status | Duration | Notes |
|-------|--------|----------|-------|
| Lint and Format | ✅ PASS | ~3m | Ruff lint, format, import-linter all clean |
| Type Check | ✅ PASS | ~3m | MyPy: 0 errors across 57 files |
| Security Scan | ✅ PASS | ~3m | pip-audit + bandit clean |
| Performance Benchmarks | ✅ PASS | ~3m | No regressions |
| Calibration Evaluation | ✅ PASS | ~3m | M24 deliverable verified |
| Test | ✅ PASS | ~6m | 684 passed, 1 skipped, coverage ≥90%, no regressions |

### Guardrails

- ✅ Import-linter enforces module boundaries
- ✅ Coverage overlap-set comparison passed (no regressions)
- ✅ All actions SHA-pinned
- ✅ Coverage data type consistency enforced (`--cov-branch` throughout)

### CI Fixes Applied

1. **Coverage data-type alignment** (commit `206d016`):
   - Added `--cov-branch` to baseline and head coverage generation
   - Resolved "Can't combine statement coverage data with branch data" error

2. **Lint error fix** (commit `33968b5`):
   - Removed unused `hash_val` variable in `tests/test_m08_model.py`

3. **Final test run fix** (commit `0541804`):
   - Added `.coverage` file cleanup before final test run
   - Added `--cov-branch` to final test run step
   - Ensures consistent branch coverage throughout pipeline

---

## Tests & Coverage (Delta-Only)

### Coverage Delta

| File | Coverage | Notes |
|------|----------|-------|
| `eval/calibration_runner.py` | 100% | All paths exercised |
| `contracts/models.py` (new models) | 100% | All CalibrationMetricsV1 models tested |
| `cli.py` (calibration command) | Covered | CLI integration tests added |
| `models/baseline_v1.py` | Improved | Branch coverage tests added (98.25% → 93.86% baseline, then restored) |

### New Tests Added

30 new tests in `test_m24_calibration.py`:
- Schema validation (CalibrationMetricsV1)
- SkillBucketId canonical bucket equality
- CalibrationAccumulator (ECE, Brier, NLL, histogram)
- OutcomeCalibrationAccumulator and PolicyCalibrationAccumulator
- Calibration runner integration (manifest loading, per-bucket metrics, determinism)
- CLI integration tests

### Test Quality

- ✅ All tests deterministic (fixed seeds, canonical JSON)
- ✅ Comprehensive edge case coverage
- ✅ Integration tests verify end-to-end flow
- ✅ No flaky tests observed

---

## Security & Supply Chain

### Dependency Changes

**None.** M24 adds no new dependencies. Uses existing:
- `pydantic` (already in dependencies)
- `jsonschema` (already in dependencies)
- Standard library (`json`, `math`, `collections`, `pathlib`, `datetime`)

### Security Scan Results

- ✅ pip-audit: No new vulnerabilities
- ✅ bandit: No security issues in new code
- ✅ Deferred torch CVEs unchanged (TORCH-SEC-001)

---

## Performance & Scalability

### Performance Impact

**Minimal.** M24 adds:
- Offline evaluation runner (not in hot path)
- CI job runs on frozen eval fixture (small, deterministic)
- No runtime performance impact (measurement-only)

### Benchmark Results

- ✅ All performance benchmarks passed
- ✅ No regressions detected

---

## Code Quality

### Linting

- ✅ Ruff lint: Clean (after fix)
- ✅ Ruff format: Clean
- ✅ Import-linter: Clean

### Type Checking

- ✅ MyPy: 0 errors
- ✅ All new code fully typed
- ✅ No `Any` types introduced

### Code Review Observations

- ✅ Clear separation of concerns
- ✅ Comprehensive docstrings
- ✅ Deterministic by design (fixed seeds, canonical JSON)
- ✅ Schema-first approach (Pydantic + JSON Schema)

---

## Issues & Exceptions

### Resolved Issues

1. **Coverage data type mismatch** (Run 1):
   - **Root cause:** Baseline and head used different coverage modes
   - **Resolution:** Added `--cov-branch` to both baseline and head coverage generation
   - **Status:** ✅ Resolved

2. **Lint error** (Run 2):
   - **Root cause:** Unused variable in test
   - **Resolution:** Removed unused `hash_val` variable
   - **Status:** ✅ Resolved

3. **Coverage data type conflict in final test run** (Run 2):
   - **Root cause:** Final test run tried to combine coverage data with different types
   - **Resolution:** Clean `.coverage` files and add `--cov-branch` to final test run
   - **Status:** ✅ Resolved

### Deferred Issues

**None.** M24 introduces no new deferrals.

### Prior Deferrals (Unchanged)

- **TORCH-SEC-001:** torch CVEs (unchanged from M23)
- **CLI-COV-001:** Remaining CLI file coverage (unchanged from M23)

---

## Governance Outcomes

### Enforcement Strengthened

1. **Coverage system consistency:**
   - All coverage steps now use `--cov-branch` consistently
   - Prevents future data type conflicts
   - Long-term maintainability improvement

2. **Calibration visibility:**
   - New CI job provides continuous calibration metrics
   - Enables future recalibration work (M25+)

3. **Schema validation:**
   - CalibrationMetricsV1 has both Pydantic and JSON Schema validation
   - Ensures contract stability

### Boundaries Clarified

- ✅ Phase C contracts remain frozen (no changes)
- ✅ Runtime behavior unchanged (measurement-only)
- ✅ Clear separation: measurement vs. recalibration

---

## Exit Criteria Evaluation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| CalibrationMetricsV1 schema | ✅ Met | Schema created, validated, tested |
| Calibration evaluation runner | ✅ Met | Runner implemented, tested, CI-verified |
| Per-Elo bucket stratification | ✅ Met | Uses canonical SkillBucketId, tested |
| CI calibration job | ✅ Met | Job added, passes, artifacts uploaded |
| No Phase C contract changes | ✅ Met | No changes to AdviceFactsV1, EloBucketDeltaFactsV1, CoachingDraftV1 |
| No runtime behavior changes | ✅ Met | Measurement-only, no recalibration |
| Deterministic artifacts | ✅ Met | Fixed seeds, canonical JSON, tested |
| Test coverage | ✅ Met | 30 new tests, 100% coverage of new code |

---

## Final Verdict

**Milestone objectives met. Safe to proceed.**

M24 successfully introduces Phase D's first quality measurement layer without compromising Phase C contracts or runtime behavior. All CI gates pass. Coverage system consistency improved. No new technical debt introduced.

**Recommendation:** ✅ **APPROVED FOR MERGE**

---

## Authorized Next Step

**M25 — Phase D Recalibration / Adjustment**

M24 enables M25 to change behavior because measurement capability is now proven. Examples:
- Temperature scaling
- Bucket-specific calibration curves
- Thresholding experiments
- Human evaluation alignment loops

---

## Canonical References

- **PR:** #30
- **Final Commit:** `029e611`
- **CI Runs:**
  - Run 1: 21557859901 (coverage data type mismatch)
  - Run 2: 21569452167 (lint + coverage conflict)
  - Run 3: 21569555120 (✅ fully green)
- **Plan:** `docs/milestones/PhaseD/M24/M24_plan.md`
- **Summary:** `docs/milestones/PhaseD/M24/M24_summary.md`
- **Tool Calls:** `docs/milestones/PhaseD/M24/M24_toolcalls.md`

