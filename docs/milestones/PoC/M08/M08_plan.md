Below is a **Cursor-ready M11 plan** that (a) preserves the Post-Phase-XV discipline established through M10, and (b) adds the missing **Deferred Issues Registry** as a first-class governance artifact in `docs/audit/`, including a deterministic **backfill/backlog generation** pass from existing milestone docs.

This design follows well-established “issue log / risk register” practice: explicit owner, status, severity, mitigation/exit criteria, and continuous updates rather than “end-of-project cleanup.” ([Atlassian][1])

---

# M11_plan — Deferred Issues Registry + Governance Backfill

## Milestone Identity

* **Milestone:** M11
* **Title:** DEFERRED-REG-001 — Deferred Issues Registry + Backfill
* **Project:** R2L (README-to-Lab) — Post-Phase-XV Expansion
* **Branch:** `m11-deferred-registry`
* **Baseline:** M10 CLOSED (deterministic eval report + comparison preserved all guarantees)
* **Status Goal:** CLOSED / IMMUTABLE (CI green + audit artifacts)

---

## Objective

Create a **single source of truth** for deferred work and governance debt:

1. Add `docs/audit/DeferredIssuesRegistry.md` as the canonical registry
2. Generate a **deterministic backlog** of deferred items by scanning existing milestone docs (M00–M10)
3. Add lightweight enforcement so future milestones can’t “forget” deferred issues

This milestone adds **governance signal**, not product capability.

---

## Scope

### In Scope

* Registry file + schema/spec
* Backfill generator (scan existing milestone docs and seed registry)
* Minimal enforcement guardrail (tests / lint-level validation)
* Documentation updates to make “registry update” part of the milestone closeout checklist

### Out of Scope

* Converting registry into GitHub Issues / Jira
* Implementing any deferred items found
* Adding new required CI jobs (use existing test job unless strictly necessary)

---

## Design Principles

* **Deterministic & auditable:** same repo state → same registry output
* **Append-only governance:** entries never “disappear”; they move to *Resolved* with evidence
* **Explicit ownership & exit criteria:** each deferred item has an owner and an explicit closure condition (mirrors proven issue-log practice) ([Atlassian][1])
* **No weakened gates:** registry is a governance enhancement, not an escape hatch

---

## Deliverables

### A) Registry (human-readable, canonical)

Create: `docs/audit/DeferredIssuesRegistry.md`

**Required sections (fixed headings, canonical ordering):**

1. Purpose
2. Definitions (Deferred vs Known Issue vs Future Work)
3. Severity rubric (S0–S3)
4. Entry schema (fields + meaning)
5. Active Deferred Issues (table)
6. Resolved Deferred Issues (table)
7. Generation + update rules (how to add, how to close, how to defer explicitly)

**Entry fields (minimum):**

* `id` (stable, deterministic)
* `title`
* `status` (`active` | `resolved` | `superseded`)
* `severity` (`S0-blocking` | `S1-high` | `S2-medium` | `S3-low`)
* `introduced_in` (milestone, commit/PR if known)
* `deferred_to` (milestone target or “TBD”)
* `rationale` (why deferred)
* `exit_criteria` (what proves it is done)
* `evidence` (links to milestone doc paths; no URLs required)
* `owner` (team/role acceptable: “Maintainer”, “AI Agent”)

This matches common “issue log / risk register” expectations: status, priority/severity, owner, mitigation/closure criteria. ([Atlassian][1])

---

### B) Registry spec (machine-checkable)

Add: `docs/audit/deferred_issues_registry.v1.schema.json`

* JSON Schema for a machine-readable registry representation (see next item)
* Keep it minimal (don’t over-engineer)

Add: `docs/audit/deferred_issues_registry.v1.json`

* Canonical machine-readable registry used for deterministic checks
* `DeferredIssuesRegistry.md` is the human view; the `.json` is the enforcement substrate

---

### C) Deterministic backfill generator

Add a small tool:

* `tools/deferred_registry/backfill.py` (or similar)

**Behavior:**

* Scans:

  * `docs/milestones/**/M*_plan.md`
  * `docs/milestones/**/M*_run*.md`
  * `docs/milestones/**/M*_audit.md`
  * `docs/milestones/**/M*_summary.md`
* Extracts candidate deferrals via deterministic heuristics:

  * headings: `Deferred`, `Deferred Work`, `Out of Scope`, `Known Issues`, `Next Actions`
  * phrases: `defer`, `deferred to`, `explicitly deferred`, `follow-up`
* Produces:

  * `docs/audit/deferred_issues_registry.v1.json` (sorted keys, stable ordering)
  * and updates (or regenerates) the Active/Resolved tables in `DeferredIssuesRegistry.md`

**Determinism rules:**

* Stable sorting by `(introduced_in, severity, id)`
* Stable ID format:

  * `DIR-MXX-###` where `MXX` is the milestone the tool inferred
  * numbering is stable by sorted discovery order
* No timestamps in generated artifacts
* Canonical JSON serialization

---

### D) Enforcement guardrail (minimal but real)

Add tests under existing test job:

* `tests/test_deferred_registry_schema.py`

  * validates `docs/audit/deferred_issues_registry.v1.json` against schema
* `tests/test_deferred_registry_determinism.py`

  * runs backfill generator in a temp workspace and asserts byte-identical output
* Optional (if feasible without brittleness):

  * ensure every `DIR-*` referenced in milestone docs exists in the JSON registry

This aligns with the general principle of measurable exit criteria / objective readiness checks. ([Baeldung on Kotlin][2])

---

## Backfill Expectations

M10 explicitly stated **no deferred work**; the registry should reflect that (either no M10 entries, or explicit “none”).

For earlier milestones:

* If the scan finds no explicit deferrals, that’s acceptable: the registry starts sparse.
* If the scan finds ambiguous “future work,” classify as:

  * **Not Deferred** unless it was a *missed obligation* or a *known issue*
* If the scan finds genuine governance/quality debt, it becomes an **Active** entry with:

  * explicit exit criteria
  * a “deferred_to: TBD” if no target is clear

---

## Milestone Work Plan

### Step 1 — Create the registry skeleton

* Add `docs/audit/DeferredIssuesRegistry.md`
* Add `docs/audit/deferred_issues_registry.v1.schema.json`
* Add empty `docs/audit/deferred_issues_registry.v1.json` (valid, but no entries)

### Step 2 — Implement deterministic backfill generator

* Implement scanning + extraction + canonical output
* Run once to generate initial backlog from the repo

### Step 3 — Add enforcement tests

* Schema validation test
* Determinism test
* (Optional) reference integrity checks

### Step 4 — Wire governance into closeout norms

* Update the milestone closeout checklist doc (wherever your repo keeps it) to require:

  * “Registry updated OR explicitly ‘no deferred issues’ asserted”
* Add a short note in docs explaining how this supports audit posture

### Step 5 — CI verification

* Open PR
* Ensure CI green (no new required jobs)
* Fix any drift detected by tests

### Step 6 — Closeout artifacts

* `docs/milestones/M11/M11_summary.md`
* `docs/milestones/M11/M11_audit.md`
* Update toolcalls per your standard workflow

---

## Exit Criteria

M11 may be closed only when:

* ✅ `docs/audit/DeferredIssuesRegistry.md` exists and is populated (even if “none”)
* ✅ `docs/audit/deferred_issues_registry.v1.json` validates against schema
* ✅ Backfill generator is deterministic (tests prove it)
* ✅ CI green (all required checks)
* ✅ M11 audit + summary created
* ✅ Any discovered Active deferrals have explicit exit criteria and owner

---

## Guardrails

* Do **not** weaken Phase XV / Post-Phase-XV gates
* Do **not** create a “registry-only” carve-out that allows deferrals without evidence
* Prefer “Resolved with evidence” over deleting entries (append-only posture)
* If backfill touches many files, keep changes restricted to:

  * `docs/audit/*`
  * `tools/deferred_registry/*`
  * `tests/*`
  * `docs/milestones/M11/*`

---

## Handoff Note for Cursor

Implement M11 as a **governance milestone**:

* One PR
* Deterministic artifacts
* Tests proving determinism + schema validity
* Closeout docs generated after CI green

---

If you want M11 to also include a tiny “quality-of-life” enhancement related to M10 (e.g., report endpoints listing available comparisons), say so and I’ll fold it in—but the above plan is intentionally tight so it closes cleanly.

[1]: https://www.atlassian.com/software/jira/templates/issue-log?utm_source=chatgpt.com "Issue log template | Jira"
[2]: https://www.baeldung.com/cs/testing-entry-exit-criteria?utm_source=chatgpt.com "Entry and Exit Criteria in Software Testing"
