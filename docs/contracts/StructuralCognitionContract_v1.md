# Structural Cognition Contract v1

**Project:** RenaceCHESS  
**Version:** v1  
**Status:** FROZEN  
**Effective From:** M11 (Structural Interpretability Expansion)  
**Last Updated:** 2026-01-27

---

## 1. Purpose

This document defines the **authoritative contract** for structural cognition in RenaceCHESS. It specifies:

- Piece indexing and identity rules
- Square-map semantics and invariants
- Determinism guarantees
- Backward-compatibility rules
- Behavioral impact prohibition

All implementations of structural features **MUST** comply with this contract.

---

## 2. Scope

This contract governs:

| Component | Description |
|-----------|-------------|
| `PerPieceFeaturesV1` | Piece-indexed structural tensor (32 slots) |
| `SquareMapFeaturesV1` | Square-level weak/strong/hole maps (64 squares × 6 maps) |
| Context Bridge v2 | LLM grounding payload with structural cognition fields |

This contract does **NOT** govern:

- Move policy behavior
- Outcome head predictions
- HDI computation
- Training or evaluation semantics

---

## 3. Piece Indexing Rules (FROZEN)

### 3.1 Slot Ordering

All pieces are indexed in a **fixed 32-slot ordering** that **never changes**, regardless of captures, promotions, or game state.

| Slots 0–15 (White) | Slots 16–31 (Black) |
|--------------------|---------------------|
| 0: K (King) | 16: k (King) |
| 1: Q (Queen) | 17: q (Queen) |
| 2: R_a (a-file Rook) | 18: r_a (a-file Rook) |
| 3: R_h (h-file Rook) | 19: r_h (h-file Rook) |
| 4: B_c (c-file Bishop) | 20: b_c (c-file Bishop) |
| 5: B_f (f-file Bishop) | 21: b_f (f-file Bishop) |
| 6: N_b (b-file Knight) | 22: n_b (b-file Knight) |
| 7: N_g (g-file Knight) | 23: n_g (g-file Knight) |
| 8: P_a (a-file Pawn) | 24: p_a (a-file Pawn) |
| 9: P_b (b-file Pawn) | 25: p_b (b-file Pawn) |
| 10: P_c (c-file Pawn) | 26: p_c (c-file Pawn) |
| 11: P_d (d-file Pawn) | 27: p_d (d-file Pawn) |
| 12: P_e (e-file Pawn) | 28: p_e (e-file Pawn) |
| 13: P_f (f-file Pawn) | 29: p_f (f-file Pawn) |
| 14: P_g (g-file Pawn) | 30: p_g (g-file Pawn) |
| 15: P_h (h-file Pawn) | 31: p_h (p-file Pawn) |

**Rook/Bishop/Knight file assignment:**
- Rooks: a-file (queenside) and h-file (kingside)
- Bishops: c-file (dark square) and f-file (light square)
- Knights: b-file (queenside) and g-file (kingside)

### 3.2 Capture Handling

When a piece is captured:

- `alive: false`
- `square: null`
- **All other fields remain present** (zeroed or last-known as appropriate)
- **The slot is never removed or reordered**

This preserves:
- Tensor stability
- Historical identity
- LLM interpretability ("the a-rook is gone")

### 3.3 Pawn Promotion

When a pawn promotes:

- The **pawn slot retains identity** (e.g., `P_a` remains slot 8)
- Set `is_promoted: true`
- Set `promoted_to: "Q" | "R" | "B" | "N"`

**No new piece slots are created.** The promoted piece inherits the pawn slot.

---

## 4. Per-Piece Feature Fields (FROZEN)

Each slot in `PerPieceFeaturesV1` contains:

### 4.1 Identity Fields

| Field | Type | Description |
|-------|------|-------------|
| `slot_id` | int | Slot index (0–31) |
| `color` | "white" \| "black" | Piece color |
| `piece_type` | "K" \| "Q" \| "R" \| "B" \| "N" \| "P" | Original piece type |
| `starting_file` | "a"–"h" | Starting file for piece identity |

### 4.2 State Fields

| Field | Type | Description |
|-------|------|-------------|
| `alive` | bool | Is the piece still on the board? |
| `square` | string \| null | Current square (e.g., "e4") or null if captured |
| `is_promoted` | bool | Has this pawn promoted? (only for P slots) |
| `promoted_to` | "Q" \| "R" \| "B" \| "N" \| null | Promotion target (only if is_promoted) |

### 4.3 Mobility Fields

| Field | Type | Description |
|-------|------|-------------|
| `mobility_legal` | int | Count of legal moves for this piece |
| `mobility_safe` | int | Count of "safe" moves (see §5 for definition) |

### 4.4 Tension Fields

| Field | Type | Description |
|-------|------|-------------|
| `attacked_by` | int | Count of enemy pieces attacking this piece |
| `defended_by` | int | Count of friendly pieces defending this piece |
| `net_defense` | int | `defended_by - attacked_by` |

### 4.5 Tactical Flags

| Field | Type | Description |
|-------|------|-------------|
| `is_hanging` | bool | `attacked_by > 0` AND `defended_by == 0` |
| `is_pinned` | bool | Piece is pinned to the king |
| `is_restricted` | bool | `mobility_legal < 3` (arbitrary threshold) |
| `is_dominated` | bool | `net_defense < -1` (under significant pressure) |
| `is_attacker` | bool | Attacks enemy pieces or key squares |
| `is_defender_of_king` | bool | Defends squares around friendly king |

---

## 5. Safe Mobility Definition (FROZEN)

A move is **unsafe** if:

1. The destination square is attacked by **any enemy piece**, AND
2. The moving piece is **not defended** on that square by at least one friendly piece of **equal or lower value**

**Piece values for comparison:**
- P = 1
- N = 3
- B = 3
- R = 5
- Q = 9
- K = ∞ (never trades)

**Note:** Full SEE (Static Exchange Evaluation) is explicitly **out of scope** for v1. This is a static, conservative heuristic.

---

## 6. Square Map Semantics (FROZEN)

### 6.1 Maps Provided

All maps are **side-relative** and length-64 (indexed by square a1=0 to h8=63):

| Map | Type | Description |
|-----|------|-------------|
| `weak_for_white` | bool[64] | Squares that are weak for White |
| `strong_for_white` | bool[64] | Squares that are strong for White |
| `weak_for_black` | bool[64] | Squares that are weak for Black |
| `strong_for_black` | bool[64] | Squares that are strong for Black |
| `is_hole_for_white` | bool[64] | Holes (permanent weaknesses) for White |
| `is_hole_for_black` | bool[64] | Holes (permanent weaknesses) for Black |

### 6.2 Pawn Contestability

A square is **pawn-contestable for side S** if **any pawn of side S** could legally move or capture to that square in the future (ignoring checks).

This is computed by checking:
- For White pawns: Can any White pawn reach this square via advance or capture?
- For Black pawns: Can any Black pawn reach this square via advance or capture?

### 6.3 Control Differential

For a square `sq`:

```
control_diff_for_S = attackers_S(sq) - attackers_opponent(sq)
```

Where `attackers_S(sq)` counts pieces of side S that attack the square.

### 6.4 Hole Definition

A square `sq` is a **hole for side S** if:

```
pawn_contestable_by_S(sq) == false AND control_diff_for_S(sq) < 0
```

**Interpretation:** A hole is a square that:
1. Can never be defended by a pawn of side S
2. Is currently controlled more by the opponent

### 6.5 Weak/Strong Definitions

**Strong for S:**
```
control_diff_for_S(sq) > 0 AND pawn_contestable_by_S(sq) == true
```

**Weak for S:**
```
control_diff_for_S(sq) < 0 AND pawn_contestable_by_S(sq) == false
```

**Neutral:** Everything else.

---

## 7. Determinism Guarantees (INVARIANT)

### 7.1 Repeatability

Given the same FEN:
- `PerPieceFeaturesV1` output is **byte-identical** across invocations
- `SquareMapFeaturesV1` output is **byte-identical** across invocations
- Context Bridge v2 structural fields are **byte-identical** across invocations

### 7.2 Independence

Structural feature computation:
- Does **NOT** depend on random state
- Does **NOT** depend on external services
- Does **NOT** depend on trained model weights
- Is purely derived from board state

---

## 8. Backward Compatibility Rules (GOVERNANCE)

### 8.1 v1 Immutability

Once a structural feature version is frozen:
- Field names **cannot change**
- Field semantics **cannot change**
- Slot ordering **cannot change**
- Definition formulas **cannot change**

### 8.2 Extension via Versioning

New features or changed semantics require:
- A new version (v2, v3, etc.)
- A new contract document
- Explicit migration guidance

### 8.3 Additive Fields

Optional fields may be added to v1 if:
- They have default values
- They do not change existing field semantics
- They are documented in an addendum

---

## 9. Behavioral Impact Prohibition (CRITICAL)

### 9.1 Read-Only Layer

Structural cognition is a **read-only observation layer**. It:
- ❌ Does NOT influence move selection
- ❌ Does NOT modify policy probabilities
- ❌ Does NOT affect outcome predictions
- ❌ Does NOT change training loss
- ❌ Does NOT inject engine evaluations

### 9.2 Consumer Scope

Structural features are consumed by:
- Context Bridge (for LLM grounding)
- Narrative seed generation
- Future personality modules (M12+)
- Coaching UX

They are **never** fed back into policy/outcome models in v1.

---

## 10. Testing Requirements

### 10.1 Invariant Tests

All implementations must pass:
- Slot count invariant (exactly 32 pieces)
- Slot ordering invariant (fixed indices)
- Determinism tests (same FEN → same output)
- Captured piece handling (slot preserved, fields updated)
- Promotion handling (identity preserved)

### 10.2 Golden FEN Assertions

A curated set of FEN positions with expected:
- Specific piece feature values
- Specific square map cells
- Deterministic across all runs

---

## 11. Version History

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2026-01-27 | Initial frozen contract (M11) |

---

## 12. References

- `src/renacechess/contracts/schemas/v1/PerPieceFeaturesV1.schema.json`
- `src/renacechess/contracts/schemas/v1/SquareMapFeaturesV1.schema.json`
- `src/renacechess/contracts/schemas/v1/context_bridge.v2.schema.json`
- `src/renacechess/features/per_piece.py`
- `src/renacechess/features/square_map.py`
- `docs/milestones/PoC/M11/M11_plan.md`

---

**END OF CONTRACT**

