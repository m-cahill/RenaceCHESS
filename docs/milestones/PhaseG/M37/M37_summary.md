# M37 — Summary

**Milestone:** Public Release DX Shortcuts  
**Status:** 🚧 Open PR / in review (update to ✅ Closed after merge and post-merge CI)  
**Phase:** G — Public Release Readiness  

## What Shipped

- [`Makefile`](../../../../Makefile) — `install` aliases `install-dev`; split `lint` vs `format-check`; `test-fast`, `docs-check`, `boundary-check`, `verify`, `clean-coverage`; `demo` writes `demo.json` when `tests/data/sample.pgn` exists (otherwise prints guidance). Existing `clean` retained.
- [`scripts/setup_dev.py`](../../../../scripts/setup_dev.py) — prints recommended venv steps; `python scripts/setup_dev.py --install` runs editable dev install in the current interpreter.
- [`tests/test_m37_dx_shortcuts.py`](../../../../tests/test_m37_dx_shortcuts.py) — structural checks for Makefile targets, setup script, and onboarding doc references.
- [`README.md`](../../../../README.md), [`CONTRIBUTING.md`](../../../../CONTRIBUTING.md), [`docs/GETTING_STARTED.md`](../../../../docs/GETTING_STARTED.md), [`docs/DOCS_INDEX.md`](../../../../docs/DOCS_INDEX.md) — shortcut discovery and non-`make` fallbacks.
- [`renacechess.md`](../../../../renacechess.md) — M36 closed (PR #47); M37 active row and details.

## What Did Not Change

- No `src/renacechess/` product logic, schemas, contracts, proof-pack payloads, or CI semantics.
- No credential scanner or dependency upgrades beyond documented dev install path.

## Post-merge

After merge: confirm `main` CI green; set M37 status and completion metadata in `renacechess.md`; fill PR URL and CI run in this summary and `M37_audit.md`.
