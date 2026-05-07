# Credential Scanning

## Purpose

M38 adds credential scanning as part of Phase G public release readiness. CI runs a **blocking** scan of the **current tracked repository tree** (filesystem) so obvious secrets do not enter public branches. **Full git history** scanning is **manual / reporting only** because history may contain pre-boundary material; any finding there requires an explicit maintainer decision (including whether **history rewrite** is appropriate — do not rewrite history without approval).

## What Is Scanned

| Scope | Where | Blocking? |
|-------|--------|-----------|
| Current tracked tree | `git archive HEAD` → `gitleaks dir` (CI **Security Scan**) | Yes (PR + `main`) |
| Full git history | Local `gitleaks detect` or manual workflow | No — reporting only |

- **CI** uses a pinned [Gitleaks](https://github.com/gitleaks/gitleaks) binary and repo-local [`.gitleaks.toml`](../../.gitleaks.toml).
- **Private boundary paths** (`docs/prompts/`, `docs/foundationdocs/`, `.cursorrules`) must remain **untracked** (M35). They are not part of the public Git tree and must not be scanned *through Git* in CI; keep them local only.

## Private Boundary

The following paths must remain local/private:

- `docs/prompts/`
- `docs/foundationdocs/`
- `.cursorrules`

Use:

```bash
python scripts/check_public_release_boundary.py
git ls-files docs/prompts docs/foundationdocs .cursorrules
```

The second command must print nothing (no tracked files under those paths).

## Local Use

Optional — requires [gitleaks](https://github.com/gitleaks/gitleaks) and a Unix-style environment for `mktemp` / `tar` (e.g. Git Bash on Windows):

```bash
make secret-scan
```

```bash
make secret-scan-no-git
```

Both targets unpack **`git archive HEAD`** into a temporary directory, then run **`gitleaks dir`** with the repo-root `.gitleaks.toml`. That matches CI (tracked files at `HEAD` only) and skips paths that exist only locally (for example `.venv/`).

To run manually:

```bash
scan_root="$(mktemp -d)"
git archive HEAD | tar -x -C "${scan_root}"
( cd "${scan_root}" && gitleaks dir . --redact --config .gitleaks.toml )
rm -rf "${scan_root}"
```

## Full History (Manual / Reporting Only)

**Do not** treat this as a substitute for the blocking CI gate.

Local (full clone):

```bash
gitleaks detect --source . --redact --config .gitleaks.toml
```

Maintainers may also run the GitHub Action **Credential Scan (Full History, Manual)** (`workflow_dispatch` only; not a required branch-protection check). If this surfaces historical issues (including possible pre-M35 paths), **stop and report** — remediation may require **rotate** credentials and/or an explicit decision on **history rewrite**; do not silently suppress with broad allowlists.

## If a Secret Is Found

1. Do not commit the secret.
2. Remove it from the working tree and index.
3. **Rotate** the credential if it was real.
4. If it exists in Git history, pause and request maintainer approval before any **history rewrite**.
5. Document the finding and resolution in the milestone audit.

## False Positives

False positives must use the narrowest possible allowlist entry in `.gitleaks.toml` (or fingerprint-based `.gitleaksignore` where appropriate) with a documented rationale. Do not add broad allowlists for real-looking tokens.

**Example (M38):** Frozen eval v2 JSONL shards under `data/frozen_eval_v2/shard_*.jsonl` contain `meta.recordKey` strings derived from position keys. Gitleaks `generic-api-key` can flag those lines; those shard paths are allowlisted with an explicit regex in `.gitleaks.toml` (see `M38_audit.md`).

The **test suite** (`tests/**/*.py` and `tests/fixtures/**`) embeds FEN / `recordKey` literals for deterministic tests; `generic-api-key` can match patterns like `key2 = "... b KQkq ..."`. Those paths are allowlisted. **Do not** store real credentials under `tests/`; reviewers should reject any non-test secret material there.

## CI vs `gitleaks-action` Pin

The tag `gitleaks/gitleaks-action@v2` resolves to commit `ff98106e4c7b2bc287b24eaf42907196329070c7` (recorded in `docs/milestones/PhaseG/M38/` closeout docs). That action invokes `gitleaks detect` with `--log-opts` over **git commit ranges**, which does not match this repository’s **current tracked tree** blocking policy. Blocking CI therefore uses the pinned **gitleaks CLI** (default **8.24.3**, aligned with the action’s bundled default), unpacks **`git archive HEAD`**, and runs **`gitleaks dir`** on that tree.

## Auditable Evidence

- On success: CI **Security Scan** job log shows the “Credential scan (gitleaks current tree)” step completing with exit code 0.
- On failure: the same step fails with **gitleaks** rule output (redacted). See “If a Secret Is Found” above.
