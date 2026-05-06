# M35 — Public Release Boundary Guardrails

**Phase:** Phase F — Public Release Hardening  
**Branch:** `m35-public-release-boundary-guardrails`  
**Title:** Public Release Boundary Guardrails  
**Scope:** Narrow, pre-release safety — prevent accidental commit of three private surfaces.

## Objective

Ensure these paths exist only locally — never tracked in Git:

- `docs/prompts/`
- `docs/foundationdocs/`
- `.cursorrules`

## Implementation

1. `.gitignore` entries for those paths  
2. `git rm --cached …` where previously tracked  
3. `scripts/check_public_release_boundary.py` + CI step in lint job  
4. `docs/release/PUBLIC_REPO_BOUNDARY.md`  
5. `tests/test_m35_public_release_boundary.py`  

## Non-Goals

Per governance: no history rewrite, no schema/model/eval/proof-pack changes, no release-lock weakening, no gitleaks as new dependency unless already present tool-wide.
