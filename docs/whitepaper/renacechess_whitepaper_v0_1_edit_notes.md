# RenaceCHESS White Paper — Edit Notes

## v0.2 refinement (same file name, PR #56 branch)

### What changed (v0.1 → v0.2)

1. **Header:** Version bumped to **0.2**; roadmap updated for new §2.6, §8.5, §9.4, Appendix C.
2. **§2.6 Data availability:** Explicit disclosure for external circulation—Lichess CC0 at vision level; required elements for a future empirical paper; what v1.0.0 evidence actually uses (synthetic eval + proof pack).
3. **§4.0 Big-picture diagram:** Single Mermaid “RenaceCHESS at a glance” (inputs → signals → grounding → translation → governance).
4. **§5.0 Four tracks:** Table separating PoC learned baseline, LiveM01, Phase E v1.0.0, and future full-vocab work.
5. **§8.5 Governance threat model:** Table of failure modes (schema drift, overclaiming, eval misuse, LLM invention, greenwashing, v1 mutation) vs repo responses; **explicit non-claim** of formal security certification.
6. **§9.4 Limitations at a glance:** Scannable table mirroring conservative claim posture.
7. **Appendix C:** Compact milestone glossary (M07, M11, M19–M22, M30–M34, LiveM01).
8. **Fix:** §2.2 cross-reference `§13` → `§11`.

### Sources used

Unchanged core: research pack PR #55, `VISION.md`, `RELEASE_NOTES_v1.md`, milestone summaries, `proof_pack_v1/README.md`, `importlinter_contracts.ini`, `ci.yml`, registry.

### Claims strengthened or softened

- **Softened:** Governance section now **explicitly denies** formal security/certification language while still describing **dishonesty resistance**.
- **Clarified (not strengthened):** Four-way modeling split; data availability expects future dumps/splits—**no** invented data card.
- **Unchanged:** No production, Stockfish, hallucination-prevention, or full-vocab proof claims introduced.

### Word count

**Approximate word count** (Python `str.split` on `renacechess_whitepaper_v0_1.md`): **6,145** (meets ≥6,000 target for v0.2).

### Remaining open questions

- Concrete Lichess split manifest for any submitted empirical paper.
- Live LLM evaluation under contract.
- Human baseline (e.g., Maia-class) protocol.
- Optional v0.3: single consolidated PDF figure from Mermaid for publishers that do not render diagrams.

### Repo changes

Docs only under `docs/whitepaper/` (`renacechess_whitepaper_v0_1*.md`). No code, CI, registry, proof pack, or milestone history.
