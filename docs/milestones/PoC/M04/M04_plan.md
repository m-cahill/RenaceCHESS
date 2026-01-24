Below is a **paste-ready, detailed Cursor handoff prompt** for **M04**. It assumes **M03 is closed/immutable** and builds directly on the deterministic dataset + manifest v2 foundation you now have.  

---

## ✅ Cursor Handoff Prompt — **M04: Evaluation Harness v0 (CHESS-aligned)**

### Context / Why M04 Exists (do not re-litigate)

RenaceCHESS now has a complete, auditable **data spine** through **M03**: deterministic ingestion receipts → deterministic dataset assembly → bounded JSONL shards → manifest v2 with dataset identity. 
M04’s goal is to make that spine *useful* by adding an **evaluation harness** (policy-in → metrics-out) that is:

* deterministic
* offline-first
* schema-validated
* CI-enforced (coverage, types, formatting)

This is analogous to how “evaluation harness” frameworks standardize model testing over tasks/datasets, but scoped to our chess record format and strict determinism posture. ([GitHub][1])

---

# Milestone Label

**M04 — Evaluation Harness v0: Deterministic Policy Evaluation Over Dataset Manifests**

---

# Single Objective

Implement a **deterministic evaluation runner** that:

1. reads a dataset via **manifest v2 + JSONL shards** (streaming, no full dataset buffering), ([JSON Lines][2])
2. runs one or more **policy providers** (baselines for now),
3. emits a **schema-validated evaluation report** with stable hashes and stable output bytes.

---

# Hard Constraints (must obey)

* **No weakening CI gates** (ruff lint/format, mypy, pytest, coverage threshold).
* **No network calls in tests** (offline-first).
* **Determinism is a feature, not a hope**: same inputs + same config → byte-identical report.
* **No training in M04** (evaluation only).
* **No Stockfish dependency in M04** (engine-based “accuracy” can be M05+; lichess-style accuracy is explicitly engine-derived and a later add). ([lichess.org][3])
* Keep changes **additive**; do not refactor M03 unless strictly necessary for correctness.

---

# Branch / Workflow Rules

1. Start from `main` at the post-M03 merge commit.
2. Create branch: **`m04-eval-harness`**
3. Initialize:

   * `docs/milestones/PoC/M04/M04_plan.md`
   * `docs/milestones/PoC/M04/M04_toolcalls.md` (recovery-first discipline)
4. One PR: `m04-eval-harness` → `main`
5. CI must be green before merge.

---

# Definition of Done (DoD)

✅ **CLI**: `renacechess eval run ...` works locally and in CI
✅ **Report contract**: `eval_report.v1.schema.json` exists + tests validate model ↔ schema
✅ **Determinism**: golden test proves report bytes are stable across runs
✅ **Streaming**: reads JSONL shards record-by-record (no full-load requirement) ([JSON Lines][2])
✅ **Baselines**: at least 2 baseline policy providers implemented and evaluated
✅ **CI**: all required checks pass; coverage ≥ threshold
✅ **Closeout artifacts**: `M04_run*.md`, `M04_audit.md`, `M04_summary.md`

---

# Implementation Plan (phased, small milestones inside M04)

## Phase 0 — Recovery & Recon (must do first)

* Confirm clean workspace, `main` up to date.
* Confirm M03 closed and referenced (do not modify M03 docs). 
* Populate `M04_toolcalls.md` with every tool call / command.

## Phase 1 — Contracts First: `EvalReportV1`

Create a new report contract:

### Add schema

* `src/renacechess/contracts/schemas/v1/eval_report.v1.schema.json`

### Add Pydantic model

* `EvalReportV1`, `EvalRunConfigV1`, `EvalMetricsV1`, etc. in `contracts/models.py`
* Follow your established alias rules (snake_case in Python + aliases if needed).

### Required report fields (minimum)

* `schemaVersion`: `"eval_report.v1"`
* `createdAt`: injectable timestamp for determinism tests
* `datasetDigest`: copied from dataset manifest v2
* `assemblyConfigHash`: copied from dataset manifest v2
* `policyId`: string (e.g., `"baseline.uniform_random"`)
* `evalConfigHash`: hash of canonical JSON config (sorted keys, stable)
* `metrics`: object with:

  * `recordsEvaluated`
  * `illegalMoveRate` (percentage of records where policy emits move not in `legalMoves`)
  * `topKLegalCoverage` (whether policy's top-K outputs intersect `legalMoves`; K configurable, default 1 and 3)
  * `policyEntropy` (mean Shannon entropy of policy distribution, if applicable)
  * `uniqueMovesEmitted` (number of unique moves emitted across dataset)
* `splits`: per-split metric breakdown (train/val/frozenEval/etc if present)

**Note:** M04 evaluates policy validity and structure, not correctness vs human play. Ground-truth accuracy metrics are deferred to M05+ when labeled records or engine annotation are available.

### Contract tests (required)

* Schema validation test that `EvalReportV1.model_dump(by_alias=True)` validates against JSON Schema (same pattern as prior schema tests).

## Phase 2 — Eval Core (streaming runner)

Create package:

* `src/renacechess/eval/`

Modules (suggested):

* `interfaces.py`

  * `PolicyProvider` Protocol: `predict(record) -> list[PolicyMove]` or ranked move IDs
* `baselines.py`

  * `UniformRandomLegalPolicy` (deterministic seeded RNG)
  * `FirstLegalPolicy` (simple deterministic baseline)
  * (Optional) `PreferCapturesPolicy` if capture detection is already easy; otherwise defer.
* `metrics.py`

  * compute illegal move rate (percentage of records where policy emits move not in `legalMoves`)
  * compute top-K legal coverage (whether policy's top-K outputs intersect `legalMoves`)
  * compute policy entropy (Shannon entropy of probability distribution, if applicable)
  * compute output cardinality (number of unique moves emitted across dataset)
  * aggregate per-split metrics (train/val/frozenEval)
* `runner.py`

  * reads dataset manifest v2
  * iterates shards in order (`shard_000.jsonl`, …) and records line-by-line (JSONL streaming) ([JSON Lines][2])
  * applies split assignment already present (or use split field if record contains it)
  * aggregates metrics
* `report.py`

  * builds `EvalReportV1`
  * stable JSON serialization function (sorted keys, consistent separators, newline at end)

### Determinism rules

* Any baseline using randomness must seed via:

  * `seed = sha256(f"{datasetDigest}:{policyId}:{evalConfigHash}")` (or equivalent)
* Ensure float formatting stability:

  * either store metrics as rationals (numerator/denominator) + also compute float rounded to fixed decimals
  * or store fixed-decimal strings (recommended for byte-stability)

## Phase 3 — CLI wiring

Add a CLI group:

* `renacechess eval run`

Flags (minimum):

* `--dataset-manifest <path>` (v2)
* `--policy <id>` (baseline ids)
* `--out <dir>` (write `eval_report.json`)
* `--max-records <n>` (for fast runs; default no limit)
* `--created-at <iso>` (hidden or documented as test-only) to lock timestamps in golden tests

Fail fast:

* if dataset manifest missing
* if schema version mismatch
* if policy id unknown

## Phase 4 — Tests (must bring coverage up naturally, no cheating)

Add tests in `tests/`:

### Unit tests

* metrics correctness on small synthetic records
* deterministic seed behavior for random baseline (same seed → same selections)
* schema validation test for eval report

### Integration/golden tests

* Use existing small dataset fixture approach:

  * either build a tiny dataset in-test from sample PGN (preferred if already stable),
  * or ship a minimal `tests/data/dataset_small_v2/` with manifest + shards.

Golden requirement:

* `test_eval_report_golden_bytes`:

  * run eval twice
  * assert byte-identical report output
  * validate schema

This “golden output” style is a known regression-detection technique when outputs are structured and determinism matters. ([Shaped][4])

## Phase 5 — Docs

Add:

* `docs/EVALUATION.md` (or update an existing docs hub)
  Include:
* what eval does (policy validity evaluation, not ground-truth accuracy)
* how to run on a dataset manifest
* policy baseline ids
* determinism guarantees
* what is explicitly deferred (ground-truth accuracy, Stockfish/lichess-style accuracy, SPRT arenas, training)

Note: engine-vs-engine testing and SPRT are legitimate *future* methodology for comparative strength testing, but out of scope for M04. ([chessprogramming.org][5])

---

# Acceptance Checklist (Cursor must verify locally before pushing)

* `ruff format .`
* `ruff check .`
* `mypy src`
* `pytest -q`
* Confirm coverage gate passes locally (or at least doesn’t regress).
* Ensure no test requires network.

---

# CI Workflow Handling (truthfulness posture)

If CI fails:

1. produce `docs/milestones/PoC/M04/M04_runX.md` with:

   * workflow identity
   * failure classification
   * exact fix
   * guardrail note (did we weaken anything? answer must be “no”)
2. fix only what is required
3. re-run until green

---

# Closeout Deliverables (required once CI green + PR merged)

Generate and commit:

* `docs/milestones/PoC/M04/M04_audit.md` using `docs/prompts/unifiedmilestoneauditprompt.md`
* `docs/milestones/PoC/M04/M04_summary.md` using `docs/prompts/summaryprompt.md`

Update governance tracker (wherever prior milestones are recorded).

---

# Explicitly Deferred (write this into plan + docs)

* **Ground-truth accuracy metrics** (requires labeled records with `chosenMove` field; deferred to M05+)
* Stockfish-based evaluation / lichess accuracy metrics (engine dependency) ([lichess.org][3])
* Engine-vs-engine arenas / SPRT harness ([chessprogramming.org][5])
* Training loop
* Any cloud persistence / dashboards

**Rationale for deferring accuracy:** Current dataset records represent decision contexts (positions), not decisions (moves). Adding `chosenMove` would require retroactive schema changes and violate milestone discipline. M04 focuses on policy validity (legality, distribution, entropy) rather than correctness vs human play.

---

## Final instruction to Cursor

Proceed with implementation **now**, following the phases above, and return:

1. the completed `M04_plan.md`
2. any clarifying questions that remain *strictly necessary* before coding (prefer zero)
3. once CI runs, provide `M04_run1.md` analysis if anything fails; otherwise proceed to merge readiness.

---

[1]: https://github.com/EleutherAI/lm-evaluation-harness?utm_source=chatgpt.com "EleutherAI/lm-evaluation-harness: A framework for few- ..."
[2]: https://jsonlines.org/?utm_source=chatgpt.com "JSON Lines"
[3]: https://lichess.org/page/accuracy?utm_source=chatgpt.com "Lichess Accuracy metric"
[4]: https://www.shaped.ai/blog/golden-tests-in-ai?utm_source=chatgpt.com "Golden Tests in AI: Ensuring Reliability Without Slowing ..."
[5]: https://www.chessprogramming.org/Sequential_Probability_Ratio_Test?utm_source=chatgpt.com "Sequential Probability Ratio Test, or SPRT ..."
