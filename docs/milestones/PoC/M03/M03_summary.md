# 📌 Milestone Summary — M03: Deterministic Multi-Shard Dataset Assembly

**Project:** RenaceCHESS  
**Phase:** PoC  
**Milestone:** M03 — Deterministic Multi-Shard Dataset Assembly  
**Timeframe:** 2026-01-23 → 2026-01-23  
**Status:** ✅ **Closed**

---

## 1. Milestone Objective

M03 addressed the gap between M02's deterministic ingestion with provenance receipts and the ability to assemble multiple ingested artifacts into stable, bounded, reproducible datasets. Without M03, RenaceCHESS would have been limited to processing individual PGN files or receipts in isolation, making it impossible to create unified datasets from multiple sources with deterministic sharding and split assignments.

The milestone built on M00's foundation (deterministic hashing, versioned contracts), M01's dataset materialization (JSONL shards, manifest v1), and M02's ingestion pipeline (receipts, provenance) to create a deterministic dataset assembly pipeline that:
- Converts ingested artifacts (PGN files or ingest receipts) into structured, versioned, and sharded datasets
- Enforces bounded shard sizes with sequential shard filling
- Produces byte-stable outputs from identical inputs
- Emits versioned "dataset manifest v2" with full provenance and deterministic hashes

> **What would have been incomplete or unsafe if this milestone did not exist?**
>
> Without M03, RenaceCHESS would be unable to assemble datasets from multiple ingested artifacts, making it impossible to create unified training/evaluation datasets with deterministic sharding. This would prevent reproducible dataset generation and make downstream training/evaluation unreliable.

---

## 2. Scope Definition

### In Scope

**Components:**
- Dataset assembly engine (`src/renacechess/dataset/builder.py`)
- Receipt reader utilities (`src/renacechess/dataset/receipt_reader.py`)
- Dataset manifest v2 schema and generation (`src/renacechess/dataset/manifest.py`)
- CLI dataset build command (`renacechess dataset build`)
- Sequential shard filling with configurable `shard_size`
- Deterministic split assignment (record-level, not shard-level)

**Subsystems:**
- Multi-shard dataset assembly from receipts or PGN files
- Shard size enforcement (sequential filling, no in-memory buffering)
- Assembly configuration hashing (`assemblyConfigHash`)
- Dataset digest computation (`datasetDigest` = stable dataset identity)
- Input provenance tracking (receipt IDs, digests, paths)
- Line ending normalization for cross-platform determinism

**Workflows:**
- Receipt-based dataset building (canonical path)
- PGN file-based dataset building (backward compatibility)
- Multi-shard generation with deterministic ordering
- Manifest v2 generation with full provenance

**Contracts:**
- Dataset Manifest schema v2 (JSON Schema)
- Pydantic models matching schema exactly
- Schema validation tests
- Backward compatibility with v1 manifests

**Documents:**
- `docs/DATASETS.md` — Updated with v2 manifest format and receipt-based building
- `docs/milestones/PoC/M03/` — Plan, toolcalls, run analyses, audit, summary

### Out of Scope

**Explicitly deferred:**
- Model training or evaluation (deferred to future milestones)
- Streaming / incremental dataset updates (deferred to future milestones)
- Parallel shard building (deferred to future milestones)
- Performance optimization (deferred to future milestones)
- Dataset version diffing (deferred to future milestones)
- Dataset mutation or append mode (deferred to future milestones)
- Cloud storage / upload (deferred to future milestones)
- Train/val/test semantics beyond deterministic split (deferred to future milestones)

**Intentionally untouched:**
- Ingestion pipeline (M02 scope)
- Single-file dataset building (M01 scope)
- Contract definitions (M00 scope)

**Scope changes:** None — scope remained stable throughout execution.

---

## 3. Work Executed

### High-Level Actions

1. **Dataset Manifest v2 schema creation** — Created new versioned schema with:
   - `assemblyConfigHash` — Hash of assembly configuration parameters
   - `datasetDigest` — Stable dataset identity (hash of config + inputs + schema versions)
   - `inputs` — List of input artifacts with type, digest, receipt ID, and path
   - `assemblyConfig` — Configuration parameters (shard size, limits, ply ranges)
   - Backward compatibility with v1 (v1 preserved, v2 additive)

2. **Receipt reader utilities** — Implemented `receipt_reader.py` with:
   - Receipt loading and validation
   - PGN path resolution (absolute/relative, cache directory support)
   - Compressed file detection (fail fast if `.zst` without decompressed path)
   - PGN digest computation with line ending normalization

3. **Sequential shard filling** — Refactored `builder.py` with `ShardWriter` class:
   - Sequential shard filling based on `shard_size`
   - No in-memory buffering of entire dataset
   - Deterministic shard ordering (`shard_000.jsonl`, `shard_001.jsonl`, ...)
   - Record-level split assignment (stable even if shard size changes)

4. **CLI integration** — Extended `cli.py` with:
   - `--receipt` flag (multiple times, canonical path)
   - `--pgn` flag (multiple times, backward compatibility)
   - `--shard-size` flag (default: 10000, minimum: 1)
   - `--cache-dir` flag (for resolving receipt paths)
   - Mutual exclusivity enforcement (`--pgn` and `--receipt` cannot both be used)

5. **Test coverage expansion** — Added 4 new test files:
   - `test_dataset_build_v2_golden.py` — Multi-shard golden tests with determinism checks
   - `test_dataset_receipt_build.py` — Receipt-based building tests (226 lines)
   - `test_dataset_builder_edge_cases_m03.py` — Edge cases (empty inputs, zero limits, small shard sizes)
   - Updated existing tests for v2 compatibility

**Statistics:**
- 89 files changed, 11,815 insertions(+), 178 deletions(-)
- 160 tests (up from 144 in M02)
- Coverage: 92.45% (exceeds 90% threshold)

---

## 4. Validation & Evidence

### Tests Run

**CI Tests:**
- **Run 1 (21304980117):** 160/160 tests passed, 92.45% coverage, formatting failure only
- **Run 2 (21305144364):** 160/160 tests passed, 92.45% coverage, fully green

**Test Types:**
- Unit tests (dataset builder, receipt reader, manifest generation)
- Integration tests (end-to-end dataset building from receipts)
- Golden file tests (determinism checks, byte-identical outputs)
- Schema validation tests (v1 and v2)
- Edge case tests (empty inputs, zero limits, small shard sizes)

**Enforcement Mechanisms:**
- Ruff linting: ✅ Enforced and passing
- Ruff formatting: ✅ Enforced and passing (after Run 1 fix)
- MyPy type checking: ✅ Enforced and passing
- Pytest with coverage gate: ✅ Enforced and passing (92.45% > 90%)

### Failures Encountered

**Run 1 Formatting Failure:**
- **Observation:** 5 files needed auto-formatting by Ruff
- **Root Cause:** New files not auto-formatted before commit
- **Resolution:** Ran `ruff format .`, committed, pushed
- **Status:** ✅ Resolved in Run 2

**No correctness failures** — All tests passed in both runs.

### Evidence of Validation Meaningfulness

- **Determinism verified:** Golden tests confirm byte-identical outputs from identical inputs
- **Schema validation:** Both v1 and v2 schemas validated against JSON Schema
- **Coverage discipline:** 92.45% coverage exceeds 90% threshold
- **Type safety:** MyPy passes with no errors or warnings
- **Cross-platform determinism:** Line ending normalization ensures identical hashes across Windows and Linux

---

## 5. CI / Automation Impact

### Workflows Affected

**CI Workflow:**
- No workflow changes
- All existing checks enforced (lint, format, type, test, coverage)
- No new checks added
- No checks removed or weakened

### Checks Added, Removed, or Reclassified

**None** — All checks remain as-is from M02.

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
- **Description:** 5 files needed auto-formatting by Ruff
- **Root Cause:** New files not auto-formatted before commit
- **Resolution Status:** ✅ Resolved (Run 2)
- **Tracking Reference:** `docs/milestones/PoC/M03/M03_run1.md`, `M03_run2.md`

**No other issues** — All other checks passed in both runs.

---

## 7. Deferred Work

### Deferred Items

**Explicitly deferred in M03 plan:**
- Model training or evaluation
- Streaming / incremental dataset updates
- Parallel shard building
- Performance optimization
- Dataset version diffing
- Dataset mutation or append mode
- Cloud storage / upload
- Train/val/test semantics beyond deterministic split

**Status:** All deferred items remain deferred — no status changes as a result of M03 work.

---

## 8. Governance Outcomes

### What Changed in Governance Posture

**Enforcement strengthened:**
- ✅ All CI gates remain enforced (no weakening)
- ✅ Coverage threshold maintained (90%)
- ✅ Type checking remains strict
- ✅ Formatting enforcement maintained

**Ambiguity removed:**
- ✅ Dataset assembly process is now deterministic and auditable
- ✅ Shard size is configurable but bounded
- ✅ Receipt-based building is canonical (PGN support for backward compatibility)
- ✅ Manifest v2 provides stable dataset identity

**Boundaries clarified:**
- ✅ Dataset assembly is separate from ingestion (M02) and training (future)
- ✅ v2 manifest is versioned and isolated from v1 (backward compatible)
- ✅ Sequential shard filling is deterministic (no parallel processing)

**Risks reduced or isolated:**
- ✅ Cross-platform determinism ensured (line ending normalization)
- ✅ Input provenance fully tracked (receipt IDs, digests, paths)
- ✅ Dataset identity is stable (`datasetDigest`)

### What Is Now Provably True

1. **Deterministic dataset assembly:** Given identical inputs and configuration, RenaceCHESS will always produce byte-identical dataset shards and manifests.
2. **Stable dataset identity:** `datasetDigest` provides a stable identifier for datasets, enabling reproducible dataset references.
3. **Full provenance tracking:** Dataset manifests include complete input provenance (receipt IDs, digests, paths).
4. **Bounded shard sizes:** Shard sizes are enforced with sequential filling, preventing unbounded memory usage.
5. **Cross-platform determinism:** Line ending normalization ensures identical hashes across Windows and Linux.

---

## 9. Exit Criteria Evaluation

### Original Success Criteria (from M03 Plan)

1. ✅ **`renacechess dataset build` works end-to-end**
   - **Evidence:** CLI command implemented, tested, and working
   - **Status:** Met

2. ✅ **Dataset shards are deterministic and bounded**
   - **Evidence:** Golden tests confirm byte-identical outputs, shard size enforced
   - **Status:** Met

3. ✅ **Dataset manifest v2 exists and validates**
   - **Evidence:** v2 schema created, Pydantic models implemented, validation tests pass
   - **Status:** Met

4. ✅ **Golden dataset test passes**
   - **Evidence:** `test_dataset_build_v2_golden.py` passes with determinism checks
   - **Status:** Met

5. ✅ **CI fully green**
   - **Evidence:** Run 2 (21305144364) fully green, all checks passing
   - **Status:** Met

6. ✅ **`M03_plan.md`, `M03_run*.md`, `M03_audit.md`, `M03_summary.md` committed**
   - **Evidence:** All documents generated and committed
   - **Status:** Met

7. ✅ **No unresolved deferred issues (or explicitly documented)**
   - **Evidence:** All deferred items documented in plan, no new issues introduced
   - **Status:** Met

**Overall Status:** ✅ **All exit criteria met**

---

## 10. Final Verdict

**Milestone objectives met. Safe to proceed.**

M03 successfully implemented deterministic multi-shard dataset assembly with full provenance tracking, versioned manifests, and cross-platform determinism. All gates passing, no regressions, ready for M04 planning.

---

## 11. Authorized Next Step

**M04 planning** — M03 is complete and immutable. Next milestone can proceed with:
- Model training infrastructure
- Evaluation pipelines
- Human-skill modeling
- Or other authorized directions

**Constraints:**
- M03 codebase is frozen (no further commits to M03)
- All follow-ups start on M04
- CI history preserved as canonical evidence

---

## 12. Canonical References

### Commits

- **M03 Initial:** `021e218` — M03: Deterministic Multi-Shard Dataset Assembly
- **M03 Fixes:** `49ca213`, `470a164`, `d2782ae`, `2f7eb8c` — CI error fixes
- **M03 Run 1 Analysis:** `19887b1` — M03: Add CI run analysis report (Run 1)
- **M03 Formatting Fix:** `f7750c3` — M03: Auto-format code (ruff format)
- **M03 Run 2 Analysis:** `8d9b362` — M03: Add CI run analysis report (Run 2 - fully green)
- **M03 Final:** `0acae10` — Merge pull request #5 from m-cahill/m03-dataset-assembly

### Pull Requests

- **PR #5:** `m03-dataset-assembly → main` — Merged 2026-01-23

### Documents

- **Plan:** `docs/milestones/PoC/M03/M03_plan.md`
- **Tool Calls:** `docs/milestones/PoC/M03/M03_toolcalls.md`
- **Run 1 Analysis:** `docs/milestones/PoC/M03/M03_run1.md`
- **Run 2 Analysis:** `docs/milestones/PoC/M03/M03_run2.md`
- **Audit:** `docs/milestones/PoC/M03/M03_audit.md`
- **Summary:** `docs/milestones/PoC/M03/M03_summary.md` (this document)

### CI Runs

- **Run 1:** 21304980117 — Failed (formatting only)
- **Run 2:** 21305144364 — Passed (fully green)

### Issue Trackers

- **None** — No issues tracked externally

### Audit Artifacts

- **Audit Report:** `docs/milestones/PoC/M03/M03_audit.md`
- **CI Analysis Reports:** `docs/milestones/PoC/M03/M03_run1.md`, `M03_run2.md`

---

**Generated:** 2026-01-23  
**Status:** ✅ **M03 CLOSED / IMMUTABLE**

