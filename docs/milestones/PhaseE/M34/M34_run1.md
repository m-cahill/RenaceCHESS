# M34 CI Run 1 Analysis

**Run ID:** 21623903944  
**PR:** #40  
**Branch:** m34-release-lock  
**Status:** ❌ FAILURE  
**Date:** 2026-02-03T09:00:00Z (approximate)  
**Duration:** ~9 minutes

---

## Executive Summary

The first CI run for M34 PR #40 failed with **2 failing jobs** out of 15 total jobs:

1. **Lint and Format** ❌ (12 lint errors: line length, whitespace)
2. **Release Contract Freeze** ❌ (Hash mismatch: `eval_set_provenance.v1.schema.json`)

**13 jobs passed**, including:
- ✅ Type Check
- ✅ Security Scan
- ✅ Test (all tests passed)
- ✅ Release Dependency Freeze
- ✅ Release Proof Pack Verification
- ✅ All milestone validation jobs (M26, M27, M30, M31, M32, M33)

The failures are **implementation issues** (code formatting and line ending normalization) rather than architectural problems. All functional tests pass.

---

## Detailed Analysis

### 1. Lint and Format Job (FAILURE)

**Job ID:** 62319151507  
**Status:** ❌ FAILURE  
**Duration:** ~3m7s

#### Errors Found

1. **E501: Line too long** (multiple files)
   - `src/renacechess/contracts/models.py:5988` (107 > 100 chars)
   - `src/renacechess/contracts/models.py:6014` (113 > 100 chars)
   - `src/renacechess/contracts/registry.py:149` (107 > 100 chars)
   - `src/renacechess/contracts/registry.py:276` (119 > 100 chars)
   - `tests/test_m34_contract_registry.py:118` (168 > 100 chars)
   - `tests/test_m34_contract_registry.py:124` (141 > 100 chars)

2. **W293: Blank line contains whitespace** (multiple locations)
   - `src/renacechess/contracts/registry.py:21, 59, 64, 238, 242`

3. **W291: Trailing whitespace**
   - `src/renacechess/contracts/registry.py:22`

#### Impact
- **Severity:** Low (code quality issues, not functional bugs)
- **Blocking:** Yes (CI gate)
- **Fix Complexity:** Trivial (formatting fixes)

---

### 2. Release Contract Freeze Job (FAILURE)

**Job ID:** 62319151599  
**Status:** ❌ FAILURE  
**Duration:** ~3m50s

#### Error Found

**Hash mismatch for `eval_set_provenance.v1.schema.json`:**
- **Expected:** `dd1ac75422290d5e447ccdc66ad179a1289a9a229c67d1c63108a763b307b7e7`
- **Got:** `f175ba805746c7cd3d670a9bcdeb2ed00681f0975a879157424d2e222692cac2`

#### Root Cause

The `.gitattributes` file enforces LF line endings for JSON files (`*.json text eol=lf`), but the local file had CRLF line endings. When CI checks out the file, Git normalizes it to LF, causing a hash mismatch.

#### Impact
- **Severity:** Medium (contract immutability enforcement)
- **Blocking:** Yes (release gate)
- **Fix Complexity:** Trivial (normalize all JSON schema files to LF)

---

## Step 2 — Signal Integrity Analysis

### A) Tests

- **Test tiers:** Unit tests (M34 contract registry tests)
- **Failures:** None — all tests passed
- **Missing tests:** None identified

### B) Coverage

- **Coverage type:** Line coverage (PR mode)
- **Status:** ✅ Passed
- **Exclusions:** Not applicable

### C) Static / Policy Gates

- **Linting:** ❌ Failed (formatting issues)
- **Type checking:** ✅ Passed (MyPy)
- **Security:** ✅ Passed (pip-audit, bandit)
- **Formatting:** ❌ Failed (ruff format check)

### D) Performance / Benchmarks

- **Status:** ✅ Passed
- **Isolation:** Correctly isolated from correctness signals

---

## Step 3 — Delta Analysis (Change Impact)

### Files Modified

1. **New files:**
   - `src/renacechess/contracts/registry.py` (contract registry generator)
   - `src/renacechess/contracts/models.py` (ContractEntryV1, ContractRegistryV1 models)
   - `contracts/CONTRACT_REGISTRY_v1.json` (generated registry)
   - `tests/test_m34_contract_registry.py` (test suite)
   - `.github/workflows/ci.yml` (added 3 release gates)

2. **Modified files:**
   - `README.md` (added "What this is/is not" section)
   - `renacechess.md` (added M34 entry)
   - `RELEASE_NOTES_v1.md` (new)
   - `docs/phases/PhaseE_closeout.md` (new)

### CI Signals Affected

- **Lint and Format:** New code introduced formatting violations
- **Release Contract Freeze:** New gate, failing due to line ending issue
- **Release Dependency Freeze:** New gate, ✅ passed
- **Release Proof Pack Verification:** New gate, ✅ passed

### Unexpected Deltas

- **Line ending normalization:** All JSON schema files need LF line endings, but some had CRLF locally

---

## Step 4 — Failure Analysis

### Failure 1: Lint and Format

**Classification:** CI misconfiguration / Code quality

**In scope:** Yes (M34 implementation)

**Blocking:** Yes (CI gate)

**Fix:** Format code to comply with Ruff rules

### Failure 2: Release Contract Freeze

**Classification:** Environmental / Line ending normalization

**In scope:** Yes (M34 contract freeze requirement)

**Blocking:** Yes (release gate)

**Fix:** Normalize all JSON schema files to LF line endings and regenerate registry

---

## Step 5 — Invariants & Guardrails Check

✅ **Required CI checks remain enforced**  
✅ **No semantic scope leakage**  
✅ **Release / consumer contracts were not weakened**  
✅ **Determinism and reproducibility preserved** (after line ending fix)

**Note:** Line ending normalization is required for contract hash stability across platforms.

---

## Step 6 — Verdict

> **Verdict:**  
> This run surfaces **implementation issues** (formatting and line ending normalization) that are **blocking but easily fixable**. All functional tests pass, and the architectural changes (contract registry, release gates) are sound. The failures are **in scope** for M34 and must be fixed before merge.

**⛔ Merge blocked** — Fix formatting and normalize line endings, then re-run CI.

---

## Step 7 — Next Actions

1. **Fix lint errors** (Owner: AI/Cursor)
   - Format `src/renacechess/contracts/registry.py`
   - Format `tests/test_m34_contract_registry.py`
   - Fix line length violations in `src/renacechess/contracts/models.py`

2. **Normalize JSON schema line endings** (Owner: AI/Cursor)
   - Convert all JSON schema files in `src/renacechess/contracts/schemas/v1/` to LF
   - Regenerate `contracts/CONTRACT_REGISTRY_v1.json` with correct hashes

3. **Re-run CI** (Owner: GitHub Actions)
   - Verify all gates pass after fixes

**Scope:** M34 (current milestone)  
**Estimated time:** 10-15 minutes

---

## Run 2 Summary

**Run ID:** 21624264925  
**Status:** ❌ FAILURE (partial progress)

After fixes from Run 1:
- ✅ **Lint errors fixed** (Ruff lint passed)
- ❌ **Format check still failing** (2 files need reformatting)
- ❌ **Contract registry hash mismatch** (now `advice_facts.v1.schema.json`)

**Remaining issues:**
1. Run `ruff format` on `src/renacechess/contracts/registry.py` and `tests/test_m34_contract_registry.py`
2. Normalize **all** JSON schema files to LF (not just one)

**Progress:** 50% — Lint errors resolved, formatting and line ending normalization still needed.

