Below is a **paste-ready M01 plan prompt** you can hand to Cursor. It assumes **M00 is closed/immutable** and builds forward from the established contracts + determinism baseline in your attached closeout docs.  

---

## Cursor handoff — **M01 Plan**

```text
You are Cursor operating as an implementation agent for RenaceCHESS.

Milestone: M01 — Deterministic Dataset Shard Builder (Local PGN → JSONL + Manifest)
Branch: m01-dataset-shards (one branch per milestone)
Objective (single): Add a deterministic, schema-validated “dataset shard builder” that converts local PGNs into JSONL records of Context Bridge payloads, and emits a Dataset Manifest referencing the produced shard(s).

GOVERNANCE (non-negotiable)
- One milestone = one primary objective. No scope creep.
- CI truthfulness stays strict: required checks must remain authoritative.
- Maintain coverage thresholds (>= 90% lines, >= 85% branches).
- All outputs must be deterministic: stable ordering, stable hashing, no time-based drift in tests.
- Milestone artifacts required:
  - docs/milestones/M01_plan.md
  - docs/milestones/M01_summary.md
  - docs/milestones/M01_audit.md
  - M01_toolcalls.md (log tool/actions; initialize even if empty)

M01 SCOPE (IN)
1) Dataset shard builder library code:
   - Input: local PGN file(s) (no network IO)
   - Output: JSON Lines (.jsonl) file(s), each line = one Context Bridge payload record (schema v1)
   - Output: Dataset Manifest (schema v1) referencing shard(s)
   - Deterministic hashing + deterministic “split assignment” (train/val/frozenEval) based on record key hashing

2) CLI extension:
   - `renacechess dataset build --pgn <file|dir> --out <dir> [--max-games N] [--max-positions N] [--start-ply X] [--end-ply Y]`
   - Writes:
     - <out>/shards/<shard_id>.jsonl
     - <out>/manifest.json

3) Tests + goldens:
   - Golden shard JSONL + golden manifest, generated from tests/data/sample.pgn
   - Schema validation tests for every record line
   - CLI smoke test

4) Small contract hardening: Pydantic alias validation forward-compat
   - Replace/augment model config to use `validate_by_alias` + `validate_by_name` (equivalent behavior to prior populate_by_name) and keep `by_alias=True` serialization where appropriate.
   - Add/keep tests proving both alias-based and snake_case name-based inputs validate.

M01 SCOPE (OUT)
- No Lichess downloads / ingestion pipeline.
- No ML training.
- No engine integration.
- No UI.

IMPLEMENTATION PHASES (small milestones within M01)

PHASE 0 — Initialization & Recovery
- Create branch `m01-dataset-shards` from current `main`.
- Initialize `M01_toolcalls.md`.
- Create docs skeleton:
  - docs/milestones/M01_plan.md (this plan, adjusted to actual repo state)
  - docs/milestones/M01_summary.md (stub)
  - docs/milestones/M01_audit.md (stub)

PHASE 1 — Core Dataset Builder (library)
- Add a new module (suggested):
  - src/renacechess/dataset/
      __init__.py
      builder.py
      manifest.py
      split.py
      config.py (dataclass / Pydantic model for build config)
- Builder responsibilities:
  1) Enumerate games and positions deterministically:
     - Always iterate PGN files in sorted order.
     - Always iterate games in file order.
     - Always iterate positions by ply increasing.
     - If `max_positions` is set, take the first N encountered (no randomness).
  2) For each position:
     - Reuse the existing Context Bridge generator (refactor to a pure function if needed).
     - Ensure `generatedAt` is injectable so tests can freeze it.
  3) Write JSONL:
     - One JSON object per line, newline delimited.
     - Use canonical JSON from determinism module for stable bytes.
     - No trailing spaces; newline at end of file.

PHASE 2 — Dataset Manifest + Split Assignment
- Use existing dataset manifest schema v1 and conform exactly.
- Manifest should include (only fields that schema allows):
  - schemaVersion
  - createdAt (injectable/frozen in tests)
  - shardRefs (each referencing shard id/path + any allowed metadata)
  - filterConfigHash (sha256 of canonical config JSON)
  - splitAssignments (deterministic mapping, if allowed by schema)
- Split strategy (deterministic):
  - Define record_key = position.fen (or a stable composite like fen + ply).
  - split_bucket = int(sha256(record_key)[:8], 16) % 100
  - Example allocation:
    - 0–4   => frozenEval (5%)
    - 5–14  => val       (10%)
    - 15–99 => train     (85%)
  - Ensure the split logic is unit-tested and stable.

PHASE 3 — Pydantic Alias Validation Forward-Compat (micro-hardening)
- Update model config to align with Pydantic v2.11+ guidance:
  - Use validate_by_alias=True, validate_by_name=True where needed
  - Preserve serialization by alias for JSON outputs
- Add/maintain tests verifying:
  - alias input validates
  - snake_case input validates
  - JSON output uses camelCase keys (aliases)

PHASE 4 — Tests + Goldens
Add tests and goldens:
- tests/golden/
  - shard.demo.v1.jsonl
  - manifest.demo.v1.json
- Tests:
  1) test_dataset_build_golden.py
     - Build dataset with fixed params and frozen timestamps
     - Compare produced JSONL bytes (canonical) to golden
     - Compare produced manifest to golden (canonical)
  2) test_dataset_schema_validation.py
     - For each JSONL line, validate against context_bridge.schema.json
     - Validate manifest against dataset_manifest.schema.json
  3) test_cli_dataset_build.py
     - Run CLI build into tmp dir
     - Assert files exist and hashes match expected
  4) test_split_determinism.py
     - Assert known record_key -> expected split bucket

Guardrails:
- If any schema needs changes, do NOT mutate v1 silently:
  - Prefer adding v2 schemas in contracts/schemas/v2/
  - Keep v1 intact
  - Update code to emit v2 only if necessary, and document in M01_audit.md

PHASE 5 — CI + Documentation
- Ensure CI still runs:
  - ruff check
  - ruff format --check
  - mypy
  - pytest + coverage gates
- Add docs:
  - docs/DATASETS.md describing:
    - JSONL output format
    - deterministic build rules
    - how to reproduce shards from the same input PGN
    - how the manifest references shards
- Update README briefly to mention `renacechess dataset build`.

DEFINITION OF DONE (M01)
- CI green on PR (all required jobs pass).
- `renacechess dataset build` works and produces deterministic outputs.
- Golden shard + manifest tests pass.
- Every JSONL line validates against Context Bridge schema.
- Manifest validates against dataset manifest schema.
- Pydantic alias/name validation behavior is explicitly tested and stable.
- M01_plan/M01_summary/M01_audit committed and complete.

AUDIT POSTURE
- Any deviation (schema bump, config shift, etc.) must be recorded in M01_audit.md with:
  - rationale
  - blast radius
  - evidence (tests/CI run links)
- No “temporary” ignores unless explicitly justified and planned for removal.

DELIVERABLES CHECKLIST (PR description must include)
- [ ] Dataset builder module
- [ ] CLI dataset build command
- [ ] JSONL + manifest outputs (deterministic)
- [ ] Golden tests + schema validation tests
- [ ] Docs: DATASETS.md + updated README
- [ ] Milestone docs: M01_plan/M01_summary/M01_audit + M01_toolcalls.md
```

---

### Notes (why these choices are “enterprise-grade”)

* **JSON Lines** is an appropriate streaming dataset format for “one record per position” pipelines. ([JSON Lines][1])
* **python-chess PGN parsing** is mature and well-documented, so we can keep M01 local and deterministic without building our own PGN reader. ([Python Chess][2])
* **Pydantic alias validation**: in newer Pydantic versions, `validate_by_name`/`validate_by_alias` provides the fine-grained behavior and is explicitly documented as equivalent to the old “populate-by-name” behavior when both are true. ([Pydantic][3])

If you want, M02 can be “network ingestion (Lichess) with cached, reproducible download manifests,” but M01 as written keeps us **small, deterministic, and fully verifiable**.

[1]: https://jsonlines.org/?utm_source=chatgpt.com "JSON Lines"
[2]: https://python-chess.readthedocs.io/en/latest/pgn.html?utm_source=chatgpt.com "PGN parsing and writing - python-chess - Read the Docs"
[3]: https://docs.pydantic.dev/latest/api/config/?utm_source=chatgpt.com "Configuration - Pydantic Validation"


