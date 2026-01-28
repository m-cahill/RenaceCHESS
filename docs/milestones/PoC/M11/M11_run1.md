# M11 CI Workflow Analysis — Run 1 (FINAL)

**Status:** ✅ GREEN  
**Analysis Date:** 2026-01-28

---

## Inputs

### 1. Workflow Identity

| Field | Value |
|-------|-------|
| Workflow Name | CI |
| Run ID | 21421642384 |
| Trigger | PR push |
| Branch | `m11-structural-interpretability` |
| Commit SHA | `effe8ad` |

### 2. Change Context

| Field | Value |
|-------|-------|
| Milestone | M11 — Structural Interpretability Expansion |
| Objective | Introduce per-piece and square-level structural cognition without altering core policy or evaluation |
| Run Type | Corrective (final successful run after 3 attempts) |

### 3. Baseline Reference

| Field | Value |
|-------|-------|
| Last Trusted Green | `main` branch @ M10 closure |
| Invariants | No coverage regression on existing files; 90% overall coverage threshold |

---

## Step 1 — Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
|-------------|-----------|---------|-----------|-------|
| Lint and Format | Yes | Ruff lint + format enforcement | ✅ PASS | All checks passed |
| Type Check | Yes | MyPy static type checking | ✅ PASS | All checks passed |
| Test | Yes | pytest + coverage with non-regression | ✅ PASS | 90% threshold met, no regressions |

**Merge-blocking:** All three jobs are merge-blocking.  
**Bypasses:** None.

---

## Step 2 — Signal Integrity Analysis

### A) Tests

- **Tier:** Unit tests (384 collected, 383 passed, 1 skipped)
- **Failures:** None
- **Coverage:** Line + branch coverage enforced
- **New test files:** `test_m11_per_piece_features.py`, `test_m11_square_map_features.py`, `test_m11_context_bridge_v2.py`

### B) Coverage

- **Type:** Line and branch coverage via pytest-cov
- **Mode:** Overlap-set comparison (PR mode) + absolute threshold (90%)
- **Non-regression:** No existing file lost coverage
- **New files:** 3 new feature modules + 3 new test files added

### C) Static / Policy Gates

| Gate | Status |
|------|--------|
| Ruff lint | ✅ All checks passed |
| Ruff format | ✅ All files formatted |
| MyPy | ✅ No type errors |

### D) Performance / Benchmarks

Not applicable for this milestone.

---

## Step 3 — Delta Analysis (Change Impact)

### Files Modified (M11 scope only)

| Category | Files |
|----------|-------|
| Contracts | `src/renacechess/contracts/models.py` (added Pydantic models for PerPieceFeaturesV1, SquareMapFeaturesV1, ContextBridgePayloadV2) |
| Schemas | `PerPieceFeaturesV1.schema.json`, `SquareMapFeaturesV1.schema.json`, `context_bridge.v2.schema.json` |
| Feature Extractors | `src/renacechess/features/per_piece.py`, `square_map.py`, `context_bridge_v2.py`, `__init__.py` |
| Documentation | `docs/contracts/StructuralCognitionContract_v1.md` |
| Tests | `tests/test_m11_*.py` (3 files), `tests/fixtures/fens_m11.json` |
| Toolcalls | `docs/milestones/PoC/M11/M11_toolcalls.md` |

### Signal Impact

- **Direct:** All 47 new M11 tests passed
- **Indirect:** No regressions in existing 336 tests
- **Unexpected:** Initial runs failed due to ruff auto-fixing non-M11 files (resolved by reverting)

---

## Step 4 — Failure Analysis

### Previous Runs (Resolved)

| Run | Failure | Root Cause | Resolution |
|-----|---------|------------|------------|
| Run 21421262018 | Lint (E501, E741) | Line too long, ambiguous variable `l` | Fixed lint errors |
| Run 21421396840 | Lint (format) + Coverage regression | `ruff check .` auto-fixed non-M11 files | Applied format, but still had coverage regression |
| Run 21421520149 | Coverage regression | Non-M11 files had import removals causing coverage delta | Reverted non-M11 files to main |

### Final Run

No failures. All checks passed.

---

## Step 5 — Invariants & Guardrails Check

| Invariant | Status | Notes |
|-----------|--------|-------|
| Required CI checks enforced | ✅ | All 3 jobs required and passed |
| No semantic scope leakage | ✅ | Coverage measures code, not tests; no cross-contamination |
| Consumer contracts not weakened | ✅ | ContextBridgePayloadV2 supersets V1 |
| Determinism preserved | ✅ | Feature extraction is pure function of FEN |
| Non-M11 files unchanged | ✅ | Reverted all non-M11 modifications |

**Violations:** None.

---

## Step 6 — Verdict

> **Verdict:** This run is GREEN and safe to merge. The M11 implementation introduces structural cognition features (PerPieceFeaturesV1, SquareMapFeaturesV1) with comprehensive tests, frozen contracts, and JSON schemas. Coverage remains at 90%+ with no regressions on existing files. The implementation adheres to all governance rules and milestone scope.

**Decision:** ✅ **Merge approved**

---

## Step 7 — Next Actions

| Action | Owner | Scope | Milestone |
|--------|-------|-------|-----------|
| Await merge approval | User | PR #13 | M11 |
| Update `renacechess.md` milestone table | Cursor | Governance | M11 |
| Generate M11_audit.md | Cursor | Documentation | M11 |
| Generate M11_summary.md | Cursor | Documentation | M11 |
| Closeout M11 (upon approval) | Cursor | Governance | M11 |

---

## Appendix: CI Run Summary

```
Run ID: 21421642384
Status: completed
Conclusion: success

Jobs:
- Lint and Format: success (2m 37s)
- Test: success (3m 18s)
- Type Check: success (3m 13s)

Tests: 383 passed, 1 skipped
Coverage: 90%+ (non-regression satisfied)
```

