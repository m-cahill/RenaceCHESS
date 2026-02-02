# 📌 Milestone Summary — M28: Runtime Recalibration Activation Decision

**Project:** RenaceCHESS  
**Phase:** D — Data Expansion, Calibration & Quality  
**Milestone:** M28 — PHASE-D-RECALIBRATION-ACTIVATION-DECISION-001  
**Timeframe:** 2026-02-02 (single session)  
**Status:** ✅ Closed  

---

## 1. Milestone Objective

M28 existed to provide a **governed decision framework** for determining if and how runtime recalibration should be activated.

Phase D established:
- **M24:** Calibration metrics (ECE, Brier, NLL)
- **M25:** Offline recalibration fitting (temperature scaling)
- **M26:** Runtime gating mechanism (RecalibrationGateV1)
- **M27:** Paired evaluation (evidence generation)

M28 closes the loop by:
- Consuming M27 evidence
- Applying a declarative activation policy
- Producing a human-readable, deterministic decision artifact

Without M28, runtime recalibration would require ad-hoc, unauditable activation decisions. M28 ensures all activation is **explicit, evidence-based, and reversible**.

---

## 2. Scope Definition

### In Scope

| Item | Status |
|------|--------|
| RuntimeRecalibrationActivationPolicyV1 schema | ✅ Complete |
| RuntimeRecalibrationDecisionV1 schema | ✅ Complete |
| 8 supporting Pydantic models | ✅ Complete |
| Decision runner (recalibration_decision_runner.py) | ✅ Complete |
| CLI command (renacechess eval runtime-recalibration-decision) | ✅ Complete |
| CI job (runtime-recalibration-decision) | ✅ Complete |
| Comprehensive test suite (36 tests) | ✅ Complete |

### Out of Scope

| Item | Reason |
|------|--------|
| Actual activation of recalibration | Decision framework only |
| Modification of Phase C contracts | Frozen |
| Changes to default runtime behavior | Preservation by design |
| Per-time-control or per-confidence thresholds | Future extension |

---

## 3. Work Executed

### Schemas Created

1. **RuntimeRecalibrationActivationPolicyV1** — Declarative policy artifact with:
   - `defaultEnabled`: Global activation switch
   - `bucketOverrides`: Per-bucket activation overrides
   - `scopeOverrides`: Per-scope (policy/outcome) overrides

2. **RuntimeRecalibrationDecisionV1** — Human-readable decision artifact with:
   - `decisionOutcome`: rejected | restricted | activated
   - `bucketDecisions`: Per-bucket activation decisions
   - `validationResult`: Policy validation status
   - `humanSummary`: Plain-language explanation

### Pydantic Models Added (8 total)

- `BucketOverrideV1`
- `ScopeOverrideV1`
- `PolicyValidationResultV1`
- `BucketDecisionV1`
- `DecisionOutcomeV1` (Literal enum)
- `RuntimeRecalibrationActivationPolicyV1`
- `RuntimeRecalibrationDecisionV1`
- `BucketDecisionMetadataV1`

### Implementation

- **recalibration_decision_runner.py** (356 lines):
  - `load_runtime_recalibration_report()` — Load M27 report artifact
  - `load_runtime_recalibration_delta()` — Load M27 delta artifact
  - `load_activation_policy()` — Load policy artifact
  - `create_conservative_policy()` — Generate default conservative policy
  - `compute_runtime_recalibration_decision()` — Main decision computation
  - `save_decision()` / `save_policy()` — Artifact persistence

### CLI Command

```bash
renacechess eval runtime-recalibration-decision \
  --report PATH --delta PATH --policy PATH --output PATH
```

### CI Job

New `runtime-recalibration-decision` job in CI workflow:
- Depends on M27 evaluation job
- Downloads M27 artifacts
- Runs decision computation
- Uploads decision artifact

---

## 4. Validation & Evidence

### Tests Executed

- **36 new tests** in `test_m28_recalibration_decision.py`
- **Test categories:**
  - Schema validation (JSON Schema + Pydantic)
  - Policy loading and validation
  - Bucket decision computation
  - Conservative/activated/restricted scenarios
  - Determinism verification
  - Error path coverage

### Coverage

| Module | Coverage |
|--------|----------|
| `recalibration_decision_runner.py` | 94.54% |
| Overall project | 91.10% |

### CI Runs

| Run | ID | Result | Notes |
|-----|-----|--------|-------|
| 1 | 21577843642 | ❌ Failure | False positive coverage regression (resolved) |
| 2 | 21578177807 | ✅ Success | All 10 checks passing |

---

## 5. CI / Automation Impact

### Workflows Affected

- `.github/workflows/ci.yml` — New job added

### Checks Added

- `runtime-recalibration-decision` — New required check

### Enforcement Behavior

- CI validates decision generation with conservative policy
- Decision artifact uploaded for audit
- Job depends on M27 (proper sequencing)

### Signal Assessment

| Signal | Status |
|--------|--------|
| Blocked incorrect changes | ✅ First run correctly identified transient issue |
| Validated correct changes | ✅ Second run confirmed all correct |
| Failed to observe risk | ❌ N/A (no missed risks) |

---

## 6. Issues & Exceptions

### Transient CI Issue

- **Description:** First CI run reported false positive coverage regression
- **Root cause:** CI caching artifact inconsistency between base and head
- **Resolution:** Force-push re-triggered clean CI run
- **Status:** ✅ Resolved
- **Tracking:** Documented in M28_run1.md

> No new issues were introduced during this milestone.

---

## 7. Deferred Work

**No deferrals from M28.**

All Phase D milestones (M23–M28) completed without new deferrals.

---

## 8. Governance Outcomes

After M28 closeout, the following statements are **enforceably true**:

1. **Recalibration activation is explicit**
   - No silent or automatic activation
   - Policy artifact required for any activation

2. **Decisions are evidence-based**
   - Every decision references M27 report + delta hashes
   - Lineage is verifiable

3. **Conservative defaults are enforced**
   - `create_conservative_policy()` disables all buckets
   - Any activation requires explicit policy override

4. **Decisions are auditable**
   - Human-readable summary in every decision
   - Determinism hash for reproducibility
   - Schema-validated artifacts

5. **Phase C contracts remain frozen**
   - AdviceFactsV1, EloBucketDeltaFactsV1, etc. unchanged
   - No behavioral drift

---

## 9. Exit Criteria Evaluation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Schema + Pydantic models created | ✅ Met | 2 schemas, 8 models |
| Decision runner implemented | ✅ Met | recalibration_decision_runner.py |
| CLI command added | ✅ Met | `eval runtime-recalibration-decision` |
| CI job added | ✅ Met | runtime-recalibration-decision job |
| Tests cover all paths | ✅ Met | 36 tests, 94.54% coverage |
| Phase C contracts unchanged | ✅ Met | No modifications |
| Default behavior preserved | ✅ Met | M26 guard job passes |

---

## 10. Final Verdict

**Milestone objectives met. Safe to proceed.**

M28 delivers a complete, governed decision framework for runtime recalibration activation. All 10 CI checks passing. No regressions. Phase D is now complete and ready for closeout.

---

## 11. Authorized Next Step

**Authorized:**
1. Merge PR #34 (M28)
2. Generate PhaseD_closeout.md
3. Update renacechess.md (mark Phase D CLOSED)
4. Seed M29 folder for Phase E entry

**Constraints:**
- Phase D closeout requires explicit authorization (granted above)
- Phase E entry blocked until Phase D closeout complete

---

## 12. Canonical References

### Commits
- `003f7121866e5d7a39db39da8e70d15600ad8582` — M28 implementation

### Pull Requests
- PR #34 — M28: Runtime recalibration activation decision framework

### CI Runs
- Run 21578177807 — Final green run

### Documents
- `docs/milestones/PhaseD/M28/M28_plan.md`
- `docs/milestones/PhaseD/M28/M28_toolcalls.md`
- `docs/milestones/PhaseD/M28/M28_run1.md`
- `docs/milestones/PhaseD/M28/M28_audit.md`

### Schemas
- `src/renacechess/contracts/schemas/v1/runtime_recalibration_activation_policy.v1.schema.json`
- `src/renacechess/contracts/schemas/v1/runtime_recalibration_decision.v1.schema.json`

### Models
- `renacechess.contracts.models.RuntimeRecalibrationActivationPolicyV1`
- `renacechess.contracts.models.RuntimeRecalibrationDecisionV1`
- `renacechess.contracts.models.BucketOverrideV1`
- `renacechess.contracts.models.ScopeOverrideV1`
- `renacechess.contracts.models.PolicyValidationResultV1`
- `renacechess.contracts.models.BucketDecisionV1`
- `renacechess.contracts.models.BucketDecisionMetadataV1`

