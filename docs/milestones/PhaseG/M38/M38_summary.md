# M38 — Summary

**Milestone:** M38 — Credential Scanner Hardening  
**Branch:** `m38-credential-scanner-hardening` (merged; branch deleted)  
**Status:** ✅ **Closed (MERGED)** — PR [#51](https://github.com/m-cahill/RenaceCHESS/pull/51)

## Merge record

| Field | Value |
|--------|--------|
| Merge method | Squash |
| Merge commit (`main`) | `14a386119d6f73b0d90c995d5eb7a29f1c2a4040` |
| Pre-merge CI (tip `0a7f7d6`) | [25527801670](https://github.com/m-cahill/RenaceCHESS/actions/runs/25527801670) — success |
| Post-merge `main` CI | [25529051353](https://github.com/m-cahill/RenaceCHESS/actions/runs/25529051353) — success |
| Credential step (post-merge) | **Security Scan** job [74931082954](https://github.com/m-cahill/RenaceCHESS/actions/runs/25529051353/job/74931082954) — **Credential scan (gitleaks current tree)** pass |

## What shipped

- **Blocking CI:** [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) — **Security Scan** runs **Credential scan (gitleaks current tree)** using pinned **gitleaks** CLI **8.24.3**, **`git archive HEAD`** unpacked to a temp dir, then **`gitleaks dir`** (tracked files at `HEAD` only; **no** full-history requirement on PRs).
- **Repo-local gitleaks config:** [`.gitleaks.toml`](../../../.gitleaks.toml) (narrow allowlists, including M30 frozen-eval shard false positives and test/FEN literals).
- **Manual / reporting:** [`.github/workflows/credential-scan-full-history.yml`](../../../.github/workflows/credential-scan-full-history.yml) — **`workflow_dispatch` only**, `fetch-depth: 0`, `gitleaks detect` (full git history). Not a required branch-protection job.
- **Documentation:** [`docs/security/CREDENTIAL_SCANNING.md`](../../../docs/security/CREDENTIAL_SCANNING.md); onboarding links updated.
- **DX:** `make secret-scan`, `make secret-scan-no-git` (graceful no-op message if `gitleaks` missing).
- **Tests:** [`tests/test_m38_credential_scanner_config.py`](../../../tests/test_m38_credential_scanner_config.py) (structural); `make test-fast` includes M35–M38 guardrails.

## Supply-chain note

- **gitleaks/gitleaks-action** `v2` → commit **`ff98106e4c7b2bc287b24eaf42907196329070c7`** (annotated tag `dcedce43c6f43de0b836d1fe38946645c9c638dc`). Recorded in `ci.yml` comment and this milestone. Blocking implementation uses **CLI + `git archive` + `gitleaks dir`** (see plan).

## Post-open fix (PR #51)

First CI run: **Security Scan** failed on `generic-api-key` false positives in `data/frozen_eval_v2/shard_*.jsonl` (`meta.recordKey`). Addressed with a **regex path allowlist** and switching the blocking scan to **`git archive HEAD` + `gitleaks dir`** (see `M38_audit.md`).

## Allowlist review (pre-merge)

- **Broad regexes for real tokens:** no — only example/dummy/fake helper strings.
- **Broad path suppressions:** yes, limited — `^tests/.*\.py$`, `^tests/fixtures/`, plus narrow docs and frozen-eval shard regex; rationale in [`CREDENTIAL_SCANNING.md`](../../../docs/security/CREDENTIAL_SCANNING.md).
- **Recommendation:** acceptable for M38; do not widen without review.

## Deferred / not in scope

- **M39** — Torch CVE upgrade or formal deferral review.
