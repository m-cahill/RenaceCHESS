# M31 Run Fix 1 — CI Workflow Analysis

**Document Type:** CI / Workflow Analysis  
**Template:** `docs/prompts/workflowprompt.md`

---

## Inputs (Mandatory)

### 1. Workflow Identity

| Field | Value |
|-------|-------|
| Workflow Name | CI (`.github/workflows/ci.yml`) |
| Run IDs | 21613590149, 21613824581, 21614123855 |
| Trigger | Pull Request #37 |
| Branch | `m31-frozen-eval-compat` |
| Commits | `fe2725c` → `800548e` → `e00896d` → `342d9a6` |

### 2. Change Context

| Field | Value |
|-------|-------|
| Milestone | M31: FULL-TRAINING-RUN-001 |
| Phase | E (Scale Proof, Training Run, Release Lock) |
| Objective | Fix FrozenEval V2 compatibility for training |
| Run Type | **Corrective** |

**Declared Intent:**  
M31 execution attempt #1 failed because training loaders expected `FrozenEvalManifestV1` but M30 produced `FrozenEvalManifestV2`. This PR adds a compatibility loader to support both schema versions.

### 3. Baseline Reference

| Field | Value |
|-------|-------|
| Last Trusted Green | `2707b1b` (M31 implementation merged) |
| Invariants | No changes to model architecture, hyperparameters, frozen eval v2, or training semantics |

---

## Step 1 — Workflow Inventory

### Jobs Executed (All 3 Runs)

| Job / Check | Required? | Purpose | Run 1 | Run 2 | Run 3 |
|-------------|-----------|---------|-------|-------|-------|
| Lint and Format | ✅ Yes | Code style enforcement | ❌ Fail | ✅ Pass | ✅ Pass |
| Type Check | ✅ Yes | Static type safety (mypy) | ✅ Pass | ✅ Pass | ✅ Pass |
| Security Scan | ✅ Yes | Vulnerability detection (bandit) | ✅ Pass | ✅ Pass | ✅ Pass |
| Test | ✅ Yes | Correctness + coverage | ⏳ Pending | ❌ Fail | ✅ Pass |
| Performance Benchmarks | ✅ Yes | Regression detection | ✅ Pass | ✅ Pass | ✅ Pass |
| Calibration Evaluation | ✅ Yes | Policy calibration | ✅ Pass | ✅ Pass | ✅ Pass |
| Recalibration Evaluation | ✅ Yes | Outcome calibration | ✅ Pass | ✅ Pass | ✅ Pass |
| Runtime Recalibration Guard (M26) | ✅ Yes | Guard gate | ✅ Pass | ✅ Pass | ✅ Pass |
| Runtime Recalibration Evaluation (M27) | ✅ Yes | Full recal eval | ✅ Pass | ✅ Pass | ✅ Pass |
| Frozen Eval V2 Validation (M30) | ✅ Yes | Eval set integrity | ✅ Pass | ✅ Pass | ✅ Pass |
| M31 Schema Validation | ✅ Yes | Training schemas | ✅ Pass | ✅ Pass | ✅ Pass |

**All 11 jobs are merge-blocking.**  
**No checks use `continue-on-error`.**  
**No checks are muted, weakened, or bypassed.**

---

## Step 2 — Signal Integrity Analysis

### A) Tests

| Aspect | Assessment |
|--------|------------|
| Tiers | Unit, integration, contract |
| Total Tests | 928 passed, 1 skipped |
| Coverage Enforcement | 90% minimum, non-regression on overlap set |
| New Test Files | `tests/test_frozen_eval_compat.py` (6 tests) |

**Run 2 Failure Analysis:**  
The Test job failed with coverage regression:
```
models/baseline_v1.py: 100.00% → 96.49% (delta: -3.51%)
```

This was a **real signal**, not flakiness. The cause was that lines 274-278 in `BaselinePolicyV1.forward()` were not deterministically covered by existing tests. The main branch achieved 100% through non-deterministic hash behavior that happened to cover those lines in CI but not consistently.

**Resolution:**  
Added `test_baseline_policy_v1_forward_mixed_vocab_coverage()` to deterministically cover the mixed-vocabulary code path.

### B) Coverage

| Aspect | Assessment |
|--------|------------|
| Type | Line + branch |
| Threshold | 90% global, non-regression on existing files |
| Comparison | Against `coverage-base.xml` from main |
| Exclusions | None undocumented |

**Coverage mechanism is sound.** The regression detection correctly identified a real coverage gap.

### C) Static / Policy Gates

| Gate | Status | Notes |
|------|--------|-------|
| Ruff lint | ✅ | Clean |
| Ruff format | ✅ | Required formatting fix in Run 1 |
| MyPy type check | ✅ | Clean |
| Import-linter | ✅ | Architecture rules enforced |
| Bandit security | ✅ | No vulnerabilities |

**Run 1 Failure Analysis:**  
```
Would reformat: src/renacechess/frozen_eval/compat.py
Would reformat: tests/test_frozen_eval_compat.py
```

This was a **procedural failure**, not a correctness issue. Fixed by running `ruff format`.

### D) Performance / Benchmarks

| Aspect | Assessment |
|--------|------------|
| Isolation | Benchmarks run in separate job |
| Contamination | None — benchmarks do not affect coverage or tests |
| Regression | None detected |

---

## Step 3 — Delta Analysis (Change Impact)

### Files Modified

| File | Type | Impact |
|------|------|--------|
| `src/renacechess/frozen_eval/compat.py` | **NEW** | Compatibility loader for V1/V2 manifests |
| `src/renacechess/frozen_eval/__init__.py` | Modified | Export new functions |
| `src/renacechess/models/training.py` | Modified | Use new loader (4 lines changed) |
| `src/renacechess/models/training_outcome.py` | Modified | Use new loader (4 lines changed) |
| `tests/test_frozen_eval_compat.py` | **NEW** | Compatibility tests (6 tests) |
| `tests/test_m08_model.py` | Modified | Coverage test for lines 274-278 |

### Signal Mapping

| Change | Affected Signals |
|--------|------------------|
| New compat.py | Test, Type Check, Lint |
| Training patches | Test (frozen eval loading), M31 Schema Validation |
| Coverage test | Test (coverage non-regression) |

### Unexpected Deltas

| Delta | Explanation | Action |
|-------|-------------|--------|
| `baseline_v1.py` coverage regression | Non-deterministic hash behavior in existing tests | Fixed by adding deterministic test |

**No signal drift, coupling issues, or hidden dependencies discovered.**

---

## Step 4 — Failure Analysis

### Run 1: Lint and Format (FAILED)

| Aspect | Value |
|--------|-------|
| Classification | Procedural / formatting |
| In Scope | Yes |
| Blocking | Yes (required gate) |
| Resolution | Applied `ruff format` to 2 files |

### Run 2: Test (FAILED)

| Aspect | Value |
|--------|-------|
| Classification | Coverage regression (real signal) |
| Root Cause | Lines 274-278 in `baseline_v1.py` not deterministically covered |
| In Scope | Yes (M31 corrective work) |
| Blocking | Yes (coverage non-regression is enforced) |
| Resolution | Added `test_baseline_policy_v1_forward_mixed_vocab_coverage()` |

**Failure Details:**
```
❌ Coverage regression detected:
  models/baseline_v1.py: 100.00% → 96.49% (delta: -3.51%)
```

**Analysis:**  
The main branch's 100% coverage was achieved through non-deterministic behavior of Python's `hash()` function, which varies between processes. In some CI runs, the hash collisions happened to exercise lines 274-278; in others, they did not.

The new test uses explicit vocabulary management to deterministically force the code path where some legal moves are in the vocabulary and some are not, ensuring 100% reproducible coverage.

### Run 3: All Jobs (PASSED)

No failures. All 11 jobs green.

---

## Step 5 — Invariants & Guardrails Check

| Invariant | Status | Evidence |
|-----------|--------|----------|
| Required CI checks enforced | ✅ Held | All 11 jobs required |
| No semantic scope leakage | ✅ Held | Coverage measures correctness, benchmarks measure performance |
| Release contracts preserved | ✅ Held | No schema changes, no eval data changes |
| Determinism preserved | ✅ Held | New loader maintains hash verification |
| Model architecture unchanged | ✅ Held | No changes to `baseline_v1.py` logic |
| Hyperparameters unchanged | ✅ Held | No training config changes |
| Frozen eval v2 unchanged | ✅ Held | Only reading manifest, no modifications |
| Training semantics unchanged | ✅ Held | Loader only normalizes access, not behavior |

**No invariant violations detected.**

---

## Step 6 — Verdict

> **Verdict:**  
> This run (Run 3, ID 21613824581) is **safe to merge**. The corrective patch successfully resolves the M31 execution blocker without violating any Phase E invariants. The two intermediate failures (formatting, coverage) were real signals that were addressed through proper fixes rather than workarounds. The coverage fix strengthens the test suite by eliminating reliance on non-deterministic hash behavior.

**✅ Merge approved**

---

## Step 7 — Next Actions

| Action | Owner | Scope | Milestone |
|--------|-------|-------|-----------|
| Await merge authorization | User | PR #37 | M31 |
| Merge PR #37 | User/Cursor | GitHub | M31 |
| Regenerate config lock | Cursor | New commit SHA | M31 |
| Re-run M31 training execution | Cursor | Phase 4 of M31 | M31 |

---

## Run Summary Table

| Run | ID | Commit | Result | Failure | Resolution |
|-----|-----|--------|--------|---------|------------|
| 1 | 21613590149 | `fe2725c` | ❌ | Lint: formatting needed | `ruff format` applied |
| 2 | 21613824581 | `800548e` | ❌ | Test: coverage regression | Added deterministic coverage test |
| 3 | 21614123855 | `e00896d` | ✅ | None | All 11 jobs pass |

---

## Appendix: Failure Logs

### Run 1 — Lint Failure

```
Would reformat: src/renacechess/frozen_eval/compat.py
Would reformat: tests/test_frozen_eval_compat.py
2 files would be reformatted, 152 files already formatted
##[error]Process completed with exit code 1.
```

### Run 2 — Coverage Failure

```
Files in base: 52
Files in head: 53
Overlap files compared: 52

❌ Coverage regression detected:
  models/baseline_v1.py: 100.00% → 96.49% (delta: -3.51%)
##[error]Process completed with exit code 1.
```

### Run 3 — Success

```
All 11 jobs passed in ~8 minutes
928 tests passed, 1 skipped
Coverage non-regression satisfied
```

---

**Document generated:** 2026-02-03  
**Author:** Cursor AI  
**Status:** Complete

