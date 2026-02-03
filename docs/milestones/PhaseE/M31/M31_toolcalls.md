# M31 Tool Calls Log

This file logs all tool invocations for M31 milestone execution.

## Tool Call History

| Date | Tool | Purpose | Files/Target | Status |
|------|------|---------|--------------|--------|
| 2026-02-03 10:00 | read_file | Project analysis and M31 plan review | Multiple docs | ✅ Complete |
| 2026-02-03 10:15 | search_replace | Log session start | M31_toolcalls.md | ✅ Complete |
| 2026-02-03 10:16 | read_file | Review existing training infrastructure | training/, models/ | ✅ Complete |
| 2026-02-03 10:20 | write | Create TrainingConfigLockV1 JSON schema | schemas/v1/ | ✅ Complete |
| 2026-02-03 10:25 | write | Create TrainingRunReportV1 JSON schema | schemas/v1/ | ✅ Complete |
| 2026-02-03 10:30 | search_replace | Add Pydantic models for M31 schemas | models.py | ✅ Complete |
| 2026-02-03 10:35 | write | Create training dataset v2 generator | dataset/ | ✅ Complete |
| 2026-02-03 10:45 | write | Create M31 training runner | models/ | ✅ Complete |
| 2026-02-03 10:50 | write | Create M31 test suite | tests/ | ✅ Complete |
| 2026-02-03 11:00 | search_replace | Add M31 CI validation job | ci.yml | ✅ Complete |
| 2026-02-03 11:05 | search_replace | Update renacechess.md M31 status | renacechess.md | ✅ Complete |

---

## Implementation Complete

All M31 artifacts have been created:

1. **Schemas (JSON Schema):**
   - `training_config_lock.v1.schema.json`
   - `training_run_report.v1.schema.json`

2. **Pydantic Models:**
   - `TrainingConfigLockV1` + supporting models
   - `TrainingRunReportV1` + supporting models

3. **Training Dataset Generator:**
   - `training_dataset_v2.py` (~100k positions, disjoint from frozen eval)

4. **Training Runner:**
   - `m31_training_runner.py` (config lock + execution + report)

5. **Tests:**
   - `test_m31_training_run.py` (comprehensive test suite)

6. **CI:**
   - `m31-schema-validation` job added to ci.yml

**Status:** ✅ Ready for execution approval

---

## Test Results

- M31 tests: 19 passed
- M30 tests: 29 passed (no regressions)
- Total: 48 passed in 3.47s

---

## PR Creation

| Date | Tool | Purpose | Files/Target | Status |
|------|------|---------|--------------|--------|
| 2026-02-03 11:30 | git checkout | Create M31 branch | m31-full-training-run | ✅ Complete |
| 2026-02-03 11:31 | git commit | Commit M31 implementation | 11 files | ✅ Complete |
| 2026-02-03 11:32 | git push | Push branch to origin | origin/m31-full-training-run | ✅ Complete |
| 2026-02-03 11:33 | gh pr create | Create PR #36 | PR #36 | ✅ Complete |
| 2026-02-03 11:34 | gh run watch | Monitor CI | PR #36 | 🔄 In Progress |

**PR:** https://github.com/m-cahill/RenaceCHESS/pull/36

---

## Session: 2026-02-03 — M31 Implementation Start

### Locked Decisions Received
- Q1: Production dataset manifest v2 — CREATE in M31 (~100k positions)
- Q2: Training config — Use templates verbatim, 10 epochs
- Q3: Checkpoints — External storage, hashes committed
- Q4: New schemas — Create TrainingConfigLockV1, TrainingRunReportV1
- Q5: Timeline — 2-6 hours target, 12h hard timeout
- Q6: AMP — Out of scope (FP32 only)

---

---

## CI Fix: Coverage Regression

| Date | Tool | Purpose | Files/Target | Status |
|------|------|---------|--------------|--------|
| 2026-02-03 12:00 | gh pr checks | Check CI status | PR #36 | ✅ Complete |
| 2026-02-03 12:01 | gh run view | Analyze Test job failure | CI logs | ✅ Complete |
| 2026-02-03 12:05 | search_replace | Add robust coverage test | test_m08_model.py | ✅ Complete |
| 2026-02-03 12:06 | pytest | Verify new test passes | test_m08_model.py | ✅ Complete |

**Issue:** CI showed coverage regression in `models/baseline_v1.py` (100% → 96.49%)
**Root cause:** Python's non-deterministic `hash()` function caused test flakiness
**Fix:** Added `test_baseline_policy_v1_forward_uniform_distribution_guaranteed` that uses
       `move_vocab_size=1` to guarantee hash collisions regardless of PYTHONHASHSEED

---

**Last Updated:** 2026-02-03

