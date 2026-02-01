# M26 CI Run 3 Analysis

**Workflow Identity**
- Workflow: CI
- Run ID: 21572170439
- Trigger: Pull Request (#32)
- Branch: `m26-phase-d-runtime-gating-001`
- Commit: 337d10b (Run 2 analysis report)

**Change Context**
- Milestone: M26 (PHASE-D-RUNTIME-GATING-001)
- Intent: Governance and safety milestone for controlled runtime application of recalibration
- Type: Analysis/documentation (no code changes)
- Baseline: M25 (last known green: commit from M25 closeout)

---

## Step 1 — Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
| ----------- | --------- | ------- | --------- | ----- |
| Security Scan | ✅ Required | Dependency vulnerability scan (pip-audit) + static security analysis (bandit) | ✅ Pass | No security issues found |
| Test | ✅ Required | Unit + integration tests with coverage | ❌ Fail | 2 test failures (uniform probability edge case) |
| Performance Benchmarks | ✅ Required | Performance regression detection | ✅ Pass | No performance regressions |
| Lint and Format | ✅ Required | Ruff linting, formatting, import boundary checks | ✅ Pass | All formatting checks passed |
| Type Check | ✅ Required | MyPy static type checking | ✅ Pass | All type checks passed |
| Calibration Evaluation | ✅ Required | Calibration metrics validation | ✅ Pass | Calibration metrics generated successfully |
| Recalibration Evaluation | ✅ Required | Recalibration parameter fitting and validation | ✅ Pass | Recalibration parameters generated successfully |
| Runtime Recalibration Guard (M26) | ✅ Required | M26-specific guard job for byte-identical default path | ❌ Fail | Manifest version mismatch (expected, per locked decision) |

**Merge-blocking checks:** All required checks must pass for merge.

---

## Step 2 — Signal Integrity Analysis

### A) Tests

**Test tiers executed:**
- Unit tests (comprehensive M26 runtime recalibration tests)
- Integration tests (existing test suite)
- Contract tests (schema validation)

**Failures:**
- 2 failures in `test_m26_runtime_recalibration.py`
- Root cause: Test uses uniform probabilities `[0.25, 0.25, 0.25, 0.25]` and expects temperature scaling to change them
- Mathematical reality: Temperature scaling on uniform probabilities returns uniform probabilities (correct behavior)
- Tests affected:
  - `test_gate_enabled_applies_scaling` (policy)
  - `test_gate_scope_policy_only`

**Test coverage:**
- Overall coverage: 91.81% (above 90% threshold)
- `runtime_recalibration.py`: 87.37% (improved from 74.74% in Run 2)
- All other modules maintained or improved coverage

**Assessment:** Failures are **test design issues**, not correctness failures. Temperature scaling on uniform probabilities is mathematically correct to return uniform probabilities. Tests should use non-uniform probabilities to observe temperature scaling effects.

### B) Coverage

**Coverage type:** Line + branch coverage
- Enforced threshold: 90% (absolute)
- PR mode: Overlap-set comparison
- Coverage scoped correctly to source code
- Exclusions: None documented

**Coverage results:**
- Total: 91.81% (4586 statements, 256 missed, 1324 branches, 178 partial)
- New module `runtime_recalibration.py`: 87.37% (67 statements, 5 missed, 28 branches, 7 partial)
- Significant improvement from Run 2 (74.74% → 87.37%)

**Assessment:** Coverage is correctly scoped and continues to improve. Remaining gaps are in error handling paths.

### C) Static / Policy Gates

**Linting (Ruff):**
- ✅ All checks passed
- Format check passed (fixed in Run 2)
- No lint errors

**Type checking (MyPy):**
- ✅ All type checks passed
- No type errors

**Assessment:** All static gates are clean.

### D) Performance / Benchmarks

**Benchmark results:**
- All benchmarks passed
- No performance regressions detected
- Benchmarks isolated from correctness signals

**Assessment:** Performance signals are clean and isolated.

---

## Step 3 — Delta Analysis (Change Impact)

**Files modified since Run 2:**
- `docs/milestones/PhaseD/M26/M26_run2.md` (analysis report only, no code changes)

**CI signals affected:**
- **Tests:** 2 new failures (test design issue, not code bug)
- **Linting:** ✅ Fixed (all checks pass)
- **Type checking:** ✅ Fixed (all checks pass)
- **Coverage:** Improved (87.37% vs 74.74% in Run 2)

**Unexpected deltas:**
- Test failures revealed: uniform probability edge case in test design
- All other signals improved or remained stable

**Signal drift:**
- No drift detected. All existing signals remain stable.

**Coupling revealed:**
- None. M26 changes are properly isolated from Phase C contracts.

---

## Step 4 — Failure Analysis

### Failure 1: Test Failures (2 failures)

**Classification:** Test design issue (not a correctness bug)

**Root cause:**
- Tests use uniform probabilities `[0.25, 0.25, 0.25, 0.25]`
- Temperature scaling on uniform probabilities returns uniform probabilities (mathematically correct)
- Test incorrectly expects uniform probabilities to change under temperature scaling

**Mathematical explanation:**
- Uniform probabilities have equal logits: `log(0.25) = -1.386...` for all
- Dividing equal logits by temperature: `-1.386 / 0.5 = -2.772...` (still equal)
- After exp and renormalization: `[0.25, 0.25, 0.25, 0.25]` (unchanged)

**In scope:** ✅ Yes (M26 test suite)

**Blocking:** ✅ Yes (must fix before merge)

**Fix required:**
- Update tests to use non-uniform probabilities (e.g., `[0.4, 0.3, 0.2, 0.1]`)
- Temperature scaling will then produce observable changes
- Verify that temperature < 1.0 sharpens (peaks) and temperature > 1.0 flattens

### Failure 2: Runtime Recalibration Guard Job Failure

**Classification:** CI misconfiguration (expected per locked decision)

**Root cause:**
- Guard job uses `--dataset-manifest` which expects v2 manifest
- Frozen eval fixture is v1 manifest
- Error: "Expected manifest v2, got schema version: 1"

**In scope:** ✅ Yes (M26 CI job)

**Blocking:** ✅ Yes (M26-specific guard job must pass)

**Fix required:**
- Per locked decision: Simplify guard job to use unit/integration tests only
- Remove dependency on frozen eval manifests
- Validate byte-identical behavior via deterministic unit tests
- This aligns with M26's intent: runtime gating ≠ dataset evaluation

---

## Step 5 — Invariants & Guardrails Check

**Required CI checks remain enforced:** ✅ Yes
- All merge-blocking checks are still enforced
- No checks were muted or bypassed

**No semantic scope leakage:** ✅ Yes
- Coverage measures code coverage (not performance)
- Benchmarks measure performance (not correctness)
- Tests measure correctness (not performance)

**Release / consumer contracts not weakened:** ✅ Yes
- Phase C contracts remain untouched
- No changes to frozen contracts
- Provenance metadata is separate from Phase C artifacts

**Determinism and reproducibility preserved:** ✅ Yes
- Default path (gate disabled) is byte-identical (proven by unit tests)
- Recalibration application is deterministic (temperature scaling)
- Temperature scaling behavior is mathematically correct

**Invariant violations:** None detected (test failures are test design issues, not architectural violations)

---

## Step 6 — Verdict

**Verdict:**
This run shows **excellent progress** from Run 2:
- ✅ Formatting fixed (all checks pass)
- ✅ Type checking fixed (all checks pass)
- ✅ Coverage improved (87.37% vs 74.74%)
- ❌ 2 test failures (test design issue: uniform probability edge case)
- ❌ CI guard job manifest version (expected, per locked decision)

The remaining failures are **straightforward to fix**:
1. Update tests to use non-uniform probabilities (test design fix)
2. Simplify CI guard job per locked decision (remove manifest dependency)

**Status:** ⛔ **Merge blocked**

**Reason:** Test failures (uniform probability edge case) and CI guard job must be fixed.

---

## Step 7 — Next Actions

### Immediate Actions (M26 scope)

1. **Fix test design** (Owner: AI/Cursor)
   - Update `test_gate_enabled_applies_scaling` and `test_gate_scope_policy_only` to use non-uniform probabilities
   - Use probabilities like `[0.4, 0.3, 0.2, 0.1]` instead of `[0.25, 0.25, 0.25, 0.25]`
   - Verify temperature scaling produces observable changes
   - Scope: `tests/test_m26_runtime_recalibration.py`
   - Milestone: M26 (current)

2. **Simplify CI guard job** (Owner: AI/Cursor)
   - Remove `--dataset-manifest` dependency
   - Use unit/integration tests for byte-identical verification
   - Validate gate disabled → byte-identical, gate enabled → output differs
   - Scope: `.github/workflows/ci.yml`
   - Milestone: M26 (current)
   - **Rationale:** Per locked decision, runtime gating ≠ dataset evaluation

3. **Re-run CI after fixes** (Owner: GitHub Actions)
   - Verify all checks pass
   - Confirm byte-identical default path
   - Scope: Full CI run
   - Milestone: M26 (current)

### Deferred Actions

None. All issues are fixable within M26 scope.

---

## Summary

**Run Status:** ❌ Failed (6/8 jobs passed)

**Critical Issues:**
- Test design issue (uniform probability edge case)
- CI guard job manifest version (expected, per locked decision)

**Positive Signals:**
- ✅ Security scan passed
- ✅ Performance benchmarks passed
- ✅ Type checking passed
- ✅ Formatting passed
- ✅ Calibration/recalibration evaluation passed
- ✅ Coverage improved significantly (87.37% vs 74.74%)
- ✅ No architectural violations
- ✅ No Phase C contract changes

**Progress from Run 2:**
- Test failures: 4 → 2 (50% reduction)
- Format check: ❌ → ✅ (fixed)
- Coverage: 74.74% → 87.37% (17% improvement)
- All static gates: ✅ Clean

**Next Run Expectations:**
After fixing test design (non-uniform probabilities) and simplifying CI guard job (remove manifest dependency), all checks should pass. The implementation is sound; failures are test design issues and expected CI configuration.

---

**Analysis Date:** 2026-02-01  
**Analyst:** AI Agent (Cursor)  
**Milestone:** M26 (PHASE-D-RUNTIME-GATING-001)

