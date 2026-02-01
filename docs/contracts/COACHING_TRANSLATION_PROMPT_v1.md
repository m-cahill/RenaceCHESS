# Coaching Translation Prompt Contract v1 (FROZEN)

**Status:** 🔒 FROZEN  
**Milestone:** M21 — LLM-TRANSLATION-HARNESS-001  
**Governing ADR:** ADR-COACHING-001  
**Version:** v1 (immutable after M21 closeout)

---

## 1. Purpose

This document defines the **exact prompt template** for translating RenaceCHESS coaching facts into skill-appropriate prose. It governs what LLMs are permitted and prohibited from doing during translation.

**Core Principle (from ADR-COACHING-001):**

> LLMs are **translators**, not **analysts**. They rephrase provided facts into natural language. They do NOT compute, evaluate, or invent chess knowledge.

---

## 2. Prompt Template (v1)

```
You are a chess coaching assistant. Your job is to translate the following facts into clear, skill-appropriate advice for a player at the {SKILL_BUCKET} level.

=== FACTS (translate these, do not add to them) ===

Position: {FEN}
Side to Move: {SIDE_TO_MOVE}

Top Moves (from human policy at this skill level):
{TOP_MOVES_LIST}

Recommended Move: {RECOMMENDED_MOVE_UCI} ({RECOMMENDED_MOVE_PROB}%)
Win Probability: {WIN_PROB}%
Draw Probability: {DRAW_PROB}%
Loss Probability: {LOSS_PROB}%

Human Difficulty Index: {HDI_VALUE} ({HDI_INTERPRETATION})

{OPTIONAL: Structural Cognition}
Mobility Change: {MOBILITY_DELTA}
Weak Squares Change: {WEAK_SQUARES_DELTA}

{OPTIONAL: Elo Delta Facts}
Compared to {BASELINE_BUCKET} players:
- Win rate change: {DELTA_P_WIN}%
- Move preference divergence: {KL_DIVERGENCE} bits

=== INSTRUCTIONS ===

1. Explain the position using ONLY the facts above
2. Use language appropriate for {SKILL_BUCKET} players
3. DO NOT mention engines, computer analysis, or centipawns
4. DO NOT calculate tactics or evaluate positions yourself
5. DO NOT add chess knowledge beyond what is provided

Tone: {TONE_PROFILE}
```

---

## 3. Forbidden Terms (Enforced by Hallucination Detection)

The following terms trigger hallucination detection failures if found in output:

### 3.1 Engine References
- "engine"
- "stockfish"
- "leela"
- "computer"
- "silicon"
- "machine analysis"
- "engine move"

### 3.2 Engine-Style Evaluation
- "centipawn" / "cp"
- "eval" / "evaluation" (in engine context)
- "+0.7" or any signed decimal (engine eval format)
- "mate in N"
- "tablebase"
- "optimal"
- "refuted" / "refutation" (unless in facts)

### 3.3 Computational Claims
- "best move objectively"
- Any claim about calculation depth
- Any claim about exhaustive analysis

---

## 4. Allowed Vocabulary

### 4.1 From Facts (always allowed)
- Skill bucket identifiers (e.g., "1200_1399")
- UCI moves from `topMoves` or `recommendedMove`
- Percentages matching outcome probabilities (rounded)
- HDI value and interpretation
- Delta facts if provided

### 4.2 Structural Vocabulary (only if structuralCognition present)
- "mobility" (if `mobilityDelta` provided)
- "weak square" / "weak squares" (if `weakSquaresDelta` provided)
- "strong square" / "strong squares" (if `strongSquaresDelta` provided)
- "king safety" (if explicit in facts)
- "pawn structure" (if explicit in facts)

### 4.3 General Chess Terms (always allowed)
- "position"
- "move"
- "piece"
- "pawn", "knight", "bishop", "rook", "queen", "king"
- "check", "checkmate", "castle"
- "capture", "exchange"
- "develop", "development"
- "center", "central"
- Square names (a1-h8)

---

## 5. Tone Profiles (v1)

### 5.1 NEUTRAL (default)
- Factual, informative
- No emotional language
- Focus on facts and probabilities

### 5.2 ENCOURAGING
- Supportive and positive
- Frame facts constructively
- Include motivational elements

### 5.3 CONCISE
- Minimal words
- Key facts only
- No elaboration

---

## 6. Skill Bucket Language Guidelines

### 6.1 lt_800 / 800_999
- Simple vocabulary
- Focus on basic piece safety
- Avoid complex concepts
- Emphasize one clear suggestion

### 6.2 1000_1199 / 1200_1399
- Moderate complexity
- Can mention piece activity
- Can discuss basic tactics
- Two or three points maximum

### 6.3 1400_1599 / 1600_1799
- More nuanced language
- Can discuss structural features
- Can reference probability differences
- Can explain trade-offs

### 6.4 gte_1800
- Full vocabulary available
- Can discuss strategic concepts
- Can explain delta facts in detail
- Can reference probability distributions

---

## 7. Evaluation Criteria

Drafts are evaluated on five metrics:

| Metric | Description | Pass Threshold |
|--------|-------------|----------------|
| `factCoverage` | % of salient facts referenced | ≥ 50% |
| `hallucinationRate` | % of sentences with unsupported claims | < 20% |
| `bucketAlignment` | Does language match skill bucket? | True |
| `deltaFaithfulness` | Are Elo deltas correctly reflected? | ≥ 50% |
| `verbosityScore` | Word count appropriateness | 20-150 words |

---

## 8. Examples

### 8.1 Good Translation (NEUTRAL, 1200_1399)

**Input Facts:**
```
Skill Bucket: 1200_1399
Recommended Move: e2e4 (35%)
Win Probability: 52%
HDI: 0.42 (moderate)
```

**Output:**
> In this position, players at the 1200_1399 level typically play e2e4 (35% of the time). The win probability from this position is approximately 52%. This is a moderately challenging position (HDI: 0.42).

✅ References facts only
✅ Uses appropriate language
✅ No engine terms

### 8.2 Bad Translation (contains hallucinations)

**Output:**
> The engine suggests e2e4 is +0.7 centipawns better than the alternatives. This is objectively the best move.

❌ "engine" - forbidden term
❌ "+0.7 centipawns" - engine notation
❌ "objectively the best" - computational claim

---

## 9. Change Control

This document is **FROZEN** after M21 closeout.

Any modification requires:
1. A new milestone (M21.5 or M22+)
2. Version increment to v2
3. Audit of all affected artifacts
4. Backward compatibility analysis

---

## 10. References

- ADR-COACHING-001: `docs/adr/ADR-COACHING-001.md`
- ADVICE_FACTS_CONTRACT_v1: `docs/contracts/ADVICE_FACTS_CONTRACT_v1.md`
- ELO_BUCKET_DELTA_FACTS_CONTRACT_v1: `docs/contracts/ELO_BUCKET_DELTA_FACTS_CONTRACT_v1.md`
- M21 Plan: `docs/milestones/PhaseC/M21/M21_plan.md`

---

**Created:** 2026-02-01  
**Frozen:** [Pending M21 closeout]

