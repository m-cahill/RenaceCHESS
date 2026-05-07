# M38 — Audit

**Milestone:** M38 — Credential Scanner Hardening  
**Branch:** `m38-credential-scanner-hardening`

## Checklist

- [x] `.gitleaks.toml` exists and extends defaults with a narrow allowlist.
- [x] **Security Scan** job includes a **blocking** credential step (**`git archive HEAD`** → **`gitleaks dir`**, pinned CLI **8.24.3**).
- [x] Full-history scan is **manual / reporting only** (`credential-scan-full-history.yml` + docs); **not** a required PR gate.
- [x] `docs/security/CREDENTIAL_SCANNING.md` covers purpose, scope, private boundary, local commands, incident response, false positives, and limitation note (history / **history rewrite**).
- [x] `Makefile` includes `secret-scan` and `secret-scan-no-git`; `secret-scan` **not** in `verify`.
- [x] `CONTRIBUTING.md` PR checklist mentions credential / **gitleaks** expectations.
- [x] `tests/test_m38_credential_scanner_config.py` passes; `test-fast` includes M35–M38 structural guardrails.
- [x] `renacechess.md` lists M38 (**active**) and Phase G still **active**.
- [x] No changes under `docs/prompts/`, `docs/foundationdocs/`, `.cursorrules` (untracked private paths).
- [x] No edits to `contracts/CONTRACT_REGISTRY_v1.json`, `proof_pack_v1/`, `src/renacechess/contracts/schemas/`, `src/renacechess/models/`.
- [ ] PR opened, CI green, merge by maintainer (post-implementation).

## Resolved references

| Reference | Value |
|-----------|--------|
| `gitleaks/gitleaks-action` `v2` (dereferenced) | `ff98106e4c7b2bc287b24eaf42907196329070c7` |
| `gitleaks/gitleaks-action` `v2` (annotated tag object) | `dcedce43c6f43de0b836d1fe38946645c9c638dc` |
| Blocking CI CLI | **gitleaks** **8.24.3** (matches gitleaks-action default in `v2` sources) |

## PR #51 — first CI run (credential scan false positives)

**Security Scan** failed on the first push: **`generic-api-key`** on `data/frozen_eval_v2/shard_*.jsonl` at `meta.recordKey` (FEN-derived identifiers, not API keys).

**Resolution (M38-scoped):**

1. **Narrow allowlist** in `.gitleaks.toml`: `^data/frozen_eval_v2/shard_[0-9]+\\.jsonl$` with rationale in `docs/security/CREDENTIAL_SCANNING.md`.
2. **CI / Makefile** unpack **`git archive HEAD`** into a temp directory, **`cd` into it**, and run **`gitleaks dir .`** so allowlist paths match repo-relative paths (for example `^data/frozen_eval_v2/...`).

**Commits:** `757eee4` (initial M38), `4eead77` (frozen-eval allowlist + `git archive`), then a follow-up fixing **allowlist application** by running **`gitleaks dir .` from inside the archive directory** (paths in logs were absolute under `/tmp/...`, so `^data/` did not match until the working directory was the archive root).

## Known limitation (explicit)

- **gitleaks-action** was **not** invoked as `uses:` because its `detect` + `--log-opts` path targets **git commit ranges**, not the **tracked-tree-at-HEAD** snapshot used for the blocking gate. The resolved action SHA is still **recorded** in CI comments and milestone docs for audit.

## Verification commands (local)

```bash
python scripts/check_public_release_boundary.py
git ls-files docs/prompts docs/foundationdocs .cursorrules
pytest tests/test_m38_credential_scanner_config.py tests/test_m37_dx_shortcuts.py tests/test_m36_docs_navigation.py tests/test_m35_public_release_boundary.py --no-cov
```

Optional (if `gitleaks` installed, Unix-style shell):

```bash
make secret-scan-no-git
```
