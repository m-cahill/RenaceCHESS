# M18_plan — PERSONALITY-EVAL-HARNESS-001

## Milestone Identity

**Milestone:** M18 — PERSONALITY-EVAL-HARNESS-001  
**Phase:** Phase B — Personality Framework & Style Modulation  
**Status:** 🔜 Planned  
**Pre-reqs:**
- M15 — Personality Safety Contract (merged)
- M16 — Pawn Clamp Personality (merged)
- M17 — Neutral Baseline Personality (merged)

**Branch:** `m18-personality-eval-harness-001`

---

## 1. Purpose (Single Sentence)

Introduce an **evaluation harness** that measures personality effects against the Neutral Baseline, enabling scientific comparison of style transformations.

---

## 2. Why This Milestone Exists

After M17, we have:
- A Neutral Baseline (zero divergence control)
- A Pawn Clamp personality (bounded style effects)

Before adding more personalities, we need infrastructure to:
- **Measure divergence** between personalities and baseline
- **Generate evaluation reports** with style metrics
- **Validate bounded behavior** across positions

This is the "evaluation layer" that makes Phase B scientifically rigorous.

---

## 3. Explicit Non-Goals (Hard Constraints)

M18 **must not**:
- Add new personalities
- Modify existing personality behavior
- Change training or models
- Add LLM or coaching logic
- Integrate with product surfaces

This is **measurement infrastructure**, not behavior.

---

## 4. Scope — What M18 Does

*To be defined based on locked answers to clarifying questions.*

### Expected Scope (Draft)

- Personality evaluation runner
- Divergence metrics computation (KL, TV, per-move delta)
- Evaluation report schema (personality_eval_report.v1)
- CLI command for personality evaluation
- Sample evaluation on synthetic/frozen positions

---

## 5. Definition of Done (M18)

*To be finalized after plan review.*

Draft criteria:
- ✅ Evaluation harness implemented
- ✅ Divergence metrics computed correctly
- ✅ Evaluation reports generated
- ✅ CLI command working
- ✅ CI truthful green

---

## 6. Clarifying Questions

*To be asked at plan review phase.*

---

**Plan Status:** Draft (awaiting detailed specification)  
**Created:** 2026-01-31 (M17 closeout)

