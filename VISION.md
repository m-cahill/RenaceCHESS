RenaceCHESS — Not Another Chess Engine; it’s a Cognitive Human Evaluation & Skill Simulation
==========================================================================================

1. Purpose and north-star outcome

---------------------------------

Build a **human-centered chess intelligence system** that can:

1. predict **what move a human of a given skill (and time pressure) is likely to play**,

2. estimate **human win/draw/loss chances for that same skill level**, and

3. provide **LLM-groundable context** for real-time, natural-language coaching and broadcast narrative — **without asking the LLM to “calculate chess.”**

The endgame is *not* “stronger-than-Stockfish.”
The endgame is a **human decision & difficulty simulator** that supports:

- creator tooling (recaps, highlights, “why humans miss this”),
- coaching (skill/time-conditioned advice),
- and “Chessmaster-style” controllable personalities (aggression/defense, material vs positional emphasis, concept attention like passed pawns/king safety) **without collapsing into “always play the engine #1 move.”**

The system is grounded in **open, scalable data** from Lichess’ public database exports (released under **CC0** and permitted for download/redistribution). ([database.lichess.org](https://database.lichess.org/))

* * *

2. What this project is and is not

----------------------------------

### This project **is**

- A **probabilistic human decision model**:
  \[
  P(\text{move} \mid \text{position}, \text{skill}, \text{time})
  \]

- A **skill-conditioned human outcome model** (not engine self-play):
  \[
  P(\text{W/D/L} \mid \text{position}, \text{skill}, \text{time})
  \]

- A **context-grounding layer** that turns those probabilities into stable, structured payloads for LLM coaching/broadcast (the “LLM Context Bridge”).

### This project **is not**

- A new superhuman engine.

- A replacement for Stockfish/Leela.

- A purely “chatty” LLM chess coach (we explicitly avoid hallucination-by-guessing by grounding advice in calibrated probabilities).

* * *

3. Key thesis (why this matters now)

------------------------------------

Modern LLMs are excellent at language but unreliable at **calculation, probability, and domain calibration** under time pressure.

RenaceCHESS is designed to **decouple calculation from explanation**:

- **RenaceCHESS** computes *human-conditioned* probabilities (move distribution, human WDL, difficulty).
- An **LLM** converts those grounded facts into coaching language, narrative, and product UX.

This is the “unlock” for modern AI product stacks in chess: **Context Grounding**.

* * *

PoC-Core (must be complete, auditable, and Google/Microsoft-handable)
=====================================================================

4. PoC objective (single sentence)

----------------------------------

Produce an auditable PoC (paper + demo artifact) proving that, using CC0 Lichess games ([database.lichess.org](https://database.lichess.org/)), we can generate **calibrated, skill- and time-conditioned human move probabilities and human WDL**, and expose them through a stable “LLM Context Bridge” API that enables truthful real-time coaching and creator tooling.

* * *

5. PoC-Core deliverables

------------------------

### 5.1 Reproducible dataset pipeline (appendable without redesign)

**Outputs:**

- Immutable **position shards** (e.g., Parquet) containing:
  
  - FEN / position encoding
  - legal move encoding
  - chosen move label
  - player rating (bucketed)
  - time control class (at minimum: blitz vs rapid)
  - time features (at minimum: a coarse time-pressure bucket)
  - game outcome label (from the mover’s perspective)

- A **dataset manifest** that includes:
  
  - shard hashes
  - filter config hash
  - schema version
  - split assignments (train/val/frozen-eval)

**Hard requirement:** adding another month of games = **new shards + updated manifest**, no refactor.

### 5.2 Frozen evaluation set (never changes)

A small but representative eval corpus, stratified by:

- skill buckets (minimum 4)
- time-pressure regimes (minimum 3)
- game phase proxy (optional but recommended: move number bands)

### 5.3 Core models (policy + human outcome)

A single model can share a trunk with two heads:

1. **Policy head**: predicts move distribution over legal moves  
2. **Outcome head**: predicts **human** W/D/L (or expected score) for the mover at that skill/time

Rationale: superhuman engines aren’t good predictors of human choices; skill-conditioned move prediction is learnable at scale and useful for human-AI alignment. See **Maia** (paper + Microsoft Research project page). ([Maia paper](https://www.cs.toronto.edu/~ashton/pubs/maia-kdd2020.pdf), [Project Maia](https://www.microsoft.com/en-us/research/project/project-maia/))

### 5.4 Conditioning variables (minimum PoC set)

- **Skill bucket** (native Lichess rating bands, no cross-site mapping required)
- **Time-pressure bucket** (NORMAL / LOW / TROUBLE)
- Optional (recommended if low cost): time control class (blitz/rapid)

### 5.5 Human-realism stress tests & “anti-collapse” gates

Add automated checks that fail the PoC if:

- the policy becomes trivially engine-peaked in ambiguous positions (probability mass collapses unrealistically),
- calibration degrades badly in higher skill buckets,
- time-pressure conditioning has no measurable effect (a sign features aren’t wired or data is wrong).

**PoC-minimum HRS suite (v1):**

- entropy decreases with skill (trend check),
- time-pressure increases blunder probability / policy entropy (trend check),
- no “engine-like spikes” in quiet positions (distribution sanity check),
- stability across reruns of the frozen-eval set (determinism + regression).

### 5.6 Broadcast-style artifact (the “wow” demo)

Given a PGN:

- show top-N predicted human moves with probabilities,
- show **human W/D/L before and after the played move** for that skill bucket,
- highlight “surprise moves” (low predicted probability),
- optionally show engine WDL/eval only as a **contrast layer** (never the primary “human truth”). (Stockfish `UCI_ShowWDL` + WDL model docs: [UCI & Commands](https://official-stockfish.github.io/docs/stockfish-wiki/UCI-%26-Commands.html), [WDL model](https://official-stockfish.github.io/docs/stockfish-wiki/Useful-data.html), [WDL_model repo](https://github.com/official-stockfish/WDL_model))

### 5.7 GenAI Grounding Interface (the “LLM Context Bridge”)

A standardized JSON output designed for:

- LLM context injection (Gemini/Copilot/etc.),
- RAG/document grounding,
- creator automation (recaps, highlights, thumbnails, captions),
- coaching UX (tips and warnings that are *factually true* for the given skill/time).

**PoC v1 payload shape (minimum fields):**

- `position`: `{ fen, sideToMove, legalMoves[] }`
- `conditioning`: `{ skillBucket, timeControlClass?, timePressureBucket }`
- `policy`: `{ topMoves: [{ uci, san?, p }], entropy, topGap }`
- `humanWDL`: `{ pre: {w,d,l}, postByMove: { uci -> {w,d,l} } }`
- `hdi`: `{ value, components: { entropy, topGap, wdlSensitivity } }`
- `narrativeSeeds`: `[{ type, severity, facts[] }]`
  - Examples:
    - “trap-risk”: “Engine win% ↑, but human-1200 blunder risk ↑”
    - “confusing”: “Top-3 moves near-equal probability”
    - “time-sensitive”: “Trouble-time causes sharp accuracy drop”

**Important:** LLMs should *not* “invent evaluation.” They only translate these facts into language.

### 5.8 Developer-facing API contract (platform feel)

Freeze a minimal contract surface so this can plug into product stacks cleanly:

- `predict_move_distribution(position, skill, time) -> policy`
- `predict_human_wdl(position, skill, time) -> wdl`
- `explain_position_human_difficulty(position, skill, time) -> {hdi, clf?}`
- `generate_personality_policy(position, personality) -> policy_delta` *(post-PoC implementation; PoC defines the contract)*
- `produce_llm_grounding_payload(position, skill, time, options) -> json`

PoC requirement: inputs/outputs are versioned and schema-validated.

### 5.9 Human Difficulty Index (HDI) + Cognitive Load Features (CLF) — PoC v1

**HDI (PoC v1):** a single scalar intended to answer:

> “How hard is this position **for humans at this skill/time**?”

**PoC v1 compute (suggested):**

- policy entropy (dispersion of human choices),
- top-move probability gap (clarity vs ambiguity),
- WDL sensitivity (how much human WDL changes across candidate moves).

**CLF (PoC v1, optional/report-only):**

- “candidate set size” after pruning (top-K coverage),
- tactical horizon proxy (e.g., presence of forcing lines / checks / captures density),
- conceptual load tags (king safety / pawn tension / initiative proxies),
- local vs global tension proxy.

These are *derived features* for explainability; PoC can ship them as “experimental.”

* * *

6. PoC-Core success criteria (what makes it “viable”)

-----------------------------------------------------

The PoC is considered successful when:

1. **Data**: dataset can be rebuilt deterministically; manifest verification passes; adding new data is append-only.
2. **Policy quality**: NLL improves meaningfully over baselines; calibration is reasonable; stratified reports are stable.
3. **Outcome quality**: human W/D/L predictions are calibrated per bucket and respond sensibly to time-pressure.
4. **Human realism**: HRS/anti-collapse gates pass; model remains “human-distributional,” not “always engine #1.”
5. **Grounding**: the LLM Context Bridge payload is schema-stable and demonstrably supports truthful coaching/recap.
6. **Demo**: PGN overlay artifact convincingly shows why this is better than Stockfish-only commentary.

* * *

7. PoC-Core scope boundaries

----------------------------

### In scope

- Lichess-only data
- policy + human W/D/L heads
- skill + time-pressure conditioning
- frozen-eval set + regression baselines
- LLM Context Bridge JSON + schema versioning
- minimal HDI/CLF (as defined above)

### Explicitly out of scope for PoC

- full personality suite training
- player-specific personalization
- full error taxonomy / blunder ontology
- longitudinal “skill trajectory” modeling
- v3 ingestion / generalized multi-domain ingestion

* * *

Later additions (post-PoC roadmap sections)
===========================================

8. Higher-Elo extension and “human-3000” projection

---------------------------------------------------

After PoC stability:

- increase skill bucket granularity into GM bands,

- model how decision entropy, blunder tails, and conversion rates change with skill/time,

- extrapolate with monotone/saturating constraints to avoid “turning into Stockfish.”
9. Chessmaster-style personality suite (controllable without large strength drift)

----------------------------------------------------------------------------------

Introduce a **bounded style layer** that reweights the base policy using concept deltas:

- passed pawns attention
- king safety sensitivity
- mobility/activity emphasis
- material vs positional preference
- aggression/defense bias
- custom piece values (0–15) as constraints/biases (not a new evaluator)

**Governance requirement (added): Personality Suite Stability Tests**

- strength drift regression,

- blunder rate stability by bucket,

- concept-weight monotonicity,

- bounded aggression/defense deltas (no pathological extremes).
10. Explainability, broadcast overlays, and narrative trace generation

---------------------------------------------------------------------

Turn grounded signals into creator/broadcaster tools:

- “most aggressive candidate move”
- “most king-pressure move”
- “most defensive consolidation”
- “best for human win% at this rating” vs “best for engine win%”

**Narrative Trace Generator (product feature):**

- consumes the LLM Context Bridge payload,

- produces recaps (template-first; LLM optional),

- supports highlight selection (“turning points,” “missed wins,” “confusion spikes”).
11. Human vs engine divergence map (the “wow slide”)

----------------------------------------------------

A visualization-ready artifact showing:

- where humans deviate from engines,

- how divergence changes with skill/time,

- which concepts drive divergence (via CLF/concept deltas).
12. Player-specific modeling (optional)

---------------------------------------

Personalize move probabilities and risk preferences for individual players (only where sufficient data exists). (Background: Microsoft Research’s Maia write-up highlights skill- and player-conditioned modeling directions. [The human side of AI for chess](https://www.microsoft.com/en-us/research/blog/the-human-side-of-ai-for-chess/))

13. Skill-conditioned error taxonomy (Human blunder ontology)

------------------------------------------------------------

A reusable framework that categorizes human mistakes:

- tactical oversight patterns
- positional misunderstanding patterns
- time-pressure degradation modes
- skill-specific blind spots

This becomes a universal language for coaching/broadcast/LLMs, but is deferred until post-PoC.

14. Reasoning trace alignment layer

-----------------------------------

Align natural-language explanations to model probabilities:

- reasoning traces grounded in policy/WDL/HDI,

- trace-level consistency checks (no “made up” tactics),

- trace compression/expansion for coaching.
15. Human skill trajectory model (explicitly deferred)

------------------------------------------------------

A longitudinal model predicting:

- how accuracy changes over time,
- how time pressure affects improvement,
- how concept mastery changes blunder rates.

This is **not** a PoC dependency.

16. Phase XVI: RediAI v3 ingestion and enhancements (explicitly deferred)

-------------------------------------------------------------------------

Phase XVI is where we:

- formalize ingestion as a RediAI library capability,
- add additional governance/automation improvements,
- generalize dataset + grounding contracts for other domains.

This is **not** a PoC dependency.

* * *

17. One-line narrative for a Google/Microsoft handoff

-----------------------------------------------------

“We prove—using CC0 Lichess data ([database.lichess.org](https://database.lichess.org/))—that we can generate calibrated, skill- and time-conditioned **human move probability** and **human win probability** for any position, and we provide a schema-stable **LLM Context Bridge** that enables truthful real-time coaching, creator automation, and a clear post-PoC path to Chessmaster-grade controllable personalities and divergence-aware broadcast overlays.”
