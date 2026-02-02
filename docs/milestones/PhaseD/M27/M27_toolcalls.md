# M27 Tool Calls Log

This file logs all tool invocations for M27 milestone execution.

## Tool Call History

| Date | Tool | Purpose | Files/Target | Status |
|------|------|---------|--------------|--------|
| 2026-02-01 | write | Initialize M27 milestone folder | M27_plan.md, M27_toolcalls.md | ✅ Complete |
| 2026-02-02 | read_file | Analyze project and M27 plan | Primary/secondary docs, M27_plan.md | ✅ Complete |
| 2026-02-02 | todo_write | Create M27 implementation task list | N/A | ✅ Complete |
| 2026-02-02 | write | Create RuntimeRecalibrationReportV1 schema | schemas/v1/runtime_recalibration_report.v1.schema.json | ✅ Complete |
| 2026-02-02 | write | Create RuntimeRecalibrationDeltaV1 schema | schemas/v1/runtime_recalibration_delta.v1.schema.json | ✅ Complete |
| 2026-02-02 | search_replace | Add Pydantic models to models.py | contracts/models.py | ✅ Complete |
| 2026-02-02 | write | Create runtime_recalibration_eval_runner.py | eval/runtime_recalibration_eval_runner.py | ✅ Complete |
| 2026-02-02 | search_replace | Add CLI subcommand eval runtime-recalibration | cli.py | ✅ Complete |
| 2026-02-02 | write | Create test fixtures (gate + params) | tests/fixtures/frozen_eval/*.json | ✅ Complete |
| 2026-02-02 | search_replace | Add CI job runtime-recalibration-eval | .github/workflows/ci.yml | ✅ Complete |
| 2026-02-02 | write | Create M27 tests | tests/test_m27_runtime_recalibration_eval.py | ✅ Complete |
| 2026-02-02 | search_replace | Fix M25 Windows Unicode test | tests/test_m25_recalibration.py | ✅ Complete |
| 2026-02-02 | search_replace | Fix runner determinism hash (exclude generatedAt) | runtime_recalibration_eval_runner.py | ✅ Complete |
| 2026-02-02 | run_terminal_cmd | Run full test suite (791 passed, 90.12% coverage) | All tests | ✅ Complete |
| 2026-02-02 | run_terminal_cmd | Create branch and PR | git | 🔄 In Progress |

---

**Last Updated:** 2026-02-02 (All tests passing, coverage ≥90%)

