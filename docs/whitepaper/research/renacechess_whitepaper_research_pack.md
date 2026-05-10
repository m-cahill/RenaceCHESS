# RenaceCHESS White Paper — Research Pack (Memo)

**Status:** Research-only input for a future white paper — **not** the paper itself.  
**Date:** 2026-05-10 (branch `whitepaper-research-pack`)  
**Working thesis (from charter):** RenaceCHESS demonstrates that chess analysis can be reframed from engine-optimal move selection to **reproducible, skill-conditioned human decision modeling**, combining human move distributions, human W/D/L estimates, difficulty signals, structural cognition features, **immutable contracts**, and **facts-first** LLM translation—under **explicit** non-goals and limitations.

**Companion deliverables:** `renacechess_whitepaper_claims_register.md`, `renacechess_whitepaper_sources.md`, `renacechess_whitepaper_outline.md`, `renacechess_whitepaper_open_questions.md`.

---

## Executive summary

RenaceCHESS is architected as a **governed research system** for **human-centered chess signals**: learned and/or baseline **policy** (move distribution), **outcome** head (W/D/L), **Human Difficulty Index (HDI)**, **structural cognition** tensors (M11 / Context Bridge v2), and a **coaching pipeline** where LLMs are **translators** over schema-validated facts (M19–M22)—not primary chess calculators (`VISION.md`; `M21_summary.md`).

The **v1.0.0** story (M30–M34) is intentionally **research-grade**: it hardens **reproducibility and honesty** (frozen synthetic eval at scale, training lock, post-train eval reporting **degradation**, external proof pack, contract registry + CI release gates) while **refusing** claims of playing strength, production readiness, or full-move-vocabulary performance (`RELEASE_NOTES_v1.md`; `proof_pack_v1/README.md`).

**Differentiation for a paper:** strongest **evidence class** today is **architecture + governance** (contracts, import-linter boundaries, CI jobs including overlap-set coverage and release freezes, proof-pack verification). **Model-performance** claims must stay **narrow** and **linked** to the documented narrow training regime and synthetic eval (`RELEASE_NOTES_v1.md` Known Limitations).

---

## 1. Core thesis (with contrasts)

### 1.1 Thesis in-repo

- **Human move policy:** \(P(\text{move}\mid\text{position},\text{skill},\text{time})\) (`VISION.md`).
- **Human outcome model:** \(P(W/D/L\mid\cdots)\) — “not engine self-play” (`VISION.md`).
- **Context Bridge:** structured payloads for coaching/broadcast so LLMs need not “calculate chess” (`VISION.md`; contracts in `CONTRACT_REGISTRY_v1.json`).

### 1.2 Versus a chess engine / Stockfish wrapper

Engines optimize **strength** and **best move**; RenaceCHESS disclaims superhuman engine goals (`VISION.md`; `RELEASE_NOTES_v1.md`). **Stockfish `UCI_ShowWDL`** exposes **engine** WDL derived from engine evaluation (cite official docs)—orthogonal to **human** WDL modeling in RenaceCHESS.

### 1.3 Versus a “normal chess coach”

Traditional coaching mixes heuristics + engine analysis. RenaceCHESS targets **probabilistic human modeling** + **calibration-minded metrics** (Phase D contracts such as `calibration_metrics` / `calibration_delta` in registry) with **explicit** evaluation limits.

### 1.4 Versus a generic LLM chess assistant

`VISION.md` and `M21_summary.md` emphasize **decoupling**: RenaceCHESS computes **grounded numeric/structured facts**; the LLM **verbalizes**. Generic assistants often hallucinate tactics; RenaceCHESS’s Phase C design **reduces dependence** on LLM chess calculation—it does **not** prove hallucination elimination (`claims_register`).

### 1.5 Versus a normal ML research repo

Unusually heavy **schema-first** artifact spine: **33** frozen v1 contracts in `CONTRACT_REGISTRY_v1.json`, **import-linter** architectural law (`importlinter_contracts.ini`), **proof pack** third-party verification (`proof_pack_v1/`), and **release-blocking** CI gates for dependencies/contracts/proof pack (`RELEASE_NOTES_v1.md`; `M34_summary.md`; `.github/workflows/ci.yml`).

### 1.6 Related scientific lineage (external, brief)

**Maia / Microsoft Research** popularized **human move prediction** from large human game corpora—useful **related work** and contrast point (see `renacechess_whitepaper_sources.md`). RenaceCHESS should cite Maia for **problem family**, not imply equivalence of datasets/models.

---

## 2. Technical capabilities today (catalog)

For each: **description · location · milestone · proves · does not prove**.

| Capability | Description | Where | Milestone | Proves | Does **not** prove |
|------------|-------------|-------|-----------|--------|--------------------|
| Skill-conditioned human policy (baseline) | Temperature scaling over masked softmax by skill key | e.g. `src/renacechess/models/baseline_v1.py` (per `LiveM01_summary.md`) | **LiveM01** | Deterministic skill differentiation on **baseline** architecture | Trained policy strength; human fidelity at scale |
| Learned human policy + outcome heads (PoC) | Trainable heads, frozen eval discipline | PoC summaries M08–M09; manifests | **M08–M09** | **Learnability + calibration discipline** in PoC scope | Final competitive human prediction |
| HDI v1 | Human difficulty index definition | Frozen in PoC semantics | **M07** | Defined, reproducible difficulty signal in PoC framing | Real-world coaching efficacy |
| Structural cognition | `PerPieceFeaturesV1`, `SquareMapFeaturesV1`, Context Bridge v2 | Schemas in registry | **M11** | Deterministic structural tensors for grounding | Human-interpretable “explanations” quality |
| Context Bridge | Payload for LLM / consumers | `context_bridge*.schema.json` | **M04** / **M11** | Stable JSON contracts | Narrative quality |
| AdviceFacts | Facts-only single-bucket coaching substrate | `advice_facts` schema; `coaching/` | **M19** | **Groundable fact assembly** w/ import boundary | End-user coaching quality |
| EloBucketDeltaFacts | Cross-bucket statistical deltas | `elo_bucket_deltas` schema | **M20** | **Non-prose** comparative facts | Causal skill claims |
| LLM translation harness | `DeterministicStubLLM`, draft + evaluation contracts | `coaching` module | **M21** | **Testable** translation + hallucination checks **in harness** | Production LLM safety |
| Coaching CLI | `renacechess coach` surface | CLI + `coaching_surface` schema | **M22** | Governed end-to-end path **without network** | Product deployment |
| Personality modulation | Bounded modulation (downstream only) | `personality/`; linter forbids core imports | Phase **B** (e.g. M15–M18) | Auditable personality variants | Psychological realism |
| Frozen eval v2 | 10k **synthetic** stratified set | `data/frozen_eval_v2/`; CI job | **M30** | Deterministic **relative** eval / calibration stability tooling | Real-game coverage |
| Training run lock + report | Config lock + run reporting | `artifacts/`; proof pack copies | **M31** | **Executed** training with governance artifacts | Strong policy |
| Post-train eval | Baseline vs trained metrics | `post_train_eval` artifacts | **M32** | Honest **infrastructure** for comparing models | High accuracy |
| Proof pack | External verifier bundle | `proof_pack_v1/` | **M33** | Third-party integrity of declared artifacts | Model correctness |
| Contract registry + CI gates | Hash inventory + freeze jobs | `contracts/`; `ci.yml` | **M34** | **v1 immutability** enforcement | Future v2 semantics |
| Overlap-set coverage CI | Non-regression on intersecting test file sets | `ci.yml` `Compare overlap-set coverage` | **M10** lineage | Prevents silent coverage loss on shared subsets | Formal verification |
| Deterministic LLM stub | CI-safe “LLM” | `M21_summary.md` | **M21** | Deterministic, offline tests | Provider realism |

---

## 3. What v1.0.0 proved (honest summary)

**Source of truth:** `RELEASE_NOTES_v1.md` + `proof_pack_v1/README.md` + Phase E milestone summaries (**M30–M34**).

- **M30:** 10k **synthetic** frozen eval v2; stratified; hash-verified; **relative** evaluation intent.
- **M31:** Full training **infrastructure** executed with locks/reports; **`moveVocabSize`: 4096** with **narrow effective training regime** (often described alongside eight common opening moves in prose—**authoritative numeric/config** is the training lock + release notes).
- **M32:** Post-train eval **reports degradation** vs baseline under vocab/eval mismatch—framed as **expected**, validating reporting integrity.
- **M33:** Self-contained **proof pack** w/ README listing **does NOT prove** strength/full vocab.
- **M34:** **Contract registry** + **three release gates** (dependencies, contracts, proof pack).

**Explicit non-claims (`RELEASE_NOTES_v1.md`):** not production; not commercial product; not superhuman engine; not full-vocab performance; playing strength not established.

---

## 4. Novel architectural patterns (for paper §11)

| Pattern | Where | Unusual? | Why it matters | Highlight? |
|---------|-------|----------|----------------|----------|
| **Architecture-as-test-failure** | `importlinter_contracts.ini` + boundary tests | Yes—layering as **law** not convention | Prevents “helpful” coupling that breaks audit | **Yes** |
| **Hash-chain / artifact provenance** | Proof pack manifest; frozen eval manifests | Common in mature infra; rare in academic ML repos | External audit | **Yes** |
| **Contract registry = immutability proof** | `CONTRACT_REGISTRY_v1.json` + `release-contract-freeze` | Uncommon at this granularity for **research** repos | Makes drift costly | **Yes** |
| **Overlap-set coverage non-regression** | `ci.yml` | Niche but strong governance | Prevents coverage gaming | **Maybe** (specialist readers) |
| **CI as authority surface** | Many validation jobs in `ci.yml` | Emerging norm; here **extensive** | “Truth” operationalized | **Yes** (careful: CI ≠ proof of AI) |
| **Governance-as-code** | Registry + linter + workflows | Aligns with OSS maturity models | Trust argument | **Yes** |
| **Intentional constraint layers** | Phases in `postpocphasemap.md` | Yes—program phases w/ exit criteria | Scope control | **Maybe** |
| **Deterministic LLM stub for CI** | `M21_summary.md` | Yes | Makes LLM path testable offline | **Yes** |

---

## 5. External research summary (short bibliography)

See **`renacechess_whitepaper_sources.md`** for URLs and section mapping. **Core set:** Maia (McIlroy-Young et al.) + MSR pages; Lichess database CC0; Stockfish UCI_ShowWDL docs; Guo et al. calibration; Ji et al. hallucination survey; Pineau et al. reproducibility report.

---

## 6. Claims posture (summary)

Full classified register: **`renacechess_whitepaper_claims_register.md`**.

**Rule of thumb for drafting:**

- **Safe:** anything directly mirrored in `RELEASE_NOTES_v1.md`, proof pack README, registry, or CI with **narrow** wording.
- **Risky:** “simulator”, “prevents hallucination”, unconstrained “production”.
- **Unsupported:** Stockfish comparisons, full-vocab human modeling, commercial readiness.

---

## 7. Recommended white paper outline

**See** `renacechess_whitepaper_outline.md` (full section goals, evidence, citations, figure list).

---

## 8. Recommended figures / tables (generation timing)

| Title | Purpose | Source data | Format | When |
|-------|---------|------------|--------|------|
| System pipeline | Human signals → bridge → LLM | `VISION.md`, registry | Block diagram | **Later** (drafting) |
| Layer / dependency boundaries | Contracts vs models vs coaching | `importlinter_contracts.ini` | Box-arrow | **Later** |
| Hash-chain / proof-pack flow | Third-party verify | `proof_pack_v1/README.md` | Flowchart | **Later** |
| LLM-as-translator | Facts → draft → eval | M21 | Sequence | **Later** |
| Engine vs LLM coach vs RenaceCHESS | Positioning | This memo + `VISION.md` | **Table** | **Later** (static markdown OK) |
| Milestone timeline M30–M34 (+ Phase G pointer) | Release narrative | `renacechess.md`, release notes | **Table** | **Later** |
| Capability catalog | §2 of this memo | Milestones | **Table** | **Can derive now** from memo |
| Safe / risky / unsupported | Claims discipline | `claims_register.md` | **Table** | **Now** (copy register) |
| Proof-pack verification flow | Ops / audit appendix | `RELEASE_NOTES_v1.md` | Flowchart | **Later** |
| Evaluation limitations | Honesty | `RELEASE_NOTES_v1.md` | **Table** | **Later** |

**Now vs later:** Textual **tables** can be lifted during drafting; **diagrams** after outline freeze.

---

## 9. Internal evidence gaps recorded

- Root-level **`v1novelanalysis.md`**, **`v1fullaudit.md`**, **`v1capabilities.md`**: **not found** — listed in sources gap log.
- **`docs/renacechess_fullaudit.md`**: useful narrative snapshot but **untracked** at authoring time — verify git tracking before citing as repository evidence.

---

**End of research pack.**
