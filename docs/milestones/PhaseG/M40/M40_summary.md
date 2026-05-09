# M40 Summary — Public Release Candidate Review

**Phase:** G  
**Branch:** `m40-public-release-candidate-review` → **`main`** (squash merged)  
**PR:** [#54](https://github.com/m-cahill/RenaceCHESS/pull/54)  
**Status:** ✅ **Closed (MERGED)** — review-only milestone; **no public release action** authorized by M40  

## Objective

Final audit-grade **public release candidate** review: boundary safety, release narrative, contract registry + proof pack verification, and classification of deferrals — without feature or model changes.

## Outcomes

- **Verdict:** `APPROVE_PUBLIC_RC` (see `M40_public_release_candidate_review.md`)
- **Deliverables:** `docs/milestones/PhaseG/M40/` — plan, review, run log, summary (this file), audit
- **Docs updated pre-merge:** `RELEASE_NOTES_v1.md`, `docs/phases/PhaseE_closeout.md`, `renacechess.md`, `docs/phases/PhaseG_closeout.md` — reconciled public narrative for M31 (`moveVocabSize`: 4096 vs narrow synthetic regime); M40 / Phase G traceability

## Merge evidence (`main`)

| Item | Value |
|------|--------|
| Final PR head (pre-squash tip) | `e65fc462178540f7316b4d3bac318141d77d31ec` |
| Pre-merge PR CI | [25612956250](https://github.com/m-cahill/RenaceCHESS/actions/runs/25612956250) — **success** |
| Squash merge commit | `f175c8999a70772c6a2df0246cc92efd17c73097` |
| Post-merge `main` CI | [25614956502](https://github.com/m-cahill/RenaceCHESS/actions/runs/25614956502) — **success** |

## Evidence

- **`M40_run1.md`:** commands, Windows/MyPy/registry EOL notes, pytest counts, merge boundary
- **Pre-merge:** ruff pass, `mypy src/renacechess` pass, pytest 1044 passed / 1 skipped (per run log), registry + proof pack pass
- **TORCH-SEC-001:** Resolved under M39; M40 pip-audit spot check clean (see run log)

## Explicit non-actions (charter preserved post-merge)

- **No** tag, package publish, GitHub Release, or repo visibility change without **M41** or explicit release command
- **No** proof-pack manifest hash / frozen JSON edits (legacy prose inconsistency noted for optional M41 regeneration)

## Summary prompt / audit prompt

`docs/prompts/summaryprompt.md` and `docs/prompts/unifiedmilestoneauditpromptV2.md` are **not present** in the public tree (private boundary). This summary follows prior Phase G milestone structure.

## Follow-up

- **M41:** optional governed proof-pack regeneration (manifest prose vs `moveVocabSize`), MyPy on `tests/`, informal benchmark thresholds — **non-blocking** for RC verdict
