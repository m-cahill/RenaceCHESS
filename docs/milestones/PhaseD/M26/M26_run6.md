# M26 CI Run 6 Analysis

**Workflow Identity**
- Workflow: CI
- Run ID: 21573752972
- Trigger: Pull Request (#32)
- Branch: `m26-phase-d-runtime-gating-001`
- Commit: 481f288 (fix type hints in resolve_recalibration_gate_from_args)

**Change Context**
- Milestone: M26 (PHASE-D-RUNTIME-GATING-001)
- Intent: Governance and safety milestone for controlled runtime application of recalibration
- Type: Corrective (extract CLI gate loading logic + fix type hints)
- Baseline: M25 (last known green: commit from M25 closeout)

---

## Step 1 — Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
| ----------- | --------- | ------- | --------- | ----- |
| Security Scan | ✅ Required | Dependency vulnerability scan (pip-audit) + static security analysis (bandit) | ✅ Pass | No security issues found |
| Test | ✅ Required | Unit + integration tests with coverage | ❌ Fail | Coverage regression in eval/runner.py |
| Performance Benchmarks | ✅ Required | Performance regression detection | ✅ Pass | No performance regressions |
| Lint and Format | ✅ Required | Ruff linting, formatting, import boundary checks | ❌ Fail | Formatting issues in cli.py and test_m26_cli_integration.py |
| Type Check | ✅ Required | MyPy static type checking | ✅ Pass | All type checks passed (fixed with TYPE_CHECKING) |
| Calibration Evaluation | ✅ Required | Calibration metrics validation | ✅ Pass | Calibration metrics generated successfully |
| Recalibration Evaluation | ✅ Required | Recalibration parameter fitting and validation | ✅ Pass | Recalibration parameters generated successfully |
| Runtime Recalibration Guard (M26) | ✅ Required | M26-specific guard job for runtime invariants | ✅ Pass | All guard tests passed |

**Merge-blocking checks:** All required checks must pass for merge.

---

## Step 2 — Signal Integrity Analysis

### A) Tests

**Test tiers executed:**
- Unit tests (comprehensive M26 runtime recalibration tests)
- Integration tests (existing test suite + new CLI gate loading tests)
- Contract tests (schema validation)

**Failures:**
- No test failures (all tests pass)
- Coverage regression detected in overlap-set comparison:
  - `eval/runner.py`: 85.47% → 80.87% (delta: -4.59%)
  - **Note:** `cli.py` is NO LONGER in the regression list (was 87.08% → 83.33% in Run 5)

**Assessment:** The refactor to extract `resolve_recalibration_gate_from_args()` successfully restored coverage in `cli.py`. The remaining regression in `eval/runner.py` needs investigation.

### B) Coverage

**Coverage type:** Line coverage with overlap-set non-regression enforcement

**Coverage scoping:**
- Overlap-set comparison (files that existed in baseline)
- 0.5% tolerance for minor fluctuations
- New files evaluated independently

**Exclusions:** None documented in this run

**Assessment:** Coverage signal is clean. The `cli.py` regression is resolved, confirming the architectural fix worked.

### C) Static / Policy Gates

**Linting (Ruff):**
- ❌ Formatting issues detected:
  - `src/renacechess/cli.py` needs reformatting
  - `tests/test_m26_cli_integration.py` needs reformatting
- These are auto-fixable with `ruff format`

**Type checking (MyPy):**
- ✅ All type checks passed
- Fixed with `TYPE_CHECKING` import for forward references

**Assessment:** Formatting issues are trivial and auto-fixable. Type checking is clean.

---

## Step 3 — Delta Analysis (Change Impact)

**Files modified since Run 5:**
- `src/renacechess/cli.py` (extracted `resolve_recalibration_gate_from_args()` function, added TYPE_CHECKING imports)
- `tests/test_m26_cli_gate_loading.py` (new file with targeted unit tests)

**CI signals affected:**
- **Tests:** ✅ All tests pass (no changes)
- **Linting:** ❌ Formatting issues (auto-fixable)
- **Type checking:** ✅ Fixed (all checks pass)
- **Coverage:** Regression in `eval/runner.py` persists, but `cli.py` regression is RESOLVED
- **Guard job:** ✅ Fixed (all guard tests pass)

**Unexpected deltas:**
- ✅ **Positive:** `cli.py` coverage regression resolved (architectural fix successful)
- ⚠️ **Remaining:** `eval/runner.py` coverage regression persists (needs investigation)
- ⚠️ **Removed from regression:** `models/baseline_v1.py` is no longer in the regression list (was -3.51% in Run 5)

---

## Step 4 — Failure Analysis

### Failure 1: Formatting Issues

**Classification:** CI misconfiguration (auto-fixable)

**Root cause:**
- Files need reformatting with `ruff format`
- `src/renacechess/cli.py` and `tests/test_m26_cli_integration.py`

**In scope:** ✅ Yes (M26 code)

**Blocking:** ✅ Yes (formatting is merge-blocking)

**Fix required:**
- Run `ruff format` on affected files
- Commit and push

**Status:** ⚠️ **Trivial fix required**

### Failure 2: Coverage Regression in eval/runner.py

**Classification:** Coverage gap (needs investigation)

**Root cause:**
- `eval/runner.py`: 85.47% → 80.87% (delta: -4.59%)
- Likely related to new M26 integration paths not fully covered
- The `run_conditioned_evaluation` function receives gate/params but some code paths may not be exercised

**In scope:** ✅ Yes (M26 integration)

**Blocking:** ✅ Yes (coverage regression is merge-blocking)

**Fix required:**
- Investigate which lines in `eval/runner.py` are uncovered
- Add targeted tests to exercise those paths
- May need to test the actual `run_conditioned_evaluation` call with gate/params

**Status:** ⚠️ **Investigation required**

---

## Step 5 — Invariants & Guardrails Check

**Required CI checks remain enforced:** ✅ Yes

**No semantic scope leakage:** ✅ Yes

**Release / consumer contracts not weakened:** ✅ Yes

**Determinism and reproducibility preserved:** ✅ Yes

**Phase C contract preservation:** ✅ Yes (no Phase C contract changes)

**Default path byte-identical:** ✅ Yes (proven by guard job tests)

**Assessment:** All invariants held. The architectural refactor improved testability without changing behavior.

---

## Step 6 — Verdict

**Verdict:**
This run demonstrates **significant progress** on M26. The architectural refactor to extract `resolve_recalibration_gate_from_args()` successfully resolved the `cli.py` coverage regression, proving that the extraction was the correct fix. However, two issues remain: (1) trivial formatting issues that are auto-fixable, and (2) a coverage regression in `eval/runner.py` that needs investigation and targeted test coverage.

The refactor itself is sound and improves the codebase's testability without changing runtime behavior. The remaining coverage gap in `eval/runner.py` suggests that while the gate loading logic is now well-tested, the integration point where the gate is passed to `run_conditioned_evaluation` may need additional test coverage.

**Status:** ⛔ **Merge blocked**

**Reason:** Formatting issues and coverage regression in `eval/runner.py` must be addressed before merge.

---

## Step 7 — Next Actions

1. **Fix formatting issues** (Owner: AI/Cursor)
   - Run `ruff format src/renacechess/cli.py tests/test_m26_cli_integration.py`
   - Commit and push
   - Scope: Formatting only
   - Milestone: M26 (current)

2. **Investigate and fix eval/runner.py coverage regression** (Owner: AI/Cursor)
   - Identify uncovered lines in `eval/runner.py` related to M26 integration
   - Add targeted tests to exercise `run_conditioned_evaluation` with gate/params
   - Verify coverage is restored
   - Scope: `eval/runner.py` M26 integration paths
   - Milestone: M26 (current)

3. **Re-run CI after fixes** (Owner: CI system)
   - Verify all checks pass
   - Confirm coverage regression cleared
   - Scope: Full CI run
   - Milestone: M26 (current)

---

## Progress Summary

**From Run 5 to Run 6:**
- ✅ `cli.py` coverage regression: **RESOLVED** (87.08% → 83.33% → **no longer in regression list**)
- ✅ Type checking: **FIXED** (TYPE_CHECKING imports)
- ✅ Guard job: **PASSING** (all tests pass)
- ⚠️ Formatting: **Needs fix** (auto-fixable)
- ⚠️ `eval/runner.py` coverage: **Still regressed** (needs investigation)

**Key Achievement:**
The architectural refactor to extract `resolve_recalibration_gate_from_args()` was successful. This proves that the extraction approach was correct and that the CLI gate loading logic is now properly testable. The remaining `eval/runner.py` regression is a separate issue that needs targeted test coverage for the integration point.

