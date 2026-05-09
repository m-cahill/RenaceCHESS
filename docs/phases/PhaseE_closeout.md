# **Phase E Closeout — Scale Proof, Training Run, Release Lock**

**Project:** RenaceCHESS  
**Phase:** E — Scale Proof, Training Run, Release Lock  
**Status:** ✅ **CLOSED**  
**Milestones:** M29–M34  
**Closeout Date:** 2026-02-03  

---

## 1. Phase E Purpose (Restated)

Phase E was chartered to answer a single, critical question:

> **Can we execute a full training run, evaluate it at scale, package it for external verification, and lock it as an immutable research release?**

This phase explicitly rejected:

* ad-hoc training runs,
* unverified evaluation claims,
* undocumented limitations,
* unfrozen contracts.

Instead, Phase E treated **release as a governed process**, not a milestone marker.

---

## 2. What Phase E Built (End-to-End)

Phase E delivered a **complete, auditable research release**, from hardware validation to immutable contract lock, without weakening any prior guarantees.

### 2.1 Hardware Validation (M29)

M29 established RTX 5090 Blackwell compatibility:

* GPU detection and VRAM validation
* Training loop execution (synthetic benchmark)
* Memory headroom verification (no OOM)
* Benchmark infrastructure for time estimation

**Key invariant:** Hardware is validated before production training.

---

### 2.2 Frozen Evaluation Set (M30)

**FrozenEvalManifestV2** established release-grade evaluation:

* 10,000 synthetic positions (chess-valid, not random)
* 7 skill buckets with minimum 1,000 positions each
* Deterministic generation (fixed seed, reproducible)
* Hash-verified manifest and provenance

**Key invariant:** Evaluation set is immutable and verifiable.

---

### 2.3 Full Training Run (M31)

**TrainingConfigLockV1** and **TrainingRunReportV1** enabled governed training:

* Immutable configuration lock (code → data → config hash chain)
* Full training execution (10 epochs, policy + outcome heads)
* Reproducible training report with checkpoint references
* Causal separation from evaluation data

**Key invariant:** Training is locked before execution; results are canonical.

---

### 2.4 Post-Train Evaluation (M32)

**PostTrainEvalReportV1** measured training impact:

* 10,000-position evaluation (100% of frozen eval v2)
* Baseline comparison with delta metrics
* No training/eval overlap verified
* Honest reporting of degraded metrics (expected due to narrow effective training regime; locked `moveVocabSize` in `TrainingConfigLockV1` is 4096 — see proof pack `config_lock.json`)

**Key invariant:** Evaluation is honest; limitations are explicit.

---

### 2.5 External Proof Pack (M33)

**ExternalProofPackV1** enabled independent verification:

* Self-contained proof bundle (`proof_pack_v1/`)
* Hash-chained artifacts from M30-M32
* External verification without codebase trust
* Limitations explicitly documented

**Key invariant:** External auditors can verify claims without trusting the codebase.

---

### 2.6 Release Lock (M34)

**ContractRegistryV1** and CI release gates enforced immutability:

* 33 v1 contracts frozen with schema hashes
* CI gates prevent v1 contract changes
* Dependency freeze enforcement
* Proof pack verification in CI

**Key invariant:** v1 contracts are immutable; future changes require v2+ versioning.

---

## 3. Phase E Exit Criteria (All Met)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| M29–M34 closed | ✅ | All 6 milestones completed |
| CI green with release gates | ✅ | 3 release gates added and passing |
| v1 tag exists | ✅ | `v1.0.0-renacechess` tag created |
| Contracts frozen | ✅ | ContractRegistryV1 with 33 contracts |
| Proof pack built & verified | ✅ | `proof_pack_v1/` with hash verification |
| Phase E closeout written | ✅ | This document |
| No open deferred issues | ✅ | Registry clean |

**Phase E Status:** ✅ **CLOSED**

---

## 4. What Phase E Proved

Phase E may claim **only**:

1. **Pipeline Integrity**
   Training → evaluation → reporting is end-to-end consistent.

2. **Contract Discipline**
   Schema-first design survived real execution.

3. **Scientific Honesty**
   Degraded results are reported, not hidden or reframed.

4. **Reproducibility**
   All artifacts are hash-chained and replayable.

5. **Release Immutability**
   v1 contracts are frozen and cannot drift.

It does **not** claim:
* Production readiness
* Commercial viability
* Performance superiority
* Feature completeness

---

## 5. What Phase E Did Not Prove

### Playing Strength
- Policy head locked with **`moveVocabSize`: 4096**; synthetic M31 data exercised a small opening set (often summarized as ~8 UCI moves), so **effective** training diversity was narrow
- Model specialized away from general human move distributions on frozen eval
- Metrics degraded compared to baseline (expected)

### Full-Vocab Performance
- Production training will use full move vocabulary
- v1 training is proof-of-concept scope

### Production Readiness
- Research system, not production
- No deployment tooling
- No operational monitoring

---

## 6. Known Limitations (Explicitly Documented)

### Training Vocabulary
M31 policy training records **`moveVocabSize`: 4096** in **`TrainingConfigLockV1`**. The executed synthetic dataset emphasized a **small opening move set** (often summarized as eight UCI moves for readability), so the effective training distribution remains narrow. This is **by design** for proof-of-concept scope.

**Impact:** Trained model shows "degraded" metrics because:
- Baseline has uniform probability over the evaluation vocabulary, occasionally matching by chance
- Trained model concentrates mass on a regime that mismatches much of frozen eval

**Mitigation:** Production training will use full move vocabulary and richer data.

### Synthetic Evaluation Set
Frozen eval v2 is **synthetic** (algorithmically generated, not from real games).

**Impact:** Metrics are for **relative evaluation and calibration stability**, not absolute strength claims.

**Mitigation:** This is intentional — synthetic set enables deterministic, reproducible evaluation.

---

## 7. Governance Outcomes

**What is now provably true that was not true before:**

1. ✅ **Training is reproducible** — Config lock + run report enable replay
2. ✅ **Evaluation is honest** — Limitations explicitly documented
3. ✅ **Contracts are immutable** — v1 contracts frozen with CI enforcement
4. ✅ **External verification possible** — Proof pack enables independent audit
5. ✅ **Release is governed** — CI gates prevent contract drift

---

## 8. Phase E Artifacts

### Contract Registry
- **Location:** `contracts/CONTRACT_REGISTRY_v1.json`
- **Contracts:** 33 v1 contracts with schema hashes
- **Status:** Frozen (CI-enforced)

### Proof Pack
- **Location:** `proof_pack_v1/`
- **Manifest:** `proof_pack_v1/proof_pack_manifest.json`
- **Determinism Hash:** `sha256:6a69e1f801ca1c03d3aedcc2d8bb6ea86f87eb38e8e6322d9cea477ff398ca2f`

### Training Artifacts
- **Config Lock:** `artifacts/m31_training_run/config_lock.json`
- **Run Report:** `artifacts/m31_training_run/training_run_report.json`

### Evaluation Artifacts
- **Post-Train Eval:** `artifacts/m32_post_train_eval/post_train_eval_report.json`
- **Frozen Eval v2:** `data/frozen_eval_v2/manifest.json`

---

## 9. CI Release Gates

Three release-blocking CI jobs enforce immutability:

1. **`release-dependency-freeze`** — Blocks dependency changes
2. **`release-contract-freeze`** — Validates registry and blocks v1 schema changes
3. **`release-proof-pack-verification`** — Verifies proof pack integrity

These gates ensure v1 contracts remain frozen and verifiable.

---

## 10. Phase E Milestones Summary

| Milestone | Objective | Status |
|-----------|-----------|--------|
| M29 | GPU Benchmarking (RTX 5090 validation) | ✅ Closed |
| M30 | Frozen Eval v2 (10k synthetic positions) | ✅ Closed |
| M31 | Full Training Run (executed) | ✅ Closed |
| M32 | Post-Train Evaluation (10k positions) | ✅ Closed |
| M33 | External Proof Pack (self-contained bundle) | ✅ Closed |
| M34 | Release Lock (contract freeze, CI gates) | ✅ Closed |

**All milestones completed. Phase E closed.**

---

## 11. Future Work (Post-v1)

After v1.0.0:

- **v1.1+** — Any future changes require explicit v2+ versioning
- **Contract evolution** — New schemas must be v2+ (v1 frozen)
- **Feature additions** — Must not break v1 contracts
- **Production training** — Full move vocabulary, real data pipeline

This release establishes the **immutable baseline** for all future work.

---

## 12. Phase E Verdict

> **Phase E is CLOSED.**
>
> This phase delivered a complete, auditable research release with:
> - Full training run execution
> - Scale evaluation (10k positions)
> - External proof pack for independent verification
> - Immutable contract lock with CI enforcement
>
> All claims are verifiable. All limitations are explicit. All artifacts are hash-chained.
>
> **This makes future dishonesty impossible.**

---

**Phase E Closeout Complete.**  
**RenaceCHESS v1.0.0 is locked and immutable.**

