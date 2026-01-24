# M06 Conditioned Evaluation

**Status:** M06 core infrastructure complete, integration pending  
**Version:** M06 Spec v1  
**Date:** 2026-01-24

---

## Overview

M06 introduces **conditioning axes** for skill- and time-stratified evaluation, enabling measurement of policy accuracy and distribution characteristics across different human skill levels, time controls, and time pressure regimes.

This document describes the M06 conditioning framework and its usage.

---

## Conditioning Axes (M06 Spec v1)

### 1. Skill Bucket ID

Deterministic mapping from player rating → bucket ID:

| Bucket ID | Rating Range |
|-----------|--------------|
| `lt_800` | rating < 800 |
| `800_999` | 800 ≤ rating ≤ 999 |
| `1000_1199` | 1000 ≤ rating ≤ 1199 |
| `1200_1399` | 1200 ≤ rating ≤ 1399 |
| `1400_1599` | 1400 ≤ rating ≤ 1599 |
| `1600_1799` | 1600 ≤ rating ≤ 1799 |
| `gte_1800` | rating ≥ 1800 |
| `unknown` | missing/invalid rating |

**Assignment function:** `renacechess.conditioning.buckets.assign_skill_bucket(rating)`

**Spec version:** 1 (frozen for M06)

### 2. Time Control Class

Deterministic classification from PGN `TimeControl` header:

| Class | Estimated Total Seconds |
|-------|------------------------|
| `bullet` | < 180s |
| `blitz` | 180s - 479s |
| `rapid` | 480s - 1499s |
| `classical` | ≥ 1500s |
| `unknown` | parse failure / missing |

**Formula:** `estimatedTotalSeconds = baseSeconds + 40 * incSeconds`

**Example:** `"180+2"` → `180 + 40*2 = 260s` → `blitz`

**Parser function:** `renacechess.conditioning.buckets.parse_time_control(time_control_str)`

**Spec version:** 1 (frozen for M06)

### 3. Time Pressure Bucket

Classification from remaining clock time:

| Bucket | Remaining Time |
|--------|----------------|
| `trouble` | ≤ 10 seconds |
| `low` | ≤ 30 seconds |
| `normal` | ≤ 120 seconds |
| `early` | > 120 seconds |
| `unknown` | no clock data |

**Assignment function:** `renacechess.conditioning.buckets.assign_time_pressure_bucket(remaining_seconds)`

**M06 decision:** Per-move clock data not yet captured. All records use `unknown` for M06. Plumbing implemented for future use.

**Spec version:** 1 (frozen for M06)

---

## Usage

### Python API

```python
from renacechess.conditioning import (
    assign_skill_bucket,
    parse_time_control,
    assign_time_pressure_bucket,
)

# Skill bucket assignment
skill_bucket_id = assign_skill_bucket(1350)  # Returns "1200_1399"

# Time control parsing
tc_class, tc_raw = parse_time_control("300+5")  # Returns ("blitz", "300+5")

# Time pressure assignment (future use)
tp_bucket = assign_time_pressure_bucket(15.0)  # Returns "low"
```

### Backward Compatibility

M06 extends `PositionConditioning` with **optional** fields:

```json
{
  "conditioning": {
    "skillBucket": "1200-1400",  // Legacy (required)
    "timePressureBucket": "NORMAL",  // Legacy (required, accepts M06 lowercase)
    "timeControlClass": "blitz",  // Legacy (optional, accepts M06 values)
    
    // M06-specific (all optional)
    "skillBucketId": "1200_1399",
    "skillBucketSpecVersion": 1,
    "timeControlRaw": "300+5",
    "timeControlSpecVersion": 1,
    "timePressureSpecVersion": 1
  }
}
```

**All existing records remain valid.** M06 fields are additive.

---

## Conditioned Metrics (Eval Report v3)

Eval Report v3 adds stratified metrics:

```json
{
  "schemaVersion": "eval_report.v3",
  "overall": { /* ConditionedMetrics */ },
  "bySkillBucketId": {
    "1200_1399": { /* ConditionedMetrics */ },
    "1400_1599": { /* ConditionedMetrics */ }
  },
  "byTimeControlClass": {
    "blitz": { /* ConditionedMetrics */ },
    "rapid": { /* ConditionedMetrics */ }
  },
  "byTimePressureBucket": {
    "unknown": { /* ConditionedMetrics */ }
  }
}
```

Each `ConditionedMetrics` includes:
- **Accuracy** (top-1, top-K, coverage) — label-only
- **Distribution** (entropy, topGap, legalMovesCount stats) — all records with policy
- **Validity** (illegal rate, unique moves) — all records with policy

---

## What Claims Can Be Made

✅ **Valid claims with M06:**
- "Policy accuracy is X% for skill bucket 1200-1399"
- "Entropy decreases with skill from bucket A to bucket B"
- "Blitz games have higher policy entropy than rapid"

❌ **Invalid claims without proper conditioning:**
- "Policy is human-realistic" (without stratified evidence)
- "Accuracy improves with time" (time pressure = unknown in M06)

---

## Future Extensions

- **M07+:** Per-move clock data capture for true time pressure conditioning
- **M07+:** Player-specific conditioning
- **M07+:** Concept-based conditioning (tactical vs positional positions)

---

**Last Updated:** 2026-01-24  
**Spec Version:** 1 (frozen)

