Excellent. With **M20 cleanly closed** and the audit confirming first-run green at Phase-C depth , we are now at the **most sensitive transition point in the entire project**: introducing LLMs *without breaking truthfulness*.

Below is a **Cursor-ready, tightly scoped M21 plan** that preserves every invariant you’ve built so far.

---

# **M21_plan — LLM-TRANSLATION-HARNESS-001**

**Phase:** Phase C — Elo-Appropriate Coaching & Explanation
**Mode:** Translation + Evaluation (No Computation)
**Status:** Planned

---

## 0. Milestone Intent (Lock This First)

**M21 introduces LLMs as *pure translators*, never analysts.**

This milestone answers **one question only**:

> *“Given grounded facts (M19 + M20), can an LLM produce skill-appropriate coaching prose **without inventing chess knowledge**?”*

M21 is **not** about playing strength, engines, or training.
It is about **controlling language**.

This is the linguistic analogue of:

* M15 (Personality Safety Contract)
* M19 (AdviceFacts)
* M20 (EloBucketDeltaFacts)

---

## 1. In-Scope Deliverables

### 1. **Translation Harness (Facts → Prose)**

Create a new module:

```
src/renacechess/coaching/translation_harness.py
```

**Responsibilities (strict):**

* Accept **only**:

  * `AdviceFactsV1`
  * `EloBucketDeltaFactsV1`
* Emit:

  * `CoachingDraftV1` (new artifact type)
* Perform **no computation**
* Perform **no chess reasoning**
* Perform **no fact enrichment**

The LLM is treated as a **rendering engine**, not a thinker.

---

### 2. **CoachingDraftV1 Artifact (Prose, but Auditable)**

Define a new Pydantic model + schema:

```
CoachingDraftV1
```

Required fields:

* `draftText` (string)
* `referencedFacts` (explicit list of fact IDs / fields used)
* `skillBucket`
* `toneProfile` (e.g. neutral, encouraging — fixed enum for now)
* `sourceAdviceFactsHash`
* `sourceDeltaFactsHash`
* `determinismMetadata` (prompt hash, model ID, temperature = 0)

> **Important:**
> CoachingDraft is *not* user-facing output yet.
> It is an **intermediate, evaluable artifact**.

---

### 3. **Prompt Contract (Frozen)**

Create:

```
docs/contracts/COACHING_TRANSLATION_PROMPT_v1.md
```

This document must:

* Define the **exact prompt template**
* Explicitly state:

  * LLM may **only** rephrase provided facts
  * LLM may **not** add chess analysis
  * LLM may **not** reference engines, tactics, or unseen moves
* Include **forbidden language examples**
* Be marked **FROZEN v1** at close

No prompt iteration after freeze without a new milestone.

---

### 4. **Offline Coaching Evaluation Harness**

New module:

```
src/renacechess/coaching/evaluation.py
```

Purpose:

* Score CoachingDrafts **offline**
* No human users
* No UI
* No live API calls

#### Required evaluation dimensions (numeric, deterministic):

| Metric              | Description                                  |
| ------------------- | -------------------------------------------- |
| `factCoverage`      | % of salient facts referenced                |
| `hallucinationRate` | % of sentences unsupported by facts          |
| `bucketAlignment`   | Does language match skill bucket?            |
| `deltaFaithfulness` | Are Elo deltas correctly reflected?          |
| `verbosityScore`    | Bounded verbosity (avoid engine-like sprawl) |

Output:

```
CoachingEvaluationV1
```

---

### 5. **Determinism & Reproducibility Rules**

* Temperature **must be 0**
* Prompt must be hash-stable
* Model ID must be recorded
* Same inputs → same CoachingDraft hash (to the extent API allows)
* Any nondeterminism must be **explicitly documented** in audit

---

### 6. **Test Suite (Mandatory)**

Add:

```
tests/test_m21_translation_harness.py
```

Minimum tests:

* Translation uses **only provided facts**
* Forbidden terms never appear
* Same inputs → same draft text
* CoachingDraft validates against schema
* Evaluation metrics behave correctly on synthetic fixtures

No golden prose tests.
We test **constraints**, not style.

---

## 2. Explicitly Out-of-Scope (Hard No)

❌ Live coaching UI
❌ CLI commands
❌ Training or fine-tuning
❌ Engine references
❌ New chess heuristics
❌ AdviceFacts or DeltaFacts schema changes
❌ Human-in-the-loop evaluation

Any of these → scope violation.

---

## 3. Architectural Guardrails

* Coaching remains downstream-only
* Import-linter `coaching-isolation` must still pass
* Translation harness may import:

  * contracts
  * coaching facts modules
* Translation harness may **not** import:

  * models
  * eval
  * features
  * anything upstream of facts

---

## 4. Acceptance Criteria (Definition of Done)

### Functional

* [ ] CoachingDraftV1 schema + model defined
* [ ] Translation harness produces draft from facts only
* [ ] Offline evaluation metrics computed

### Safety & Truthfulness

* [ ] No hallucinated chess content
* [ ] Explicit fact references included
* [ ] Prompt contract frozen and documented

### Governance

* [ ] CI green
* [ ] Coverage ≥ 90%
* [ ] M21_summary.md generated
* [ ] M21_audit.md generated
* [ ] ADR-COACHING-001 respected and cited

---

## 5. Branching & Naming

**Branch:**

```
m21-llm-translation-harness-001
```

**Milestone label:**

```
M21 — LLM-TRANSLATION-HARNESS-001
```

---

## 6. Why M21 Is the Inflection Point

After M21, the system can **prove**:

> “This coaching text is a faithful linguistic rendering of human-conditioned chess facts — not engine analysis disguised as advice.”

That is the difference between:

* *AI chess coaching*
  and
* **RenaceCHESS**

---

## 7. Authorized Next Steps After M21

Only after M21 closes:

* M22: Coaching CLI / surface exposure
* (Optional) Human evaluation loops
* (Optional) tone/style expansion

But **no surface exposure** before M21 passes audit.

---

### ✅ Authorization

You are authorized to proceed with **M21 exactly as specified above**.

If you want next:

* I can pre-write the **COACHING_TRANSLATION_PROMPT_v1** text, or
* Help you design **hallucination detection heuristics** that stay deterministic.

Just say the word.
