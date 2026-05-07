# M38 — Summary

**Milestone:** M38 — Credential Scanner Hardening  
**Branch:** `m38-credential-scanner-hardening`  
**Status:** Implementation complete — **pending PR / merge approval**

## What shipped

- **Repo-local gitleaks config:** [`.gitleaks.toml`](../../../.gitleaks.toml) (conservative allowlist for docs/examples only).
- **Blocking CI:** [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) — **Security Scan** runs **Credential scan (gitleaks current tree)** using pinned **gitleaks** CLI **8.24.3** and `gitleaks dir .` (filesystem / current tree; **no** full-history requirement on PRs).
- **Manual / reporting:** [`.github/workflows/credential-scan-full-history.yml`](../../../.github/workflows/credential-scan-full-history.yml) — **`workflow_dispatch` only**, `fetch-depth: 0`, `gitleaks detect` (full git history). Not a required branch-protection job.
- **Documentation:** [`docs/security/CREDENTIAL_SCANNING.md`](../../../docs/security/CREDENTIAL_SCANNING.md); onboarding links updated.
- **DX:** `make secret-scan`, `make secret-scan-no-git` (graceful no-op message if `gitleaks` missing).
- **Tests:** [`tests/test_m38_credential_scanner_config.py`](../../../tests/test_m38_credential_scanner_config.py) (structural); `make test-fast` includes M35–M38 guardrails.

## Supply-chain note

- **gitleaks/gitleaks-action** `v2` → commit **`ff98106e4c7b2bc287b24eaf42907196329070c7`** (annotated tag `dcedce43c6f43de0b836d1fe38946645c9c638dc`). Recorded in `ci.yml` comment and this milestone. Blocking implementation uses **CLI + `dir`** per current-tree-only policy (see plan).

## Deferred / not in scope

- **M39** — Torch CVE upgrade or formal deferral review.
