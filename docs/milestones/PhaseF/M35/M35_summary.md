# M35 Summary — Public Release Boundary Guardrails

**Status:** Implemented (pending merge / CI verification)  
**Phase:** Phase F — Public Release Hardening  

## Objective

Establish an auditable boundary so `docs/prompts/`, `docs/foundationdocs/`, and `.cursorrules` cannot be committed or reintroduced without CI failure.

## What Shipped

- **`.gitignore`** — Entries for all three private paths.  
- **Git index** — Previously tracked prompt, foundation-doc, and `.cursorrules` files removed from the index only (local copies unchanged).  
- **`scripts/check_public_release_boundary.py`** — Fails CI if `git ls-files` returns any tracked path under the boundary list.  
- **CI** — “Public release boundary check” step added to the existing **Lint and Format** job (after import-linter).  
- **`docs/release/PUBLIC_REPO_BOUNDARY.md`** — Public documentation and reviewer checklist.  
- **`tests/test_m35_public_release_boundary.py`** — Asserts `git ls-files` for the three roots is empty.  

## Credential Scanning / gitleaks

**gitleaks** was **not** available in the local toolchain at closeout verification time. Per M35 rules, credential scanning continues to rely on existing CI (**pip-audit**, **bandit**). Optional **gitleaks** hardening is deferred to **M36** if desired.

## Verification (local)

```text
python scripts/check_public_release_boundary.py   → exit 0
git ls-files docs/prompts docs/foundationdocs .cursorrules   → empty
pytest tests/test_m35_public_release_boundary.py   → pass
```

Full suite and CI: run on PR merge path per normal gates (`ruff`, `mypy`, `pytest` with coverage).

## Risks / Follow-Ups

- Historical milestone/doc text may cite paths under `docs/prompts/` or `docs/foundationdocs/` as references; clones will not contain those paths publicly. Editors may treat those citations as informational only — no M35 scrub was performed beyond the boundary.  
- **M36** may pick up toolchain items noted in audit (e.g. gitleaks, audit-score lift).
