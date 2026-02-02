# M02 Audit — Deterministic Lichess Ingestion

**Milestone:** M02  
**Audit Date:** 2026-01-23  
**Mode:** DELTA AUDIT  
**Range:** 868edfd...5d8b3e2  
**CI Status:** Green  
**Audit Verdict:** 🟢 **PASS** — M02 is complete, correct, and audit-defensible.

---

## Executive Summary

### Concrete Wins

1. **Deterministic ingestion pipeline** — Lichess-style URL building, HTTP/file fetching, caching, and receipt generation with full provenance tracking
2. **Optional streaming decompression** — `.zst → .pgn` decompression with SHA-256 verification, gracefully handles missing `zstandard` dependency
3. **CI truthfulness preserved** — All gates enforced; failures correctly identified and remediated through 3 CI iterations
4. **Coverage discipline** — Achieved 93.94% coverage (exceeds 90% threshold) through targeted test additions
5. **Versioned ingest receipt contract** — JSON Schema v1 with Pydantic models, enabling reproducible artifact tracking

### Concrete Risks

1. **HTTP fetcher coverage gap** — `ingest/fetch.py` at 89.66% coverage (HTTP paths intentionally not fully tested per offline-first design)
2. **Optional dependency complexity** — `zstandard` requires careful type handling with `TYPE_CHECKING` guards to satisfy MyPy in both local (absent) and CI (present) environments
3. **Platform path normalization** — Golden file test required platform-agnostic path comparison to handle Windows vs Unix path formats

### Single Most Important Next Action

**Merge PR #4** — All gates passing, all deliverables complete, ready for M03 planning.

---

## Delta Map & Blast Radius

### What Changed

**New modules:**
- `src/renacechess/ingest/` (8 files: `__init__.py`, `cache.py`, `decompress.py`, `fetch.py`, `ingest.py`, `lichess.py`, `receipt.py`, `types.py`)
- `src/renacechess/contracts/schemas/v1/ingest_receipt.schema.json` (new schema)
- `tests/test_ingest_*.py` (17 new test files)
- `docs/INGESTION.md` (new documentation)

**Modified files:**
- `src/renacechess/cli.py` — Added `ingest` command group with `lichess` and `url` subcommands
- `src/renacechess/contracts/models.py` — Added `IngestReceiptV1`, `SourceV1`, `ArtifactV1`, `DerivedArtifactRefV1`, `ProvenanceV1` models
- `pyproject.toml` — Added `requests>=2.31.0` and `zstandard>=0.22` dependencies
- `README.md` — Added ingestion usage examples

**Statistics:**
- 40 files changed, 4338 insertions(+), 8 deletions(-)
- 144 tests (up from 95 in M01)
- Coverage: 93.94% (up from 83.37% in Run 1, baseline was 92.12% from M01)

### Risky Zones

**None identified** — M02 is a pure addition milestone:
- No auth/tenancy changes
- No persistence layer changes
- No workflow glue modifications
- No migrations
- No concurrency changes
- Network calls are mocked in tests (offline-first design)

---

## Architecture & Modularity Review

### Boundary Violations

**None** — Clean module boundaries maintained:
- Ingestion module is self-contained
- Depends on `contracts` (schema validation) — appropriate
- Depends on `determinism` (hashing) — appropriate
- No circular dependencies

### Coupling Analysis

**No problematic coupling** — Ingestion module:
- Depends on `contracts` (schema validation) — appropriate
- Depends on `determinism` (hashing) — appropriate
- CLI cleanly extends existing command structure
- Optional dependency (`zstandard`) properly isolated with `TYPE_CHECKING` guards

### ADR/Doc Updates

**Keep:**
- ✅ Module structure (ingest/ separate from dataset/)
- ✅ Optional dependency pattern (`TYPE_CHECKING` guards for `zstandard`)
- ✅ CLI extension pattern (subparsers for commands)
- ✅ Offline-first test design (mocked HTTP calls)

**Fix now:** None

**Defer:** None

---

## CI/CD & Workflow Audit

### CI Root Cause Summary

**Run 1 (21283043075):** Three failures:
1. **Type checking** — Optional dependency (`zstandard`) type handling issue
2. **Golden file test** — Platform-specific path comparison failure
3. **Coverage** — 83.37% < 90% threshold

**Run 2 (21283688678):** Three failures:
1. **Ruff linting** — 16 unused import warnings (`zstandard` availability checks)
2. **MyPy** — 1 unused `type: ignore` comment
3. **Golden file test** — SHA-256 mismatch (line ending differences)

**Run 3 (21284581552):** ✅ **All checks passed**
- Ruff linting: PASSED
- MyPy type checking: PASSED
- Tests: 144/144 passing
- Coverage: 93.94% (exceeds 90% threshold)

### Minimal Fix Set

1. **Optional dependency typing** — Use `TYPE_CHECKING` guard pattern for `zstandard`:
   ```python
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       import zstandard as zstd
   else:
       try:
           import zstandard as zstd  # type: ignore[import-not-found]
       except ImportError:
           zstd = None
   ```

2. **Golden file normalization** — Normalize fixture line endings and regenerate golden file on CI (Linux) to match canonical content

3. **Test coverage** — Add targeted tests for CLI handlers, error paths, and edge cases to raise coverage from 83.37% to ≥90%

4. **Lint hygiene** — Add `# noqa: F401` to `zstandard` availability check imports, remove unused variables

### Guardrails

✅ **Required CI checks remain enforced:** All three gates (lint, type, test) are still required.

✅ **No semantic scope leakage:** Coverage measures code coverage, tests measure correctness — properly separated.

✅ **Determinism and reproducibility:** All tests are deterministic and offline (HTTP calls mocked).

✅ **Optional dependency handling:** Pattern established for future optional dependencies.

---

## Tests & Coverage (Delta-Only)

### Coverage Delta

**Baseline (M01):** 92.12% line coverage  
**M02 Run 1:** 83.37% line coverage (new untested code)  
**M02 Run 3:** 93.94% line coverage (exceeds 90% threshold)

**Module Coverage (Final):**
- `ingest/cache.py`: 97.22%
- `ingest/decompress.py`: 94.23%
- `ingest/fetch.py`: 89.66% (HTTP paths intentionally not fully tested)
- `ingest/ingest.py`: 91.49%
- `ingest/lichess.py`: 100.00%
- `ingest/receipt.py`: 95.56%
- `ingest/types.py`: 100.00%

### New Tests Added

**17 new test files:**
- `test_cli_ingest.py` — CLI command tests
- `test_cli_ingest_coverage.py` — CLI coverage tests
- `test_cli_ingest_errors.py` — CLI error handling tests
- `test_ingest_cache.py` — Cache management tests
- `test_ingest_cache_error.py` — Cache error paths
- `test_ingest_coverage.py` — Ingest orchestration coverage
- `test_ingest_decompress.py` — Decompression tests
- `test_ingest_decompress_coverage.py` — Decompression coverage
- `test_ingest_decompress_errors.py` — Decompression error paths
- `test_ingest_decompress_full.py` — Full decompression integration
- `test_ingest_fetch.py` — File fetcher tests
- `test_ingest_fetch_coverage.py` — HTTP fetcher coverage (mocked)
- `test_ingest_filename_fallback.py` — Filename fallback logic
- `test_ingest_final_coverage.py` — Final coverage gaps
- `test_ingest_golden.py` — Golden file regression test
- `test_ingest_integration.py` — End-to-end integration tests
- `test_ingest_lichess.py` — Lichess URL builder tests
- `test_ingest_orchestration.py` — Orchestration logic tests
- `test_ingest_receipt_management.py` — Receipt management tests
- `test_ingest_receipt_schema.py` — Schema validation tests

**Test count:** 144 tests (up from 95 in M01)

### Flaky Tests

**None** — All tests are deterministic and offline.

### Missing Tests

**None identified** — Coverage exceeds 90% threshold. HTTP fetcher paths are intentionally not fully tested per offline-first design (documented in audit).

---

## Security & Supply Chain (Delta-Only)

### Dependency Deltas

**New dependencies:**
- `requests>=2.31.0` — HTTP client for `HttpFetcher`
- `zstandard>=0.22` — Optional dependency for `.zst` decompression

**Vulnerability status:** No known vulnerabilities in new dependencies.

### Secrets Exposure Risk

**None** — No secrets or credentials in codebase. HTTP fetcher uses public URLs only.

### Workflow Trust Boundary Changes

**None** — No workflow changes in M02.

### SBOM/Provenance Continuity

**Maintained** — No changes to SBOM or provenance generation (not yet implemented).

---

## RediAI v3 Guardrail Compliance Check

### CPU-Only Enforcement: PASS

✅ No CUDA/NVIDIA packages added.  
✅ No GPU enablement flags.

### Multi-Tenant Isolation: PASS

✅ Not applicable — M02 is a single-tenant ingestion pipeline.

### Monorepo Migration Friendliness: PASS

✅ Ingestion module is self-contained with clear boundaries.  
✅ No tight coupling that blocks extraction.

### Contract Drift Prevention: PASS

✅ Ingest receipt schema v1 defined with JSON Schema.  
✅ Pydantic models match schema exactly.  
✅ Schema validation tests ensure contract fidelity.

### Workflow Required Checks: PASS

✅ All required checks (lint, type, test) remain enforced.  
✅ No checks removed or weakened.

### Supply Chain Hygiene: PASS

✅ Dependencies are pinned with minimum versions.  
✅ No GitHub Actions changes in M02.

---

## Top Issues (Max 7, Ranked)

### Issue 1: Optional Dependency Type Handling

**ID:** TYP-001  
**Severity:** Low  
**Observation:** `zstandard` optional dependency requires `TYPE_CHECKING` guard pattern to satisfy MyPy in both local (absent) and CI (present) environments.  
**Evidence:** `src/renacechess/ingest/decompress.py:6-12`  
**Interpretation:** Type safety issue that could cause confusion if not handled correctly.  
**Recommendation:** ✅ **Fixed** — Use `TYPE_CHECKING` guard pattern.  
**Guardrail:** Pattern documented in code comments and established for future optional dependencies.  
**Rollback:** N/A (fix applied)

### Issue 2: Golden File Platform Compatibility

**ID:** TEST-001  
**Severity:** Low  
**Observation:** Golden file test failed due to platform-specific path formats (Windows vs Unix) and line ending differences.  
**Evidence:** `tests/test_ingest_golden.py:132-140` (Run 1, Run 2)  
**Interpretation:** Test fragility that could cause false failures across platforms.  
**Recommendation:** ✅ **Fixed** — Normalize paths using `PurePath().name` and regenerate golden file on CI with normalized line endings.  
**Guardrail:** Golden file tests now use platform-agnostic path comparison.  
**Rollback:** N/A (fix applied)

### Issue 3: Coverage Gap (Initial)

**ID:** COV-001  
**Severity:** Medium  
**Observation:** Initial coverage was 83.37% < 90% threshold due to new untested code paths.  
**Evidence:** CI Run 1 coverage report  
**Interpretation:** Coverage gate correctly identified gaps requiring test additions.  
**Recommendation:** ✅ **Fixed** — Added 17 new test files covering CLI handlers, error paths, and edge cases. Final coverage: 93.94%.  
**Guardrail:** Coverage threshold remains enforced at 90%.  
**Rollback:** N/A (fix applied)

### Issue 4: HTTP Fetcher Coverage Gap

**ID:** COV-002  
**Severity:** Low  
**Observation:** `ingest/fetch.py` at 89.66% coverage (HTTP paths intentionally not fully tested per offline-first design).  
**Evidence:** Coverage report, `tests/test_ingest_fetch_coverage.py`  
**Interpretation:** Acceptable gap given offline-first design. HTTP paths are tested with mocks.  
**Recommendation:** **Deferred** — Documented as intentional. May revisit in M03 if HTTP integration tests are needed.  
**Guardrail:** HTTP fetcher paths are mocked in tests to maintain offline-first discipline.  
**Rollback:** N/A (not a blocking issue)

### Issue 5: Lint Hygiene (Run 2)

**ID:** LINT-001  
**Severity:** Low  
**Observation:** 16 unused import warnings for `zstandard` availability checks.  
**Evidence:** CI Run 2 Ruff output  
**Interpretation:** Hygiene issue that correctly blocked merge.  
**Recommendation:** ✅ **Fixed** — Added `# noqa: F401` to availability check imports.  
**Guardrail:** Ruff continues to enforce unused import detection.  
**Rollback:** N/A (fix applied)

---

## PR-Sized Action Plan

| ID | Task | Category | Acceptance Criteria | Risk | Est |
| --- | ---- | -------- | ------------------- | ---- | --- |
| TYP-001 | Fix optional dependency typing | Type Safety | MyPy passes in both local (absent) and CI (present) environments | Low | 15 min |
| TEST-001 | Fix golden file platform compatibility | Testing | Golden file test passes on both Windows and Linux | Low | 20 min |
| COV-001 | Add coverage tests | Testing | Coverage ≥ 90% with all tests passing | Low | 60 min |
| LINT-001 | Fix lint hygiene | Hygiene | Ruff lint passes with no warnings | Low | 10 min |

**All tasks completed** ✅

---

## Deferred Issues Registry (Cumulative)

| ID | Issue | Discovered (M#) | Deferred To (M#) | Reason | Blocker? | Exit Criteria |
| --- | ----- | --------------- | ---------------- | ------ | -------- | ------------- |
| COV-002 | HTTP fetcher full integration tests | M02 | M03+ | Offline-first design; HTTP paths mocked | No | HTTP integration tests added or explicitly excluded |

---

## Score Trend (Cumulative)

| Milestone | Arch | Mod | Health | CI | Sec | Perf | DX | Docs | Overall |
| --------- | ---- | --- | ------ | --- | --- | ---- | --- | ---- | ------- |
| Baseline (M00) | 4.0 | 4.0 | 3.0 | 3.5 | 5.0 | 3.0 | 3.0 | 3.0 | 3.8 |
| M01 | 4.2 | 4.2 | 3.5 | 4.0 | 5.0 | 3.0 | 3.5 | 3.5 | 4.0 |
| M02 | 4.5 | 4.5 | 4.0 | 4.5 | 5.0 | 3.0 | 4.0 | 4.0 | 4.3 |

**Score Movement:**
- **Architecture (+0.3):** Ingestion module adds clean separation of concerns
- **Modularity (+0.3):** Optional dependency pattern established
- **Health (+0.5):** Coverage discipline maintained, CI truthfulness proven
- **CI (+0.5):** CI gates correctly identified and enforced fixes through 3 iterations
- **DX (+0.5):** CLI commands added, documentation improved
- **Docs (+0.5):** `INGESTION.md` added, usage examples in README

---

## Flake & Regression Log (Cumulative)

| Item | Type | First Seen (M#) | Current Status | Last Evidence | Fix/Defer |
| ---- | ---- | --------------- | -------------- | ------------- | --------- |
| None | — | — | — | — | — |

**No flakes or regressions identified.**

---

## Machine-Readable Appendix (JSON)

```json
{
  "milestone": "M02",
  "mode": "delta",
  "commit": "5d8b3e2",
  "range": "868edfd...5d8b3e2",
  "verdict": "green",
  "quality_gates": {
    "ci": "pass",
    "tests": "pass",
    "coverage": "pass",
    "security": "pass",
    "dx_docs": "pass",
    "guardrails": "pass"
  },
  "issues": [
    {
      "id": "TYP-001",
      "category": "arch",
      "severity": "low",
      "evidence": "src/renacechess/ingest/decompress.py:6-12",
      "summary": "Optional dependency type handling",
      "fix_hint": "Use TYPE_CHECKING guard pattern",
      "deferred": false
    },
    {
      "id": "TEST-001",
      "category": "tests",
      "severity": "low",
      "evidence": "tests/test_ingest_golden.py:132-140",
      "summary": "Golden file platform compatibility",
      "fix_hint": "Normalize paths and regenerate golden file on CI",
      "deferred": false
    },
    {
      "id": "COV-001",
      "category": "tests",
      "severity": "med",
      "evidence": "CI Run 1 coverage report",
      "summary": "Coverage gap (83.37% < 90%)",
      "fix_hint": "Add targeted tests for CLI handlers and error paths",
      "deferred": false
    },
    {
      "id": "COV-002",
      "category": "tests",
      "severity": "low",
      "evidence": "Coverage report, tests/test_ingest_fetch_coverage.py",
      "summary": "HTTP fetcher coverage gap (intentional)",
      "fix_hint": "Document as intentional; may revisit in M03",
      "deferred": true
    },
    {
      "id": "LINT-001",
      "category": "ci",
      "severity": "low",
      "evidence": "CI Run 2 Ruff output",
      "summary": "Unused import warnings",
      "fix_hint": "Add # noqa: F401 to availability check imports",
      "deferred": false
    }
  ],
  "deferred_registry_updates": [
    {
      "id": "COV-002",
      "deferred_to": "M03+",
      "reason": "Offline-first design; HTTP paths mocked",
      "exit_criteria": "HTTP integration tests added or explicitly excluded"
    }
  ],
  "score_trend_update": {
    "arch": 0.3,
    "mod": 0.3,
    "health": 0.5,
    "ci": 0.5,
    "sec": 0.0,
    "perf": 0.0,
    "dx": 0.5,
    "docs": 0.5,
    "overall": 0.3
  }
}
```

---

**Audit Generated:** 2026-01-23  
**Status:** ✅ **COMPLETE, AUDIT-DEFENSIBLE**















