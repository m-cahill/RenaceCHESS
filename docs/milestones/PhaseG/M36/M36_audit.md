# M36 — Audit (Milestone Closeout)

This document is the **milestone** audit for M36. It is distinct from the input **full codebase audit** in [`M36_fullaudit.md`](M36_fullaudit.md), which documented overall repo health (e.g. Docs **3.5/5**, fragmentation, missing `CONTRIBUTING.md`) and informed this milestone.

## Observation

M36 is scoped as **documentation and navigation only**, with a small guardrail test. No changes to contracts, models, training, or proof-pack integrity.

## Acceptance Criteria

| Criterion | Evidence |
|-----------|----------|
| `CONTRIBUTING.md` at repo root | File present |
| `docs/GETTING_STARTED.md` exists | File present |
| `docs/DOCS_INDEX.md` exists with audience sections | File present |
| README links to GETTING_STARTED, CONTRIBUTING, DOCS_INDEX, PUBLIC_REPO_BOUNDARY | `tests/test_m36_docs_navigation.py` + README |
| CONTRIBUTING covers setup, verification, milestones, boundary, contracts, PR checklist | [`CONTRIBUTING.md`](../../../../CONTRIBUTING.md) |
| `tests/test_m36_docs_navigation.py` passes | `pytest tests/test_m36_docs_navigation.py --no-cov` |
| M35 boundary unchanged | `pytest tests/test_m35_public_release_boundary.py --no-cov`; `python scripts/check_public_release_boundary.py` |
| `renacechess.md` lists M36 + Phase G active + M36–M39 roadmap | Edits in `renacechess.md` |
| Milestone docs under Phase G | This folder |
| Full audit stored as input under Phase G | `M36_fullaudit.md` |
| No Phase F M36 path | `docs/milestones/PhaseF/M36/` removed |

## Interpretation

Onboarding is centralized without weakening release locks or teaching readers to bypass governance.

## Recommendation (post-close)

- After merge, fill in PR number, merge commit, and post-merge CI run in `renacechess.md`.
- M37: Makefile / setup shortcuts per roadmap.
