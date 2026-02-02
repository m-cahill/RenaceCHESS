# M27 CI Workflow Analysis — Run 4

**Generated:** 2026-02-02T04:04:40Z

---

## Inputs (Mandatory)

### 1. Workflow Identity

| Field | Value |
|-------|-------|
| Workflow name | CI |
| Run ID | 21576813444 |
| Trigger | pull_request |
| Branch | m27-runtime-recalibration-eval |
| Commit SHA | e5e734684a99404f0d73920763f23ee33ea58af2 |
| URL | https://github.com/m-cahill/RenaceCHESS/actions/runs/21576813444 |

### 2. Change Context

| Field | Value |
|-------|-------|
| Milestone | M27 — Runtime Recalibration Evaluation |
| Phase | Phase D (Data Expansion, Calibration & Quality) |
| Objective | Evaluate real-world impact of runtime recalibration under controlled conditions |
| Run type | **Corrective** (4th attempt after fixing MyPy, Ruff, and coverage issues) |

### 3. Baseline Reference

| Field | Value |
|-------|-------|
| Last trusted green | M26 (main branch after M26 merge) |
| Invariants | No Phase C contract changes, default behavior unchanged, 90% coverage threshold |

---

## Step 1 — Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
|-------------|-----------|---------|-----------|-------|
| **Type Check** | ✅ Yes | MyPy static type checking | ✅ Pass | All type errors resolved |
| **Lint and Format** | ✅ Yes | Ruff lint + format check | ✅ Pass | All formatting applied |
| **Security Scan** | ✅ Yes | pip-audit + bandit | ✅ Pass | No vulnerabilities |
| **Test** | ✅ Yes | pytest + coverage | ✅ Pass | 795 tests, 90.90% coverage |
| **Calibration Evaluation** | ✅ Yes | M24 calibration pipeline | ✅ Pass | Schema validated |
| **Recalibration Evaluation** | ✅ Yes | M25 recalibration pipeline | ✅ Pass | Schema validated |
| **Runtime Recalibration Guard (M26)** | ✅ Yes | M26 runtime gating tests | ✅ Pass | 2 tests passed |
| **Runtime Recalibration Evaluation (M27)** | ✅ Yes | M27 evaluation harness | ✅ Pass | Determinism verified |
| **Performance Benchmarks** | ⚪ Informational | pytest-benchmark | ✅ Pass | No regressions |

**Merge-blocking checks:** All 9 jobs are required and passing.  
**Informational checks:** Performance Benchmarks (does not block merge).  
**Bypassed/muted checks:** None.

---

## Step 2 — Signal Integrity Analysis

### A) Tests

| Aspect | Finding |
|--------|---------|
| Test tiers | Unit, integration, contract validation |
| Test count | 795 passed, 1 skipped |
| New tests | 25 tests in `test_m27_runtime_recalibration_eval.py` |
| Coverage mode | Line + branch, 90% fail-under threshold |
| Test stability | All tests deterministic, no flakes observed |

### B) Coverage

| Aspect | Finding |
|--------|---------|
| Type | Line + branch coverage |
| Threshold | 90% fail-under (enforced) |
| Result | **90.90%** (above threshold) |
| Overlap-set check | ✅ Passed — cli.py coverage maintained |
| M27 file coverage | `runtime_recalibration_eval_runner.py` at 92.10% |

### C) Static / Policy Gates

| Gate | Status | Notes |
|------|--------|-------|
| Ruff lint | ✅ Pass | No errors |
| Ruff format | ✅ Pass | All files formatted |
| MyPy | ✅ Pass | No type errors |
| Import boundary | ✅ Pass | import-linter contracts enforced |
| Security (bandit) | ✅ Pass | No issues |
| Dependency audit | ✅ Pass | No known vulnerabilities |

### D) Performance / Benchmarks

| Aspect | Finding |
|--------|---------|
| Isolation | Benchmarks run in separate job |
| Impact | No contamination of coverage or test signals |
| Regressions | None detected |

---

## Step 3 — Delta Analysis (Change Impact)

### Files Modified

| Category | Files |
|----------|-------|
| New schemas | `runtime_recalibration_report.v1.schema.json`, `runtime_recalibration_delta.v1.schema.json` |
| Models | `contracts/models.py` (new Pydantic models) |
| Runner | `eval/runtime_recalibration_eval_runner.py` (new) |
| CLI | `cli.py` (new subcommand) |
| CI | `.github/workflows/ci.yml` (new job) |
| Tests | `test_m27_runtime_recalibration_eval.py` (new) |
| Fixtures | `recalibration_gate.json`, `recalibration_params.json` (new) |
| Bugfix | `test_m25_recalibration.py` (Windows Unicode fix) |

### CI Signals Affected

| Signal | Impact |
|--------|--------|
| Type Check | New models validated |
| Lint/Format | New files formatted |
| Test | New test file exercised |
| Coverage | New code covered at 92%+ |
| M27 Job | New job validates artifacts |

### Unexpected Deltas

None. All deltas are expected for the M27 implementation.

---

## Step 4 — Failure Analysis

**No failures in Run 4.**

### Historical Failures (Runs 1-3)

| Run | Failure | Classification | Resolution |
|-----|---------|----------------|------------|
| Run 1 | MyPy type errors | Correctness (type safety) | Renamed variables to avoid shadowing |
| Run 2 | Ruff format check | Policy violation | Ran `ruff format` |
| Run 3 | Coverage regression (cli.py) | Test coverage gap | Added direct CLI tests |

All failures were **in scope** for M27 and resolved within the milestone.

---

## Step 5 — Invariants & Guardrails Check

| Invariant | Status | Evidence |
|-----------|--------|----------|
| Required CI checks enforced | ✅ Held | All 9 jobs required and passing |
| No semantic scope leakage | ✅ Held | Coverage measures tests, benchmarks separate |
| Phase C contracts unchanged | ✅ Held | No modifications to existing contracts |
| Default behavior unchanged | ✅ Held | Runtime gating disabled by default |
| Determinism preserved | ✅ Held | M27 CI job runs determinism check (hashes match) |
| 90% coverage threshold | ✅ Held | 90.90% achieved |
| Coverage non-regression | ✅ Held | cli.py overlap-set check passed |

**No invariant violations detected.**

---

## Step 6 — Verdict

> **Verdict:**  
> This run is safe to merge. All 9 CI jobs pass, including the new M27 runtime recalibration evaluation job. The implementation satisfies all M27 exit criteria: new `RuntimeRecalibrationReportV1` and `RuntimeRecalibrationDeltaV1` artifacts are produced, schema-validated, and deterministic. Coverage is 90.90% (above threshold), all type checks pass, and no Phase C contracts were modified. The default runtime behavior remains unchanged per M27 constraints.

**✅ Merge approved**

---

## Step 7 — Next Actions

| Action | Owner | Scope | Milestone |
|--------|-------|-------|-----------|
| Await merge permission | User | Gate | M27 |
| Generate M27_audit.md | AI/Cursor | M27 closeout | M27 |
| Generate M27_summary.md | AI/Cursor | M27 closeout | M27 |
| Update renacechess.md milestone table | AI/Cursor | Governance | M27 |
| Create M28 folder and seed files | AI/Cursor | Next milestone prep | M28 |

---

## Appendix: Job Execution Timeline

| Job | Start | End | Duration |
|-----|-------|-----|----------|
| Security Scan | 03:57:21 | 04:00:29 | 3m 8s |
| Lint and Format | 03:57:21 | 04:00:32 | 3m 11s |
| Runtime Recalibration Guard (M26) | 03:57:21 | 04:00:33 | 3m 12s |
| Calibration Evaluation | 03:57:21 | 04:00:41 | 3m 20s |
| Performance Benchmarks | 03:57:22 | 04:00:45 | 3m 23s |
| Recalibration Evaluation | 03:57:21 | 04:00:47 | 3m 26s |
| Runtime Recalibration Evaluation (M27) | 03:57:21 | 04:00:52 | 3m 31s |
| Type Check | 03:57:21 | 04:01:20 | 3m 59s |
| Test | 03:57:22 | 04:04:40 | 7m 18s |

**Total workflow duration:** ~7m 20s

