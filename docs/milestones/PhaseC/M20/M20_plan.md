# M20 Plan — ELO-BUCKET-DELTA-REASONING-001

**Phase:** Phase C — Elo-Appropriate Coaching & Explanation  
**Milestone:** M20  
**Status:** 🔜 Planned  
**Prerequisite:** M19 (ADVICE-FACTS-CONTRACT-001)

---

## Objective

Extend AdviceFacts generation with Elo-bucket delta reasoning — generating skill-level-specific facts about move quality and position assessment.

---

## Scope

### In Scope

- Skill-bucket-aware move quality commentary (facts, not prose)
- Delta reasoning between skill levels (e.g., "this move is more popular at higher Elo")
- ExplanationHints population (M19 placeholder becomes active)
- Extended AdviceFacts builder with delta inputs

### Out of Scope

- LLM translation (M21)
- Coaching CLI commands (M22)
- Prose generation of any kind

---

## Entry Criteria

- M19 merged and closed
- AdviceFacts schema frozen
- ADR-COACHING-001 in effect

---

## Exit Criteria

- [ ] ExplanationHints populated in AdviceFacts builder
- [ ] Skill-delta facts documented in schema
- [ ] Tests for delta reasoning
- [ ] CI green

---

**Created:** 2026-02-01 (M19 closeout)

