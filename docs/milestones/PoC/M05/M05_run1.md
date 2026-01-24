# M05 CI Run 1 Analysis

**Workflow:** CI  
**Run ID:** 21306722594  
**Run URL:** https://github.com/m-cahill/RenaceCHESS/actions/runs/21306722594  
**Trigger:** Pull Request #7 (`m05-labeled-evaluation` → `main`)  
**Branch:** `m05-labeled-evaluation`  
**Commit SHA:** `dec31e9c4c35dfdf4eb7ebed9314838b2399f81e`  
**Status:** ✅ **SUCCESS**  
**Created:** 2026-01-24T01:24:57Z  
**Completed:** 2026-01-24T01:25:29Z  
**Duration:** ~32 seconds

---

## Change Context

**Milestone:** M05 — Ground-Truth Labeled Evaluation v1  
**Objective:** Add `chosenMove` optional field to Context Bridge payload, implement accuracy metrics computation, and create evaluation report schema v2.

**Change Intent:**
- Add optional `chosenMove` field to Context Bridge payload (v1-compatible extension)
- Update dataset builder to capture moves from PGN
- Create evaluation report schema v2 with accuracy metrics
- Extend evaluation harness to compute accuracy (top-1, top-K, coverage)
- Extend CLI with `--compute-accuracy` and `--top-k` flags

**Run Type:** Corrective (addressed formatting and coverage issues from initial run)

**Baseline Reference:** Last trusted green commit on `main` (M04 completion)

---

## Step 1 — Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
|------------|-----------|---------|-----------|-------|
| Lint and Format | ✅ Required | Enforce code style and formatting | ✅ PASS | Ruff lint + format check |
| Type Check | ✅ Required | Static type checking with MyPy | ✅ PASS | All type checks passed |
| Test | ✅ Required | Run test suite with coverage | ✅ PASS | 204 tests passed, 92.38% coverage |

**Merge-Blocking Checks:** All three jobs are merge-blocking.

**Informational Checks:** None

**Bypassed Checks:** None

---

## Step 2 — Signal Integrity Analysis

### A) Tests

**Test Tiers Executed:**
- Unit tests (model validation, schema validation)
- Integration tests (end-to-end dataset build and evaluation)
- Contract tests (schema validation against JSON Schema)
- Golden file tests (determinism verification)

**Test Results:**
- **Total:** 204 tests
- **Passed:** 204 (100%)
- **Failed:** 0
- **Warnings:** 9 (all related to small shard size in test fixtures, expected)

**Test Coverage for M05 Changes:**
- `test_m05_chosen_move.py` — 4 tests (schema validation, backward compatibility)
- `test_m05_accuracy_metrics.py` — 5 tests (accuracy computation correctness)
- `test_m05_eval_report_v2.py` — 5 tests (v2 schema validation)
- `test_m05_labeled_evaluation.py` — 5 tests (integration and determinism)
- `test_cli_eval_coverage.py` — 5 tests (CLI eval command coverage)

**Failures:** None. All tests passed.

**Missing Tests:** None identified. All new functionality is covered.

### B) Coverage

**Coverage Type:** Line + Branch coverage (pytest-cov)

**Coverage Results:**
- **Total Coverage:** 92.38% (exceeds 90% threshold)
- **Statements:** 1,285 total, 68 missed
- **Branches:** 342 total, 48 partial

**Key File Coverage:**
- `cli.py`: 88.34% (14 lines missed — error handling paths)
- `contracts/models.py`: 100.00% (all models covered)
- `dataset/builder.py`: 98.60% (1 line missed — edge case)
- `eval/metrics.py`: 91.87% (3 lines missed — edge cases)
- `eval/report.py`: 87.38% (3 lines missed — error paths)
- `eval/runner.py`: 89.43% (5 lines missed — error handling)

**Coverage Exclusions:** None documented. All code is in scope.

**Coverage Assessment:** ✅ **PASS** — Exceeds 90% threshold. M05 changes are well-tested.

### C) Static / Policy Gates

**Linting (Ruff):**
- ✅ All checks passed
- No violations detected

**Formatting (Ruff format):**
- ✅ All files formatted correctly
- 70 files already formatted (no changes needed)

**Type Checking (MyPy):**
- ✅ All type checks passed
- No type errors detected

**Policy Assessment:** All gates enforce current reality. No legacy assumptions detected.

### D) Performance / Benchmarks

**Not Applicable:** No performance benchmarks in this workflow.

---

## Step 3 — Delta Analysis (Change Impact)

### Files Modified

**Core Changes:**
- `src/renacechess/contracts/models.py` — Added `ChosenMove`, `AccuracyMetrics`, `EvalMetricsV2`, `EvalReportV2`
- `src/renacechess/contracts/schemas/v1/context_bridge.schema.json` — Added optional `chosenMove` field
- `src/renacechess/contracts/schemas/v1/eval_report.v2.schema.json` — New schema file
- `src/renacechess/dataset/builder.py` — Added `chosenMove` capture from PGN
- `src/renacechess/demo/pgn_overlay.py` — Added `chosen_move` parameter
- `src/renacechess/eval/metrics.py` — Added accuracy metrics computation
- `src/renacechess/eval/runner.py` — Added accuracy computation support
- `src/renacechess/eval/report.py` — Added v2 report building
- `src/renacechess/cli.py` — Added `--compute-accuracy` and `--top-k` flags

**Test Files Added:**
- `tests/test_m05_chosen_move.py`
- `tests/test_m05_accuracy_metrics.py`
- `tests/test_m05_eval_report_v2.py`
- `tests/test_m05_labeled_evaluation.py`
- `tests/test_cli_eval_coverage.py`

### CI Signals Affected

1. **Linting:** No impact (all code follows style guidelines)
2. **Formatting:** Initial run failed due to trailing newlines in test files — fixed in this run
3. **Type Checking:** No impact (all types correct)
4. **Tests:** All new tests pass, no regressions
5. **Coverage:** Improved from 89.18% (initial run) to 92.38% (this run) after adding CLI eval tests

### Unexpected Deltas

**Initial Run (21306671140):**
- ❌ Formatting failure (4 test files needed formatting)
- ❌ Coverage failure (89.18% < 90% threshold)

**This Run (21306722594):**
- ✅ All formatting issues resolved
- ✅ Coverage improved to 92.38% (above threshold)
- ✅ All tests passing

**Signal Drift:** None. All signals are stable and improving.

**Coupling Revealed:** None. Changes are well-isolated.

**Hidden Dependencies:** None identified.

---

## Step 4 — Failure Analysis

**Failures in This Run:** None. All checks passed.

**Previous Run Failures (Resolved):**

1. **Formatting Failure (Initial Run)**
   - **Classification:** CI misconfiguration (test files not formatted)
   - **Resolution:** Applied `ruff format` to test files
   - **Status:** ✅ Resolved

2. **Coverage Failure (Initial Run)**
   - **Classification:** Missing test coverage for CLI eval command
   - **Resolution:** Added `test_cli_eval_coverage.py` with 5 tests
   - **Status:** ✅ Resolved (coverage improved from 89.18% to 92.38%)

---

## Step 5 — Invariants & Guardrails Check

### Required CI Checks

✅ **All checks remain enforced:**
- Lint and Format: ✅ Enforced
- Type Check: ✅ Enforced
- Test + Coverage: ✅ Enforced (90% threshold maintained)

### Semantic Scope

✅ **No scope leakage:**
- Coverage measures code coverage only (not performance)
- Tests measure correctness only (not benchmarks)
- Static analysis measures code quality only

### Release / Consumer Contracts

✅ **Contracts preserved:**
- Context Bridge payload schema v1 remains backward compatible
- Evaluation report schema v1 remains immutable
- New evaluation report schema v2 is additive (does not break v1)

### Determinism and Reproducibility

✅ **Determinism preserved:**
- All tests are deterministic
- Golden file tests verify byte-stable outputs
- No non-deterministic behavior introduced

**Invariant Violations:** None

---

## Step 6 — Verdict

**Verdict:** This run is **safe to merge** and **closes the M05 milestone**. All CI gates passed, coverage exceeds threshold, and all tests are passing. The implementation maintains backward compatibility, preserves determinism, and follows all project governance rules. The initial formatting and coverage issues were resolved, and the codebase is in a clean, audit-defensible state.

**Decision:** ✅ **Merge approved**

---

## Step 7 — Next Actions

### Immediate Actions (M05 Closeout)

1. **Update Governance Documentation**
   - **Owner:** AI Agent (Cursor)
   - **Scope:** Update `renacechess.md` to add M05 to completed milestones table
   - **Milestone:** M05 (current)

2. **Generate Audit Document**
   - **Owner:** AI Agent (Cursor)
   - **Scope:** Generate `M05_audit.md` using `docs/prompts/unifiedmilestoneauditprompt.md`
   - **Milestone:** M05 (current)

3. **Generate Summary Document**
   - **Owner:** AI Agent (Cursor)
   - **Scope:** Generate `M05_summary.md` using `docs/prompts/summaryprompt.md`
   - **Milestone:** M05 (current)

4. **Initialize Next Milestone**
   - **Owner:** AI Agent (Cursor)
   - **Scope:** Create M06 milestone folder and seed with empty plan and toolcalls files
   - **Milestone:** M06 (next)

### Deferred Actions

**None.** All M05 objectives are complete and verified.

---

## Additional Notes

- **Test Count Increase:** Total tests increased from 199 to 204 (+5 tests for CLI eval coverage)
- **Coverage Improvement:** Coverage improved from 89.18% to 92.38% (+3.2 percentage points)
- **No Regressions:** All existing tests continue to pass
- **Backward Compatibility:** Verified through schema validation and integration tests

---

**Analysis Date:** 2026-01-24  
**Analyst:** AI Agent (Cursor)  
**Review Status:** Ready for milestone closeout

