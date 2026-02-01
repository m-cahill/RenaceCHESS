# ADVICE_FACTS_CONTRACT_v1

**Status:** FROZEN  
**Version:** v1  
**Effective:** M19 (Phase C Entry)  
**Governing ADR:** ADR-COACHING-001

---

## 1. Purpose

This contract defines the **AdviceFactsV1** artifact — a deterministic, schema-stable, facts-only payload that enables LLM coaching without hallucination.

AdviceFacts is the Phase C equivalent of the Personality Safety Contract from Phase B: it establishes a hard boundary between computed signals (truthful) and generated prose (translation only).

---

## 2. Core Principle

> **LLMs translate facts. They do not invent analysis.**

Every field in AdviceFactsV1 is pre-computed by RenaceCHESS code. The LLM's role is to translate these facts into Elo-appropriate natural language. The LLM may NOT:

- Compute or infer evaluations not present in the artifact
- Invent tactical lines or variations
- Claim move quality beyond what probabilities indicate
- Add speculation disguised as analysis

---

## 3. Schema Reference

**JSON Schema:** `src/renacechess/contracts/schemas/v1/advice_facts.v1.schema.json`  
**Pydantic Model:** `renacechess.contracts.models.AdviceFactsV1`

---

## 4. Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | `"1.0"` | Schema version identifier |
| `generatedAt` | ISO 8601 datetime | Artifact generation timestamp |
| `position` | Object | Chess position (FEN + side to move) |
| `context` | Object | Conditioning context (skill bucket, time buckets) |
| `policy` | Object | Policy distribution (top moves + recommended) |
| `outcome` | Object | W/D/L probabilities |
| `hdi` | Object | Human Difficulty Index (value + components) |
| `determinismHash` | `sha256:<hex>` | SHA-256 of canonical JSON |
| `sourceContractVersions` | Object | Referenced contract versions |

---

## 5. Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `structuralCognition` | Object | M11 structural deltas (when available) |
| `explanationHints` | Array | Placeholder for M20+ hint tags (not populated in v1) |

---

## 6. Canonical Ordering Rules

To ensure determinism, AdviceFactsV1 enforces strict ordering:

### 6.1 Move Ordering

`policy.topMoves` must be ordered by:
1. `prob` descending (highest probability first)
2. `uci` ascending (alphabetical tiebreaker)

### 6.2 Float Precision

All floats are rounded to **6 decimal places** before:
- Storage in the artifact
- Computing the determinism hash

### 6.3 JSON Key Ordering

For `determinismHash` computation, JSON keys are **alphabetically sorted** and serialized with no extra whitespace.

---

## 7. Determinism Hash

The `determinismHash` field contains a SHA-256 hash of the canonical JSON representation of the artifact (excluding the hash field itself).

Format: `sha256:<64-character-lowercase-hex>`

Example: `sha256:a1b2c3d4e5f6...`

This hash enables:
- Reproducibility verification across runs
- Artifact integrity checking
- Deduplication

---

## 8. Context Fields

### 8.1 `context.skillBucket` (Required)

Skill bucket identifier from M06 conditioning. Examples:
- `"lt_800"`
- `"1200_1399"`
- `"gte_1800"`

### 8.2 `context.timeControlBucket` (Optional)

Time control bucket. Examples:
- `"BLITZ"`
- `"RAPID"`
- `"CLASSICAL"`

### 8.3 `context.timePressureBucket` (Optional)

Time pressure bucket. Examples:
- `"NORMAL"`
- `"LOW"`
- `"TROUBLE"`

---

## 9. Policy Fields

### 9.1 `policy.topMoves`

Array of top moves with probabilities. Default: 5 moves (`TOP_K = 5`).

Each move contains:
- `uci`: Move in UCI notation (required)
- `san`: Move in SAN notation (optional)
- `prob`: Probability (0-1, required)

### 9.2 `policy.recommendedMove`

The top recommended move (highest probability). Same structure as move entries.

---

## 10. Outcome Fields

W/D/L probabilities from the conditioned outcome head:

- `pWin`: Win probability (0-1)
- `pDraw`: Draw probability (0-1)
- `pLoss`: Loss probability (0-1)

**Invariant:** `pWin + pDraw + pLoss ≈ 1.0` (within 1e-4 tolerance)

---

## 11. HDI Fields

Human Difficulty Index from M07:

- `value`: HDI scalar (0-1, higher = more difficult)
- `entropy`: Policy entropy component (optional)
- `topGapInverted`: Inverted top gap (optional)
- `legalMovePressure`: Legal move pressure (optional)
- `outcomeSensitivity`: Outcome sensitivity (optional)

---

## 12. Structural Cognition (Optional)

When M11 structural features are available:

- `mobilityDelta`: Change in piece mobility
- `weakSquaresDelta`: Change in weak squares
- `strongSquaresDelta`: Change in strong squares
- `summary`: Brief textual summary

**Note:** This field is optional in v1. If present, `sourceContractVersions.structuralCognitionContract` must be set.

---

## 13. Explanation Hints (M20+ Placeholder)

The `explanationHints` field is reserved for future M20+ functionality:

```json
{
  "explanationHints": [
    { "tag": "mobility_advantage", "weight": 0.8 },
    { "tag": "time_pressure", "weight": 0.3 }
  ]
}
```

In M19, this field is always `null` or omitted. The builder does NOT populate it.

---

## 14. Source Contract Versions

Traceability fields referencing governing contracts:

- `adviceFactsContract`: This contract version (`"v1"`)
- `inputSemanticsContract`: CONTRACT_INPUT_SEMANTICS version (`"v1.0"`)
- `structuralCognitionContract`: StructuralCognitionContract version (if structural cognition present)

---

## 15. Builder Function

The canonical builder function is:

```python
from renacechess.coaching.advice_facts import build_advice_facts_v1

facts = build_advice_facts_v1(inputs)
```

This function:
- Accepts pre-computed signals (no provider orchestration)
- Produces byte-stable output for identical inputs
- Is stateless and side-effect-free

---

## 16. Enforcement

### 16.1 Import Boundary

The `coaching` module is isolated via import-linter:
- Core modules (`contracts`, `eval`, `features`, `models`) cannot import `coaching`
- `coaching` may import `contracts` (for models/schemas)

### 16.2 Schema Validation

All AdviceFactsV1 artifacts must validate against:
- JSON Schema: `advice_facts.v1.schema.json`
- Pydantic: `AdviceFactsV1` model

### 16.3 Determinism Tests

CI must verify that:
- Same inputs → identical output (including hash)
- Float rounding is consistent
- Move ordering is stable

---

## 17. Versioning

This contract is **FROZEN** at v1. Changes require:

1. New schema version (`advice_facts.v2.schema.json`)
2. New Pydantic model (`AdviceFactsV2`)
3. New contract document (`ADVICE_FACTS_CONTRACT_v2.md`)
4. Backward compatibility with v1 consumers

---

## 18. Related Documents

- `ADR-COACHING-001.md` — Coaching truthfulness decision
- `CONTRACT_INPUT_SEMANTICS.md` — Dict input conventions
- `StructuralCognitionContract_v1.md` — M11 feature definitions
- `PERSONALITY_SAFETY_CONTRACT_v1.md` — Phase B safety model

---

**Contract Frozen:** 2026-01-31 (M19)  
**Signature:** RenaceCHESS Governance

