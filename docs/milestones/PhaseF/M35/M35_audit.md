# M35 Audit — Public Release Boundary Guardrails

## Scope Confirmation

| Requirement | Verified |
|-------------|----------|
| `.gitignore` contains `docs/prompts/`, `docs/foundationdocs/`, `.cursorrules` | Yes |
| `git ls-files docs/prompts docs/foundationdocs .cursorrules` empty after change | Yes (tracked-list source of truth) |
| `scripts/check_public_release_boundary.py` exists; exits non-zero if tracked | Yes (script exits 1 if any stdout from `git ls-files`) |
| CI runs boundary check inside existing lint job | Yes (Lint and Format workflow) |
| `docs/release/PUBLIC_REPO_BOUNDARY.md` documents boundary | Yes |
| Local private files not deleted | Yes (presence checked post–`git rm --cached`) |
| No schemas, contracts, model behavior, training/eval logic, proof-pack semantics changed | Yes (diff limited to governance/CI/script/test/docs/release + index removals + ignore) |
| No release-lock job semantics weakened | Yes |

## Evidence (commands)

- Tracking source of truth before index removal: `git ls-files docs/prompts docs/foundationdocs .cursorrules` enumerated prior tracked files (prompts subset, foundationdocs tree, `.cursorrules`).  
- Post-change: same command returns empty; `python scripts/check_public_release_boundary.py` prints success and exits `0`.

## Credential / Secret Hygiene

- **gitleaks:** Not installed in local environment at verification; **not** added as CI or package dependency per M35 non-goals.  
- Existing CI **Security Scan** job (pip-audit, bandit) unchanged.

## Out of Scope (Confirmed Not Done)

- Git history rewrite  
- Broad repo scrub  
- New security frameworks  

## Recommendation

Treat M35 as **complete for merge** after GitHub Actions confirms green on the branch PR.
