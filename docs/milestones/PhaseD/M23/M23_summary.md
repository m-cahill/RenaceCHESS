# 📌 Milestone Summary — M23: Phase D Hardening

**Project:** RenaceCHESS  
**Phase:** D (Data Expansion, Calibration & Quality)  
**Milestone:** M23 — PHASE-D-HARDENING-001  
**Timeframe:** 2026-02-01  
**Status:** Closed  

---

## 1. Milestone Objective

M23 established Phase D's hardened foundation by addressing audit findings from the Phase C closeout:

1. **Missing security scanning** — No dependency vulnerability or SAST checks in CI
2. **No performance regression visibility** — No benchmark harness to detect performance degradation
3. **CLI coverage gap** — CLI module at ~72% coverage (below 90% file-level target)
4. **DX friction** — No local pre-commit hooks for fast lint feedback

Without M23, Phase D would have begun with audit-flagged gaps in governance controls.

---

## 2. Scope Definition

### In Scope

- **Security CI job**: pip-audit (dependency vulnerabilities) + bandit (SAST)
- **Performance benchmark harness**: pytest-benchmark with artifact upload
- **CLI coverage uplift**: Systematic test coverage for help/dispatch/error paths
- **Pre-commit config**: Local DX guardrail (CI remains authoritative)
- **Documented deferrals**: torch CVEs (TORCH-SEC-001), CLI file-level target (CLI-COV-001)

### Out of Scope

- torch major version upgrade (deferred to future milestone)
- CLI coverage to 100% (84% achieved, remainder deferred)
- Performance timing thresholds (visibility-only per locked decision)
- CI enforcement of pre-commit (local-only per locked decision)

---

## 3. Work Executed

### A. Security CI Job

| Action | Count |
|--------|-------|
| New CI job added | 1 (`security`) |
| pip-audit integration | ✅ |
| bandit SAST integration | ✅ |
| CVEs ignored (documented) | 4 (torch) |
| bandit rules skipped | 1 (B614) |

**Result:** Security scanning is now a first-class CI signal.

### B. Performance Benchmark Harness

| Action | Count |
|--------|-------|
| New CI job added | 1 (`perf-benchmarks`) |
| Benchmark tests created | 10 |
| Artifact upload | ✅ (`benchmark-results.json`) |
| Timing thresholds | None (visibility-only) |

**Result:** Performance regression surface established without CI flakiness.

### C. CLI Coverage Uplift

| Action | Count |
|--------|-------|
| New test file created | 1 (`test_m23_cli_coverage.py`) |
| New tests added | 27 |
| CLI coverage before | ~72% |
| CLI coverage after | ~84% |
| Overall coverage | 92.20% |

**Result:** Material coverage improvement; file-level target documented as deferral.

### D. Pre-commit Config

| Action | Count |
|--------|-------|
| Config file created | 1 (`.pre-commit-config.yaml`) |
| Hooks configured | 2 (ruff lint, ruff format) |
| README documentation | ✅ |

**Result:** Local DX guardrail without CI duplication.

---

## 4. Artifacts Produced

### Files Created

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | Modified: +security, +perf-benchmarks jobs |
| `.pre-commit-config.yaml` | Local pre-commit hooks |
| `tests/test_m23_perf_benchmarks.py` | 10 benchmark tests |
| `tests/test_m23_cli_coverage.py` | 27 CLI coverage tests |
| `docs/milestones/PhaseD/M23/M23_plan.md` | Milestone plan |
| `docs/milestones/PhaseD/M23/M23_toolcalls.md` | Tool call log |
| `docs/milestones/PhaseD/M23/M23_run1.md` | CI Run 1 analysis |
| `docs/milestones/PhaseD/M23/M23_run2.md` | CI Run 2-4 analysis |
| `docs/milestones/PhaseD/M23/M23_audit.md` | Milestone audit |
| `docs/milestones/PhaseD/M23/M23_summary.md` | This document |

### Dependency Changes

| Package | Change |
|---------|--------|
| `requests` | `~=2.31.0` → `>=2.32.4` (CVE fix) |
| `pytest-benchmark` | Added `~=4.0.0` |
| `pip-audit` | Added `~=2.7.0` |
| `bandit` | Added `~=1.7.0` |

---

## 5. CI Behavior Changes

### New Jobs

| Job | Trigger | Failure Condition |
|-----|---------|-------------------|
| `security` | All PRs + push to main | pip-audit or bandit finds unignored issues |
| `perf-benchmarks` | All PRs + push to main | Benchmarks fail to execute (not timing) |

### Existing Jobs

| Job | Change |
|-----|--------|
| `lint` | No change |
| `typecheck` | No change |
| `test` | Coverage still 90% threshold |

---

## 6. Deferrals and Known Issues

### TORCH-SEC-001 (Deferred)

| Field | Value |
|-------|-------|
| Severity | Medium |
| CVEs | PYSEC-2025-41, PYSEC-2024-259, GHSA-3749-ghw9-m3mg, GHSA-887c-mr87-cxwp |
| Current Version | torch 2.2.2 |
| Required Version | 2.6.0+ |
| Rationale | Major version upgrade requires training validation |
| Mitigation | CI ignores via `--ignore-vuln`; no RemoteModule usage |

### CLI-COV-001 (Deferred)

| Field | Value |
|-------|-------|
| Severity | Low |
| Current Coverage | 84% |
| Target Coverage | 90% |
| Rationale | Remaining paths are low-value (help branches, complex integration) |
| Resolution | Opportunistic during Phase D UX/CLI expansion |

---

## 7. Verification and Acceptance

### CI Verification

| Run | ID | Status |
|-----|----|--------|
| 1 | 21556741625 | ❌ Format, security, benchmark cov |
| 2 | 21556935928 | ❌ torch CVEs not ignored |
| 3 | 21557031338 | ❌ bandit B614 |
| 4 | 21557136080 | ✅ All green |

### Coverage Verification

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Overall coverage | 92.20% | 90% | ✅ PASS |
| Overlap-set regression | 0 files | 0 | ✅ PASS |

### Test Count

| Before M23 | After M23 | Delta |
|------------|-----------|-------|
| 613 | 649 | +36 |

---

## 8. Governance Compliance

| Check | Status |
|-------|--------|
| Single milestone branch | ✅ `m23-phase-d-hardening-001` |
| PR to main (not direct push) | ✅ PR #29 |
| Coverage gates preserved | ✅ 92.20% |
| Security findings addressed or deferred | ✅ |
| All deferrals documented | ✅ |
| Phase D runway established | ✅ |

---

## 9. What This Unlocks

M23 establishes Phase D's hardened foundation:

1. **Security scanning enforced** — Vulnerabilities detected at PR time
2. **Performance regression visibility** — Benchmark artifacts for comparison
3. **Stable CI truth posture** — All signals green and meaningful
4. **No unresolved hidden debt** — All deferrals documented

### Authorized Next Moves

- **M24+**: Phase D data expansion, calibration, UX
- Human evaluation loops
- CLI/UI evolution (absorbs remaining CLI coverage)
- External demos or partner review

---

## 10. Lessons Learned

1. **Security scanning surfaced real findings**: requests CVE was immediately fixable; torch CVE correctly deferred
2. **Coverage threshold on benchmark job**: Required explicit `--no-cov` to prevent false failure
3. **bandit B614 (torch.save)**: False positive for state_dict pattern; correctly acknowledged
4. **First-run failures are expected**: Enterprise audit posture is "fail → analyze → fix → verify"

---

## Appendix: Commit History

| Commit | Message |
|--------|---------|
| `a7de663` | feat(M23): add security scanning, perf benchmarks, CLI coverage, pre-commit |
| `b11aa35` | fix(M23): address CI Run 1 failures |
| `e625e1c` | fix(M23): ignore deferred torch CVEs in pip-audit |
| `2b2ce4f` | fix(M23): skip B614 in bandit (torch.save is safe pattern) |
| `a706c84` | docs(M23): add Run 2 consolidated analysis - CI GREEN |

---

**Milestone M23 is CLOSED.**



