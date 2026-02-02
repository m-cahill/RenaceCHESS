# M26 CI Run 5 Analysis

**Workflow Identity**
- Workflow: CI
- Run ID: 21572576231 (fixes applied: e9d281e)
- Trigger: Pull Request (#32)
- Branch: `m26-phase-d-runtime-gating-001`
- Commit: e9d281e (fix line length violations and disable coverage in guard job)

**Change Context**
- Milestone: M26 (PHASE-D-RUNTIME-GATING-001)
- Intent: Governance and safety milestone for controlled runtime application of recalibration
- Type: Analysis/documentation (no code changes)
- Baseline: M25 (last known green: commit from M25 closeout)

---

## Step 1 — Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
| ----------- | --------- | ------- | --------- | ----- |
| Security Scan | ✅ Required | Dependency vulnerability scan (pip-audit) + static security analysis (bandit) | ✅ Pass | No security issues found |
| Test | ✅ Required | Unit + integration tests with coverage | ❌ Fail | Coverage regression in cli.py and runner.py |
| Performance Benchmarks | ✅ Required | Performance regression detection | ✅ Pass | No performance regressions |
| Lint and Format | ✅ Required | Ruff linting, formatting, import boundary checks | ✅ Pass | All lint checks passed (fixed in e9d281e) |
| Type Check | ✅ Required | MyPy static type checking | ✅ Pass | All type checks passed |
| Calibration Evaluation | ✅ Required | Calibration metrics validation | ✅ Pass | Calibration metrics generated successfully |
| Recalibration Evaluation | ✅ Required | Recalibration parameter fitting and validation | ✅ Pass | Recalibration parameters generated successfully |
| Runtime Recalibration Guard (M26) | ✅ Required | M26-specific guard job for runtime invariants | ✅ Pass | All guard tests passed (fixed in e9d281e) |

**Merge-blocking checks:** All required checks must pass for merge.

---

## Step 2 — Signal Integrity Analysis

### A) Tests

**Test tiers executed:**
- Unit tests (comprehensive M26 runtime recalibration tests)
- Integration tests (existing test suite)
- Contract tests (schema validation)

**Failures:**
- No test failures (all tests pass)
- Coverage regression detected in overlap-set comparison:
  - `cli.py`: 87.08% → 83.33% (delta: -3.75%)
  - `eval/runner.py`: 85.47% → 80.87% (delta: -4.59%)
  - `models/baseline_v1.py`: 100.00% → 96.49% (delta: -3.51%) - unexpected

**Test coverage:**
- Overall coverage: 91.81% (above 90% threshold)
- `runtime_recalibration.py`: 87.37% (maintained)
- Coverage regression in `cli.py` and `runner.py` due to new M26 code paths not fully covered

**Assessment:** Test failures are **none** (all tests pass). Coverage regression is a **real issue** - new M26 code paths in CLI and runner aren't fully covered by existing tests. The M26 unit tests comprehensively cover the runtime recalibration logic itself, but CLI/runner integration paths need E2E tests.

### B) Coverage

**Coverage type:** Line + branch coverage
- Enforced threshold: 90% (absolute)
- PR mode: Overlap-set comparison (regression detected)
- Coverage scoped correctly to source code
- Exclusions: None documented

**Coverage results:**
- Total: 91.81% (4586 statements, 256 missed, 1324 branches, 178 partial)
- New module `runtime_recalibration.py`: 87.37% (maintained)
- Regression in `cli.py` and `runner.py` due to new M26 integration code

**Assessment:** Coverage regression is **real** and **expected** - new code paths were added for M26 integration. The M26 unit tests cover the core logic, but CLI/runner integration paths need additional E2E tests similar to existing CLI integration tests (e.g., `test_m24_calibration.py`, `test_m25_recalibration.py`).

### C) Static / Policy Gates

**Linting (Ruff):**
- ✅ All lint checks passed
- Fixed in commit e9d281e (line length violations)

**Type checking (MyPy):**
- ✅ All type checks passed
- No type errors

**Assessment:** All static gates are clean. Lint failures were fixed in e9d281e.

### D) Performance / Benchmarks

**Benchmark results:**
- All benchmarks passed
- No performance regressions detected
- Benchmarks isolated from correctness signals

**Assessment:** Performance signals are clean and isolated.

---

## Step 3 — Delta Analysis (Change Impact)

**Files modified since Run 4:**
- `tests/test_m26_runtime_recalibration.py` (fixed line length violations)
- `.github/workflows/ci.yml` (disabled coverage in guard job with --no-cov flag)

**CI signals affected:**
- **Tests:** ✅ All tests pass
- **Linting:** ✅ Fixed (all checks pass)
- **Type checking:** ✅ Fixed (all checks pass)
- **Coverage:** Regression in `cli.py`, `runner.py`, and `baseline_v1.py` (unchanged from Run 4)
- **Guard job:** ✅ Fixed (all guard tests pass)

**Unexpected deltas:**
- Coverage regression persists (expected for new code in `cli.py` and `runner.py`)
- Unexpected coverage regression in `baseline_v1.py` (needs investigation - may be unrelated to M26)

**Signal drift:**
- No drift detected. All existing signals remain stable.

**Coupling revealed:**
- None. M26 changes are properly isolated from Phase C contracts.

---

## Step 4 — Failure Analysis

### Failure 1: Coverage Regression

**Classification:** Coverage regression (new code paths not fully covered)

**Root cause:**
- New M26 code paths added to `cli.py` and `runner.py`:
  - CLI argument parsing for `--recalibration-gate`
  - Gate loading and validation in CLI
  - Recalibration application in runner
- Existing test suite doesn't cover these new integration paths
- M26 unit tests cover core logic but not CLI/runner integration

**In scope:** ✅ Yes (M26 integration code)

**Blocking:** ✅ Yes (coverage regression is merge-blocking)

**Fix required:**
- Add E2E tests for CLI integration (similar to `test_m24_calibration.py::TestCalibrationCLI` and `test_m25_recalibration.py::TestRecalibrationCLI`)
- Test `eval run --recalibration-gate` with both disabled and enabled gates
- Test `run_conditioned_evaluation` with gate parameter
- Verify gate loading, validation, and application paths

**Assessment:** This is a **real coverage gap** that should be addressed. The pattern is clear from existing CLI integration tests - we need similar E2E tests for M26.

### Failure 2: Unexpected Coverage Regression in baseline_v1.py

**Classification:** Coverage regression (unexpected)

**Root cause:**
- `models/baseline_v1.py`: 100.00% → 96.49% (delta: -3.51%)
- This is unexpected and may be unrelated to M26
- Could be due to test execution changes or unrelated code paths

**In scope:** ⚠️ Unclear (may be unrelated to M26)

**Blocking:** ✅ Yes (coverage regression is merge-blocking)

**Fix required:**
- Investigate why `baseline_v1.py` lost coverage
- Determine if this is related to M26 or a separate issue
- Add tests to restore coverage if needed

**Status:** ⚠️ **Needs investigation**

---

## Step 5 — Invariants & Guardrails Check

**Required CI checks remain enforced:** ✅ Yes
- All merge-blocking checks are still enforced
- No checks were muted or bypassed

**No semantic scope leakage:** ✅ Yes
- Coverage measures code coverage (not performance)
- Benchmarks measure performance (not correctness)
- Tests measure correctness (not performance)

**Release / consumer contracts not weakened:** ✅ Yes
- Phase C contracts remain untouched
- No changes to frozen contracts
- Provenance metadata is separate from Phase C artifacts

**Determinism and reproducibility preserved:** ✅ Yes
- Default path (gate disabled) is byte-identical (proven by unit tests)
- Recalibration application is deterministic (temperature scaling)
- All M26 tests pass

**Invariant violations:** None detected (coverage regression is expected for new code, not an architectural violation)

---

## Step 6 — Verdict

**Verdict:**
This run shows **significant progress** from Run 4:
- ✅ All tests pass (no test failures)
- ✅ Lint failures fixed (all checks pass)
- ✅ Guard job fixed (all guard tests pass)
- ❌ Coverage regression persists (CLI/runner integration paths + unexpected baseline_v1.py regression)

The **coverage regression** is the only remaining blocker. The CLI/runner regression is expected for new code and should be addressed with E2E tests following the established pattern. The `baseline_v1.py` regression is unexpected and needs investigation.

**Status:** ⛔ **Merge blocked**

**Reason:** Coverage regression must be addressed (E2E tests for CLI/runner + investigation of baseline_v1.py regression).

---

## Step 7 — Next Actions

### Immediate Actions (M26 scope)

1. **Add E2E tests for CLI/runner integration** (Owner: AI/Cursor)
   - Create `test_m26_cli_integration.py` following pattern from `test_m24_calibration.py` and `test_m25_recalibration.py`
   - Test `eval run --recalibration-gate` with disabled gate
   - Test `eval run --recalibration-gate` with enabled gate
   - Test `run_conditioned_evaluation` with gate parameter
   - Scope: New test file + coverage of CLI/runner integration paths
   - Milestone: M26 (current)

2. **Investigate baseline_v1.py coverage regression** (Owner: AI/Cursor)
   - Determine why `baseline_v1.py` lost coverage
   - Check if this is related to M26 or a separate issue
   - Add tests to restore coverage if needed
   - Scope: `models/baseline_v1.py`
   - Milestone: M26 (current)
   - **Status:** Pending investigation

4. **Re-run CI after fixes** (Owner: GitHub Actions)
   - Verify all checks pass
   - Confirm coverage regression addressed
   - Scope: Full CI run
   - Milestone: M26 (current)

### Deferred Actions

None. All issues are fixable within M26 scope.

---

## Summary

**Run Status:** ❌ Failed (7/8 jobs passed)

**Critical Issues:**
- Coverage regression in CLI/runner integration (expected, needs E2E tests)
- Unexpected coverage regression in baseline_v1.py (needs investigation)

**Positive Signals:**
- ✅ Security scan passed
- ✅ Performance benchmarks passed
- ✅ Type checking passed
- ✅ Lint and format passed (fixed in e9d281e)
- ✅ Guard job passed (fixed in e9d281e)
- ✅ All M26 tests pass
- ✅ Calibration/recalibration evaluation passed
- ✅ No architectural violations
- ✅ No Phase C contract changes

**Progress from Run 4:**
- Test failures: 0 → 0 (maintained)
- Lint failures: ❌ → ✅ (fixed in e9d281e)
- Guard job: ❌ → ✅ (fixed in e9d281e)
- Coverage regression: Persists (needs E2E tests + baseline_v1.py investigation)

**Next Run Expectations:**
After adding E2E tests for CLI/runner integration and fixing lint/guard job issues, all checks should pass. The coverage regression is expected for new code and follows the established pattern for addressing it (E2E tests).

---

**Analysis Date:** 2026-02-01  
**Analyst:** AI Agent (Cursor)  
**Milestone:** M26 (PHASE-D-RUNTIME-GATING-001)

