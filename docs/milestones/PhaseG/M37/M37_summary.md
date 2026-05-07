# M37 — Summary

**Milestone:** Public Release DX Shortcuts  
**Status:** ✅ Closed (merged)  
**Phase:** G — Public Release Readiness  

## Closeout record

| Field | Value |
|-------|--------|
| **PR** | [#48](https://github.com/m-cahill/RenaceCHESS/pull/48) |
| **Merge method** | Squash |
| **Implementation commit (branch tip)** | `cef888c3179ffdae00c6599fe4a614b9aa8ddd4e` |
| **Merge commit on `main`** | `9e9c1478f866bf4d5e33d08087e2aa6f185b904b` |
| **Merged at** | 2026-05-07 (UTC) |
| **Pre-merge PR CI** | [25481712932](https://github.com/m-cahill/RenaceCHESS/actions/runs/25481712932) — success |
| **Post-merge `main` CI** | [25483024592](https://github.com/m-cahill/RenaceCHESS/actions/runs/25483024592) — success |
| **Boundary script on `main`** | pass (`python scripts/check_public_release_boundary.py`) |
| **Private path tracking on `main`** | empty (`git ls-files` for boundary paths) |
| **M37 guardrail tests on `main`** | pass (`pytest tests/test_m37_dx_shortcuts.py … --no-cov`) |
| **`setup_dev.py` default** | prints guidance only; no install without `--install` |
| **`make` on maintainer Windows checkout** | not on PATH; Makefile validated via `tests/test_m37_dx_shortcuts.py` and Linux CI jobs |

## What Shipped

- [`Makefile`](../../../../Makefile) — `install` aliases `install-dev`; split `lint` vs `format-check`; `test-fast`, `docs-check`, `boundary-check`, `verify`, `clean-coverage`; `demo` writes `demo.json` when `tests/data/sample.pgn` exists (otherwise prints guidance). Existing `clean` retained.
- [`scripts/setup_dev.py`](../../../../scripts/setup_dev.py) — prints recommended venv steps; `python scripts/setup_dev.py --install` runs editable dev install in the current interpreter.
- [`tests/test_m37_dx_shortcuts.py`](../../../../tests/test_m37_dx_shortcuts.py) — structural checks for Makefile targets, setup script, and onboarding doc references.
- [`README.md`](../../../../README.md), [`CONTRIBUTING.md`](../../../../CONTRIBUTING.md), [`docs/GETTING_STARTED.md`](../../../../docs/GETTING_STARTED.md), [`docs/DOCS_INDEX.md`](../../../../docs/DOCS_INDEX.md) — shortcut discovery and non-`make` fallbacks.
- [`renacechess.md`](../../../../renacechess.md) — M37 milestone row and details (closeout commit records merge + CI).

## What Did Not Change

- No `src/renacechess/` product logic, schemas, contracts, proof-pack payloads, or CI workflow semantics.
- No credential scanner or dependency upgrades beyond documented dev install path.

## Next

- **M38:** Credential scanner hardening (`gitleaks` or equivalent in CI), per Phase G roadmap.
