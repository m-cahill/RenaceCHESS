# **Phase G Closeout — Public Release Readiness**

**Project:** RenaceCHESS  
**Phase:** G — Public Release Readiness  
**Status:** 🔒 **CLOSED**  
**Milestones:** M36–M39 (plus **M40** — final public release candidate review appended after Phase G closeout; no feature scope reopened)

**Closeout Reference Date:** 2026-05-09 (**M40** merged to `main` — see `docs/milestones/PhaseG/M40/` and canonical closure below)  

---

## Purpose

Phase G prepared the repository for trustworthy public onboarding and auditability:

- Consolidated onboarding and documentation routing (M36)
- Executable DevEx shortcuts aligned with onboarding (M37)
- Blocking credential (**secret**) scanning aligned with the tracked public boundary (M38)
- **Torch CVE governance** resolved via bounded dependency upgrade (`M39`; see `docs/security/TORCH_SECURITY_REVIEW.md`)

No Phase G milestone modified frozen v1 contracts, the registry, or proof-pack semantics.

### M40 — Final public release candidate review (after M39)

**M40** was added as a **governance-only** public release candidate review after the Phase G feature milestones closed. It does not reopen Phase G for product work. Evidence and verdict: `docs/milestones/PhaseG/M40/M40_public_release_candidate_review.md`.

### Canonical closure on `main` (M40)

Public release candidate review landed via **PR [#54](https://github.com/m-cahill/RenaceCHESS/pull/54)** (**squash**; merge commit **`f175c8999a70772c6a2df0246cc92efd17c73097`**). Final PR head: **`e65fc462178540f7316b4d3bac318141d77d31ec`**. Pre-merge PR CI: [25612956250](https://github.com/m-cahill/RenaceCHESS/actions/runs/25612956250) — **SUCCESS**. Authoritative **`main`** CI after merge: [25614956502](https://github.com/m-cahill/RenaceCHESS/actions/runs/25614956502) — **SUCCESS**. **Verdict:** `APPROVE_PUBLIC_RC`. **M40 does not authorize** tag, package publish, GitHub Release, or repository visibility change — **M41** or explicit release command only.

Detailed evidence: `docs/milestones/PhaseG/M40/M40_summary.md`, `M40_run1.md`, `M40_public_release_candidate_review.md`.

---

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
| M40 | Public release candidate review (boundary, artifacts, verification, claim safety) — `docs/milestones/PhaseG/M40/` |

---

## What Remains After Phase G

Ongoing hygiene is embedded in CI and contributor workflows (boundary check, scanners, editable install). **Public release action** (tag, package publish, GitHub Release, visibility) is **not** implied by Phase G or M40 — use **M41** or an explicit release command. Future security work proceeds under normal milestones and governance.
