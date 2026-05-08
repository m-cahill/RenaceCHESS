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
| Security Scan CI | `.github/workflows/ci.yml` — Torch `--ignore-vuln` lines removed; `pip-audit` command matches local gate |

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

---

## PR / Freeze

- **`release-dependency-freeze` bypass:** Maintainer must include **`RELDEPS-EXCEPTION`** token in PR body per existing workflow.

---

## Post-merge

Confirm **GitHub Actions** green on **`main`** after merge; rerun closeout narratives if CI numbers differ slightly from local (expected for coverage/OS).
