# M40 Audit — Public Release Candidate Review

**Phase:** G — Public Release Readiness  
**Milestone:** M40 — Public Release Candidate Review  
**Mode:** Review + verification (no behavior change beyond doc clarity)

---

## Scorecard (1–5)

| Dimension | Score | Notes |
|-----------|------:|-------|
| Governance / scope discipline | 5 | Review-only; frozen contracts untouched |
| Security / public boundary | 5 | `git ls-files` clean; grep clean; boundary script pass |
| Documentation / claim integrity | 4.5 | Training vocab narrative reconciled; frozen manifest still has legacy bullet inconsistency |
| Reproducibility / verification | 5 | Registry + proof pack pass; pytest green; CI-equivalent MyPy green |
| Technical debt visibility | 4 | `mypy src tests` optional; benchmark thresholds still informal |

**Overall:** **4.7 / 5.0**

---

## Material findings

1. **Windows registry validation pitfall (resolved in log):** CRLF working-tree copies of `*.schema.json` can fail registry hash checks; `git restore` / LF checkout matches CI. **Not a product defect**; documented in `M40_run1.md`.

2. **MyPy scope:** `mypy src tests` fails; **CI authoritative target is `src/renacechess`**. Classification: defer typing of full test tree to later milestone.

3. **Training vocabulary public narrative:** Frozen config lock uses **`moveVocabSize: 4096`**; historical docs emphasized “8 moves” for the narrow synthetic opening set. M40 aligns **RELEASE_NOTES**, **Phase E closeout**, and **Source of Truth** to reflect **both** architecture lock and effective diversity. **Frozen** `proof_pack_manifest.json` still contains one limitations bullet inconsistent with `move_count: 4096` — left unchanged; **M41** may address via governed proof-pack regeneration if desired.

4. **TORCH-SEC-001:** **Resolved in M39**; M40 verification does not re-open Torch CVE deferral.

---

## Verdict alignment

`M40_public_release_candidate_review.md` executive verdict: **`APPROVE_PUBLIC_RC`**.

---

## Merge boundary (closeout)

| Field | Value |
|-------|--------|
| PR | [#54](https://github.com/m-cahill/RenaceCHESS/pull/54) |
| Final PR head | `e65fc462178540f7316b4d3bac318141d77d31ec` |
| Squash on `main` | `f175c8999a70772c6a2df0246cc92efd17c73097` |
| Pre-merge PR CI | [25612956250](https://github.com/m-cahill/RenaceCHESS/actions/runs/25612956250) — **success** |
| Post-merge `main` CI | [25614956502](https://github.com/m-cahill/RenaceCHESS/actions/runs/25614956502) — **success** |

M40 **did not** authorize tag, publish, package release, or visibility change.

---

## Prompt sources

Milestone audit prompt files under `docs/prompts/` are not present in the tracked repository (private boundary). This audit follows the structure of prior Phase G milestones (e.g. M39 audit) and the M40 plan acceptance criteria.

**Refresh:** Closeout metrics recorded above; no separate prompt-driven regeneration available in-repo.
