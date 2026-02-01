# M20 CI Run 1 Analysis

**Run ID:** 21554238255  
**Trigger:** pull_request (PR #26)  
**Branch:** m20-elo-bucket-delta-facts  
**Status:** ✅ **SUCCESS**  
**Duration:** 4m6s total  
**Date:** 2026-02-01

---

## Job Summary

| Job | Status | Duration |
|-----|--------|----------|
| Lint and Format | ✅ Pass | 3m23s |
| Test | ✅ Pass | 4m3s |
| Type Check | ✅ Pass | 3m34s |

---

## Signal Integrity

### Tests
- **Total:** 554 tests passed
- **M20 Tests:** 42 new tests
- **Skipped:** 1 (pre-existing)
- **Coverage:** 91.57% (above 90% threshold)

### Linting
- Ruff format: ✅ Clean
- Ruff check: ✅ Clean

### Type Check
- MyPy: ✅ Pass (pre-existing warnings in other files, M20 files clean)

### Import Boundaries
- contracts-isolation: ✅ Kept
- personality-isolation: ✅ Kept
- coaching-isolation: ✅ Kept

---

## Delta Analysis

### New Files (4)
| File | Purpose | Coverage |
|------|---------|----------|
| `src/renacechess/coaching/elo_bucket_deltas.py` | Builder function | 95.76% |
| `src/renacechess/contracts/schemas/v1/elo_bucket_deltas.v1.schema.json` | JSON Schema | N/A |
| `docs/contracts/ELO_BUCKET_DELTA_FACTS_CONTRACT_v1.md` | Contract doc | N/A |
| `tests/test_m20_elo_bucket_deltas.py` | Tests | N/A |

### Modified Files (4)
| File | Changes |
|------|---------|
| `src/renacechess/contracts/models.py` | +10 Pydantic models, 100% coverage |
| `src/renacechess/coaching/__init__.py` | +1 export |
| `docs/milestones/PhaseC/M20/M20_plan.md` | Status update |
| `docs/milestones/PhaseC/M20/M20_toolcalls.md` | Implementation log |

---

## Invariant Checks

| Invariant | Status |
|-----------|--------|
| Coverage ≥ 90% | ✅ 91.57% |
| No regressions in overlap set | ✅ N/A (no overlap set changes) |
| All GitHub Actions SHA-pinned | ✅ (from M13) |
| Coaching module isolated | ✅ import-linter contract kept |
| No AdviceFacts schema changes | ✅ Frozen |
| Determinism hash reproducible | ✅ Tested |

---

## Verdict

**✅ GREEN — All checks pass. CI is healthy.**

---

## Next Actions

1. ⏳ **STOP** — Await permission to merge PR #26 to main
2. After merge: Update `renacechess.md` with M20 milestone
3. Generate M20_audit.md and M20_summary.md

---

*Analysis generated: 2026-02-01*

