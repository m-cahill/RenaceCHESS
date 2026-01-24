# RenaceCHESS — Source of Truth

This document tracks milestones, schema, migrations, and governance decisions for RenaceCHESS.

---

## Milestones

| Milestone | Status | Branch | Completion Date | Description |
|-----------|--------|--------|-----------------|-------------|
| M00 | ✅ Closed | `m00-bootstrap` → `main` | 2026-01-23 | Repository Bootstrap + Contract Skeleton + Deterministic Demo |
| M01 | ✅ Closed | `m01-dataset-shards` → `main` | 2026-01-23 | Deterministic Dataset Shard Builder (PGN → JSONL + Manifest) |
| M02 | ✅ Closed | `m02-lichess-ingestion` → `main` | 2026-01-23 | Deterministic Lichess Ingestion |
| M03 | ✅ Closed | `m03-dataset-assembly` → `main` | 2026-01-23 | Deterministic Multi-Shard Dataset Assembly |
| M04 | ✅ Closed | `m04-eval-harness` → `main` | 2026-01-24 | Evaluation Harness v0: Deterministic Policy Evaluation Over Dataset Manifests |
| M05 | ✅ Closed (MERGED) | `m05-labeled-evaluation` → `main` | 2026-01-24 | Ground-Truth Labeled Evaluation v1: Accuracy Metrics and Evaluation Report v2 |

**M00 Details:**
- **CI Run 1:** 21271461853 (FAILURE - 28 Ruff errors, 7 MyPy errors)
- **CI Run 2:** 21271784917 (SUCCESS - All gates passing)
- **Final Coverage:** 93.36% lines, ~88.7% branches
- **Remediation Commit:** `1c29812b5942adcd8a36374130b30a31c538158e`
- **Audit:** `docs/milestones/PoC/M00/M00_audit.md`
- **Summary:** `docs/milestones/PoC/M00/M00_summary.md`

**M01 Details:**
- **CI Run 1:** 21279550886 (FAILURE - Format check + coverage 89.02% < 90%)
- **CI Run 2-3:** Intermediate runs (linting fixes)
- **CI Run 4:** 21279736846 (SUCCESS - All gates passing)
- **Final Coverage:** 92.12% lines (exceeds 90% threshold)
- **Test Count:** 51 tests (up from 40)
- **PR:** #3 (ready for merge)
- **Audit:** `docs/milestones/PoC/M01/M01_audit.md`
- **Summary:** `docs/milestones/PoC/M01/M01_summary.md`

**M02 Details:**
- **CI Run 1:** 21283043075 (FAILURE - Type checking, golden test, coverage 83.37% < 90%)
- **CI Run 2:** 21283688678 (FAILURE - Lint hygiene, MyPy, golden test)
- **CI Run 3:** 21284581552 (SUCCESS - All gates passing)
- **Final Coverage:** 93.94% lines (exceeds 90% threshold)
- **Test Count:** 144 tests (up from 95)
- **PR:** #4 (ready for merge)
- **Final Commit:** `5d8b3e2`
- **Audit:** `docs/milestones/PoC/M02/M02_audit.md`
- **Summary:** `docs/milestones/PoC/M02/M02_summary.md`

**M03 Details:**
- **CI Run 1:** 21304980117 (FAILURE - Formatting only, all tests passing)
- **CI Run 2:** 21305144364 (SUCCESS - All gates passing)
- **Final Coverage:** 92.45% lines (exceeds 90% threshold)
- **Test Count:** 160 tests (up from 144)
- **PR:** #5 (merged)
- **Final Commit:** `0acae10`
- **Audit:** `docs/milestones/PoC/M03/M03_audit.md`
- **Summary:** `docs/milestones/PoC/M03/M03_summary.md`

**M04 Details:**
- **CI Run 1:** 21306101033 (FAILURE - Formatting only, all tests passing)
- **CI Run 2:** 21306130316 (SUCCESS - All gates passing)
- **Final Coverage:** Meets 90% threshold (CI job passed)
- **Test Count:** 180 tests (up from 160)
- **PR:** #6 (merged)
- **Final Commit:** `c99e148`
- **Audit:** `docs/milestones/PoC/M04/M04_audit.md`
- **Summary:** `docs/milestones/PoC/M04/M04_summary.md`

**M05 Details:**
- **CI Run 1:** 21306671140 (FAILURE - Formatting and coverage 89.18% < 90%)
- **CI Run 2:** 21306722594 (SUCCESS - All gates passing)
- **Final Coverage:** 92.38% (exceeds 90% threshold)
- **Test Count:** 204 tests (up from 199)
- **PR:** #7 (ready for merge)
- **Final Commit:** `82e9454`
- **Audit:** `docs/milestones/PoC/M05/M05_audit.md`
- **Summary:** `docs/milestones/PoC/M05/M05_summary.md`

---

## Database Schema

*(No database schema yet — to be added in future milestones)*

---

## Migrations

*(No migrations yet — to be added in future milestones)*

---

## Governance Decisions

### M00 Decisions

1. **Python Version:** Python 3.11 only
   - **Rationale:** Determinism > optional compatibility at M00. 3.11 is the current "enterprise-safe" baseline.
   - **Documented in:** `docs/milestones/PoC/M00/M00_audit.md`

2. **Coverage Thresholds:** 90% lines, 85% branches
   - **Rationale:** Small codebase + deterministic logic = no excuse not to be strict.
   - **Achieved:** 93.36% lines, ~88.7% branches (exceeds requirement)
   - **Documented in:** `docs/milestones/PoC/M00/M00_audit.md`

3. **Pydantic Naming Strategy:** snake_case Python attributes with camelCase JSON aliases
   - **Implementation:** Use `Field(alias=...)` with `ConfigDict(populate_by_name=True)`
   - **Rationale:** Preserves Python naming conventions while maintaining JSON schema compatibility
   - **Documented in:** `docs/milestones/PoC/M00/M00_audit.md`

4. **CI Truthfulness:** All gates enforced from day zero, no weakening or bypassing
   - **Gates:** Ruff lint, MyPy typecheck, Pytest with coverage
   - **Evidence:** CI Run 1 correctly identified 35 real errors; Run 2 confirmed all fixes
   - **Documented in:** `docs/milestones/PoC/M00/M00_run1.md`, `M00_run2.md`

---

## Versioned Contracts

### Context Bridge Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/context_bridge.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.ContextBridgePayload`
- **Status:** ✅ Complete and validated

### Dataset Manifest Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/dataset_manifest.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.DatasetManifest`
- **Status:** ✅ Complete and validated (backward compatible, preserved)

### Dataset Manifest Schema (v2)
- **Location:** `src/renacechess/contracts/schemas/v1/dataset_manifest.v2.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.DatasetManifestV2`
- **Status:** ✅ Complete and validated (default for new builds)

### Ingest Receipt Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/ingest_receipt.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.IngestReceiptV1`
- **Status:** ✅ Complete and validated

### Evaluation Report Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/eval_report.v1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.EvalReportV1`
- **Status:** ✅ Complete and validated (immutable)

### Evaluation Report Schema (v2)
- **Location:** `src/renacechess/contracts/schemas/v1/eval_report.v2.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.EvalReportV2`
- **Status:** ✅ Complete and validated (extends v1 with accuracy metrics)

### Context Bridge Schema (v1) — Extended
- **Location:** `src/renacechess/contracts/schemas/v1/context_bridge.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.ContextBridgePayload`
- **Status:** ✅ Complete and validated (v1-compatible extension with optional `chosenMove` field)

---

## Key Guarantees Established in M00

From M00 forward, RenaceCHESS guarantees:

1. **Truthful CI Baseline:** All gates enforce real quality standards, not cosmetic checks
2. **Enforced Static Analysis:** Ruff and MyPy enforced from day zero
3. **Deterministic Artifact Generation:** Byte-stable, reproducible outputs via canonical JSON
4. **Versioned Contracts:** Schema-first design with JSON Schema + Pydantic validation
5. **Coverage Discipline:** Coverage gates enforced and exceeded (93.36% > 90%)
6. **Governance Loop:** Proven workflow of "fail → analyze → fix → verify"

---

**Last Updated:** 2026-01-24 (M05 closeout)


