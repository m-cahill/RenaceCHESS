# M37 — Public Release DX Shortcuts

**Milestone:** M37  
**Branch:** `m37-public-release-dx-shortcuts`  
**Category:** Developer Experience / Public Release Readiness  
**Scope:** Low-risk tooling and documentation; no product behavior changes.

## Objective

Make the M36 public onboarding path immediately actionable with local shortcuts: `Makefile` targets, a conservative `scripts/setup_dev.py`, and doc links.

## Driver

M36 audit and Phase G roadmap: onboarding docs exist; next step is executable commands without memorization.

## Deliverables

| Deliverable | Path |
|------------|------|
| Makefile (extended) | [`Makefile`](../../../../Makefile) |
| Setup helper | [`scripts/setup_dev.py`](../../../../scripts/setup_dev.py) |
| Structural tests | [`tests/test_m37_dx_shortcuts.py`](../../../../tests/test_m37_dx_shortcuts.py) |
| README / CONTRIBUTING / GETTING_STARTED / DOCS_INDEX | Updated |
| Milestone source of truth | [`renacechess.md`](../../../../renacechess.md) |
| Closeout | `M37_summary.md`, `M37_audit.md` (this folder) |

## Non-Goals

- No application or model behavior changes.
- No schema, contract registry, or proof-pack edits.
- No `gitleaks` (M38) or Torch upgrade (M39).
- No `cli.py` / `contracts/models.py` splits.
- No new heavy required CI jobs.

## Phase Placement

**Phase G — Public Release Readiness** (active).

## Verification (local)

```bash
python scripts/check_public_release_boundary.py
git ls-files docs/prompts docs/foundationdocs .cursorrules
pytest tests/test_m37_dx_shortcuts.py tests/test_m36_docs_navigation.py tests/test_m35_public_release_boundary.py --no-cov
python scripts/setup_dev.py
make help
make verify
```

If `make` is unavailable, rely on structural tests and plain commands in CONTRIBUTING.
