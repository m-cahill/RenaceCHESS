Perfect — M19 is cleanly closed, audit posture is strong, and Phase C is now *properly* entered.
M20 is where the project gets genuinely interesting, but it must stay **facts-only** and **LLM-free**.

Below is a **Cursor-ready M20 plan**, scoped tightly to avoid premature explanation logic while still creating real explanatory power.

---

# **M20_plan — ELO-BUCKET-DELTA-FACTS-001**

**Phase:** Phase C — Elo-Appropriate Coaching & Explanation
**Mode:** Architecture + Facts Generation
**Status:** Planned

---

## 0. Milestone Intent (Lock This)

**M20 introduces Elo-relative reasoning as structured facts — not prose.**

This milestone answers one question only:

> *“What changes, statistically and structurally, as you move from one Elo bucket to the next — and how does the current position deviate from that?”*

M20 **does not** explain anything in natural language.
It generates **Elo-delta facts** that *enable* explanation later.

This is the Phase C analogue to:

* M11 (structural cognition substrate)
* M15 (personality safety contract)

---

## 1. In-Scope Deliverables

### 1. **EloBucketDeltaFacts schema (v1)**

A new **facts-only artifact** describing *how* stronger/weaker humans differ in this position.

**New schema (v1):**

```
elo_bucket_deltas.v1.schema.json
```

This schema will be referenced by `AdviceFactsV1` but **not merged into it yet** (composition, not mutation).

---

### 2. **EloBucketDeltaFactsV1 Pydantic models**

Add models to `contracts/models.py`:

* `EloBucketDeltaFactsV1`
* Supporting sub-models (policy deltas, outcome deltas, difficulty deltas)

No changes to frozen v1 AdviceFacts schema.

---

### 3. **Pure delta-builder function**

New module:

```
src/renacechess/coaching/elo_bucket_deltas.py
```

**Pure function only** — accepts pre-computed signals.

```python
build_elo_bucket_delta_facts_v1(
    *,
    position_facts: AdviceFactsInputsV1,
    baseline_bucket: EloBucket,
    comparison_bucket: EloBucket,
    baseline_policy: PolicySummary,
    comparison_policy: PolicySummary,
    baseline_outcome: OutcomeSummary,
    comparison_outcome: OutcomeSummary,
) -> EloBucketDeltaFactsV1
```

No provider orchestration. No inference. No model calls.

---

### 4. **Delta categories (facts, not advice)**

M20 facts should answer *what changed*, never *what to do*.

#### A) **Policy divergence**

* KL divergence
* Total variation distance
* Move-rank flips (same move ranked differently)
* Probability mass shift toward/away from top-N moves

#### B) **Outcome expectation shifts**

* ΔP(win), ΔP(draw), ΔP(loss)
* Win-rate slope across buckets (monotonicity check)

#### C) **Difficulty sensitivity**

* ΔHDI
* Optional: normalized difficulty slope vs Elo

#### D) **Structural emphasis shifts** (if structural data present)

* Mobility reliance change
* Weak-square sensitivity change
* King safety weighting change

All numeric. All bounded. All deterministic.

---

### 5. **Determinism & audit hooks**

Every `EloBucketDeltaFactsV1` artifact must include:

* `baselineBucket`
* `comparisonBucket`
* `determinismHash`
* `sourceAdviceFactsHash`
* `sourceContractVersions`

This allows:

* offline evaluation
* reproducible explanation audits
* later attribution of coaching claims

---

### 6. **Schema & Contract Documentation**

Create:

```
docs/contracts/ELO_BUCKET_DELTA_FACTS_CONTRACT_v1.md
```

Document:

* bucket semantics
* monotonicity assumptions
* allowed vs forbidden interpretations
* explicit **non-goals** (no advice, no prose)

Mark **FROZEN v1** at milestone close.

---

### 7. **Tests (mandatory)**

Add tests in:

```
tests/test_m20_elo_bucket_deltas.py
```

Minimum required tests:

* Determinism (same inputs → same hash)
* Delta symmetry (A→B ≈ −(B→A) where applicable)
* Zero delta when buckets equal
* Stable ordering
* Float rounding enforcement
* Schema validation

Coverage must remain ≥ 90%.

---

## 2. Out-of-Scope (Explicitly Forbidden)

❌ LLM prompts
❌ Natural language text
❌ Coaching heuristics (“you should…”)
❌ CLI commands
❌ Training runs
❌ Provider orchestration
❌ Schema changes to AdviceFactsV1

Any of these triggers a **scope violation**.

---

## 3. Import & Architecture Guardrails

* Coaching module remains downstream-only
* No imports from `coaching/` into:

  * `models`
  * `eval`
  * `features`
* Reuse existing `coaching-isolation` import-linter contract

If Cursor needs new helpers:

* Put them in `contracts/` or `features/`
* Do **not** leak logic into coaching

---

## 4. Acceptance Criteria (Definition of Done)

### Functional

* [ ] EloBucketDeltaFacts schema validated
* [ ] Builder produces correct deltas for synthetic fixtures
* [ ] Determinism hash stable

### Architectural

* [ ] AdviceFacts untouched
* [ ] Coaching isolation preserved
* [ ] No provider orchestration

### Governance

* [ ] CI green
* [ ] Coverage ≥ 90%
* [ ] M20_summary.md generated
* [ ] M20_audit.md generated
* [ ] Deferred Issues Registry unchanged (unless justified)

---

## 5. Naming & Branching

**Branch:**

```
m20-elo-bucket-delta-facts-001
```

**Milestone Label:**
`M20 — ELO-BUCKET-DELTA-FACTS-001`

---

## 6. Why This Milestone Matters (Cursor Context)

After M20, the system can say — *provably*:

> “This position punishes lower-rated players because the probability mass shifts toward structurally unsound moves, and the outcome slope steepens.”

…but **still without generating prose**.

That’s the exact boundary you want before M21.

---

## 7. Authorized Next Steps (After M20)

Only after M20 closes:

* M21: LLM translation harness (facts → prose)
* M21 includes *offline coaching quality evaluation*
* No live coaching until evaluation proves truthfulness

---

### ✅ Authorization

You are authorized to proceed with **M20 implementation exactly as specified above**.

If you want, next I can:

* Pre-design the **EloBucketDeltaFacts schema**, or
* Draft the **M21 guardrails** so we don’t accidentally slip into “engine-speak coaching.”

Just say the word.
