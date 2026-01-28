# 🔒 RenaceCHESS — PoC Release Manifest

**Release Name:** `poc-v1.0`  
**Project:** RenaceCHESS  
**Status:** **LOCKED / IMMUTABLE**  
**Release Date:** 2026-01-28  
**Locked At Commit:** `282db6aed4bdf75683666bc51e5767be43253a1e`  
**Git Tag:** `poc-v1.0`  
**Protected Branch:** `poc-lock`

---

## 1️⃣ Purpose of This Manifest

This document defines the **authoritative, immutable envelope** of the RenaceCHESS Proof of Concept (PoC).

It exists to ensure that:

* reviewers can evaluate the PoC independently of ongoing development,
* architectural meaning is frozen even as the repository evolves,
* and future work cannot silently redefine what the PoC "was."

> **This is a semantic lock, not a development freeze.**

---

## 2️⃣ What the PoC Proves (Scope Statement)

The RenaceCHESS PoC v1.0 proves that it is possible to build a **human-centered chess intelligence system** that:

1. Predicts **human move distributions** conditioned on skill and time,
2. Predicts **human outcomes** (Win / Draw / Loss) probabilistically,
3. Quantifies **human difficulty** (HDI) in a calibrated, reproducible way,
4. Produces **truthful, structured signals** suitable for LLM grounding,
5. Supports **future cognition layers** without architectural redesign,
6. Maintains **determinism, auditability, and governance discipline** end-to-end.

This PoC does **not** attempt to maximize playing strength or engine-like optimality.

---

## 3️⃣ Included Milestones (Immutable)

This release includes **exactly** the following milestones:

| Milestone | Description | Completion Date |
|-----------|-------------|-----------------|
| M00 | Repository bootstrap, governance skeleton | 2026-01-23 |
| M01 | Deterministic dataset shard builder | 2026-01-23 |
| M02 | Deterministic Lichess ingestion | 2026-01-23 |
| M03 | Deterministic multi-shard dataset assembly | 2026-01-23 |
| M04 | Evaluation harness | 2026-01-24 |
| M05 | Labeled evaluation & accuracy metrics | 2026-01-24 |
| M06 | Skill & time conditioning + frozen eval manifests | 2026-01-24 |
| M07 | Human Difficulty Index (HDI v1) | 2026-01-24 |
| M08 | Learned human move policy baseline | 2026-01-24 |
| M09 | Learned human outcome head (W/D/L) | 2026-01-25 |
| M10 | CI hardening, coverage non-regression enforcement | 2026-01-27 |
| **M11** | **Structural Interpretability Expansion** | **2026-01-28** |

No milestones beyond **M11** are part of PoC v1.0.

---

## 4️⃣ Frozen Artifacts & Contracts

The following artifacts are **frozen and authoritative** for this PoC release:

### 📜 Schemas & Contracts

| Schema | Location | Version |
|--------|----------|---------|
| Dataset Manifest | `src/renacechess/contracts/schemas/v1/dataset_manifest.v2.schema.json` | v2 |
| Ingest Receipt | `src/renacechess/contracts/schemas/v1/ingest_receipt.schema.json` | v1 |
| Evaluation Report | `src/renacechess/contracts/schemas/v1/eval_report.v5.schema.json` | v5 |
| Context Bridge | `src/renacechess/contracts/schemas/v1/context_bridge.v2.schema.json` | v2 |
| Frozen Eval Manifest | `src/renacechess/contracts/schemas/v1/frozen_eval_manifest.v1.schema.json` | v1 |
| Per-Piece Features | `src/renacechess/contracts/schemas/v1/PerPieceFeaturesV1.schema.json` | v1 |
| Square Map Features | `src/renacechess/contracts/schemas/v1/SquareMapFeaturesV1.schema.json` | v1 |

### 📖 Constitutional Contracts

| Contract | Location |
|----------|----------|
| Structural Cognition Contract | `docs/contracts/StructuralCognitionContract_v1.md` |

### 🧠 Semantics Frozen

* Definition of Human Difficulty Index (HDI v1)
* Definition of human move probability and outcome probability
* Definitions of:
  * weak squares (control_diff < 0 AND not pawn-contestable)
  * strong squares (control_diff > 0 AND pawn-contestable)
  * holes (not pawn-contestable AND control_diff < 0)
  * piece-level structural roles (mobility, tension, flags)

Any future change **must** introduce a new version (v2+) and does not retroactively apply to this PoC.

---

## 5️⃣ Training Performed (and Not Performed)

### ✅ Training Included

* Local training of:
  * human move policy baseline (M08)
  * human outcome head (M09)
* Fixed seeds for reproducibility
* Frozen eval exclusion (training never touches frozen eval sets)
* Deterministic evaluation

### ❌ Explicitly Not Included

* No reinforcement learning
* No online / continual learning
* No personality-conditioned training
* No hyperparameter sweeps
* No engine-strength optimization

The PoC demonstrates **learnability and calibration**, not final performance.

---

## 6️⃣ Determinism & Reproducibility Guarantees

For PoC v1.0:

* All evaluations are deterministic
* Frozen eval sets are never used for training
* CI enforces:
  * ≥90% coverage
  * overlap-set non-regression
* Structural feature extraction is a pure function of position (FEN)

Reproducing this release at the locked commit must produce **identical outputs** for identical inputs.

---

## 7️⃣ Field Testing & Data Generation

The PoC **may be field tested** as a measurement and analysis instrument.

It can generate:

* human move probabilities
* human outcome probabilities
* HDI values
* per-piece structural features
* square-level weak/strong/hole maps
* Context Bridge v2 payloads

However:

* The PoC does **not** learn from field data
* Field data is **not ingested** back into the model
* Any feedback loop or retraining is out of scope

Using field data for learning requires a **post-PoC milestone**.

---

## 8️⃣ What This PoC Is Not

This release is **not**:

* a strongest-move chess engine
* a reinforcement-learning agent
* a personality-driven bot
* an online-learning system
* a production deployment

It is a **truthful, human-grounded cognition substrate**.

---

## 9️⃣ Development After PoC Lock

After this release:

* Active development continues on `main`
* New work must:
  * version schemas/contracts explicitly
  * reference new milestones (M12+)
* This PoC remains reviewable, reproducible, and unchanged

A protected branch (`poc-lock`) and tag (`poc-v1.0`) point to this release.

---

## 🔟 Verification Instructions

To verify this PoC release:

```bash
# Clone and checkout the locked commit
git clone https://github.com/m-cahill/RenaceCHESS.git
cd RenaceCHESS
git checkout poc-v1.0

# Verify the commit SHA
git rev-parse HEAD
# Expected: 282db6aed4bdf75683666bc51e5767be43253a1e

# Install dependencies
pip install -e ".[dev]"

# Run full test suite
pytest --cov=renacechess --cov-fail-under=90

# All tests should pass with ≥90% coverage
```

---

## 🔏 Final Declaration

> **RenaceCHESS PoC v1.0 is hereby locked.**

Its meaning, semantics, and evaluation guarantees are frozen at the commit referenced above.
All future work builds *on top of* this foundation and does not redefine it.

---

**Signed:** AI Agent (Cursor)  
**Date:** 2026-01-28  
**Witnessed by:** Project Governance

