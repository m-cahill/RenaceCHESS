# M19 CI Run Analysis

**Milestone:** M19 — ADVICE-FACTS-CONTRACT-001  
**Phase:** Phase C — Elo-Appropriate Coaching & Explanation

---

## Run Summary

| Run | ID | Status | Duration | Issues |
|-----|-----|--------|----------|--------|
| Run 1 | 21553586177 | ❌ Failed | 5m24s | Ruff format, MyPy ConfigDict |
| Run 2 | 21553672113 | ✅ Success | 4m42s | None |

---

## Run 1 Analysis

### Failures

1. **Ruff format check** — 4 files would be reformatted
   - `src/renacechess/coaching/__init__.py`
   - `src/renacechess/coaching/advice_facts.py`
   - `src/renacechess/contracts/models.py`
   - `tests/test_m19_advice_facts.py`

2. **MyPy type check** — 1 error
   - `src/renacechess/contracts/models.py:958`: Extra keys `validate_by_alias`, `validate_by_name` for TypedDict `ConfigDict`
   - **Root cause:** Pre-existing code in `AccuracyMetrics` class used deprecated/invalid ConfigDict keys

### Fixes Applied

1. **Format fix:** `ruff format .` — reformatted 4 files
2. **MyPy fix:** Changed `AccuracyMetrics.model_config` from:
   ```python
   model_config = ConfigDict(
       validate_by_alias=True,
       validate_by_name=True,
       extra="allow",
   )
   ```
   To:
   ```python
   model_config = ConfigDict(
       populate_by_name=True,
       extra="allow",
   )
   ```

### Commit

```
fix: ruff format + mypy ConfigDict fix for AccuracyMetrics
SHA: 3ba4ea3
```

---

## Run 2 Analysis

### Results

All jobs passed:

| Job | Status | Duration |
|-----|--------|----------|
| Lint and Format | ✅ | ~30s |
| Type Check | ✅ | ~20s |
| Test | ✅ | ~4m |

### Test Summary

- **512 passed**, 1 skipped
- **Coverage:** 91.33% (threshold: 90%)
- **Overlap-set non-regression:** Passed

### Import Linter

All 3 contracts kept:
- `contracts-isolation`
- `personality-isolation`
- `coaching-isolation` (new in M19)

---

## Lessons Learned

1. **Run `ruff format .` before committing** — Local `ruff check` passed but format check failed in CI
2. **Pre-existing tech debt surfaced** — The `AccuracyMetrics` ConfigDict issue existed before M19 but wasn't caught locally until CI ran with stricter checks

---

## Status

✅ **CI GREEN** — Ready for governance updates and merge permission request

---

**Generated:** 2026-02-01T00:51:00Z

