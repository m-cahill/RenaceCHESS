# Torch Security Review

## Purpose

M39 (`Torch CVE Upgrade / Deferral Review`) reviews Torch CVE posture before public release: either merge a bounded dependency upgrade supported by CI evidence, or document a formal, time-bounded deferral.

## Current State Before M39

| Item | Value |
|------|--------|
| Torch constraint (`pyproject.toml`) | `torch~=2.2.0` |
| Typical resolved Torch (editable install) | 2.2.x (e.g. 2.2.2+cpu on CPU-only wheels) |
| Ignored advisories in CI (`pip-audit`) | `PYSEC-2025-41`, `PYSEC-2024-259`, `GHSA-3749-ghw9-m3mg`, `GHSA-887c-mr87-cxwp` |
| Related notes | See historical `TORCH-SEC-001` in `docs/milestones/PhaseD/M23/M23_audit.md`. Bandit skips `B614` for intentional `torch.save(state_dict)` usage. |

pip-audit (no ignores): reported multiple Torch findings on 2.2.x plus setuptools issues when an old setuptools was pulled transitively.

## Upgrade Attempt

| Item | Value |
|------|--------|
| Candidate constraint | `torch>=2.8.0,<3` — lowest coherent bound that clears the CI-ignored Torch set (`GHSA-887c-mr87-cxwp` is fixed at **2.8.0** per advisory metadata; other ignored IDs resolve at earlier 2.x lines). Resolver may pick latest in range (e.g. **2.11.0** at time of upgrade). Not pinned to PyPI-latest for its own sake. |
| Setuptools companion | `setuptools>=78.1.1,<82` — Torch declares `setuptools<82`; after raising Torch, `pip-audit` still flagged setuptools **65.5.0** until explicitly upgraded. This satisfies PySEC/GHSA fix versions without relaxing Torch’s `<82` ceiling. |
| Commands run | `pip install -e ".[dev]"`; `pip-audit --desc on --progress-spinner off`; full test suite `pytest -q --no-cov`; `ruff check` / `mypy src/renacechess`; `python scripts/check_public_release_boundary.py`. |
| Result | Torch advisories cleared in pip-audit; CI `pip-audit` step runs **without** `--ignore-vuln` for the former Torch set. setuptools cleared with explicit pin. |

## Decision

**Outcome A — upgrade accepted.**

Bounded dependency change only: no schema, contract registry, proof-pack, architecture, or training-logic edits.

## Evidence

| Gate | Status |
|------|--------|
| pytest (`--no-cov`) | Pass (maintainer run; Linux CI authoritative for coverage thresholds) |
| mypy (`src/renacechess`) | Pass |
| ruff (`check`; `format --check`) | Pass |
| pip-audit (no Torch ignores; setuptools addressed) | Pass — no known vulns reported for audited packages beyond local-project skip for editable name |
| Security Scan CI | Expected green on PR (**dependency + bandit steps** unchanged except pip-audit command) |

Bandit retains `--skip B614` for deliberate `torch.save` / serialization patterns unrelated to Torch version bumps.

## Compensating Controls

Not applicable under Outcome A in the TORCH-SEC-001 deferral sense: dependency versions align with audited fix ranges.

Ongoing posture (unchanged):

- No ingestion of arbitrary untrusted pickled checkpoints into production flows; training and eval use controlled paths.

## Next Review

- If pip-audit or upstream advisories change materially, revisit under a future security milestone or release window.
- **Next triggered review:** Torch major.minor bump or reopening TORCH-focused advisory debt in CI.
