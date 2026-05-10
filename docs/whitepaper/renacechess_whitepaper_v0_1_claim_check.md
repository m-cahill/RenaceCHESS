# RenaceCHESS White Paper — Claim Audit Companion (v0.2)

**Paper draft:** `docs/whitepaper/renacechess_whitepaper_v0_1.md` (content revision **v0.2**)  
**Authoritative discipline:** `docs/whitepaper/research/renacechess_whitepaper_claims_register.md`

Major claims and their audit status:

| Paper claim (paraphrase) | Status | Evidence | Risk | Notes |
|--------------------------|--------|----------|------|-------|
| RenaceCHESS models human move + human W/D/L distributions under skill/time conditioning | **Safe** | `VISION.md`; thesis §3 | Low | Bounded by training/eval regime in v1.0.0 |
| RenaceCHESS is not an engine / Stockfish replacement | **Safe** | `VISION.md`; `RELEASE_NOTES_v1.md`; §2–3 | Low | Repeated as non-goals |
| v1.0.0 is research-grade, not production | **Safe** | `RELEASE_NOTES_v1.md`; §1, §9 | Low | Explicit; §9.4 table |
| **Four modeling tracks** (PoC, LiveM01, Phase E, future) are distinct | **Safe** | Milestone summaries; §5.0 | Low | Clarification only—reduces mis-read |
| LLMs are translators over facts in Phase C design | **Risky but caveated** | M19–M22 summaries; §7 | Med | Designed pipeline; not all deployments |
| System reduces reliance on LLM for chess *calculation* | **Risky but caveated** | Architecture intent; §7 | Med | Does not remove all fabrication risk |
| Universal hallucination prevention | **Removed / avoided** | — | N/A | Draft states non-guarantee |
| Full-vocabulary human move prediction proven | **Removed / avoided** | `RELEASE_NOTES_v1.md` | N/A | §9.4 |
| Proof pack verifies artifact integrity, not model correctness | **Safe** | `proof_pack_v1/README.md`; §8–9 | Low | §9.4 |
| Contract registry + release gates enforce v1 immutability | **Safe** | `CONTRACT_REGISTRY_v1.json`; `M34_summary.md`; `ci.yml` | Low | v2+ evolution explicit |
| 33 frozen v1 contracts in registry | **Safe** | `RELEASE_NOTES_v1.md` | Low | Re-verify if registry count changes |
| Import-linter encodes layering law | **Safe** | `importlinter_contracts.ini`; §4, §10 | Low | — |
| **Governance threat model** prevents *specific dishonesty modes* (drift, leakage rhetoric, greenwashing) | **Risky but caveated** | §8.5; `ci.yml`; registry | Med | **Not** formal security certification; “makes misbehavior noisier” |
| Governance stack makes insider / malicious bypass **impossible** | **Removed / avoided** | §8.5 caveat | N/A | Explicitly disclaimed |
| Engine WDL (Stockfish UCI_ShowWDL) ≠ human WDL | **Safe** | [Stockfish-UCI]; §2 | Low | Contrast only |
| Maia lineage is related work, not superiority claim | **Safe** | [Maia-2020]; §2 | Low | No benchmark comparison asserted |
| M32 “degradation” read as reporting integrity under mismatch | **Risky but caveated** | `RELEASE_NOTES_v1.md`; `M32_summary.md`; §5.4.1 | Med | Not “baseline stronger chess” |
| HDI v1 is reproducible difficulty signal (PoC semantics) | **Safe** | `docs/POC_RELEASE_MANIFEST.md`; §6 | Low | Synthetic eval limits §9 |
| Structural cognition tensors are deterministic grounding | **Safe** | Registry M11; §6 | Low | Not learner UX validation |
| DeterministicStubLLM proves production LLM behavior | **Removed / avoided** | M21 | N/A | §9.4 |
| LiveM01 temperature scaling vs M31 checkpoints | **Safe** | `LiveM01_summary.md`; §5.0–5.2 | Low | — |
| CI overlap-set coverage non-regression | **Safe** | `.github/workflows/ci.yml`; §8, §10 | Low | Not formal verification |
| **Data availability §2.6:** vision cites Lichess CC0; camera-ready needs dumps/splits | **Risky but caveated** | `VISION.md`; [Lichess-DB]; §2.6 | Med | Honest gap-forward; no fake data card |
| v1.0.0 narrative leans on **synthetic** eval + proof pack, not new real-game benchmark | **Safe** | `RELEASE_NOTES_v1.md`; §2.6, §9 | Low | — |
| RediAI inherited guarantees prove RenaceCHESS | **Removed / avoided** | `REDIAI_V3_ASSUMED_GUARANTEES.md` | N/A | §8.6 |
| Commercial / SaaS readiness | **Removed / avoided** | `RELEASE_NOTES_v1.md` | N/A | — |
| “Better than Stockfish” | **Removed / avoided** | — | N/A | — |
| Governance + reproducibility strongest current evidence class | **Safe** | Proof pack, registry, CI; §1.1, §8, §9, §12 | Low | Core thesis |

**Review rule:** Before **v0.3** or external publication, re-validate any sentence that implies **strength**, **deployment**, **formal certification**, or **hallucination elimination** against this table.
