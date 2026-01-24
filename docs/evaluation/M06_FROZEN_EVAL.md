# M06 Frozen Evaluation

**Status:** M06 core infrastructure complete, CLI integration pending  
**Version:** Frozen Eval Manifest v1  
**Date:** 2026-01-24

---

## Overview

M06 introduces **frozen evaluation sets** — immutable, stratified subsets of datasets used for regression-safe policy evaluation and comparability across experiments.

This document describes frozen eval manifests, generation, and CI enforcement.

---

## Why Frozen Eval?

### Problem

Without frozen eval:
- Different experiments use different subsets → **not comparable**
- Dataset changes break historical baselines → **no regression detection**
- Cherry-picking evaluation data → **optimistic bias**

### Solution

Frozen eval manifest:
- **Immutable:** Hash-stable, version-controlled
- **Stratified:** Representative across skill/time axes
- **Auditable:** Provenance to source dataset manifest v2

---

## Frozen Eval Manifest v1

### Schema

```json
{
  "schemaVersion": 1,
  "createdAt": "2024-01-01T12:00:00Z",
  "sourceManifestRef": {
    "datasetDigest": "abc...123",  // Source dataset manifest v2 hash
    "manifestPath": "/path/to/source/manifest.json"
  },
  "records": [
    {
      "recordKey": "fen:abc",
      "shardId": "shard_000",
      "shardHash": "def...456",
      "skillBucketId": "1200_1399",  // M06 conditioning metadata
      "timeControlClass": "blitz",
      "timePressureBucket": "unknown"
    }
  ],
  "stratificationTargets": {
    "totalRecords": 10000,
    "minPerSkillBucket": 500
  },
  "countsBySkillBucketId": { "1200_1399": 1500, ... },
  "countsByTimeControlClass": { "blitz": 5000, ... },
  "countsByTimePressureBucket": { "unknown": 10000 },
  "coverageShortfalls": [
    {
      "axis": "skillBucketId",
      "value": "lt_800",
      "target": 500,
      "actual": 150
    }
  ],
  "manifestHash": "xyz...789"  // Hash of entire manifest
}
```

### Key Fields

- **`sourceManifestRef`:** Links to source dataset manifest v2
- **`records`:** Array of record references with conditioning metadata
- **`stratificationTargets`:** Target counts for selection
- **`counts*`:** Actual counts by conditioning axis
- **`coverageShortfalls`:** Where targets not met
- **`manifestHash`:** Immutability guarantee

---

## Generating Frozen Eval Manifests

### Python API

```python
from renacechess.frozen_eval import generate_frozen_eval_manifest, write_frozen_eval_manifest
from pathlib import Path

# Generate frozen manifest
manifest = generate_frozen_eval_manifest(
    source_manifest_path=Path("data/manifests/dataset_v2.json"),
    target_total_records=10000,  # Default
    min_per_skill_bucket=500,    # Default
)

# Write to disk
write_frozen_eval_manifest(
    manifest,
    output_path=Path("data/frozen_eval/manifest.v1.json")
)
```

### CLI (Pending M06 Completion)

```bash
renacechess eval generate-frozen \
  --dataset-manifest data/manifests/dataset_v2.json \
  --out data/frozen_eval/manifest.v1.json \
  --target-records 10000 \
  --min-per-skill-bucket 500
```

### Selection Logic

1. **Extract labeled records** (with `chosenMove`) from source dataset
2. **Group by skill bucket** for stratification
3. **Allocate proportionally** while respecting minimums
4. **Select deterministically** (sorted by `recordKey`, first N)
5. **Compute counts** by all conditioning axes
6. **Track shortfalls** where minimums not met
7. **Hash manifest** for immutability

**Minimum total labeled records:** 1,000 (fail generation if not met)

---

## CI Enforcement (Pending M06 Completion)

### Invariant

> Any evaluation run claiming comparability **must** reference the frozen eval manifest.

### Rules

- ❌ Fail if evaluation runs without frozen manifest AND claims comparability
- ❌ Fail if frozen manifest hash mismatches source
- ✅ Allow exploratory runs (labeled "exploratory") without frozen manifest
- ✅ Frozen manifest is version-controlled and immutable

### Implementation (Pending)

```yaml
# .github/workflows/ci.yml (example)
- name: Validate Frozen Eval Usage
  run: |
    # Check that all eval reports reference frozen manifest
    # Validate frozen manifest hash matches committed version
```

---

## Canonical Frozen Manifest Location

**Path:** `data/frozen_eval/manifest.v1.json`

This manifest:
- ✅ Committed to version control
- ✅ Immutable (hash-stable)
- ✅ Referenced by all comparable evaluation runs
- ✅ Regenerated only when source dataset fundamentally changes

---

## What Claims Can Be Made

✅ **Valid claims with frozen eval:**
- "Policy A improved by X% over Policy B on frozen eval set"
- "Accuracy regressed from version N to version N+1"
- "Top-K coverage is stable across experiments"

❌ **Invalid claims without frozen eval:**
- "Policy is better" (on what data?)
- "No regression detected" (compared to what baseline on what data?)

---

## Coverage Shortfalls

If dataset has insufficient records for stratification targets:

1. **Document shortfall** in `coverageShortfalls` array
2. **Still generate manifest** (do not fail unless total < 1,000)
3. **Report shortfall** in audit documents
4. **Consider** re-stratification or lower minimums

---

## Future Extensions

- **M07+:** Multiple frozen sets (different skill distributions, time controls)
- **M07+:** Frozen set versioning (v1, v2, etc.)
- **M07+:** Automated frozen set refresh (e.g., quarterly)

---

**Last Updated:** 2026-01-24  
**Spec Version:** 1 (frozen)  
**Canonical Location:** `data/frozen_eval/manifest.v1.json`

