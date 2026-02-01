# M24 Tool Calls Log

**Milestone:** M24 — PHASE-D-CALIBRATION-001  
**Phase:** D  
**Status:** ⏳ In Progress  

---

## Tool Call History

| Timestamp | Tool | Purpose | Files/Target | Status |
|-----------|------|---------|--------------|--------|
| 2026-02-01T10:00 | read_file | Project familiarization | Primary/secondary docs | ✅ Complete |
| 2026-02-01T10:15 | clarify | Locked answers received | 6 clarifying questions | ✅ Locked |
| 2026-02-01T10:20 | todo_write | Create implementation plan | M24 todos | ✅ Complete |
| 2026-02-01T10:25 | search_replace | Add CalibrationMetricsV1 models | models.py | ✅ Complete |
| 2026-02-01T10:30 | write | Create calibration_metrics.v1.schema.json | schemas/v1/ | ✅ Complete |
| 2026-02-01T10:35 | write | Create frozen eval CI fixture | tests/fixtures/frozen_eval/ | ✅ Complete |
| 2026-02-01T10:40 | write | Create calibration_runner.py | src/renacechess/eval/ | ✅ Complete |
| 2026-02-01T10:45 | write | Create test_m24_calibration.py | tests/ | ✅ Complete |
| 2026-02-01T10:50 | run_terminal_cmd | Run M24 tests | pytest tests/test_m24_calibration.py | ✅ Complete (29/30 passed, 1 fixed) |
| 2026-02-01T10:55 | search_replace | Add calibration CLI command | cli.py | ✅ Complete |
| 2026-02-01T11:00 | search_replace | Add calibration-eval CI job | .github/workflows/ci.yml | ✅ Complete |
| 2026-02-01T11:05 | read_file | Verify dependencies | pyproject.toml | ✅ Complete (no new deps needed) |
| 2026-02-01T11:10 | run_terminal_cmd | Create PR branch | git checkout -b m24-phase-d-calibration-001 | ✅ Complete |
| 2026-02-01T11:15 | run_terminal_cmd | Commit M24 changes | git commit | ✅ Complete (commit 4d09b8f) |
| 2026-02-01T11:20 | run_terminal_cmd | Push branch and create PR | gh pr create | ✅ Complete (PR #30) |
| 2026-02-01T11:25 | run_terminal_cmd | Monitor CI runs | gh run list | ✅ Complete |
| 2026-02-01T11:30 | run_terminal_cmd | Fix CI failures (format, MyPy) | ruff format, type fixes | ✅ Complete (commit 8cfdea0) |
| 2026-02-01T11:35 | run_terminal_cmd | Fix MyPy unused ignore | calibration_runner.py | ✅ Complete (commit 5935cd1) |
| 2026-02-01T11:40 | run_terminal_cmd | Analyze CI Run 1 | gh run view, generate M24_run1.md | ✅ Complete |

---

## Locked Decisions (M24)

1. **Frozen eval**: Use `FrozenEvalManifestV1`, require `--manifest` flag, include CI fixture
2. **Model artifacts**: Checkpoint-optional, CI uses baselines only
3. **Elo buckets**: Import from `src/renacechess/conditioning/buckets.py` (no duplication)
4. **CalibrationMetricsV1**: Full scope including outcome + policy metrics with fixed 10-bin histogram
5. **CI job**: Required check, fails on error/schema/determinism only (no thresholds)
6. **Artifacts**: Upload `calibration-metrics.json` via `actions/upload-artifact`

---

## Notes

This file tracks all tool invocations for M24 per the workflow rules in `.cursorrules`.

