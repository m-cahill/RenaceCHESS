# Deferred Issues Registry

This registry tracks **explicit deferrals only** — items that were identified as obligations, risks, or gaps within a milestone and consciously deferred to a later milestone.

**Governance Rule:** If an item was not explicitly deferred with intent, it does not appear in this registry.

---

## Active Deferred Issues

| ID | Issue | Discovered (M#) | Deferred To (M#) | Reason | Blocker? | Exit Criteria |
|----|-------|-----------------|------------------|--------|----------|---------------|
| LEGACY-COV-001 | Global coverage below 90% due to pre-M09 legacy files | M09 | M10 | Prevents unrelated legacy debt from blocking M09 | No (post-M09) | Raise coverage of legacy files (`cli.py`, `eval/runner.py`, `eval/report.py`, `models/training.py`) to ≥90% |
| CLI-COV-001 | Outcome-head CLI command (`train-outcome-head`) untested | M09 | M10 | New M09 execution path in orchestration layer; CLI tests are cross-cutting and belong in surface stabilization milestone | No | Add integration tests for `train-outcome-head` command in CLI |
| EVAL-RUNNER-COV-001 | Outcome-head eval integration wiring untested | M09 | M10 | New M09 execution path in orchestration layer; eval runner integration tests are cross-cutting | No | Add integration tests for outcome head evaluation paths in `eval/runner.py` |

---

## Resolved Deferred Issues

| ID | Issue | Discovered (M#) | Deferred To (M#) | Reason | Blocker? | Exit Criteria |
|----|-------|-----------------|------------------|--------|----------|---------------|
| M06-D01 | CLI conditioned metrics incomplete | M06 | Resolved (M07) | Required HDI spec finalization first | No | CLI fully supports conditioned metrics |
| M06-D02 | Frozen eval enforcement incomplete | M06 | Resolved (M07) | Enforcement logic deferred to HDI milestone | No | CLI hard-fails without frozen eval |

---

**Last Updated:** 2026-01-26 (M09 XML overlap-set gate findings)

