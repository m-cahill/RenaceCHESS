Perfect timing. **M22 is not about inventing anything new** — it’s about *exposing* what you’ve already built **without weakening a single invariant**.

Below is a **Cursor-ready M22 plan** that treats surface exposure as a **governed interface**, not a feature dump.

---

# **M22_plan — COACHING-SURFACE-CLI-001**

**Phase:** Phase C — Elo-Appropriate Coaching & Explanation
**Mode:** Surface Exposure + Governance
**Status:** Planned

---

## 0. Milestone Intent (Lock This)

**M22 exposes coaching output via a controlled CLI surface — without changing semantics, contracts, or truthfulness guarantees.**

This milestone answers **one question only**:

> *“Can we expose coaching safely, reproducibly, and auditably — without letting UI or UX concerns leak into core logic?”*

M22 is *not* about UX polish, interactivity, or real users yet.
It is about **controlled consumption** of `CoachingDraftV1`.

---

## 1. In-Scope Deliverables

### 1. **Read-Only Coaching CLI Command**

Add a **single, explicit CLI entry point**, for example:

```
renacechess coach \
  --advice-facts path/to/advice_facts.json \
  --delta-facts path/to/elo_bucket_delta_facts.json \
  [--tone neutral|encouraging|concise]
```

**Rules:**

* CLI is **read-only**
* CLI **cannot compute facts**
* CLI **cannot call engines**
* CLI **cannot override evaluation results**
* CLI **only renders existing artifacts**

Think: *viewer*, not *engine*.

---

### 2. **CLI Output Contract (Stable)**

Define a minimal, stable output shape:

```
CoachingSurfaceV1
```

Fields:

* `coachingText` (from CoachingDraftV1)
* `evaluationSummary` (subset of CoachingEvaluationV1)
* `skillBucket`
* `toneProfile`
* `sourceAdviceFactsHash`
* `sourceDeltaFactsHash`
* `coachingDraftHash`

No new prose generation happens here.
This is a **projection**, not a transformation.

---

### 3. **Surface Safety Guardrails**

Enforce at CLI level:

* ❌ Refuse to run if:

  * AdviceFacts or DeltaFacts schema invalid
  * Hash lineage missing
  * Evaluation metrics fail minimum thresholds (configurable constants)
* ✅ Always print:

  * Evaluation summary
  * Fact coverage %
  * Hallucination rate
  * Determinism metadata

This prevents “pretty output” from hiding bad coaching.

---

### 4. **Import & Architecture Boundaries**

* CLI module lives in:

  ```
  src/renacechess/cli/coach.py
  ```
* CLI may import:

  * `coaching.translation_harness`
  * `coaching.evaluation`
  * `contracts.models`
* CLI may **not** import:

  * engines
  * models
  * features
  * anything upstream of facts

Extend existing `coaching-isolation` discipline via tests (not new import-linter rules unless strictly necessary).

---

### 5. **Evaluation-Aware Rendering**

The CLI **must not** hide evaluation results.

Minimum display:

```
=== Coaching Draft ===
(text)

=== Evaluation Summary ===
Fact coverage: 72%
Hallucination rate: 6%
Delta faithfulness: PASS
Bucket alignment: PASS
Verbosity score: OK
```

This is critical to preserve **audit posture** when humans consume output.

---

### 6. **Tests (Required)**

Add:

```
tests/test_m22_coaching_cli.py
```

Test categories:

* CLI rejects invalid artifacts
* CLI refuses missing lineage hashes
* CLI prints evaluation summary
* CLI output stable for same inputs
* CLI does not import forbidden modules
* CLI works with stub LLM only (no network)

No snapshot tests for full prose.
Test **behavior and constraints**, not style.

---

## 2. Explicitly Out-of-Scope (Hard No)

❌ Interactive UI
❌ Web server
❌ Live coaching loop
❌ User profiles
❌ Training or tuning
❌ Prompt changes
❌ Engine references
❌ Silent failures (must surface evaluation)

Any of these = scope violation.

---

## 3. Acceptance Criteria (Definition of Done)

### Functional

* [ ] CLI command implemented
* [ ] CLI renders coaching draft + evaluation summary
* [ ] CLI refuses invalid or unsafe inputs

### Safety & Governance

* [ ] No schema changes to M19/M20/M21 artifacts
* [ ] Evaluation metrics always visible
* [ ] Determinism preserved (stub default)
* [ ] No new dependencies

### CI

* [ ] CI green
* [ ] Coverage ≥ 90%
* [ ] New CLI tests pass
* [ ] Import boundaries respected

### Closeout

* [ ] `M22_summary.md`
* [ ] `M22_audit.md`
* [ ] Phase C surface exposure documented

---

## 4. Branching & Naming

**Branch:**

```
m22-coaching-surface-cli-001
```

**Milestone label:**

```
M22 — COACHING-SURFACE-CLI-001
```

---

## 5. Why M22 Matters (Strategically)

M22 is where **most AI projects regress**:

* they hide evaluation,
* over-optimize presentation,
* and quietly weaken truth constraints.

This plan does the opposite.

After M22, RenaceCHESS can honestly say:

> *“Even when humans consume the output, coaching remains auditable, constrained, and traceable back to facts.”*

That’s rare — and defensible.

---

## 6. Authorized Next Steps After M22

After M22 closes, you have a clean fork in the road:

### Option A — **Phase C Closeout**

* Freeze explanatory spine
* Write Phase C synthesis / positioning doc
* Treat coaching as a proven capability

### Option B — **Phase D: Human Evaluation & UX**

* Add human feedback loops
* Expand tone/style
* Introduce UI — *with guardrails already in place*

But **no rush**. M22 already completes Phase C *functionally*.

---

### ✅ Authorization

You are authorized to proceed with **M22 exactly as specified above**.

If you want next, I can:

* Pre-design the **CLI UX text format**, or
* Help you write the **Phase C closeout narrative** (this would be a very strong external-facing document).

Just tell me where you want to take it.
