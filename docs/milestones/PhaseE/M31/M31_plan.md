Perfect. With **M30 fully closed and merged**, we are now in the cleanest possible position to begin **M31 — FULL-TRAINING-RUN-001**.

Below is a **Cursor-ready, enterprise-grade M31 plan**, aligned with everything proven in M29–M30 and explicitly grounded in the frozen eval v2 artifacts you just closed out  .

---

# **M31_plan — FULL-TRAINING-RUN-001**

**Phase:** Phase E — Scale, Proof & Release Lock
**Milestone:** M31 — FULL-TRAINING-RUN-001
**Status:** Planned (Ready to Implement)
**Owner:** Cursor (implementation) + Human (execution & evidence)

---

## 1. Milestone Intent (Single Sentence)

> Execute **one full, end-to-end training run** of RenaceCHESS using the production training pipeline, producing **reproducible checkpoints and metrics** suitable for downstream evaluation and external proof.

This milestone is about **execution, not experimentation**.

---

## 2. What M31 Explicitly Does

M31 will:

1. Run **exactly one** full training session:

   * Policy head
   * Outcome head
   * Fixed architecture
   * Fixed hyperparameters
2. Produce **versioned training artifacts**:

   * Checkpoints
   * Training metrics
   * Configuration snapshot
3. Preserve **strict determinism where possible**, and explicitly document where it is not.
4. Leave behind a **complete evidence trail** for M32 and M33.

---

## 3. What M31 Explicitly Does *Not* Do

🚫 No architecture changes
🚫 No hyperparameter sweeps
🚫 No model selection
🚫 No calibration logic changes
🚫 No eval-set changes
🚫 No ingestion redesign

If something feels like “tuning,” it is **out of scope**.

---

## 4. Preconditions (All Must Be True)

| Precondition                               | Status |
| ------------------------------------------ | ------ |
| Phase D closed                             | ✅      |
| M29 GPU feasibility proven                 | ✅      |
| Frozen eval v2 exists (10k, deterministic) | ✅      |
| CI green baseline                          | ✅      |
| Training code path exercised               | ✅      |

**If any precondition breaks, M31 pauses.**

---

## 5. Training Configuration (Locked Inputs)

These are **frozen for the milestone**.

### 5.1 Model Scope

| Component             | Included     |
| --------------------- | ------------ |
| Policy head           | ✅            |
| Outcome head          | ✅            |
| HDI computation       | ✅            |
| Personality overlays  | ❌ (disabled) |
| Runtime recalibration | ❌ (off)      |

---

### 5.2 Precision & Hardware

| Item       | Value                                     |
| ---------- | ----------------------------------------- |
| GPU        | RTX 5090 (Blackwell)                      |
| CUDA       | 12.8+                                     |
| PyTorch    | 2.10.0+cu128                              |
| Precision  | FP32 **baseline**, AMP optional secondary |
| Batch size | **256** (validated in M29)                |

> AMP may be run **only if FP32 completes successfully first**.

---

### 5.3 Dataset Inputs

| Dataset       | Source                            |
| ------------- | --------------------------------- |
| Training data | Production dataset manifest (v2)  |
| Frozen eval   | `data/frozen_eval_v2/` (from M30) |
| Shuffle seed  | Fixed                             |
| Epoch count   | Fixed (documented in config)      |

---

## 6. Artifacts Produced (Required)

M31 is not complete unless **all** of the following exist.

### 6.1 Training Artifacts

```
artifacts/m31_training_run/
├── config.json                # Full training config snapshot
├── env.json                   # CUDA, PyTorch, GPU, OS
├── training_metrics.jsonl     # Losses, steps, timing
├── checkpoint_step_*.pt       # One or more checkpoints
├── final_checkpoint.pt
└── README.md                  # Human summary
```

---

### 6.2 Determinism & Provenance

| Artifact              | Purpose                |
| --------------------- | ---------------------- |
| Config hash           | Proves training inputs |
| Code commit SHA       | Ties model to code     |
| Dataset manifest hash | Ties model to data     |
| Frozen eval hash      | Locks evaluation ruler |

---

## 7. CI & Automation Rules

**CI does NOT run training.**

CI responsibilities in M31:

* Schema validation of emitted artifacts
* Presence checks (files exist)
* Hash format validation
* **No GPU usage**
* **No training execution**

Training is **human-executed, evidence-checked**.

---

## 8. Validation Criteria (Exit Gates)

M31 exits successfully if and only if:

1. Training completes without crash
2. At least one usable checkpoint exists
3. Metrics are recorded and parseable
4. Frozen eval v2 hash matches M30
5. All artifacts are committed or externally referenced
6. M31 audit contains **no unknowns**

Failure is acceptable. **Silent failure is not.**

---

## 9. Failure Modes & Guardrails

| Risk           | Guardrail                                   |
| -------------- | ------------------------------------------- |
| OOM            | Batch size fallback (256 → 128, documented) |
| Long runtime   | Early abort with metrics preserved          |
| Nondeterminism | Explicitly documented                       |
| Disk overflow  | Artifact pruning policy                     |

Any fallback must be **written down**.

---

## 10. Deliverables to Commit (Governance)

| File                                          | Required |
| --------------------------------------------- | -------- |
| `docs/milestones/PhaseE/M31/M31_plan.md`      | ✅        |
| `docs/milestones/PhaseE/M31/M31_toolcalls.md` | ✅        |
| `docs/milestones/PhaseE/M31/M31_audit.md`     | ✅        |
| `docs/milestones/PhaseE/M31/M31_summary.md`   | ✅        |
| Artifact references                           | ✅        |

---

## 11. How Cursor Should Proceed (Explicit Instructions)

**Cursor should:**

1. Scaffold the M31 milestone folder
2. Add config snapshot + artifact schemas (if missing)
3. Prepare training runner for a **single execution**
4. Add CI validations for artifact presence only
5. Ask clarifying questions **before** touching training code

**Cursor must not:**

* Change training logic
* Add flags “just in case”
* Tune anything

---

## 12. Why M31 Matters (Context for Cursor)

M31 is the **only milestone that proves RenaceCHESS actually trains**.

Everything after this (M32–M34) is:

* evaluation
* comparison
* packaging
* release

If M31 fails, that’s acceptable.
If M31 is sloppy, **the project fails**.

---

## 13. Immediate Next Action

👉 Hand this plan to Cursor.
👉 Ask Cursor for **clarifying questions only**.
👉 Do not start training until answers are locked.

---

If you want, next I can:

* pre-answer likely Cursor questions
* draft the **training config template**
* or define the **exact artifact schemas** M31 should emit

Just say the word.
