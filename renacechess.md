# RenaceCHESS — Source of Truth

This document tracks milestones, schema, migrations, and governance decisions for RenaceCHESS.

---

## Milestones

| Milestone | Status | Branch | Completion Date | Description |
|-----------|--------|--------|-----------------|-------------|
| M00 | ✅ Closed | `m00-bootstrap` → `main` | 2026-01-23 | Repository Bootstrap + Contract Skeleton + Deterministic Demo |

**M00 Details:**
- **CI Run 1:** 21271461853 (FAILURE - 28 Ruff errors, 7 MyPy errors)
- **CI Run 2:** 21271784917 (SUCCESS - All gates passing)
- **Final Coverage:** 93.36% lines, ~88.7% branches
- **Remediation Commit:** `1c29812b5942adcd8a36374130b30a31c538158e`
- **Audit:** `docs/milestones/PoC/M00/M00_audit.md`
- **Summary:** `docs/milestones/PoC/M00/M00_summary.md`

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
- **Status:** ✅ Complete and validated (stubbed but real)

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

**Last Updated:** 2026-01-23 (M00 closeout)

