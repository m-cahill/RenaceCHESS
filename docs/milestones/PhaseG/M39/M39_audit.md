# M39 Audit — Torch CVE Upgrade / Deferral Review

**Phase:** G — Public Release Readiness  
**Status:** ✅ Complete (**Outcome A**)  
**Decision driver:** Eliminate Torch-only `pip-audit` ignores with a bounded dependency upgrade documented in **`docs/security/TORCH_SECURITY_REVIEW.md`**.

---

## Verification Matrix

### Dependency & security tooling

| Check | Evidence |
|-------|----------|
| pip-audit (no Torch ignores post-change) | Local run: exit 0, no known vulns listed for audited installs after `pip install -e ".[dev]"`; local-project editable entry skipped per pip-audit default |
| Security Scan CI | `.github/workflows/ci.yml` — Torch `--ignore-vuln` lines removed; **Test** job uses CPU-only Torch reinstall (see `TORCH_SECURITY_REVIEW.md` CI section) |

### Quality gates

| Check | Evidence |
|-------|----------|
| ruff check / format | Maintainer run: pass (`--fix`/`format` normalized unused imports surfaced during check) |
| mypy `src/renacechess` | Pass |
| pytest `--no-cov` | Full suite pass (1044 passed, 1 skipped) |

### Scope guardrail

No changes to immutable contracts (`contracts/CONTRACT_REGISTRY_v1.json`, v1 schemas, `proof_pack_v1/`), no model-architecture edits, no new training behavior.

Companion changes:

- Unused-import cleanup in **`src/renacechess/contracts/registry.py`** (`typing.Any`), **`tests/test_m34_contract_registry.py`** (`pytest`) surfaced by lint during verification — aligns with enforced Ruff CI.

### CI / Test job (PR #52)

**Test** job failed on first push: CUDA-linked Torch on `ubuntu-latest` (`libtorch_cuda.so` / NCCL). Addressed by reinstalling Torch from **`https://download.pytorch.org/whl/cpu`** after `pip install -e ".[dev]"`, using the `torch` line from the **current checkout’s** `pyproject.toml` (baseline vs PR head stay consistent); **setuptools** is then re-installed from PyPI using the **`setuptools`** line from the same file so the CPU-index transitive pin does not violate **`setuptools>=78.1.1,<82`**.

---

## PR / Freeze

- **`release-dependency-freeze` bypass:** Maintainer must include **`RELDEPS-EXCEPTION`** token in PR body per existing workflow.

## Post-merge (`main`)

- **Merge:** squash [#52](https://github.com/m-cahill/RenaceCHESS/pull/52) → **`ab74a2d75918f7aaf7b881468ccf06c64d2f5b2c`** (2026-05-09 UTC).
- **`main` CI:** [25587676084](https://github.com/m-cahill/RenaceCHESS/actions/runs/25587676084) — **SUCCESS** (**Security Scan** job incl. pip-audit / credential scan / bandit; **Test** with CPU-only Torch reinstall; **Release Dependency Freeze** / **Contract Freeze** / **Proof Pack Verification** pass).

**Torch import (Linux Test job diagnostic on PR CI):** `torch 2.11.0+cpu`, **`cuda_available` false** ([25537724848](https://github.com/m-cahill/RenaceCHESS/actions/runs/25537724848) logs).

**Maintainer spot-check:** boundary script pass; untracked private paths; **`pip-audit`** clean aside from editable skip; Phase G guardrail pytest subset pass (expected OS variance vs Linux for full suite counts).
