# M32 Tool Calls Log

**Milestone:** M32 — POST-TRAIN-EVAL-PACK-001  
**Phase:** E (Scale Proof, Training Run, Release Lock)  
**Status:** Implementation Complete — Pending CI Verification

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

