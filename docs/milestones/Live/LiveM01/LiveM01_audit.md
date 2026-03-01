# LiveM01 Audit — Deterministic Skill Conditioning

**Milestone:** LiveM01  
**Audit Date:** 2026-02-28  
**Scope:** Research-side skill conditioning activation for RenaceCHESS-Live M09

---

## 1. Objective Compliance

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Different skill_id → distinct distributions | ✅ | `test_skill_conditioning_changes_distribution`, `test_at_least_three_distinct_distributions` |
| Deterministic (no RNG) | ✅ | `test_determinism_same_skill_twice`, `test_determinism_across_model_instances` |
| Preserves normalization | ✅ | `test_all_named_buckets_produce_valid_distributions` (sum=1.0 check) |
| Preserves legal-move masking | ✅ | `test_same_move_count_across_all_buckets` |
| Canonical ordering preserved | ✅ | Legal moves sorted before inference |
| No schema changes | ✅ | No schema files modified |
| No new dependencies | ✅ | No changes to `pyproject.toml` dependencies |
| No nondeterminism | ✅ | `test_determinism_midgame_position` |

---

## 2. Hard Constraints Verification

| Constraint | Satisfied | Notes |
|------------|-----------|-------|
| No random sampling | ✅ | Temperature is a pure scalar division |
| No RNG | ✅ | No `torch.rand`, no `random.*` |
| No stochastic dropout | ✅ | Model in eval mode; no dropout added |
| No env-dependent behavior | ✅ | Temperature map is hardcoded |
| No schema change | ✅ | Zero schema files touched |
| No float instability | ✅ | `max(temp, 1e-8)` guards division-by-zero |
| Pure functional transformation | ✅ | `temperature_for_skill()` is stateless |

---

## 3. Implementation Review

### Temperature Scaling Location

**Correct:** Applied after `forward_logits()` extracts masked logits, before `softmax()`.

```python
# In forward():
temp = max(temperature_for_skill(skill_bucket), 1e-8)
scaled_logits = legal_logits / temp
probs = functional.softmax(scaled_logits, dim=0)
```

**Verified:** Illegal move logits are already excluded by `forward_logits()` before temperature is applied. No probability mass leaks to illegal moves.

### Dual-Key Resolution

**Correct:** `temperature_for_skill()` checks named keys first, then Elo keys, then defaults to 1.6.

**Verified:** Existing `_encode_skill_bucket()` is NOT modified. Temperature scaling is additive — a separate concern from the embedding path.

### Version Bump

| File | Before | After |
|------|--------|-------|
| `pyproject.toml` | 0.1.0 | 0.2.0 |
| `src/renacechess/__init__.py` | 0.1.0 | 0.2.0 |

---

## 4. Test Coverage

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_livem01_skill_conditioning.py` | 19 | ✅ All pass |
| `test_m08_model.py` | 16 | ✅ All pass (zero regressions) |

### Test Categories

- **Temperature lookup:** 5 tests (named, Elo, case, unknown, whitespace)
- **Skill differentiation:** 4 tests (named, Elo, valid distributions, distinctness)
- **Entropy ordering:** 4 tests (beginner>advanced, advanced>master, monotone, varies)
- **Move integrity:** 1 test (same move count across buckets)
- **Determinism:** 4 tests (same skill, Elo keys, cross-instance, midgame)
- **Cross-key:** 1 test (named ↔ Elo temperature equivalence)

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Existing tests break | None | N/A | 16/16 M08 tests pass |
| Float precision drift | Low | Low | `max(temp, 1e-8)` + existing clamp/renormalize |
| Live goldens break | Expected | Low | Live handles golden refresh under M09 governance |
| Training path affected | None | N/A | `forward_logits()` unchanged; training uses logits, not probs |

---

## 6. Files Modified

| File | Change | Lines Changed |
|------|--------|---------------|
| `src/renacechess/models/baseline_v1.py` | Temperature scaling + dual-key lookup | ~50 added |
| `src/renacechess/__init__.py` | Version bump | 1 |
| `pyproject.toml` | Version bump | 1 |

### Files Added

| File | Purpose |
|------|---------|
| `tests/test_livem01_skill_conditioning.py` | 19 tests for skill conditioning |

### Files NOT Modified

- All schema files
- All other model files
- All evaluation files
- All coaching/personality files
- All existing tests

---

## 7. Audit Verdict

**PASS** — Implementation satisfies all requirements, hard constraints, and scientific acceptance criteria. Zero regressions. Artifact ready for Live-side consumption.
