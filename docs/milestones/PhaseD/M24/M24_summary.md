# 📌 Milestone Summary — M24: Phase D Calibration Metrics

**Project:** RenaceCHESS  
**Phase:** D (Data Expansion, Calibration & Quality)  
**Milestone:** M24 — PHASE-D-CALIBRATION-001  
**Timeframe:** 2026-02-01  
**Status:** Closed  

---

## 1. Milestone Objective

M24 introduced human-aligned calibration and evaluation signals without changing frozen Phase C contracts or runtime behavior. This milestone establishes Phase D's first quality measurement layer, enabling future recalibration work.

**Why this milestone existed:**
Phase D needed a way to measure calibration quality (how well predicted probabilities match observed frequencies) across Elo buckets. Without M24, Phase D would lack the measurement infrastructure needed to justify recalibration changes in future milestones.

---

## 2. Scope Definition

### In Scope

- **CalibrationMetricsV1 schema:** Pydantic models and JSON Schema for calibration artifacts
- **Calibration evaluation runner:** Offline runner that computes ECE, Brier score, NLL, and confidence histograms
- **Per-Elo bucket stratification:** Metrics broken down by canonical SkillBucketId
- **CI calibration job:** Automated evaluation on frozen eval fixture
- **CLI integration:** `renacechess calibration run` command
- **Test suite:** Comprehensive unit and integration tests

### Out of Scope

- **Recalibration logic:** No temperature scaling, thresholding, or probability adjustment
- **Phase C contract changes:** AdviceFactsV1, EloBucketDeltaFactsV1, CoachingDraftV1 untouched
- **Runtime behavior changes:** Measurement-only, no changes to prediction logic
- **Large eval datasets:** CI uses small, deterministic fixture only

---

## 3. Work Executed

### High-Level Actions

1. **Schema Definition**
   - Created `CalibrationMetricsV1` Pydantic models (CalibrationBinV1, CalibrationHistogramV1, OutcomeCalibrationMetricsV1, PolicyCalibrationMetricsV1, EloBucketCalibrationV1)
   - Created JSON Schema (`calibration_metrics.v1.schema.json`)
   - Integrated with existing contract system

2. **Calibration Runner Implementation**
   - Created `eval/calibration_runner.py` with:
     - `CalibrationAccumulator` (base class for ECE, Brier, NLL computation)
     - `OutcomeCalibrationAccumulator` (W/D/L calibration)
     - `PolicyCalibrationAccumulator` (move probability calibration)
     - `run_calibration_evaluation` (orchestration function)
   - Uses baseline models by default (checkpoint-optional)

3. **CI Integration**
   - Added `calibration-eval` job to `.github/workflows/ci.yml`
   - Uses frozen eval fixture (`tests/fixtures/frozen_eval/`)
   - Uploads `calibration-metrics.json` as artifact
   - Required check (fails on error/schema/determinism only)

4. **CLI Integration**
   - Added `calibration` subcommand to `renacechess.cli`
   - Takes `--manifest` and `--out` arguments
   - Calls `run_calibration_evaluation`

5. **Test Suite**
   - Created `tests/test_m24_calibration.py` (30 tests, 653 lines)
   - Tests schema validation, accumulator logic, runner integration, CLI, determinism
   - Added branch coverage tests for `baseline_v1.py`

6. **CI Fixes**
   - Fixed coverage data type mismatch (added `--cov-branch` to all coverage steps)
   - Fixed lint error (removed unused variable)
   - Fixed coverage data type conflict in final test run

### File Counts

| Metric | Count |
|--------|-------|
| Files changed | 38 |
| Lines added | ~3,792 |
| Lines removed | ~324 |
| New source files | 3 |
| New test files | 1 |
| New schema files | 1 |
| New fixture files | 3 |

---

## 4. Validation & Evidence

### Tests Run

| Venue | Result |
|-------|--------|
| Local | 30 M24 tests passed |
| CI Run 3 | 684 passed, 1 skipped, 90%+ coverage |

### Enforcement Mechanisms

| Mechanism | Status |
|-----------|--------|
| Ruff lint | ✅ Enforced |
| Ruff format | ✅ Enforced |
| MyPy | ✅ Enforced |
| Import-linter | ✅ Enforced |
| Coverage threshold (90%) | ✅ Enforced |
| Coverage overlap-set comparison | ✅ Enforced |
| Security scan (pip-audit + bandit) | ✅ Enforced |
| Performance benchmarks | ✅ Enforced |

### Failures Encountered and Resolved

| Run | Failure | Resolution |
|-----|---------|------------|
| 1 | Coverage data type mismatch | Added `--cov-branch` to baseline and head |
| 2 | Lint error (unused variable) | Removed unused variable |
| 2 | Coverage data type conflict | Cleaned `.coverage` files, added `--cov-branch` to final test run |
| 3 | — | ✅ All checks passing |

### Validation Meaningfulness

- Tests exercise actual calibration computation (not just existence)
- Determinism verified (same input produces same output)
- Schema validation ensures contract stability
- CI job provides continuous visibility

---

## 5. CI / Automation Impact

### Workflows Affected

- **`.github/workflows/ci.yml`:**
  - Added `calibration-eval` job (new)
  - Modified `test` job (coverage data type alignment)

### Checks Added

- **Calibration evaluation:** New required check
- **Coverage branch consistency:** Enforced across all coverage steps

### Changes in Enforcement Behavior

- Coverage system now uses `--cov-branch` consistently (prevents data type conflicts)
- Calibration metrics generated on every PR (continuous visibility)

### Signal Integrity

- ✅ CI blocked incorrect changes (coverage data type mismatch caught)
- ✅ CI validated correct changes (all gates pass)
- ✅ No signal drift observed

---

## 6. Issues & Exceptions

**No new issues were introduced during this milestone.**

All issues encountered were CI configuration issues (coverage data type alignment) and minor lint errors, all resolved within the milestone.

---

## 7. Deferred Work

**No deferred work from M24.**

Prior deferrals (TORCH-SEC-001, CLI-COV-001) remain unchanged and are not affected by M24.

---

## 8. Governance Outcomes

### What is now provably true that was not true before:

1. **Calibration measurement capability exists:**
   - Can compute ECE, Brier score, NLL for outcome and policy predictions
   - Metrics stratified by Elo bucket
   - Deterministic artifacts for audit trail

2. **Coverage system consistency:**
   - All coverage steps use `--cov-branch` consistently
   - Prevents future data type conflicts
   - Long-term maintainability improvement

3. **Phase D measurement infrastructure:**
   - Enables future recalibration work (M25+)
   - Measurement-only posture maintained (no behavior changes)

4. **CI truth posture preserved:**
   - All gates pass without weakening
   - Coverage comparison working correctly
   - No masked failures

---

## 9. Exit Criteria Evaluation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| CalibrationMetricsV1 schema | ✅ Met | Schema created, validated, tested |
| Calibration evaluation runner | ✅ Met | Runner implemented, tested, CI-verified |
| Per-Elo bucket stratification | ✅ Met | Uses canonical SkillBucketId, tested |
| CI calibration job | ✅ Met | Job added, passes, artifacts uploaded |
| No Phase C contract changes | ✅ Met | No changes to AdviceFactsV1, EloBucketDeltaFactsV1, CoachingDraftV1 |
| No runtime behavior changes | ✅ Met | Measurement-only, no recalibration |
| Deterministic artifacts | ✅ Met | Fixed seeds, canonical JSON, tested |
| Test coverage | ✅ Met | 30 new tests, 100% coverage of new code |
| CI fully green | ✅ Met | Run 3: All 6 jobs passed |

---

## 10. Final Verdict

**Milestone objectives met. Safe to proceed.**

M24 successfully introduces Phase D's first quality measurement layer without compromising Phase C contracts or runtime behavior. All CI gates pass. Coverage system consistency improved. No new technical debt introduced.

---

## 11. Authorized Next Step

**M25 — Phase D Recalibration / Adjustment**

M24 enables M25 to change behavior because measurement capability is now proven. Examples:
- Temperature scaling
- Bucket-specific calibration curves
- Thresholding experiments
- Human evaluation alignment loops

**Constraint:** M25 can now change behavior because M24 proved we can measure it.

---

## 12. Canonical References

- **PR:** #30
- **Final Commit:** `029e611`
- **CI Runs:**
  - Run 1: 21557859901 (coverage data type mismatch)
  - Run 2: 21569452167 (lint + coverage conflict)
  - Run 3: 21569555120 (✅ fully green)
- **Plan:** `docs/milestones/PhaseD/M24/M24_plan.md`
- **Audit:** `docs/milestones/PhaseD/M24/M24_audit.md`
- **Tool Calls:** `docs/milestones/PhaseD/M24/M24_toolcalls.md`
- **Run Analyses:**
  - `docs/milestones/PhaseD/M24/M24_run1.md`
  - `docs/milestones/PhaseD/M24/M24_run2.md`
  - `docs/milestones/PhaseD/M24/M24_run3.md`

