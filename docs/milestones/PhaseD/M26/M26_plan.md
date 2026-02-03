Excellent. M25 closed cleanly, and the attached **audit** and **summary** confirm we are at the exact inflection point Phase D was designed to reach  .

M26 is therefore **not “more calibration work”** — it is a **governance milestone** that decides *how (and whether)* recalibration becomes part of the system’s observable behavior.

Below is a **Cursor-ready M26 plan**, written to align with your audit posture and to avoid accidental Phase C erosion.

---

# M26_plan — PHASE-D-RUNTIME-GATING-001

**Phase:** D — Data Expansion, Calibration & Quality
**Milestone intent:** Introduce a **strictly governed runtime gating mechanism** for recalibration, without changing default behavior and without modifying Phase C contracts.

---

## 0) Why M26 exists (clear framing)

After M25, it is provably true that:

* Recalibration parameters can be fit deterministically
* Calibration improvements can be measured per Elo bucket
* Recalibration is currently **offline-only** and **non-binding**

What is *not yet true*:

> “We can safely *optionally* apply recalibration to runtime outputs without undermining explanation safety, auditability, or trust.”

M26 exists to answer **that question only**.

---

## 1) Scope definition

### ✅ In Scope (M26)

M26 introduces **runtime gating infrastructure**, not runtime behavior changes.

Specifically:

1. **RecalibrationGateV1 contract**
2. **Explicit runtime toggle (off by default)**
3. **Provenance-aware application wrapper**
4. **End-to-end guardrails & tests**
5. **CI enforcement that default path remains unchanged**

---

### ❌ Explicitly Out of Scope

* No default-on recalibration
* No user-facing UX changes
* No LLM prompt changes
* No Phase C contract changes
* No new calibration methods
* No training or fine-tuning

---

## 2) Core deliverables

### A) RecalibrationGateV1 (new contract)

Define a **minimal, explicit gate artifact**:

```text
RecalibrationGateV1
```

Fields:

* `enabled: bool`
* `parameters_ref: Optional[str]` (hash or path to RecalibrationParametersV1)
* `scope: Literal["outcome", "policy", "both"]`
* `applied_at: Optional[timestamp]`
* `notes: Optional[str]`

📌 This contract is **the only authority** that allows runtime recalibration.

---

### B) Runtime application wrapper (non-default)

Add a wrapper function, e.g.:

```python
apply_recalibration_if_enabled(
    probs,
    skill_bucket,
    gate: RecalibrationGateV1,
    params: RecalibrationParametersV1
) -> probs
```

Rules:

* If `gate.enabled == False`: **return input unchanged**
* If enabled:

  * Apply temperature scaling
  * Preserve probability mass
  * Record provenance metadata

📌 This wrapper must live **outside** Phase C logic (e.g. in `eval/runtime_recalibration.py`).

---

### C) Provenance propagation

When recalibration is applied:

* Attach metadata to runtime result:

  * `recalibration_applied: true`
  * `recalibration_parameters_hash`
  * `recalibration_gate_hash`

This metadata:

* Is **not consumed** by LLMs
* Is **not surfaced** by default
* Exists for audit/debugging only

---

### D) CI job: `runtime-recalibration-guard`

Add a required CI job that asserts:

1. **Default runtime path unchanged**

   * With gate disabled, outputs byte-for-byte identical to M25 baseline
2. **Enabled path correctness**

   * With gate enabled, outputs match offline recalibration logic
3. **No Phase C contract touched**
4. **Determinism preserved**

This job **fails hard** if default behavior changes.

---

### E) Tests (critical)

Add tests that explicitly prove:

* Gate disabled ⇒ no change
* Gate enabled ⇒ change occurs
* Missing params ⇒ runtime refusal
* Scope = outcome/policy/both respected
* Metadata attached correctly
* LLM inputs unchanged

These tests are the *real* deliverable of M26.

---

## 3) Acceptance criteria (hard gates)

M26 is **closable only if**:

1. ✅ Default runtime behavior is provably unchanged
2. ✅ Recalibration cannot be applied without an explicit gate
3. ✅ Gate + parameters are fully traceable
4. ✅ Phase C contracts untouched
5. ✅ CI coverage ≥90%
6. ✅ New CI job enforces invariants

---

## 4) Guardrails (non-negotiable)

🚫 No “implicit enable”
🚫 No environment-variable shortcuts
🚫 No silent probability modification
🚫 No LLM awareness of recalibration
🚫 No UX changes

M26 is **plumbing and proof**, not product.

---

## 5) Execution plan (Cursor-friendly)

**Branch:**
`m26-phase-d-runtime-gating-001`

### PR1 — Contracts

* Add `RecalibrationGateV1`
* Schema + Pydantic
* Validation tests

### PR2 — Runtime wrapper

* Implement `apply_recalibration_if_enabled`
* No call-site wiring yet
* Unit tests

### PR3 — Integration wiring

* Wire wrapper into runtime path *behind gate*
* Provenance metadata
* No default change

### PR4 — CI enforcement

* Add `runtime-recalibration-guard` job
* Golden-path equivalence tests

### PR5 — Docs & audit stubs

* M26_plan / run / audit / summary placeholders

---

## 6) Why M26 comes before “using” recalibration

This ordering preserves trust:

* **M24:** measure
* **M25:** improve (offline)
* **M26:** prove safety of optional runtime use
* **M27:** decide exposure (if ever)

No shortcuts.

---

## 7) One-line positioning

> **M26 proves that recalibration can be applied to RenaceCHESS without silently changing behavior — and that safety, not convenience, controls activation.**

---

## Authorization

This plan is **approved for handoff to Cursor**.

If you want next, I can:

* Pre-draft `RecalibrationGateV1`
* Sketch the exact CI guard assertions
* Or outline **M27 (human evaluation vs runtime rollout)** so Phase D stays coherent

Just tell me how conservative you want to be.






