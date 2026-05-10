# RenaceCHESS White Paper — Claims Register

**Purpose:** Conservative classification for drafting. **Architecture/governance** claims may be **Safe** when tied to CI + artifacts. **Model strength / product** claims default **Risky** or **Unsupported** unless narrowly worded.

**Categories:** Safe · Risky · Unsupported / Do Not Claim · Future Work Only

---

| Claim | Category | Recommended wording | Evidence | Risk | Caveat / notes |
|-------|----------|---------------------|----------|------|----------------|
| RenaceCHESS targets **human** move distributions and **human** W/D/L conditioned on skill/time, not engine-optimal play. | **Safe** | “RenaceCHESS implements skill- and time-conditioned **human** policy and outcome heads as design intent; evaluation artifacts are bounded by documented training/eval regimes.” | `VISION.md`; PoC manifest; Phase C–E milestones | Low | Do not imply match to human databases at scale in v1 proof unless stated |
| RenaceCHESS is **not** a chess engine / Stockfish replacement. | **Safe** | “The project explicitly disclaims superhuman engine objectives (`VISION.md`, `RELEASE_NOTES_v1.md`).” | `VISION.md` §2; `RELEASE_NOTES_v1.md` “What This Release Is Not” | Low | — |
| RenaceCHESS v1.0.0 is a **research-grade**, auditable release—not a production product. | **Safe** | “v1.0.0 is positioned as a research system with explicit non-goals (`RELEASE_NOTES_v1.md`).” | `RELEASE_NOTES_v1.md` | Low | — |
| “RenaceCHESS is a **human decision simulator**.” | **Risky** | “RenaceCHESS **models distributions over human moves and outcomes** under declared conditioning; ‘simulator’ is informal—prefer ‘probabilistic model’ or cite equations from `VISION.md`.” | `VISION.md` | Med | “Simulator” invites product/strength readings |
| “RenaceCHESS is a **production-ready** coaching platform.” | **Unsupported / Do Not Claim** | Do not use. | Explicit non-goals: `RELEASE_NOTES_v1.md`; M21/M22 scope excludes live LLM vendor integration | N/A | Coaching CLI + stub LLM are **research surfaces** |
| “RenaceCHESS is **better than Stockfish**.” | **Unsupported / Do Not Claim** | Forbidden comparison for thesis paper unless defining a narrow, honest metric | N/A | N/A | Different objective: human vs optimal |
| “RenaceCHESS **prevents** LLM hallucination.” | **Unsupported / Do Not Claim** | “RenaceCHESS **reduces reliance on LLM chess calculation** by supplying schema-validated facts for translation (M19–M21); **does not guarantee** absence of hallucination in unconstrained deployments.” | `M21_summary.md`; `M19_summary.md` (ADR-COACHING-001) | High | Hallucination detection in harness ≠ production safety proof |
| “RenaceCHESS **constrains** LLM coaching to structured facts.” | **Risky** (narrow) **Safe** | **Safe** in-repo: “Phase C implements **facts-only inputs** (`AdviceFacts`, `EloBucketDeltaFacts`) and evaluation hooks for drafts (`M21`).” **Risky** if implying all deployments: add “when the integration supplies only these artifacts.” | M19–M22 summaries; schemas in registry | Med | Live LLM integrations out of scope for M21 |
| “RenaceCHESS proves **full-vocabulary** human move prediction.” | **Unsupported / Do Not Claim** | “v1 training used **`moveVocabSize` 4096** with **narrow effective training regime**; eval set is broader—degradation is expected and reported (`RELEASE_NOTES_v1.md`, `proof_pack_v1/README.md`).” | `RELEASE_NOTES_v1.md` Known Limitations; proof pack README | N/A | Align wording with lock + release notes, not colloquial “8 moves” alone |
| “RenaceCHESS demonstrates an **audit-governed AI-native research architecture**.” | **Risky** → **Safe** if scoped | **Safe:** “RenaceCHESS v1 pairs **contract registry hashing**, **proof-pack verification**, and **CI release gates** (`M34`, workflows).” **Risky:** “AI-native” is buzzword—define or drop. | `M34_summary.md`; `RELEASE_NOTES_v1.md`; `.github/workflows/ci.yml` | Low–Med | Strongest defensible story is **governance + reproducibility** |
| Human Difficulty Index (HDI v1) exists and is **deterministic from position + model signals** (PoC scope). | **Safe** (PoC) / **Risky** (extend) | Cite `docs/POC_RELEASE_MANIFEST.md` semantics freeze; Phase E may extend eval—tie to milestone | PoC manifest; M07 lineage | Low in PoC | v1 proof uses synthetic eval—strength claims separate |
| **Structural cognition** features (M11) enrich Context Bridge v2. | **Safe** | “M11 adds deterministic structural feature tensors and Context Bridge v2 (`CONTRACT_REGISTRY_v1.json`).” | Registry entries `M11`; PoC manifest | Low | Does not prove human interpretability quality |
| **Proof pack** enables third-party **artifact integrity** checks without trusting source tree narrative alone. | **Safe** | As stated in `proof_pack_v1/README.md` + verifier | `verify_proof_pack`; README | Low | Does not prove model correctness |
| **Contract registry** enforces immutability of **v1 schemas** in CI. | **Safe** | “`release-contract-freeze` + hashed registry (`M34`).” | `ci.yml`; `contracts/CONTRACT_REGISTRY_v1.json` | Low | v2+ evolution is explicit future path |
| **Overlap-set coverage non-regression** guards coverage on shared file sets. | **Safe** | Describe as implemented in CI test job | `ci.yml` (Compare overlap-set coverage) | Low | XML baseline artifact—describe briefly, don’t oversell as formal verification |
| RenaceCHESS uses **Lichess CC0** data stance in vision. | **Risky** (legal) **Safe** (intent) | “Public vision cites Lichess database exports as **CC0** (`VISION.md`); confirm packaging/compliance for any paper data section.” | `VISION.md`; https://database.lichess.org/ | Med | Paper should cite Lichess **license page** directly |
| **LiveM01** skill conditioning via temperature scaling. | **Safe** (scoped) | “LiveM01 adjusts baseline policy spread by skill id (**research milestone**).” | `docs/milestones/Live/LiveM01/LiveM01_summary.md` | Low | Distinct from M31 trained checkpoint story—don’t conflate |
| **Personality** framework is bounded/modulated per Phase B contracts. | **Risky** (detail) | Summarize only with `PERSONALITY_SAFETY_CONTRACT_v1.md` + import boundaries | `importlinter_contracts.ini`; contract docs | Med | Omit depth unless paper has space |

---

## Prompt examples (explicit user list)

| Example phrasing | Category | Notes |
|------------------|----------|--------|
| “Human decision simulator” | Risky | Prefer probabilistic wording + citations |
| “Production-ready coaching platform” | Unsupported | Contradicts release notes |
| “Better than Stockfish” | Unsupported | Different problem |
| “Prevents hallucination” | Unsupported | Mitigates reliance on LLM chess arithmetic; no full prevention proof |
| “Constrains LLM coaching to structured facts” | Risky→Safe narrow | True for **designed Phase C pipeline** |
| “Full-vocabulary human move prediction” | Unsupported | v1 explicitly **not** full vocab / narrow regime |
| “Audit-governed AI-native architecture” | Safe if **operationalized** to registry/proof pack/CI | Define terms |

---

**Drafting rule:** If a sentence appears in **Unsupported**, remove or rewrite using **Recommended wording** before external publication.
