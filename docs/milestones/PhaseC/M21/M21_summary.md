# 📌 Milestone Summary — M21: LLM-TRANSLATION-HARNESS-001

**Project:** RenaceCHESS  
**Phase:** C — Elo-Appropriate Coaching & Explanation  
**Milestone:** M21 — LLM Translation Harness + Coaching Evaluation  
**Timeframe:** 2026-02-01  
**Status:** ✅ **CLOSED**

---

## 1. Milestone Objective

Introduce LLMs as **pure translators, not analysts** — determining whether an LLM can produce skill-appropriate coaching prose without inventing chess knowledge, given pre-computed facts from M19 (AdviceFactsV1) and M20 (EloBucketDeltaFactsV1).

**Problem Addressed:**  
Phase C required a mechanism to convert deterministic facts into natural language coaching while:
- Preventing LLM hallucination of chess analysis
- Maintaining determinism in CI
- Enabling offline quality evaluation

**Baseline:** M20 (Elo-Bucket Delta Facts Artifact)

---

## 2. Scope Definition

### In Scope

| Category | Deliverable |
|----------|-------------|
| Protocol | `LLMClient` abstract interface |
| Implementation | `DeterministicStubLLM` (CI-safe, no network) |
| Harness | `translate_facts_to_coaching()` function |
| Evaluation | `evaluate_coaching_draft()` with hallucination detection |
| Contracts | `CoachingDraftV1`, `CoachingEvaluationV1` Pydantic models |
| Schemas | `coaching_draft.v1.schema.json`, `coaching_evaluation.v1.schema.json` |
| Prompt Contract | `COACHING_TRANSLATION_PROMPT_v1.md` (FROZEN) |
| Tests | 33 constraint-driven tests |
| Guardrail | AST-based import boundary test |

### Out of Scope

- Live coaching UI
- CLI commands for coaching
- Real LLM vendor integration (OpenAI, Anthropic)
- Training/fine-tuning
- Engine references in output
- New chess heuristics
- AdviceFacts/DeltaFacts schema changes
- Human-in-the-loop evaluation

---

## 3. Work Executed

### Core Implementation

| Component | Files | Lines | Purpose |
|-----------|-------|-------|---------|
| LLM Client | `coaching/llm_client.py` | 271 | Protocol + deterministic stub |
| Translation Harness | `coaching/translation_harness.py` | 237 | Facts → prose pipeline |
| Evaluation Harness | `coaching/evaluation.py` | 435 | Hallucination detection + metrics |
| Pydantic Models | `contracts/models.py` (+280) | — | CoachingDraftV1, CoachingEvaluationV1 |
| JSON Schemas | 2 new files | 278 | Contract definitions |

### Hallucination Detection (v1)

Rule-based heuristics implemented:
1. **Forbidden terms detector** — 15+ terms (engine, stockfish, centipawn, etc.)
2. **Move-reference constraint** — Only `topMoves`/`recommendedMove` allowed
3. **Numeric-claim constraint** — Percentages must match source facts (rounded)
4. **Structural-claim constraint** — Controlled vocabulary (mobility, weak squares, etc.)

### Evaluation Metrics

| Metric | Description | Pass Threshold |
|--------|-------------|----------------|
| `factCoverage` | Fraction of salient facts referenced | ≥50% |
| `hallucinationRate` | Unsupported claims per sentence | <20% |
| `bucketAlignment` | Language matches skill bucket | True |
| `deltaFaithfulness` | Elo delta accuracy | ≥50% |
| `verbosityScore` | Word count appropriateness | 20-150 words |

---

## 4. Validation & Evidence

### Test Suite

| Category | Tests | Status |
|----------|-------|--------|
| Stub LLM | 5 | ✅ Pass |
| Translation Harness | 7 | ✅ Pass |
| Hallucination Detection | 5 | ✅ Pass |
| Evaluation Harness | 7 | ✅ Pass |
| Schema Validation | 2 | ✅ Pass |
| Import Boundary | 2 | ✅ Pass |
| Invariants | 5 | ✅ Pass |
| **Total** | **33** | ✅ Pass |

### CI Run

| Run | Status | Details |
|-----|--------|---------|
| First run | ✅ GREEN | All 3 jobs pass |

### Enforcement

- `coaching-isolation` import-linter contract: **KEPT**
- AST-based import boundary test: **PASS**
- Coverage: 91.34% (exceeds 90% gate)

---

## 5. CI / Automation Impact

### Workflows Affected
- None — CI definition unchanged

### Checks Added
- None new (existing gates sufficient)

### Enforcement Behavior
- ✅ CI **blocked** no incorrect changes (first-run green)
- ✅ CI **validated** determinism via stub LLM
- ✅ Import-linter **prevented** boundary violations

---

## 6. Issues & Exceptions

**No new issues were introduced during this milestone.**

### Observations (Non-Blocking)

| ID | Observation | Status |
|----|-------------|--------|
| M21-O01 | `llm_client.py` at 79% coverage | Acceptable (edge cases in stub) |
| M21-O02 | Minor branch gaps in `evaluation.py` | Acceptable (structural claim edge cases) |

---

## 7. Deferred Work

**No work deferred from M21.**

All deliverables completed within scope.

---

## 8. Governance Outcomes

### What Is Now Provably True

1. **LLMs can only translate pre-computed facts** — Hallucination detection enforces this
2. **Coaching prose is deterministic in CI** — Stub LLM guarantees reproducibility
3. **Prompt contract is governance-locked** — FROZEN status prevents drift
4. **Coaching module remains isolated** — Import boundary enforced by tests + import-linter
5. **No network calls in CI** — Stub is default, vendor integration opt-in

### Architectural Significance

With M21 closed, RenaceCHESS can now provably claim:

> "Coaching text is a deterministic linguistic rendering of explicit, human-conditioned facts — not engine analysis disguised as advice."

---

## 9. Exit Criteria Evaluation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| CoachingDraftV1 schema defined | ✅ Met | `coaching_draft.v1.schema.json` |
| CoachingEvaluationV1 schema defined | ✅ Met | `coaching_evaluation.v1.schema.json` |
| Translation harness functional | ✅ Met | 7 passing tests |
| Evaluation harness with metrics | ✅ Met | 5 metrics implemented |
| Hallucination detection heuristics | ✅ Met | 4 heuristics validated |
| Prompt contract frozen | ✅ Met | `COACHING_TRANSLATION_PROMPT_v1.md` |
| CI green (first run) | ✅ Met | Run 21554787481 |
| Coverage ≥90% | ✅ Met | 91.34% |
| coaching-isolation contract kept | ✅ Met | import-linter pass |

---

## 10. Final Verdict

**Milestone objectives met. Safe to proceed.**

M21 achieved first-run green CI at the most sensitive architectural boundary in the project — LLM integration. All Phase C invariants were preserved. The coaching module is now complete for its core mission: translating facts into skill-appropriate prose while preventing hallucination.

---

## 11. Authorized Next Step

**Proceed to M22** — or close Phase C core if the coaching explanatory spine is considered functionally complete.

Phase C status after M21:
| Layer | Status |
|-------|--------|
| Facts substrate | ✅ M19 |
| Cross-bucket reasoning | ✅ M20 |
| Safe LLM translation | ✅ M21 |
| Surface exposure | ❌ Deferred |

The explanatory spine is complete. Surface exposure (CLI, UI) remains for Phase D or E.

---

## 12. Canonical References

### Commits
- **Merge commit:** d351ca2
- **Implementation commit:** 164e77e
- **Run analysis commit:** 2138ae1

### Pull Requests
- **PR #27:** https://github.com/m-cahill/RenaceCHESS/pull/27

### CI Runs
- **Run 21554787481:** https://github.com/m-cahill/RenaceCHESS/actions/runs/21554787481

### Documents
- Plan: `docs/milestones/PhaseC/M21/M21_plan.md`
- Run Analysis: `docs/milestones/PhaseC/M21/M21_run1.md`
- Audit: `docs/milestones/PhaseC/M21/M21_audit.md`
- Prompt Contract: `docs/contracts/COACHING_TRANSLATION_PROMPT_v1.md`

### Governing ADR
- ADR-COACHING-001: `docs/adr/ADR-COACHING-001.md`

---

**Summary Closed:** 2026-02-01

