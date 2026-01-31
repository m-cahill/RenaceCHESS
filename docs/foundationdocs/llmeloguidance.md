What you want is an **“explanation compiler”**: take _human-grounded deltas_ (what stronger humans do differently) + _structural deltas_ (what the move changes) + _difficulty signals_ (HDI/CLF) → emit **skill-appropriate advice** that never drifts into engine-speak.

This fits RenaceCHESS’s core thesis: **calculation/probability lives in RenaceCHESS; language lives in the LLM; the bridge is structured and factual**.

Below is a concrete architecture + an auto-generation pipeline + a phased plan with small milestones and E2E verification at each step.

* * *

1) The “Next Bucket Delta” is the coaching signal

-------------------------------------------------

For a position (s) and bucket (k):

* (P_k(a \mid s)): human move policy for bucket (k) (over legal moves)

* (P_{k+1}(a \mid s)): policy for next bucket

Compute:

* **Policy delta:** (\Delta P(a) = P_{k+1}(a)-P_k(a))

* Optional: **advantage delta:** (\Delta \text{WDL}(a) = \text{WDL}_k(\text{post}(s,a)) - \text{WDL}_k(\text{pre}(s)))

**Interpretation:** moves with high (\Delta P) are “the next thing to learn” because stronger humans prefer them _without needing engine justification_.

### Picking the coaching target (deterministic)

Choose 1 coaching move (a^*) using a simple, stable rule:

1. Candidate set (C) = top-N by (\Delta P) (e.g., N=3), filtered to avoid:
   
   * extremely low base probability in both buckets (noise)
   
   * only-move tactics if you want “Capablanca mode” (see forcing filters below)

2. Select (a^*) = argmax over a weighted score:  
   [  
   \text{score}(a)=\alpha \cdot \Delta P(a) + \beta \cdot \Delta \text{WDL}(a) - \gamma \cdot \text{ComplexityPenalty}(s,a)  
   ]

This yields advice that is:

* **skill-scaffolded** (learn what next bucket does)

* **human-realistic** (human distributions)

* **non-engine** (no “+0.73” talk)

* * *

2) Turn deltas into “why” using structural features

---------------------------------------------------

You already sketched this: you don’t want the LLM inventing reasons; you want it **mapping measured deltas to a concept label**.

### 2.1 Feature deltas you can compute cheaply

For each candidate move (a), compute “before/after” structural deltas:

* **Piece activity**: mobility changes, activation of worst piece

* **Square control**: key square contested/uncontested, outpost creation/denial

* **King safety**: exposure, attackers near king, luft status

* **Pawn structure**: weaknesses created/removed, pawn tension changes

* **Tension/forcing**: checks/captures/threat density; “resolution vs maintenance”

* **Coordination**: piece connections, defender count on critical points

These can be lightweight heuristics (not Stockfish), because your grounding is human preference + human WDL, not perfect play.

### 2.2 Concept attribution (deterministic classifier)

Build a small rule-based scorer that maps deltas → concept tags.

Example concept set (Capablanca-friendly):

* **Develop / improve worst piece**

* **Centralize / contest key square**

* **Reduce opponent activity**

* **King safety / avoid weakening**

* **Maintain tension vs release tension**

* **Simplify when ahead / avoid trades when behind** (bucket-gated)

* **Convert advantage: improve position before grabbing pawns**

Each concept gets a score from deltas; pick top 1–2 concepts. This is **explainability without free-form LLM invention**.

* * *

3) Use HDI/CLF to keep the explanation “Elo-appropriate”

--------------------------------------------------------

RenaceCHESS already frames HDI/CLF as _the knobs that keep language honest and level-appropriate_.

### 3.1 Difficulty-aware verbosity + vocabulary gates

* If **HDI high** (ambiguous position): advice must be shorter, with “safe principles”

* If **CLF high** (tactical load): emphasize _risk reduction_ and _forcing move awareness_

* If player is far from next bucket: pick **one** concept, one sentence, one follow-up

* If close to next bucket: allow a second concept or a short “if…then…” line

### 3.2 Forcing-move guardrail (prevents engine-speak)

If forcing density is high (checks/captures dominate), positional heuristics can mislead.

So:

* In “Capablanca mode,” **filter out** advice that requires a 4-move tactic unless it’s also a high-probability human motif for that bucket.

* Otherwise switch to a “tactical safety” template: _“Check threats first; don’t allow …”_

* * *

4) Make the LLM a renderer, not a reasoner

------------------------------------------

You want a deterministic payload that the LLM converts into English.

### Advice Payload (v1)

This parallels your “LLM Context Bridge” philosophy: structured facts → language.
    {
      "bucket": 1200,
      "nextBucket": 1400,
      "position": { "fen": "...", "sideToMove": "w" },
      "recommendation": {
        "move": "Nf3",
        "altMovePlayed": "h3",
        "deltaPolicy": 0.22,
        "deltaWDL": { "win": +0.07, "draw": -0.01, "loss": -0.06 }
      },
      "concepts": [
        { "tag": "improve_worst_piece", "evidence": ["knight mobility +5", "connects rooks sooner"] },
        { "tag": "contest_key_square", "evidence": ["increases control of d4/e5"] }
      ],
      "difficulty": { "hdi": 0.63, "clf": { "forcingDensity": 0.18, "candidateMoves": 6 } },
      "constraints": {
        "maxSentences": 2,
        "vocabTier": "simple",
        "noEngineEval": true
      }
    }

The LLM prompt becomes trivial:

* **DO NOT** add new chess claims

* Speak only from payload fields

* Use allowed templates for the bucket

This gives you:

* reproducibility

* auditability

* consistent skill scaling

* low hallucination surface area

(And it aligns with your general governance/testing posture: **don’t re-test platform invariants; test the new claim**.)

* * *

5) Capablanca-style heuristic library as templates

--------------------------------------------------

Think of these as **rendering templates** keyed by concept tags and difficulty tier:

### Example template (simple tier)

**Tag:** improve_worst_piece

> “Stronger players usually develop here. It gets your _[piece]_ into the game and makes your position easier to play.”

### Example template (intermediate tier)

**Tag:** contest_key_square

> “This move fights for _[square]_ and limits your opponent’s plans. That’s why stronger players choose it more often.”

### Example template (high HDI)

**Tag:** safe_principle

> “There are a few playable moves here, so keep it simple: improve a piece and avoid creating new weaknesses.”

The key is: **templates are stable; content slots are filled from measured deltas**.

* * *

6) End-to-end verification: how you prove it works

--------------------------------------------------

You’ll want tests that check the advice is:

1. **grounded** (no fabricated facts),

2. **level-appropriate**, and

3. **useful** (correlates with next-bucket improvement).

### Suggested evaluation harness (v1)

* **Factuality checks (hard gates):**
  
  * Every noun phrase about “why” must map to a concept tag present in payload
  
  * Every numeric claim must match payload values
  
  * No engine terms (banlist)

* **Complexity checks (hard gates):**
  
  * Sentence count ≤ limit
  
  * Reading level proxy (word list tier)

* **Outcome checks (soft metrics):**
  
  * When advice recommends (a^*), verify (P_{k+1}(a^*)) is meaningfully higher than (P_k(a^*))
  
  * Optional offline A/B: does showing advice increase selection of (a^*) in a sandbox?

* * *

7) Phased plan with small milestones (E2E each time)

----------------------------------------------------

### M1 — Advice Payload v1 (no LLM yet)

**Goal:** deterministically produce the payload for a position.

* Implement (\Delta P) selection + basic structural deltas + concept tagger

* Output JSON only

* **E2E:** golden test fixtures: given frozen inputs → byte-stable payload

### M2 — Template Renderer (no free-form generation)

**Goal:** render English without an LLM.

* Render from templates using payload slots

* **E2E:** snapshot tests: payload → exact string

### M3 — LLM Renderer (strict)

**Goal:** LLM produces the same kind of output as templates, but more natural.

* Constrain with: allowed templates, max tokens, banned terms, “no new facts”

* **E2E:** “extraction test”: parse LLM output back into claims and verify all claims exist in payload

### M4 — Difficulty scaling (HDI/CLF gates)

**Goal:** advice changes _only_ in verbosity/vocab as HDI/CLF changes.

* **E2E:** same position, different bucket/time-pressure → different style, same factual base

### M5 — “Why this move” from next-bucket (the big unlock)

**Goal:** validate that your advice aligns with bucket transition.

* **E2E:** offline report: for a sample set, recommended move’s (\Delta P) distribution + concept frequencies

* * *

If you want, the next concrete step is to **lock the concept tag set + the deterministic selection rule** (that’s the part you’ll least want to revisit later). The rest—templates, phrasing, UI—can iterate without threatening correctness.
