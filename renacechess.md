# RenaceCHESS — Source of Truth

This document tracks milestones, schema, migrations, and governance decisions for RenaceCHESS.

---

## Milestones

| Milestone | Status | Branch | Completion Date | Description |
|-----------|--------|--------|-----------------|-------------|
| M00 | ✅ Closed | `m00-bootstrap` → `main` | 2026-01-23 | Repository Bootstrap + Contract Skeleton + Deterministic Demo |

---

## Database Schema

*(No database schema yet — to be added in future milestones)*

---

## Migrations

*(No migrations yet — to be added in future milestones)*

---

## Governance Decisions

### M00 Decisions

1. **Python Version:** Python 3.11 only (documented in M00_audit.md)
2. **Coverage Thresholds:** 90% lines, 85% branches (achieved 93.36%)
3. **Pydantic Naming Strategy:** snake_case Python attributes with camelCase JSON aliases via `Field(alias=...)` (documented in M00_audit.md)
4. **CI Truthfulness:** All gates enforced from day zero, no weakening or bypassing

---

**Last Updated:** 2026-01-23 (M00 closeout)

