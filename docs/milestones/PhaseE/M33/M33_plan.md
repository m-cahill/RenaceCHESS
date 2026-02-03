# M33 Plan: EXTERNAL-PROOF-PACK-001

**Status:** 🔜 Planned  
**Phase:** E (Scale Proof, Training Run, Release Lock)  
**Predecessor:** M32 (Post-Train Eval Pack)  
**Successor:** M34 (Release Lock)  

---

## Single Objective

Package M30–M32 artifacts into a shareable, auditor-friendly proof bundle suitable for external review (researchers, engineers, partners).

---

## Scope

**IN SCOPE:**
- Narrative documentation explaining the evaluation
- Artifact manifest with hash verification
- Provenance chain linking all artifacts
- Human-readable report format

**OUT OF SCOPE:**
- New computation or metrics
- Model changes or retraining
- Schema modifications
- Code changes beyond documentation generation

---

## Inputs

| Artifact | Source | Hash |
|----------|--------|------|
| PostTrainEvalReportV1 | M32 | (from report) |
| TrainingRunReportV1 | M31 | (from report) |
| FrozenEvalManifestV2 | M30 | (from report) |
| Policy checkpoint | M31 | (from report) |
| Outcome checkpoint | M31 | (from report) |

---

## Outputs

| Artifact | Description |
|----------|-------------|
| `proof_pack_manifest.json` | Master manifest with all artifact references |
| `PROOF_PACK_README.md` | Human-readable explanation for external reviewers |
| `provenance_chain.json` | Hash chain linking M30 → M31 → M32 |

---

## Exit Criteria

- [ ] Proof pack manifest created and validated
- [ ] README explains evaluation methodology
- [ ] All referenced artifacts have verified hashes
- [ ] No new computation required
- [ ] Documentation suitable for external sharing

---

## CI Role

M33 is documentation-only. CI should validate:
- Manifest JSON is valid
- All referenced files exist
- Hashes match declared values

---

**Plan Created:** 2026-02-03  
**Awaiting:** Plan review and locked answers  

