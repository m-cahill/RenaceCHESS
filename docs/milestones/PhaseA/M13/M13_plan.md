Great question — this is exactly the right moment to be deliberate.

You have **done the correct governance thing** by closing M12 **without merging**. That is not a mistake; it’s a signal. Now we just need to formalize what that means and move cleanly into M13.

I’ll break this into two parts:

1. **What to do about the unmerged M12 branch**
2. **A concrete, Cursor-ready plan for M13 — CONTRACT-INPUT-SEMANTICS-001**

---

## 1️⃣ What to Do About the Unmerged M12 Branch

### Short answer

**Do not merge `m12-audit-remediation` into `main`.**
Instead, **archive it as an evidence branch** and explicitly supersede it with M13.

This preserves audit truthfulness and avoids polluting `main` with half-resolved semantics.

### Why this is correct

M12 did three *governance-correct* things:

* Hardened supply chain
* Enforced architectural boundaries
* **Surfaced a real, previously undefined contract**

But it also proved something crucial:

> The system cannot proceed without an explicit decision on dict-input semantics.

Merging M12 would either:

* Break CI on `main`, or
* Force an implicit semantic decision (which violates your governance rules)

So instead, we **freeze M12 as evidence**, not as state.

---

### Required Actions (One-Time)

Have Cursor do the following **before starting M13**:

#### A. Lock the M12 branch

```bash
git branch -m m12-audit-remediation m12-archive
git push origin m12-archive
```

Then:

* Mark `m12-archive` as **read-only** in GitHub
* Add a short note in the branch description:

  > “Archived evidence branch. Superseded by M13 — CONTRACT-INPUT-SEMANTICS-001.”

#### B. Add an explicit non-merge note

In `docs/milestones/PhaseA/M12/M12_summary.md`, append:

> **Branch Status:**
> The M12 implementation branch (`m12-audit-remediation`) was intentionally **not merged**.
> This is correct and expected: M12 surfaced a contract ambiguity that requires an explicit semantic decision, which is deferred to M13.

This closes the loop for any future reviewer.

---

## 2️⃣ M13 Plan — CONTRACT-INPUT-SEMANTICS-001

This is a **real milestone**, not a cleanup task. It defines how *every contract in RenaceCHESS accepts data*.

Below is a **Cursor-ready plan**.

---

# 📐 M13 — CONTRACT-INPUT-SEMANTICS-001

**Phase:** A — Post-PoC Hardening & Training Readiness
**Status:** Planned
**Predecessor:** M12 (closed, unmerged by design)

---

## 🎯 Milestone Objective

**Explicitly define, implement, and enforce the input semantics for all contract models**, resolving the ambiguity revealed in M12 regarding dict-based instantiation under Pydantic v2.

This milestone establishes **one canonical rule** for how contracts may be constructed — and makes CI green again **without weakening any gates**.

---

## 🔒 Problem Statement (Why M13 Exists)

M12 revealed that:

* Dict-based instantiation using snake_case keys was *implicitly accepted*
* This behavior was never specified as a contract
* Pydantic v2 correctly rejects this ambiguity
* Tests relied on undefined behavior

**This is not a bug.**
This is a missing contract.

M13 exists to **decide and codify** that contract.

---

## 🧭 Contract Decision (Must Be Explicit)

M13 must choose **one** of the following and enforce it everywhere:

### **Option A — Alias-Only Dict Inputs (Recommended)**

* Dict inputs **must use alias (camelCase) keys**
* Keyword arguments may use snake_case
* All dict normalization happens **at boundaries**
* Tests updated accordingly

**Pros:**

* Cleanest mental model
* Aligns with JSON / wire formats
* Avoids Pydantic internals entirely

**Cons:**

* Requires test updates (expected and acceptable)

> This is the recommended option based on M12 findings.

---

### Option B — Dual-Key Acceptance (Snake + Camel)

* Contracts accept both snake_case and camelCase dicts
* Requires explicit normalization everywhere
* Higher long-term complexity

**Not recommended** unless you have a strong backwards-compatibility requirement.

---

## 📦 Scope (In / Out)

### In Scope

1. **Formal contract decision**

   * Documented in `docs/contracts/CONTRACT_INPUT_SEMANTICS.md`

2. **Contract implementation**

   * Enforce the chosen rule consistently
   * Remove any remaining ambiguity

3. **Boundary normalization**

   * All feature extractors normalize inputs *before* model creation
   * No reliance on Pydantic interception

4. **Test suite alignment**

   * Update tests to comply with the explicit contract
   * CI must return to green with no weakened gates

5. **Deferred issue resolution**

   * Close `PYDANTIC-DICT-CONTRACT-001` in `DeferredIssuesRegistry.md`

---

### Out of Scope

* Training logic changes
* Model architecture changes
* New features or personalities
* Performance optimization

---

## 🛠️ Deliverables

| # | Deliverable                                        |
| - | -------------------------------------------------- |
| 1 | `CONTRACT_INPUT_SEMANTICS.md` (authoritative spec) |
| 2 | Updated contract constructors / boundaries         |
| 3 | Test suite updated to match contract               |
| 4 | CI green with all gates enforced                   |
| 5 | Deferred issue formally closed                     |
| 6 | M13 audit + summary docs                           |

---

## ✅ Exit Criteria

M13 may close **only when all are true**:

* CI is fully green
* No gates weakened or bypassed
* Dict-input semantics are explicit and documented
* All tests comply with the contract
* `PYDANTIC-DICT-CONTRACT-001` marked **Resolved**
* No reliance on Pydantic internal behavior

---

## 🔁 Relationship to M12

* M12 remains **closed and archived**
* M13 **supersedes** M12.1 exploratory work
* No rebasing or merging from `m12-archive`
* M13 starts clean from `main`

---

## 🚀 After M13

Once M13 closes, you are unblocked for:

* **M14 — Training Benchmark Pack**
* **M15 — Elo-Conditioned Guidance Pipeline**
* Phase B (training scale-up)

At that point, RenaceCHESS will have:

* Locked PoC
* Hardened infra
* Explicit contracts
* Green CI
* Zero hidden semantics

---

## Final Recommendation

You did the right thing by **not merging M12**.

Proceed exactly like this:

1. Archive M12 branch
2. Start M13 cleanly from `main`
3. Make the semantic decision explicit
4. Bring CI back to green *honestly*

If you want, next I can:

* Draft `CONTRACT_INPUT_SEMANTICS.md`
* Or generate the **exact Cursor handoff prompt** for M13 implementation

You’re navigating this at a very high level — this is how real platforms are built.
