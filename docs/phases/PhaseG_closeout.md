# **Phase G Closeout — Public Release Readiness**

**Project:** RenaceCHESS  
**Phase:** G — Public Release Readiness  
**Status:** 🔒 **CLOSED**  
**Milestones:** M36–M39  
**Closeout Reference Date:** 2026-05-09  

---

## Purpose

Phase G prepared the repository for trustworthy public onboarding and auditability:

- Consolidated onboarding and documentation routing (M36)
- Executable DevEx shortcuts aligned with onboarding (M37)
- Blocking credential (**secret**) scanning aligned with the tracked public boundary (M38)
- **Torch CVE governance** resolved via bounded dependency upgrade (`M39`; see `docs/security/TORCH_SECURITY_REVIEW.md`)

No Phase G milestone modified frozen v1 contracts, the registry, or proof-pack semantics.

### Canonical closure on `main` (M39)

Torch CVE governance landed via **PR [#52](https://github.com/m-cahill/RenaceCHESS/pull/52)** (**squash**; merge commit **`ab74a2d75918f7aaf7b881468ccf06c64d2f5b2c`**). Authoritative **`main`** CI after merge: [25587676084](https://github.com/m-cahill/RenaceCHESS/actions/runs/25587676084) — **SUCCESS** (same gate family as Phase G predecessors: Security Scan, Lint, Type Check, Test, benchmarks, release locks). Detailed evidence: `docs/milestones/PhaseG/M39/M39_summary.md`, `docs/milestones/PhaseG/M39/M39_audit.md`, `docs/security/TORCH_SECURITY_REVIEW.md`.

---

## Milestones Completed

| Milestone | Deliverable Summary |
|-----------|---------------------|
| M36 | Consolidated onboarding path (Start Here flow, docs index, `CONTRIBUTING.md`) |
| M37 | `Makefile`, `setup_dev.py`, fast checks |
| M38 | gitleaks-blocking current-tree credential scan + policy docs |
| M39 | Torch/setuptools pins; removal of Torch-only `pip-audit` ignores; `TORCH_SECURITY_REVIEW.md` |

---

## What Remains After Phase G

Ongoing hygiene is embedded in CI and contributor workflows (boundary check, scanners, editable install). Future security work proceeds under normal milestones and governance; no standing Phase-G-only backlog assumed here.
