```markdown
# Cursor Handoff — M10 Plan (RenaceCHESS)

## Context Snapshot (Starting Point)
- M09 (Outcome Head v1) is **CLOSED/IMMUTABLE**.
- A **coverage non-regression** concept was introduced during M09 using **coverage.xml** (Cobertura-style) parsing. Coverage’s XML report is intended for Cobertura-compatible consumers. :contentReference[oaicite:0]{index=0}
- Current pain point carried forward:
  - New M09 code paths caused **coverage regressions in existing files** (notably `cli.py`, `eval/runner.py`) under overlap-set comparison.
  - There was also a fragile float edge case in an M08 test (`test_baseline_policy_v1_forward`).

M10 is the cleanup/hardening milestone that makes the governance rule *actually pass* by restoring coverage on impacted legacy files via tests (and stabilizing the float edge case), without expanding scope.

---

## Milestone: M10 — Coverage Hardening + Runner/CLI Path Tests (v1)

### Objective (single sentence)
Restore/raise coverage in **pre-existing** modules impacted by M09 integration (CLI + eval runner), stabilize the M08 float edge case, and leave CI with a robust, truthful non-regression posture.

### Non-goals (explicit)
- Do **not** change outcome-head math, schemas, or report versions unless absolutely necessary for correctness.
- Do **not** add SBOM/provenance or action SHA pinning here (unless already explicitly scoped in M10 docs).
- Do **not** relax CI gates (no “mute”), only strengthen tests/fixtures.

### Definition of Done
1. ✅ CI is **GREEN** with required checks passing.
2. ✅ Overlap-set coverage comparison (XML-based) reports **no regressions** for overlap files.
3. ✅ Overall project coverage meets the project’s enforced threshold (or the project’s agreed governance rule is met without bypassing truthfulness).
4. ✅ The M08 floating-point precision failure is resolved deterministically (no flaky epsilon).
5. ✅ Deferred Issues Registry updated: coverage-regression item(s) marked resolved or moved with explicit exit criteria.

---

## Work Plan (Governed Phases)

### Phase 0 — Recovery & Branch Setup
- Create branch: `m10-coverage-hardening` (or follow repo naming convention).
- Update `docs/audit/toolcalls.md` with recovery entry (what was last done, what’s next).

### Phase 1 — Baseline Recon (No behavior changes)
1. Identify which CI step is enforcing coverage now:
   - Is it still `pytest --cov-fail-under=90` or config-based `fail_under`?
   - Is the overlap-set XML comparison step the merge blocker?
2. Generate local artifacts:
   - `coverage xml -o coverage.xml`
   - Store “before” coverage report output in scratch notes (not committed).

### Phase 2 — Fix the Real Regressions (Tests, not exceptions)
**Goal:** Add tests that execute the newly-added (but previously untested) code paths in existing modules.

#### A) CLI Coverage Restoration
Target: `src/renacechess/cli.py` — specifically the `train-outcome-head` (or equivalent) wiring.

Implementation approach (choose the one matching the repo’s CLI framework):
- If argparse:
  - Import parser builder and call handler through the same entry function used by `__main__`.
  - Use `monkeypatch` to replace the actual training function with a fast deterministic stub.
- If Typer/Click:
  - Use the framework’s `CliRunner` to invoke the command.
  - Provide minimal args and temp paths.
  - Stub training to avoid heavy work.

Test requirements:
- Assert command exits `0`.
- Assert it calls the expected training entrypoint with expected parameters.
- Assert it writes expected artifacts (or stub artifacts) into `tmp_path`.

#### B) Eval Runner Coverage Restoration
Target: `src/renacechess/eval/runner.py` — specifically new outcome-head integration paths.

Add one **small integration test** that:
- Creates a minimal “fake” outcome head artifact (or uses a tiny real model fixture if already supported).
- Runs eval runner on a minimal deterministic fixture dataset/frozen-eval subset already used in tests.
- Asserts:
  - runner loads the outcome head (or provider) path successfully
  - report includes the expected outcome metrics section when outcome head is provided
  - deterministic output (stable keys and shapes)

**Important:** keep runtime low. Prefer monkeypatching model inference to a deterministic constant if full model load is slow.

### Phase 3 — Fix the M08 Float Precision Edge Case (Minimal + Deterministic)
Target failure: `tests/test_m08_model.py::test_baseline_policy_v1_forward` negative tiny float like `-2.98e-08`.

Fix pattern (choose minimal):
- Clamp probs to `[0, 1]` after softmax and renormalize to sum=1 (deterministic).
- Update/extend test to:
  - Assert `min(probs) >= 0.0` with strict equality allowed after clamp
  - Assert sum close to 1 within a tight epsilon

Add a micro regression test that specifically forces the edge case if feasible (e.g., seed + crafted logits).

### Phase 4 — Re-run Coverage & Validate Gates
- Run `pytest` locally with coverage exactly as CI does.
- Confirm:
  - No overlap-set regressions for `cli.py` and `eval/runner.py`
  - Total coverage meets required threshold
- If overlap-set tool exists as a script, add/adjust tests for the script only if it’s failing. Otherwise, do not churn CI code.

### Phase 5 — Governance Updates (Docs)
1. Update `docs/audit/deferredissuesregistry.md`
   - Mark the relevant LEGACY-COV entry resolved (or split into: “regression fixed” vs “still low absolute coverage”).
   - Add “Exit Criteria satisfied” and the commit/PR reference.
2. Update `docs/audit/toolcalls.md` with actions taken and CI results.

### Phase 6 — Closeout Artifacts (M10)
Create:
- `docs/audit/M10_summary.md`
- `docs/audit/M10_audit.md`
- (Optional) `docs/audit/M10_ci_analysis.md` if your process uses it consistently

Include:
- What changed
- Why it was necessary (truthfulness: tests added to cover real paths)
- Evidence: CI run id(s), coverage before/after, regressions eliminated

### Phase 7 — Permission Gate
- STOP after CI is green and closeout artifacts committed.
- Do **not** merge without user authorization.

---

## Implementation Checklist (Concrete)
- [ ] Add CLI test(s) that exercise outcome-head training command wiring
- [ ] Add eval runner test(s) that exercise outcome-head integration path
- [ ] Patch baseline policy probs to avoid tiny-negative float edge case (+ test)
- [ ] Confirm CI exact coverage gates pass locally
- [ ] Update Deferred Issues Registry
- [ ] Write M10 summary + audit
- [ ] Push branch, verify CI green, stop for permission

---

## Commit Hygiene
Use scoped commits:
- `test(m10): cover CLI outcome training path`
- `test(m10): cover runner outcome integration path`
- `fix(m10): clamp/renormalize baseline policy probabilities`
- `docs(m10): add closeout artifacts + registry updates`

---

## Deliverable Guarantee
At the end of M10:
- CI is green
- Coverage regressions are eliminated by tests (not by weakening gates)
- Deferred Issues Registry reflects accurate project state

STOP and request merge authorization once all required checks are green.
```
