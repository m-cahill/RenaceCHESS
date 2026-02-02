# M28 Plan — PHASE-D-RECALIBRATION-ACTIVATION-DECISION-001

**Status:** Pending  
**Audience:** Cursor / AI agent  
**Phase:** Phase D (Data Expansion, Calibration & Quality)  
**Predecessor:** M27 (Runtime Recalibration Evaluation)

---

## 🎯 M28 Objective (Single Sentence)

> **Decide whether to activate runtime recalibration** based on M27 evaluation data, and implement the chosen activation strategy (or document the decision to abandon/defer).

---

## 📋 Prerequisites

M28 cannot begin until:

1. ✅ M27 merged to main
2. ✅ M27 evaluation artifacts reviewed
3. ⏳ Activation decision made (enabled globally / restricted / abandoned)

---

## 🔒 Hard Constraints (Non-Negotiable)

1. **Phase C contracts frozen** — No changes to AdviceFactsV1, EloBucketDeltaFactsV1, CoachingDraftV1
2. **Default path governed** — Any activation must pass M26 guard job (byte-identical default when gate disabled)
3. **Evidence-based decision** — Activation decision must cite M27 evaluation data
4. **Deterministic outputs** — All artifacts must be reproducible

---

## 🎯 Possible Outcomes

Based on M27 evaluation data, M28 will implement one of:

### Option A: Enable Globally

- Recalibration enabled for all Elo buckets
- Gate becomes opt-out (default enabled)
- Update CLI defaults

### Option B: Enable Selectively

- Recalibration enabled for specific Elo buckets (e.g., only where improvement observed)
- Gate configuration specifies scope
- Bucket-level activation map

### Option C: Defer/Abandon

- Evaluation shows no clear benefit or regressions
- Document decision and rationale
- No code changes (governance-only milestone)

---

## 📦 Deliverables (Depends on Decision)

| Decision | Deliverables |
|----------|--------------|
| Option A | Updated gate defaults, CLI changes, updated docs |
| Option B | Bucket-scoped gate configuration, selective activation |
| Option C | Decision document only, no code changes |

---

## 🧪 Tests (If Code Changes)

- Unit tests for new activation logic
- Integration tests for CLI defaults
- Regression tests for default path
- M26 guard job must pass

---

## 📈 Success Criteria

M28 is complete when:

1. ✅ Decision documented with M27 evidence
2. ✅ If code changes: All CI jobs pass
3. ✅ If code changes: Coverage ≥ 90%
4. ✅ M26 guard job still passes (default path byte-identical)
5. ✅ Audit and summary generated

---

## 🚫 Explicit Non-Goals

- Adding new model heads
- Changing Phase C contracts
- Retraining models
- Adding new calibration methods

---

*This plan will be refined once M27 merge is complete and evaluation data is reviewed.*


