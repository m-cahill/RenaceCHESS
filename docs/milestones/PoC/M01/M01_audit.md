# M01 Audit — Deterministic Dataset Shard Builder

**Milestone:** M01  
**Audit Date:** 2026-01-23  
**Mode:** DELTA AUDIT  
**Range:** 268a3a5...ee7b546  
**CI Status:** Green  
**Audit Verdict:** 🟢 **PASS** — M01 is complete, correct, and audit-defensible.

---

## Executive Summary

### Concrete Wins

1. **Deterministic dataset builder** — PGN → JSONL shards with reproducible manifest generation
2. **Schema-validated outputs** — Every JSONL record validates against Context Bridge schema v1
3. **CI truthfulness preserved** — All gates enforced; failures correctly identified and remediated
4. **Coverage discipline** — Achieved 92.12% coverage (exceeds 90% threshold) through targeted test additions

### Concrete Risks

1. **CLI coverage gap** — `cli.py` at 68.42% coverage (acceptable given error handling complexity)
2. **Single shard limitation** — M01 implements single-shard strategy; multi-shard deferred to future milestone
3. **No network ingestion** — Local PGN files only; Lichess download pipeline explicitly deferred

### Single Most Important Next Action

**Merge PR #3** — All gates passing, all deliverables complete, ready for M02 planning.

---

## Delta Map & Blast Radius

### What Changed

**New modules:**
- `src/renacechess/dataset/` (5 files: `__init__.py`, `builder.py`, `config.py`, `manifest.py`, `split.py`)
- `tests/test_dataset_*.py` (5 new test files)

**Modified modules:**
- `src/renacechess/cli.py` — Added `dataset build` command
- `src/renacechess/contracts/models.py` — Updated Pydantic configs (`validate_by_alias`, `validate_by_name`)
- `src/renacechess/demo/pgn_overlay.py` — Extracted `generate_payload_from_board()` for reuse
- `src/renacechess/contracts/schemas/v1/context_bridge.schema.json` — Added null support for optional fields

**Documentation:**
- `docs/DATASETS.md` — New dataset format documentation
- `README.md` — Updated with dataset build usage
- `docs/milestones/PoC/M01/` — Plan, toolcalls, run analyses

### Risky Zones

**None identified** — M01 is a pure addition milestone:
- No auth/tenancy changes
- No persistence layer changes
- No workflow glue modifications
- No migrations
- No concurrency changes

---

## Architecture & Modularity Review

### Boundary Violations

**None** — Clean module boundaries maintained:
- Dataset builder is self-contained
- Reuses existing demo payload generator (no duplication)
- CLI cleanly extends existing command structure

### Coupling Analysis

**No problematic coupling** — Dataset module:
- Depends on `contracts` (schema validation) — appropriate
- Depends on `demo` (payload generation) — appropriate reuse
- Depends on `determinism` (hashing) — appropriate
- No circular dependencies

### ADR/Doc Updates

**Keep:**
- ✅ Module structure (dataset/ separate from demo/)
- ✅ Reuse pattern (demo payload generator extracted for reuse)
- ✅ CLI extension pattern (subparsers for commands)

**Fix now:** None

**Defer:** None

---

## CI/CD & Workflow Audit

### CI Root Cause Summary

**Run 1 (21279550886):** Two failures:
1. **Format check** — 11 files not formatted with `ruff format`
2. **Coverage** — 89.02% < 90% threshold

**Remediation:**
- Run 2-3: Fixed linting issues (unused variables, formatting)
- Run 4 (21279736846): ✅ All gates passing

### Minimal Fix Set

**Applied:**
1. ✅ Ran `ruff format .` — formatted all 11 files
2. ✅ Added 11 targeted tests — increased coverage to 92.12%
3. ✅ Fixed linting errors — removed unused variables

### Guardrails

**CI gates remain truthful:**
- Format check correctly identified unformatted files
- Coverage gate correctly enforced 90% threshold
- All failures were real, not flaky

**No gates weakened or bypassed.**

---

## Tests & Coverage

### Coverage Delta

**Overall:** 89.02% → 92.12% (+3.10%)

**Module breakdown:**
- `dataset/builder.py`: 86.44% → 97.46% (+11.02%)
- `dataset/config.py`: 100% (new, fully covered)
- `dataset/manifest.py`: 100% (new, fully covered)
- `dataset/split.py`: 100% (new, fully covered)
- `cli.py`: 68.42% (acceptable — error handling complexity)

### New Tests Added

**11 new tests:**
- 4 CLI error handling tests (`test_cli_dataset_build.py`)
- 7 dataset builder edge case tests (`test_dataset_builder_edge_cases.py`)

**Test count:** 40 → 51 (+11 tests)

### Missing Tests

**None blocking** — All critical paths covered:
- ✅ Empty input handling
- ✅ Limit boundaries (zero, invalid ranges)
- ✅ Directory vs file handling
- ✅ Error propagation

### Fast Fixes

**None required** — Coverage exceeds threshold.

### New Markers/Tags

**None needed** — All tests are unit tests, deterministic.

---

## Security & Supply Chain

### Dependency Deltas

**No new dependencies** — M01 uses existing dependencies:
- `python-chess` (already in use)
- `pydantic` (already in use)
- `jsonschema` (already in use)

### Secrets Exposure Risk

**None** — No secrets, no credentials, no API keys.

### Workflow Trust Boundary Changes

**None** — No workflow changes.

### SBOM/Provenance Continuity

**Maintained** — No changes to artifact generation.

---

## RediAI v3 Guardrail Compliance Check

### CPU-Only Enforcement

✅ **PASS** — No CUDA/NVIDIA packages, no GPU enablement.

### Multi-Tenant Isolation

✅ **PASS** — Not applicable (no multi-tenant features in M01).

### Monorepo Migration Tracking

✅ **PASS** — Clean module boundaries, no tight coupling.

### Contract Drift Prevention

✅ **PASS** — Schema changes are backward-compatible (null support for optional fields).

### Workflow Required Checks

✅ **PASS** — All required checks enforced (lint, typecheck, test).

### Supply Chain Hygiene

✅ **PASS** — No new actions, no trust expansion.

---

## Top Issues

**None** — M01 is clean. All issues from Run 1 were resolved.

---

## PR-Sized Action Plan

| ID | Task | Category | Acceptance Criteria | Risk | Est |
| --- | ---- | -------- | ------------------- | ---- | --- |
| N/A | Merge PR #3 | Governance | PR merged to main, CI green | Low | 5 min |

**No blocking issues.**

---

## Deferred Issues Registry

| ID | Issue | Discovered (M#) | Deferred To (M#) | Reason | Blocker? | Exit Criteria |
| --- | ----- | --------------- | ---------------- | ------ | -------- | ------------- |
| M01-001 | Multi-shard strategies | M01 | M02+ | Explicitly out of scope for M01 | No | Multi-shard implementation |
| M01-002 | Lichess network ingestion | M01 | M02+ | Explicitly out of scope for M01 | No | Network download pipeline |
| M01-003 | CLI coverage gap (68.42%) | M01 | Future | Acceptable given error handling complexity | No | Coverage ≥90% overall (achieved) |

---

## Score Trend

| Milestone | Arch | Mod | Health | CI | Sec | Perf | DX | Docs | Overall |
| --------- | ---- | --- | ------ | --- | --- | ---- | --- | ---- | ------- |
| Baseline (M00) | 4.5 | 4.5 | 4.0 | 4.5 | 5.0 | N/A | 4.0 | 4.0 | 4.4 |
| M01 | 4.5 | 4.5 | 4.5 | 5.0 | 5.0 | N/A | 4.5 | 4.5 | 4.6 |

**Score movement:**
- **CI:** 4.5 → 5.0 (proven CI truthfulness through Run 1-4 remediation)
- **Health:** 4.0 → 4.5 (coverage discipline, test expansion)
- **DX:** 4.0 → 4.5 (dataset documentation, CLI improvements)
- **Docs:** 4.0 → 4.5 (DATASETS.md, comprehensive run analyses)

---

## Flake & Regression Log

| Item | Type | First Seen (M#) | Current Status | Last Evidence | Fix/Defer |
| ---- | ---- | --------------- | -------------- | ------------- | --------- |
| N/A | N/A | N/A | N/A | N/A | N/A |

**No flakes or regressions.**

---

## What Was Added

### Core Functionality

1. **Dataset Builder Module** (`src/renacechess/dataset/`)
   - `builder.py` — Main builder logic (PGN → JSONL)
   - `config.py` — Build configuration dataclass
   - `manifest.py` — Dataset manifest generation
   - `split.py` — Deterministic split assignment (train/val/frozenEval)
   - 97.46% test coverage

2. **CLI Extension** (`src/renacechess/cli.py`)
   - `dataset build` command with filtering options
   - Error handling for invalid inputs
   - 68.42% test coverage (acceptable)

3. **Pydantic Model Updates** (`src/renacechess/contracts/models.py`)
   - Replaced `populate_by_name=True` with `validate_by_alias=True, validate_by_name=True`
   - Forward-compatible with Pydantic v2.11+
   - All models updated consistently

4. **Schema Updates** (`src/renacechess/contracts/schemas/v1/context_bridge.schema.json`)
   - Added null support for optional fields (`san`, `timeControlClass`)
   - Backward-compatible change

5. **Demo Module Refactoring** (`src/renacechess/demo/pgn_overlay.py`)
   - Extracted `generate_payload_from_board()` for reuse
   - Maintains backward compatibility

### Testing Infrastructure

- 51 tests total (up from 40)
- 11 new tests (4 CLI + 7 builder edge cases)
- Coverage: 92.12% (exceeds 90% threshold)
- Golden file tests for dataset build
- Schema validation tests for every JSONL record

### Documentation

- `docs/DATASETS.md` — Comprehensive dataset format documentation
- `README.md` — Updated with dataset build usage
- `docs/milestones/PoC/M01/` — Complete milestone documentation

---

## What Was Deferred

1. **Multi-shard strategies** — Explicitly out of scope (single shard per build in M01)
2. **Network ingestion** — Lichess download pipeline deferred to future milestone
3. **ML training** — Not in scope for M01
4. **Engine integration** — Not in scope for M01

---

## Technical Decisions

### Single Shard Per Build

**Decision:** M01 implements single-shard strategy (one `shard_000.jsonl` per build).

**Rationale:** Keeps M01 small, auditable, and deterministic. Multi-shard strategies introduce policy complexity that belongs in later milestones.

**Documented in:** M01_plan.md, M01_audit.md

### Pydantic Alias Validation

**Decision:** Update all models to use `validate_by_alias=True, validate_by_name=True`.

**Rationale:** Forward-compatibility with Pydantic v2.11+, consistency across all models.

**Documented in:** M01_audit.md

### Schema Null Support

**Decision:** Allow null for optional fields in Context Bridge schema.

**Rationale:** JSON Schema best practice for optional fields; enables proper validation of payloads with missing optional data.

**Documented in:** M01_audit.md

---

## CI Evidence

**Workflow:** `.github/workflows/ci.yml`

**Final Run:** 21279736846 (✅ SUCCESS)

**Jobs:**
1. `lint` — Ruff lint + format check ✅
2. `typecheck` — MyPy type checking ✅
3. `test` — Pytest with coverage gate ✅

**Coverage:** 92.12% (exceeds 90% requirement)

**Test Count:** 51 tests, all passing

---

## Deviations from Plan

**None** — Implementation followed M01_plan.md exactly.

---

## Known Issues

**None** — All tests passing, coverage exceeds threshold, all linting/type errors resolved.

---

## Audit Verdict

✅ **PASS** — M01 is complete, correct, and audit-defensible.

All deliverables met:
- ✅ Dataset builder module complete
- ✅ CLI dataset build command works
- ✅ JSONL + manifest outputs deterministic
- ✅ Golden shard + manifest tests pass
- ✅ Every JSONL line validates against Context Bridge schema
- ✅ Manifest validates against dataset manifest schema
- ✅ Pydantic alias/name validation behavior tested and stable
- ✅ Coverage exceeds 90% threshold (92.12%)
- ✅ All CI gates passing
- ✅ M01_plan/M01_summary/M01_audit/M01_run1/M01_run2 committed

**Ready for:** Merge to main and M02 planning

---

**Machine-Readable Appendix (JSON)**

```json
{
  "milestone": "M01",
  "mode": "delta",
  "commit": "ee7b546008b865cffaf0d95c92693706af2750f0",
  "range": "268a3a5...ee7b546",
  "verdict": "green",
  "quality_gates": {
    "ci": "pass",
    "tests": "pass",
    "coverage": "pass",
    "security": "pass",
    "dx_docs": "pass",
    "guardrails": "pass"
  },
  "issues": [],
  "deferred_registry_updates": [
    {
      "id": "M01-001",
      "deferred_to": "M02+",
      "reason": "Explicitly out of scope for M01",
      "exit_criteria": "Multi-shard implementation"
    },
    {
      "id": "M01-002",
      "deferred_to": "M02+",
      "reason": "Explicitly out of scope for M01",
      "exit_criteria": "Network download pipeline"
    }
  ],
  "score_trend_update": {
    "arch": 0,
    "mod": 0,
    "health": 0.5,
    "ci": 0.5,
    "sec": 0,
    "perf": 0,
    "dx": 0.5,
    "docs": 0.5,
    "overall": 0.2
  }
}
```

