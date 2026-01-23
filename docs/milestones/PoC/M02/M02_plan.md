# M02 Plan — Deterministic Lichess Ingestion

**Milestone:** M02  
**Status:** 🔄 **IN PROGRESS**  
**Branch:** `m02-lichess-ingestion`

---

## Single Objective

Add a deterministic, audit-friendly ingestion pipeline for Lichess database exports:
- download (or fetch from local file URL for tests),
- cache,
- verify integrity via sha256,
- optionally decompress .pgn.zst to .pgn,
- emit a versioned "ingest receipt" manifest that makes the artifact reproducible.

## Deferred Issues

**Resolves:**
- M01-002: Lichess network ingestion (deferred to M02+) ✅ address in M02.

**Keeps deferred:**
- M01-001: Multi-shard strategies (defer to M03+).

## Non-Negotiable Governance

- One milestone = one primary objective (ingestion). No feature creep.
- CI truthfulness remains strict. Do NOT weaken gates.
- Maintain coverage thresholds: >= 90% lines, >= 85% branches.
- All tests MUST be offline/deterministic (no external network calls in CI).
- Required milestone artifacts:
  - docs/milestones/PoC/M02/M02_plan.md
  - docs/milestones/PoC/M02/M02_summary.md
  - docs/milestones/PoC/M02/M02_audit.md
  - docs/milestones/PoC/M02/M02_toolcalls.md
  - docs/milestones/PoC/M02/M02_run1.md, etc. (if needed)

## M02 Scope (IN)

### 1) Ingestion Module (new)

**Location:** `src/renacechess/ingest/`

**Files:**
- `__init__.py`
- `lichess.py` — URL builder + preset metadata
- `fetch.py` — fetchers: http + file
- `cache.py` — cache layout + atomic writes
- `receipt.py` — receipt model + JSON schema validation
- `decompress.py` — zst → pgn streaming decompression
- `types.py` — small dataclasses/TypedDicts

**Supports:**
- Fetch by Lichess "monthly dump" URL pattern (standard rated) OR explicit URL.
- Local file source (file:// or path) for tests.
- Cache hits (skip re-download if sha matches).
- sha256 verification for downloaded bytes.
- Optional decompress of .zst to .pgn using streaming (no huge memory usage).

### 2) New Contract: Ingest Receipt Schema v1 + Pydantic Model

**Location:**
- `contracts/schemas/v1/ingest_receipt.schema.json`
- `contracts/models.py` updated with:
  - `IngestReceiptV1`
  - `SourceArtifactRefV1`

**Receipt MUST include:**
- `schemaVersion` ("v1")
- `createdAt` (injectable/frozen in tests)
- `source`: { `uri`, `resolvedUri?`, `etag?`, `lastModified?`, `contentLength?` }
- `artifact`: { `cachePath`, `sha256`, `sizeBytes`, `mediaType`, `compression?` }
- `derived`: { `decompressedPath?`, `decompressedSha256?`, `decompressedSizeBytes?` } (optional)
- `provenance`: { `toolVersion`, `platform?`, `pythonVersion?` } (keep minimal)

Receipt must validate against schema, and schema must be versioned.

### 3) CLI Additions

**Extend CLI with an "ingest" command group:**
- `renacechess ingest lichess --month YYYY-MM --out <dir> [--decompress] [--cache-dir <dir>]`
  - Default preset: standard rated monthly dump.
- `renacechess ingest url --url <https://...> --out <dir> [--decompress]`

**CLI behavior:**
- Never downloads in CI tests from the public internet.
- Prints a short summary including sha256 and output paths.
- All filesystem writes are atomic where feasible (write temp + rename).

### 4) Documentation

**`docs/INGESTION.md`:**
- what gets downloaded
- CC0 licensing note for Lichess exports
- huge file sizes warning + recommended approach (use small early months for local experiments)
- reproducibility: receipt is the "proof"

**README update:** add example usage.

## M02 Scope (OUT)

- No torrent support (lichess provides torrents; we will document but not implement).
- No multi-shard dataset rollover strategy.
- No training pipeline.
- No UI.

## Primary Sources / Reality Checks

- Lichess DB exports are available at database.lichess.org and are released under CC0; files are .pgn.zst monthly dumps and also have .torrent links.
- The "standard rated" monthly dump index is publicly browsable (pattern-based filenames).
- Decompression should be streaming via zstandard library.

## Phased Execution

### PHASE 0 — Initialization & Recovery

- ✅ Create branch m02-lichess-ingestion from main.
- ✅ Initialize docs/milestones/PoC/M02/M02_toolcalls.md.
- ✅ Create M02_plan.md.

### PHASE 1 — Contracts: Ingest Receipt v1

- Add `ingest_receipt.schema.json` (v1).
- Add corresponding Pydantic models with alias behavior consistent with existing style.
- Add tests:
  - Schema validation (jsonschema) for a minimal receipt instance.
  - Roundtrip: Model -> canonical JSON -> schema validate.

### PHASE 2 — Cache + Fetch (offline-first design)

- Implement a cache layout:
  - `<cache_dir>/sources/<source_id>/<filename>`
  - `<cache_dir>/receipts/<source_id>.json`
- Define source_id deterministically:
  - `sha256(canonical JSON of {preset/url, month, resolvedUri})[:16]`
- Implement FileFetcher:
  - accepts file paths and file:// URIs
  - copies to cache via atomic write
- Implement HttpFetcher:
  - streaming download to temp file
  - optional ETag/Last-Modified recording (best-effort)
  - computes sha256 while streaming
  - NO external network in tests; only unit test via local http.server if needed.

### PHASE 3 — Zstandard Decompression (optional)

- Add dependency: `zstandard` (python-zstandard) >= 0.22
- Implement streaming decompress: .zst → .pgn (write to cache/derived/).
- Compute sha256 + size of decompressed output.
- Receipt "derived" section populated when --decompress used.
- Tests use tiny fixture .pgn.zst in tests/data/.

### PHASE 4 — CLI Integration

- Add `ingest` group + subcommands.
- Ensure CLI supports:
  - `--cache-dir` override
  - `--out` target directory for exported artifacts and receipt copy
- Provide output:
  - Path to cached artifact
  - sha256
  - receipt path

### PHASE 5 — Tests + Goldens (deterministic, offline)

- Add fixtures:
  - `tests/data/sample_lichess_small.pgn` (tiny)
  - `tests/data/sample_lichess_small.pgn.zst` (compressed fixture)
- Add tests:
  1) `test_ingest_file_receipt_schema.py`
     - ingest from local path
     - receipt validates
     - sha matches expected
  2) `test_ingest_zst_decompress.py`
     - ingest .zst fixture with --decompress
     - decompressed sha matches expected
     - receipt includes derived fields
  3) `test_ingest_cache_hit.py`
     - ingest same source twice
     - second run is cache hit (no rewrite, same sha, deterministic receipt)
  4) `test_cli_ingest_smoke.py`
     - run CLI against fixture paths (no network)
     - asserts output files exist + receipt parseable
- Optional golden:
  - `tests/golden/ingest_receipt.v1.json` (only if stable after freezing createdAt).

### PHASE 6 — CI & Docs

- Ensure CI gates pass:
  - ruff check + format --check
  - mypy
  - pytest + coverage gates
- Add `docs/INGESTION.md` and update README.

## Definition of Done (M02)

- CI green on PR.
- Offline deterministic ingestion tests pass.
- `renacechess ingest url` works for local file inputs.
- `renacechess ingest lichess --month YYYY-MM` constructs correct URL (no download required in CI, but URL builder covered by unit tests).
- Ingest receipt schema v1 exists and is validated in tests.
- Optional decompress works on fixture .zst deterministically.
- M02_plan/M02_summary/M02_audit/M02_toolcalls committed and complete.
- Deferred registry updated:
  - Mark M01-002 resolved by M02
  - Keep M01-001 deferred to M03+

## Guardrails / Anti-Flake Rules

- No public internet in CI tests. Use local fixtures or a localhost server only.
- No "skip" based on environment variables unless strictly necessary and documented.
- Any new dependency must be justified in M02_audit.md (zstandard is expected).

## Output Format

- Open PR: m02-lichess-ingestion → main
- PR description must include a checklist mapped to Definition of Done.
- If any deviation occurs, document it in M02_audit.md with rationale and evidence.

---

## Notes for Documentation

* Lichess database exports are published at **database.lichess.org**, are **CC0**, and the monthly game dumps are **`.pgn.zst`** (with torrent links available).
* Use **streaming decompression** for `.zst` via `python-zstandard` APIs (avoid loading large archives into memory).
* Be explicit in docs about **huge storage requirements** for full-history downloads; encourage starting with small early months for local runs.

---

### Why This M02 is the Right Next Step

M01 proved you can **materialize deterministic datasets from local PGN**; M02 makes the dataset supply **realistic and reproducible** by adding a cache + receipt layer—without forcing you into multi-shard policy or big-data ops yet.
