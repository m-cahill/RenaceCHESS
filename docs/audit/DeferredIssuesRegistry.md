# Deferred Issues Registry

This registry tracks **explicit deferrals only** — items that were identified as obligations, risks, or gaps within a milestone and consciously deferred to a later milestone.

**Governance Rule:** If an item was not explicitly deferred with intent, it does not appear in this registry.

---

## Active Deferred Issues

*(No active deferred issues)*

---

## Resolved Deferred Issues

| ID | Issue | Discovered (M#) | Deferred To (M#) | Reason | Blocker? | Exit Criteria |
|----|-------|-----------------|------------------|--------|----------|---------------|
| M06-D01 | CLI conditioned metrics incomplete | M06 | Resolved (M07) | Required HDI spec finalization first | No | CLI fully supports conditioned metrics |
| M06-D02 | Frozen eval enforcement incomplete | M06 | Resolved (M07) | Enforcement logic deferred to HDI milestone | No | CLI hard-fails without frozen eval |
| LEGACY-COV-001 | Global coverage below 90% due to pre-M09 legacy files | M09 | Resolved (M10) | Prevents unrelated legacy debt from blocking M09 | No (post-M09) | ✅ Resolved: Total coverage restored to 90.35% (exceeds 90% threshold) |
| CLI-COV-001 | Outcome-head CLI command (`train-outcome-head`) untested | M09 | Resolved (M10) | New M09 execution path in orchestration layer; CLI tests are cross-cutting and belong in surface stabilization milestone | No | ✅ Resolved: Integration tests added in `test_cli.py` (3 tests covering train-outcome-head command) |
| EVAL-RUNNER-COV-001 | Outcome-head eval integration wiring untested | M09 | Resolved (M10) | New M09 execution path in orchestration layer; eval runner integration tests are cross-cutting | No | ✅ Resolved: Integration tests added in `test_m10_runner_outcome_head.py` (3 tests covering outcome head evaluation paths) |

---

**Last Updated:** 2026-01-26 (M10 closeout - all M09 deferrals resolved)

