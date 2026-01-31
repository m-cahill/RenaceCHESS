# M16 — PERSONALITY-PAWNCLAMP-001

## Milestone Identity

| Field | Value |
|-------|-------|
| **Phase** | Phase B: Personality Framework & Style Modulation |
| **Milestone ID** | M16 |
| **Codename** | PERSONALITY-PAWNCLAMP-001 |
| **Status** | ⏳ Pending |

---

## Objective

Implement the first concrete personality module ("Pawn Clamp") that demonstrates M15's personality framework in action, while validating all safety constraints and evaluation requirements.

---

## Prerequisites

- [x] M15 complete (Personality Safety Contract + Interface)
- [x] PersonalityModuleV1 protocol defined
- [x] SafetyEnvelopeV1 and PersonalityConfigV1 models available
- [x] Import boundary `personality-isolation` enforced

---

## Scope

### In Scope

| Component | Description |
|-----------|-------------|
| Pawn Clamp Personality | First concrete implementation of PersonalityModuleV1 |
| Configuration | Pawn clamp specific config extending PersonalityConfigV1 |
| Unit Tests | Validation of safety constraints and envelope compliance |
| Eval Integration | Metrics per M15_PERSONALITY_EVAL_REQUIREMENTS.md |

### Out of Scope

| Item | Rationale |
|------|-----------|
| LLM coaching integration | Phase C work |
| Elo-specific behavior | Phase C work |
| Training changes | No model retraining |
| Multiple personalities | M16 is single personality only |

---

## Deliverables

1. **Pawn Clamp Implementation**
   - `src/renacechess/personality/pawn_clamp.py`
   - Implements PersonalityModuleV1 protocol
   - Respects SafetyEnvelopeV1 constraints

2. **Configuration**
   - Pawn clamp specific parameters
   - Validates against PersonalityConfigV1 schema

3. **Tests**
   - Safety envelope validation tests
   - Base reachability tests (is_identity verification)
   - Constraint violation detection tests

4. **Evaluation Metrics**
   - Per M15_PERSONALITY_EVAL_REQUIREMENTS.md
   - Entropy metrics
   - Move diversity metrics

---

## Success Criteria

1. Pawn clamp personality passes all unit tests
2. Safety envelope constraints are enforced
3. Import boundaries remain intact
4. Coverage ≥ 90% maintained
5. No PoC semantics touched
6. CI green on first or second run

---

## Definition of Done

- [ ] Pawn clamp implementation complete
- [ ] All tests passing
- [ ] CI green
- [ ] Audit generated
- [ ] Summary generated
- [ ] PR merged to main

---

## Notes

*This plan is a skeleton. Full plan to be developed when M16 work begins.*

