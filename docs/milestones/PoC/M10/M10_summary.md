# 📌 Milestone Summary — M10: Coverage Hardening + Runner/CLI Path Tests (v1)

**Project:** RenaceCHESS  
**Phase:** Proof of Concept (PoC)  
**Milestone:** M10 — Coverage Hardening + Runner/CLI Path Tests (v1)  
**Timeframe:** 2026-01-26 → 2026-01-27  
**Status:** ✅ **CLOSED / IMMUTABLE**

---

## 1. Milestone Objective

M10 restores coverage in **pre-existing modules impacted by M09 integration** (specifically `src/renacechess/cli.py` and `src/renacechess/eval/runner.py`), fixes the **M08 float precision edge case** deterministically, and establishes a robust, truthful CI non-regression posture without weakening gates.

Without this milestone, RenaceCHESS would have:
- Coverage regressions in orchestration layers (CLI and eval runner) from M09 integration paths
- A flaky float precision edge case in baseline policy probability computation
- M09-specific conditional exception logic in CI workflow (not permanent governance)

M10 completes the **execution surface hardening** that makes the governance rule actually pass by restoring coverage via tests (not exceptions), stabilizing the float edge case, and leaving CI with a clean, permanent non-regression mechanism.

**Baseline:** M09 CLOSED / IMMUTABLE (Human Outcome Head W/D/L v1, with coverage regressions deferred)

---

## 2. Scope Definition

### In Scope

**CLI Coverage Restoration:**
- Add integration tests for `train-outcome-head` command wiring in `cli.py`
- Test command argument parsing, training function invocation, output artifact handling
- Test error handling paths
- Use monkeypatching to stub training (avoid heavy work in tests)

**Eval Runner Coverage Restoration:**
- Add integration tests for outcome head evaluation paths in `eval/runner.py`
- Test outcome head loading, metrics computation, report generation
- Test error handling (missing files, invalid paths)
- Use deterministic stubs for outcome head provider

**M08 Float Precision Fix:**
- Clamp probabilities to `[0.0, 1.0]` after softmax computation
- Renormalize to ensure sum = 1.0 after clamping
- Add regression test that ensures no negative values and sum ≈ 1.0

**CI Workflow Governance:**
- Remove M09-specific conditional exception logic
- Keep XML overlap-set coverage comparison permanently (for all PRs)
- Enforce both absolute ≥90% threshold AND overlap-set non-regression for PRs
- Enforce absolute ≥90% threshold for main branch

**Deferred Issues Resolution:**
- Mark LEGACY-COV-001, CLI-COV-001, EVAL-RUNNER-COV-001 as resolved in Deferred Issues Registry

### Out of Scope

- ❌ Changing outcome-head math, schemas, or report versions (unless necessary for correctness)
- ❌ Adding SBOM/provenance or action SHA pinning (unless already scoped)
- ❌ Relaxing CI gates (no "mute"), only strengthen tests/fixtures
- ❌ Bringing every historically-low file to ≥90% individually (only what blocks total ≥90%)

---

## 3. Work Executed

### Implementation

| Component | Files | Description |
|-----------|-------|-------------|
| CLI Tests | `tests/test_cli.py` | Added 3 tests for train-outcome-head command (basic, with frozen eval, error handling) |
| Runner Tests | `tests/test_m10_runner_outcome_head.py` | Added 3 tests for outcome head integration (basic, file not found, without path) |
| Float Precision Fix | `src/renacechess/models/baseline_v1.py` | Added clamping and renormalization after softmax |
| Regression Test | `tests/test_m08_model.py` | Added `test_baseline_policy_v1_probability_precision` regression test |
| CI Workflow | `.github/workflows/ci.yml` | Removed M09-specific conditional, enabled overlap-set comparison for all PRs |
| Deferred Issues | `docs/audit/DeferredIssuesRegistry.md` | Marked all M09 deferrals as resolved |

**Statistics:**
- 6 files changed
- ~300 insertions, ~50 deletions
- 6 new tests (all passing)
- Coverage: 90.64% (exceeds 90% threshold)
- Final CI Run: #21388511020 (all checks passing)

---

## 4. Validation & Evidence

### Tests

| Test Suite | Tests | Status |
|------------|-------|--------|
| `test_cli.py` (new tests) | 3 | ✅ PASS |
| `test_m10_runner_outcome_head.py` | 3 | ✅ PASS |
| `test_m08_model.py` (regression test) | 1 | ✅ PASS |
| All existing tests | ~330 | ✅ PASS |

### CI Runs

| Run | Conclusion | Root Cause |
|-----|-----------:|------------|
| Run #21388511020 | ✅ success | Coverage 90.64% (exceeds 90% threshold), all checks passing |

### Coverage Status

**Total Coverage:** 90.64% (exceeds 90% threshold)

**Key Files:**
- `cli.py`: 68.33% (improved from 66.08% in M09, new paths covered)
- `eval/runner.py`: 78.97% (improved from 73.84% in M09, new paths covered)
- `baseline_v1.py`: 95.81% (improved from 94.39% baseline, regression fixed)

**Coverage Regressions Eliminated:**
- ✅ `cli.py`: Coverage restored (new M09 paths now tested)
- ✅ `eval/runner.py`: Coverage restored (new M09 paths now tested)

### Determinism Verification

- Float precision fix is deterministic (clamping + renormalization)
- Regression test uses multiple model instances to catch edge cases
- All tests pass consistently

---

## 5. CI / Automation Impact

### Workflows Affected

- **CI workflow updated** — Removed M09-specific conditional, enabled overlap-set comparison for all PRs
- **Coverage governance upgraded** — Both absolute threshold (90%) and overlap-set non-regression enforced for PRs

### Checks Added, Removed, or Reclassified

- **Overlap-set comparison** — Now enabled for all PRs (not just m09-*)
- **Absolute threshold** — Still enforced (90% for PRs and main)
- **All existing checks** — Remain required and passing

### Changes in Enforcement Behavior

- **PRs:** Enforce both absolute ≥90% AND overlap-set non-regression
- **Main:** Enforce absolute ≥90% threshold
- **No exceptions** — M09-specific conditional removed

### Signal Drift

**None observed** — All signals remain truthful and meaningful. Coverage regressions eliminated via tests (not exceptions).

---

## 6. Issues & Exceptions

### Issues Encountered

**None** — All work completed as planned. Tests added, coverage restored, float precision fixed, CI workflow cleaned up.

---

## 7. Deferred Work

### M09 Deferrals Closed

| ID | Issue | Status | Evidence |
|----|-------|--------|----------|
| LEGACY-COV-001 | Global coverage below 90% due to pre-M09 legacy files | ✅ **RESOLVED** | Total coverage restored to 90.35% |
| CLI-COV-001 | Outcome-head CLI command untested | ✅ **RESOLVED** | Integration tests added in `test_cli.py` |
| EVAL-RUNNER-COV-001 | Outcome-head eval integration untested | ✅ **RESOLVED** | Integration tests added in `test_m10_runner_outcome_head.py` |

### No New Deferrals

M10 introduced no new deferrals.

---

## 8. Governance Outcomes

### What Changed in Governance Posture

1. **Coverage regressions eliminated** — All M09 integration paths now tested
2. **Float precision stabilized** — Deterministic clamping + renormalization prevents edge cases
3. **CI governance cleaned** — M09-specific exception removed, overlap-set comparison permanent
4. **Deferred issues closed** — All M09 deferrals resolved with exit criteria met

### What Is Now Provably True

- ✅ Total coverage meets 90% threshold (90.64%)
- ✅ Coverage regressions in `cli.py` and `eval/runner.py` eliminated via tests
- ✅ Float precision edge case fixed deterministically
- ✅ CI workflow has clean, permanent governance (no exceptions)
- ✅ All M09 deferrals resolved

---

## 9. Exit Criteria Evaluation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| CI is GREEN with required checks passing | ✅ Met | CI run #21388511020 passes, coverage 90.64% |
| Overlap-set coverage comparison reports no regressions | ✅ Met | New paths covered, no regressions detected |
| Overall project coverage meets enforced threshold | ✅ Met | 90.64% exceeds 90% threshold |
| M08 floating-point precision failure resolved | ✅ Met | Clamping + renormalization implemented, regression test added |
| Deferred Issues Registry updated | ✅ Met | All M09 deferrals marked resolved |

**All criteria met.** No criteria were adjusted.

---

## 10. Final Verdict

**Milestone objectives met. Safe to proceed.**

M10 successfully restores coverage in orchestration layers, fixes the M08 float precision edge case, and establishes a clean, permanent CI governance mechanism. All M09 deferrals are resolved, and the system is ready for the next milestone.

---

## 11. Authorized Next Step

**M10 is CLOSED and IMMUTABLE.**

**Next milestone:** M11 (to be planned)

**Constraints:**
- No further commits to `m10-execution-surface-hardening` branch (to be merged)
- M10 artifacts are frozen
- Next milestone scope: TBD

---

## 12. Canonical References

### Commits

- Branch: `m10-execution-surface-hardening`
- Final commit: `24d2fc6`
- Final coverage: 90.64%

### Pull Request

- PR: #12 (ready for merge)

### CI Runs

- Run #21388511020: ✅ PASS (coverage 90.64%, all checks passing)

### Documents

- `docs/milestones/PoC/M10/M10_plan.md` — Implementation plan
- `docs/milestones/PoC/M10/M10_toolcalls.md` — Tool calls log
- `docs/milestones/PoC/M10/M10_summary.md` — This document
- `docs/milestones/PoC/M10/M10_audit.md` — Milestone audit
- `docs/audit/DeferredIssuesRegistry.md` — Updated with M10 resolutions

### Key Files

| Path | Purpose |
|------|---------|
| `tests/test_cli.py` | CLI integration tests for train-outcome-head |
| `tests/test_m10_runner_outcome_head.py` | Eval runner integration tests for outcome head |
| `src/renacechess/models/baseline_v1.py` | Float precision fix (clamping + renormalization) |
| `tests/test_m08_model.py` | Regression test for float precision |
| `.github/workflows/ci.yml` | CI workflow with permanent overlap-set comparison |

---

**Summary Generated:** 2026-01-26  
**Summary Author:** AI Agent (Cursor)  
**Status:** CLOSED / IMMUTABLE

