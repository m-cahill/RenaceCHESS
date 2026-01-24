# M08_plan — First Learned Human Policy Baseline

## Milestone Identity

**Milestone:** M08
**Title:** First Learned Human Policy Baseline
**Phase:** PoC-Core
**Precondition:** M07 CLOSED / IMMUTABLE
**Branch:** `m08-learned-baseline` (to be created)
**Status Goal:** CLOSED with audit artifacts

---

## Objective (Single Sentence)

Train the first minimal human-move policy baseline on Lichess data and evaluate it against the frozen eval set, demonstrating that the PoC-core evaluation stack can measure learned model performance.

---

## Scope Definition

### In Scope

*(To be defined in Phase 2: Clarifying Questions)*

Candidate scope items:
- Minimal policy network architecture
- Training loop with deterministic seeding
- Evaluation on frozen eval manifest
- Comparison with baseline policies (uniform_random, first_legal)
- Training reproducibility verification

### Explicitly Out of Scope

- ❌ Outcome head training (W/D/L prediction)
- ❌ HDI learning (weights remain fixed)
- ❌ Personality modeling
- ❌ Multi-GPU training
- ❌ Hyperparameter tuning infrastructure

---

## Design Principles (Carry-Forward)

- **Reproducibility** — Training is seeded and deterministic
- **Minimal viable** — Smallest architecture that shows learning
- **Evaluation-first** — Must work with existing eval harness
- **No scope creep** — One trained baseline, not a training framework

---

## Work Breakdown

*(To be defined after clarifying questions are answered)*

---

## Exit Criteria (Draft)

- ✅ Trained policy baseline achieves >10% top-1 accuracy on frozen eval
- ✅ Training is reproducible (same seed → same model)
- ✅ Evaluation report v4 generated with HDI
- ✅ All tests green
- ✅ Audit + summary artifacts generated
- ✅ M08 marked CLOSED / IMMUTABLE

---

## Deferred Explicitly to M09+

- Outcome head training
- Multi-epoch hyperparameter search
- Model comparison dashboards

---

## Governance Note

M08 is the first milestone that introduces **learning**. All prior milestones were deterministic pipelines and derived metrics.

This is a significant conceptual transition:
- M00-M07: Infrastructure + evaluation
- M08+: Learned models evaluated by infrastructure

---

### Next Action

This plan is a **template**. Await clarifying questions and locked answers before implementation.

