# M22 Plan — [PENDING DEFINITION]

**Milestone:** M22  
**Phase:** C — Elo-Appropriate Coaching & Explanation  
**Status:** 🔜 Pending  
**Prerequisite:** M21 (LLM-TRANSLATION-HARNESS-001)

---

## Context

M21 completed the Phase C core coaching spine:
- M19: AdviceFactsV1 — facts-only substrate
- M20: EloBucketDeltaFactsV1 — cross-bucket comparison
- M21: LLM Translation Harness — deterministic coaching prose

The Phase C **explanatory spine is now complete**.

---

## Candidate Objectives

The following are potential M22 directions (to be decided):

### Option A: Coaching CLI Integration
- Add CLI commands for coaching generation
- Expose `translate_facts_to_coaching()` via CLI
- Print draft text, metrics, pass/fail status

### Option B: Coaching Evaluation Improvements
- Add more hallucination heuristics
- Implement additional evaluation metrics
- Create benchmark evaluation set

### Option C: Phase C Closeout
- Formal Phase C closeout document
- Close Phase C, open Phase D (Data Expansion)

### Option D: Real LLM Integration (Local Only)
- Add OpenAI/Anthropic adapter
- Keep out of CI (local development only)
- Add configuration for API keys

---

## Scope

*To be defined after direction is selected.*

---

## Acceptance Criteria

*To be defined after direction is selected.*

---

## References

- M21 Summary: `docs/milestones/PhaseC/M21/M21_summary.md`
- Phase C roadmap: `docs/postpocphasemap.md`
- ADR-COACHING-001: `docs/adr/ADR-COACHING-001.md`

---

**Plan Status:** Awaiting direction from project governance

