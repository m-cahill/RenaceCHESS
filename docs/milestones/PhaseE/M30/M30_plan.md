# M30 Plan — Frozen Eval Scale Planning

**Project:** RenaceCHESS  
**Phase:** E (Release)  
**Milestone:** M30 — FROZEN-EVAL-SCALE-001  
**Prerequisite:** M29 closed ✅  
**Branch:** TBD

---

## 0. Why M30 Exists

M29 validated that the RTX 5090 hardware stack is viable for training. M30 determines the **appropriate scale for the frozen evaluation set** that will be used to measure model quality throughout training and release.

This milestone bridges infrastructure validation (M29) and actual training (M31).

---

## 1. Milestone Objective

> **Determine the frozen eval set size, composition, and coverage requirements for Phase E release, using M29 synthetic throughput as a conservative baseline.**

---

## 2. Scope Definition

### ✅ In Scope

1. **Frozen eval sizing analysis**
   - Minimum positions for statistical significance
   - Coverage across skill buckets, time controls, time pressure
   - Balance between evaluation rigor and evaluation time

2. **Evaluation time budget**
   - Target: eval completes in < N minutes per checkpoint
   - Use M29 synthetic throughput (conservative) for estimates

3. **Frozen eval manifest requirements**
   - Document required fields for production frozen eval
   - Define stratification targets

4. **Documentation**
   - M30 summary and audit
   - Frozen eval scale recommendation document

### ❌ Out of Scope

- Actual frozen eval generation (requires production data → M31)
- Real-data benchmarking (deferred from M29 → M31)
- Model training (M31)
- Production ingestion (pre-M31 data pipeline work)

---

## 3. Deliverables

| Deliverable | Description |
|-------------|-------------|
| Frozen eval sizing doc | Analysis of position counts, coverage, eval time budget |
| M30 summary | Milestone summary with recommendations |
| M30 audit | Closeout audit |

---

## 4. Exit Criteria

- [ ] Frozen eval size recommendation documented
- [ ] Evaluation time budget defined
- [ ] Coverage requirements specified (skill/time/pressure buckets)
- [ ] M30 audit completed
- [ ] Ready to proceed to M31

---

## 5. Notes

This is a **planning milestone**, not an implementation milestone. No code changes expected unless documentation requires schema updates.

---

**Created:** 2026-02-02  
**Status:** PENDING

