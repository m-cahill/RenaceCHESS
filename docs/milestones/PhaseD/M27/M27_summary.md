# 📌 Milestone Summary — M27: PHASE-D-RUNTIME-RECALIBRATION-EVALUATION-001

**Project:** RenaceCHESS  
**Phase:** Phase D (Data Expansion, Calibration & Quality)  
**Milestone:** M27 — Runtime Recalibration Evaluation  
**Timeframe:** 2026-02-01 → 2026-02-02  
**Status:** Closed

---

## 1. Milestone Objective

M27 existed to **measure whether runtime-gated recalibration improves human-conditioned predictions**, without changing default behavior or Phase C contracts.

This milestone was strictly **evidence generation**, not a decision to enable recalibration. Prior milestones established:

- **M24:** Calibration metrics (ECE, Brier, NLL)
- **M25:** Offline recalibration fitting (temperature scaling)
- **M26:** Runtime gating infrastructure (gate artifact + wrapper)

M27's job was to produce paired evaluation data comparing baseline (gate disabled) vs recalibrated (gate enabled) predictions, enabling a future data-driven decision on activation.

> *What would have been incomplete without M27?*  
> There would be no empirical evidence about recalibration's real-world impact — only theoretical justification.

---

## 2. Scope Definition

### In Scope

- `RuntimeRecalibrationReportV1` schema and Pydantic model
- `RuntimeRecalibrationDeltaV1` schema and Pydantic model
- Paired evaluation runner (`runtime_recalibration_eval_runner.py`)
- CLI subcommand (`renacechess eval runtime-recalibration`)
- CI job (`runtime-recalibration-eval`)
- Determinism verification (SHA-256 hashes)
- Unit, integration, and CLI tests (25 new tests)

### Out of Scope

- Enabling recalibration by default
- Adding new model heads
- Changing inference paths
- Modifying coaching outputs
- Deciding whether recalibration is "good enough"

---

## 3. Work Executed

### New Artifacts

| Artifact | Purpose |
|----------|---------|
| `RuntimeRecalibrationReportV1` | Full paired evaluation result with metadata, per-bucket metrics |
| `RuntimeRecalibrationDeltaV1` | Human-readable deltas with directionality (improved/degraded/neutral) |

### Implementation

| Component | Lines | Description |
|-----------|-------|-------------|
| Schemas | ~200 | Two new JSON Schema files |
| Pydantic models | ~180 | 12 new models in `contracts/models.py` |
| Evaluation runner | ~400 | Pure function implementation with deterministic hashing |
| CLI subcommand | ~50 | Explicit opt-in, required arguments |
| CI job | ~30 | Artifact validation and determinism check |
| Tests | ~500 | 25 tests covering unit, integration, determinism |

### Bugfix

Fixed pre-existing Windows Unicode issue in `test_m25_recalibration.py` (Unicode arrow character encoding).

---

## 4. Validation & Evidence

### CI Runs

| Run | Outcome | Issue | Resolution |
|-----|---------|-------|------------|
| Run 1 | ❌ Fail | MyPy type errors | Renamed variables to avoid shadowing |
| Run 2 | ❌ Fail | Ruff format check | Applied formatting |
| Run 3 | ❌ Fail | Coverage regression | Added direct CLI tests |
| Run 4 | ✅ Pass | All 9 jobs green | N/A |

### Test Results

- **795 tests passed**, 1 skipped
- **90.90% coverage** (exceeds 90% threshold)
- **Overlap-set check passed** (cli.py coverage maintained)
- **Determinism verified** (hashes stable across runs)

### Enforcement Mechanisms

| Gate | Status |
|------|--------|
| Type Check (MyPy) | ✅ Pass |
| Lint and Format (Ruff) | ✅ Pass |
| Security Scan | ✅ Pass |
| Coverage Threshold | ✅ Pass (90.90%) |
| M26 Guard Job | ✅ Pass (default path byte-identical) |
| M27 Evaluation Job | ✅ Pass (artifacts validated) |

---

## 5. CI / Automation Impact

### Workflows Affected

| Workflow | Change |
|----------|--------|
| `ci.yml` | Added `runtime-recalibration-eval` job |

### New CI Job: `runtime-recalibration-eval`

- **Purpose:** Validate M27 evaluation harness
- **Triggers:** Runs on PR and push to main
- **Dependencies:** Runs after `test` job
- **Actions:**
  1. Creates test fixtures (gate, params, manifest)
  2. Runs evaluation command
  3. Validates schema compliance
  4. Verifies determinism (hash check)
- **Artifacts:** Uploads report and delta JSON files

### Signal Quality

| Signal | Behavior |
|--------|----------|
| CI blocked incorrect changes | ✅ Yes (Runs 1-3 failures caught real issues) |
| CI validated correct changes | ✅ Yes (Run 4 confirmed all fixes) |
| CI observed relevant risk | ✅ Yes (coverage regression detected and addressed) |

---

## 6. Issues & Exceptions

### Issues Encountered

| Issue | Root Cause | Resolution |
|-------|------------|------------|
| MyPy type errors | Variable shadowing in CLI | Renamed `report` → `recal_report`, `delta` → `recal_delta` |
| Ruff format check failure | Long lines | Applied `ruff format` |
| Coverage regression | CLI code paths untested | Added direct CLI tests with `mock.patch` |
| Windows Unicode failure (M25) | Literal arrow character | Changed to `\u2192` escape sequence |

All issues were resolved within the milestone. No new issues introduced.

---

## 7. Deferred Work

No deferred work from M27.

No pre-existing deferred items were affected.

---

## 8. Governance Outcomes

### What is now provably true

1. **Paired evaluation works:** Baseline vs recalibrated predictions can be computed deterministically
2. **Delta artifacts are schema-validated:** `RuntimeRecalibrationDeltaV1` captures per-bucket improvements/degradations
3. **Determinism is enforced:** SHA-256 hashes exclude `generated_at` timestamp for reproducibility
4. **Default behavior unchanged:** M26 guard job proves byte-identical default path
5. **Evaluation is advisory:** No runtime activation, no user-facing changes

### Enforcement Posture

- Runtime recalibration remains **opt-in only** (gate must be explicitly provided)
- CI enforces determinism via hash comparison
- All Phase C contracts remain frozen

---

## 9. Exit Criteria Evaluation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All CI jobs pass | ✅ Met | Run 4: 9/9 jobs green |
| Coverage ≥ 90% | ✅ Met | 90.90% achieved |
| Deterministic paired artifacts generated | ✅ Met | Hash comparison passes in CI |
| Deltas clearly show improvement/degradation | ✅ Met | `RuntimeRecalibrationDeltaV1.directionality` field |
| Default runtime behavior unchanged | ✅ Met | M26 guard job passes |
| Guard job still green | ✅ Met | `runtime-recalibration-guard-m26` passes |

---

## 10. Final Verdict

> **Milestone objectives met. Safe to proceed.**

M27 is an **evaluation-only milestone** that achieved its single objective: produce deterministic, schema-validated evidence about runtime recalibration's impact without changing default behavior.

---

## 11. Authorized Next Step

**Authorized:** Proceed to M28 — Recalibration Activation Decision

M27 provides the data needed to decide whether runtime recalibration should be:
- Activated globally
- Restricted to certain Elo buckets
- Abandoned entirely

This decision is explicitly **out of scope for M27** and belongs to M28+.

---

## 12. Canonical References

### Commits

| Commit | Description |
|--------|-------------|
| `b9846aa` | M27: Runtime recalibration evaluation harness |
| `67d654b` | Fix MyPy and Ruff errors |
| `6852655` | Run ruff format on M27 files |
| `e5e7346` | Add direct CLI tests for M27 coverage |

### Pull Request

- **PR #33:** m27-runtime-recalibration-eval → main

### CI Runs

| Run | ID | Outcome |
|-----|----|---------|
| Run 1 | — | Failed (MyPy) |
| Run 2 | — | Failed (Format) |
| Run 3 | — | Failed (Coverage) |
| Run 4 | 21576813444 | **SUCCESS** |

### Documents

| Document | Location |
|----------|----------|
| M27 Plan | `docs/milestones/PhaseD/M27/M27_plan.md` |
| M27 Tool Calls | `docs/milestones/PhaseD/M27/M27_toolcalls.md` |
| M27 Run Analysis | `docs/milestones/PhaseD/M27/M27_run4.md` |
| M27 Audit | `docs/milestones/PhaseD/M27/M27_audit.md` |
| M27 Summary | `docs/milestones/PhaseD/M27/M27_summary.md` |

---

## What M27 Answered

### Primary Question

> *Does runtime recalibration improve prediction quality?*

M27 provides the framework to answer this:
- Per-bucket ECE, Brier, NLL deltas for outcome head
- Entropy, Top-1 rank stability, Top-3 stability for policy head
- Directionality classification (improved/degraded/neutral)

### What M27 Did *Not* Do

| Non-Action | Reason |
|------------|--------|
| Enable recalibration | Activation is M28+ |
| Change user-facing behavior | Evaluation-only milestone |
| Alter coaching outputs | Phase C contracts frozen |
| Propose parameter tuning | Out of scope |

### Why This Matters

M27 de-risks future decisions:
- Provides empirical evidence (not speculation)
- Maintains strict governance posture
- Preserves default path safety
- Enables data-driven activation decision

---

## Forward Pointer

> *M27 provides the data needed to decide whether runtime recalibration should be activated, restricted, or abandoned in a future milestone.*

---

**M27 is CLOSED.**  
All objectives met.  
No follow-up required within this milestone.



