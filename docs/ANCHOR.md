# RenaceCHESS Project Anchor

## Purpose and North Star

Build a **human-centered chess intelligence system** that can:

1. Predict **what move a human of a given skill (and time pressure) is likely to play**
2. Estimate **human win/draw/loss chances for that same skill level**
3. Provide **LLM-groundable context** for real-time, natural-language coaching and broadcast narrative — **without asking the LLM to "calculate chess."**

## What This Project Is

- A **probabilistic human decision model**: `P(move | position, skill, time)`
- A **skill-conditioned human outcome model** (not engine self-play): `P(W/D/L | position, skill, time)`
- A **context-grounding layer** that turns those probabilities into stable, structured payloads for LLM coaching/broadcast (the "LLM Context Bridge")

## What This Project Is Not

- A new superhuman engine
- A replacement for Stockfish/Leela
- A purely "chatty" LLM chess coach (we explicitly avoid hallucination-by-guessing by grounding advice in calibrated probabilities)

## Key Thesis

Modern LLMs are excellent at language but unreliable at **calculation, probability, and domain calibration** under time pressure.

RenaceCHESS is designed to **decouple calculation from explanation**:

- **RenaceCHESS** computes *human-conditioned* probabilities (move distribution, human WDL, difficulty)
- An **LLM** converts those grounded facts into coaching language, narrative, and product UX

This is the "unlock" for modern AI product stacks in chess: **Context Grounding**.

## Data Foundation

The system is grounded in **open, scalable data** from Lichess' public database exports (released under **CC0** and permitted for download/redistribution).

- [Lichess Database](https://database.lichess.org/)

## References

- **Maia** (Microsoft Research) - Skill-conditioned human move prediction
  - [Maia Paper](https://www.cs.toronto.edu/~ashton/pubs/maia-kdd2020.pdf)
  - [Project Maia](https://www.microsoft.com/en-us/research/project/project-maia/)

- **Stockfish WDL** - Engine evaluation contrast layer
  - [UCI & Commands](https://official-stockfish.github.io/docs/stockfish-wiki/UCI-%26-Commands.html)
  - [WDL Model](https://official-stockfish.github.io/docs/stockfish-wiki/Useful-data.html)

