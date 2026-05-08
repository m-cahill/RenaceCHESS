# M39 Plan — Torch CVE Upgrade / Deferral Review

**Milestone:** M39  
**Branch:** `m39-torch-cve-upgrade-review`  
**Phase:** G — Public Release Readiness  
**Category:** Security / Dependency Governance  

## Objective

Resolve or formally govern remaining Torch CVE debt reflected in CI `pip-audit --ignore-vuln` before public release:

1. Inventory current Torch constraint, resolved version, and ignored IDs.
2. Run `pip-audit` with and without ignores in a CI-like environment.
3. Attempt the lowest bounded upgrade that clears the repo’s Torch ignore list without destabilizing tests or widening scope.
4. If clean: remove Torch ignores from CI and document evidence (**Outcome A**).
5. If not clean after one bounded attempt: **Outcome B** — formal deferral with expiration and compensating controls.

## Guardrails

- No schema / contract registry / proof-pack / model-architecture changes.
- Do not weaken `pip-audit`, bandit, gitleaks, or release gates.
- Python policy (`requires-python`): unchanged unless a candidate forces it (reject such candidates).
- `RELDEPS-EXCEPTION` in PR body required for `release-dependency-freeze` when `pyproject.toml` changes intentionally.

## Outcome Implemented

See **`M39_summary.md`**: **Outcome A — upgrade accepted** (bounded `torch` + `setuptools` pins, Torch ignores removed from CI).
