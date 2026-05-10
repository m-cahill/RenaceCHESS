# RenaceCHESS — Proposed White Paper Structure

**Working title:** *RenaceCHESS: Audit-Governed Human Chess Cognition and Grounded Coaching Substrate*

**Subtitle (optional):** *Skill-conditioned move and outcome modeling with immutable contracts, proof packs, and facts-first LLM translation*

**Target length:** 6–10 pages core + appendices  
**Audience:** ML + chess-informatics + governance-minded engineers; journal / arXiv-style or strong industry white paper

---

## Title page metadata (draft)

- **Keywords:** human move prediction, calibration, chess cognition, LLM grounding, reproducibility, JSON-schema contracts
- **Data:** Lichess CC0 exports (cite database.lichess.org); internal synthetic frozen eval for v1 proof (cite `M30`, `RELEASE_NOTES_v1.md`)
- **Code & artifacts:** Public repo; proof pack verification commands in `RELEASE_NOTES_v1.md`

---

## Section-by-section plan

### 1. Abstract

| Field | Content |
|-------|---------|
| **Purpose** | One-paragraph positioning: human-behavior modeling + governance + grounded coaching |
| **Key arguments** | Not an engine; v1 is research-grade; contracts + proof pack + CI |
| **Repo evidence** | `VISION.md`; `RELEASE_NOTES_v1.md` opening sections |
| **External citations** | Maia (human prediction); Ji et al. (hallucination survey) **one line**; Guo et al. **one line** optional |
| **Figures** | None |

---

### 2. Introduction

| Field | Content |
|-------|---------|
| **Purpose** | Motivate engine-first analysis gap; LLM limitations on chess calculation |
| **Key arguments** | Decouple “compute human probabilities” from “generate language” |
| **Repo evidence** | `VISION.md` §3 thesis |
| **External citations** | MSR Maia blog; optionally Stockfish UCI_ShowWDL **contrast** |
| **Figures** | **Fig 1** (optional): high-level pipeline sketch |

---

### 3. Problem: engine-first chess analysis is not human cognition

| Field | Content |
|-------|---------|
| **Purpose** | Distinguish optimal play engines from human-behavior models |
| **Key arguments** | Engines answer best move; RenaceCHESS answers human *distribution* |
| **Repo evidence** | `VISION.md` §2; PoC manifest §2 |
| **External citations** | Maia paper; Stockfish docs (WDL is engine WDL, not human) |
| **Figures** | **Table 1** engine vs human-model vs LLM coach (see research pack) |

---

### 4. RenaceCHESS thesis

| Field | Content |
|-------|---------|
| **Purpose** | Formal problem statement: \(P(\text{move}\mid\text{pos},skill,time)\), \(P(W/D/L\mid \cdots)\) |
| **Key arguments** | Context Bridge for LLM; personalities as downstream (Phase B) |
| **Repo evidence** | `VISION.md` equations; `postpocanchor` “human triad” |
| **External citations** | Light—keep repo-primary |
| **Figures** | **Fig 2** equation + Context Bridge box |

---

### 5. System architecture

| Field | Content |
|-------|---------|
| **Purpose** | Modules: dataset/ingest, models, eval, features, coaching, contracts |
| **Key arguments** | Import-linter **enforces** layering (`importlinter_contracts.ini`) |
| **Repo evidence** | Registry (`CONTRACT_REGISTRY_v1.json`); REDIAI assumptions doc **as posture** |
| **External citations** | Optional: Pineau reproducibility report (process norms) |
| **Figures** | **Fig 3** dependency / boundary diagram |

---

### 6. Modeling approach

| Field | Content |
|-------|---------|
| **Purpose** | Policy + outcome heads; conditioning; baseline vs trained v1 run |
| **Key arguments** | **Separate** PoC/M00–M11 narrative from Phase E M31–M32 **narrow-vocab** proof |
| **Repo evidence** | `M31_summary`, `M32_summary`, `RELEASE_NOTES_v1.md` Known Limitations; `LiveM01` for baseline temperature |
| **External citations** | Maia (human prediction prior art); Guo (calibration vocabulary) |
| **Figures** | **Table 2** capability catalog (training vs eval scope) |

---

### 7. Human Difficulty Index and structural cognition

| Field | Content |
|-------|---------|
| **Purpose** | HDI v1 + M11 tensors → Context Bridge v2 |
| **Key arguments** | Deterministic feature extraction (FEN in / features out) |
| **Repo evidence** | `docs/POC_RELEASE_MANIFEST.md`; M11 in registry |
| **External citations** | Minimal; optional XAI survey **only if** framing interpretability |
| **Figures** | **Fig 4** feature → bridge payload |

---

### 8. LLM Context Bridge and grounded coaching

| Field | Content |
|-------|---------|
| **Purpose** | Facts-only substrate; translator pattern |
| **Key arguments** | M19 AdviceFacts; M20 deltas; M21 stub LLM + eval; M22 CLI |
| **Repo evidence** | M19–M22 summaries; ADR reference in M19 |
| **External citations** | Ji et al. survey (why grounding matters); **not** claiming full hallucination immunity |
| **Figures** | **Fig 5** LLM-as-translator flow |

---

### 9. Reproducibility, proof packs, and governance

| Field | Content |
|-------|---------|
| **Purpose** | Hash chains, registry, CI jobs, release gates |
| **Key arguments** | “CI as authority surface” + external verifier |
| **Repo evidence** | `M34_summary`; `RELEASE_NOTES_v1.md` verification; `.github/workflows/ci.yml`; overlap coverage |
| **External citations** | Pineau et al.; optional SLSA one-sentence vocabulary |
| **Figures** | **Fig 6** hash-chain / proof-pack flow; **Fig 7** CI job grouping (conceptual) |

---

### 10. v1.0.0 evidence and limitations

| Field | Content |
|-------|---------|
| **Purpose** | Honest recap: M30–M34 |
| **Key arguments** | Synthetic eval; degraded metrics **expected**; not strength proof |
| **Repo evidence** | `RELEASE_NOTES_v1.md`; `proof_pack_v1/README.md`; M32 table |
| **External citations** | None required |
| **Figures** | **Table 3** limitations; **Table 4** milestone timeline (M30–M34 + Phase G pointer optional) |

---

### 11. Novel AI-native architecture patterns

| Field | Content |
|-------|---------|
| **Purpose** | Curated list: architecture-as-test-failure, registry immutability, overlap non-regression, deterministic LLM stub |
| **Key arguments** | Why unusual for research repos; why matters for audit |
| **Repo evidence** | `importlinter_contracts.ini`; `ci.yml`; `M34`; `M21_summary` |
| **External citations** | Sparse—this section is repo-differentiation |
| **Figures** | Reuse Fig 3 / 6 |

---

### 12. Future work

| Field | Content |
|-------|---------|
| **Purpose** | Full-vocab training, real-game eval, live LLM adapters, v2 contracts |
| **Key arguments** | All already hinted in `RELEASE_NOTES_v1.md` |
| **Repo evidence** | Release notes “Next Steps”; open questions doc |
| **External citations** | Optional Maia-2 if positioning multi-skill |
| **Figures** | None |

---

### 13. Conclusion

| Field | Content |
|-------|---------|
| **Purpose** | Restate thesis + strongest **proven** claim classes |
| **Key arguments** | Governance evidence >> strength evidence today |
| **Repo evidence** | Cross-reference §9–10 |
| **External citations** | Minimal |
| **Figures** | None |

---

### 14. Appendices

| Appendix | Purpose | Evidence |
|----------|---------|----------|
| A. Contract inventory snapshot | List contract filenames + milestones | `CONTRACT_REGISTRY_v1.json` |
| B. Verification commands | Copy from release notes | `RELEASE_NOTES_v1.md` |
| C/Milestone table | Extended timeline | `renacechess.md` (extract) |
| D. Claims register excerpt | Safe wording | `renacechess_whitepaper_claims_register.md` |

---

## Citations needed (summary checklist)

- [ ] Maia (MSR + arXiv)
- [ ] Lichess database landing (CC0)
- [ ] Stockfish UCI_ShowWDL (contrast)
- [ ] Guo et al. calibration (optional depth)
- [ ] Ji et al. hallucination survey (short)
- [ ] Pineau reproducibility report (short)

---

## Figures / tables (cross-reference)

See **`renacechess_whitepaper_research_pack.md`** §8 for generation timing (**later** for most visuals; **now** = claims + outline only).
