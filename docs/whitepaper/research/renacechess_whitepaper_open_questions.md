# RenaceCHESS White Paper — Open Questions & Evidence Gaps

**Purpose:** Track unresolved items **before** camera-ready drafting. Answering these improves paper strength without expanding claims prematurely.

---

## A. Missing or relocated anchor documents

| Item | Question | Suggested follow-up |
|------|----------|---------------------|
| `v1novelanalysis.md` (expected root) | Was this renamed, split, or never committed? | Locate or author a **short internal** “novelty claims” memo **or** drop the filename from governance |
| `v1fullaudit.md` (expected root) | Same | If intent was full audit, consider curating a **tracked** summary under `docs/audit/` with explicit scope |
| `v1capabilities.md` (expected root) | Same | Could be satisfied by extracting §2 of `renacechess_whitepaper_research_pack.md` into a slim `docs/` capability sheet |
| `docs/renacechess_fullaudit.md` | Untracked at research-pack time—legitimate citation? | **Commit** (if desired) or **replace** with tracked Phase audits |

---

## B. Model / evaluation science

| Question | Why it matters |
|----------|----------------|
| What is the **quantitative human baseline** (if any) comparable to Maia-style metrics on a **declared** eval slice? | Related work section needs honest apples-to-oranges discussion |
| Will the paper include **a fresh** non-synthetic eval slice (post–frozen eval v2)? | Synthetic eval v2 is intentional but limits **external** strength narrative |
| How will authors present **`moveVocabSize` 4096** vs colloquial “eight opening lines”? | Single authoritative sentence + pointer to `TrainingConfigLockV1` / proof pack |
| Is **LiveM01** baseline conditioning in scope for the paper’s experiments section vs **M31** checkpoint? | Avoid reader confusion between milestones |

---

## C. LLM / coaching

| Question | Why it matters |
|----------|----------------|
| Is there **any** measured result with a **non-stub** LLM provider retained for publication? | M21 explicitly scoped stub + offline; claims about “real” coaching need data |
| How will hallucination be **defined** in the paper (NLG survey categories vs chess-specific checks)? | Align with `M21` evaluation semantics |
| Translation prompts: cite **`COACHING_TRANSLATION_PROMPT_v1.md`** as frozen artifact—public? | Confirm licensing / redaction for paper appendix |

---

## D. Governance / related work boundaries

| Question | Why it matters |
|----------|----------------|
| How much **RediAI / R2L** pedigree to cite vs RenaceCHESS-native proof? | `REDIAI_V3_ASSUMED_GUARANTEES.md` references **external** Phase XV artifacts not in this repo—avoid over-claim |
| Any plan for **SLSA / supply-chain** formalism vs informal “hash + CI”? | Optional one-sentence positioning |
| Phase **G** (M35–M40) in paper body or appendix only? | Impacts length; M40 is governance RC—may be appendix |

---

## E. Legal / data

| Question | Why it matters |
|----------|----------------|
| Paper’s **data availability** statement: which **Lichess** dumps / filters / splits? | `VISION.md` states CC0 stance—paper should cite **primary** Lichess license page |
| Trademark / naming: “RenaceCHESS” vs product | Editorial |

---

## F. Visualization / reproduction package

| Question | Why it matters |
|----------|----------------|
| Will the paper ship a **minimal reproduction container** or only cite proof-pack commands? | Affects reviewer experience |
| Figure ownership / tool (TikZ, draw.io, Excalidraw) | Logistics |

---

## G. Resolved at research-pack time (for auditors)

- **v1.0.0 boundaries:** `RELEASE_NOTES_v1.md` remains authoritative for research vs production.
- **Proof pack scope:** `proof_pack_v1/README.md` states provable vs non-provable claims.
- **CI role:** `.github/workflows/ci.yml` documents operational gates—not a substitute for formal methods.

---

**When closing this file:** move answered rows to a “Closed” subsection or delete—keep the file short for future milestones.
