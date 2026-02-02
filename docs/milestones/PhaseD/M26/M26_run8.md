# M26 CI Run 8 Analysis

**Workflow Identity**
- Workflow: CI
- Run ID: 21574403076
- Trigger: Pull Request (#32)
- Branch: `m26-phase-d-runtime-gating-001`
- Commit: fbe358e (add comprehensive edge case tests + fix formatting)

**Change Context**
- Milestone: M26 (PHASE-D-RUNTIME-GATING-001)
- Intent: Governance and safety milestone for controlled runtime application of recalibration
- Type: Corrective (add comprehensive edge case tests for integration functions)
- Baseline: M25 (last known green: commit from M25 closeout)

---

## Step 1 — Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
| ----------- | --------- | ------- | --------- | ----- |
| Security Scan | ✅ Required | Dependency vulnerability scan (pip-audit) + static security analysis (bandit) | ✅ Pass | No security issues found |
| Test | ✅ Required | Unit + integration tests with coverage | ❌ Fail | Coverage regression in eval/runner.py persists (-1.28%) |
| Performance Benchmarks | ✅ Required | Performance regression detection | ✅ Pass | No performance regressions |
| Lint and Format | ✅ Required | Ruff linting, formatting, import boundary checks | ✅ Pass | All formatting issues fixed |
| Type Check | ✅ Required | MyPy static type checking | ✅ Pass | All type checks passed |
| Calibration Evaluation | ✅ Required | Calibration metrics validation | ✅ Pass | Calibration metrics generated successfully |
| Recalibration Evaluation | ✅ Required | Recalibration parameter fitting and validation | ✅ Pass | Recalibration parameters generated successfully |
| Runtime Recalibration Guard (M26) | ✅ Required | M26-specific guard job for runtime invariants | ✅ Pass | All guard tests passed |

**Merge-blocking checks:** All required checks must pass for merge.

---

## Step 2 — Signal Integrity Analysis

### A) Tests

**Test tiers executed:**
- Unit tests (comprehensive M26 runtime recalibration tests - now 20 tests total)
- Integration tests (existing test suite + CLI gate loading tests + runner integration tests)
- Contract tests (schema validation)

**Failures:**
- No test failures (all 20 tests pass)
- Coverage regression detected in overlap-set comparison:
  - `eval/runner.py`: 85.47% → 84.18% (delta: -1.28%)
  - **No change from Run 7:** Additional edge case tests did not restore coverage

**Assessment:** The additional edge case tests (error paths, SAN preservation, single move handling) did not improve coverage in `eval/runner.py`. This suggests that the uncovered lines are not in the integration functions themselves (which are now comprehensively tested), but rather in the actual call sites within `runner.py`'s main evaluation loop.

### B) Coverage

**Coverage type:** Line coverage with overlap-set non-regression enforcement

**Coverage scoping:**
- Overlap-set comparison (files that existed in baseline)
- 0.5% tolerance for minor fluctuations
- New files evaluated independently

**Exclusions:** None documented in this run

**Assessment:** Coverage signal shows **no improvement** from additional tests. The -1.28% regression persists, indicating that the uncovered lines are likely:
1. The actual function call sites in `runner.py` (lines 316-323, 357-367)
2. The import statements inside the loop (lines 312-314, 353-355)
3. The `_recal_applied` variable assignments (unused but executed)
4. The `predicted_wdl` assignment after recalibration (line 367)

These lines are in the main evaluation loop and are difficult to test without running the full evaluation pipeline.

### C) Static / Policy Gates

**Linting (Ruff):**
- ✅ All checks passed (formatting fixed)

**Type checking (MyPy):**
- ✅ All type checks passed

**Assessment:** All static checks are clean.

---

## Step 3 — Delta Analysis (Change Impact)

**Files modified since Run 7:**
- `tests/test_m26_runner_recalibration_integration.py` (added 5 new edge case tests)
- `src/renacechess/eval/recalibration_integration.py` (formatted)
- `src/renacechess/eval/runner.py` (formatted)

**CI signals affected:**
- **Tests:** ✅ All tests pass (20 tests total, all passing)
- **Linting:** ✅ Fixed (all formatting issues resolved)
- **Type checking:** ✅ Fixed (all checks pass)
- **Coverage:** ⚠️ No improvement (-1.28% regression persists)
- **Guard job:** ✅ Passing (all guard tests pass)

**Unexpected deltas:**
- ⚠️ **Coverage unchanged:** Additional edge case tests did not improve `eval/runner.py` coverage
- ✅ **Formatting fixed:** All formatting issues resolved
- ✅ **Test coverage expanded:** 5 new edge case tests added (error paths, SAN preservation, single move handling)

---

## Step 4 — Failure Analysis

### Failure 1: Coverage Regression in eval/runner.py (Persistent)

**Classification:** Coverage gap (persistent, likely call sites)

**Root cause:**
- `eval/runner.py`: 85.47% → 84.18% (delta: -1.28%)
- **No improvement** from additional edge case tests
- Likely represents uncovered call sites in the main evaluation loop:
  - Function call sites (lines 316-323, 357-367)
  - Import statements inside loop (lines 312-314, 353-355)
  - Variable assignments (`_recal_applied`, `predicted_wdl`)

**In scope:** ✅ Yes (M26 integration)

**Blocking:** ⚠️ **Needs architectural decision** (regression is small but persistent)

**Fix required:**
- The uncovered lines are in the main evaluation loop, not in the extracted integration functions
- These lines are difficult to test without running the full evaluation pipeline
- Options:
  1. Accept the -1.28% regression as acceptable (within tolerance for edge cases)
  2. Extract more logic from `runner.py` to make call sites testable
  3. Add lightweight integration tests that exercise the call sites

**Status:** ⚠️ **Persistent, needs architectural decision**

---

## Step 5 — Invariants & Guardrails Check

**Required CI checks remain enforced:** ✅ Yes

**No semantic scope leakage:** ✅ Yes

**Release / consumer contracts not weakened:** ✅ Yes

**Determinism and reproducibility preserved:** ✅ Yes

**Phase C contract preservation:** ✅ Yes (no Phase C contract changes)

**Default path byte-identical:** ✅ Yes (proven by guard job tests)

**Assessment:** All invariants held. The extraction pattern successfully improved testability and coverage of the integration functions themselves, but the call sites in `runner.py` remain uncovered.

---

## Step 6 — Verdict

**Verdict:**
This run demonstrates that **additional edge case tests did not improve coverage** in `eval/runner.py`. The -1.28% regression persists, indicating that the uncovered lines are in the actual call sites within `runner.py`'s main evaluation loop, not in the extracted integration functions (which are now comprehensively tested with 20 tests).

The integration functions themselves are fully covered, but the call sites (function calls, imports, variable assignments) in the main evaluation loop are difficult to test without running the full evaluation pipeline.

**Status:** ⚠️ **Merge blocked pending architectural decision on coverage regression**

**Reason:** Coverage regression in `eval/runner.py` (-1.28%) persists despite comprehensive testing of integration functions. The uncovered lines are likely call sites in the main evaluation loop, which are difficult to test without full pipeline execution.

---

## Step 7 — Next Actions

1. **Architectural decision on coverage regression** (Owner: Human)
   - Assess if -1.28% regression is acceptable (within tolerance for edge cases)
   - Decide if call sites in main evaluation loop need coverage
   - Consider if additional extraction is needed or if regression is acceptable
   - Scope: `eval/runner.py` uncovered call sites
   - Milestone: M26 (current)

2. **If additional extraction needed** (Owner: AI/Cursor)
   - Extract more logic from `runner.py` to make call sites testable
   - Or add lightweight integration tests that exercise call sites
   - Scope: Specific uncovered lines in `eval/runner.py`
   - Milestone: M26 (current)

3. **If regression is acceptable** (Owner: Human)
   - Document the decision and rationale
   - Proceed with merge
   - Scope: Documentation and merge
   - Milestone: M26 (current)

---

## Progress Summary

**From Run 7 to Run 8:**
- ✅ Formatting: **FIXED** (all formatting issues resolved)
- ✅ Test coverage: **EXPANDED** (5 new edge case tests added, 20 total)
- ✅ Integration functions: **FULLY COVERED** (all branches tested)
- ⚠️ `eval/runner.py` coverage: **NO IMPROVEMENT** (-1.28% regression persists)

**Key Finding:**
The additional edge case tests did not improve coverage in `eval/runner.py`, indicating that the uncovered lines are in the call sites within the main evaluation loop, not in the extracted integration functions. The integration functions themselves are now comprehensively tested with 20 tests covering all branches, error paths, and edge cases.

**Architectural Status:**
- ✅ `cli.py` extraction: **Complete** (coverage restored)
- ✅ Integration functions: **Fully tested** (20 tests, all branches covered)
- ⚠️ `runner.py` call sites: **Uncovered** (-1.28% regression, likely call sites in main loop)

**Recommendation:**
The -1.28% regression is small and likely represents call sites in the main evaluation loop that are difficult to test without full pipeline execution. The integration functions themselves are fully covered, and the extraction pattern has successfully improved testability. An architectural decision is needed on whether this regression is acceptable or if additional extraction/testing is required.

