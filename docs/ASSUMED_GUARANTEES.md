# RenaceCHESS Assumed Guarantees

This document declares which **RediAI v3 properties are already proven, certified, and audit-defensible**, based on prior work in the **R2L (README-to-Lab)** project.

## Source of Truth

The guarantees below are backed by **Phase XV (Consumer Certification)** of R2L and its complete audit trail:

- `r2l.md` — canonical governance + milestone record
- `PHASE_XV_AUDIT.md` — meta-audit (roll-up)
- `PHASE_XV_CLOSEOUT.md` — formal closeout

Phase XV is **closed, CI-verified, and audit-defensible**.

## RediAI v3 Guarantees Assumed by RenaceCHESS

RenaceCHESS **inherits** the following guarantees without re-testing:

### 1. Determinism (Proven)

**Guarantee:** Identical inputs → byte-stable outputs.

**RenaceCHESS posture:**
- ❌ No need to re-prove determinism at the platform level
- ✅ Only model-level randomness (training, sampling) needs to be scoped and documented

### 2. Schema-Validated Artifacts (Proven)

**Guarantee:** All structured artifacts are schema-validated *before* hashing and persistence.

**RenaceCHESS posture:**
- ❌ No need to re-introduce schema enforcement machinery
- ✅ RenaceCHESS artifacts should simply define schemas and plug into existing validation flow

### 3. Provider-Agnostic Adapter Contracts (Proven)

**Guarantee:** Provider choice does not affect artifact correctness, structure, or guarantees.

**RenaceCHESS posture:**
- ❌ No provider-specific logic allowed in core artifacts
- ✅ Chess-specific inference backends may vary *only* behind adapter boundaries

### 4. CI Truthfulness (Proven)

**Guarantee:** Green CI means invariant-safe; red CI means real failure.

**RenaceCHESS posture:**
- ❌ No weakening of required checks
- ❌ No duplicate or redundant enforcement jobs
- ✅ Any new check must answer a *new* question

### 5. Certification-Grade Governance (Proven)

**Guarantee:** RediAI v3 supports external, portfolio-grade audit and certification.

**RenaceCHESS posture:**
- ❌ RenaceCHESS is not required to re-establish governance primitives
- ✅ RenaceCHESS must respect scope boundaries and produce auditable artifacts

## What RenaceCHESS Does *Not* Need to Test Again

- Platform determinism mechanics
- Artifact hashing and persistence semantics
- Schema validation infrastructure
- Adapter contract enforcement logic
- CI signal truthfulness model
- Branch protection or merge discipline

## What RenaceCHESS *Must* Test

RenaceCHESS testing should focus **only** on *new questions introduced by this project*:

### Model-Level Correctness
- Human move-distribution calibration
- Skill-conditioned W/D/L accuracy
- Time-pressure sensitivity

### Human-Realism Properties
- Entropy vs skill trends
- Blunder-rate sensitivity to time
- Non-collapse in ambiguous positions

### Domain-Specific Artifacts
- LLM Context Bridge payload correctness
- HDI / CLF signal stability
- Narrative seed factual grounding

## Testing Philosophy

**Principle:** *Do not test the platform. Test the claims.*

RenaceCHESS exists to test **new scientific and product claims**:
- "We can model human chess decisions probabilistically."
- "We can ground LLM coaching in factual human difficulty."

Everything else is inherited.

