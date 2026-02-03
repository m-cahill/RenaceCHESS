# M32 Audit: POST-TRAIN-EVAL-PACK-001

**Milestone:** M32  
**Phase:** E (Scale Proof, Training Run, Release Lock)  
**Audit Date:** 2026-02-03  
**Verdict:** ✅ PASS  

---

## Executive Summary

M32 successfully implemented and executed post-training evaluation infrastructure. The trained M31 checkpoints were evaluated against the full frozen eval v2 set (10,000 positions) and compared to fresh-init baselines. All governance requirements were met.

---

## Execution Verdict: PASS

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All positions evaluated | ✅ | 10,000 / 10,000 |
| No training overlap | ✅ | Verified in report |
| Baseline seed fixed | ✅ | 1337 |
| Delta metrics computed | ✅ | Policy + Outcome |
| Artifacts hash-chained | ✅ | SHA-256 in report |
| Schemas validated | ✅ | CI job passed |
| Tests passed | ✅ | 59/59 M32 tests |

---

## Material Findings

**None.**

All deviations from initial implementation were:
1. Documented in toolcalls log
2. Fixed with transparent code changes
3. Committed with clear commit messages

---

## Known Limitations

### Minimal Training Vocabulary

The M31 training run used an 8-move vocabulary:
- `e2e4`, `d2d4`, `g1f3`, `c2c4` (white opening moves)
- `e7e5`, `d7d5`, `g8f6`, `c7c5` (black opening moves)

**Impact:** Trained model shows "degraded" metrics compared to baseline because:
- Baseline has uniform probability over vocab, occasionally matching by chance
- Trained model is confident in wrong moves for positions outside its distribution

**Mitigation:** This is expected behavior for a proof-of-concept. Production training will use full move vocabulary.

**Risk Level:** None — the limitation is by design and does not affect infrastructure validity.

---

## Carry-Forward Risk

**None.**

M32 is a read-only evaluation milestone. No state is modified that could affect downstream milestones. The evaluation report is a static artifact.

---

## Compatibility Fixes Applied

| Fix | Reason | Resolution |
|-----|--------|------------|
| Vocab size loading | Checkpoint trained with 8 moves, default is 1000 | Read from metadata JSON |
| Record parsing | FrozenEval v2 has `chosenMove` at top level | Updated extraction path |
| Legal moves | FrozenEval v2 lacks `legalMoves` field | Compute from FEN |

All fixes were applied during execution phase with documentation.

---

## Governance Compliance

### Two-Phase Flow

| Phase | Status | Evidence |
|-------|--------|----------|
| Implementation (CI only) | ✅ | PR #38, 4 CI runs |
| Execution (local GPU) | ✅ | Commit 89b9a4c |

### Artifact Integrity

| Artifact | Hash Recorded | Verified |
|----------|---------------|----------|
| Policy checkpoint | `sha256:94b65268...` | ✅ |
| Outcome checkpoint | `sha256:d815f508...` | ✅ |
| Frozen eval manifest | `sha256:73a0c4aa...` | ✅ |
| Training run report | `sha256:6462f2f2...` | ✅ |
| Determinism hash | `sha256:3897a8b0...` | ✅ |

### CI Validation

| Job | Status |
|-----|--------|
| M32 Eval Pack Validation | ✅ PASS |
| All 12 CI jobs | ✅ PASS |

---

## Recommendations

1. **For M33:** Package M32 artifacts into external proof bundle as-is
2. **For future:** Consider adding move vocabulary size to report metadata
3. **No code changes required**

---

## Audit Conclusion

M32 meets all exit criteria. The infrastructure is validated and ready for packaging in M33.

| Criterion | Met |
|-----------|-----|
| Single objective achieved | ✅ |
| All deliverables complete | ✅ |
| Tests passing | ✅ |
| CI green | ✅ |
| Artifacts committed | ✅ |
| Documentation updated | ✅ |

**Final Status:** ✅ CLOSED — EXECUTED

---

**Auditor:** AI Agent  
**Date:** 2026-02-03  

