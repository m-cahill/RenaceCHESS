Excellent — M29 is **cleanly closed**, the audit posture is strong, and Phase E is progressing exactly as designed.
Let’s move on to **M30**.

Below is a **Cursor-ready, enterprise-grade milestone plan** you can hand off directly.

---

# **M30_plan — FROZEN-EVAL-SCALESET-001**

**Phase:** Phase E — Scale, Proof & Release
**Milestone ID:** M30
**Title:** Frozen Evaluation Scale Set (Deterministic, Release-Grade)
**Status:** Planned
**Prerequisite:** M29 (GPU-BENCHMARKING-001) — **CLOSED** 
**CI Impact:** Limited (schema + determinism validation only)

---

## 1. Milestone Intent

M30 establishes a **release-grade, deterministic frozen evaluation set** large enough to support:

* statistically meaningful calibration metrics (ECE, Brier, NLL),
* meaningful pre/post-training comparisons,
* governed recalibration evaluation (Phase D artifacts),
* and external proof packs (M33).

This milestone **does not train models**.
It defines and freezes **what future evaluations will be measured against**.

---

## 2. Problem Being Solved

Current state:

* Only a **small v1 frozen eval fixture** exists (≈70 records).
* Too small for:

  * stable calibration curves,
  * per-bucket confidence analysis,
  * post-training deltas.

M30 answers:

> **“What is the largest evaluation set we can freeze now that is still deterministic, auditable, and feasible to run repeatedly?”**

---

## 3. Explicit Non-Goals (Hard Constraints)

M30 does **not**:

* introduce new data ingestion pipelines,
* download or curate new PGN sources,
* perform training or fine-tuning,
* change Phase D calibration or gating logic,
* alter runtime behavior.

If no production dataset exists yet, M30 works with **controlled, deterministic subsets** derived from available ingestion artifacts or fixtures.

---

## 4. Scope of Work

### 4.1 Frozen Eval Set Definition

M30 will define **Frozen Eval Set v2**, characterized by:

* **Deterministic membership**
* **Immutable manifest**
* **Explicit provenance**
* **Stable ordering**
* **Re-runnable at any time**

The set must be:

* large enough to reduce metric noise,
* small enough to run repeatedly in CI / local eval.

---

### 4.2 Target Scale (Guidance, Not Hard Requirement)

Using conservative M29 throughput as baseline:

| Target Size           | Rationale                            |
| --------------------- | ------------------------------------ |
| **5k–10k positions**  | Minimum viable calibration stability |
| **20k–30k positions** | Preferred (if feasible)              |
| **>50k**              | Only if runtime cost is acceptable   |

Cursor should surface tradeoffs, not guess.

---

### 4.3 Manifest & Artifacts

M30 must produce:

1. **`FrozenEvalManifestV2`**

   * schema-validated
   * includes `createdAt`, `source`, `selectionStrategy`, `hash`

2. **Shard descriptors (if applicable)**

   * deterministic shardRefs
   * explicit counts

3. **Provenance metadata**

   * upstream dataset or fixture reference
   * selection logic (e.g., stratified by Elo bucket)

---

## 5. Determinism & Governance Requirements

### 5.1 Determinism Guarantees

* Fixed random seeds
* Canonical ordering
* Content hash stored in manifest
* Repeat generation must produce byte-identical results

### 5.2 CI Posture

CI should:

* validate schema correctness,
* validate determinism hashes,
* validate manifest immutability.

CI should **not**:

* regenerate the dataset,
* depend on external data,
* perform heavy evaluation runs.

---

## 6. Deliverables

### Required Artifacts

| Artifact                                    | Purpose                       |
| ------------------------------------------- | ----------------------------- |
| `FrozenEvalManifestV2`                      | Authoritative eval definition |
| `EvalSetProvenanceV1`                       | Data lineage                  |
| `docs/milestones/PhaseE/M30/M30_summary.md` | Human-readable summary        |
| `docs/milestones/PhaseE/M30/M30_audit.md`   | Audit verdict                 |

---

## 7. Exit Criteria (Binary)

M30 is **complete** when:

* ✅ Frozen eval set size is explicitly declared
* ✅ Manifest validates against v2 schema
* ✅ Determinism hash is recorded and tested
* ✅ CI validates schema + immutability
* ✅ Audit explicitly approves use for M31/M32

---

## 8. Risks & Guardrails

### Known Risks

* Dataset may still be provisional (no production ingest yet)
* Eval size tradeoff between rigor and runtime

### Guardrails

* Any provisional nature must be **explicitly documented**
* No “temporary” eval sets without audit notation
* If scale is insufficient, that fact must be recorded — not hidden

---

## 9. Expected Cursor Clarifying Questions

Cursor is expected to ask:

1. Target eval size preference (5k vs 20k vs other)
2. Whether to stratify by Elo bucket
3. Whether to reuse v1 frozen eval as a subset
4. Whether to shard or keep monolithic
5. Whether CI should run a tiny smoke-eval

These are normal and expected.

---

## 10. What This Unlocks

Completion of M30 unlocks:

* **M31** — Full training run (evaluated against frozen set)
* **M32** — Post-train evaluation + recalibration comparison
* **M33** — External proof pack with stable metrics

---

## Summary (One-Line)

> **M30 freezes the yardstick.**
> No training, no tuning — just a deterministic, auditable evaluation set that everything else in Phase E will be measured against.

---

If you want, next we can:

* pre-answer Cursor’s likely clarifying questions,
* decide a **default target eval size** now,
* or draft the **M30 audit verdict template** in advance.

You’re exactly on the critical path now — and it’s a good one.
