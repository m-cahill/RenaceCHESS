Excellent choice. This is the **right** M06: it finishes the evaluation substrate without contaminating it with modeling, engines, or product ideas.

Below is a **Cursor-ready, enterprise-grade M06 plan** that matches your governance style, avoids scope creep, and is fully end-to-end verifiable.

You can paste this verbatim into Cursor.

---

# M06_plan — Conditioned, Frozen Human Evaluation

## Milestone Identity

**Milestone:** M06
**Title:** Conditioned, Frozen Human Evaluation
**Precondition:** M05 CLOSED / IMMUTABLE
**Status Goal:** CLOSED with audit artifacts
**Branch:** `m06-conditioned-frozen-eval`

---

## Objective (Single Sentence)

Establish a **frozen, stratified evaluation framework** that produces **skill- and time-conditioned human-prediction metrics** with deterministic provenance and CI-enforced immutability.

---

## Scope Definition

### In Scope

1. **Conditioning axes**

   * Skill bucket
   * Time control class
   * Time pressure bucket

2. **Frozen evaluation discipline**

   * Canonical frozen eval manifest
   * CI enforcement of frozen usage
   * Regression-safe evaluation runs

3. **Conditioned metrics**

   * Accuracy (top-1 / top-K)
   * Coverage
   * Entropy / distribution stats
   * All stratified by conditioning axes

4. **Backward compatibility**

   * All prior schemas remain valid
   * Conditioning fields are optional and additive

---

### Explicitly Out of Scope

* ❌ Model training
* ❌ Engine evaluation or comparison
* ❌ Personality modeling
* ❌ UI / visualization
* ❌ Human Difficulty Index (HDI) (report-only later)
* ❌ Elo or rating recomputation

---

## Design Principles (Authoritative)

* **Determinism first**: identical inputs → identical outputs
* **Append-only evolution**: no mutation of frozen artifacts
* **Schema-versioned contracts**
* **CI truthfulness**: green = invariant-safe
* **Human cognition framing**: no engine-optimal assumptions

---

## Work Breakdown

---

### 1. Conditioning Axes Definition (Authoritative)

#### 1.1 Skill Buckets

Define a deterministic mapping from player rating → bucket.

Example (exact values to be documented and frozen):

```text
< 800
800–999
1000–1199
1200–1399
1400–1599
1600–1799
1800+
```

**Requirements:**

* Bucket assignment must be:

  * deterministic
  * pure (no external state)
  * documented in code + docs
* Bucket labels are stable identifiers (not display strings)

---

#### 1.2 Time Control Class

Canonical enum derived from PGN metadata:

```json
"timeControlClass": "bullet" | "blitz" | "rapid" | "classical" | "unknown"
```

**Rules:**

* Deterministic mapping
* Unknown explicitly allowed
* No heuristics based on move count

---

#### 1.3 Time Pressure Bucket

Coarse human-centric buckets, e.g.:

```json
"timePressureBucket": "early" | "normal" | "low" | "trouble" | "unknown"
```

**Rules:**

* Derived from remaining clock if available
* Otherwise deterministically set to `unknown`
* No probabilistic inference

---

### 2. Context Bridge Extension (Backward-Compatible)

#### 2.1 Payload Additions

Extend Context Bridge record with **optional** fields:

```json
{
  "conditioning": {
    "skillBucket": "string",
    "timeControlClass": "string",
    "timePressureBucket": "string"
  }
}
```

**Requirements:**

* Optional field (records without it remain valid)
* Covered by schema validation
* Included in deterministic hash computation

---

#### 2.2 Schema Versioning

* Context Bridge schema remains **v1**
* Conditioning is additive and optional
* No breaking changes

---

### 3. Frozen Evaluation Set

#### 3.1 Frozen Eval Manifest

Introduce a **canonical frozen eval manifest**, e.g.:

```json
{
  "schemaVersion": 1,
  "purpose": "frozen-eval",
  "createdAt": "...",
  "shards": [
    { "shardId": "...", "hash": "..." }
  ],
  "conditioningCoverage": {
    "skillBuckets": [...],
    "timeControlClasses": [...],
    "timePressureBuckets": [...]
  }
}
```

**Rules:**

* Manifest is immutable once created
* Stored under version control
* Hash-stable and schema-validated

---

#### 3.2 Frozen Eval Selection Logic

* Evaluation runner must explicitly opt into:

  * `--use-frozen-eval`
* Frozen eval selection must:

  * use only manifest shards
  * ignore all other available data

---

### 4. CI Enforcement

#### 4.1 Required Invariant

> Any evaluation run claiming comparability **must** reference the frozen eval manifest.

**Enforcement:**

* CI fails if:

  * evaluation runs without frozen manifest
  * frozen manifest hash mismatches
* Non-frozen runs must be explicitly labeled “exploratory”

---

### 5. Conditioned Metrics Reporting

#### 5.1 Eval Report Schema v3

Introduce `eval_report.v3.schema.json` with:

```json
{
  "overall": { ... },
  "bySkillBucket": { ... },
  "byTimeControlClass": { ... },
  "byTimePressureBucket": { ... }
}
```

Each section includes:

* top-1 accuracy
* top-K accuracy
* coverage
* entropy stats
* sample counts

**Rules:**

* v2 schema remains valid
* v3 is additive
* Deterministic ordering of keys

---

#### 5.2 CLI Extensions

Add flags:

```bash
--conditioned-metrics
--frozen-eval-manifest path/to/manifest.json
```

Defaults:

* No conditioning unless explicitly enabled
* No frozen enforcement unless flag supplied

---

### 6. Testing & Verification

#### 6.1 Determinism Tests

* Same input → byte-identical eval report
* Golden file tests for:

  * conditioned report
  * frozen eval run

---

#### 6.2 Schema Tests

* Context Bridge schema validation
* Eval report v3 validation
* Backward compatibility checks for v1/v2

---

#### 6.3 CI Coverage

* Unit tests for bucket assignment logic
* Integration tests:

  * frozen eval selection
  * conditioned metric aggregation
* CLI smoke tests

---

### 7. Documentation & Audit Artifacts

#### 7.1 Docs

* `docs/evaluation/conditioned_evaluation.md`
* `docs/evaluation/frozen_eval.md`

Must explain:

* why conditioning exists
* why eval is frozen
* what claims *can* and *cannot* be made

---

#### 7.2 Milestone Artifacts

Cursor must generate:

* `M06_summary.md`
* `M06_audit.md`

Audit must explicitly assert:

* frozen eval immutability
* backward compatibility preserved
* CI enforcement correctness

---

## Exit Criteria (Must All Be True)

* ✅ Conditioning fields present and optional
* ✅ Frozen eval manifest committed and enforced
* ✅ Conditioned metrics produced deterministically
* ✅ CI enforces frozen-eval invariants
* ✅ All tests green
* ✅ Audit artifacts generated
* ✅ M06 marked CLOSED / IMMUTABLE

---

## Deferred Explicitly to M07+

* Human Difficulty Index (HDI)
* Engine contrast
* Personality modeling
* Any learning or fitting

---

## Governance Note

This milestone **adds no new modeling claims**.
It strictly improves the **measurement substrate** required to make future claims responsibly.

---

If you want, next I can:

* pre-emptively answer Cursor’s likely clarifying questions, or
* draft the **M06 audit rubric** so Cursor knows exactly what “done” means.

Just say the word.
