# Deferred Issues Registry

This registry tracks **explicit deferrals only** — items that were identified as obligations, risks, or gaps within a milestone and consciously deferred to a later milestone.

**Governance Rule:** If an item was not explicitly deferred with intent, it does not appear in this registry.

---

## Active Deferred Issues

*(No active deferred issues)*

---

## Resolved Deferred Issues (M13+)

| ID | Issue | Discovered (M#) | Resolved In (M#) | Resolution | Exit Criteria Met |
|----|-------|-----------------|------------------|------------|-------------------|
| PYDANTIC-DICT-CONTRACT-001 | Dict-Based Contract Input Semantics Undefined | M12 | ✅ M13 | Contract explicitly defined: Option A (Alias-Only Dict Inputs). Models use `populate_by_name=True`. Dict inputs require camelCase alias keys; keyword args may use snake_case. | ✅ `docs/contracts/CONTRACT_INPUT_SEMANTICS.md` created; tests comply with contract; CI green |

---

## Resolved Deferred Issues (M10 and earlier)

| ID | Issue | Discovered (M#) | Deferred To (M#) | Reason | Blocker? | Exit Criteria |
|----|-------|-----------------|------------------|--------|----------|---------------|
| M06-D01 | CLI conditioned metrics incomplete | M06 | Resolved (M07) | Required HDI spec finalization first | No | CLI fully supports conditioned metrics |
| M06-D02 | Frozen eval enforcement incomplete | M06 | Resolved (M07) | Enforcement logic deferred to HDI milestone | No | CLI hard-fails without frozen eval |
| LEGACY-COV-001 | Global coverage below 90% due to pre-M09 legacy files | M09 | Resolved (M10) | Prevents unrelated legacy debt from blocking M09 | No (post-M09) | ✅ Resolved: Total coverage restored to 90.64% (exceeds 90% threshold) |
| CLI-COV-001 | Outcome-head CLI command (`train-outcome-head`) untested | M09 | Resolved (M10) | New M09 execution path in orchestration layer; CLI tests are cross-cutting and belong in surface stabilization milestone | No | ✅ Resolved: Integration tests added in `test_cli.py` (3 tests covering train-outcome-head command) |
| EVAL-RUNNER-COV-001 | Outcome-head eval integration wiring untested | M09 | Resolved (M10) | New M09 execution path in orchestration layer; eval runner integration tests are cross-cutting | No | ✅ Resolved: Integration tests added in `test_m10_runner_outcome_head.py` (3 tests covering outcome head evaluation paths) |

---

**Last Updated:** 2026-02-01 (M13 closeout - PYDANTIC-DICT-CONTRACT-001 resolved; contract semantics explicitly defined)

