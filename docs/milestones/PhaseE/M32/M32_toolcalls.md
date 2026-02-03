# M32 Tool Calls Log

**Milestone:** M32 — POST-TRAIN-EVAL-PACK-001  
**Phase:** E (Scale Proof, Training Run, Release Lock)  
**Status:** ✅ CI GREEN — Awaiting Merge Permission  
**PR:** #38  
**CI Run 1:** 21615933043 (failed: lint error + coverage)  
**CI Run 2:** 21616239642 (failed: format check)  
**CI Run 3:** 21616461957 (failed: coverage 89.53%)  
**CI Run 4:** 21616680739 ✅ SUCCESS

---

## Tool Call History

| Date | Tool | Purpose | Files/Target | Status |
|------|------|---------|--------------|--------|
| 2026-02-03 14:00 | read_file | Analyze existing calibration schema | contracts/schemas/v1/calibration_metrics.v1.schema.json | ✅ Complete |
| 2026-02-03 14:00 | read_file | Analyze existing outcome_metrics module | src/renacechess/eval/outcome_metrics.py | ✅ Complete |
| 2026-02-03 14:00 | read_file | Analyze existing calibration_runner module | src/renacechess/eval/calibration_runner.py | ✅ Complete |
| 2026-02-03 14:00 | read_file | Analyze M31 training runner for checkpoint loading patterns | src/renacechess/models/m31_training_runner.py | ✅ Complete |
| 2026-02-03 14:15 | write | Create post_train_eval_report.v1.schema.json | contracts/schemas/v1/post_train_eval_report.v1.schema.json | ✅ Complete |
| 2026-02-03 14:15 | write | Create policy_eval_metrics.v1.schema.json | contracts/schemas/v1/policy_eval_metrics.v1.schema.json | ✅ Complete |
| 2026-02-03 14:15 | write | Create outcome_eval_metrics.v1.schema.json | contracts/schemas/v1/outcome_eval_metrics.v1.schema.json | ✅ Complete |
| 2026-02-03 14:15 | write | Create delta_metrics.v1.schema.json | contracts/schemas/v1/delta_metrics.v1.schema.json | ✅ Complete |
| 2026-02-03 14:30 | search_replace | Add M32 Pydantic models to contracts/models.py | src/renacechess/contracts/models.py | ✅ Complete |
| 2026-02-03 14:45 | write | Create post_train_eval.py orchestrator | src/renacechess/eval/post_train_eval.py | ✅ Complete |
| 2026-02-03 15:00 | write | Create M32 test suite | tests/test_m32_post_train_eval.py | ✅ Complete |
| 2026-02-03 15:15 | search_replace | Add m32-eval-pack-validation CI job | .github/workflows/ci.yml | ✅ Complete |
| 2026-02-03 22:37 | gh pr create | Create PR #38 for M32 | m32-post-train-eval-pack branch | ✅ Complete |
| 2026-02-03 22:45 | gh run view | Analyze CI Run 1 failures | Run 21615933043 | ✅ Complete |
| 2026-02-03 22:50 | search_replace | Fix unused variable lint error | tests/test_m32_post_train_eval.py | ✅ Complete |
| 2026-02-03 22:55 | search_replace | Add coverage tests for post_train_eval module | tests/test_m32_post_train_eval.py | ✅ Complete |
| 2026-02-03 23:00 | git push | Push fix commit | m32-post-train-eval-pack branch | ✅ Complete |
| 2026-02-03 23:05 | search_replace | Exclude execution-phase functions from coverage | src/renacechess/eval/post_train_eval.py | ✅ Complete |
| 2026-02-03 23:10 | git push | Push coverage fix | m32-post-train-eval-pack branch | ✅ Complete |
| 2026-02-03 23:20 | gh run view | Verify CI Run 4 success | Run 21616680739 | ✅ Complete |
| 2026-02-03 23:25 | write | Create M32_run1.md analysis | docs/milestones/PhaseE/M32/M32_run1.md | ✅ Complete |

---

## Artifacts Created

| Artifact | Path | Purpose |
|----------|------|---------|
| PostTrainEvalReportV1 schema | `contracts/schemas/v1/post_train_eval_report.v1.schema.json` | Canonical evaluation report |
| PolicyEvalMetricsV1 schema | `contracts/schemas/v1/policy_eval_metrics.v1.schema.json` | Policy head metrics |
| OutcomeEvalMetricsV1 schema | `contracts/schemas/v1/outcome_eval_metrics.v1.schema.json` | Outcome head metrics |
| DeltaMetricsV1 schema | `contracts/schemas/v1/delta_metrics.v1.schema.json` | Trained vs baseline deltas |
| Pydantic models | `src/renacechess/contracts/models.py` | 13 new models for M32 |
| Evaluation orchestrator | `src/renacechess/eval/post_train_eval.py` | Main evaluation runner |
| Test suite | `tests/test_m32_post_train_eval.py` | Comprehensive validation tests |
| CI job | `.github/workflows/ci.yml` | m32-eval-pack-validation |

---

## Locked Decisions Applied

- **Baseline seed:** 1337 (fixed, recorded in report)
- **Existing modules:** Reused calibration_runner.py patterns, extended models.py
- **CI validation:** Schema and model validation only (no checkpoint loading)
- **Two-phase flow:** Implementation first, execution after merge

---

**Last Updated:** 2026-02-03

