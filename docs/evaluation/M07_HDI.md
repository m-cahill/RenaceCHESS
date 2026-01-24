# Human Difficulty Index (HDI) v1 — M07

## Overview

The Human Difficulty Index (HDI) is a deterministic, explainable scalar measure of cognitive difficulty for humans at a given skill/time level. HDI v1 is computed from existing evaluation signals (policy entropy, top-gap, legal move count, outcome sensitivity) without requiring new model training.

**HDI is not:**
- A learned metric (it's a pure function)
- An engine evaluation (it measures human difficulty, not optimality)
- A replacement for policy accuracy (it complements accuracy metrics)

**HDI is:**
- A derived metric from existing evaluation signals
- Deterministic (same inputs → same HDI)
- Explainable (components are exposed)
- Human-centric (measures cognitive difficulty, not engine strength)

---

## HDI v1 Formula

HDI v1 is computed as a weighted linear combination of normalized components:

```text
HDI = clamp01(
    0.40 * norm_entropy +
    0.25 * norm_top_gap_inverted +
    0.20 * norm_legal_move_pressure +
    0.15 * norm_outcome_sensitivity
)
```

### Component Weights (Fixed, Documented)

| Component                   | Weight | Rationale                           |
| --------------------------- | ------ | ----------------------------------- |
| Entropy                     | 0.40   | Dominant signal for human ambiguity |
| Top-gap (inverted)          | 0.25   | Measures decisiveness vs confusion  |
| Legal move pressure         | 0.20   | Captures branching burden           |
| Outcome sensitivity (proxy) | 0.15   | Captures consequence severity       |

**Note:** Weights are static and hard-coded. Changes to weights constitute HDI spec v2, not a patch.

---

## Component Definitions

### 1. Normalized Entropy

**Source:** Policy entropy (Shannon entropy in bits)

**Normalization:**
```text
norm_entropy = clamp01(entropy / 10.0)
```

**Rationale:** 10 bits is a reasonable upper bound for chess policy entropy. Higher entropy indicates more ambiguity in move selection.

### 2. Normalized Top-Gap Inverted

**Source:** Top gap (p1 - p2, the probability difference between top-2 moves)

**Normalization:**
```text
norm_top_gap_inverted = 1.0 - clamp01(top_gap)
```

**Rationale:** Inverted so that higher values indicate more ambiguity (smaller gap = more confusion). A gap of 0.0 means equal probability for top moves (maximum ambiguity).

### 3. Normalized Legal Move Pressure

**Source:** Number of legal moves in the position

**Normalization:**
```text
norm_legal_move_pressure = clamp01(legal_moves_count / 40)
```

**Rationale:** 40 is a human-relevant ceiling (not the theoretical maximum of ~218). Positions with > 40 legal moves are cognitively equivalent for humans. This keeps the signal meaningful instead of diluted.

### 4. Outcome Sensitivity (Proxy)

**Source:** Proxy when no outcome head exists (M07)

**Proxy Formula:**
```text
norm_outcome_sensitivity = clamp01(
    normalize_entropy(entropy) * normalize_top_gap_inverted(top_gap)
)
```

**Rationale:** Combines entropy and ambiguity as a proxy for how much the outcome changes with move choice. When a real outcome head exists (M08+), the proxy is replaced, not mixed.

**Metadata:**
- `source`: `"proxy"` (M07) or `"outcome_head"` (M08+)
- `note`: Explains the proxy formula

---

## HDI Properties

### Determinism

HDI computation is **deterministic**: identical inputs produce identical outputs. This is verified by:
- Pure functions (no side effects)
- No randomness
- Floating-point stable (explicit rounding where needed)

### Monotonicity Properties

HDI exhibits expected monotonicity properties:

1. **HDI increases with entropy** (all else equal)
   - Higher entropy → more ambiguous → higher difficulty

2. **HDI increases as top-gap decreases** (all else equal)
   - Smaller gap → more confusion → higher difficulty

3. **HDI increases with legal move count** (all else equal)
   - More moves → more branching → higher difficulty

### Range

HDI values are clamped to `[0.0, 1.0]`:
- `0.0`: Minimum difficulty (clear, decisive position)
- `1.0`: Maximum difficulty (highly ambiguous, many moves, high entropy)

---

## Usage in Evaluation Reports

HDI is included in **Eval Report v4** (M07) as an optional field in `ConditionedMetrics`:

```json
{
  "hdi": {
    "value": 0.73,
    "specVersion": 1,
    "components": {
      "entropy": 0.82,
      "topGapInverted": 0.41,
      "legalMovePressure": 0.67,
      "outcomeSensitivity": {
        "value": 0.55,
        "source": "proxy",
        "note": "entropy * (1 - topGap); replaced when outcome head exists"
      }
    }
  }
}
```

HDI is computed for:
- Overall metrics (all records)
- Stratified metrics (by skill bucket, time control class, time pressure bucket)

---

## Backward Compatibility

- **Eval Report v3** remains valid (HDI field is optional)
- **Eval Report v4** is additive (extends v3 with HDI)
- Existing v3 reports continue to validate

---

## Implementation Details

### Module

`src/renacechess/eval/hdi.py`

### Key Functions

- `compute_hdi_v1()`: Main HDI computation function
- `normalize_entropy()`: Entropy normalization
- `normalize_top_gap_inverted()`: Top gap inversion and normalization
- `normalize_legal_move_pressure()`: Legal move count normalization
- `compute_outcome_sensitivity_proxy()`: Outcome sensitivity proxy

### Integration

HDI is computed in `ConditionedMetricsAccumulator.build_metrics()` from mean values of:
- Policy entropy (from `entropy_values`)
- Top gap (from `top_gap_values`)
- Legal moves count (from `legal_moves_count_values`)

---

## Future Evolution

### HDI Spec v2 (Post-PoC)

Potential changes for v2:
- Updated weights (if empirical evidence suggests different balance)
- Additional components (e.g., tactical complexity, positional tension)
- Outcome sensitivity from real outcome head (replaces proxy)

**Governance:** Weight changes or formula changes require a new spec version. No silent changes.

---

## References

- **M07 Plan:** `docs/milestones/PoC/M07/M07_plan.md`
- **HDI Module:** `src/renacechess/eval/hdi.py`
- **HDI Tests:** `tests/test_m07_hdi.py`
- **Eval Report Schema v4:** `src/renacechess/contracts/schemas/v1/eval_report.v4.schema.json`

