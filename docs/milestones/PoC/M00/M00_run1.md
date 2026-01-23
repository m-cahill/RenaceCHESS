# M00 Run 1 — CI Workflow Analysis

**Workflow:** CI  
**Run ID:** 21271461853  
**Trigger:** Push to `main`  
**Branch:** `main`  
**Commit:** `26a6d223199e44c63f125f00c5afa4d774025ddc`  
**Status:** ❌ **FAILURE**  
**Date:** 2026-01-23T01:40:06Z

---

## 1. Workflow Identity

- **Workflow Name:** CI
- **Run ID:** 21271461853
- **Trigger:** Push to `main` branch
- **Branch:** `main`
- **Commit SHA:** `26a6d223199e44c63f125f00c5afa4d774025ddc`
- **Milestone:** M00 (Repository Bootstrap + Contract Skeleton + Deterministic Demo)

---

## 2. Change Context

**Milestone:** M00 — Repository Bootstrap + Contract Skeleton + Deterministic Demo

**Declared Intent:** Create minimal, auditable, enterprise-grade repository scaffold with versioned contracts, deterministic demo generator, and CI truthfulness.

**Run Type:** Initial bootstrap (first CI run on new repository)

**Baseline Reference:** None (this is the first commit)

---

## 3. Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
|------------|-----------|---------|-----------|-------|
| **Lint and Format** | ✅ Yes | Ruff lint + format check | ❌ **FAIL** | 28 linting errors (N815 mixedCase, E501 line length, E741 ambiguous variable) |
| **Type Check** | ✅ Yes | MyPy type checking | ❌ **FAIL** | 7 type errors in `pgn_overlay.py` |
| **Test** | ✅ Yes | Pytest with coverage gate | ✅ **PASS** | 27/27 tests passing, 93.02% coverage |

**Merge-Blocking Checks:** All 3 jobs are required (merge-blocking)

**Informational Checks:** None

**Continue-on-Error:** None used

---

## 4. Signal Integrity Analysis

### A) Tests

**Test Tiers:** Unit tests only (no integration, contract, e2e, or smoke tiers yet)

**Failures:** None — all 27 tests passing

**Missing Tests:** None identified for changed surface

**Verdict:** ✅ Test signal is truthful — all tests pass, no test instability

### B) Coverage

**Coverage Type:** Line + branch coverage enforced

**Coverage Scoped:** Correctly scoped to `src/renacechess/` (excludes tests)

**Coverage Results:**
- **Lines:** 93.02% (exceeds 90% requirement)
- **Branches:** Not explicitly reported, but coverage tool tracks branches

**Exclusions:** Documented in `pyproject.toml` (tests, `__init__.py`)

**Verdict:** ✅ Coverage signal is truthful — exceeds threshold, correctly scoped

### C) Static / Policy Gates

**Linting (Ruff):**
- **Status:** ❌ **FAIL**
- **Errors:** 28 total
  - 23 N815 violations (mixedCase variable names in class scope)
  - 4 E501 violations (line too long > 100 chars)
  - 1 E741 violation (ambiguous variable name `l`)

**Type Checking (MyPy):**
- **Status:** ❌ **FAIL**
- **Errors:** 7 type errors in `src/renacechess/demo/pgn_overlay.py`
  - Missing `san` argument for `PolicyMove`
  - Type confusion between `PolicyMove` and chess library `Move`
  - Dict get type issues

**Verdict:** ⚠️ Static gates are enforcing current reality, but failures are **fixable code quality issues**, not correctness bugs

### D) Performance / Benchmarks

**Status:** Not present (out of scope for M00)

---

## 5. Delta Analysis (Change Impact)

**Files Modified:** All files are new (first commit)

**CI Signals Affected:**
- Lint: New codebase with intentional camelCase field names (matches JSON schema)
- Type: New code with type errors
- Test: New test suite (all passing)

**Unexpected Deltas:**
- None (this is the baseline)

**Signal Drift:** None (no baseline to compare against)

**Coupling Revealed:**
- Pydantic models use camelCase to match JSON schema field names, which conflicts with Python naming conventions (N815)
- Type system needs alignment between chess library types and our `PolicyMove` type

---

## 6. Failure Analysis

### Failure 1: Ruff Linting (N815 — MixedCase Variables)

**Classification:** Intentional policy violation (camelCase matches JSON schema)

**Root Cause:** Pydantic models use camelCase field names to match JSON Schema exactly (e.g., `sideToMove`, `legalMoves`, `skillBucket`). Ruff's N815 rule flags these as violations of Python naming conventions.

**In Scope:** ✅ Yes — M00 scope includes schema-aligned models

**Blocking:** ⚠️ **Yes, but fixable** — Need to configure Ruff to ignore N815 for Pydantic model fields, or use `Field(alias=...)` to map between Python snake_case and JSON camelCase

**Deferrable:** ❌ No — Should be fixed in M00 to maintain CI truthfulness

**Fix Strategy:** Add Ruff ignore for N815 on Pydantic model classes, or refactor to use `Field(alias=...)` pattern

### Failure 2: Ruff Linting (E501 — Line Too Long)

**Classification:** Code quality issue

**Root Cause:** 4 lines exceed 100 character limit

**In Scope:** ✅ Yes — M00 scope includes code quality

**Blocking:** ⚠️ **Yes, but fixable** — Simple line breaks needed

**Deferrable:** ❌ No — Should be fixed in M00

**Fix Strategy:** Break long lines (117, 101, 113, 128, 134 characters)

### Failure 3: Ruff Linting (E741 — Ambiguous Variable Name)

**Classification:** Code quality issue

**Root Cause:** Variable name `l` (for "loss") is too short and ambiguous

**In Scope:** ✅ Yes — M00 scope includes code quality

**Blocking:** ⚠️ **Yes, but fixable** — Rename to `loss` or `loss_prob`

**Deferrable:** ❌ No — Should be fixed in M00

**Fix Strategy:** Rename `l` to `loss` in `HumanWDL` model (requires schema update or alias)

### Failure 4: MyPy Type Errors (7 errors in `pgn_overlay.py`)

**Classification:** Type correctness bug

**Root Cause:** 
1. `PolicyMove` constructor missing optional `san` argument
2. Variable name collision: `move` used for both chess library `Move` and our `PolicyMove`
3. Dict get type mismatch

**In Scope:** ✅ Yes — M00 scope includes type safety

**Blocking:** ✅ **Yes** — Type errors must be fixed

**Deferrable:** ❌ No — Should be fixed in M00

**Fix Strategy:**
1. Pass `san=None` explicitly or make it truly optional
2. Rename variables to avoid collision (e.g., `chess_move` vs `policy_move`)
3. Fix dict get type annotations

---

## 7. Invariants & Guardrails Check

### Required CI Checks Remain Enforced
✅ **PASS** — All 3 jobs are required and enforced (no weakening)

### No Semantic Scope Leakage
✅ **PASS** — Coverage measures coverage, tests measure correctness, lint measures style (no cross-contamination)

### Release / Consumer Contracts Not Weakened
✅ **PASS** — No release contracts exist yet (M00 is bootstrap)

### Determinism and Reproducibility Preserved
✅ **PASS** — Determinism helpers are tested and passing

**Invariant Violations:** None

---

## 8. Verdict

**Verdict:**  
This run surfaces **real code quality and type safety issues** that must be fixed before merge. The failures are **fixable and in-scope for M00**. All failures are in the static analysis gates (linting and type checking), not in correctness (tests pass, coverage exceeds threshold).

**Merge Status:** ⛔ **MERGE BLOCKED**

**Rationale:**
- Tests pass (27/27) ✅
- Coverage exceeds threshold (93.02% > 90%) ✅
- Linting fails (28 errors) ❌
- Type checking fails (7 errors) ❌

**Required Actions:**
1. Fix Ruff linting errors (N815, E501, E741)
2. Fix MyPy type errors (7 errors in `pgn_overlay.py`)
3. Re-run CI to verify all checks pass

---

## 9. Next Actions

### Action 1: Fix Ruff Linting Errors
- **Owner:** AI Agent (Cursor)
- **Scope:** 
  - Configure Ruff to ignore N815 for Pydantic model fields (or use Field aliases)
  - Fix 4 E501 line length violations
  - Fix 1 E741 ambiguous variable name (`l` → `loss` with alias)
- **Milestone:** M00 (fits current milestone)

### Action 2: Fix MyPy Type Errors
- **Owner:** AI Agent (Cursor)
- **Scope:**
  - Fix `PolicyMove` constructor calls (add `san=None`)
  - Rename variables to avoid `Move` vs `PolicyMove` collision
  - Fix dict get type annotations
- **Milestone:** M00 (fits current milestone)

### Action 3: Re-run CI
- **Owner:** GitHub Actions (automatic on push)
- **Scope:** Verify all checks pass after fixes
- **Milestone:** M00 (verification step)

---

## 10. Evidence

**Workflow Run URL:** https://github.com/m-cahill/RenaceCHESS/actions/runs/21271461853

**Job URLs:**
- Lint and Format: https://github.com/m-cahill/RenaceCHESS/actions/runs/21271461853/job/61222329405
- Type Check: https://github.com/m-cahill/RenaceCHESS/actions/runs/21271461853/job/61222329403
- Test: https://github.com/m-cahill/RenaceCHESS/actions/runs/21271461853/job/61222329396

**Test Results:** 27/27 passing, 93.02% coverage

**Lint Errors:** 28 total (23 N815, 4 E501, 1 E741)

**Type Errors:** 7 total (all in `pgn_overlay.py`)

---

**Analysis Complete:** 2026-01-23  
**Analyst:** AI Agent (Cursor)  
**Status:** ⛔ **MERGE BLOCKED** — Fixes required before merge

