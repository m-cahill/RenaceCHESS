# M15_plan — PERSONALITY-CONTRACT-001: Personality Safety Contract

## Milestone Identity

**Milestone:** M15 — PERSONALITY-CONTRACT-001  
**Phase:** Phase B — Personality Framework & Style Modulation  
**Status:** ⏳ Planned  
**Pre-reqs:** M14 (training readiness), M13 (contract semantics), M11 (PoC lock)  
**Branch:** `m15-personality-contract-001`

---

## 1. Purpose (Single Sentence)

Define the **Personality Safety Contract** that governs bounded behavioral variation using the M11 structural substrate, ensuring personalities cannot override correctness.

---

## 2. Explicit Non-Goals (Hard Constraints)

M15 **must not**:

* Implement actual personality modules
* Retrain any models
* Modify learned policy or outcome head behavior
* Change HDI definitions or structural cognition semantics
* Alter frozen schemas or PoC contracts
* Weaken CI gates or determinism guarantees

If any of the above becomes necessary, the change **must be deferred to a later milestone**.

---

## 3. Scope (What This Milestone Does)

### 3.1 Personality Safety Contract Definition

Define the safety envelope within which personality modules may operate:

**Deliverable:**

* `docs/contracts/PERSONALITY_SAFETY_CONTRACT.md`

**Must specify:**

* Bounded shaping constraints (top-k, Δeval threshold)
* Allowed modification surfaces (move re-ranking only)
* Prohibited modifications (base probabilities, WDL, HDI semantics)
* Versioning and audit requirements
* Regression test requirements

---

### 3.2 PersonalityModuleV1 Interface Schema

Define the interface contract for personality modules:

**Deliverable:**

* `src/renacechess/contracts/schemas/v1/personality_module.v1.schema.json`
* Pydantic model in `src/renacechess/contracts/models.py`

**Must specify:**

* Input: base policy distribution, position, conditioning
* Output: adjusted policy distribution
* Knobs: aggression, positional emphasis, piece activity, etc.
* Bounds: λ thresholds, top-k constraints

---

### 3.3 Personality Evaluation Framework (Schema Only)

Define how personality behavior will be evaluated:

**Deliverable:**

* `docs/evaluation/PERSONALITY_EVALUATION.md` (specification only)

**Must specify:**

* Strength drift metrics
* Blunder rate stability requirements
* Style divergence measurement
* Comparison methodology

---

## 4. CI & Governance Guardrails

### Required CI Behavior

* CI remains **unchanged** unless adding:
  * Schema validation for new contract
  * Type checks for new interface
* No personality execution in CI
* No training or evaluation changes

### Audit Posture

* Contract must be marked **FROZEN** once merged
* Any modification to safety constraints requires new milestone

---

## 5. Files & Artifacts Inventory

**New Files Expected:**

```
docs/
  contracts/
    PERSONALITY_SAFETY_CONTRACT.md

  evaluation/
    PERSONALITY_EVALUATION.md

src/renacechess/
  contracts/
    schemas/v1/
      personality_module.v1.schema.json
    models.py (updated)
```

**No existing files should change behaviorally.**

---

## 6. Validation Criteria (Definition of Done)

M15 is complete when:

* ✅ Personality safety contract defined and frozen
* ✅ PersonalityModuleV1 schema created and validated
* ✅ Personality evaluation framework specified
* ✅ No PoC artifacts, schemas, or behaviors changed
* ✅ CI remains truthful green
* ✅ Audit trail clearly states "contract definition only"

---

## 7. Deferred Items (Explicit)

The following are **explicitly deferred** beyond M15:

* Actual personality module implementations
* Personality training campaigns
* Personality evaluation execution
* GM-style pawn-clamp personality (M16)
* Personality library expansion (M17)

---

## 8. Closeout Requirements

At closeout, generate:

* `M15_summary.md`
* `M15_audit.md`

Each must explicitly state:

> "M15 defines the personality safety contract only.
> No personality modules were implemented and no PoC semantics were altered."

---

## 9. Success Signal

After M15, you should be able to answer — **with evidence**:

> "We have an explicit, frozen contract governing how personality modules may modify behavior — and we know exactly what safety invariants must hold."

---

*Plan created as part of M14 closeout.*

