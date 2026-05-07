# M35 Summary — Public Release Boundary Guardrails

**Status:** Closed / merged (see below)  
**Phase:** Phase F — Public Release Hardening  

## Closeout (GitHub)

```text
Status: Closed / merged
PR: #43
Merge method: squash
Merge commit: 0273dba28581d3e7439aa75fd433d0e49e3b81c0
Main head SHA: 0273dba28581d3e7439aa75fd433d0e49e3b81c0
Post-merge main CI: success
Main CI run: 25468691726
Boundary script on main: pass
Private path tracking on main: empty
Boundary doc: docs/release/PUBLIC_REPO_BOUNDARY.md
```

**Context:** M36 (PR #44) pytest security hotfix and PR #45 CI-only pytest-cov/coverage stabilization landed on `main` before M35 #43 merged; they unblocked and stabilized CI and are not part of M35’s scope.

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

**gitleaks** was **not** added in M35. Credential scanning continues to rely on existing CI (**pip-audit**, **bandit**). Optional **gitleaks** hardening remains a candidate for a **future** security milestone if desired.

## Verification (local)

```text
python scripts/check_public_release_boundary.py   → exit 0
git ls-files docs/prompts docs/foundationdocs .cursorrules   → empty
pytest tests/test_m35_public_release_boundary.py   → pass
```

Full suite: exercised via normal PR and post-merge `main` CI gates (`ruff`, `mypy`, `pytest` with coverage).

## Risks / Follow-Ups

- Historical milestone/doc text may cite paths under `docs/prompts/` or `docs/foundationdocs/` as references; clones will not contain those paths publicly. Editors may treat those citations as informational only — no M35 scrub was performed beyond the boundary.
