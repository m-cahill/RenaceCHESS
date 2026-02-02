You’re right — **M27 is fully done and cleanly closed** (audit + summary attached, CI green). Let’s answer both parts crisply and then move forward.

---

## How many milestones remain in **Phase D**?

Based on how Phase D has unfolded and the governance posture you’ve enforced, Phase D now looks **nearly complete**.

### Phase D original intent

**Phase D = Data Expansion, Calibration & Quality**

> Measure, correct, gate, and *evaluate* probabilistic quality — without changing default behavior.

You have now delivered:

| Milestone | Purpose                                         | Status   |
| --------- | ----------------------------------------------- | -------- |
| M23       | Hardening runway (security, perf, CLI coverage) | ✅ Closed |
| M24       | Calibration metrics (ECE, Brier, NLL)           | ✅ Closed |
| M25       | Offline recalibration fitting                   | ✅ Closed |
| M26       | Runtime recalibration gating                    | ✅ Closed |
| M27       | Runtime recalibration evaluation                | ✅ Closed |

### What remains in Phase D?

**Only ONE truly Phase-D-legitimate milestone remains:**

> **M28 — Recalibration Activation Decision**

After M28, anything else would either be:

* **Phase E (Productization / UX / Human-in-the-loop)**, or
* A *new* Phase D+ extension you’d explicitly define.

### ✅ Phase D remaining milestone count

**Answer:**
👉 **Exactly 1 remaining milestone (M28)**

Phase D is otherwise **complete in substance**.

---

## M28 — PHASE-D-RECALIBRATION-ACTIVATION-DECISION-001

### (Plan to hand off to Cursor)

### 🔑 Core purpose of M28

M28 is **not engineering-first** — it is a **governed decision milestone**.

> **Question M28 answers:**
> *Given M27’s evidence, should runtime recalibration be activated — and if so, where, how, and with what constraints?*

---

## M28 Scope Definition

### ✅ In Scope

1. **Decision artifact**

   * Explicitly records whether recalibration is:

     * ❌ Rejected
     * ⚠️ Restricted (specific Elo buckets / scopes)
     * ✅ Activated (policy, outcome, or both)

2. **Activation policy schema**

   * `RuntimeRecalibrationPolicyV1`
   * Declarative rules, not code switches

3. **Evidence linkage**

   * References **M27 RuntimeRecalibrationReportV1**
   * Records justification per bucket

4. **Runtime wiring (minimal)**

   * If activated, wiring is **policy-driven**, not hard-coded
   * Gate + policy both required
   * Default path remains unchanged unless policy allows

5. **CI enforcement**

   * CI job asserts:

     * Policy + gate consistency
     * No activation without explicit policy
     * M26 guard still holds for disabled cases

---

### ❌ Explicitly Out of Scope

* Retraining
* Parameter tuning
* UI/UX changes
* Human feedback loops
* Coaching behavior changes
* Any automatic activation

M28 **decides**, it does not iterate.

---

## M28 Deliverables

### 1. New Schemas

| Schema                           | Purpose                        |
| -------------------------------- | ------------------------------ |
| `RuntimeRecalibrationPolicyV1`   | Declarative activation rules   |
| `RuntimeRecalibrationDecisionV1` | Human-readable decision record |

---

### 2. Decision Runner

* Reads:

  * M27 report
  * Proposed policy
* Emits:

  * Decision artifact
  * Validation verdict (consistent / inconsistent)

No math, no fitting — **pure governance logic**.

---

### 3. Runtime Integration (If Activated)

* **Only applied if BOTH exist:**

  1. RecalibrationGateV1 (M26)
  2. RuntimeRecalibrationPolicyV1 (M28)

* Supports:

  * Per-Elo bucket activation
  * Per-scope activation (`policy`, `outcome`, `both`)

---

### 4. CLI Command

```bash
renacechess eval runtime-recalibration-decision \
  --report runtime_recalibration_report.json \
  --policy runtime_recalibration_policy.json
```

Outputs:

* Decision artifact
* Human-readable summary

---

### 5. CI Jobs

| Job                               | Purpose                        |
| --------------------------------- | ------------------------------ |
| `runtime-recalibration-decision`  | Validate policy vs evidence    |
| `runtime-recalibration-guard-m28` | Ensure default path still safe |

All deterministic, all schema-validated.

---

## M28 Exit Criteria (Very Important)

M28 is complete when:

* [ ] A **clear decision** is recorded
* [ ] The decision is **traceable to M27 evidence**
* [ ] Runtime behavior is **unchanged unless explicitly allowed**
* [ ] CI enforces the decision
* [ ] Phase D can be formally closed

---

## After M28

Once M28 closes, you have three clean options:

1. **Phase E — Human Evaluation & UX**
2. **Phase E — Coaching Quality & Presentation**
3. **Phase E — External Demo / Paper / Partner Review**

But **Phase D itself will be DONE**.

---

## Summary

* **Remaining Phase D milestones:** **1**
* **That milestone:** **M28**
* **Nature of M28:** Decision + governance, not experimentation
* **Phase D after M28:** Complete and defensible

If you want, next I can:

* Draft `M28_plan.md` verbatim for Cursor, or
* Help you pre-decide likely activation policies based on M27 patterns, or
* Sketch the Phase D → Phase E transition doc

Just say the word.
