# M36 — Public Release Documentation Onboarding

**Milestone:** M36  
**Branch:** `m36-public-release-docs-onboarding`  
**Category:** Documentation / Public Release Readiness / Contributor Onboarding  
**Scope:** Docs-first; no product code, schemas, models, proof-pack, or CI semantic changes.

## Objective

Raise public-readiness and contributor clarity by adding a **single entry path**: Getting Started, Contributing, and a documentation index keyed by audience (contributors, auditors, researchers, release reviewers).

## Driver

Input audit: [`M36_fullaudit.md`](M36_fullaudit.md) (full codebase audit) — **Docs 3.5/5**; documentation fragmented (264+ Markdown files); missing root `CONTRIBUTING.md` and consolidated “Start Here” onboarding.

## Deliverables

| Deliverable | Path |
|------------|------|
| Contributor guide | [`CONTRIBUTING.md`](../../../../CONTRIBUTING.md) |
| Getting started | [`docs/GETTING_STARTED.md`](../../../../docs/GETTING_STARTED.md) |
| Docs index | [`docs/DOCS_INDEX.md`](../../../../docs/DOCS_INDEX.md) |
| README updates | [`README.md`](../../../../README.md) |
| Milestone source of truth | [`renacechess.md`](../../../../renacechess.md) |
| Full audit (input artifact) | [`M36_fullaudit.md`](M36_fullaudit.md) |
| Guardrail test | [`tests/test_m36_docs_navigation.py`](../../../../tests/test_m36_docs_navigation.py) |
| Closeout | `M36_summary.md`, `M36_audit.md` (this folder) |

## Non-Goals

- No Makefile or setup scripts (M37).
- No credential scanner in CI (M38).
- No Torch / dependency upgrade (M39).
- No `cli.py` or `contracts/models.py` splits.
- No Phase G closeout document (premature until Phase G ends).

## Phase Placement

**Phase G — Public Release Readiness** opens with M36; Phases A–F remain closed.

## Public Release Roadmap (M36–M39)

| Milestone | Title | Primary target |
|-----------|--------|----------------|
| M36 | Public Release Documentation Onboarding | Docs |
| M37 | Public Release DX Shortcuts | DX |
| M38 | Credential Scanner Hardening | Security |
| M39 | Torch CVE Upgrade / Deferral Review | Security |

## Acceptance

See `M36_audit.md` checklist; must match items in milestone instructions (files exist, README links, boundary checks, tests green, CI green after PR).
