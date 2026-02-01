# M24 CI Run 2 Analysis

**Workflow:** CI  
**Run ID:** 21569452167  
**Trigger:** Pull Request #30  
**Branch:** `m24-phase-d-calibration-001`  
**Commit:** `f0a5fd24ee5b2363aa0821aed3c1308b3dba4e55`  
**Status:** ❌ Failure (2 jobs failed, 4 passed)  
**URL:** https://github.com/m-cahill/RenaceCHESS/actions/runs/21569452167  
**Created:** 2026-02-01T20:10:28Z

---

## Step 1 — Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
| ----------- | --------- | ------- | --------- | ----- |
| Type Check (MyPy) | ✅ Yes | Static type checking | ✅ **PASS** | All 57 files checked, 0 errors |
| Security Scan | ✅ Yes | Dependency vuln scan + SAST | ✅ **PASS** | pip-audit + bandit clean |
| Lint and Format | ✅ Yes | Code style + import boundaries | ❌ **FAIL** | Ruff lint: unused variable `hash_val` in test_m08_model.py:268 |
| Performance Benchmarks | ✅ Yes | Performance regression detection | ✅ **PASS** | All benchmarks passed |
| Calibration Evaluation (M24) | ✅ Yes | M24 deliverable verification | ✅ **PASS** | Calibration metrics generated and validated |
| Test | ✅ Yes | Test suite + coverage gates | ❌ **FAIL** | Coverage data type conflict in final test run |

---

## Step 2 — Signal Integrity Analysis

### A) Tests

**Test Execution:**
- 684 tests passed, 1 skipped
- All M24 calibration tests passed
- All existing tests maintained

**Coverage Status:**
- ✅ **Coverage comparison step PASSED** — This is the key fix from Run 1
- ✅ Baseline and head coverage XML generated successfully with `--cov-branch`
- ✅ Overlap-set comparison completed without data type errors
- ❌ Final test run failed due to coverage data type conflict

**Coverage Comparison Results:**
- Files in base: 43
- Files in head: 44
- Overlap files compared: 43
- ✅ **No coverage regressions detected** (coverage comparison passed)

### B) Linting

**Ruff Lint:**
- ❌ 1 error: Unused variable `hash_val` in `tests/test_m08_model.py:268`
- Error introduced in test improvements for branch coverage
- **Fix:** Remove unused variable assignment

### C) Type Checking

**MyPy:**
- ✅ All 57 files checked
- ✅ 0 type errors
- No regressions from M24 changes

### D) Security

**pip-audit:**
- ✅ No new vulnerabilities detected
- Deferred torch vulnerabilities remain (TORCH-SEC-001)

**Bandit SAST:**
- ✅ No security issues found
- All scans clean

### E) Performance

**Benchmarks:**
- ✅ All performance benchmarks passed
- No regressions detected

---

## Step 3 — Delta Analysis (vs Run 1)

### Improvements

1. **✅ Coverage Data Type Mismatch FIXED**
   - Added `--cov-branch` to both baseline and head coverage generation
   - Coverage comparison step now passes
   - No more "Can't combine statement coverage data with branch data" error

2. **✅ Coverage Regression FIXED**
   - Added comprehensive tests for `baseline_v1.py` branch coverage
   - All skill bucket legacy format branches now covered
   - Hash conflict detection branch covered
   - Empty legal moves path covered

### New Issues

1. **❌ Lint Error (F841)**
   - Unused variable `hash_val` in test
   - **Fix Applied:** Removed unused variable in commit `33968b5`

2. **❌ Coverage Data Type Conflict in Final Test Run**
   - Error: "Can't combine statement coverage data with branch data"
   - Root cause: Final test run step doesn't clean `.coverage` files from previous steps
   - **Fix Applied:** Added `--cov-branch` and `.coverage` cleanup in commit `0541804`

---

## Step 4 — Failure Analysis

### Failure 1: Lint and Format

**Error:**
```
tests/test_m08_model.py:268:5: F841 Local variable `hash_val` is assigned to but never used
```

**Root Cause:**
- Test improvement added `hash_val` variable for documentation but didn't use it
- Ruff lint correctly flagged unused variable

**Resolution:**
- ✅ Fixed in commit `33968b5` — removed unused variable
- ✅ No functional impact

### Failure 2: Test (Final Test Run)

**Error:**
```
coverage.exceptions.DataError: Can't combine statement coverage data with branch data
```

**Root Cause:**
- Baseline and head coverage XML generation steps create `.coverage` files with branch data
- Final test run step (`Run tests with absolute threshold (PR mode)`) tries to combine coverage data
- Previous `.coverage` files have branch data, but final run might generate statement-only data
- Coverage library cannot combine different data types

**Resolution:**
- ✅ Fixed in commit `0541804`:
  - Added `rm -f .coverage .coverage.*` to clean existing coverage files
  - Added `--cov-branch` flag to final test run step
  - Ensures consistent branch coverage throughout pipeline

---

## Step 5 — Invariants & Guardrails Check

### Coverage Gates

- ✅ **Overlap-set comparison:** PASSED (no regressions)
- ✅ **90% absolute threshold:** Will be verified in Run 3 after fixes
- ✅ **Coverage data type consistency:** FIXED (all steps use `--cov-branch`)

### Quality Gates

- ✅ **Type checking:** PASSED (0 errors)
- ✅ **Security scanning:** PASSED (no new issues)
- ✅ **Performance benchmarks:** PASSED (no regressions)
- ❌ **Linting:** FAILED (fixed in subsequent commit)
- ❌ **Test execution:** FAILED (fixed in subsequent commit)

### M24 Deliverables

- ✅ **Calibration evaluation job:** PASSED
- ✅ **Calibration metrics schema:** Validated
- ✅ **Calibration artifacts:** Generated successfully

---

## Step 6 — Verdict

### Run 2 Status: **PARTIAL SUCCESS → FIXES APPLIED**

**Key Achievements:**
1. ✅ **Coverage data type mismatch resolved** — Core issue from Run 1 fixed
2. ✅ **Coverage comparison working** — Overlap-set comparison passes
3. ✅ **No coverage regressions** — All existing files maintain coverage
4. ✅ **M24 deliverables verified** — Calibration evaluation job passes

**Issues Identified and Fixed:**
1. ✅ Lint error (unused variable) — Fixed in commit `33968b5`
2. ✅ Coverage data type conflict in final test run — Fixed in commit `0541804`

**Next Steps:**
- Monitor CI Run 3 (21569555120) to verify all fixes
- Expected: All jobs green, including lint and test
- If Run 3 passes, M24 is ready for merge

---

## Step 7 — Next Actions

### Immediate Actions (Completed)

- [x] Fix lint error (unused variable)
- [x] Fix coverage data type conflict in final test run
- [x] Push fixes to trigger Run 3

### Pending Verification

- [ ] Verify Run 3 passes all checks
- [ ] Confirm 90% coverage threshold met
- [ ] Generate M24_run3.md if needed (or proceed to audit/summary)

### Merge Readiness

**Status:** ⏳ **PENDING RUN 3 VERIFICATION**

Once Run 3 confirms all fixes:
- ✅ All quality gates pass
- ✅ Coverage gates pass
- ✅ M24 deliverables verified
- ✅ Ready for merge and closeout

---

## Evidence Summary

### Commits in Run 2

- `f0a5fd2` — test(M24): Improve baseline_v1.py branch coverage
- `206d016` — fix(M24): Align baseline and head coverage data types

### Fixes Applied After Run 2

- `33968b5` — fix(M24): Fix lint error and coverage data type conflict
- `0541804` — fix(M24): Clean .coverage files and add --cov-branch to final test run

### Test Results

- **Total tests:** 684 passed, 1 skipped
- **Coverage comparison:** ✅ PASSED (no regressions)
- **M24 tests:** ✅ All passing

---

## Conclusion

Run 2 successfully resolved the core coverage data type mismatch issue from Run 1. The coverage comparison step now works correctly with branch coverage enabled. Two minor issues (lint error and final test run coverage conflict) were identified and fixed immediately. Run 3 will verify that all fixes are correct and CI is fully green.

**M24 Progress:** ✅ Core functionality working, ✅ Coverage fixes applied, ⏳ Final CI verification pending

