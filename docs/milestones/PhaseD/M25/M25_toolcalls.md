# M25 Tool Calls Log

**Milestone:** M25 — PHASE-D-RECALIBRATION-001  
**Phase:** D  
**Status:** 🚧 In Progress  

---

## Tool Call History

| Timestamp | Tool | Purpose | Files/Target | Status |
|-----------|------|---------|--------------|--------|
| 2026-02-01 | read_file | Review M25 plan and locked clarifications | M25_plan.md | ✅ Complete |
| 2026-02-01 | read_file | Understand M24 calibration structure | calibration_runner.py, models.py | ✅ Complete |
| 2026-02-01 | search_replace | Update toolcalls log | M25_toolcalls.md | ✅ Complete |
| 2026-02-01 | search_replace | Add M25 Pydantic models | contracts/models.py | ✅ Complete |
| 2026-02-01 | write | Create recalibration_parameters.v1.schema.json | contracts/schemas/v1/ | ✅ Complete |
| 2026-02-01 | write | Create calibration_delta.v1.schema.json | contracts/schemas/v1/ | ✅ Complete |
| 2026-02-01 | write | Implement recalibration runner | eval/recalibration_runner.py | ✅ Complete |
| 2026-02-01 | search_replace | Add recalibration CLI commands | cli.py | ✅ Complete |
| 2026-02-01 | search_replace | Add recalibration-eval CI job | .github/workflows/ci.yml | ✅ Complete |
| 2026-02-01 | write | Create comprehensive test suite | tests/test_m25_recalibration.py | ✅ Complete |

---

## Locked Decisions (M25)

**From locked clarifications:**
- Fit method: Grid search only (temps: [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0])
- Fit metric: NLL (primary), ECE (secondary reporting)
- Dataset: Same frozen eval fixture as M24
- Models: Baseline default, checkpoint-optional
- Temperature bounds: 0.25 - 3.0
- CLI preview: Read-only before/after, per-bucket, off by default
- Delta artifact: Separate CalibrationDeltaV1 (not embedded)
- CI gating: Fail only on crash/schema/determinism (no metric-based failures)

---

## Notes

This file tracks all tool invocations for M25 per the workflow rules in `.cursorrules`.

