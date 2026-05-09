# M39 Summary — Torch CVE Upgrade / Deferral Review

**Milestone:** M39  
**Status:** ✅ Complete (Outcome A — upgrade accepted)  
**Branch:** `m39-torch-cve-upgrade-review` → **`main`** (squash [#52](https://github.com/m-cahill/RenaceCHESS/pull/52))  
**Date:** 2026-05-09 (merged)  

---

## Decision

**Outcome A — upgrade accepted.**

- Torch bound raised to **`torch>=2.8.0,<3`** (clears GHSA minimum 2.8.0; resolver installed **2.11.0+cpu** in validation environment — latest satisfying the range).
- **`setuptools>=78.1.1,<82`** ensures `pip-audit` passes alongside Torch’s `setuptools<82` requirement after the upgrade removed the old transitive pin.
- **Removed** `--ignore-vuln` entries for Torch from `.github/workflows/ci.yml`; **pip-audit** runs with no Torch-specific ignores.

## Key Files

| File | Change |
|------|--------|
| `pyproject.toml` | Torch range; setuptools companion pin |
| `.github/workflows/ci.yml` | Security Scan pip-audit; Test job reinstalls Torch from **`https://download.pytorch.org/whl/cpu`** (spec from `pyproject.toml`) |
| `docs/security/TORCH_SECURITY_REVIEW.md` | Before/after, evidence, decision |
| `tests/test_m39_torch_security_docs.py` | Structural doc guards |
| `docs/milestones/PhaseG/M39/*` | Plan, summary, audit |
| `renacechess.md` | Milestone table + Phase G closeout |

## Verification (local Maintainer Run)

Linux CI remains authoritative for **coverage thresholds** and integration.

- `python scripts/check_public_release_boundary.py` — pass  
- `pip-audit --desc on --progress-spinner off` — no known vulns (after pins)  
- `ruff check .`, `ruff format --check .` — pass  
- `mypy src/renacechess` — pass  
- `pytest -q --no-cov` — pass  

## CI (GitHub Actions)

PR #52 follow-up: default Linux wheels for recent Torch can be CUDA-linked and fail to import on `ubuntu-latest` (NCCL symbol errors). The **Test** job (including PR baseline/head coverage installs) force-reinstalls Torch from the **official CPU index** using the **same** PEP 508 spec as the checked-out `pyproject.toml`, then restores **`setuptools`** from PyPI per `pyproject.toml` — CI install policy only; not a model semantic change. See `docs/security/TORCH_SECURITY_REVIEW.md`.

## Merge closure (`main`)

| Item | Evidence |
|------|----------|
| **PR #52** (squash) | Merge commit **`ab74a2d75918f7aaf7b881468ccf06c64d2f5b2c`** (merged 2026-05-09 UTC) |
| **PR tip CI** | [25537724848](https://github.com/m-cahill/RenaceCHESS/actions/runs/25537724848) — **success** (Security Scan incl. pip-audit without Torch ignores; **Test** with CPU Torch + setuptools restore; release gates) |
| **Post-merge `main` CI** | [25587676084](https://github.com/m-cahill/RenaceCHESS/actions/runs/25587676084) (`databaseId`: **25587676084**) — **success**, head **`ab74a2d…`** |

**Maintainer verification on `main` (post-merge):** `scripts/check_public_release_boundary.py` pass; `git ls-files` on private prefixes empty; guardrail pytest subset pass; **`pip-audit`** no known vulns (editable skip as usual).

## Merge Note (historical — PR gate)

Sanctioned `pyproject.toml` change requires **`RELDEPS-EXCEPTION`** in the PR description body for **`release-dependency-freeze`** CI (#52 included token).
