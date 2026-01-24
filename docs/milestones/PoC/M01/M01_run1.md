# M01 CI Run 1 Analysis

**Workflow:** CI  
**Run ID:** 21279550886  
**Trigger:** PR #3 (m01-dataset-shards)  
**Branch:** m01-dataset-shards  
**Commit:** 27dce3d  
**Status:** ❌ **FAILURE**

---

## Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
| ----------- | --------- | ------- | --------- | ----- |
| Lint and Format | ✅ Yes | Ruff lint + format check | ❌ FAIL | Format check failed |
| Type Check | ✅ Yes | MyPy type checking | ✅ PASS | All type checks passed |
| Test | ✅ Yes | Pytest with coverage gate | ❌ FAIL | Coverage 89.02% < 90% threshold |

**Merge-blocking checks:** All three jobs are required.

---

## Signal Integrity Analysis

### A) Tests

**Test tiers:** Unit tests only (40 tests total)

**Failures:** No test failures — all 40 tests passed.

**Missing tests:** Coverage analysis shows:
- `cli.py`: 68.42% coverage (missing lines 97-118 — dataset command error handling)
- `dataset/builder.py`: 86.44% coverage (missing edge cases: empty PGN lists, directory handling, limit boundaries)
- `demo/pgn_overlay.py`: 88.89% coverage (minor gaps in error paths)

**Test stability:** All tests are deterministic and stable.

### B) Coverage

**Type:** Line coverage (90% threshold) + branch coverage (85% threshold implied)

**Overall:** 89.02% line coverage (below 90% threshold)

**Scoped correctly:** Yes — coverage measures all source files in `src/renacechess/`

**Exclusions:** Standard exclusions (tests, `__init__.py`, pragma comments) — documented and justified.

**Coverage breakdown:**
- `cli.py`: 68.42% (13 lines missed)
- `dataset/builder.py`: 86.44% (6 lines missed, 8 branch misses)
- `demo/pgn_overlay.py`: 88.89% (3 lines missed, 7 branch misses)
- All other modules: 100% coverage

### C) Static / Policy Gates

**Linting:** Ruff format check failed — 11 files need reformatting:
- `src/renacechess/cli.py`
- `src/renacechess/dataset/__init__.py`
- `src/renacechess/dataset/builder.py`
- `src/renacechess/dataset/config.py`
- `src/renacechess/dataset/manifest.py`
- `src/renacechess/dataset/split.py`
- `tests/test_cli_dataset_build.py`
- `tests/test_dataset_build_golden.py`
- `tests/test_dataset_schema_validation.py`
- `tests/test_dataset_split.py`
- `tests/test_pydantic_alias_validation.py`

**Type checking:** MyPy passed — no type errors.

**Gates enforce current reality:** Yes — format check correctly identified files that don't match Ruff's formatting rules.

### D) Performance / Benchmarks

Not applicable for this milestone.

---

## Delta Analysis (Change Impact)

### Files Modified

**New modules:**
- `src/renacechess/dataset/` (5 new files)
- `tests/test_dataset_*.py` (5 new test files)

**Modified files:**
- `src/renacechess/cli.py` (added dataset command)
- `src/renacechess/contracts/models.py` (Pydantic config updates)
- `src/renacechess/demo/pgn_overlay.py` (extracted reusable function)
- `src/renacechess/contracts/schemas/v1/context_bridge.schema.json` (null support)

### CI Signals Affected

1. **Format check:** New files not formatted with `ruff format`
2. **Coverage:** New code paths not fully covered (89.02% < 90%)

### Unexpected Deltas

None — all failures are expected for new code that hasn't been formatted or fully tested.

---

## Failure Analysis

### Failure 1: Ruff Format Check

**Classification:** CI misconfiguration / developer workflow gap

**Root cause:** Files were created/edited but not formatted with `ruff format` before commit.

**Is this in scope?** ✅ Yes — formatting is a required gate.

**Blocking / Deferrable / Informational:** ⛔ **Blocking** — required check.

**Resolution:**
1. Run `ruff format .` locally
2. Commit formatted files
3. Re-run CI

**Guardrail:** Add pre-commit hook or document requirement to run `ruff format` before commit.

### Failure 2: Coverage Below Threshold

**Classification:** Test coverage gap

**Root cause:** New code paths not fully covered:
- CLI error handling paths (dataset command)
- Builder edge cases (empty inputs, directory handling)
- Minor demo overlay error paths

**Is this in scope?** ✅ Yes — coverage threshold is a required gate.

**Blocking / Deferrable / Informational:** ⛔ **Blocking** — coverage gate is 90%, achieved 89.02%.

**Resolution:**
1. Add tests for CLI error handling (dataset command)
2. Add tests for builder edge cases (empty PGN lists, directory globbing)
3. Add tests for demo overlay error paths (if not already covered)
4. Target: Achieve ≥90% line coverage

**Guardrail:** Coverage gate already enforced — CI will fail until threshold met.

---

## Invariants & Guardrails Check

✅ **Required CI checks remain enforced** — All three jobs are still required.

✅ **No semantic scope leakage** — Coverage measures code coverage, not performance or other concerns.

✅ **Release / consumer contracts not weakened** — Schema changes (null support) are backward-compatible additions.

✅ **Determinism preserved** — All tests remain deterministic; no randomness introduced.

---

## Verdict

**Verdict:**  
This run surfaces **two real, fixable issues**:
1. **Formatting:** 11 files need `ruff format` applied
2. **Coverage:** 0.98% coverage gap (89.02% vs 90% threshold)

Both issues are **in-scope for M01** and should be fixed before merge.

**Merge status:** ⛔ **Merge blocked** — formatting and coverage gates must pass.

---

## Next Actions

### Immediate (Before Merge)

1. **Format files** (Owner: Developer / Cursor)
   - Run `ruff format .`
   - Commit formatted files
   - Scope: 11 files identified by CI
   - Risk: Low — formatting only, no logic changes
   - Est: 5 minutes

2. **Increase coverage** (Owner: Developer / Cursor)
   - Add tests for CLI dataset command error handling
   - Add tests for builder edge cases (empty PGN lists, directory handling)
   - Target: ≥90% line coverage
   - Scope: ~10-15 lines of test code
   - Risk: Low — adding tests, not changing logic
   - Est: 30-45 minutes

### After Fixes

3. **Re-run CI** (Owner: CI system)
   - Verify formatting passes
   - Verify coverage ≥90%
   - Verify all tests still pass

4. **Create M01_run2.md** (Owner: Developer / Cursor)
   - If CI still fails, analyze run 2
   - If CI passes, proceed to Phase 5 (Governance Updates)

---

## Evidence Summary

- **Run URL:** https://github.com/m-cahill/RenaceCHESS/actions/runs/21279550886
- **PR:** https://github.com/m-cahill/RenaceCHESS/pull/3
- **Format failures:** 11 files need reformatting
- **Coverage:** 89.02% (target: 90%)
- **Tests:** 40/40 passing
- **Type check:** ✅ Pass

---

**Analysis Date:** 2026-01-23  
**Analyst:** Cursor AI (workflow prompt)


