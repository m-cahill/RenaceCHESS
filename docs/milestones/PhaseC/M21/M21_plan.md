# M21 Milestone Plan — LLM-TRANSLATION-HARNESS-001

**Phase:** Phase C — Elo-Appropriate Coaching & Explanation  
**Status:** 🔜 Planned  
**Predecessor:** M20 — ELO-BUCKET-DELTA-FACTS-001

---

## Objective

Introduce the LLM translation harness for converting facts-only artifacts (AdviceFactsV1, EloBucketDeltaFactsV1) into Elo-appropriate coaching prose.

This milestone establishes:
- A deterministic translation interface
- Offline coaching evaluation framework
- Truthfulness constraints per ADR-COACHING-001

---

## Scope

### In Scope

- LLM translation interface/protocol definition
- Translation harness that consumes M19 + M20 artifacts
- Offline coaching evaluation harness
- Truthfulness metrics (fact grounding, hallucination detection)
- Test fixtures for translation evaluation
- Contract documentation

### Out of Scope

- Live LLM API calls in CI
- User-facing coaching UI
- Multi-turn conversation
- Provider orchestration
- Training or fine-tuning

---

## Entry Criteria

- [x] M20 merged and closed
- [x] EloBucketDeltaFactsV1 artifact available
- [x] AdviceFactsV1 artifact available
- [x] ADR-COACHING-001 in effect

---

## Exit Criteria

- [ ] LLM translation interface defined (protocol/abstract class)
- [ ] Translation harness accepts AdviceFacts + EloBucketDeltaFacts
- [ ] Offline evaluation harness for coaching truthfulness
- [ ] Truthfulness metrics documented (grounding, hallucination rate)
- [ ] Contract documentation for translation interface
- [ ] Tests for translation harness (determinism, grounding)
- [ ] CI green

---

## Technical Approach

### 1. Translation Interface

Define a protocol for LLM translation:
- Input: AdviceFactsV1, optional EloBucketDeltaFactsV1
- Output: Structured coaching response with grounding metadata
- Constraints: No analysis beyond provided facts

### 2. Offline Evaluation

Create an evaluation harness that:
- Measures fact grounding (% of claims traceable to artifacts)
- Detects hallucinations (claims not supported by artifacts)
- Computes coaching quality metrics

### 3. Test Fixtures

Create synthetic fixtures for:
- Simple positions with clear advice
- Complex positions requiring delta reasoning
- Edge cases (equal buckets, extreme skill gaps)

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| LLM outputs are non-deterministic | Use structured output formats, temperature=0 |
| Hallucination detection is hard | Focus on explicit fact grounding |
| Scope creep into live systems | Strict offline-only constraint |

---

## Dependencies

- M19: AdviceFactsV1 artifact
- M20: EloBucketDeltaFactsV1 artifact
- ADR-COACHING-001: Truthfulness constraints

---

## Estimated Duration

2-3 sessions

---

*Plan created: 2026-02-01*

