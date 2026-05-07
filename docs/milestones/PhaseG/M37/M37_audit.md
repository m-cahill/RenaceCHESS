# M37 — Audit (Milestone Closeout)

**Outcome:** **PASS / CLOSED**

## Closeout evidence

- **PR [#48](https://github.com/m-cahill/RenaceCHESS/pull/48)** merged to `main` (squash).
- **Merge commit:** `9e9c1478f866bf4d5e33d08087e2aa6f185b904b`
- **Post-merge `main` CI:** [run 25483024592](https://github.com/m-cahill/RenaceCHESS/actions/runs/25483024592) — **success** (all required jobs).
- **Public boundary invariant:** `python scripts/check_public_release_boundary.py` passes on `main`; `git ls-files docs/prompts docs/foundationdocs .cursorrules` is empty.
- **M37 DX tests:** `tests/test_m37_dx_shortcuts.py` passes; M35/M36 doc navigation tests still pass.
- **Scope:** No product/model/schema/proof-pack/contract-registry/release-lock behavioral or artifact changes in M37.

## Observation

M37 adds **DX-only** tooling so contributors can run boundary checks, lint, format, typecheck, and fast guardrail tests via `make` or documented fallbacks. No release artifacts or runtime behavior change.

## Acceptance Criteria

| Criterion | Evidence |
|-----------|----------|
| `Makefile` includes `help`, `install-dev`, `install` → `install-dev`, `lint`, `format-check`, `type`, `test`, `test-fast`, `docs-check`, `boundary-check`, `verify`, `clean-coverage` | [`Makefile`](../../../../Makefile); [`tests/test_m37_dx_shortcuts.py`](../../../../tests/test_m37_dx_shortcuts.py) |
| `scripts/setup_dev.py` conservative by default; `--install` runs pip editable dev | Script + structural test |
| CONTRIBUTING / GETTING_STARTED reference shortcuts | Doc tests in `test_m37_dx_shortcuts.py` |
| DOCS_INDEX points to Makefile + setup helper | [`docs/DOCS_INDEX.md`](../../../../docs/DOCS_INDEX.md) |
| M35/M36 guardrail tests still pass | `pytest tests/test_m35_public_release_boundary.py tests/test_m36_docs_navigation.py --no-cov` |
| Public boundary script passes | `python scripts/check_public_release_boundary.py` |
| `renacechess.md` lists M37; Phase G active | Table + M37 details block |
| Milestone docs under Phase G | This folder |

## Interpretation

Shortcuts mirror CI separation (lint vs format) for local signals; `verify` is convenience only and does not replace full `pytest` + `lint-imports` documented in CONTRIBUTING.

## Recommendation

Proceed to **M38** (credential scanner hardening) per Phase G roadmap when approved.
