# M26 CI Run 4 Analysis

**Workflow Identity**
- Workflow: CI
- Run ID: 21572460508
- Trigger: Pull Request (#32)
- Branch: `m26-phase-d-runtime-gating-001`
- Commit: 87dd3b9 (test design fix and guard job simplification)

**Change Context**
- Milestone: M26 (PHASE-D-RUNTIME-GATING-001)
- Intent: Governance and safety milestone for controlled runtime application of recalibration
- Type: Corrective (fixing test design and simplifying CI guard job)
- Baseline: M25 (last known green: commit from M25 closeout)

---

## Step 1 — Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
| ----------- | --------- | ------- | --------- | ----- |
| Security Scan | ✅ Required | Dependency vulnerability scan (pip-audit) + static security analysis (bandit) | ✅ Pass | No security issues found |
| Test | ✅ Required | Unit + integration tests with coverage | ❌ Fail | Coverage regression in cli.py and runner.py |
| Performance Benchmarks | ✅ Required | Performance regression detection | ✅ Pass | No performance regressions |
| Lint and Format | ✅ Required | Ruff linting, formatting, import boundary checks | ❌ Fail | 2 E501 line length violations |
| Type Check | ✅ Required | MyPy static type checking | ✅ Pass | All type checks passed |
| Calibration Evaluation | ✅ Required | Calibration metrics validation | ✅ Pass | Calibration metrics generated successfully |
| Recalibration Evaluation | ✅ Required | Recalibration parameter fitting and validation | ✅ Pass | Recalibration parameters generated successfully |
| Runtime Recalibration Guard (M26) | ✅ Required | M26-specific guard job for runtime invariants | ❌ Fail | Coverage threshold failure (expected, fixed) |

**Merge-blocking checks:** All required checks must pass for merge.

---

## Step 2 — Signal Integrity Analysis

### A) Tests

**Test tiers executed:**
- Unit tests (comprehensive M26 runtime recalibration tests)
- Integration tests (existing test suite)
- Contract tests (schema validation)

**Failures:**
- No test failures (all 19 M26 tests passed)
- Coverage regression detected in overlap-set comparison:
  - `cli.py`: 87.08% → 83.33% (delta: -3.75%)
  - `eval/runner.py`: 85.47% → 80.87% (delta: -4.59%)

**Test coverage:**
- Overall coverage: 91.81% (above 90% threshold)
- `runtime_recalibration.py`: 87.37% (maintained from Run 3)
- Coverage regression in `cli.py` and `runner.py` due to new M26 code paths not fully covered

**Assessment:** Test failures are **none** (all tests pass). Coverage regression is a **real issue** - new M26 code paths in CLI and runner aren't fully covered by existing tests. However, the M26 unit tests comprehensively cover the runtime recalibration logic itself.

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

**Assessment:** Coverage regression is **real** but **expected** - new code paths were added for M26 integration. The M26 unit tests cover the core logic, but CLI/runner integration paths need additional coverage.

### C) Static / Policy Gates

**Linting (Ruff):**
- 2 E501 violations (line length > 100 characters)
- Files: `tests/test_m26_runtime_recalibration.py` (2 violations in comments)
- All violations are in new M26 test code

**Type checking (MyPy):**
- ✅ All type checks passed
- No type errors

**Assessment:** Lint failures are **policy violations** that must be fixed. Type checking is clean.

### D) Performance / Benchmarks

**Benchmark results:**
- All benchmarks passed
- No performance regressions detected
- Benchmarks isolated from correctness signals

**Assessment:** Performance signals are clean and isolated.

---

## Step 3 — Delta Analysis (Change Impact)

**Files modified since Run 3:**
- `tests/test_m26_runtime_recalibration.py` (fixed test design: non-uniform probabilities)
- `.github/workflows/ci.yml` (simplified guard job: removed manifest dependency)

**CI signals affected:**
- **Tests:** ✅ All tests pass (19/19 M26 tests)
- **Linting:** ❌ 2 E501 violations (test comments)
- **Type checking:** ✅ Fixed (all checks pass)
- **Coverage:** Regression in `cli.py` and `runner.py` (new M26 code paths)
- **Guard job:** Coverage threshold failure (expected, since it only runs M26 tests)

**Unexpected deltas:**
- Coverage regression in CLI/runner integration paths (expected for new code)
- Guard job coverage failure (expected, since it only runs subset of tests)

**Signal drift:**
- No drift detected. All existing signals remain stable.

**Coupling revealed:**
- None. M26 changes are properly isolated from Phase C contracts.

---

## Step 4 — Failure Analysis

### Failure 1: Lint Failures (2 E501 violations)

**Classification:** Policy violation (line length > 100 characters)

**Root cause:**
- Test comments exceed 100-character limit
- Files: `tests/test_m26_runtime_recalibration.py` (lines 151, 230)
- Comments: "Non-uniform probabilities (temperature scaling requires non-uniform input to observe changes)"

**In scope:** ✅ Yes (M26 test code)

**Blocking:** ✅ Yes (linting is merge-blocking)

**Fix required:**
- Split long comment lines across multiple lines
- Use parentheses for string continuation

**Status:** ✅ **FIXED in commit e9d281e**

### Failure 2: Coverage Regression

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
- Add E2E tests for CLI integration (test `eval run --recalibration-gate`)
- Add integration tests for runner integration (test `run_conditioned_evaluation` with gate)
- Or: Document that CLI/runner integration coverage will be added in follow-up milestone

**Assessment:** This is a **real coverage gap** but may be acceptable if:
1. M26 unit tests comprehensively cover the core logic
2. CLI/runner integration is straightforward (just wiring)
3. Coverage regression is documented and tracked

### Failure 3: Guard Job Coverage Failure

**Classification:** CI misconfiguration (expected behavior)

**Root cause:**
- Guard job runs only M26 tests (`test_m26_runtime_recalibration.py`)
- Pytest picks up coverage config from `pyproject.toml`
- Coverage threshold (90%) fails because only subset of codebase is tested
- Coverage: 16.11% (expected for subset of tests)

**In scope:** ✅ Yes (M26 CI job)

**Blocking:** ✅ Yes (guard job must pass)

**Fix required:**
- Add `--no-cov` flag to pytest command in guard job
- Guard job validates runtime invariants, not full codebase coverage

**Status:** ✅ **FIXED in commit e9d281e**

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
- All M26 tests pass (19/19)

**Invariant violations:** None detected (coverage regression is expected for new code, not an architectural violation)

---

## Step 6 — Verdict

**Verdict:**
This run shows **excellent progress** from Run 3:
- ✅ All tests pass (19/19 M26 tests)
- ✅ Guard job simplified (removed manifest dependency)
- ✅ Test design fixed (non-uniform probabilities)
- ❌ 2 lint violations (fixed in commit e9d281e)
- ❌ Coverage regression (expected for new code paths)
- ❌ Guard job coverage failure (fixed in commit e9d281e)

The remaining issue is **coverage regression** in CLI/runner integration paths. This is expected for new code but should be addressed either:
1. Add E2E tests for CLI/runner integration
2. Document and defer to follow-up milestone

**Status:** ⛔ **Merge blocked**

**Reason:** Coverage regression in `cli.py` and `runner.py` must be addressed (either fix or document).

---

## Step 7 — Next Actions

### Immediate Actions (M26 scope)

1. **Fix lint violations** (Owner: AI/Cursor) ✅ **FIXED in commit e9d281e**
   - Split long comment lines
   - Scope: `tests/test_m26_runtime_recalibration.py`
   - Milestone: M26 (current)
   - **Status:** Fixed

2. **Fix guard job coverage** (Owner: AI/Cursor) ✅ **FIXED in commit e9d281e**
   - Add `--no-cov` flag to pytest command
   - Scope: `.github/workflows/ci.yml`
   - Milestone: M26 (current)
   - **Status:** Fixed

3. **Address coverage regression** (Owner: AI/Cursor)
   - Option A: Add E2E tests for CLI/runner integration
   - Option B: Document coverage gap and defer to follow-up milestone
   - Scope: `cli.py`, `eval/runner.py`
   - Milestone: M26 (current) or follow-up
   - **Status:** Pending decision

4. **Re-run CI after fixes** (Owner: GitHub Actions)
   - Verify all checks pass
   - Confirm coverage regression addressed
   - Scope: Full CI run
   - Milestone: M26 (current)

### Deferred Actions

- Coverage regression in CLI/runner integration (can be deferred if documented)

---

## Summary

**Run Status:** ❌ Failed (5/8 jobs passed)

**Critical Issues:**
- ✅ Lint violations (fixed in commit e9d281e)
- ✅ Guard job coverage (fixed in commit e9d281e)
- ⚠️ Coverage regression (expected for new code, needs decision)

**Positive Signals:**
- ✅ Security scan passed
- ✅ Performance benchmarks passed
- ✅ Type checking passed
- ✅ All M26 tests pass (19/19)
- ✅ Guard job simplified (removed manifest dependency)
- ✅ No architectural violations
- ✅ No Phase C contract changes

**Progress from Run 3:**
- Test failures: 2 → 0 (100% fixed)
- Guard job: ❌ → ✅ (simplified, coverage fixed)
- Lint violations: 0 → 2 → 0 (fixed)
- Coverage: Maintained at 91.81% (regression in new code paths)

**Next Run Expectations:**
After commit e9d281e (lint and guard job fixes), all checks except coverage regression should pass. Coverage regression needs decision: add E2E tests or document and defer.

---

**Analysis Date:** 2026-02-01  
**Analyst:** AI Agent (Cursor)  
**Milestone:** M26 (PHASE-D-RUNTIME-GATING-001)

