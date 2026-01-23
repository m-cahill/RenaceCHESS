You are generating a **Comprehensive Milestone Summary** for a software or systems project.

This summary is a **canonical project artifact**, not a retrospective narrative.
It must be suitable for:

- governance records
- phase reviews
- future audits
- onboarding new contributors
- anchoring subsequent milestones

The tone must be:

- neutral
- factual
- evidence-based
- non-promotional

Do NOT speculate.
Do NOT infer intent unless it is explicitly documented.
Do NOT include future plans beyond what is explicitly authorized by this milestone.

---

## REQUIRED INPUTS (You must infer these from context if not explicitly provided)

Identify and record:

- Project name
- Milestone identifier (ID + name)
- Phase (if applicable)
- Date range
- Status (Open / Closed / Blocked / Rolled Back)
- Baseline reference (prior milestone, phase exit, or commit)
- Scope boundaries (what was explicitly in-scope vs out-of-scope)

If any required input cannot be determined, explicitly mark it as **UNKNOWN**.

---

## OUTPUT FORMAT (STRICT — follow exactly)

# 📌 Milestone Summary — <Milestone ID>: <Milestone Name>

**Project:** <project name>  
**Phase:** <phase name or UNKNOWN>  
**Milestone:** <ID + descriptive name>  
**Timeframe:** <start date → end date>  
**Status:** <Closed / Open / Blocked / Rolled Back>  

---

## 1. Milestone Objective

State **why this milestone existed**.

- Describe the specific problem, gap, or risk it was meant to address
- Tie the objective to a prior baseline, decision, or phase goal
- Keep this section short and precise

> This section should answer:  
> “What would have been incomplete or unsafe if this milestone did not exist?”

---

## 2. Scope Definition

### In Scope

Explicitly list:

- components
- subsystems
- workflows
- contracts
- documents
- enforcement surfaces

### Out of Scope

Explicitly list:

- known exclusions
- deferred work
- intentionally untouched areas

If scope changed during execution, document **when and why**.

---

## 3. Work Executed

Summarize **what actually happened**, not what was planned.

Include:

- high-level actions (e.g., extraction, refactor, migration, hardening)
- counts where meaningful (files changed, modules affected, workflows updated)
- mechanical vs semantic changes (clearly distinguish)

Avoid implementation trivia unless it affects governance or risk.

---

## 4. Validation & Evidence

Describe **how correctness was verified**.

Include:

- tests run (CI, local, integration, manual)
- enforcement mechanisms involved (linters, gates, policies)
- failures encountered and how they were resolved
- evidence that validation is meaningful (not just “green”)

If validation is incomplete, explicitly state what is missing and why.

---

## 5. CI / Automation Impact

Document the milestone’s interaction with automation.

Include:

- workflows affected
- checks added, removed, or reclassified
- changes in enforcement behavior
- any signal drift observed

State whether CI:

- blocked incorrect changes
- validated correct changes
- failed to observe relevant risk

---

## 6. Issues & Exceptions

List all notable issues encountered:

For each issue:

- description
- root cause (if known)
- resolution status (resolved / deferred / unchanged)
- tracking reference (issue ID, registry entry, doc)

If no issues occurred, explicitly state:  

> “No new issues were introduced during this milestone.”

---

## 7. Deferred Work

Enumerate any deferred items touched or surfaced.

For each deferred item:

- why it was deferred
- whether it pre-existed the milestone
- whether its status changed as a result of this work

This section must not introduce new, untracked debt.

---

## 8. Governance Outcomes

State **what changed in the system’s governance posture** as a result of this milestone.

Examples:

- enforcement strengthened or restored
- ambiguity removed
- boundaries clarified
- risks reduced or isolated

This section should answer:  

> “What is now provably true that was not true before?”

---

## 9. Exit Criteria Evaluation

Evaluate the milestone against its original success criteria.

For each criterion:

- Met / Partially Met / Not Met
- evidence or rationale

If criteria were adjusted, document the change and justification.

---

## 10. Final Verdict

Provide a concise, authoritative conclusion.

Examples:

- “Milestone objectives met. Safe to proceed.”
- “Milestone partially complete; further work required before progression.”
- “Milestone invalidated; rollback recommended.”

This verdict should be unambiguous.

---

## 11. Authorized Next Step

Document **only what is explicitly authorized** as a result of this milestone.

- next milestone(s), phase transition, or pause
- any constraints or conditions on proceeding

If no next step is authorized, explicitly state that.

---

## 12. Canonical References

List all authoritative references used:

- commits
- pull requests
- documents
- issue trackers
- audit artifacts

These references must be sufficient for an external reviewer to reconstruct context.

---

## FORMATTING RULES

- Use markdown
- Prefer tables for inventories and comparisons
- Use bullet points over prose
- Mark UNKNOWN explicitly
- Do not embed opinions or future planning unless authorized

---

## COMPLETION RULE

Stop after generating the summary.
Do not propose improvements or additional work unless explicitly requested.
