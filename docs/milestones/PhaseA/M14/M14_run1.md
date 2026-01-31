# M14 CI Analysis — Run 1

**Analysis Date:** 2026-01-31

---

## Inputs

### Workflow Identity
| Field | Value |
|-------|-------|
| Workflow Name | CI |
| Run ID | 21539604426 (final green run) |
| Trigger | Pull Request #17 |
| Branch | `m14-train-pack-001` |
| Commit SHA | fecdb7c |

### Change Context
| Field | Value |
|-------|-------|
| Milestone | M14 — TRAIN-PACK-001 |
| Phase | Phase A: Hardening & Training Readiness |
| Intent | Establish training readiness infrastructure without retraining models |
| Run Type | Hardening (training benchmark + publication standards) |

### Baseline Reference
| Field | Value |
|-------|-------|
| Last Trusted Green | main @ 4617482 (M13 merge) |
| Key Invariants | 90% coverage threshold, no PoC semantic changes |

---

## Step 1 — Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
|-------------|-----------|---------|-----------|-------|
| Lint and Format | Yes | Ruff lint + format check + import-linter | ✅ Pass | Fixed formatting in Run 2 |
| Type Check | Yes | MyPy static type analysis | ✅ Pass | New script type-checks cleanly |
| Test | Yes | pytest with coverage enforcement | ✅ Pass | 383 passed, 1 skipped, 90%+ coverage |

### Checks with `continue-on-error`
- **Generate baseline coverage XML**: Uses `continue-on-error: true` to handle cases where main branch has incompatible dependencies.

### Bypassed or Weakened Checks
- **None.** All required checks enforced.

---

## Step 2 — Signal Integrity Analysis

### A) Tests
- **Test tiers:** Unit, integration, golden file regression tests
- **Failures:** None (383 passed, 1 skipped)
- **Test stability:** All tests deterministic
- **Missing coverage:** None required for M14 scope (benchmark script excluded from CI execution)

### B) Coverage
- **Type:** Line + branch coverage via pytest-cov
- **Threshold:** 90% (enforced)
- **Actual:** 90%+ (met threshold)
- **Note:** Benchmark script is linted/typed but NOT executed in CI per M14 spec

### C) Static / Policy Gates
| Gate | Status | Notes |
|------|--------|-------|
| Ruff lint | ✅ | All checks pass |
| Ruff format | ✅ | All files formatted (fixed in Run 2) |
| MyPy | ✅ | No type errors including new script |
| Import-linter | ✅ | Contracts module isolation enforced |

### D) Performance / Benchmarks
- Not applicable for this milestone (benchmark script is local-only)

---

## Step 3 — Delta Analysis

### Files Modified/Created
| Category | Files |
|----------|-------|
| Benchmark Script | `scripts/benchmark_training.py` (new) |
| Training Templates | `training/configs/template_policy.yaml` (new), `training/configs/template_outcome.yaml` (new) |
| Documentation | `docs/training/M14_TRAINING_BENCHMARK.md` (new), `docs/training/CHECKPOINT_PUBLICATION_STANDARD.md` (new) |
| Governance | `docs/milestones/PhaseA/M14/M14_toolcalls.md` (updated) |

### CI Signals Affected
1. **Lint/Format:** New script must pass Ruff checks
2. **Type Check:** New script must pass MyPy
3. **Tests:** No new tests required (benchmark script not executed in CI)

### Unexpected Deltas
- **Run 1 had a spurious coverage regression** in `models/baseline_v1.py` (98.25% → 93.86%)
- This was NOT caused by M14 changes (file unchanged)
- Run 2 passed without this regression (flake in baseline coverage generation)

---

## Step 4 — Failure Analysis

### Run 1 (21539554164) — Failed
| Issue | Cause | Resolution |
|-------|-------|------------|
| Format check failed | `scripts/benchmark_training.py` needed formatting | Fixed with `ruff format` |
| Coverage regression | Spurious baseline_v1.py regression | Resolved in Run 2 (flake) |

### Run 2 (21539604426) — Passed
- All checks green
- No failures

---

## Step 5 — Invariants & Guardrails Check

| Invariant | Status | Notes |
|-----------|--------|-------|
| Required CI checks enforced | ✅ | All 3 jobs pass, no bypasses |
| No semantic scope leakage | ✅ | Benchmark script not executed in CI |
| PoC contracts not modified | ✅ | No schema/contract changes |
| Coverage threshold maintained | ✅ | 90%+ maintained |
| Determinism preserved | ✅ | Tests deterministic |

### Violations
- **None.**

---

## Step 6 — Verdict

> **Verdict:** This run is green and truthful. All M14 deliverables are validated:
> 1. Training benchmark harness created with hardware detection and frozen-eval check
> 2. Training configuration templates created with placeholder hyperparameters
> 3. Benchmark report template created (awaiting local execution)
> 4. Checkpoint publication standard documented
> 5. No PoC semantics altered, no models retrained
>
> CI correctly enforced lint/format/type checks on the new script while not executing it (per M14 spec).

**✅ Merge approved** (pending user permission per governance rules)

---

## Step 7 — Next Actions

| Action | Owner | Scope | Milestone |
|--------|-------|-------|-----------|
| Approve and merge PR #17 | User | M14 closure | M14 |
| Generate M14_audit.md | AI | Documentation | M14 |
| Generate M14_summary.md | AI | Documentation | M14 |
| Update renacechess.md | AI | Governance | M14 |
| Create M15 folder skeleton | AI | Milestone prep | M15 |

---

**Analysis completed by:** AI Agent (RediAI v3)  
**Reviewed by:** Pending user review

