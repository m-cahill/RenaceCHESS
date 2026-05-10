# RenaceCHESS White Paper v0.1 — Edit Notes

## Summary of deliverable

- **`renacechess_whitepaper_v0_1.md`:** First full draft (standalone readable narrative) synthesizing the merged research pack (PR #55) and authoritative repo sources. Audience: ML + chess informatics + infra + governance reviewers.
- **`…_claim_check.md`:** Maps major paper claims to Safe / Risky / Removed per the research claims register.

## Sources used (primary)

Internal:

- `docs/whitepaper/research/renacechess_whitepaper_research_pack.md`
- `docs/whitepaper/research/renacechess_whitepaper_outline.md`
- `docs/whitepaper/research/renacechess_whitepaper_sources.md`
- `docs/whitepaper/research/renacechess_whitepaper_open_questions.md`
- `VISION.md`, `RELEASE_NOTES_v1.md`, `docs/POC_RELEASE_MANIFEST.md`, `docs/postpocphasemap.md`, `docs/postpocanchor.md`
- `contracts/CONTRACT_REGISTRY_v1.json` (intro + milestone labels)
- `proof_pack_v1/README.md`, `importlinter_contracts.ini`, `.github/workflows/ci.yml` (job families, described conceptually)
- Phase C summaries M19–M22, Phase E M30–M34, LiveM01 summary (cited paths)

External (bibliography as link anchors in paper):

- Maia [Maia-2020], MSR pages, Lichess DB, Stockfish UCI, Guo calibration, Ji hallucination survey, Pineau reproducibility report.

## Claims intentionally softened or avoided

- **No** “prevents hallucination”; **yes** to “reduces reliance on LLM calculation” **in designed pipeline** and structured evaluation hooks.
- **No** production / SaaS / commercial framing.
- **No** Stockfish comparison or “stronger engine.”
- **moveVocabSize: 4096** + **narrow effective regime** per `RELEASE_NOTES_v1.md` (not “only eight moves” in isolation).
- M32 metrics framed as **integrity / mismatch** reading, not tactical superiority of baseline.
- RediAI doc referenced only as **pedigree caution**, not proof transfer.

## Figures / tables included

- Markdown tables: comparison, capability catalog, v1 proven vs not claimed, patterns.
- Mermaid: signal pipeline, translator sequence, proof-pack flow (may render in GitHub / compatible viewers).

## Word count

Approximate word count (`python` whitespace split) at authoring time: **~5,001 words** (meets **≥4,500** minimum; **6,000–8,000** stretch can be done in v0.2 with deeper phase detail or appendices).

## Unresolved gaps (carry forward)

Aligned with `renacechess_whitepaper_open_questions.md`:

- No formal human-baseline / Maia-protocol comparison numbers.
- Live LLM vendor results not in scope of M21 stub narrative.
- Lichess license + concrete data splits for any future empirical section.
- Missing root `v1*.md` anchors remain a doc hygiene item, not blocking this draft.

## Recommended next edit pass (v0.2)

1. Add **numeric** pointers only where frozen in artifacts (e.g., exact registry contract count re-verified against `CONTRACT_REGISTRY_v1.json` on branch).
2. Optional **appendix** with verbatim `RELEASE_NOTES_v1.md` limitation bullets for legal/compliance readers.
3. Expand **related work** with Maia-2 [arXiv:2409.20553] **only if** positioning requires it.
4. Consistency pass: ensure every milestone codename appears with phase label once in a glossary-linked form.
5. If targeting 7k+ words: deepen Phase D milestone enumeration and Phase G public-readiness **one-page** summary (M35–M40) — **only** if charter allows expanding scope.

## Repo changes in this milestone

Docs only under `docs/whitepaper/`; no code, CI, schema, registry, proof pack, or milestone history edits.
