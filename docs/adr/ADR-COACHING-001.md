# ADR-COACHING-001: LLM Coaching Must Use Grounded Facts Only

**Status:** Accepted  
**Date:** 2026-01-31  
**Milestone:** M19 — ADVICE-FACTS-CONTRACT-001  
**Phase:** Phase C — Elo-Appropriate Coaching & Explanation

---

## Context

RenaceCHESS produces calibrated, skill- and time-conditioned human move probabilities, outcome predictions (W/D/L), Human Difficulty Index (HDI), and structural cognition features. These signals form a truthful substrate for chess coaching and analysis.

Large Language Models (LLMs) excel at natural language generation but are unreliable at chess calculation, probability estimation, and tactical analysis. When asked to "explain" a chess position, LLMs frequently hallucinate tactical lines, invent evaluation details, or produce advice that sounds plausible but is factually incorrect.

Phase C introduces **Elo-appropriate coaching** — translating RenaceCHESS signals into skill-appropriate explanations. This ADR defines the fundamental constraint that prevents coaching from becoming a hallucination vector.

---

## Decision

**LLM coaching must use grounded facts only. No invention.**

Specifically:

### 1. Facts-Only Artifact

All coaching generation must start from an **AdviceFacts** artifact — a schema-validated, deterministic payload containing pre-computed signals:

- Position (FEN, side to move)
- Conditioning context (skill bucket, time pressure)
- Policy distribution (top moves with probabilities)
- Outcome prediction (W/D/L)
- HDI value and components
- Structural cognition deltas (optional)

The AdviceFacts artifact is produced by RenaceCHESS code, not by the LLM.

### 2. Translation, Not Computation

LLMs may only **translate** AdviceFacts fields into natural language. They may not:

- Compute or infer chess evaluations not present in facts
- Invent tactical lines or variations
- Claim move quality beyond what probabilities indicate
- Generate advice that contradicts the facts
- Add speculation disguised as analysis

### 3. Explicit Grounding Requirements

Every coaching output must be traceable to specific AdviceFacts fields:

| Coaching Claim | Required Grounding |
|----------------|-------------------|
| "This move is popular at your level" | `policy.topMoves[].prob` |
| "This position is difficult" | `hdi.value` |
| "You have good winning chances" | `outcome.pWin` |
| "Consider developing your pieces" | `structuralCognition.mobility` (when present) |

### 4. Complexity Scaling

Coaching complexity should scale with the player's skill bucket:

- **Lower Elo:** Simpler language, focus on one key point
- **Higher Elo:** More nuanced, reference multiple factors

This scaling is a **presentation** choice, not an invitation to invent additional analysis.

---

## Consequences

### Positive

1. **Truthful coaching** — Advice is grounded in calibrated model outputs, not LLM speculation
2. **Measurable quality** — Coaching can be evaluated against the facts it claims to translate
3. **Reproducibility** — Same AdviceFacts → same factual claims (LLM variance only in phrasing)
4. **Auditability** — Every claim has a traceable source in the deterministic artifact

### Negative

1. **Limited scope** — Coaching cannot explain concepts not captured in AdviceFacts
2. **Dependency on model quality** — Bad model → bad facts → bad coaching (but honestly bad)
3. **Rigidity** — Adding new coaching topics requires schema evolution

### Neutral

1. **LLM still required** — For natural language generation and Elo-appropriate phrasing
2. **Schema evolution expected** — As coaching matures, AdviceFacts will expand

---

## Enforcement

1. **Contract boundary:** `ADVICE_FACTS_CONTRACT_v1.md` defines the schema
2. **Import boundary:** `coaching/` module is isolated via import-linter
3. **Test coverage:** Determinism tests verify fact generation is reproducible
4. **Review discipline:** Coaching prompts must explicitly cite which facts they use

---

## Related Decisions

- `CONTRACT_INPUT_SEMANTICS.md` — Dict input conventions
- `PERSONALITY_SAFETY_CONTRACT_v1.md` — Bounded behavioral modulation
- `StructuralCognitionContract_v1.md` — M11 feature definitions

---

## References

- Phase B Audit (2026-01-31): Recommended ADR-COACHING-001 for Phase C
- VISION.md: "RenaceCHESS computes probabilities; LLMs translate grounded facts"
- Post-PoC Anchor: "AdviceFacts pipeline (facts → translation)"

---

**Signed:** RenaceCHESS Governance  
**Effective:** Upon M19 merge

