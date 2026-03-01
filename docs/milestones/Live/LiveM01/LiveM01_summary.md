# LiveM01 Summary — Deterministic Skill Conditioning (Research Side)

**Project:** RenaceCHESS (Research Repository)  
**Milestone:** LiveM01 — Skill Conditioning Activation  
**Triggered by:** RenaceCHESS-Live M09 (Live boundary validated; research artifact needed skill differentiation)  
**Status:** Complete  
**Version:** 0.1.0 → 0.2.0

---

## Objective

Modify `BaselinePolicyV1` so that different skill identifiers produce distinct, deterministic move distributions via temperature scaling. No schema changes, no nondeterminism, no new external dependencies.

---

## What Changed

### 1. Temperature Scaling in `BaselinePolicyV1.forward()` 

**File:** `src/renacechess/models/baseline_v1.py`

Added deterministic temperature scaling applied **after legal-move masking** but **before softmax normalization**:

```
logits (masked to legal moves only)
  → divide by temperature(skill_id)
    → softmax → probabilities
```

Temperature map:

| Skill Level | Temperature | Effect |
|-------------|-------------|--------|
| beginner    | 1.6         | Flattest (most uniform) |
| intermediate| 1.2         | Moderate |
| advanced    | 0.9         | Sharper |
| expert      | 0.75        | Focused |
| master      | 0.6         | Sharpest (most peaked) |

### 2. Dual-Key Support

Temperature lookup supports **both** named keys and Elo-range keys:

| Named Key | Elo Keys | Temperature |
|-----------|----------|-------------|
| beginner | lt_800, 800_999 | 1.6 |
| intermediate | 1000_1199, 1200_1399 | 1.2 |
| advanced | 1400_1599, 1600_1799 | 0.9 |
| expert | 1800_1999, gte_1800 | 0.75 |
| master | gte_2000 | 0.6 |

Unknown keys default to beginner temperature (1.6) — safest default.

### 3. Version Bump

- `pyproject.toml`: 0.1.0 → 0.2.0
- `src/renacechess/__init__.py`: `__version__` = "0.2.0"

---

## What Did NOT Change

- `_encode_skill_bucket()` — untouched (embedding path preserved)
- `forward_logits()` — untouched (logits are pre-temperature)
- Training infrastructure — untouched
- All existing tests — zero regressions (16/16 M08 tests pass)
- No schema changes
- No new dependencies

---

## Test Results

### New Tests: 19 passed

| Category | Tests | Status |
|----------|-------|--------|
| Temperature lookup (named keys) | 1 | ✅ |
| Temperature lookup (Elo keys) | 1 | ✅ |
| Temperature case insensitivity | 1 | ✅ |
| Temperature unknown default | 1 | ✅ |
| Temperature whitespace handling | 1 | ✅ |
| Skill differentiation (named) | 1 | ✅ |
| Skill differentiation (Elo) | 1 | ✅ |
| Valid distributions (all buckets) | 1 | ✅ |
| At least 3 distinct distributions | 1 | ✅ |
| Entropy: beginner > advanced | 1 | ✅ |
| Entropy: advanced > master | 1 | ✅ |
| Entropy: monotone decreasing | 1 | ✅ |
| Entropy: varies across skills | 1 | ✅ |
| Same move count across buckets | 1 | ✅ |
| Determinism: same skill twice | 1 | ✅ |
| Determinism: Elo keys twice | 1 | ✅ |
| Determinism: across model instances | 1 | ✅ |
| Determinism: midgame position | 1 | ✅ |
| Cross-key temperature equivalence | 1 | ✅ |

### Existing Tests: 16 passed (zero regressions)

All M08 model tests pass unchanged.

---

## Entropy Values (Starting Position, Audit Trail)

Position: `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`  
Legal moves: 20

| Skill | Temperature | Entropy | Top Move |
|-------|-------------|---------|----------|
| beginner | 1.60 | 2.9787475712 | a2a4 (0.072693) |
| intermediate | 1.20 | 2.9652181970 | a2a4 (0.081728) |
| advanced | 0.90 | 2.9407727681 | a2a4 (0.094967) |
| expert | 0.75 | 2.9158468079 | a2a4 (0.106546) |
| master | 0.60 | 2.8694411586 | a2a4 (0.125537) |

**Monotonicity:** Confirmed (beginner > intermediate > advanced > expert > master)  
**Determinism:** Confirmed (each skill produces identical output on repeat)

---

## Artifact

| Property | Value |
|----------|-------|
| Version | 0.2.0 |
| Wheel | `renacechess-0.2.0-py3-none-any.whl` |
| SHA256 | `DB1C0B2B0AE8F696750055D3889157E7186D609887F3AC79EA9B30482FB3C3DD` |

---

## Live-Side Next Steps (Not Done Here)

1. Bump Live dependency to `renacechess==0.2.0`
2. Update artifact boundary SHA256
3. Run Live test suite (including `test_skill_conditioning.py`)
4. Refresh goldens if default behavior changed
5. Complete Live M09 closeout

---

## Scientific Acceptance

For the same FEN:
- beginner ≠ intermediate ≠ advanced ≠ expert ≠ master (distinct distributions) ✅
- entropy(beginner) > entropy(intermediate) > ... > entropy(master) ✅
- Repeated calls with same (fen, skill_id) → identical probabilities ✅
- No schema change; no probability mass loss; no legal-move leakage ✅
