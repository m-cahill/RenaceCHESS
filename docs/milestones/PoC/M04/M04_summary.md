# 📌 Milestone Summary — M04: Evaluation Harness v0

**Project:** RenaceCHESS  
**Phase:** PoC  
**Milestone:** M04 — Evaluation Harness v0: Deterministic Policy Evaluation Over Dataset Manifests  
**Timeframe:** 2026-01-23 → 2026-01-24  
**Status:** ✅ **Closed**

---

## 1. Milestone Objective

M04 addressed the gap between M03's deterministic dataset assembly with manifest v2 and the ability to evaluate policy providers over those datasets. Without M04, RenaceCHESS would have been limited to dataset generation without any means to measure policy behavior, validate baselines, or produce evaluation reports for downstream model development.

The milestone built on M00's foundation (deterministic hashing, versioned contracts), M01-M03's dataset pipeline (JSONL shards, manifest v2, provenance) to create a deterministic evaluation harness that:
- Reads datasets via manifest v2 + JSONL shards (streaming, no full buffering)
- Runs policy providers (baselines) over dataset records
- Emits schema-validated evaluation reports with stable hashes and byte-stable outputs
- Focuses on policy validity metrics (legality, distribution, entropy) rather than ground-truth accuracy

> **What would have been incomplete or unsafe if this milestone did not exist?**
>
> Without M04, RenaceCHESS would be unable to evaluate policy providers over datasets, making it impossible to measure policy behavior, validate baselines, or produce evaluation reports. This would prevent reproducible policy evaluation and make downstream model development unreliable.

---

## 2. Scope Definition

### In Scope

**Components:**
- Evaluation harness package (`src/renacechess/eval/`)
- Evaluation report schema v1 (`eval_report.v1.schema.json`)
- Pydantic models for evaluation reports (`EvalReportV1`, `EvalMetricsV1`, etc.)
- CLI evaluation command (`renacechess eval run`)
- Baseline policy providers (`baseline.uniform_random`, `baseline.first_legal`)

**Subsystems:**
- Streaming evaluation over dataset manifests (line-by-line JSONL processing)
- Policy validity metrics computation (illegal rate, top-K coverage, entropy, cardinality)
- Deterministic seeded RNG for reproducible baseline policies
- Per-split metric breakdown (train/val/frozenEval)
- Byte-stable report serialization (canonical JSON)

**Workflows:**
- Evaluation runner that reads manifest v2 and processes shards in order
- Metrics accumulation and aggregation
- Report generation with schema validation
- Golden determinism tests (byte-identical outputs across runs)

**Contracts:**
- Evaluation Report schema v1 (JSON Schema)
- Pydantic models matching schema exactly
- Schema validation tests

**Documents:**
- `docs/EVALUATION.md` — Evaluation harness documentation
- `docs/milestones/PoC/M04/` — Plan, toolcalls, run analyses, audit, summary

### Out of Scope

**Explicitly deferred:**
- Ground-truth accuracy metrics (requires labeled records with `chosenMove` field; deferred to M05+)
- Stockfish-based evaluation / lichess accuracy metrics (engine dependency; deferred to M05+)
- Engine-vs-engine arenas / SPRT harness (deferred to M05+)
- Training loop (deferred to future milestones)
- Cloud persistence / dashboards (deferred to future milestones)

**Intentionally untouched:**
- Dataset building pipeline (M03 scope)
- Ingestion pipeline (M02 scope)
- Contract definitions (M00 scope)

**Scope changes:** None — scope remained stable throughout execution. The decision to defer ground-truth accuracy (made during Phase 2 clarifying questions) was a scope clarification, not a change.

---

## 3. Work Executed

### High-Level Actions

1. **Evaluation Report v1 schema creation** — Created new versioned schema with:
   - Policy validity metrics (illegal rate, top-K legal coverage, policy entropy, unique moves emitted)
   - Per-split metric breakdown (train/val/frozenEval)
   - Stable dataset identity fields (datasetDigest, assemblyConfigHash)
   - Fixed-decimal string formatting for byte-stability

2. **Evaluation harness package** — Implemented complete eval package with:
   - `interfaces.py` — PolicyProvider protocol
   - `baselines.py` — Two baseline providers (uniform_random with seeded RNG, first_legal)
   - `metrics.py` — MetricsAccumulator for policy validity metrics
   - `runner.py` — Streaming evaluation runner over dataset manifests
   - `report.py` — Report generation and canonical JSON serialization

3. **CLI integration** — Extended `cli.py` with:
   - `renacechess eval run` command
   - `--dataset-manifest` flag (v2 manifest path)
   - `--policy` flag (baseline policy IDs)
   - `--out` flag (output directory)
   - `--max-records` flag (optional limit)
   - `--created-at` flag (test-only timestamp override)

4. **Test coverage expansion** — Added 4 new test files:
   - `test_eval_baselines.py` — Baseline policy provider tests (6 tests)
   - `test_eval_metrics.py` — Metrics computation tests (7 tests)
   - `test_eval_integration.py` — Integration and golden determinism tests (5 tests)
   - `test_eval_report_schema.py` — Schema validation tests (2 tests)

**Statistics:**
- 30 files changed, 3,128 insertions(+), 15 deletions(-)
- 180 tests (up from 160 in M03, +20 new tests)
- Coverage: Meets 90% threshold (CI job passed)

---

## 4. Validation & Evidence

### Tests Run

**CI Tests:**
- **Run 1 (21306101033):** 180/180 tests passed, coverage met threshold, formatting failure only
- **Run 2 (21306130316):** 180/180 tests passed, coverage met threshold, fully green

**Test Types:**
- Unit tests (baseline policies, metrics computation)
- Integration tests (end-to-end evaluation over datasets)
- Golden file tests (determinism checks, byte-identical outputs)
- Schema validation tests (eval report v1)

**Enforcement Mechanisms:**
- Ruff linting: ✅ Enforced and passing
- Ruff formatting: ✅ Enforced and passing (after Run 1 fix)
- MyPy type checking: ✅ Enforced and passing
- Pytest with coverage gate: ✅ Enforced and passing (meets 90% threshold)

### Failures Encountered

**Run 1 Formatting Failure:**
- **Observation:** 1 file needed auto-formatting by Ruff (`src/renacechess/contracts/models.py`)
- **Root Cause:** Manual line length fixes not followed by auto-formatting
- **Resolution:** Ran `ruff format`, committed, pushed
- **Status:** ✅ Resolved in Run 2

**No correctness failures** — All tests passed in both runs.

### Evidence of Validation Meaningfulness

- **Determinism verified:** Golden tests confirm byte-identical outputs from identical inputs
- **Schema validation:** Evaluation report schema validated against JSON Schema
- **Coverage discipline:** Coverage meets 90% threshold
- **Type safety:** MyPy passes with no errors or warnings
- **Policy validity:** Metrics correctly measure legality, distribution, and entropy

---

## 5. CI / Automation Impact

### Workflows Affected

**CI Workflow:**
- No workflow changes
- All existing checks enforced (lint, format, type, test, coverage)
- No new checks added
- No checks removed or weakened

### Checks Added, Removed, or Reclassified

**None** — All checks remain as-is from M03.

### Changes in Enforcement Behavior

**None** — Enforcement behavior unchanged:
- Coverage threshold: 90% (maintained)
- Type checking: Strict (maintained)
- Linting: Enforced (maintained)
- Formatting: Enforced (maintained)

### Signal Drift Observed

**None** — All signals remain truthful:
- Tests correctly identify correctness issues
- Coverage correctly measures code coverage
- Type checking correctly identifies type errors
- Formatting correctly identifies style issues

### CI Truthfulness Assessment

✅ **CI blocked incorrect changes:** Run 1 formatting failure correctly identified and blocked merge  
✅ **CI validated correct changes:** Run 2 fully green, all checks passing  
✅ **CI did not fail to observe relevant risk:** No correctness issues missed

---

## 6. Issues & Exceptions

### Issues Encountered

**Issue 1: Formatting Failure (Run 1)**
- **Description:** 1 file needed auto-formatting by Ruff
- **Root Cause:** Manual line length fixes not followed by auto-formatting
- **Resolution Status:** ✅ Resolved (Run 2)
- **Tracking Reference:** `docs/milestones/PoC/M04/M04_run1.md`, `M04_run2.md`

**No other issues** — All other checks passed in both runs.

---

## 7. Deferred Work

### Deferred Items

**Explicitly deferred in M04 plan:**
- Ground-truth accuracy metrics (requires labeled records with `chosenMove` field)
- Stockfish-based evaluation / lichess accuracy metrics (engine dependency)
- Engine-vs-engine arenas / SPRT harness
- Training loop
- Cloud persistence / dashboards

**Status:** All deferred items remain deferred — no status changes as a result of M04 work.

**Rationale for deferring accuracy:** Current dataset records represent decision contexts (positions), not decisions (moves). Adding `chosenMove` would require retroactive schema changes and violate milestone discipline. M04 focuses on policy validity (legality, distribution, entropy) rather than correctness vs human play.

---

## 8. Governance Outcomes

### What Changed in Governance Posture

**Enforcement strengthened:**
- ✅ All CI gates remain enforced (no weakening)
- ✅ Coverage threshold maintained (90%)
- ✅ Type checking remains strict
- ✅ Formatting enforcement maintained

**Ambiguity removed:**
- ✅ Evaluation process is now deterministic and auditable
- ✅ Policy validity metrics are clearly defined (legality, distribution, entropy)
- ✅ Ground-truth accuracy is explicitly deferred (not in scope for M04)
- ✅ Evaluation report schema provides stable report identity

**Boundaries clarified:**
- ✅ Evaluation harness is separate from dataset building (M03) and training (future)
- ✅ Policy validity evaluation is separate from ground-truth accuracy (M05+)
- ✅ Streaming evaluation is deterministic (no parallel processing)

**Risks reduced or isolated:**
- ✅ Deterministic seeded RNG ensures reproducible baseline policies
- ✅ Byte-stable report outputs enable regression detection
- ✅ Fixed-decimal string formatting prevents float precision issues

### What Is Now Provably True

1. **Deterministic evaluation:** Given identical inputs and configuration, RenaceCHESS will always produce byte-identical evaluation reports.
2. **Policy validity metrics:** Evaluation reports include measurable policy validity metrics (illegal rate, top-K coverage, entropy, cardinality).
3. **Streaming evaluation:** Evaluation processes datasets line-by-line without full buffering, enabling memory-efficient evaluation of large datasets.
4. **Baseline policies:** Two deterministic baseline policies are available for evaluation (`baseline.first_legal`, `baseline.uniform_random`).

---

## 9. Exit Criteria Evaluation

### Original Success Criteria (from M04 Plan)

1. ✅ **`renacechess eval run` works end-to-end**
   - **Evidence:** CLI command implemented, tested, and working
   - **Status:** Met

2. ✅ **Evaluation report contract exists and validates**
   - **Evidence:** `eval_report.v1.schema.json` created, Pydantic models implemented, validation tests pass
   - **Status:** Met

3. ✅ **Determinism proven via golden test**
   - **Evidence:** `test_eval_report_golden_bytes` passes with byte-identical outputs
   - **Status:** Met

4. ✅ **Streaming evaluation works**
   - **Evidence:** Runner processes JSONL shards line-by-line, no full-load requirement
   - **Status:** Met

5. ✅ **At least 2 baseline policy providers implemented**
   - **Evidence:** `baseline.uniform_random` and `baseline.first_legal` implemented and tested
   - **Status:** Met

6. ✅ **CI fully green**
   - **Evidence:** Run 2 (21306130316) fully green, all checks passing
   - **Status:** Met

7. ✅ **Closeout artifacts created**
   - **Evidence:** `M04_run1.md`, `M04_run2.md`, `M04_audit.md`, `M04_summary.md` generated
   - **Status:** Met

**Overall Status:** ✅ **All exit criteria met**

---

## 10. Final Verdict

**Milestone objectives met. Safe to proceed.**

M04 successfully implemented deterministic evaluation harness with policy validity metrics, baseline providers, and byte-stable report outputs. All gates passing, no regressions, ready for M05 planning.

---

## 11. Authorized Next Step

**M05 planning** — M04 is complete and immutable. Next milestone can proceed with:
- Ground-truth accuracy metrics (if labeled records are available)
- Stockfish-based evaluation
- Model training infrastructure
- Or other authorized directions

**Constraints:**
- M04 codebase is frozen (no further commits to M04)
- All follow-ups start on M05
- CI history preserved as canonical evidence

---

## 12. Canonical References

### Commits

- **M04 Initial:** `f386b1e` — M04: Evaluation Harness v0 - Deterministic Policy Evaluation Over Dataset Manifests
- **M04 Formatting Fix:** `76121b2` — M04: Fix formatting in contracts/models.py
- **M04 Run Analysis:** `c342498` — M04: Add CI run analysis reports (Run 1 and Run 2)

### Pull Requests

- **PR #6:** `m04-eval-harness → main` — Created 2026-01-24

### Documents

- **Plan:** `docs/milestones/PoC/M04/M04_plan.md`
- **Tool Calls:** `docs/milestones/PoC/M04/M04_toolcalls.md`
- **Run 1 Analysis:** `docs/milestones/PoC/M04/M04_run1.md`
- **Run 2 Analysis:** `docs/milestones/PoC/M04/M04_run2.md`
- **Audit:** `docs/milestones/PoC/M04/M04_audit.md`
- **Summary:** `docs/milestones/PoC/M04/M04_summary.md` (this document)

### CI Runs

- **Run 1:** 21306101033 — Failed (formatting only)
- **Run 2:** 21306130316 — Passed (fully green)

### Issue Trackers

- **None** — No issues tracked externally

### Audit Artifacts

- **Audit Report:** `docs/milestones/PoC/M04/M04_audit.md`
- **CI Analysis Reports:** `docs/milestones/PoC/M04/M04_run1.md`, `M04_run2.md`

---

**Generated:** 2026-01-24  
**Status:** ✅ **M04 CLOSED / IMMUTABLE**

