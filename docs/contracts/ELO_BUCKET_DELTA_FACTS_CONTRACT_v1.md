# ELO_BUCKET_DELTA_FACTS_CONTRACT_v1

**Version:** v1  
**Status:** 🔒 FROZEN  
**Created:** M20  
**Governing ADR:** ADR-COACHING-001

---

## 1. Purpose

This contract defines the **EloBucketDeltaFactsV1** artifact — a deterministic, facts-only representation of statistical and structural differences between two Elo skill buckets for the same position.

This artifact enables Phase C coaching by answering:

> *"What changes, statistically and structurally, as you move from one Elo bucket to the next?"*

---

## 2. Core Principle: Facts, Not Advice

**This artifact contains ONLY facts.** It does NOT contain:

- ❌ Natural language prose
- ❌ Coaching heuristics ("you should...")
- ❌ Move recommendations
- ❌ LLM prompts or translations

The artifact is **input** to downstream LLM translation (M21+), not the translation itself.

---

## 3. Bucket Semantics

### 3.1 Bucket Identifiers

Uses M06 skill bucket IDs exactly as defined in `conditioning/buckets.py`:

```
lt_800, 800_999, 1000_1199, 1200_1399, 1400_1599, 1600_1799, gte_1800, unknown
```

### 3.2 Baseline vs Comparison

- **Baseline bucket:** The reference point (typically lower skill)
- **Comparison bucket:** The bucket being compared (typically higher skill)

Deltas are computed as: `comparison - baseline`

### 3.3 Monotonicity Assumptions

When comparing lower to higher skill buckets:
- Win rate is expected to increase (win_rate_monotonic = true)
- HDI may decrease (higher skill players find position easier)
- Policy entropy may decrease (more focused move selection)

These are **observations**, not guarantees. Non-monotonic results are valid facts.

---

## 4. Delta Categories

### 4.1 Policy Divergence (`policyDelta`)

| Field | Type | Description |
|-------|------|-------------|
| `klDivergence` | float ≥ 0 | KL divergence in bits (baseline → comparison) |
| `totalVariation` | float [0, 1] | Total Variation distance |
| `rankFlips` | int ≥ 0 | Count of moves with different relative rankings |
| `massShiftToTop` | float [-1, 1] | Mass shift toward top-1 move |

### 4.2 Outcome Expectation Shifts (`outcomeDelta`)

| Field | Type | Description |
|-------|------|-------------|
| `deltaPWin` | float [-1, 1] | Change in win probability |
| `deltaPDraw` | float [-1, 1] | Change in draw probability |
| `deltaPLoss` | float [-1, 1] | Change in loss probability |
| `winRateMonotonic` | bool | True if delta_p_win ≥ 0 (expected direction) |

### 4.3 Difficulty Sensitivity (`difficultyDelta`)

| Field | Type | Description |
|-------|------|-------------|
| `deltaHDI` | float [-1, 1] | Change in Human Difficulty Index |

### 4.4 Structural Emphasis Shifts (`structuralDelta`, optional)

| Field | Type | Description |
|-------|------|-------------|
| `mobilityEmphasisDelta` | float | null | Change in mobility reliance |
| `weakSquareSensitivityDelta` | float | null | Change in weak square sensitivity |
| `kingSafetyWeightDelta` | float | null | Change in king safety weighting |

This section is **optional**. If structural data is not available for both buckets, this field is omitted.

---

## 5. Lineage & Governance

### 5.1 Source Hashes (Required)

Every artifact must include:

```json
"sourceAdviceFactsHashes": [
  "sha256:<baseline_hash>",
  "sha256:<comparison_hash>"
]
```

This creates a hard lineage chain:

```
AdviceFactsV1 (bucket A) + AdviceFactsV1 (bucket B) → EloBucketDeltaFactsV1
```

### 5.2 Determinism Hash

The `determinismHash` is computed by:

1. Building the artifact data as a dictionary
2. Computing canonical JSON (sorted keys, minimal whitespace)
3. Computing SHA-256 of the UTF-8 encoded JSON
4. Formatting as `sha256:<64-char-hex>`

Same inputs + same timestamp → identical hash.

### 5.3 Contract Versions

The artifact records which contract versions were used:

```json
"sourceContractVersions": {
  "eloBucketDeltaContract": "v1",
  "adviceFactsContract": "v1"
}
```

---

## 6. Allowed Interpretations

The following interpretations are **valid** downstream uses:

- "This move is more common at 1600 than at 1200"
- "Higher-rated players have 10% higher win expectation here"
- "Policy divergence (TV = 0.3) suggests meaningfully different preferences"

---

## 7. Forbidden Interpretations

The following interpretations are **NOT** derivable from this artifact:

- ❌ "You should play this move" (advice)
- ❌ "This is a good/bad move" (evaluation)
- ❌ Engine evaluation comparisons
- ❌ Any claim not grounded in the artifact's numeric facts

LLM translations must NOT invent analysis beyond the facts provided.

---

## 8. Explicit Non-Goals

This contract explicitly does NOT cover:

- LLM translation or prose generation
- CLI commands for delta computation
- Training or model updates
- Provider orchestration
- Changes to AdviceFactsV1 schema

---

## 9. Float Precision

All floating-point values are rounded to **6 decimal places** before:
- Inclusion in the artifact
- Computing the determinism hash

This ensures reproducibility across platforms.

---

## 10. Schema Reference

**JSON Schema:** `src/renacechess/contracts/schemas/v1/elo_bucket_deltas.v1.schema.json`

**Pydantic Models:**
- `EloBucketDeltaFactsV1`
- `PolicyDeltaV1`
- `OutcomeDeltaV1`
- `DifficultyDeltaV1`
- `StructuralEmphasisDeltaV1`
- `PolicySummaryV1`
- `OutcomeSummaryV1`

---

## 11. Version History

| Version | Date | Description |
|---------|------|-------------|
| v1 | M20 | Initial frozen version |

---

**Contract Status:** 🔒 FROZEN — No breaking changes permitted in v1.

---

*Generated: M20 (ELO-BUCKET-DELTA-FACTS-001)*

