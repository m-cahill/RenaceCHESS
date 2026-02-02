# M25 CI Run 5 Analysis

**Workflow:** CI  
**Run ID:** 21570965264  
**Trigger:** Pull Request #31  
**Branch:** `m25-phase-d-recalibration-001`  
**Commit SHA:** `e2ac2fb795d0eb8dbc69964fce534d6263615cd6`  
**Status:** ❌ **FAILURE**  
**Created At:** 2026-02-01T21:56:15Z

---

## Workflow Identity

- **Workflow Name:** CI
- **Run ID:** 21570965264
- **Trigger:** Pull Request (PR #31)
- **Branch:** m25-phase-d-recalibration-001
- **Commit:** e2ac2fb795d0eb8dbc69964fce534d6263615cd6

---

## Change Context

- **Milestone:** M25 — PHASE-D-RECALIBRATION-001
- **Phase:** D (Data Expansion, Calibration & Quality)
- **Intent:** Introduce explicit, measurable probability recalibration using temperature scaling
- **Run Type:** Corrective (fixing Run 4 issues)

---

## Baseline Reference

- **Baseline:** M24 (main branch after M24 merge)
- **Invariants:**
  - Coverage must remain ≥90%
  - No Phase C contract changes
  - No runtime behavior changes (default path)

---

## Step 1 — Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
|-------------|-----------|---------|-----------|-------|
| Lint and Format | ✅ Required | Ruff lint + format check | ✅ PASS | All formatting checks pass |
| Type Check | ✅ Required | MyPy strict mode | ✅ PASS | All type checks pass |
| Test | ✅ Required | pytest with coverage | ❌ FAIL | Coverage regression in cli.py |
| Security Scan | ✅ Required | pip-audit + bandit | ✅ PASS | No new vulnerabilities |
| Performance Benchmarks | ✅ Required | pytest-benchmark | ✅ PASS | No regressions |
| Calibration Evaluation | ✅ Required | M24 calibration job | ✅ PASS | Baseline functionality intact |
| Recalibration Evaluation | ✅ Required | M25 recalibration job | ✅ PASS | **Core functionality verified** |

**Merge-Blocking Jobs:** All 7 jobs are required checks.

---

## Step 2 — Signal Integrity Analysis

### A) Tests

**Status:** ⚠️ **PARTIAL PASS** (coverage regression)

**Test Execution:**
- ✅ All tests passed (706 passed, 1 skipped)
- ❌ Coverage regression detected: `cli.py: 86.26% → 80.38% (delta: -5.88%)`

**Coverage:**
- Overall: 91.78% (above threshold)
- `cli.py`: 80.38% (below baseline of 86.26%)
- `recalibration_runner.py`: 91.80% (excellent coverage)

**Interpretation:** New CLI code paths are not fully covered. The "preview" command and error handling paths need test coverage.

### B) Coverage

**Status:** ❌ **REGRESSION DETECTED**

**Details:**
- Overall coverage: 91.78% (above 90% threshold) ✅
- `cli.py` coverage: 80.38% (below baseline of 86.26%) ❌
- Regression: -5.88% (exceeds 0.5% tolerance)
- Overlap-set non-regression check: **FAILED**

**Interpretation:** New recalibration CLI commands added ~200 lines, but not all paths are covered. Need comprehensive CLI tests.

### C) Static / Policy Gates

**Lint (Ruff):**
- **Status:** ✅ **PASSED**
- All formatting checks pass

**Type Check (MyPy):**
- **Status:** ✅ **PASSED**
- All type checks pass

**Interpretation:** All static checks pass. Only coverage regression remains.

### D) Performance / Benchmarks

**Status:** ✅ **PASSED**

No regressions detected. Benchmarks isolated from correctness signals.

---

## Step 3 — Delta Analysis (Change Impact)

### Files Modified

**New Files:**
- `src/renacechess/contracts/schemas/v1/recalibration_parameters.v1.schema.json`
- `src/renacechess/contracts/schemas/v1/calibration_delta.v1.schema.json`
- `src/renacechess/eval/recalibration_runner.py` (716 lines)
- `tests/test_m25_recalibration.py` (685 lines → 919 lines after fix)

**Modified Files:**
- `src/renacechess/contracts/models.py` (+M25 models)
- `src/renacechess/cli.py` (+recalibration commands, ~200 lines)
- `.github/workflows/ci.yml` (+recalibration-eval job)

### CI Signals Affected

1. **Coverage Regression:** `cli.py` coverage dropped 5.88% due to new code paths
2. **Recalibration Job:** ✅ **PASSES** — Core functionality verified

### Unexpected Deltas

**None.** Coverage regression is expected when adding new code without full test coverage.

---

## Step 4 — Failure Analysis

### Failure: Coverage Regression in cli.py

**Classification:** Test coverage gap

**In Scope:** ✅ Yes (M25 CLI code)

**Severity:** Blocking

**Root Cause:** New recalibration CLI commands (`recalibration fit`, `recalibration preview`, error handling paths) added but not fully covered by tests.

**Impact:**
- `cli.py` coverage: 86.26% → 80.38% (-5.88%)
- Overlap-set non-regression check failed
- Missing coverage on:
  - `recalibration preview` command (full path)
  - Error handling paths (file not found checks)
  - Invalid command handling (else branch)

**Fix:** Add comprehensive CLI tests for all recalibration command paths and error cases.

**Status:** 🔧 **FIXED** (commit `435231f`)

**Fix Details:**
- Added test for `recalibration preview` command
- Added tests for all error paths (manifest not found, metrics not found, params not found)
- Added test for invalid recalibration command
- Should restore `cli.py` coverage to baseline

---

## Step 5 — Invariants & Guardrails Check

### Required CI Checks

✅ **All checks remain enforced** — No gates weakened or bypassed

### Semantic Scope

✅ **No scope leakage** — Coverage, tests, and benchmarks remain isolated

### Phase C Contracts

✅ **No Phase C contract changes** — M25 schemas are additive only

### Determinism

✅ **Determinism preserved** — All M25 functions use fixed seeds and canonical JSON

### Coverage Threshold

⚠️ **Coverage regression** — `cli.py` below baseline, but fix applied in commit `435231f`

---

## Step 6 — Verdict

**Verdict:**  
Run 5 demonstrates that **core M25 functionality works correctly** (Recalibration Evaluation job passed, all tests pass). One issue remains:

1. **Coverage regression:** `cli.py` coverage dropped 5.88% due to new code paths

**Status:** 🔁 **Re-run required** (after comprehensive CLI test additions in commit `435231f`)

**Fix Applied:**
- Added comprehensive CLI tests for all recalibration command paths
- Added tests for all error handling paths
- Added test for invalid command handling
- Should restore `cli.py` coverage to baseline in Run 6

---

## Step 7 — Next Actions

### Immediate Actions (M25)

1. **Wait for Run 6** (commit `435231f`)
   - Owner: CI system
   - Scope: Verify comprehensive CLI tests restore coverage
   - Milestone: M25 (current)

2. **If Run 6 passes:**
   - Generate Run 6 analysis
   - Request merge authorization
   - Proceed to M25 closeout

### No Deferred Work

All issues are addressable within M25 scope. No architectural concerns.

---

## Appendix: Job Details

### Test Job

**Failures:**
- Coverage regression: `cli.py: 86.26% → 80.38% (delta: -5.88%)`

**Test Execution:**
- ✅ 706 tests passed
- ✅ 1 test skipped
- ❌ Coverage regression detected

**Coverage:**
- Overall: 91.78% ✅
- `cli.py`: 80.38% ❌ (below baseline of 86.26%)
- `recalibration_runner.py`: 91.80% ✅

**Fix Applied:**
- Commit `435231f`: Added comprehensive CLI tests
- Should restore `cli.py` coverage to baseline

### Recalibration Evaluation Job

**Status:** ✅ **PASSED**

This is the **key success indicator**:
- ✅ Calibration evaluation (before) completed
- ✅ Recalibration parameters fitted successfully
- ✅ Recalibration evaluation (after) completed
- ✅ Calibration delta computed
- ✅ Artifacts uploaded

**Interpretation:** Core M25 functionality is **working correctly**.

---

**Analysis Complete.**  
**Next:** Wait for Run 6 (commit `435231f`) to verify coverage fix.



