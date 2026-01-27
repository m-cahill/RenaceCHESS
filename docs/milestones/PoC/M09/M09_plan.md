Excellent — M08 is cleanly closed, and the documents confirm the system is now at the **learning inflection point**. We can proceed with M09 without reopening any prior decisions.

Below is a **paste-ready M09 milestone plan** you can hand directly to Cursor. It is written to match your governance style, close known gaps intentionally, and avoid scope creep.

I’m explicitly choosing **Outcome Head (Human W/D/L Learning)** as M09. The alternative (policy/HDI correlation analysis) becomes *much stronger* once a learned outcome signal exists.

This plan also **does not** introduce new infra classes, new CI job types, or training-in-CI violations, and it keeps frozen-eval semantics intact .

---

# M09_plan — Human Outcome Head (W/D/L) v1

## Milestone Intent

Introduce a **learned human outcome head** that predicts **Win / Draw / Loss probabilities** conditioned on the same human-centered context as the move policy, replacing HDI’s proxy outcome sensitivity with a **direct, learned signal**.

This milestone completes the **human evaluation triad**:

| Signal                           | Status    |
| -------------------------------- | --------- |
| Human move prediction            | ✅ M08     |
| Human difficulty (HDI)           | ✅ M07     |
| Human outcome likelihood (W/D/L) | ⛔ **M09** |

The result is a system that can answer:

> *“Given this position, skill level, and time pressure — what are humans likely to do, how hard is it for them, and how likely are they to win?”*

---

## Scope Definition

### In Scope

### 1. Outcome Head Model (v1)

Implement a **minimal, interpretable outcome head**:

* **Task:** 3-class classification → `{win, draw, loss}`
* **Framework:** PyTorch (CPU-only)
* **Architecture:** Shallow linear / MLP head
* **Inputs:**

  * Same representation used by M08 policy baseline
  * Skill bucket
  * Time control class
  * (Optional) HDI scalar as an input feature (explicitly documented)
* **Outputs:** Calibrated probability vector `[P(win), P(draw), P(loss)]`

Constraints:

* Deterministic
* Fixed architecture
* Fixed seed
* No hyperparameter tuning
* No joint training with move policy (separate head)

---

### 2. Training Infrastructure (Local-Only)

Add a new training path:

```bash
renacechess model train-outcome-head
```

Rules:

* Uses **M01–M03 shards only**
* Explicitly **excludes frozen eval**
* Deterministic dataloader order
* Produces:

  * `outcome_head.pt`
  * `outcome_head_metadata.json` (hashes, manifests, config)

❌ No training in CI
❌ No mixed policy/outcome training
❌ No online or iterative learning

---

### 3. Evaluation Integration

Extend the evaluation harness to support outcome evaluation:

* New metrics:

  * Log loss (cross-entropy)
  * Brier score
  * Calibration bins (deterministic)
* Stratified by:

  * Skill bucket
  * Time control class
  * Time pressure bucket

Frozen eval rules:

* Outcome evaluation **must** require a frozen eval manifest
* Training must **never** touch frozen eval

---

### 4. Eval Report Schema v5 (Additive)

Introduce:

```
eval_report.v5.schema.json
```

Additive over v4:

```json
"outcome_metrics": {
  "overall": {...},
  "by_skill": {...},
  "by_time_control": {...}
}
```

Rules:

* v3 and v4 reports remain valid
* No breaking changes
* Schema versioning strictly enforced

---

### 5. CLI Completion

Extend CLI to support:

* Selecting outcome head model
* Running outcome evaluation
* Enforcing frozen eval usage when outcome metrics are requested

Example:

```bash
renacechess eval run \
  --policy learned.v1 \
  --outcome-head outcome.v1 \
  --frozen-eval-manifest frozen_eval.json
```

Invalid combinations must fail fast with clear errors.

---

### 6. Documentation

Add:

```
docs/evaluation/M09_Outcome_Head.md
```

Must explain:

* Why W/D/L is learned separately
* Why engine eval is still excluded
* How outcome head replaces HDI proxy sensitivity
* Scientific limitations (human data ≠ optimal play)

---

## Explicitly Out of Scope (Hard Constraints)

* ❌ Engine evaluation (Stockfish)
* ❌ Joint policy + outcome training
* ❌ Hyperparameter tuning
* ❌ Neural architecture experimentation
* ❌ Training in CI
* ❌ Dashboarding or visualization
* ❌ Elo recomputation

Any of the above requires an explicit future milestone.

---

## Tests & Verification

### Required Tests

* Unit tests for outcome head forward pass
* Dataset filtering tests (frozen eval exclusion)
* Determinism tests (same input → same output)
* Backward compatibility tests (v4 reports still validate)
* CLI validation tests (invalid flag combos)

Coverage:

* Must keep **≥90% global coverage**
* Training modules may remain below threshold *only if justified in audit*

---

## CI / Governance Rules

* No new required CI jobs
* Existing required checks remain unchanged
* No `continue-on-error`
* Frozen eval enforcement must be **code-level**, not documentation-only

---

## Exit Criteria

M09 is complete when:

* Outcome head can be trained locally
* Outcome probabilities are produced deterministically
* Outcome metrics evaluate cleanly on frozen eval
* Eval report v5 validates
* CI remains green
* No M08 or earlier contracts are weakened

---

## Deliverables Checklist

* [ ] `models/outcome_head_v1.py`
* [ ] `models/train_outcome_head.py`
* [ ] `eval/outcome_metrics.py`
* [ ] `contracts/schemas/eval_report.v5.schema.json`
* [ ] CLI extensions
* [ ] Tests (unit + integration)
* [ ] `M09_summary.md`
* [ ] `M09_audit.md`

---

## Strategic Note (Non-Implementational)

Once M09 lands, RenaceCHESS will have:

* A learned human policy
* A learned human outcome model
* Deterministic, frozen evaluation
* Conditioning by skill and time
* Explainable difficulty (HDI)

At that point, the PoC is **conceptually complete**. Everything beyond M09 is refinement, not foundation.

---

If you want, next I can:

* Generate a **Cursor-ready implementation prompt**, or
* Help you define **M10** (likely correlation analysis + narrative grounding), or
* Draft the **Deferred Issues Registry bootstrap** you mentioned earlier so it’s ready when needed.





