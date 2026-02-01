# M25 CI Run 4 Analysis

**Workflow:** CI  
**Run ID:** 21570843257  
**Trigger:** Pull Request #31  
**Branch:** `m25-phase-d-recalibration-001`  
**Commit SHA:** `132a3a0ea8d56fdf48fe43bf473fd64d707a2a3e`  
**Status:** ❌ **FAILURE**  
**Created At:** 2026-02-01T21:47:32Z

---

## Workflow Identity

- **Workflow Name:** CI
- **Run ID:** 21570843257
- **Trigger:** Pull Request (PR #31)
- **Branch:** m25-phase-d-recalibration-001
- **Commit:** 132a3a0ea8d56fdf48fe43bf473fd64d707a2a3e

---

## Change Context

- **Milestone:** M25 — PHASE-D-RECALIBRATION-001
- **Phase:** D (Data Expansion, Calibration & Quality)
- **Intent:** Introduce explicit, measurable probability recalibration using temperature scaling
- **Run Type:** Corrective (fixing Run 3 issues)

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
| Lint and Format | ✅ Required | Ruff lint + format check | ❌ FAIL | Format check failed (1 file) |
| Type Check | ✅ Required | MyPy strict mode | ✅ PASS | All type checks pass |
| Test | ✅ Required | pytest with coverage | ❌ FAIL | 1 test failure (assertion issue) |
| Security Scan | ✅ Required | pip-audit + bandit | ✅ PASS | No new vulnerabilities |
| Performance Benchmarks | ✅ Required | pytest-benchmark | ✅ PASS | No regressions |
| Calibration Evaluation | ✅ Required | M24 calibration job | ✅ PASS | Baseline functionality intact |
| Recalibration Evaluation | ✅ Required | M25 recalibration job | ✅ PASS | **Core functionality verified** |

**Merge-Blocking Jobs:** All 7 jobs are required checks.

---

## Step 2 — Signal Integrity Analysis

### A) Tests

**Status:** ⚠️ **PARTIAL PASS** (1 test failure)

**Test Execution:**
- ✅ 706 tests passed
- ✅ 1 test skipped
- ❌ 1 test failed: `test_calibration_cli_with_recalibration_flag`

**Failure Details:**
- **Test:** `TestRecalibrationCLI.test_calibration_cli_with_recalibration_flag`
- **Issue:** Test checks `stdout` for "before"/"after", but preview output goes to `stderr`
- **Root Cause:** Misunderstanding of CLI output streams (preview → stderr, JSON → stdout)

**Coverage:**
- Overall: 91.78% (above threshold)
- `cli.py`: 77.53% (improved from 73.92% in Run 3)
- `recalibration_runner.py`: 91.80% (excellent coverage)

**Interpretation:** This is a **test assertion bug**, not a functionality failure. The CLI works correctly (Recalibration Evaluation job passed).

### B) Coverage

**Status:** ✅ **PASSED**

**Details:**
- Overall coverage: 91.78% (above 90% threshold)
- `cli.py` coverage: 77.53% (improved from 73.92%)
- `recalibration_runner.py`: 91.80% (excellent)
- No regressions detected in overlap-set comparison

**Interpretation:** Coverage is healthy. CLI test additions improved coverage significantly.

### C) Static / Policy Gates

**Lint (Ruff):**
- **Status:** ❌ **FAILED** (format check only)
- **Errors:** 1 file needs reformatting: `tests/test_m25_recalibration.py`
- **Type:** Formatting only (no logic errors)

**Type Check (MyPy):**
- **Status:** ✅ **PASSED**
- All type checks pass

**Interpretation:** Formatting issue only. No logic or type errors.

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
- `tests/test_m25_recalibration.py` (685 lines)

**Modified Files:**
- `src/renacechess/contracts/models.py` (+M25 models)
- `src/renacechess/cli.py` (+recalibration commands, ~200 lines)
- `.github/workflows/ci.yml` (+recalibration-eval job)

### CI Signals Affected

1. **Format Check:** Test file needs reformatting (expected after adding tests)
2. **Test Assertion:** Test checks wrong output stream (fixable)
3. **Recalibration Job:** ✅ **PASSES** — Core functionality verified

### Unexpected Deltas

**None.** All failures are minor test/formatting issues, not functionality problems.

---

## Step 4 — Failure Analysis

### Failure 1: Ruff Format Check

**Classification:** Formatting

**In Scope:** ✅ Yes (M25 test file)

**Severity:** Blocking

**Root Cause:** Test file needs reformatting after adding CLI tests.

**Fix:** Run `ruff format tests/test_m25_recalibration.py`

**Status:** 🔧 **FIXABLE** (automatic)

---

### Failure 2: Test Assertion Error

**Classification:** Test bug (wrong assertion)

**In Scope:** ✅ Yes (M25 test)

**Severity:** Blocking

**Root Cause:** Test checks `stdout` for preview text, but CLI outputs preview to `stderr` (JSON goes to `stdout`).

**Impact:**
- Test fails with: `assert ('before' in result.stdout.lower() or 'after' in result.stdout.lower())`
- Actual behavior: Preview text is in `stderr`, JSON is in `stdout`

**Fix:** Change assertion to check `stderr` for preview markers.

**Status:** 🔧 **FIXABLE** (test fix)

**Note:** The CLI functionality works correctly (Recalibration Evaluation job passed). This is purely a test assertion issue.

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

✅ **Coverage maintained** — 91.78% overall, no regressions

---

## Step 6 — Verdict

**Verdict:**  
Run 4 demonstrates that **core M25 functionality works correctly** (Recalibration Evaluation job passed, coverage improved). Two minor issues remain:

1. **Formatting:** 1 test file needs auto-formatting (trivial fix)
2. **Test assertion:** Test checks wrong output stream (simple fix)

Both issues are **test/formatting problems**, not functionality failures. The implementation is correct.

**Status:** 🔁 **Re-run required** (after formatting + test assertion fix)

---

## Step 7 — Next Actions

### Immediate Actions (M25)

1. **Fix formatting** (commit `132a3a0` + formatting)
   - Owner: AI agent
   - Scope: Run `ruff format tests/test_m25_recalibration.py` and commit
   - Milestone: M25 (current)

2. **Fix test assertion** (new commit)
   - Owner: AI agent
   - Scope: Change test to check `stderr` instead of `stdout` for preview output
   - Milestone: M25 (current)

3. **Wait for Run 5**
   - Owner: CI system
   - Scope: Verify formatting + test fixes
   - Milestone: M25 (current)

### No Deferred Work

All issues are addressable within M25 scope. No architectural concerns.

---

## Appendix: Job Details

### Lint and Format Job

**Failures:**
- Ruff format check: 1 file needs reformatting
- File: `tests/test_m25_recalibration.py`

**Auto-fixes:** Run `ruff format tests/test_m25_recalibration.py` to fix

### Test Job

**Failures:**
- 1 test failure: `test_calibration_cli_with_recalibration_flag`
- Root cause: Test checks `stdout` but preview goes to `stderr`

**Test Execution:**
- ✅ 706 tests passed
- ✅ 1 test skipped
- ❌ 1 test failed (assertion issue)

**Coverage:**
- Overall: 91.78% ✅
- `cli.py`: 77.53% (improved from 73.92%)
- `recalibration_runner.py`: 91.80% ✅

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
**Next:** Fix formatting and test assertion, then Run 5.

