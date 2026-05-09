# **Phase G Closeout — Public Release Readiness**

**Project:** RenaceCHESS  
**Phase:** G — Public Release Readiness  
**Status:** 🔒 **CLOSED**  
**Milestones:** M36–M39  
**Closeout Reference Date:** 2026-05-08  

---

## Purpose

Phase G prepared the repository for trustworthy public onboarding and auditability:

- Consolidated onboarding and documentation routing (M36)
- Executable DevEx shortcuts aligned with onboarding (M37)
- Blocking credential (**secret**) scanning aligned with the tracked public boundary (M38)
- **Torch CVE governance** resolved via bounded dependency upgrade (`M39`; see `docs/security/TORCH_SECURITY_REVIEW.md`)

No Phase G milestone modified frozen v1 contracts, the registry, or proof-pack semantics.

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
