# RenaceCHESS White Paper v0.1 — Claim Audit Companion

**Paper draft:** `docs/whitepaper/renacechess_whitepaper_v0_1.md`  
**Authoritative discipline:** `docs/whitepaper/research/renacechess_whitepaper_claims_register.md`

Major claims from the v0.1 draft and their audit status:

| Paper claim (paraphrase) | Status | Evidence | Risk | Notes |
|--------------------------|--------|----------|------|-------|
| RenaceCHESS models human move + human W/D/L distributions under skill/time conditioning | **Safe** | `VISION.md`; thesis §3 | Low | Bounded by training/eval regime in v1.0.0 |
| RenaceCHESS is not an engine / Stockfish replacement | **Safe** | `VISION.md`; `RELEASE_NOTES_v1.md`; §2–3 | Low | Repeated as non-goals |
| v1.0.0 is research-grade, not production | **Safe** | `RELEASE_NOTES_v1.md`; §1, §9 | Low | Explicit |
| LLMs are translators over facts in Phase C design | **Risky but caveated** | M19–M22 summaries; §7 | Med | Scoped to **designed** pipeline; not all deployments |
| System reduces reliance on LLM for chess *calculation* | **Risky but caveated** | Architecture intent; §7 | Med | Does not remove all fabrication risk |
| Universal hallucination prevention | **Removed / avoided** | — | N/A | Draft states non-guarantee; Ji survey for motivation only |
| Full-vocabulary human move prediction proven | **Removed / avoided** | `RELEASE_NOTES_v1.md` Known Limitations | N/A | Draft uses moveVocabSize 4096 + narrow effective regime |
| Proof pack verifies artifact integrity, not model correctness | **Safe** | `proof_pack_v1/README.md`; §8–9 | Low | Explicit |
| Contract registry + release gates enforce v1 immutability | **Safe** | `contracts/CONTRACT_REGISTRY_v1.json`; `M34_summary.md`; `ci.yml` | Low | v2+ evolution explicit |
| 33 frozen v1 contracts in registry | **Safe** | `RELEASE_NOTES_v1.md` | Low | Count from release notes |
| Import-linter encodes layering law | **Safe** | `importlinter_contracts.ini`; §4, §10 | Low | — |
| Engine WDL (Stockfish UCI_ShowWDL) ≠ human WDL | **Safe** | [Stockfish-UCI]; §2 | Low | Contrast only |
| Maia lineage is related work, not superiority claim | **Safe** | [Maia-2020]; §2 | Low | No benchmark comparison asserted |
| M32 “degradation” read as reporting integrity under mismatch | **Risky but caveated** | `RELEASE_NOTES_v1.md`; `M32_summary.md`; §5.4.1 | Med | Careful wording to avoid “baseline stronger chess” |
| HDI v1 is reproducible difficulty signal (PoC semantics) | **Safe** | `docs/POC_RELEASE_MANIFEST.md`; §6 | Low | Synthetic eval limits §9 |
| Structural cognition tensors are deterministic grounding | **Safe** | `CONTRACT_REGISTRY_v1.json` M11; §6 | Low | Not learner UX validation |
| DeterministicStubLLM proves production LLM behavior | **Removed / avoided** | M21 | N/A | Draft: CI harness only |
| LiveM01 temperature scaling vs M31 checkpoints | **Safe** | `LiveM01_summary.md`; §5.2 | Low | Conflation explicitly warned |
| CI overlap-set coverage non-regression | **Safe** | `.github/workflows/ci.yml`; §8, §10 | Low | Not formal verification |
| Lichess data is CC0 for exports (vision-level) | **Risky but caveated** | `VISION.md`; [Lichess-DB] | Med | Paper should cite primary license text for any empirical section |
| RediAI inherited guarantees prove RenaceCHESS | **Removed / avoided** | `REDIAI_V3_ASSUMED_GUARANTEES.md` | N/A | Draft footnotes external lineage; repo CI/artifacts primary |
| Commercial / SaaS readiness | **Removed / avoided** | `RELEASE_NOTES_v1.md` | N/A | — |
| “Better than Stockfish” | **Removed / avoided** | — | N/A | — |
| Governance + reproducibility strongest current evidence class | **Safe** | Proof pack, registry, release notes, CI; §1.1, §8–9, §12 | Low | Core honest thesis |

**Review rule:** Before v0.2 or external publication, re-validate any sentence that implies **strength**, **deployment**, or **hallucination elimination** against this table.
