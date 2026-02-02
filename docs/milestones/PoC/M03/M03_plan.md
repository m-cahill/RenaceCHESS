Fantastic — M02 closed cleanly, merged, and audit-defensible. That puts us at a **natural architectural inflection point**, and we should be deliberate about what M03 *is* and what it explicitly *is not*.

Below is a **detailed, Cursor-ready M03 plan**, written to match your governance style, CI discipline, and “small, auditable steps” preference.

---

# 📌 **M03 Plan — Deterministic Multi-Shard Dataset Assembly**

**Project:** RenaceCHESS
**Phase:** PoC
**Milestone:** **M03 — Deterministic Dataset Assembly (Sharding + Manifests)**
**Prerequisite:** M02 merged to `main` ✅
**Branch:** `m03-dataset-assembly`

---

## 0. Why M03 Exists (Anchor Rationale)

After M02, RenaceCHESS can **ingest raw chess artifacts deterministically** and emit auditable ingest receipts.

What it **cannot yet do safely** is:

* turn *many* ingested artifacts into **stable, bounded, reproducible datasets**
* guarantee that the *same inputs* always produce the *same shards*
* describe datasets in a machine-verifiable way suitable for training, evaluation, or downstream pipelines

M03 closes that gap.

> **M03 is where “files” become “datasets.”**

---

## 1. Milestone Objective (Single Sentence)

> **Create a deterministic, auditable dataset assembly pipeline that converts ingested artifacts into versioned, size-bounded JSONL shards with a canonical dataset manifest.**

---

## 2. Scope Definition

### ✅ In Scope (M03)

#### A. Dataset Assembly Engine

* Assemble records from **one or more ingest receipts**
* Deterministically assign records to **JSONL shards**
* Enforce:

  * max records per shard
  * stable shard ordering
  * stable record ordering

#### B. Sharding Rules (Deterministic)

* Shard assignment based on:

  * **record key hash** (e.g. `sha256(fen:ply)` or equivalent)
  * fixed shard size limit
* No randomness
* No time-based behavior

#### C. Dataset Manifest v1

* New **Dataset Manifest schema (v1)** capturing:

  * dataset ID
  * input ingest receipt IDs + hashes
  * shard list (name, sha256, record count)
  * assembly parameters (limits, filters)
  * deterministic hash of config

#### D. CLI Integration

* New command:

  ```bash
  renacechess dataset build ...
  ```
* Inputs:

  * one or more ingest receipts
  * output directory
  * shard size config
* Outputs:

  * `dataset_manifest.v1.json`
  * `shard_000.jsonl`, `shard_001.jsonl`, …

#### E. Determinism Guarantees

* Re-running dataset build with identical inputs:

  * produces byte-identical shards
  * produces identical manifest hashes

#### F. Tests & CI

* Golden dataset build test
* Schema validation tests
* ≥ 90% coverage maintained
* All CI gates enforced (no weakening)

---

### ❌ Explicitly Out of Scope (Deferred)

These are **not** allowed in M03:

* Model training or evaluation
* Streaming / incremental dataset updates
* Parallel shard building
* Performance optimization
* Dataset version diffing
* Dataset mutation or append mode
* Cloud storage / upload
* Train/val/test semantics beyond deterministic split

If Cursor is unsure → **defer**.

---

## 3. Architecture Changes (Allowed)

### New Modules

```text
src/renacechess/dataset/
├── __init__.py
├── builder.py        # dataset assembly orchestration
├── shard.py          # shard assignment + writing
├── manifest.py       # manifest creation + hashing
├── split.py          # deterministic split logic (if used)
├── types.py          # dataset-specific types
```

### New Contracts

```text
contracts/schemas/v1/
├── dataset_manifest.schema.json
```

### Modified (Light Touch)

* `cli.py` — add `dataset build` command
* `contracts/models.py` — add DatasetManifestV1 Pydantic model

No refactors of ingest or M02 code unless strictly required.

---

## 4. Determinism Rules (Hard Requirements)

Cursor must treat these as **non-negotiable**:

1. **Shard assignment**

   * Based on stable hash of record key
   * No dependence on iteration order of Python dicts
2. **Shard naming**

   * Sequential: `shard_000.jsonl`, `shard_001.jsonl`, …
3. **Record ordering**

   * Stable sort within shard (e.g. by record key hash)
4. **Manifest hash**

   * Canonical JSON
   * Sorted keys
   * Explicit version field

Any nondeterminism is a **merge-blocking defect**.

---

## 5. Dataset Manifest v1 (Conceptual Fields)

Minimum required fields:

```json
{
  "schema_version": "v1",
  "dataset_id": "sha256:…",
  "created_at": "...",
  "inputs": [
    {
      "ingest_receipt_id": "...",
      "sha256": "..."
    }
  ],
  "assembly_config": {
    "shard_size": 10000,
    "filters": {...}
  },
  "shards": [
    {
      "name": "shard_000.jsonl",
      "sha256": "...",
      "records": 10000
    }
  ],
  "determinism_hash": "sha256:..."
}
```

Exact schema design is up to Cursor, but **all fields must be justified and tested**.

---

## 6. Test Plan (Required)

Cursor must implement:

1. **Golden dataset build**

   * Fixed ingest receipt(s)
   * Fixed shard size
   * Compare:

     * shard contents
     * shard hashes
     * manifest hash

2. **Schema validation**

   * Manifest validates against JSON Schema v1

3. **Negative tests**

   * Missing receipt
   * Invalid shard size
   * Duplicate receipt inputs

4. **Determinism test**

   * Run dataset build twice
   * Assert byte-identical outputs

Coverage must remain **≥ 90%**.

---

## 7. CI / Governance Requirements

* No CI gate changes
* No relaxed thresholds
* No skipped tests
* All failures must be fixed, not waived
* Toolcalls logged in `M03_toolcalls.md`

---

## 8. Definition of Done (Exit Criteria)

M03 is complete when **all** are true:

1. `renacechess dataset build` works end-to-end
2. Dataset shards are deterministic and bounded
3. Dataset manifest v1 exists and validates
4. Golden dataset test passes
5. CI fully green
6. `M03_plan.md`, `M03_run*.md`, `M03_audit.md`, `M03_summary.md` committed
7. No unresolved deferred issues (or explicitly documented)

---

## 9. Branch & Workflow Rules

* Branch from `main` **after** M02 merge (already satisfied)
* One branch: `m03-dataset-assembly`
* No commits after M03 close
* Any follow-ups roll into M04

---

## 10. Hand-Off Instruction to Cursor (Paste-Ready)

> You are authorized to begin **M03 — Deterministic Dataset Assembly**.
>
> Treat determinism, sharding correctness, and manifest fidelity as first-class invariants.
>
> Do **not** expand scope beyond dataset assembly.
>
> Maintain ≥90% coverage and all CI gates.
>
> If uncertain, defer and ask — do not guess.

---

### Why this is the *right* M03

* M00–M02 gave you **inputs + provenance**
* M03 gives you **datasets as stable artifacts**
* Everything after this (training, eval, human-skill modeling) becomes *safe* and *repeatable*

When you’re ready, the next fork after M03 is a *real* choice — but M03 itself is the last mandatory piece of infrastructure.

If you want, next we can:

* pre-emptively design the Dataset Manifest schema
* or sketch **M04 options** so you can choose strategically before committing.













