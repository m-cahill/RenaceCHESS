# M22 CI Run Analysis — Run 1

**Milestone:** M22 (COACHING-SURFACE-CLI-001)  
**Run:** 1  
**Date:** 2026-02-01  
**Workflow:** https://github.com/m-cahill/RenaceCHESS/actions/runs/21555595839  
**PR:** [#28](https://github.com/m-cahill/RenaceCHESS/pull/28)

---

## 1. Inventory

| Job | Status | Duration | Notes |
|-----|--------|----------|-------|
| Lint and Format | ✅ pass | 3m34s | Fixed after 2 attempts |
| Type Check | ✅ pass | 3m41s | First-run pass |
| Test | ✅ pass | 5m19s | 613 tests, 90%+ coverage |

---

## 2. Signal Integrity

### Lint and Format
- **Initial failures:** N806 (variable naming), E501 (line length), F841 (unused variable)
- **Resolution:** Renamed threshold constants to lowercase, split long lines, removed unused variable
- **Format check:** Required reformatting test file with `ruff format`

### Type Check
- First-run pass — no type errors

### Test
- **Tests passed:** 613 (including 26 new M22 tests)
- **Skipped:** 1
- **Coverage:** 90%+ (threshold met)

---

## 3. Delta Analysis

| Metric | Before M22 | After M22 | Delta |
|--------|------------|-----------|-------|
| Total tests | 587 | 613 | +26 |
| Coverage | 90.0%+ | 90.99% | +0.99% |
| CLI commands | 6 | 7 | +1 |

### New Files
1. `src/renacechess/contracts/schemas/v1/coaching_surface.v1.schema.json`
2. `tests/test_m22_coaching_cli.py`

### Modified Files
1. `src/renacechess/cli.py` — Added `coach` command (~140 lines)
2. `src/renacechess/contracts/models.py` — Added 2 Pydantic models

---

## 4. Failure Analysis

### Initial Failures (2 CI runs)

| Run | Job | Error | Root Cause | Fix |
|-----|-----|-------|------------|-----|
| 1 | Lint | N806 | UPPERCASE constants inside function | Renamed to lowercase |
| 1 | Lint | E501 | Lines >100 chars | Split into multiple statements |
| 1 | Lint | F841 | Unused `result` variable | Removed |
| 2 | Format | Formatting | Test file not formatted | Ran `ruff format` |

All issues were minor style/formatting issues, not semantic errors.

---

## 5. Invariants Check

| Invariant | Status | Evidence |
|-----------|--------|----------|
| Coverage ≥ 90% | ✅ | 90.99% |
| No type errors | ✅ | Type Check pass |
| No lint errors | ✅ | Lint and Format pass |
| All tests pass | ✅ | 613 passed |
| M21 thresholds unchanged | ✅ | Reuses same values |
| Stub LLM only | ✅ | No provider flag exists |
| Both inputs required | ✅ | Tests verify hard fail |
| Evaluation always printed | ✅ | Tests verify stderr output |

---

## 6. Verdict

**✅ CI GREEN** — All checks pass after 3 runs.

Initial failures were minor lint/format issues, quickly resolved. No semantic or architectural issues detected.

---

## 7. Next Actions

- [ ] Wait for user permission to merge PR
- [ ] After merge, update `renacechess.md` with M22 entry
- [ ] Generate M22_audit.md and M22_summary.md
- [ ] Proceed to Phase C closeout or Phase D planning






