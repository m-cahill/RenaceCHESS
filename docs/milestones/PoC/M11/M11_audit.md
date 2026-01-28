# M11 Milestone Audit

**Milestone:** M11 — Structural Interpretability Expansion  
**Mode:** DELTA AUDIT  
**Range:** `67fba02...b8860ee`  
**CI Status:** Green  
**Audit Verdict:** 🟢 PASS — Clean architectural expansion with no regressions; CI correctly detected and blocked out-of-scope changes

---

## 1. Executive Summary (Delta-First)

### Wins

1. **Per-piece structural cognition** — 32-slot tensor with mobility, tension, and flags now extractable from any FEN
2. **Square-level semantic maps** — Weak/strong/hole analysis for both sides, deterministic and engine-free
3. **Context Bridge v2** — Versioned superset of v1 with structural cognition integration
4. **Frozen Structural Cognition Contract** — `StructuralCognitionContract_v1.md` establishes immutable v1 semantics

### Risks

1. **Initial CI failures** — Ruff auto-fixed non-M11 files, causing coverage drift (correctly caught, resolved)
2. **Feature module isolation** — New `features/` package is clean but will need boundary enforcement as it grows

### Most Important Next Action

**Lock PoC (`poc-v1.0`)** — The cognitive substrate is now complete; freeze before behavioral consumers (M12+)

---

## 2. Delta Map & Blast Radius

### What Changed

| Category | Files Added/Modified |
|----------|---------------------|
| Contracts | `models.py` (+4 Pydantic models), 3 JSON schemas |
| Features | `features/__init__.py`, `per_piece.py`, `square_map.py`, `context_bridge_v2.py` |
| Documentation | `StructuralCognitionContract_v1.md` |
| Tests | 3 test files (47 tests), `fens_m11.json` |
| Governance | `M11_toolcalls.md`, `M11_run1.md` |

### Risky Zones

| Zone | Status | Notes |
|------|--------|-------|
| Auth | N/A | No auth changes |
| Tenancy | N/A | No tenancy changes |
| Persistence | N/A | No persistence changes |
| Workflow glue | ✅ Safe | No CI workflow changes in M11 |
| Migrations | N/A | No migrations |
| Concurrency | N/A | Extractors are pure functions |

---

## 3. Architecture & Modularity Review

### Boundary Violations

None. The new `features/` package is cleanly isolated:
- Imports only from `contracts.models` and `chess`
- No coupling to eval, models, or CLI
- Pure functions only

### Coupling Analysis

| Dependency | Direction | Status |
|------------|-----------|--------|
| `features/` → `contracts.models` | Allowed | Uses Pydantic models for output |
| `features/` → `chess` | Allowed | External chess library |
| `contracts.models` → `features/` | None | No reverse dependency |

### ADR/Doc Updates

- ✅ `StructuralCognitionContract_v1.md` created and frozen
- ✅ Schema documentation in JSON schema files
- No ADR updates required

### Summary

| Action | Items |
|--------|-------|
| **Keep** | Clean feature module isolation, versioned contracts, frozen semantics |
| **Fix now** | None |
| **Defer** | None |

---

## 4. CI/CD & Workflow Audit

### Required Checks Alignment

| Check | Status | Notes |
|-------|--------|-------|
| Lint and Format | ✅ PASS | Ruff lint + format enforced |
| Type Check | ✅ PASS | MyPy strict mode |
| Test | ✅ PASS | Coverage non-regression + 90% threshold |

### CI Recovery Analysis

M11 required 4 CI runs to reach green:

| Run | Result | Root Cause | Resolution |
|-----|--------|------------|------------|
| #1 | ❌ | E501 (line too long), E741 (ambiguous `l`) | Fixed lint errors |
| #2 | ❌ | Format check + coverage regression | Applied format |
| #3 | ❌ | Coverage regression (non-M11 files modified) | Reverted non-M11 files |
| #4 | ✅ | All checks passed | — |

**Root Cause Summary:** Running `ruff check .` auto-fixed unused imports across the entire codebase, not just M11 files. This modified non-M11 files and caused coverage percentage drift.

**Resolution:** Reverted all non-M11 files to `main` branch state. M11 scope was strictly preserved.

**Guardrail Recommendation:** When running linters, scope to changed files only: `ruff check src/renacechess/features/ tests/test_m11*.py`

### Minimal Fix Set

None required — CI is green.

---

## 5. Tests & Coverage (Delta-Only)

### Coverage Delta

| Metric | Value |
|--------|-------|
| Overall coverage | 90%+ (threshold met) |
| New M11 files | 70-100% (mixed, but no regressions) |
| Non-regression | ✅ Satisfied (overlap-set comparison) |

### New Tests Added

| File | Test Count | Coverage Target |
|------|------------|-----------------|
| `test_m11_per_piece_features.py` | 17 | `features/per_piece.py` |
| `test_m11_square_map_features.py` | 18 | `features/square_map.py` |
| `test_m11_context_bridge_v2.py` | 12 | `features/context_bridge_v2.py`, `contracts.models` |

### Golden FEN Testing

3 curated FEN positions used for determinism verification:
1. Starting position (baseline)
2. Complex middle game (holes, dominated pieces)
3. Endgame (pawn contestability)

### Summary

| Category | Items |
|----------|-------|
| **Missing Tests** | None critical |
| **Fast Fixes** | None |
| **New Markers** | Consider `@pytest.mark.structural` for M11 tests |

---

## 6. Security & Supply Chain (Delta-Only)

### Dependency Deltas

No new dependencies added. M11 uses only:
- `chess` (already in deps)
- `pydantic` (already in deps)

### Secrets Exposure

No secrets involved.

### Workflow Trust Boundaries

No changes to CI workflow permissions.

### SBOM/Provenance

No impact on SBOM — pure Python additions.

---

## 7. RediAI v3 Guardrail Compliance Check

| Guardrail | Status | Notes |
|-----------|--------|-------|
| CPU-only enforcement | ✅ PASS | No GPU dependencies |
| Multi-tenant isolation | N/A | No tenancy in scope |
| Monorepo migration friendliness | ✅ PASS | `features/` is cleanly extractable |
| Contract drift prevention | ✅ PASS | JSON schemas + Pydantic models in sync |
| Workflow required checks | ✅ PASS | All checks enforced |
| Supply chain hygiene | ✅ PASS | No new deps, actions unchanged |

---

## 8. Top Issues

No HIGH or MED issues identified.

| ID | Severity | Observation | Status |
|----|----------|-------------|--------|
| — | — | No issues | — |

---

## 9. PR-Sized Action Plan

| ID | Task | Category | Acceptance Criteria | Risk | Est |
|----|------|----------|---------------------|------|-----|
| M11-01 | Generate M11_summary.md | Docs | File exists with all sections | Low | 15m |
| M11-02 | Update renacechess.md | Governance | M11 row added to milestone table | Low | 5m |
| M11-03 | Lock PoC (poc-v1.0) | Governance | Tag created, release manifest generated | Low | 30m |

---

## 10. Deferred Issues Registry

No new deferrals from M11.

| ID | Issue | Discovered | Deferred To | Reason | Blocker? | Exit Criteria |
|----|-------|------------|-------------|--------|----------|---------------|
| — | — | — | — | — | — | — |

---

## 11. Score Trend

| Milestone | Arch | Mod | Health | CI | Sec | Perf | DX | Docs | Overall |
|-----------|------|-----|--------|----|----|------|----|----|---------|
| M10 | 4.5 | 4.5 | 4.5 | 4.5 | 5.0 | 3.5 | 4.0 | 4.0 | 4.3 |
| **M11** | **4.7** | **4.7** | **4.5** | **4.5** | **5.0** | **3.5** | **4.0** | **4.5** | **4.4** |

**Score Movement:**
- Arch +0.2: Clean module boundary for structural cognition
- Mod +0.2: `features/` package properly isolated
- Docs +0.5: Frozen contract document adds governance clarity

---

## 12. Flake & Regression Log

No new flakes or regressions.

| Item | Type | First Seen | Current Status | Last Evidence | Fix/Defer |
|------|------|------------|----------------|---------------|-----------|
| — | — | — | — | — | — |

---

## Machine-Readable Appendix

```json
{
  "milestone": "M11",
  "mode": "delta",
  "commit": "b8860ee",
  "range": "67fba02...b8860ee",
  "verdict": "green",
  "quality_gates": {
    "ci": "pass",
    "tests": "pass",
    "coverage": "pass",
    "security": "pass",
    "dx_docs": "pass",
    "guardrails": "pass"
  },
  "issues": [],
  "deferred_registry_updates": [],
  "score_trend_update": {
    "arch": 4.7,
    "mod": 4.7,
    "health": 4.5,
    "ci": 4.5,
    "sec": 5.0,
    "perf": 3.5,
    "dx": 4.0,
    "docs": 4.5,
    "overall": 4.4
  }
}
```

