

## 📘 M12_plan — POST-POC-HARDEN-001

**Project:** RenaceCHESS
**Phase:** A — Post-PoC Hardening & Training Readiness
**Milestone:** **M12 — Audit Remediation Pack**
**Status:** PLANNED
**Predecessor:** M11 (CLOSED / PoC LOCKED)

---

## 🎯 Milestone Objective

Address all **high-priority audit findings** and introduce guardrails that prevent architectural drift, without changing PoC semantics or model behavior.

---

## 🚫 Non-Goals (Explicit)

M12 **MUST NOT**:

* Change model outputs or training logic
* Modify PoC-locked schemas or contracts
* Introduce personalities or coaching logic
* Require retraining models

---

## 📦 Deliverables

### 1️⃣ Supply-Chain Hardening

* Pin all GitHub Actions to **commit SHAs**
* Review and lock dependency versions
* Add documentation for dependency update process

**Artifacts**

* Updated workflow files
* `docs/governance/supply_chain.md`

---

### 2️⃣ Architectural Boundary Enforcement

* Introduce module boundary rules:

  * prevent cross-layer imports (e.g., features → training internals)
* Add enforcement via lint or test rule

**Artifacts**

* Boundary configuration
* Boundary violation tests

---

### 3️⃣ CLI / Orchestration Seam Hardening

* Review CLI entry points
* Enforce:

  * no hidden side effects
  * no implicit training triggers
* Document CLI contract explicitly

**Artifacts**

* CLI contract doc
* Tests for CLI invariants

---

### 4️⃣ Audit Score Improvement Evidence

* Update audit documentation with:

  * resolved findings
  * before/after rationale
* No deferrals unless explicitly justified

**Artifacts**

* `M12_audit.md`
* Updated audit summary section

---

## 🧪 Validation & CI Requirements

* All existing CI gates must pass
* No coverage regressions
* New tests required for:

  * boundary enforcement
  * CLI invariants

---

## ✅ Exit Criteria

M12 is complete when:

* All high-priority audit findings are closed
* Supply-chain score is improved
* Architectural boundaries are enforced
* CI is green with no exceptions
* No PoC-locked semantics are modified

---

## 🏁 Follow-On

Upon M12 closure:

* Proceed to **M13 — PoC README + Runbook**
* Then **M14 — Training Benchmark Pack**

---

If you want next, I can:

* generate the **M12 Cursor clarifying-questions prompt**, or
* draft **Phase A overview docs** to sit above the milestones, or
* sketch **M14 benchmark harness** so it’s ready when M12 closes.

Just say the word.
