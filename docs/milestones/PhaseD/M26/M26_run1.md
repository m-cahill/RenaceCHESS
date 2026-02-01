# M26 CI Run 1 Analysis

**Workflow Identity**
- Workflow: CI
- Run ID: 21571866477
- Trigger: Pull Request (#32)
- Branch: `m26-phase-d-runtime-gating-001`
- Commit: 76a0db3 (initial M26 implementation)

**Change Context**
- Milestone: M26 (PHASE-D-RUNTIME-GATING-001)
- Intent: Governance and safety milestone for controlled runtime application of recalibration
- Type: Hardening / Governance
- Baseline: M25 (last known green: commit from M25 closeout)

---

## Step 1 — Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
| ----------- | --------- | ------- | --------- | ----- |
| Security Scan | ✅ Required | Dependency vulnerability scan (pip-audit) + static security analysis (bandit) | ✅ Pass | No security issues found |
| Test | ✅ Required | Unit + integration tests with coverage | ❌ Fail | 9 test failures in M26 runtime recalibration tests |
| Performance Benchmarks | ✅ Required | Performance regression detection | ✅ Pass | No performance regressions |
| Lint and Format | ✅ Required | Ruff linting, formatting, import boundary checks | ❌ Fail | 7 E501 line length violations |
| Type Check | ✅ Required | MyPy static type checking | ❌ Fail | 4 type errors in runtime_recalibration.py |
| Calibration Evaluation | ✅ Required | Calibration metrics validation | ✅ Pass | Calibration metrics generated successfully |
| Recalibration Evaluation | ✅ Required | Recalibration parameter fitting and validation | ✅ Pass | Recalibration parameters generated successfully |
| Runtime Recalibration Guard (M26) | ✅ Required | M26-specific guard job for byte-identical default path | ❌ Fail | Job setup failed (artifact download issue) |

**Merge-blocking checks:** All required checks must pass for merge.

---

## Step 2 — Signal Integrity Analysis

### A) Tests

**Test tiers executed:**
- Unit tests (comprehensive M26 runtime recalibration tests)
- Integration tests (existing test suite)
- Contract tests (schema validation)

**Failures:**
- 9 failures in `test_m26_runtime_recalibration.py`
- Root cause: `TypeError: BaseModel.model_dump_json() got an unexpected keyword argument 'mode'`
- All failures are in the same category: incorrect Pydantic API usage

**Test coverage:**
- Overall coverage: 90.92% (above 90% threshold)
- `runtime_recalibration.py`: 32.63% (new module, expected low initial coverage)
- All other modules maintained or improved coverage

**Assessment:** Failures are **real correctness failures** due to incorrect Pydantic API usage. The tests themselves are well-designed and comprehensive.

### B) Coverage

**Coverage type:** Line + branch coverage
- Enforced threshold: 90% (absolute)
- PR mode: Overlap-set comparison (baseline generation failed, skipped)
- Coverage scoped correctly to source code
- Exclusions: None documented

**Coverage results:**
- Total: 90.92% (4580 statements, 291 missed, 1322 branches, 171 partial)
- New module `runtime_recalibration.py`: 32.63% (67 statements, 40 missed, 28 branches, 0 partial)
- All existing modules maintained coverage above threshold

**Assessment:** Coverage is correctly scoped. New module has low coverage due to test failures preventing execution.

### C) Static / Policy Gates

**Linting (Ruff):**
- 7 E501 violations (line length > 100 characters)
- Files affected: `cli.py`, `contracts/models.py`, `runner.py`
- All violations are in new M26 code (documentation strings and error messages)

**Type checking (MyPy):**
- 4 errors in `runtime_recalibration.py`
- All errors: `Unexpected keyword argument "mode" for "model_dump_json"`
- Root cause: Pydantic 2.x API change (`model_dump_json()` does not accept `mode` parameter)

**Assessment:** All static gate failures are **in scope** for M26 and represent real issues that must be fixed.

### D) Performance / Benchmarks

**Benchmark results:**
- All benchmarks passed
- No performance regressions detected
- Benchmarks isolated from correctness signals

**Assessment:** Performance signals are clean and isolated.

---

## Step 3 — Delta Analysis (Change Impact)

**Files modified:**
- `src/renacechess/contracts/models.py` (added `RecalibrationGateV1`)
- `src/renacechess/contracts/schemas/v1/recalibration_gate.v1.schema.json` (new file)
- `src/renacechess/eval/runtime_recalibration.py` (new module)
- `src/renacechess/eval/runner.py` (wired runtime recalibration)
- `src/renacechess/cli.py` (added CLI arguments)
- `tests/test_m26_runtime_recalibration.py` (new comprehensive test suite)
- `.github/workflows/ci.yml` (added `runtime-recalibration-guard` job)

**CI signals affected:**
- **Tests:** New test failures (9) due to Pydantic API misuse
- **Linting:** New E501 violations (7) in new code
- **Type checking:** New MyPy errors (4) in new code
- **Coverage:** New module with low coverage due to test failures
- **New CI job:** Runtime Recalibration Guard job failed due to artifact download issue

**Unexpected deltas:**
- None. All failures are directly related to M26 implementation issues.

**Signal drift:**
- No drift detected. All existing signals remain stable.

**Coupling revealed:**
- None. M26 changes are properly isolated from Phase C contracts.

---

## Step 4 — Failure Analysis

### Failure 1: Test Failures (9 failures)

**Classification:** Correctness bug (Pydantic API misuse)

**Root cause:**
- `model_dump_json(by_alias=True, mode="json")` is invalid in Pydantic 2.x
- Should use `model_dump(by_alias=True)` and pass result to `canonical_hash()`

**In scope:** ✅ Yes (M26 implementation bug)

**Blocking:** ✅ Yes (must fix before merge)

**Fix required:**
- Replace all `model_dump_json(mode="json")` calls with `model_dump()`
- Update hash computation to use dict from `model_dump()` directly

### Failure 2: Lint Failures (7 E501 violations)

**Classification:** Policy violation (line length > 100 characters)

**Root cause:**
- Long error messages and documentation strings exceed 100-character limit
- Files: `cli.py` (3 violations), `contracts/models.py` (2 violations), `runner.py` (2 violations)

**In scope:** ✅ Yes (M26 code)

**Blocking:** ✅ Yes (linting is merge-blocking)

**Fix required:**
- Split long strings across multiple lines
- Use parentheses for string concatenation

### Failure 3: Type Check Failures (4 MyPy errors)

**Classification:** Type error (same root cause as test failures)

**Root cause:**
- Same Pydantic API misuse as test failures
- MyPy correctly identifies invalid `mode` parameter

**In scope:** ✅ Yes (M26 implementation bug)

**Blocking:** ✅ Yes (type checking is merge-blocking)

**Fix required:**
- Same fix as Failure 1 (Pydantic API correction)

### Failure 4: Runtime Recalibration Guard Job Failure

**Classification:** CI misconfiguration

**Root cause:**
- Job attempts to download artifact from `recalibration-eval` job
- Artifact download action SHA may be incorrect or artifact doesn't exist
- Error: "An action could not be found at the URI"

**In scope:** ✅ Yes (M26 CI job)

**Blocking:** ✅ Yes (M26-specific guard job must pass)

**Fix required:**
- Make guard job self-contained (generate test parameters instead of downloading)
- Remove dependency on `recalibration-eval` job artifact

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

**Determinism and reproducibility preserved:** ✅ Yes (when fixed)
- Default path (gate disabled) will be byte-identical once Pydantic API is corrected
- Recalibration application is deterministic (temperature scaling)

**Invariant violations:** None detected (all failures are implementation bugs, not architectural violations)

---

## Step 6 — Verdict

**Verdict:**
This run surfaces **real correctness and policy issues** that must be fixed before merge. All failures are:
1. **In scope** for M26
2. **Blocking** (merge-blocking checks)
3. **Fixable** (clear root causes identified)

The failures are **not** architectural violations or scope creep. They are implementation bugs (Pydantic API misuse) and policy violations (line length) that can be corrected in a follow-up commit.

**Status:** ⛔ **Merge blocked**

**Reason:** Multiple merge-blocking check failures (tests, linting, type checking, CI guard job)

---

## Step 7 — Next Actions

### Immediate Actions (M26 scope)

1. **Fix Pydantic API usage** (Owner: AI/Cursor)
   - Replace `model_dump_json(mode="json")` with `model_dump()` in `runtime_recalibration.py`
   - Update hash computation to use dict directly
   - Scope: 4 locations in `runtime_recalibration.py`
   - Milestone: M26 (current)

2. **Fix line length violations** (Owner: AI/Cursor)
   - Split long strings in `cli.py`, `contracts/models.py`, `runner.py`
   - Scope: 7 E501 violations
   - Milestone: M26 (current)

3. **Fix CI guard job** (Owner: AI/Cursor)
   - Make guard job self-contained (generate test parameters)
   - Remove artifact download dependency
   - Scope: `.github/workflows/ci.yml`
   - Milestone: M26 (current)

4. **Re-run CI after fixes** (Owner: GitHub Actions)
   - Verify all checks pass
   - Confirm byte-identical default path
   - Scope: Full CI run
   - Milestone: M26 (current)

### Deferred Actions

None. All issues are fixable within M26 scope.

---

## Summary

**Run Status:** ❌ Failed (4/8 jobs passed)

**Critical Issues:**
- Pydantic API misuse (tests + type checking)
- Line length violations (linting)
- CI guard job configuration (artifact download)

**Positive Signals:**
- Security scan passed
- Performance benchmarks passed
- Calibration/recalibration evaluation passed
- Coverage maintained above threshold
- No architectural violations
- No Phase C contract changes

**Next Run Expectations:**
After fixes are applied, all checks should pass. The implementation is sound; failures are due to API misuse and formatting issues that are straightforward to correct.

---

**Analysis Date:** 2026-02-01  
**Analyst:** AI Agent (Cursor)  
**Milestone:** M26 (PHASE-D-RUNTIME-GATING-001)

