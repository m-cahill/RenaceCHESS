# M02 CI Run 1 Analysis

**Workflow:** CI  
**Run ID:** 21283043075  
**Trigger:** PR #4 (m02-lichess-ingestion)  
**Branch:** m02-lichess-ingestion  
**Commit:** 08fbeb4  
**Status:** ❌ **FAILURE**

---

## Workflow Inventory

| Job / Check | Required? | Purpose | Pass/Fail | Notes |
| ----------- | --------- | ------- | --------- | ----- |
| Lint and Format | ✅ Yes | Ruff lint + format check | ✅ PASS | All linting and formatting checks passed |
| Type Check | ✅ Yes | MyPy type checking | ❌ FAIL | Type errors in `decompress.py` |
| Test | ✅ Yes | Pytest with coverage gate | ❌ FAIL | 1 test failure + coverage 83.37% < 90% |

**Merge-blocking checks:** All three jobs are required.

---

## Signal Integrity Analysis

### A) Tests

**Test tiers:** Unit tests, integration tests, golden file regression tests (95 tests total)

**Failures:** 1 test failure:
- `test_ingest_receipt_golden`: AssertionError — filename comparison issue between Windows and Unix paths in golden file

**Test stability:** 94/95 tests passing. The failure is due to platform-specific path handling in the golden file test (Windows vs Unix path formats).

**Missing tests:** Coverage analysis shows gaps in:
- `cli.py`: 57.14% coverage (CLI command handlers not fully tested)
- `ingest/fetch.py`: 43.68% coverage (HTTP fetcher paths not tested — intentionally offline-first)
- `ingest/ingest.py`: 79.79% coverage (some error paths and edge cases)
- `ingest/decompress.py`: 80.77% coverage (error handling paths)

### B) Coverage

**Type:** Line coverage (90% threshold)

**Overall:** 83.37% line coverage (below 90% threshold)

**Scoped correctly:** Yes — coverage measures all source files in `src/renacechess/`

**Exclusions:** Standard exclusions (tests, `__init__.py`, pragma comments) — documented and justified.

**Coverage breakdown:**
- New ingest module: 83.37% overall
  - `ingest/cache.py`: 83.33%
  - `ingest/decompress.py`: 80.77%
  - `ingest/fetch.py`: 43.68% (HTTP paths intentionally not tested — offline-first design)
  - `ingest/ingest.py`: 79.79%
  - `ingest/lichess.py`: 100%
  - `ingest/receipt.py`: 95.56%
  - `ingest/types.py`: 100%
- `cli.py`: 57.14% (CLI handlers need more tests)
- All other modules: 88.89% - 100% coverage

**Coverage gap analysis:**
- HTTP fetcher paths (43.68%) are intentionally not tested per offline-first design
- CLI handlers (57.14%) need additional test coverage
- Error paths in ingest module need coverage

### C) Static / Policy Gates

**Linting:** Ruff lint passed — no linting errors.

**Formatting:** Ruff format check passed — all files properly formatted.

**Type checking:** MyPy failed with 2 errors in `src/renacechess/ingest/decompress.py`:
1. `error: Unused "type: ignore" comment [unused-ignore]` (line 8)
2. `error: Incompatible types in assignment (expression has type "None", variable has type Module) [assignment]` (line 10)

**Root cause:** The `zstandard` library is installed in CI, so mypy can find it but has no type stubs. The type ignore on the import is unused locally (where zstandard may not be installed) but the assignment of `None` to `zstd` causes a type error when zstandard is available.

**Gates enforce current reality:** Yes — type checking correctly identified a real type safety issue with optional dependency handling.

### D) Performance / Benchmarks

Not applicable for this milestone.

---

## Delta Analysis (Change Impact)

### Files Modified

**New modules:**
- `src/renacechess/ingest/` (7 new files: `__init__.py`, `cache.py`, `decompress.py`, `fetch.py`, `ingest.py`, `lichess.py`, `receipt.py`, `types.py`)
- `src/renacechess/contracts/schemas/v1/ingest_receipt.schema.json` (new schema)
- `tests/test_ingest_*.py` (9 new test files)
- `docs/INGESTION.md` (new documentation)

**Modified files:**
- `src/renacechess/cli.py` (added ingest command group)
- `src/renacechess/contracts/models.py` (added IngestReceiptV1 models)
- `pyproject.toml` (added `requests>=2.31.0` and `zstandard>=0.22` dependencies)
- `README.md` (added ingestion usage examples)

### CI Signals Affected

1. **Type checking:** New optional dependency (`zstandard`) requires proper type handling
2. **Coverage:** New code paths not fully covered (83.37% < 90%)
3. **Tests:** Platform-specific path handling in golden file test

### Unexpected Deltas

**Signal drift:**
- Coverage dropped from baseline (was ~90%+) due to new untested code paths
- Type checking revealed optional dependency handling issue

**Coupling revealed:**
- Golden file test couples to platform-specific path formats (Windows vs Unix)
- Optional dependency type checking behaves differently in local vs CI environments

**Previously hidden dependency:**
- `zstandard` type stubs not available, requiring careful type ignore handling

---

## Failure Analysis

### Failure 1: Type Checking (MyPy)

**Classification:** CI misconfiguration / type safety issue

**Details:**
- `src/renacechess/ingest/decompress.py:8`: Unused type ignore comment
- `src/renacechess/ingest/decompress.py:10`: Incompatible type assignment (`None` to `Module`)

**Root cause:** Optional dependency (`zstandard`) is installed in CI but not locally, causing different type checking behavior. When installed, mypy sees the module but has no stubs, and assigning `None` to a module-typed variable is a type error.

**In scope:** Yes — this is directly related to M02's optional decompression feature.

**Blocking:** Yes — type checking is a merge gate.

**Fix required:**
- Use `TYPE_CHECKING` guard or proper type annotation for optional dependency
- Ensure type ignore covers both local (not installed) and CI (installed) scenarios

### Failure 2: Golden File Test

**Classification:** Test fragility / platform compatibility

**Details:**
- `test_ingest_receipt_golden`: Filename comparison fails because golden file contains full Windows path (`C:\coding\renacechess\tests\data\sample_lichess_small.pgn`) but test extracts just filename from Unix path.

**Root cause:** Golden file was created on Windows with full path, but test runs on Linux. The `Path().name` extraction works differently when the path format differs.

**In scope:** Yes — this is a test for M02's receipt determinism.

**Blocking:** Yes — test failure blocks merge.

**Fix required:**
- Normalize path extraction to handle both Windows and Unix formats
- Or update golden file to use relative paths or normalize paths before comparison

### Failure 3: Coverage Threshold

**Classification:** Coverage gap (not a correctness failure)

**Details:**
- Overall coverage: 83.37% < 90% threshold
- Main gaps: CLI handlers (57.14%), HTTP fetcher (43.68% — intentional), error paths

**Root cause:** New code added without full test coverage, particularly:
- CLI command handlers
- Error handling paths in ingest module
- HTTP fetcher (intentionally not tested per offline-first design)

**In scope:** Yes — coverage is a merge gate.

**Blocking:** Yes — coverage threshold must be met.

**Fix required:**
- Add tests for CLI handlers
- Add tests for error paths in ingest module
- Document intentional exclusion of HTTP fetcher paths (or add offline HTTP tests with mocks)

---

## Invariants & Guardrails Check

✅ **Required CI checks remain enforced:** All three gates (lint, type, test) are still required.

✅ **No semantic scope leakage:** Coverage measures code coverage, tests measure correctness — properly separated.

⚠️ **Release / consumer contracts:** New ingest module adds new functionality but doesn't break existing contracts.

✅ **Determinism and reproducibility:** All tests are deterministic and offline (except golden file path issue).

**Invariant violations:** None — all guardrails remain intact.

---

## Verdict

**Verdict:**  
This run surfaces **real correctness and quality issues** that must be addressed before merge:

1. **Type safety issue** with optional dependency handling (blocking)
2. **Platform compatibility issue** in golden file test (blocking)
3. **Coverage gap** requiring additional tests (blocking)

The implementation is functionally correct (94/95 tests passing), but CI gates are correctly identifying areas that need attention.

⛔ **Merge blocked** — fixes required for:
- Type checking (optional dependency handling)
- Golden file test (platform path normalization)
- Coverage threshold (additional tests needed)

---

## Next Actions

### Immediate (Blocking)

1. **Fix type checking issue** (Owner: AI/Cursor)
   - Scope: `src/renacechess/ingest/decompress.py`
   - Use `TYPE_CHECKING` guard or proper type annotation for `zstd`
   - Ensure type ignore works in both local and CI environments
   - Fits current milestone: Yes

2. **Fix golden file test** (Owner: AI/Cursor)
   - Scope: `tests/test_ingest_golden.py`
   - Normalize path extraction to handle Windows and Unix formats
   - Or update golden file to use platform-agnostic paths
   - Fits current milestone: Yes

3. **Increase test coverage** (Owner: AI/Cursor)
   - Scope: CLI handlers, error paths in ingest module
   - Add tests for `cli.py` ingest commands
   - Add tests for error handling in `ingest/ingest.py` and `ingest/decompress.py`
   - Document intentional exclusion of HTTP fetcher paths (or add mocked HTTP tests)
   - Fits current milestone: Yes

### Deferred (Non-blocking for M02)

- HTTP fetcher integration tests (deferred per offline-first design)
- Performance benchmarks for large file decompression (out of scope for M02)

---

## Iteration History

This is **Run 1** of M02 CI. Multiple fix iterations were attempted:
- Initial push: Multiple CI failures (linting, type checking, tests, coverage)
- Fix iteration 1: Fixed line length, type ignores, file:// URI handling
- Fix iteration 2: Fixed indentation error, type checking approach
- Fix iteration 3: Attempted broader type ignore (still failing)

**Current status:** 3 blocking issues remain (type checking, golden test, coverage).

