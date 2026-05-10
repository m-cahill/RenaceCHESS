# RenaceCHESS White Paper — Source Index

**Purpose:** Citation-ready index of **internal** (repo) and **external** sources for the future white paper.  
**Standard:** Prefer primary URLs; record **path substitutions** where expected filenames differ or are missing.

---

## A. Internal sources (repository)

| Source | Type | URL / Path | Key relevance | Suggested section(s) | Notes |
|--------|------|------------|---------------|----------------------|--------|
| Project vision & non-goals | Doc | `VISION.md` | Human move + WDL + context-bridge thesis; explicit “not an engine” | §2–4, §6 | Canonical product narrative |
| Milestones & governance SoT | Doc | `renacechess.md` | Milestone traceability (M00–M40), Phase G public readiness | §5, §10, timeline | Large; cite specific milestone rows/sections |
| v1.0.0 release framing | Doc | `RELEASE_NOTES_v1.md` | Research-grade vs production; M30–M34; limitations; CI release gates | §9–10, §6 | **Authoritative** for “what v1 proved / did not prove” |
| PoC lock envelope | Doc | `docs/POC_RELEASE_MANIFEST.md` | M00–M11 scope, frozen schemas, determinism claims for PoC | §5, §10 “PoC baseline” | Semantic lock vs `main` evolution |
| Post-PoC roadmap | Doc | `docs/postpocphasemap.md` | Phases A–E definitions, exit criteria | §5, timeline | Program-level phase construct |
| Post-PoC anchor | Doc | `docs/postpocanchor.md` | Consolidated “what’s locked / what’s next”; coaching grounding | §4, §8 | Narrative bridge for new readers |
| RediAI assumed guarantees | Doc | `docs/governance/REDIAI_V3_ASSUMED_GUARANTEES.md` | Inherited platform posture (determinism, schema validation, CI truthfulness) | §9 (related work / pedigree) **or** brief architecture footnote | **External R2L artifacts** referenced inside are not in this repo; do not over-cite as RenaceCHESS-proven |
| **Expected `v1novelanalysis.md`** | — | *Not found in repo* | — | — | **Gap:** document anticipated name `v1novelanalysis.md` (root). No tracked substitute located. |
| **Expected `v1fullaudit.md`** | — | *Not found in repo* | — | — | **Gap:** document anticipated name `v1fullaudit.md` (root). |
| **Expected `v1capabilities.md`** | — | *Not found in repo* | — | — | **Gap:** document anticipated name `v1capabilities.md` (root). |
| Full codebase audit (local) | Audit | `docs/renacechess_fullaudit.md` | Architecture/CI scorecard snapshot | Optional §9 | **Untracked** in git at research-pack authoring time — **do not treat as repo-evidence** until committed; verify before formal citation |
| Contract registry | Artifact | `contracts/CONTRACT_REGISTRY_v1.json` | Immutable v1 schema inventory + hashes + milestone provenance | §5–6, §9 | Pair with `src/renacechess/contracts/registry.py` validation |
| Proof pack | Artifact | `proof_pack_v1/` + `proof_pack_v1/README.md` | External verification bundle; explicit non-claims | §9–10 | Manifest hash in `RELEASE_NOTES_v1.md` |
| Import boundaries | Config | `importlinter_contracts.ini` | Contracts / personality / coaching isolation | §5, §11 | Governance-as-code |
| CI authority surface | Config | `.github/workflows/ci.yml` | Jobs: security (gitleaks), lint, types, tests, overlap coverage, eval validations, **release-* gates**, proof-pack job | §9–11 | Overlap-set coverage non-regression embedded in test job |
| M30 summary | Milestone | `docs/milestones/PhaseE/M30/M30_summary.md` | Frozen eval v2 (10k synthetic) | §7, §10 | Synthetic = relative metrics only |
| M31 summary | Milestone | `docs/milestones/PhaseE/M31/M31_summary.md` | Training lock + run | §7, §10 | Distinguish infrastructure vs strength |
| M32 summary | Milestone | `docs/milestones/PhaseE/M32/M32_summary.md` | Post-train eval; honest degradation | §7, §10 | M32 text uses “8 moves” shorthand in places; **`RELEASE_NOTES_v1` + `TrainingConfigLockV1` / proof pack** authoritative on **`moveVocabSize`: 4096** and narrow **effective** regime |
| M33 summary | Milestone | `docs/milestones/PhaseE/M33/M33_summary.md` | External proof pack | §9 | |
| M34 summary | Milestone | `docs/milestones/PhaseE/M34/M34_summary.md` | Release lock + registry + CI gates | §9 | |
| M19 summary | Milestone | `docs/milestones/PhaseC/M19/M19_summary.md` | AdviceFacts / ADR-COACHING-001 | §8 | |
| M20 summary | Milestone | `docs/milestones/PhaseC/M20/M20_summary.md` | EloBucketDeltaFacts | §8 | |
| M21 summary | Milestone | `docs/milestones/PhaseC/M21/M21_summary.md` | LLM harness; DeterministicStubLLM; evaluation | §8, §11 | |
| M22 summary | Milestone | `docs/milestones/PhaseC/M22/M22_summary.md` | `renacechess coach` CLI; CoachingSurfaceV1 | §8 | |
| LiveM01 summary | Milestone | `docs/milestones/Live/LiveM01/LiveM01_summary.md` | Skill-conditioned temperature scaling on baseline | §7 | Research-side; distinct from Phase E trained run |
| Phase E closeout | Phase | `docs/phases/PhaseE_closeout.md` | Phase E narrative | §10 | |
| Phase G docs | Phase | `docs/phases/PhaseG_closeout.md`, `docs/milestones/PhaseG/M40/*` | Public readiness; M40 RC review | §9–10 (governance) | M40 = review-only; no release action |

---

## B. External sources (high-signal bibliography)

| Source | Type | URL | Key relevance | Suggested section(s) | Notes |
|--------|------|-----|---------------|----------------------|--------|
| **Maia: Aligning Superhuman AI with Human Behavior (Chess)** | Paper / MS Research | https://www.microsoft.com/en-us/research/publication/aligning-superhuman-ai-with-human-behavior-chess-as-a-model-system/ · arXiv: https://arxiv.org/abs/2006.01855 | Foundational **human move prediction** / human-aligned chess AI; closest academic framing | §3 Related work, §4 contrast with engine | Pair with https://www.maiachess.com/ for project context |
| **Project Maia overview** | Web | https://www.microsoft.com/en-us/research/project/project-maia/ | Institutional framing of “predict humans, not optimal play” | §3–4 | |
| **The** human side of AI for chess **(MSR blog)** | Blog | https://www.microsoft.com/en-us/research/blog/the-human-side-of-ai-for-chess/ | Accessible motivation | §1–3 | |
| **Lichess open database** | Data / license | https://database.lichess.org/ | **CC0** public game exports — aligns with `VISION.md` data stance | §3, Data availability | Also: https://github.com/lichess-org/database (README describes dataset; repo AGPL — distinguish **data** CC0 vs **code** license) |
| **Stockfish UCI & commands** | Engine docs | https://official-stockfish.github.io/docs/stockfish-wiki/UCI-%26-Commands.html | **`UCI_ShowWDL`** — engine WDL vs **human** WDL in RenaceCHESS | §3 “engine vs human substrate” | Contrast only; RenaceCHESS is not Stockfish |
| **On Calibration of Modern Neural Networks** (Guo et al., ICML 2017) | Paper | https://arxiv.org/abs/1706.04599 | ECE / calibration discourse; **temperature scaling** lineage | §7 HDI / calibration, §6 | RenaceCHESS records ECE/Brier/NLL in contracts (`calibration_metrics`); cite for *general* calibration theory |
| **Survey of Hallucination in NLG** (Ji et al., ACM Computing Surveys / arXiv:2202.03629) | Survey | https://arxiv.org/abs/2202.03629 | Grounded coaching motivation; LLM failure modes | §8 | Use to justify **facts-first** design *directionally* — not as proof RenaceCHESS solves hallucination in production |
| **Improving reproducibility in ML research** (NeurIPS 2019 reproducibility report; JMLR) | Report | http://jmlr.org/papers/v22/20-303.html | Checklist / reproducibility norms | §9 | Aligns with proof-pack + CI narrative **at process level** |

### Optional (use sparingly)

| Source | Type | URL | Key relevance | Suggested section(s) | Notes |
|--------|------|-----|---------------|----------------------|--------|
| Maia-2 (unified human-AI chess) | Paper | https://arxiv.org/abs/2409.20553 | Newer related work | §3 Related work | Cite only if paper compares architectural patterns |
| OpenSSF / SLSA | Standards | https://slsa.dev/ | Software supply-chain / provenance vocabulary | §9 *optional* one sentence | RenaceCHESS uses hashes + CI; not a SLSA certification claim |

---

## C. Path alias / gap log (for editors)

| Expected anchor (prompt) | Resolution |
|--------------------------|------------|
| `REDIAI_V3_ASSUMED_GUARANTEES.md` (root) | **Actual:** `docs/governance/REDIAI_V3_ASSUMED_GUARANTEES.md` |
| `POC_RELEASE_MANIFEST.md` (root) | **Actual:** `docs/POC_RELEASE_MANIFEST.md` |
| `postpocphasemap.md` / `postpocanchor.md` (root) | **Actual:** `docs/postpocphasemap.md`, `docs/postpocanchor.md` |
| `v1novelanalysis.md`, `v1fullaudit.md`, `v1capabilities.md` | **Missing** — gaps recorded; do not invent content |

---

**Maintainer note:** Re-run `git ls-files` on any `docs/*audit*` before citing in camera-ready paper.
