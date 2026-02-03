# M33 CI Run 1 Analysis

**Run ID:** 21620100537  
**PR:** #39  
**Branch:** m33-external-proof-pack  
**Status:** ❌ FAILURE  
**Date:** 2026-02-03T06:45:41Z  
**Duration:** 9m6s

---

## Executive Summary

The first CI run for M33 PR #39 failed with **3 failing jobs** out of 13 total jobs:

1. **Lint and Format** ❌ (3 lint errors)
2. **Type Check** ❌ (4 mypy errors)
3. **M33 Proof Pack Validation** ❌ (1 validation error in CI test)

**10 jobs passed**, including:
- ✅ Security Scan
- ✅ Test (all 12 M33 tests passed)
- ✅ Performance Benchmarks
- ✅ All other milestone validation jobs

The failures are **implementation issues** (lint, type hints, CI test data) rather than architectural problems. All functional tests pass.

---

## Detailed Analysis

### 1. Lint and Format Job (FAILURE)

**Job ID:** 62307119455  
**Status:** ❌ FAILURE  
**Duration:** ~3s

#### Errors Found

1. **F841: Unused variable** (`build_proof_pack.py:114`)
   ```
   post_train_eval_report = _load_json(post_train_eval_report_path)
   ```
   - **Issue:** Variable is loaded but never used
   - **Fix:** Remove the unused variable assignment

2. **E501: Line too long** (`build_proof_pack.py:295`)
   ```
   readme_content = readme_template.replace("{generated_date}", datetime.now().strftime("%Y-%m-%d"))
   ```
   - **Issue:** Line is 101 characters, exceeds 100 character limit
   - **Fix:** Break into multiple lines

3. **F841: Unused variable** (`tests/test_m33_proof_pack.py:56`)
   ```
   manifest = build_proof_pack(...)
   ```
   - **Issue:** Variable is assigned but never used
   - **Fix:** Remove assignment or use the variable

#### Impact
- **Severity:** Low (code quality issues, not functional bugs)
- **Blocking:** Yes (CI gate)
- **Fix Complexity:** Trivial (5 minutes)

---

### 2. Type Check Job (FAILURE)

**Job ID:** 62307119465  
**Status:** ❌ FAILURE  
**Duration:** ~12s

#### Errors Found

1. **no-any-return** (`build_proof_pack.py:78`)
   ```
   def _load_json(path: Path) -> dict[str, object]:
       return json.load(f)  # Returns Any, not dict[str, object]
   ```
   - **Issue:** `json.load()` returns `Any`, but function signature declares `dict[str, object]`
   - **Fix:** Change return type to `dict[str, Any]` or use `cast()`

2. **attr-defined** (`build_proof_pack.py:119`)
   ```
   (c for c in checkpoints_data if c.get("headType") == "policy")
   ```
   - **Issue:** `checkpoints_data` is typed as `object`, which has no `__iter__` attribute
   - **Fix:** Type `checkpoints_data` as `list[dict[str, Any]]` or similar

3. **attr-defined** (`build_proof_pack.py:122`)
   ```
   (c for c in checkpoints_data if c.get("headType") == "outcome")
   ```
   - **Issue:** Same as above - `checkpoints_data` is `object`, not iterable
   - **Fix:** Same as above

4. **attr-defined** (`build_proof_pack.py:197`)
   ```
   move_vocab_size = training_run_report.get("moveVocabSize", 8)
   ```
   - **Issue:** `training_run_report` is typed as `object`, which has no `.get()` method
   - **Fix:** Type as `dict[str, Any]`

#### Root Cause
The `_load_json()` function returns `dict[str, object]`, but `json.load()` returns `Any`. When this is used, mypy infers `object` type, which doesn't support dictionary operations.

#### Impact
- **Severity:** Medium (type safety issues, but code works at runtime)
- **Blocking:** Yes (CI gate)
- **Fix Complexity:** Low (10 minutes)

---

### 3. M33 Proof Pack Validation Job (FAILURE)

**Job ID:** 62307119533  
**Status:** ❌ FAILURE  
**Duration:** ~30s

#### Error Found

**ValidationError** in CI test step "Validate Pydantic model matches schema":
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for EvaluationArtifactsV1
report_hash
  String should match pattern '^sha256:[a-f0-9]{64}$' [type=string_pattern_mismatch, input_value='sha256:ggggggggggggggggg...ggggggggggggggggggggggg', input_type=str]
```

#### Root Cause
The CI test uses invalid hash strings:
```python
report_hash="sha256:" + "g" * 64,  # ❌ 'g' is not a valid hex character
```

The pattern `^sha256:[a-f0-9]{64}$` requires hexadecimal characters (`0-9`, `a-f`), but the test uses `"g" * 64`, which creates a string with the letter `g` repeated 64 times. The letter `g` is not a valid hexadecimal digit.

#### Impact
- **Severity:** Low (test data issue, not production code)
- **Blocking:** Yes (CI gate)
- **Fix Complexity:** Trivial (2 minutes - change test data to use valid hex)

#### Additional Issues in CI Test
The CI test also uses incorrect field names that don't match the actual Pydantic models:
- Uses `manifest_path`, `provenance_path` (correct for Python)
- Uses `checkpoints` as a dict (should check actual model structure)
- Uses `move_count`, `is_synthetic`, `proven`, `not_proven` (need to verify these match actual model fields)

---

## Test Results

### M33 Unit Tests: ✅ ALL PASSING (12/12)

All functional tests pass, confirming the implementation is correct:
```
12 passed in 0.37s
- Build proof pack: 6 tests
- Verify proof pack: 5 tests
- Error handling: 1 test
```

This confirms that:
- ✅ Builder logic is correct
- ✅ Verifier logic is correct
- ✅ Schema validation works
- ✅ Hash computation works
- ✅ Error handling works

---

## Root Cause Analysis

### Primary Issues

1. **Type Hints:** `_load_json()` return type is too restrictive (`dict[str, object]` instead of `dict[str, Any]`)
2. **Lint Violations:** Unused variables and line length
3. **CI Test Data:** Invalid hexadecimal characters in test hash strings

### Why These Weren't Caught Locally

- **Lint:** May not have run `ruff check` before committing
- **Type Check:** May not have run `mypy` before committing
- **CI Test:** The CI test is embedded in the workflow file and wasn't tested locally

---

## Recommended Fixes

### Fix 1: Type Hints (Priority: High)

**File:** `src/renacechess/proof_pack/build_proof_pack.py`

```python
from typing import Any

def _load_json(path: Path) -> dict[str, Any]:  # Change from dict[str, object]
    """Load JSON file."""
    with path.open(encoding="utf-8") as f:
        return json.load(f)
```

This will fix all 4 mypy errors.

### Fix 2: Lint Issues (Priority: Medium)

**File:** `src/renacechess/proof_pack/build_proof_pack.py`

1. Remove unused variable (line 114):
   ```python
   # Remove: post_train_eval_report = _load_json(post_train_eval_report_path)
   ```

2. Fix line length (line 295):
   ```python
   readme_content = readme_template.replace(
       "{generated_date}", datetime.now().strftime("%Y-%m-%d")
   )
   ```

**File:** `tests/test_m33_proof_pack.py`

3. Remove unused variable (line 56):
   ```python
   # Change: manifest = build_proof_pack(...)
   # To: build_proof_pack(...)  # or use the variable
   ```

### Fix 3: CI Test Data (Priority: Medium)

**File:** `.github/workflows/ci.yml` (around line 1200)

Change invalid hash strings to use valid hexadecimal:
```python
# Change from:
report_hash="sha256:" + "g" * 64,  # ❌ Invalid hex

# To:
report_hash="sha256:" + "a" * 64,  # ✅ Valid hex (or use actual test hashes)
```

Also verify all field names match the actual Pydantic models.

---

## Impact Assessment

### Functional Impact
- **None** - All functional tests pass
- Implementation is correct, only code quality issues

### CI Impact
- **Blocking** - PR cannot merge until fixed
- **Estimated Fix Time:** 15-20 minutes

### Risk Assessment
- **Low Risk** - All fixes are straightforward
- No architectural changes needed
- No test logic changes needed (only test data)

---

## Next Steps

1. ✅ **Fix type hints** - Change `_load_json()` return type to `dict[str, Any]`
2. ✅ **Fix lint issues** - Remove unused variables, fix line length
3. ✅ **Fix CI test** - Use valid hexadecimal characters in test hashes
4. ✅ **Verify locally** - Run `ruff check`, `mypy`, and `pytest` before pushing
5. ✅ **Push fix** - Commit and push to trigger new CI run

---

## Conclusion

The M33 implementation is **functionally correct** (all 12 tests pass), but has **code quality issues** that prevent CI from passing:

- **3 lint violations** (unused variables, line length)
- **4 type hint issues** (incorrect return type causing cascading errors)
- **1 CI test data issue** (invalid hex characters)

All issues are **trivial to fix** (estimated 15-20 minutes) and do not require architectural changes. Once fixed, the PR should pass CI and be ready for merge.

**Status:** ⏸️ **BLOCKED** - Awaiting fixes before merge

