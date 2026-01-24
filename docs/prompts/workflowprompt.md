

🧭 CI / Workflow Analysis Prompt
================================

**(General, Enterprise-Grade, Project-Agnostic)**
Purpose
-------

Analyze a **single CI workflow run** and extract **ground-truth evidence** about the system’s correctness, safety, and readiness.

This analysis must:

* Treat CI as a **truth signal**, not a success badge

* Distinguish **signal** from **noise**

* Produce **audit-defensible conclusions**

* Be suitable for **release gating, milestone closure, or consumer-contract certification**

Do **not** assume failure.  
Do **not** assume green means “good.”  
Do **not** optimize for speed over correctness.

* * *

Inputs (Mandatory)
------------------

Before analysis begins, identify and record:

1. **Workflow identity**
   
   * Workflow name
   
   * Run ID
   
   * Trigger (PR, push, manual, scheduled)
   
   * Branch + commit SHA

2. **Change context**
   
   * Milestone / phase / objective (if applicable)
   
   * Declared intent of the change
   
   * Whether this run is:
     
     * exploratory
     
     * corrective
     
     * hardening
     
     * release-related
     
     * consumer-certification

3. **Baseline reference**
   
   * Last known “trusted green” commit or tag
   
   * Any explicit invariants that should not change relative to baseline

* * *

Step 1 — Workflow Inventory
---------------------------

Enumerate **all jobs and checks** executed in this run.

For each job, record:

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
| ----------- | --------- | ------- | --------- | ----- |

Explicitly identify:

* Which checks are **merge-blocking**

* Which checks are **informational**

* Which checks use `continue-on-error` (and why)

If any required checks are muted, weakened, or bypassed, **flag immediately**.

* * *

Step 2 — Signal Integrity Analysis
----------------------------------

For each major signal category, answer **what it truly measures**:

### A) Tests

* What test tiers ran (unit, integration, contract, e2e, smoke)?

* Are failures real correctness failures or test instability?

* Are any tests missing for the changed surface?

### B) Coverage

* What type of coverage is enforced (line, branch, trace, mutation)?

* Is coverage scoped correctly to what it claims to measure?

* Are exclusions documented and justified?

### C) Static / Policy Gates

* Linting, formatting, typing, architecture, security

* Do these gates enforce **current reality**, or legacy assumptions?

### D) Performance / Benchmarks (if present)

* Are benchmarks isolated from correctness signals?

* Do they measure regressions without contaminating coverage or tests?

* * *

Step 3 — Delta Analysis (Change Impact)
---------------------------------------

Analyze **what changed vs the baseline**:

1. Which files, packages, or contracts were modified?

2. Which CI signals are directly affected by those changes?

3. Are there **unexpected deltas** (new failures, new passes, silent skips)?

Explicitly call out:

* Any **signal drift**

* Any **coupling revealed by the change**

* Any **previously hidden dependency**

* * *

Step 4 — Failure Analysis (If Any)
----------------------------------

For each failure:

1. Classify the failure:
   
   * Correctness bug
   
   * Contract mismatch
   
   * Test fragility
   
   * CI misconfiguration
   
   * Environmental flake
   
   * Intentional policy violation

2. Determine:
   
   * Is this **in scope** for the current milestone?
   
   * Is it **blocking**, **deferrable**, or **informational**?

3. If deferring:
   
   * Specify **why**
   
   * Specify **where it must be tracked**
   
   * Specify **what guardrail prevents silent regression**

* * *

Step 5 — Invariants & Guardrails Check
--------------------------------------

Explicitly assert whether the following held true:

* Required CI checks remain enforced

* No semantic scope leakage (e.g., coverage measuring performance, benchmarks muting tests)

* Release / consumer contracts were not weakened

* Determinism and reproducibility (if required) were preserved

If any invariant was violated:

* Describe the violation

* Assess blast radius

* Recommend containment or rollback

* * *

Step 6 — Verdict
----------------

Provide a **clear, one-paragraph verdict**:

> **Verdict:**  
> (e.g., “This run is safe to merge,” “This run closes the milestone,”  
> “This run surfaces a real correctness issue,”  
> “This run is green but misleading.”)

Then explicitly state **one** of:

* ✅ Merge approved

* ⛔ Merge blocked

* ⚠️ Merge allowed with documented debt

* 🔁 Re-run required (with reason)

* * *

Step 7 — Next Actions (Minimal & Explicit)
------------------------------------------

List **only concrete next actions**, each with:

* Owner (human / AI / Cursor)

* Scope

* Whether it requires a **new milestone** or fits the current one

Avoid speculative refactors.  
Avoid “nice-to-have” cleanups.

* * *

Output Requirements
-------------------

The final analysis must be:

* Structured

* Auditable

* Copy-pasteable into:
  
  * milestone logs
  
  * audit documents
  
  * PR comments
  
  * release records

Tone should be **neutral, technical, and authoritative**.

* * *

### Design Notes (Why this prompt works)

This prompt is intentionally compatible with:

* **Release-locked systems**

* **Consumer-driven contract workflows**

* **AI-assisted development (Cursor, agents, copilots)**

* **Long-running, multi-phase programs**

It aligns naturally with:

* strict CI truthfulness

* separation of concerns between signals

* enterprise release discipline  

If you want, next I can:

* produce a **short “lite” version** for PR comments

* generate a **Cursor-specific system prompt** that enforces this format automatically

* or adapt this into a **milestone-closure audit template**
