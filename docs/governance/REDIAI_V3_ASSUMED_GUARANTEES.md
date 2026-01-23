RenaceCHESS — RediAI v3 Assumed Guarantees & Testing Posture
============================================================

Purpose
-------

This document is imported into the **RenaceCHESS** project to explicitly declare which **RediAI v3 properties are already proven, certified, and audit‑defensible**, based on prior work in the **R2L (README‑to‑Lab)** project.

Its goal is to **prevent redundant validation**, reduce unnecessary CI and testing surface area, and allow RenaceCHESS to proceed immediately at the _modeling, research, and product_ layer—rather than re‑proving platform invariants.

This document should be treated as a **standing assumption contract** unless explicitly revoked by a future RediAI v3 audit.

* * *

Source of Truth
---------------

The guarantees below are backed by **Phase XV (Consumer Certification)** of R2L and its complete audit trail:

* `r2l.md` — canonical governance + milestone record

* `PHASE_XV_AUDIT.md` — meta‑audit (roll‑up)

* `PHASE_XV_CLOSEOUT.md` — formal closeout

Phase XV is **closed, CI‑verified, and audit‑defensible**. No RediAI v3 code was modified during Phase XV.

* * *

RediAI v3 Guarantees Assumed by RenaceCHESS
-------------------------------------------

RenaceCHESS **inherits** the following guarantees without re‑testing:

### 1. Determinism (Proven)

**Guarantee:**  
Identical inputs → byte‑stable outputs.

**Evidence:**

* Canonical JSON serialization

* Deterministic ordering of artifacts

* Bundle hash comparison in CI

* Determinism gate enforced as required CI check

**RenaceCHESS posture:**

* ❌ No need to re‑prove determinism at the platform level

* ✅ Only model‑level randomness (training, sampling) needs to be scoped and documented

* * *

### 2. Schema‑Validated Artifacts (Proven)

**Guarantee:**  
All structured artifacts are schema‑validated _before_ hashing and persistence.

**Evidence:**

* Versioned JSON Schemas

* Runtime fail‑fast validation

* CI schema‑validation gate

**RenaceCHESS posture:**

* ❌ No need to re‑introduce schema enforcement machinery

* ✅ RenaceCHESS artifacts should simply define schemas and plug into existing validation flow

* * *

### 3. Provider‑Agnostic Adapter Contracts (Proven)

**Guarantee:**  
Provider choice does not affect artifact correctness, structure, or guarantees.

**Evidence:**

* Explicit adapter contracts

* Multiple providers validated (Phi, MedGemma stub)

* CI adapter‑contract enforcement gate

**RenaceCHESS posture:**

* ❌ No provider‑specific logic allowed in core artifacts

* ✅ Chess‑specific inference backends may vary _only_ behind adapter boundaries

* * *

### 4. CI Truthfulness (Proven)

**Guarantee:**  
Green CI means invariant‑safe; red CI means real failure.

**Evidence:**

* Required checks never weakened

* No misuse of `continue‑on‑error`

* Signal separation: each job answers one question

* Binary certification verdict (CERTIFIED / NOT CERTIFIED)

**RenaceCHESS posture:**

* ❌ No weakening of required checks

* ❌ No duplicate or redundant enforcement jobs

* ✅ Any new check must answer a _new_ question

* * *

### 5. Certification‑Grade Governance (Proven)

**Guarantee:**  
RediAI v3 supports external, portfolio‑grade audit and certification.

**Evidence:**

* Phase XV consumer certification verdict

* Machine‑readable certification artifact

* Full milestone audit trail

**RenaceCHESS posture:**

* ❌ RenaceCHESS is not required to re‑establish governance primitives

* ✅ RenaceCHESS must respect scope boundaries and produce auditable artifacts

* * *

What RenaceCHESS Does _Not_ Need to Test Again
----------------------------------------------

The following are **explicitly out of scope** for RenaceCHESS testing unless RediAI v3 changes:

* Platform determinism mechanics

* Artifact hashing and persistence semantics

* Schema validation infrastructure

* Adapter contract enforcement logic

* CI signal truthfulness model

* Branch protection or merge discipline

Re‑testing these would be redundant and non‑value‑add.

* * *

What RenaceCHESS _Must_ Test
----------------------------

RenaceCHESS testing should focus **only** on _new questions introduced by this project_:

### Model‑Level Correctness

* Human move‑distribution calibration

* Skill‑conditioned W/D/L accuracy

* Time‑pressure sensitivity

### Human‑Realism Properties

* Entropy vs skill trends

* Blunder‑rate sensitivity to time

* Non‑collapse in ambiguous positions

### Domain‑Specific Artifacts

* LLM Context Bridge payload correctness

* HDI / CLF signal stability

* Narrative seed factual grounding

### Integration Surface

* Correct use of RediAI v3 adapters

* Schema compliance of chess artifacts

* * *

Testing Philosophy for RenaceCHESS
----------------------------------

**Principle:**

> _Do not test the platform. Test the claims._

RenaceCHESS exists to test **new scientific and product claims**:

* “We can model human chess decisions probabilistically.”

* “We can ground LLM coaching in factual human difficulty.”

Everything else is inherited.

* * *

Governance Rule (Imported)
--------------------------

Any change that would invalidate the assumptions in this document **requires**:

1. Explicit declaration of which RediAI v3 guarantee is being challenged

2. A scoped milestone to re‑establish that guarantee

3. A documented audit or certification outcome

Absent this, **these guarantees stand**.

* * *

One‑Line Summary for Reviewers
------------------------------

> _RenaceCHESS builds on a RediAI v3 platform that is already deterministic, schema‑validated, provider‑agnostic, and CI‑certified. The project deliberately avoids re‑testing platform invariants and instead focuses all validation effort on the novel problem: modeling and explaining human chess decision‑making._

* * *

**Status:** Imported from R2L Phase XV (CERTIFIED)  
**Last Verified:** 2026‑01‑20  
**Assumption Level:** Hard (audit‑defensible)
