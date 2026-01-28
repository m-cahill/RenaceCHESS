# 📌 Milestone Summary — M11: Structural Interpretability Expansion

**Project:** RenaceCHESS  
**Phase:** Proof of Concept (PoC)  
**Milestone:** M11 — Structural Interpretability Expansion  
**Timeframe:** 2026-01-27 → 2026-01-28  
**Status:** ✅ Closed (MERGED)

---

## 1. Milestone Objective

M11 introduced **structural cognition** to RenaceCHESS — piece-level and square-level features that capture classical chess positional concepts (mobility, tension, weak squares, holes) without altering core policy or evaluation semantics.

This was necessary because:
- Prior milestones (M00-M10) established the behavioral substrate (move prediction, difficulty, outcomes)
- **No structural grounding existed** for LLM coaching or personality modeling
- Future personality modules (M12+) require interpretable features to express style variations

Without M11, RenaceCHESS would have:
- No piece-level semantic features for grounding
- No square-level positional analysis for coaching narratives
- Limited ability to express "why" a position is difficult or risky

---

## 2. Scope Definition

### In Scope

| Component | Description |
|-----------|-------------|
| `PerPieceFeaturesV1` | 32-slot tensor with mobility, tension, and flags per piece |
| `SquareMapFeaturesV1` | 64-entry boolean maps for weak/strong/hole analysis |
| `ContextBridgePayloadV2` | Versioned superset of v1 with structural cognition |
| `StructuralCognitionContract_v1.md` | Frozen constitutional document for v1 semantics |
| Feature extractors | Pure Python extractors using `python-chess` |
| Golden FEN tests | 3 curated positions for determinism verification |

### Out of Scope

| Item | Rationale |
|------|-----------|
| Policy changes | Structural features are read-only, no behavioral influence |
| Engine calls | Extractors are engine-free by contract |
| CLI integration | No new CLI commands in M11 |
| Personality modules | Deferred to M12 |

**Scope did not change during execution.**

---

## 3. Work Executed

### Files Created

| Category | Count | Files |
|----------|-------|-------|
| Contract | 1 | `docs/contracts/StructuralCognitionContract_v1.md` |
| JSON Schemas | 3 | `PerPieceFeaturesV1.schema.json`, `SquareMapFeaturesV1.schema.json`, `context_bridge.v2.schema.json` |
| Feature Extractors | 4 | `features/__init__.py`, `per_piece.py`, `square_map.py`, `context_bridge_v2.py` |
| Test Fixtures | 1 | `tests/fixtures/fens_m11.json` |
| Tests | 3 | `test_m11_per_piece_features.py`, `test_m11_square_map_features.py`, `test_m11_context_bridge_v2.py` |
| Governance | 2 | `M11_toolcalls.md`, `M11_run1.md` |

### Pydantic Models Added

- `PerPieceFeature` — Individual piece feature slot
- `PerPieceFeaturesV1` — Container for 32 piece features
- `SquareMapFeaturesV1` — Square-level boolean maps
- `StructuralCognition` — Combined structural cognition container
- `StructuralLabel` — Narrative labels for structural features
- `NarrativeSeedV2` — Extended narrative seed types
- `ContextBridgeMetaV2` — Versioned metadata for v2
- `ContextBridgePayloadV2` — Full v2 payload with structural cognition

### Feature Semantics Implemented

| Feature | Definition |
|---------|------------|
| Safe mobility | Moves to unattacked squares or defended by equal/lower value piece |
| Hanging piece | Attacked and not defended, or net_defense < 0 |
| Pinned piece | Cannot move without exposing king |
| Hole (for side S) | Not pawn-contestable AND control_diff < 0 |
| Weak square | control_diff < 0 AND not pawn-contestable |
| Strong square | control_diff > 0 AND pawn-contestable |

---

## 4. Validation & Evidence

### Tests Run

| Test Suite | Count | Status |
|------------|-------|--------|
| M11-specific tests | 47 | ✅ All passed |
| Full test suite | 383 | ✅ All passed (1 skipped) |

### Coverage

| Metric | Value |
|--------|-------|
| Overall | 90%+ (threshold met) |
| Non-regression | ✅ Satisfied |

### CI Verification

4 CI runs were required to reach green:

1. **Run 1** — Lint errors (E501, E741) → Fixed
2. **Run 2** — Format + coverage regression → Applied format
3. **Run 3** — Coverage regression (non-M11 files modified) → Reverted non-M11 files
4. **Run 4** — ✅ All checks passed

### Key Finding

CI correctly detected out-of-scope changes when `ruff check .` auto-fixed files across the entire codebase. This demonstrates **truthful CI governance** — green only when the change is actually safe.

---

## 5. CI / Automation Impact

### Workflows Affected

None. M11 did not modify CI workflows.

### Checks Behavior

| Check | Behavior |
|-------|----------|
| Lint and Format | Correctly blocked formatting violations |
| Coverage | Correctly detected coverage regression from non-M11 file changes |
| Type Check | Passed without intervention |

### Signal Quality

CI:
- ✅ Blocked incorrect changes (out-of-scope auto-fixes)
- ✅ Validated correct changes (final implementation)
- ✅ Did not produce false positives

---

## 6. Issues & Exceptions

### Issue: Coverage Regression from Auto-Fixes

| Field | Value |
|-------|-------|
| Description | Running `ruff check .` auto-fixed unused imports in non-M11 files |
| Root Cause | Ruff modifies files in-place by default when invoked without `--no-fix` |
| Resolution | Reverted non-M11 files to `main` branch state |
| Tracking | Documented in `M11_run1.md` |

**No new issues were introduced in the final merged state.**

---

## 7. Deferred Work

No new deferrals from M11.

All M10 deferrals remain closed:
- LEGACY-COV-001: ✅ Resolved
- CLI-COV-001: ✅ Resolved
- EVAL-RUNNER-COV-001: ✅ Resolved

---

## 8. Governance Outcomes

### What is now provably true:

1. **Structural cognition is deterministic** — Given a FEN, features are byte-identical
2. **Context Bridge is versioned** — v2 supersets v1 with structural cognition
3. **Semantic definitions are frozen** — `StructuralCognitionContract_v1.md` locks v1 semantics
4. **Feature extraction is engine-free** — No runtime engine calls by contract
5. **Coverage discipline maintained** — Non-regression satisfied, 90%+ overall

### Governance Strengthened

- Versioned contracts prevent semantic drift
- Frozen definitions enable stable LLM grounding
- Clean module boundaries enable future extraction

---

## 9. Exit Criteria Evaluation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| PerPieceFeaturesV1 implemented | ✅ Met | `features/per_piece.py` + tests |
| SquareMapFeaturesV1 implemented | ✅ Met | `features/square_map.py` + tests |
| Context Bridge v2 created | ✅ Met | Schema + Pydantic model |
| Structural Cognition Contract frozen | ✅ Met | `StructuralCognitionContract_v1.md` |
| Golden FEN tests passing | ✅ Met | `fens_m11.json` + 47 tests |
| Coverage ≥ 90% | ✅ Met | 90%+ overall |
| No coverage regression | ✅ Met | Overlap-set comparison passed |
| CI green | ✅ Met | Run 21421642384 |

---

## 10. Final Verdict

**Milestone objectives met. Safe to proceed.**

M11 delivered a complete, deterministic, frozen structural cognition layer. The PoC cognitive substrate is now architecturally complete:

- Move prediction (M04-M08)
- Human difficulty (M07)
- Outcome prediction (M09)
- **Structural cognition (M11)**

---

## 11. Authorized Next Step

The following are explicitly authorized:

1. **Lock PoC (`poc-v1.0`)** — Create release tag and manifest
2. **M12: First Personality Module** — Bounded personality shaping using structural features

**Constraint:** No behavioral changes to core policy or evaluation without governance review.

---

## 12. Canonical References

### Commits

| SHA | Description |
|-----|-------------|
| `0afb3fa` | feat(M11): Structural Interpretability Expansion |
| `7bf1693` | fix(M11): Lint fixes |
| `128e417` | style(M11): Apply ruff formatting |
| `effe8ad` | revert: Restore non-M11 files |
| `a4f0336` | docs(M11): Add CI analysis report |
| `b8860ee` | Merge commit to main |

### Pull Request

- PR #13: https://github.com/m-cahill/RenaceCHESS/pull/13

### Documents

| Document | Path |
|----------|------|
| M11 Plan | `docs/milestones/PoC/M11/M11_plan.md` |
| M11 Toolcalls | `docs/milestones/PoC/M11/M11_toolcalls.md` |
| M11 CI Analysis | `docs/milestones/PoC/M11/M11_run1.md` |
| M11 Audit | `docs/milestones/PoC/M11/M11_audit.md` |
| Structural Cognition Contract | `docs/contracts/StructuralCognitionContract_v1.md` |

### Schemas

| Schema | Path |
|--------|------|
| PerPieceFeaturesV1 | `src/renacechess/contracts/schemas/v1/PerPieceFeaturesV1.schema.json` |
| SquareMapFeaturesV1 | `src/renacechess/contracts/schemas/v1/SquareMapFeaturesV1.schema.json` |
| Context Bridge v2 | `src/renacechess/contracts/schemas/v1/context_bridge.v2.schema.json` |

