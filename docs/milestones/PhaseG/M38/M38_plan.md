# M38 — Credential Scanner Hardening

**Milestone:** M38  
**Branch:** `m38-credential-scanner-hardening`  
**Phase:** G — Public Release Readiness (**active**)  
**Category:** Security / supply chain / public release readiness  
**Scope:** Narrow CI/security hardening; **no** product behavior, schema, contract registry, or proof-pack changes.

## Objective

Add a **blocking** CI credential scan over the **current tracked repository tree** and document optional **manual / reporting** full-history scanning, aligned with M35’s public/private boundary.

## Locked policy (implementation)

| Gate | Mode |
|------|------|
| PR / `main` **Security Scan** | **Tracked files at `HEAD`** (`git archive HEAD` → `gitleaks dir`; pinned CLI **8.24.3**) |
| Full git history | **`workflow_dispatch`** workflow + documented local `gitleaks detect`; **not** a required branch check |

**gitleaks/gitleaks-action@v2** dereferenced commit SHA (supply-chain record): `ff98106e4c7b2bc287b24eaf42907196329070c7` (annotated tag `dcedce43c6f43de0b836d1fe38946645c9c638dc`). The action invokes `detect` with `--log-opts` over **git commit ranges**; it is **not** used for the blocking gate so CI matches the current-tree-only policy.

## Deliverables

| Deliverable | Path |
|------------|------|
| Gitleaks config | [`.gitleaks.toml`](../../../../.gitleaks.toml) |
| CI blocking scan | [`.github/workflows/ci.yml`](../../../../.github/workflows/ci.yml) (`Security Scan` job) |
| Manual full-history workflow | [`.github/workflows/credential-scan-full-history.yml`](../../../../.github/workflows/credential-scan-full-history.yml) |
| Contributor / auditor doc | [`docs/security/CREDENTIAL_SCANNING.md`](../../../../docs/security/CREDENTIAL_SCANNING.md) |
| Structural tests | [`tests/test_m38_credential_scanner_config.py`](../../../../tests/test_m38_credential_scanner_config.py) |
| Local shortcuts | [`Makefile`](../../../../Makefile) |
| Onboarding updates | [`CONTRIBUTING.md`](../../../../CONTRIBUTING.md), [`docs/GETTING_STARTED.md`](../../../../docs/GETTING_STARTED.md), [`docs/DOCS_INDEX.md`](../../../../docs/DOCS_INDEX.md), [`README.md`](../../../../README.md) |
| Source of truth | [`renacechess.md`](../../../../renacechess.md) |
| Closeout | `M38_summary.md`, `M38_audit.md` (this folder) |

## Non-goals

- No Torch / dependency upgrade (M39).
- No Git history rewrite.
- No scanning, quoting, or committing contents from `docs/prompts/`, `docs/foundationdocs/`, `.cursorrules`.
- No weakening `pip-audit`, `bandit`, release gates, overlap-set coverage, or public boundary checks.

## Acceptance

See `M38_audit.md`.
