# RenaceCHESS — Source of Truth

This document tracks milestones, schema, migrations, and governance decisions for RenaceCHESS.

---

## Milestones

| Milestone | Status | Branch | Completion Date | Description |
|-----------|--------|--------|-----------------|-------------|
| M00 | ✅ Closed | `m00-bootstrap` → `main` | 2026-01-23 | Repository Bootstrap + Contract Skeleton + Deterministic Demo |
| M01 | ✅ Closed | `m01-dataset-shards` → `main` | 2026-01-23 | Deterministic Dataset Shard Builder (PGN → JSONL + Manifest) |
| M02 | ✅ Closed | `m02-lichess-ingestion` → `main` | 2026-01-23 | Deterministic Lichess Ingestion |
| M03 | ✅ Closed | `m03-dataset-assembly` → `main` | 2026-01-23 | Deterministic Multi-Shard Dataset Assembly |
| M04 | ✅ Closed | `m04-eval-harness` → `main` | 2026-01-24 | Evaluation Harness v0: Deterministic Policy Evaluation Over Dataset Manifests |
| M05 | ✅ Closed (MERGED) | `m05-labeled-evaluation` → `main` | 2026-01-24 | Ground-Truth Labeled Evaluation v1: Accuracy Metrics and Evaluation Report v2 |
| M06 | ✅ Closed (MERGED) | `m06-conditioned-frozen-eval` → `main` | 2026-01-24 | Conditioned, Frozen Human Evaluation: Skill/Time Conditioning + Frozen Eval Manifest |
| M07 | ✅ Closed (MERGED) | `m07-hdi-v1` → `main` | 2026-01-24 | Human Difficulty Index (HDI) v1 + CLI Completion |
| M08 | ✅ Closed (MERGED) | `m08-learned-policy-baseline` → `main` | 2026-01-24 | First Learned Human Policy Baseline |
| M09 | ✅ Closed (FUNCTIONALLY COMPLETE) | `m09-outcome-head-v1` → `main` | 2026-01-25 | Human Outcome Head (W/D/L) v1 |
| M10 | ✅ Closed | `m10-execution-surface-hardening` → `main` | 2026-01-27 | Coverage Hardening + Runner/CLI Path Tests |
| M11 | ✅ Closed (MERGED) | `m11-structural-interpretability` → `main` | 2026-01-28 | Structural Interpretability Expansion — Per-Piece & Square-Level Cognition |
| M12 | ⛔ Closed (SUPERSEDED) | `m12-archive-audit-remediation` | 2026-01-31 | Audit Remediation Pack — Surfaced contract ambiguity, superseded by M13 |
| M13 | ✅ Closed (MERGED) | `m13-contract-input-semantics` → `main` | 2026-01-31 | CONTRACT-INPUT-SEMANTICS-001 — Explicit contract semantics for dict inputs |
| M14 | ✅ Closed (MERGED) | `m14-train-pack-001` → `main` | 2026-01-31 | TRAIN-PACK-001 — Training Readiness & Benchmark Pack |
| M15 | ✅ Closed (MERGED) | `m15-personality-contract-001` → `main` | 2026-01-31 | PERSONALITY-CONTRACT-001 — Personality Safety Contract + Interface |
| M16 | ✅ Closed (MERGED) | `m16-personality-pawnclamp-001` → `main` | 2026-01-31 | PERSONALITY-PAWNCLAMP-001 — First Concrete Personality Module (Pawn Clamp) |
| M17 | ✅ Closed (MERGED) | `m17-personality-neutral-baseline-001` → `main` | 2026-01-31 | PERSONALITY-NEUTRAL-BASELINE-001 — Neutral Baseline Personality (Experimental Control) |
| M18 | ✅ Closed (MERGED) | `m18-personality-eval-harness-001` → `main` | 2026-01-31 | PERSONALITY-EVAL-HARNESS-001 — Personality Evaluation Harness (Phase B Exit) |
| M19 | ✅ Closed (MERGED) | `m19-advice-facts-contract-001` → `main` | 2026-02-01 | ADVICE-FACTS-CONTRACT-001 — AdviceFacts Contract + Coaching Foundation (Phase C Entry) |
| M20 | ✅ Closed (MERGED) | `m20-elo-bucket-delta-facts` → `main` | 2026-02-01 | ELO-BUCKET-DELTA-FACTS-001 — Elo-Bucket Delta Facts Artifact (Cross-Bucket Comparison) |
| M21 | ✅ Closed (MERGED) | `m21-llm-translation-harness-001` → `main` | 2026-02-01 | LLM-TRANSLATION-HARNESS-001 — LLM Translation Harness + Coaching Evaluation (Phase C Core Complete) |
| M22 | ✅ Closed (MERGED) | `m22-coaching-surface-cli` → `main` | 2026-02-01 | COACHING-SURFACE-CLI-001 — Coaching CLI Surface Exposure (Phase C Exit) |
| M23 | ✅ Closed (MERGED) | `m23-phase-d-hardening-001` → `main` | 2026-02-01 | PHASE-D-HARDENING-001 — Security, Performance, Coverage, DX (Phase D Entry) |
| M24 | ✅ Closed (MERGED) | `m24-phase-d-calibration-001` → `main` | 2026-02-01 | PHASE-D-CALIBRATION-001 — Calibration Metrics and Evaluation Runner |
| M25 | ✅ Closed (MERGED) | `m25-phase-d-recalibration-001` → `main` | 2026-02-01 | PHASE-D-RECALIBRATION-001 — Temperature-Based Probability Recalibration |
| M26 | ✅ Closed (MERGED) | `m26-phase-d-runtime-gating-001` → `main` | 2026-02-01 | PHASE-D-RUNTIME-GATING-001 — Runtime Recalibration Gating |
| M27 | ✅ Closed (MERGED) | `m27-runtime-recalibration-eval` → `main` | 2026-02-02 | PHASE-D-RUNTIME-RECALIBRATION-EVALUATION-001 — Paired Recalibration Evaluation |
| M28 | ✅ Closed (MERGED) | `m28-recalibration-activation-decision` → `main` | 2026-02-02 | PHASE-D-RECALIBRATION-ACTIVATION-DECISION-001 — Runtime Recalibration Decision Framework |
| M29 | ✅ Closed | `m28-recalibration-activation-decision` | 2026-02-02 | GPU-BENCHMARKING-001 — RTX 5090 Blackwell Validation + Benchmark Infrastructure |
| M30 | ✅ Closed (MERGED) | `m30-frozen-eval-scaleset` → `main` | 2026-02-02 | FROZEN-EVAL-SCALESET-001 — 10k Synthetic Frozen Eval Set v2 |
| M31 | ✅ Closed — Training Executed | `579cd2d` | 2026-02-03 | FULL-TRAINING-RUN-001 — Training completed (25m 26s, 10 epochs each, 2 checkpoints) |
| M32 | ✅ Closed — Evaluation Executed | `89b9a4c` | 2026-02-03 | POST-TRAIN-EVAL-PACK-001 — Evaluated 10k positions, delta metrics computed |
| M33 | ✅ Closed (MERGED) | `m33-external-proof-pack` → `main` | 2026-02-03 | EXTERNAL-PROOF-PACK-001 — Self-contained proof bundle with M30-M32 artifacts |
| M34 | ✅ Closed (MERGED) | `m34-release-lock` → `main` | 2026-02-03 | RELEASE-LOCK-001 — Contract registry, CI release gates, Phase E closeout |
| LiveM01 | ✅ Closed (TAGGED v0.2.0) | `main` | 2026-02-28 | Deterministic Skill Conditioning — Temperature scaling for BaselinePolicyV1 |
| M35 | ✅ Closed (MERGED) | `m35-public-release-boundary-guardrails` → `main` | 2026-05-06 | Public Release Boundary Guardrails |
| M36 | ✅ Closed (MERGED) | `m36-public-release-docs-onboarding` → `main` | 2026-05-07 | Public Release Documentation Onboarding |
| M37 | ✅ Closed (MERGED) | `m37-public-release-dx-shortcuts` → `main` | 2026-05-07 | Public Release DX Shortcuts |
| M38 | ✅ Closed (MERGED) | `m38-credential-scanner-hardening` → `main` | 2026-05-07 | Credential Scanner Hardening |
| M39 | ✅ Closed (MERGED) | `m39-torch-cve-upgrade-review` → `main` | 2026-05-09 | Torch CVE Upgrade / Deferral Review (Outcome A) |
| M40 | 🚧 In Progress ([PR #54](https://github.com/m-cahill/RenaceCHESS/pull/54)) | `m40-public-release-candidate-review` → `main` | — | PUBLIC-RELEASE-CANDIDATE-REVIEW — Public boundary, release artifact, proof-pack, and claim-safety review |

**M00 Details:**
- **CI Run 1:** 21271461853 (FAILURE - 28 Ruff errors, 7 MyPy errors)
- **CI Run 2:** 21271784917 (SUCCESS - All gates passing)
- **Final Coverage:** 93.36% lines, ~88.7% branches
- **Remediation Commit:** `1c29812b5942adcd8a36374130b30a31c538158e`
- **Audit:** `docs/milestones/PoC/M00/M00_audit.md`
- **Summary:** `docs/milestones/PoC/M00/M00_summary.md`

**M01 Details:**
- **CI Run 1:** 21279550886 (FAILURE - Format check + coverage 89.02% < 90%)
- **CI Run 2-3:** Intermediate runs (linting fixes)
- **CI Run 4:** 21279736846 (SUCCESS - All gates passing)
- **Final Coverage:** 92.12% lines (exceeds 90% threshold)
- **Test Count:** 51 tests (up from 40)
- **PR:** #3 (ready for merge)
- **Audit:** `docs/milestones/PoC/M01/M01_audit.md`
- **Summary:** `docs/milestones/PoC/M01/M01_summary.md`

**M02 Details:**
- **CI Run 1:** 21283043075 (FAILURE - Type checking, golden test, coverage 83.37% < 90%)
- **CI Run 2:** 21283688678 (FAILURE - Lint hygiene, MyPy, golden test)
- **CI Run 3:** 21284581552 (SUCCESS - All gates passing)
- **Final Coverage:** 93.94% lines (exceeds 90% threshold)
- **Test Count:** 144 tests (up from 95)
- **PR:** #4 (ready for merge)
- **Final Commit:** `5d8b3e2`
- **Audit:** `docs/milestones/PoC/M02/M02_audit.md`
- **Summary:** `docs/milestones/PoC/M02/M02_summary.md`

**M03 Details:**
- **CI Run 1:** 21304980117 (FAILURE - Formatting only, all tests passing)
- **CI Run 2:** 21305144364 (SUCCESS - All gates passing)
- **Final Coverage:** 92.45% lines (exceeds 90% threshold)
- **Test Count:** 160 tests (up from 144)
- **PR:** #5 (merged)
- **Final Commit:** `0acae10`
- **Audit:** `docs/milestones/PoC/M03/M03_audit.md`
- **Summary:** `docs/milestones/PoC/M03/M03_summary.md`

**M04 Details:**
- **CI Run 1:** 21306101033 (FAILURE - Formatting only, all tests passing)
- **CI Run 2:** 21306130316 (SUCCESS - All gates passing)
- **Final Coverage:** Meets 90% threshold (CI job passed)
- **Test Count:** 180 tests (up from 160)
- **PR:** #6 (merged)
- **Final Commit:** `c99e148`
- **Audit:** `docs/milestones/PoC/M04/M04_audit.md`
- **Summary:** `docs/milestones/PoC/M04/M04_summary.md`

**M05 Details:**
- **CI Run 1:** 21306671140 (FAILURE - Formatting and coverage 89.18% < 90%)
- **CI Run 2:** 21306722594 (SUCCESS - All gates passing)
- **Final Coverage:** 92.38% (exceeds 90% threshold)
- **Test Count:** 204 tests (up from 199)
- **PR:** #7 (merged)
- **Final Commit:** `82e9454`
- **Audit:** `docs/milestones/PoC/M05/M05_audit.md`
- **Summary:** `docs/milestones/PoC/M05/M05_summary.md`

**M06 Details:**
- **Objective:** Establish stratified evaluation framework with skill/time conditioning and frozen eval sets
- **CI Run 1:** 21309261892 (FAILURE - Formatting, lint, type errors)
- **CI Runs 2-10:** Intermediate runs (Ruff version drift, CRLF/LF normalization)
- **Final CI Run:** 21310516834 (SUCCESS - All gates passing)
- **Final Coverage:** Meets 90% threshold
- **Test Count:** 241+ tests (37+ new)
- **PR:** #8 (merged)
- **Final Commit:** `aaf1a11`
- **Audit:** `docs/milestones/PoC/M06/M06_audit.md`
- **Summary:** `docs/milestones/PoC/M06/M06_summary.md`
- **Key Files:**
  - `src/renacechess/conditioning/buckets.py` — Bucket assignment functions
  - `src/renacechess/frozen_eval/generator.py` — Frozen eval manifest generator
  - `src/renacechess/eval/conditioned_metrics.py` — Conditioned metrics accumulator
- **Notable Resolution:** CRLF/LF drift resolved via `.gitattributes` + Ruff `line-ending = "lf"`

**M07 Details:**
- **Objective:** Deterministic, explainable Human Difficulty Index (HDI) + CLI completion
- **CI Run 1:** 21311905879 (FAILURE - MyPy type error, line length violations)
- **CI Run 2:** 21312179288 (FAILURE - CRLF format, unreachable code)
- **CI Run 3:** 21312195286 (SUCCESS - All gates passing)
- **Final CI Run (main):** 21312485033 (SUCCESS - All gates passing)
- **Final Coverage:** Meets 90% threshold
- **Test Count:** 267+ tests (26 new)
- **PR:** #9 (merged)
- **Final Commit:** `f252507`
- **Audit:** `docs/milestones/PoC/M07/M07_audit.md`
- **Summary:** `docs/milestones/PoC/M07/M07_summary.md`
- **Key Files:**
  - `src/renacechess/eval/hdi.py` — HDI computation module
  - `src/renacechess/contracts/schemas/v1/eval_report.v4.schema.json` — Eval report v4 schema
  - `docs/evaluation/M07_HDI.md` — HDI specification
- **M06 Deferrals Closed:**
  - M06-D01: CLI `--conditioned-metrics` → RESOLVED
  - M06-D02: Frozen eval enforcement → RESOLVED
- **HDI v1 Formula:** `0.40*entropy + 0.25*topGapInverted + 0.20*legalMovePressure + 0.15*outcomeSensitivity`

**M08 Details:**
- **Objective:** Implement minimal PyTorch baseline model proving learnability
- **CI Run 1:** 21322870481 (FAILURE - Missing imports, wrong import path, lint issues)
- **CI Run 2:** 21322919102 (FAILURE - Formatting, probability clamping, time pressure normalization, coverage)
- **CI Run 3:** 21322990813 (FAILURE - Test expectations, frozen eval minimums, unused variables)
- **CI Run 4:** 21323086357 (SUCCESS - All gates passing)
- **Final Coverage:** 90.43% (exceeds 90% threshold)
- **Test Count:** 284 tests (up from ~241 in M07, +43 new tests)
- **PR:** #10 (merged)
- **Final Commit:** `8e11112`
- **Audit:** `docs/milestones/PoC/M08/M08_audit.md`
- **Summary:** `docs/milestones/PoC/M08/M08_summary.md`
- **Key Files:**
  - `src/renacechess/models/baseline_v1.py` — BaselinePolicyV1 PyTorch model
  - `src/renacechess/models/training.py` — Training infrastructure with frozen eval exclusion
  - `src/renacechess/eval/learned_policy.py` — LearnedHumanPolicyV1 policy provider
- **Notable Features:**
  - Shallow neural baseline (logistic/softmax classifier)
  - Local-only training (not in CI)
  - Deterministic training with fixed seeds
  - Additive integration (does not replace existing baselines)

**M09 Details:**
- **Objective:** Implement learned human outcome head (Win/Draw/Loss prediction)
- **CI Run 1-14:** Multiple runs addressing schema, coverage, and branch coverage gaps
- **CI Run 15-24:** Coverage governance exception implemented (XML-based overlap-set non-regression rule)
- **Final Coverage:** M09-specific files: 100% (all new files); Global: 88.96% (legacy files below threshold)
- **Test Count:** 384+ tests (100+ new tests)
- **PR:** #11 (functionally complete, regressions deferred to M10)
- **Final Commit:** `b7f9a63`
- **Audit:** `docs/milestones/PoC/M09/M09_audit.md`
- **Summary:** `docs/milestones/PoC/M09/M09_summary.md`
- **Key Files:**
  - `src/renacechess/models/outcome_head_v1.py` — OutcomeHeadV1 PyTorch model
  - `src/renacechess/models/training_outcome.py` — Training infrastructure with frozen eval exclusion
  - `src/renacechess/eval/outcome_head.py` — LearnedOutcomeHeadV1 outcome provider
  - `src/renacechess/eval/outcome_metrics.py` — Outcome metrics computation
  - `src/renacechess/contracts/schemas/v1/eval_report.v5.schema.json` — Eval report v5 schema
- **Notable Features:**
  - Completes human evaluation triad (move prediction, difficulty, outcome likelihood)
  - All M09-specific files at 100% coverage
  - XML-based overlap-set coverage non-regression governance mechanism
  - Coverage regressions in orchestration layers deferred to M10
- **Deferred Issues:**
  - LEGACY-COV-001: Global coverage below 90% due to pre-M09 legacy files → M10
  - CLI-COV-001: Outcome-head CLI command untested → M10
  - EVAL-RUNNER-COV-001: Outcome-head eval integration untested → M10

**M10 Details:**
- **Objective:** Restore coverage in orchestration layers, fix M08 float precision issue, establish permanent CI governance
- **CI Run 1:** 21388511020 (SUCCESS - All checks passing)
- **Final Coverage:** 90.64% (exceeds 90% threshold)
- **Test Count:** 336 passed, 1 skipped
- **PR:** #12 (ready for merge)
- **Final Commit:** `24d2fc6`
- **Audit:** `docs/milestones/PoC/M10/M10_audit.md`
- **Summary:** `docs/milestones/PoC/M10/M10_summary.md`
- **Key Files:**
  - `tests/test_cli.py` — CLI integration tests for train-outcome-head
  - `tests/test_m10_runner_outcome_head.py` — Eval runner integration tests
  - `src/renacechess/models/baseline_v1.py` — Float precision fix (clamping + renormalization)
  - `tests/test_m08_model.py` — Regression test for float precision
  - `.github/workflows/ci.yml` — Permanent overlap-set comparison governance
- **Notable Features:**
  - Coverage restored in CLI and eval runner via integration tests
  - M08 float precision edge case fixed deterministically
  - CI governance hardened with permanent overlap-set non-regression rule
  - All M09 deferrals resolved (LEGACY-COV-001, CLI-COV-001, EVAL-RUNNER-COV-001)
  - Real coverage regression detected and fixed (baseline_v1.py: 94.39% → 95.81%)

**M11 Details:**
- **Objective:** Introduce per-piece and square-level structural cognition without altering core policy or evaluation
- **CI Runs:** 4 runs (3 failures due to lint/coverage drift from auto-fixes, 1 success)
- **Final CI Run:** 21421642384 (SUCCESS - All checks passing)
- **Final Coverage:** 90%+ (exceeds threshold, non-regression satisfied)
- **Test Count:** 383 passed, 1 skipped (47 new M11 tests)
- **PR:** #13 (merged)
- **Final Commit:** `b8860ee`
- **Audit:** `docs/milestones/PoC/M11/M11_audit.md`
- **Summary:** `docs/milestones/PoC/M11/M11_summary.md`
- **Key Files:**
  - `src/renacechess/features/per_piece.py` — Per-piece feature extractor (32 slots)
  - `src/renacechess/features/square_map.py` — Square-level feature extractor (weak/strong/hole)
  - `src/renacechess/features/context_bridge_v2.py` — Context Bridge v2 integration
  - `src/renacechess/contracts/models.py` — Added PerPieceFeaturesV1, SquareMapFeaturesV1, ContextBridgePayloadV2
  - `docs/contracts/StructuralCognitionContract_v1.md` — Frozen v1 semantic definitions
- **Notable Features:**
  - 32-slot piece tensor with mobility, tension, and semantic flags
  - Square-level weak/strong/hole maps for both sides
  - Context Bridge v2 supersetting v1 with structural cognition
  - Frozen StructuralCognitionContract_v1.md establishes immutable semantics
  - CI correctly detected and blocked out-of-scope auto-fixes (truthful CI)
- **PoC Cognitive Substrate Complete:**
  - Move prediction (M04-M08)
  - Human difficulty (M07)
  - Outcome prediction (M09)
  - Structural cognition (M11)

**M12 Details:**
- **Objective:** Audit remediation pack for post-PoC hardening
- **Status:** ⛔ Closed without merge — superseded by M13
- **Reason:** M12 surfaced a contract ambiguity (dict-based model instantiation semantics undefined). Rather than choosing an arbitrary fix, M12 correctly deferred the semantic decision to M13.
- **Governance:** This is the correct governance pattern — M12 identified the problem; M13 made the decision.
- **Branch:** Archived as `m12-archive-audit-remediation` for reference
- **PR:** #14 (closed without merge)
- **Documented in:** `docs/milestones/PhaseA/M12/` (plan, run analyses)

**M13 Details:**
- **Objective:** Explicitly define contract input semantics, resolve Pydantic dict-input ambiguity
- **CI Run 1-4:** Multiple runs addressing torch version, baseline coverage, lint errors
- **CI Run 5:** 21539031015 (SUCCESS - All checks passing)
- **Final Coverage:** 90.67% (exceeds 90% threshold)
- **Test Count:** 383 passed, 1 skipped
- **PR:** #15 (merged)
- **Final Commit:** `4617482`
- **Audit:** `docs/milestones/PhaseA/M13/M13_audit.md`
- **Summary:** `docs/milestones/PhaseA/M13/M13_summary.md`
- **Key Files:**
  - `docs/contracts/CONTRACT_INPUT_SEMANTICS.md` — Frozen v1.0 contract semantics
  - `src/renacechess/contracts/models.py` — All 53 models updated to `populate_by_name=True`
  - `importlinter_contracts.ini` — Import-linter configuration for contracts isolation
  - `.github/workflows/ci.yml` — SHA-pinned actions, import-linter step, Python 3.12
- **Notable Features:**
  - **Option A (Alias-Only Dict Inputs):** Dict inputs MUST use camelCase aliases; kwargs MAY use snake_case
  - Supply-chain hardening: all dependencies pinned with `~=`, all Actions SHA-pinned
  - Architectural boundary enforcement via import-linter
  - PYDANTIC-DICT-CONTRACT-001 resolved in DeferredIssuesRegistry
  - M12 superseded (closed without merge, branch archived)
- **Phase A Hardening Started:** M13 is the first completed Phase A milestone

**M14 Details:**
- **Objective:** Establish training readiness infrastructure without retraining models
- **CI Run 1:** 21539554164 (FAILURE - Format check + spurious coverage regression)
- **CI Run 2:** 21539604426 (SUCCESS - All checks passing)
- **Final Coverage:** 90%+ (exceeds 90% threshold)
- **Test Count:** 383 passed, 1 skipped
- **PR:** #17 (merged)
- **Final Commit:** `148204d`
- **Audit:** `docs/milestones/PhaseA/M14/M14_audit.md`
- **Summary:** `docs/milestones/PhaseA/M14/M14_summary.md`
- **Key Files:**
  - `scripts/benchmark_training.py` — Training benchmark harness (local-only)
  - `training/configs/template_policy.yaml` — Policy training config template
  - `training/configs/template_outcome.yaml` — Outcome head training config template
  - `docs/training/M14_TRAINING_BENCHMARK.md` — Benchmark report template
  - `docs/training/CHECKPOINT_PUBLICATION_STANDARD.md` — Checkpoint publication rules
- **Notable Features:**
  - Hardware-agnostic benchmark (GPU detection, VRAM, CPU threads)
  - Explicit frozen-eval contamination check (fail-fast on overlap)
  - Structured JSON output for benchmark results
  - Placeholder hyperparameters with "illustrative only" labeling
  - Benchmark script linted/type-checked only (not executed in CI)
- **Phase A Status:** Training readiness established; Phase A hardening complete

**M15 Details:**
- **Objective:** Define Personality Safety Contract and interface (no behavior, contract + interface only)
- **CI Run 1:** 21540464307 (SUCCESS - All checks passing on first run)
- **Final Coverage:** 90%+ (exceeds 90% threshold)
- **Test Count:** 408+ passed, 1 skipped
- **PR:** #18 (merged)
- **Final Commit:** `206e712`
- **Audit:** `docs/milestones/PhaseB/M15/M15_audit.md`
- **Summary:** `docs/milestones/PhaseB/M15/M15_summary.md`
- **Key Files:**
  - `docs/contracts/PERSONALITY_SAFETY_CONTRACT_v1.md` — Frozen v1 safety contract
  - `src/renacechess/personality/interfaces.py` — PersonalityModuleV1 protocol
  - `src/renacechess/contracts/schemas/v1/personality_config.v1.schema.json` — Config schema
  - `src/renacechess/contracts/models.py` — SafetyEnvelopeV1, PersonalityConfigV1 models
  - `docs/personality/M15_PERSONALITY_EVAL_REQUIREMENTS.md` — Evaluation requirements
  - `docs/phases/PhaseA_closeout.md` — Formal Phase A closeout
- **Notable Features:**
  - Explicit allowed/forbidden interventions defined
  - Safety envelope parameters (top_k, delta_p_max, entropy bounds)
  - Import boundary enforcement via personality-isolation contract
  - Protocol-based interface for type-safe extensibility
  - 25 new schema/model validation tests
- **Phase B Status:** Opened; first Phase B milestone (contract-only, no behavior)

**M16 Details:**
- **Objective:** Implement first concrete personality module (Pawn Clamp) demonstrating M15 contract
- **CI Run 1:** 21551746971 (SUCCESS - All checks passing)
- **Final Coverage:** 90%+ (exceeds 90% threshold)
- **Test Count:** 423+ passed, 1 skipped
- **PR:** #22 (merged)
- **Final Commit:** `11a6b02`
- **Audit:** `docs/milestones/PhaseB/M16/M16_audit.md`
- **Summary:** `docs/milestones/PhaseB/M16/M16_summary.md`
- **Key Files:**
  - `src/renacechess/personality/pawn_clamp.py` — PawnClampPersonalityV1 implementation
  - `configs/personalities/pawn_clamp.v1.yaml` — Default personality configuration
  - `tests/test_m16_pawn_clamp.py` — 15 comprehensive tests
- **Notable Features:**
  - Style scoring using M11 structural features (mobility reduction, weak square creation)
  - Safety envelope enforcement with iterative delta_p_max scaling
  - Divergence metrics (KL divergence, Total Variation distance)
  - Configuration-driven tunable parameters
  - All safety invariants tested (determinism, legality, probability conservation)
- **Phase B Status:** First concrete personality delivered; framework proven operational

**M17 Details:**
- **Objective:** Introduce Neutral Baseline Personality (identity transformation) for experimental control
- **CI Run 1:** 21552248388 (SUCCESS - All checks passing on first run)
- **Final Coverage:** 90%+ (exceeds 90% threshold)
- **Test Count:** 459 passed, 1 skipped (18 new M17 tests)
- **PR:** #23 (merged)
- **Final Commit:** `48dbed0`
- **Audit:** `docs/milestones/PhaseB/M17/M17_audit.md`
- **Summary:** `docs/milestones/PhaseB/M17/M17_summary.md`
- **Key Files:**
  - `src/renacechess/personality/neutral_baseline.py` — NeutralBaselinePersonalityV1 implementation
  - `configs/personalities/neutral_baseline.v1.yaml` — Identity personality configuration
  - `tests/test_m17_neutral_baseline.py` — 18 comprehensive tests
  - `docs/personality/M17_NEUTRAL_BASELINE_DESCRIPTION.md` — Purpose documentation
- **Notable Features:**
  - True identity transformation (output === input)
  - `is_identity()` always returns True (definitionally identity)
  - Zero divergence from raw policy (KL div = 0, TV distance = 0)
  - Comparative tests prove PawnClamp divergence > 0 (style effects are real)
  - First-run CI success (all gates passed)
- **Phase B Status:** Experimental control established; personality effects now measurable

**M18 Details:**
- **Objective:** Introduce deterministic, offline Personality Evaluation Harness for measuring bounded behavioral divergence
- **CI Run 1:** 21552744755 (SUCCESS - All checks passing on first run)
- **Final Coverage:** 91.04% (exceeds 90% threshold)
- **Test Count:** 485 passed, 1 skipped (44 new M18 tests)
- **PR:** #24 (merged)
- **Final Commit:** `4da2635`
- **Audit:** `docs/milestones/PhaseB/M18/M18_audit.md`
- **Summary:** `docs/milestones/PhaseB/M18/M18_summary.md`
- **Key Files:**
  - `src/renacechess/personality/eval_harness.py` — PersonalityEvalHarness implementation
  - `src/renacechess/contracts/models.py` — PersonalityEvalArtifactV1 and related models
  - `src/renacechess/contracts/schemas/v1/personality_eval_artifact.v1.schema.json` — Evaluation artifact schema
  - `tests/fixtures/personality_eval/synthetic_fixtures.py` — Synthetic test fixtures
  - `tests/test_m18_personality_eval_harness.py` — 44 comprehensive tests
  - `docs/personality/M18_PERSONALITY_EVAL_HARNESS.md` — Harness documentation
- **Notable Features:**
  - Divergence metrics (KL divergence, Total Variation, Jensen-Shannon)
  - Envelope utilization tracking
  - Structural attribution (mean/min/max component stats)
  - Determinism hashes (SHA-256, reproducible)
  - First-run CI success (all gates passed)
  - Zero divergence verified for Neutral vs Neutral
  - Bounded divergence verified for Pawn Clamp vs Neutral
- **Phase B Status:** COMPLETE — Personality effects are now measurable, comparable, and auditable

**M19 Details:**
- **Objective:** Establish Phase C entry contract — facts-only coaching substrate
- **CI Run 1:** 21553586177 (FAILURE - Ruff format, MyPy ConfigDict pre-existing issue)
- **CI Run 2:** 21553672113 (SUCCESS - All checks passing)
- **Final Coverage:** 91.33% (exceeds 90% threshold)
- **Test Count:** 512 passed, 1 skipped (27 new M19 tests)
- **PR:** #25 (merged)
- **Final Commit:** `8404d9e`
- **Audit:** `docs/milestones/PhaseC/M19/M19_audit.md`
- **Summary:** `docs/milestones/PhaseC/M19/M19_summary.md`
- **Key Files:**
  - `docs/adr/ADR-COACHING-001.md` — Coaching truthfulness ADR
  - `docs/contracts/ADVICE_FACTS_CONTRACT_v1.md` — Frozen v1 contract
  - `src/renacechess/coaching/advice_facts.py` — Pure builder function
  - `src/renacechess/contracts/schemas/v1/advice_facts.v1.schema.json` — JSON Schema
  - `src/renacechess/contracts/models.py` — AdviceFactsV1 + related models
  - `importlinter_contracts.ini` — coaching-isolation rule
- **Notable Features:**
  - ADR-COACHING-001: "LLMs translate facts, not invent analysis"
  - Determinism hash (SHA-256) in every artifact
  - Canonical ordering (prob descending, UCI ascending for ties)
  - Float precision (6 decimals) for reproducibility
  - explanationHints placeholder for M20+
  - Pre-existing AccuracyMetrics ConfigDict issue fixed
- **Phase C Status:** ENTERED — Facts-only coaching substrate established

**M20 Details:**
- **Objective:** Establish Elo-bucket delta reasoning artifact for cross-bucket comparison
- **CI Run 1:** 21554238255 (SUCCESS - All checks passing on first run)
- **Final Coverage:** 91.57% (exceeds 90% threshold)
- **Test Count:** 554 passed, 1 skipped (42 new M20 tests)
- **PR:** #26 (merged)
- **Final Commit:** `f68b2f7`
- **Audit:** `docs/milestones/PhaseC/M20/M20_audit.md`
- **Summary:** `docs/milestones/PhaseC/M20/M20_summary.md`
- **Key Files:**
  - `docs/contracts/ELO_BUCKET_DELTA_FACTS_CONTRACT_v1.md` — Frozen v1 contract
  - `src/renacechess/coaching/elo_bucket_deltas.py` — Pure builder function
  - `src/renacechess/contracts/schemas/v1/elo_bucket_deltas.v1.schema.json` — JSON Schema
  - `src/renacechess/contracts/models.py` — 10 new Pydantic models
- **Notable Features:**
  - PolicyDeltaV1: KL divergence, Total Variation, rank flips, mass shift
  - OutcomeDeltaV1: W/D/L deltas, win rate monotonicity flag
  - DifficultyDeltaV1: HDI delta
  - StructuralEmphasisDeltaV1: Optional structural emphasis shifts
  - Lineage tracking: sourceAdviceFactsHashes (required, exactly 2)
  - Determinism hash (SHA-256) for reproducibility
  - First-run CI success (all gates passed)
- **Phase C Status:** Cross-bucket comparison artifact established

**M21 Details:**
- **Objective:** Introduce LLMs as pure translators, not analysts — deterministic coaching prose from facts
- **CI Run 1:** 21554787481 (SUCCESS - First-run green, all checks passing)
- **Final Coverage:** 91.34% (exceeds 90% threshold)
- **Test Count:** 587 passed, 1 skipped (33 new M21 tests)
- **PR:** #27 (merged)
- **Final Commit:** `d351ca2`
- **Audit:** `docs/milestones/PhaseC/M21/M21_audit.md`
- **Summary:** `docs/milestones/PhaseC/M21/M21_summary.md`
- **Key Files:**
  - `src/renacechess/coaching/llm_client.py` — LLMClient protocol + DeterministicStubLLM
  - `src/renacechess/coaching/translation_harness.py` — Facts → prose translation
  - `src/renacechess/coaching/evaluation.py` — Hallucination detection + metrics
  - `src/renacechess/contracts/schemas/v1/coaching_draft.v1.schema.json` — Draft schema
  - `src/renacechess/contracts/schemas/v1/coaching_evaluation.v1.schema.json` — Evaluation schema
  - `docs/contracts/COACHING_TRANSLATION_PROMPT_v1.md` — Frozen v1 prompt contract
- **Notable Features:**
  - DeterministicStubLLM for CI determinism (no network calls)
  - Hallucination detection: forbidden terms, move constraints, numeric claims, structural claims
  - Evaluation metrics: factCoverage, hallucinationRate, bucketAlignment, deltaFaithfulness, verbosityScore
  - ToneProfile enum fixed at 3 values (NEUTRAL, ENCOURAGING, CONCISE)
  - AST-based import boundary test + coaching-isolation contract
  - First-run CI success (all gates passed)
- **Phase C Status:** Core coaching spine complete (M19 facts → M20 deltas → M21 translation)

**M22 Details:**
- **Objective:** Expose coaching output via governed CLI surface — pure projection layer
- **CI Run 1-2:** Failures due to lint (N806, E501, F841) and format check
- **CI Run 3:** SUCCESS (All checks passing)
- **Final Coverage:** 90.99% (exceeds 90% threshold)
- **Test Count:** 613 passed, 1 skipped (26 new M22 tests)
- **PR:** #28 (merged)
- **Final Commit:** `7887b69`
- **Audit:** `docs/milestones/PhaseC/M22/M22_audit.md`
- **Summary:** `docs/milestones/PhaseC/M22/M22_summary.md`
- **Key Files:**
  - `src/renacechess/cli.py` — Added `coach` command (~140 lines)
  - `src/renacechess/contracts/models.py` — CoachingSurfaceV1, CoachingSurfaceEvaluationSummaryV1
  - `src/renacechess/contracts/schemas/v1/coaching_surface.v1.schema.json` — CLI output schema
  - `tests/test_m22_coaching_cli.py` — 26 comprehensive tests
- **Notable Features:**
  - Both inputs required (--advice-facts, --delta-facts)
  - Lineage validation (delta facts must reference advice facts hash)
  - Evaluation always printed to stderr (never hidden)
  - Exit non-zero on threshold failure
  - DeterministicStubLLM only (no network calls)
  - Import boundary enforcement tested
- **Phase C Status:** COMPLETE — All 4 milestones closed (M19–M22)

---

## Database Schema

*(No database schema yet — to be added in future milestones)*

---

## Migrations

*(No migrations yet — to be added in future milestones)*

---

## Governance Decisions

### M00 Decisions

1. **Python Version:** Python 3.11 only
   - **Rationale:** Determinism > optional compatibility at M00. 3.11 is the current "enterprise-safe" baseline.
   - **Documented in:** `docs/milestones/PoC/M00/M00_audit.md`

2. **Coverage Thresholds:** 90% lines, 85% branches
   - **Rationale:** Small codebase + deterministic logic = no excuse not to be strict.
   - **Achieved:** 93.36% lines, ~88.7% branches (exceeds requirement)
   - **Documented in:** `docs/milestones/PoC/M00/M00_audit.md`

3. **Pydantic Naming Strategy:** snake_case Python attributes with camelCase JSON aliases
   - **Implementation:** Use `Field(alias=...)` with `ConfigDict(populate_by_name=True)`
   - **Rationale:** Preserves Python naming conventions while maintaining JSON schema compatibility
   - **Documented in:** `docs/milestones/PoC/M00/M00_audit.md`

4. **CI Truthfulness:** All gates enforced from day zero, no weakening or bypassing
   - **Gates:** Ruff lint, MyPy typecheck, Pytest with coverage
   - **Evidence:** CI Run 1 correctly identified 35 real errors; Run 2 confirmed all fixes
   - **Documented in:** `docs/milestones/PoC/M00/M00_run1.md`, `M00_run2.md`

---

## Versioned Contracts

### Context Bridge Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/context_bridge.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.ContextBridgePayload`
- **Status:** ✅ Complete and validated

### Dataset Manifest Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/dataset_manifest.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.DatasetManifest`
- **Status:** ✅ Complete and validated (backward compatible, preserved)

### Dataset Manifest Schema (v2)
- **Location:** `src/renacechess/contracts/schemas/v1/dataset_manifest.v2.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.DatasetManifestV2`
- **Status:** ✅ Complete and validated (default for new builds)

### Ingest Receipt Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/ingest_receipt.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.IngestReceiptV1`
- **Status:** ✅ Complete and validated

### Evaluation Report Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/eval_report.v1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.EvalReportV1`
- **Status:** ✅ Complete and validated (immutable)

### Evaluation Report Schema (v2)
- **Location:** `src/renacechess/contracts/schemas/v1/eval_report.v2.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.EvalReportV2`
- **Status:** ✅ Complete and validated (extends v1 with accuracy metrics)

### Evaluation Report Schema (v3)
- **Location:** `src/renacechess/contracts/schemas/v1/eval_report.v3.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.EvalReportV3`
- **Status:** ✅ Complete and validated (extends v2 with conditioned metrics by skill/time/pressure)

### Evaluation Report Schema (v4)
- **Location:** `src/renacechess/contracts/schemas/v1/eval_report.v4.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.EvalReportV4`
- **Status:** ✅ Complete and validated (extends v3 with Human Difficulty Index - HDI)

### Frozen Eval Manifest Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/frozen_eval_manifest.v1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.FrozenEvalManifestV1`
- **Status:** ✅ Complete and validated (immutable evaluation set with hash verification)

### Frozen Eval Manifest Schema (v2)
- **Location:** `src/renacechess/contracts/schemas/v1/frozen_eval_manifest.v2.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.FrozenEvalManifestV2`
- **Status:** ✅ Complete and validated (M30 synthetic release-grade eval set, 10k positions)

### Eval Set Provenance Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/eval_set_provenance.v1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.EvalSetProvenanceV1`
- **Status:** ✅ Complete and validated (M30 provenance artifact for synthetic eval set)

### Context Bridge Schema (v1) — Extended
- **Location:** `src/renacechess/contracts/schemas/v1/context_bridge.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.ContextBridgePayload`
- **Status:** ✅ Complete and validated (v1-compatible extension with optional `chosenMove` and M06 conditioning fields)

### Context Bridge Schema (v2) — Structural Cognition
- **Location:** `src/renacechess/contracts/schemas/v1/context_bridge.v2.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.ContextBridgePayloadV2`
- **Status:** ✅ Complete and validated (supersets v1 with structural cognition)

### Per-Piece Features Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/PerPieceFeaturesV1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.PerPieceFeaturesV1`
- **Status:** ✅ Complete and validated (32-slot piece tensor with mobility, tension, flags)

### Square Map Features Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/SquareMapFeaturesV1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.SquareMapFeaturesV1`
- **Status:** ✅ Complete and validated (64-entry weak/strong/hole maps)

### Structural Cognition Contract (v1)
- **Location:** `docs/contracts/StructuralCognitionContract_v1.md`
- **Status:** ✅ FROZEN (immutable v1 semantic definitions for M11+ structural layers)

### Contract Input Semantics (v1)
- **Location:** `docs/contracts/CONTRACT_INPUT_SEMANTICS.md`
- **Status:** ✅ FROZEN (immutable v1.0 contract for dict-based model instantiation)
- **Rule:** Option A (Alias-Only Dict Inputs)
  - Dict inputs MUST use camelCase alias keys
  - Keyword arguments MAY use snake_case
  - Normalization happens at contract boundaries
- **Enforcement:** CI + code review + import-linter

### Personality Safety Contract (v1)
- **Location:** `docs/contracts/PERSONALITY_SAFETY_CONTRACT_v1.md`
- **Status:** ✅ FROZEN (immutable v1 safety envelope for personality modules)
- **Key Constraints:**
  - top_k: Maximum moves considered (default: 5)
  - delta_p_max: Maximum probability delta (default: 0.15)
  - entropy bounds: [0.5, 4.0] by default
  - base_reachable: All base moves must remain reachable

### Personality Config Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/personality_config.v1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.PersonalityConfigV1`
- **Status:** ✅ Complete and validated (personality module configuration)

### Personality Eval Artifact Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/personality_eval_artifact.v1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.PersonalityEvalArtifactV1`
- **Status:** ✅ Complete and validated (offline evaluation artifact with divergence metrics)
- **Key Fields:**
  - divergenceMetrics: KL divergence, Total Variation, Jensen-Shannon
  - envelopeUtilization: delta_p_max usage, top_k binding
  - structuralAttribution: style score components, feature deltas
  - determinismHash: SHA-256 for reproducibility verification

### AdviceFacts Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/advice_facts.v1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.AdviceFactsV1`
- **Status:** ✅ FROZEN (Phase C entry contract for coaching facts)
- **Governing ADR:** ADR-COACHING-001 ("LLMs translate facts, not invent")
- **Key Fields:**
  - position: FEN + side to move
  - context: skill/time buckets
  - policy: top moves with probabilities
  - outcome: W/D/L probabilities
  - hdi: Human Difficulty Index
  - structuralCognition: optional M11 deltas
  - explanationHints: placeholder for M20+
  - determinismHash: SHA-256 for reproducibility

### Elo-Bucket Delta Facts Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/elo_bucket_deltas.v1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.EloBucketDeltaFactsV1`
- **Status:** ✅ FROZEN (Phase C cross-bucket comparison artifact)
- **Governing ADR:** ADR-COACHING-001 ("LLMs translate facts, not invent")
- **Key Fields:**
  - baselineBucket / comparisonBucket: M06 skill bucket IDs
  - sourceAdviceFactsHashes: Lineage to source AdviceFacts (required, exactly 2)
  - policyDelta: KL divergence, TV distance, rank flips, mass shift
  - outcomeDelta: W/D/L deltas, win rate monotonicity
  - difficultyDelta: HDI delta
  - structuralDelta: Optional structural emphasis shifts
  - determinismHash: SHA-256 for reproducibility

### Coaching Draft Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/coaching_draft.v1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.CoachingDraftV1`
- **Status:** ✅ FROZEN (Phase C LLM translation artifact)
- **Governing ADR:** ADR-COACHING-001 ("LLMs translate facts, not invent")
- **Key Fields:**
  - draftText: Generated coaching prose
  - skillBucket: Target skill level
  - toneProfile: NEUTRAL | ENCOURAGING | CONCISE
  - referencedFacts: Explicit list of facts used
  - sourceAdviceFactsHash / sourceDeltaFactsHash: Lineage
  - determinismMetadata: promptTemplateVersion, promptHash, modelId, temperature, provider
  - determinismHash: SHA-256 for reproducibility

### Coaching Evaluation Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/coaching_evaluation.v1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.CoachingEvaluationV1`
- **Status:** ✅ FROZEN (Phase C offline evaluation artifact)
- **Governing ADR:** ADR-COACHING-001 ("LLMs translate facts, not invent")
- **Key Fields:**
  - metrics: factCoverage, hallucinationRate, bucketAlignment, deltaFaithfulness, verbosityScore
  - hallucinationDetails: forbiddenTermsFound, unsupportedMoves, unsupportedPercentages, unsupportedStructuralClaims
  - passed: Boolean quality gate result
  - failureReasons: List of gate failures
  - determinismHash: SHA-256 for reproducibility

### Coaching Translation Prompt Contract (v1)
- **Location:** `docs/contracts/COACHING_TRANSLATION_PROMPT_v1.md`
- **Status:** ✅ FROZEN (Prompt template for LLM coaching translation)
- **Governing ADR:** ADR-COACHING-001 ("LLMs translate facts, not invent")
- **Key Rules:**
  - Forbidden terms: engine, stockfish, centipawn, tablebase, mate in, eval
  - Move references: Only topMoves/recommendedMove allowed
  - Numeric claims: Must match source fact percentages (rounded)
  - Structural claims: Controlled vocabulary only if structuralCognition present
  - Tone profiles: NEUTRAL, ENCOURAGING, CONCISE (fixed v1 enum)

### Coaching Surface Schema (v1)
- **Location:** `src/renacechess/contracts/schemas/v1/coaching_surface.v1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.CoachingSurfaceV1`
- **Status:** ✅ FROZEN (Phase C exit contract for CLI surface)
- **Governing ADR:** ADR-COACHING-001 ("LLMs translate facts, not invent")
- **Key Fields:**
  - coachingText: The generated coaching prose
  - skillBucket: Target skill level from input
  - toneProfile: NEUTRAL | ENCOURAGING | CONCISE
  - evaluationSummary: Embedded evaluation metrics subset
  - coachingDraftHash / coachingEvaluationHash: Lineage to source artifacts
  - sourceAdviceFactsHash / sourceDeltaFactsHash: Input artifact lineage
  - determinismHash: SHA-256 for reproducibility
- **Purpose:** Minimal, stable output shape for CLI to render coaching information

### Training Config Lock Schema (v1) — M31
- **Location:** `src/renacechess/contracts/schemas/v1/training_config_lock.v1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.TrainingConfigLockV1`
- **Status:** ✅ NEW (Phase E M31 — config immutability proof)
- **Key Fields:**
  - codeCommitSha: Git commit SHA of training code
  - datasetManifestHash: SHA-256 of training dataset manifest
  - frozenEvalManifestHash: SHA-256 of frozen eval manifest (must NOT be used for training)
  - policyConfig / outcomeConfig: HeadConfigV1 with epochs, batch_size, learning_rate, seed
  - environmentRequirements: Device, precision, deterministic mode
  - checkpointPolicy: Save midpoint/final, output directory
  - sourceTemplates: References to template files with hashes
  - determinismHash: SHA-256 for reproducibility
- **Purpose:** Proves training config immutability; establishes hash chain from code → data → config

### Training Run Report Schema (v1) — M31
- **Location:** `src/renacechess/contracts/schemas/v1/training_run_report.v1.schema.json`
- **Pydantic Model:** `renacechess.contracts.models.TrainingRunReportV1`
- **Status:** ✅ NEW (Phase E M31 — execution summary)
- **Key Fields:**
  - runId: Unique training run identifier
  - startedAt / completedAt: ISO 8601 timestamps
  - status: success | aborted | failed | timeout
  - configLockHash: Reference to TrainingConfigLockV1
  - environment: ExecutionEnvironmentV1 (GPU, CUDA, PyTorch, Python, OS)
  - policyRunSummary / outcomeRunSummary: HeadRunSummaryV1 with epochs, loss, status
  - checkpoints: CheckpointReferenceV1 array (hashes, sizes, paths)
  - totalWallClockSeconds / totalWallClockFormatted: Duration
  - failureNotes: Explanation if status != success
  - determinismHash: SHA-256 for reproducibility
- **Purpose:** Canonical summary of training execution for downstream evaluation and external proof

---

## Phase Status

| Phase | Name | Status | Milestones | Closeout |
|-------|------|--------|------------|----------|
| PoC | Proof of Concept | 🔒 Locked | M00–M11 | `poc-v1.0` tag |
| A | Post-PoC Hardening & Training Readiness | 🔒 **CLOSED** | M12–M14 | `docs/phases/PhaseA_closeout.md` |
| B | Personality Framework & Style Modulation | 🔒 **CLOSED** | M15–M18 | `docs/phases/PhaseB_closeout.md` |
| C | Elo-Appropriate Coaching & Explanation | 🔒 **CLOSED** | M19–M22 | `docs/phases/PhaseC_closeout.md` |
| D | Data Expansion, Calibration & Quality | 🔒 **CLOSED** | M23–M28 | `docs/phases/PhaseD_closeout.md` |
| E | Scale Proof, Training Run, Release Lock | 🔒 **CLOSED** | M29–M34 | `docs/phases/PhaseE_closeout.md` |
| F | Public Release Hardening | 🔒 **CLOSED** | M35 | Public release boundary enforced |
| G | Public Release Readiness | 🔒 **CLOSED** | M36–M40 (M40: final RC review after closeout; see `PhaseG_closeout.md`) | `docs/phases/PhaseG_closeout.md` |

### Public Release Readiness Roadmap (Phase G)

| Milestone | Title | Scope |
|-----------|--------|--------|
| M36 | Public Release Documentation Onboarding | Start Here docs, contributor guide, docs index |
| M37 | Public Release DX Shortcuts | Makefile, setup helper, common command shortcuts |
| M38 | Credential Scanner Hardening | gitleaks or equivalent scanner in CI |
| M39 | Torch CVE Upgrade / Deferral Review — **merged to `main` (#52)** | Bounded torch/setuptools upgrade; remove Torch-only pip-audit ignores; Linux CI CPU Torch policy |
| M40 | Public Release Candidate Review | Final boundary + artifact + verification + claim-safety gate before any public release **action** |

---

## Key Guarantees Established in M00

From M00 forward, RenaceCHESS guarantees:

1. **Truthful CI Baseline:** All gates enforce real quality standards, not cosmetic checks
2. **Enforced Static Analysis:** Ruff and MyPy enforced from day zero
3. **Deterministic Artifact Generation:** Byte-stable, reproducible outputs via canonical JSON
4. **Versioned Contracts:** Schema-first design with JSON Schema + Pydantic validation
5. **Coverage Discipline:** Coverage gates enforced and exceeded (93.36% > 90%)
6. **Governance Loop:** Proven workflow of "fail → analyze → fix → verify"

---

**M23 Details:**
- **Objective:** Harden Phase D entry with security scanning, performance benchmarks, CLI coverage, and DX improvements
- **CI Runs:** 4 runs (3 failures due to security findings, bandit B614, 1 success)
- **Final CI Run:** 21557136080 (SUCCESS - All checks passing)
- **Final Coverage:** 92.20% (exceeds 90% threshold)
- **Test Count:** 649 passed, 1 skipped (36 new M23 tests)
- **PR:** #29 (merged)
- **Final Commit:** `a706c84`
- **Audit:** `docs/milestones/PhaseD/M23/M23_audit.md`
- **Summary:** `docs/milestones/PhaseD/M23/M23_summary.md`
- **Key Files:**
  - `.github/workflows/ci.yml` — Added security + perf-benchmarks jobs
  - `tests/test_m23_perf_benchmarks.py` — 10 performance benchmark tests
  - `tests/test_m23_cli_coverage.py` — 27 CLI coverage tests
  - `.pre-commit-config.yaml` — Local DX pre-commit hooks
- **Notable Features:**
  - Security CI: pip-audit (dependency vulnerabilities) + bandit (SAST)
  - Performance benchmarks: pytest-benchmark with artifact upload (no thresholds)
  - CLI coverage improved: ~72% → 84%
  - Pre-commit hooks: local DX guardrail (CI remains authoritative)
  - Documented deferrals: TORCH-SEC-001 (torch 2.2.2 CVEs), CLI-COV-001 (file-level 84%)
- **Phase D Status:** ENTERED — Hardened foundation for data expansion, calibration, and quality

**M24 Details:**
- **Objective:** Introduce human-aligned calibration and evaluation signals without changing frozen Phase C contracts
- **CI Runs:** 3 runs (2 failures due to coverage data type mismatch and lint errors, 1 success)
- **Final CI Run:** 21569555120 (SUCCESS - All checks passing)
- **Final Coverage:** ≥90% (exceeds threshold, no regressions)
- **Test Count:** 684 passed, 1 skipped (30 new M24 tests)
- **PR:** #30 (merged)
- **Final Commit:** `029e611`
- **Audit:** `docs/milestones/PhaseD/M24/M24_audit.md`
- **Summary:** `docs/milestones/PhaseD/M24/M24_summary.md`

**M25 Details:**
- **Objective:** Introduce explicit, measurable probability recalibration using temperature scaling
- **CI Runs:** 6 runs (5 failures addressing import, lint, types, CI config, datetime, fixture path, formatting, test assertion, coverage; 1 success)
- **Final CI Run:** 21571065091 (SUCCESS - All checks passing)
- **Final Coverage:** 92.53% (exceeds 90% threshold, improved from 92.14%)
- **Test Count:** 713 passed, 1 skipped (30+ new M25 tests)
- **PR:** #31 (merged)
- **Final Commit:** `435231f`
- **Audit:** `docs/milestones/PhaseD/M25/M25_audit.md`
- **Summary:** `docs/milestones/PhaseD/M25/M25_summary.md`
- **Key Files:**
  - `src/renacechess/eval/recalibration_runner.py` — Recalibration fitting and evaluation (734 lines)
  - `src/renacechess/contracts/schemas/v1/recalibration_parameters.v1.schema.json` — Recalibration parameters schema
  - `src/renacechess/contracts/schemas/v1/calibration_delta.v1.schema.json` — Calibration delta schema
  - `tests/test_m25_recalibration.py` — Comprehensive test suite (914 lines)
- **Notable Features:**
  - Temperature scaling for outcome head (W/D/L) and policy head (move probabilities)
  - Per-Elo bucket parameters with deterministic grid search fitting
  - Before/after calibration delta computation
  - Offline-only recalibration (no runtime behavior changes)
  - CLI preview mode (explicit opt-in, off by default)
  - CI recalibration job with artifact upload
- **Governance:**
  - No Phase C contract changes (AdviceFactsV1, EloBucketDeltaFactsV1, CoachingDraftV1 untouched)
  - Coverage improved despite adding 652 new statements
  - All quality gates passing, no regressions introduced
- **Key Files:**
  - `src/renacechess/contracts/models.py` — Added CalibrationMetricsV1 models
  - `src/renacechess/contracts/schemas/v1/calibration_metrics.v1.schema.json` — JSON Schema
  - `src/renacechess/eval/calibration_runner.py` — Calibration evaluation runner
  - `src/renacechess/cli.py` — Added calibration subcommand
  - `tests/test_m24_calibration.py` — 30 comprehensive tests
  - `.github/workflows/ci.yml` — Added calibration-eval job, fixed coverage data type alignment
- **Notable Features:**
  - CalibrationMetricsV1: ECE, Brier score, NLL, confidence histograms
  - Per-Elo bucket stratification: Metrics broken down by canonical SkillBucketId
  - Deterministic evaluation: Fixed seeds, canonical JSON, CI-verified
  - Measurement-only: No Phase C contract changes, no runtime behavior changes
  - Coverage system consistency: All coverage steps use `--cov-branch` (long-term maintainability win)

**M26 Details:**
- **Objective:** Introduce strictly governed runtime gating mechanism for recalibration
- **CI Runs:** 8 runs (progressive refinement: datetime serialization, guard job simplification, coverage extraction, formatting)
- **Final CI Run:** 21574403076 (SUCCESS - All checks passing, coverage regression accepted)
- **Final Coverage:** Overall maintained, -1.28% regression in `eval/runner.py` accepted (COV-M26-001)
- **Test Count:** 20+ new M26 unit tests (integration functions fully covered)
- **PR:** #32 (pending merge authorization)
- **Final Commit:** `c44750f`
- **Audit:** `docs/milestones/PhaseD/M26/M26_audit.md`
- **Summary:** `docs/milestones/PhaseD/M26/M26_summary.md`
- **Key Files:**
  - `src/renacechess/eval/runtime_recalibration.py` — Gate loading and temperature scaling wrapper
  - `src/renacechess/eval/recalibration_integration.py` — Pure integration functions for policy/outcome recalibration
  - `src/renacechess/contracts/schemas/v1/recalibration_gate.v1.schema.json` — RecalibrationGateV1 schema
  - `tests/test_m26_runtime_recalibration.py` — Core gate/scaling tests
  - `tests/test_m26_cli_gate_loading.py` — CLI gate loading unit tests
  - `tests/test_m26_runner_recalibration_integration.py` — 20+ integration tests
- **Notable Features:**
  - RecalibrationGateV1: File-based gate artifact with `enabled`, `parameters_ref`, `scope` fields
  - Runtime recalibration wrapper: Conditional temperature scaling application
  - CLI integration: `--recalibration-gate` argument for `eval run` command
  - Provenance metadata: Metadata attached when recalibration applied (audit/debugging only)
  - Runtime Recalibration Guard job: CI job enforces byte-identical default path
  - Architectural extraction: Pure integration functions extracted for testability
- **Governance:**
  - No Phase C contract changes (AdviceFactsV1, EloBucketDeltaFactsV1, CoachingDraftV1 untouched)
  - Default path byte-identical: Proven by guard job
  - Recalibration opt-in only: Gate must be explicitly enabled
  - Coverage regression accepted: -1.28% in `eval/runner.py` (structural call sites, documented in COV-M26-001)
  - All quality gates passing (coverage regression accepted)

**M27 Details:**
- **Objective:** Evaluate real-world impact of runtime recalibration under controlled conditions — evidence generation only
- **CI Runs:** 4 runs (3 failures addressing MyPy, Ruff format, coverage; 1 success)
- **Final CI Run:** 21576813444 (SUCCESS - All checks passing)
- **Final Coverage:** 90.90% (exceeds 90% threshold)
- **Test Count:** 795 passed, 1 skipped (25 new M27 tests)
- **PR:** #33 (merged)
- **Final Commit:** `e5e7346`
- **Audit:** `docs/milestones/PhaseD/M27/M27_audit.md`
- **Summary:** `docs/milestones/PhaseD/M27/M27_summary.md`
- **Key Files:**
  - `src/renacechess/eval/runtime_recalibration_eval_runner.py` — Paired evaluation runner
  - `src/renacechess/contracts/schemas/v1/runtime_recalibration_report.v1.schema.json` — Report schema
  - `src/renacechess/contracts/schemas/v1/runtime_recalibration_delta.v1.schema.json` — Delta schema
  - `src/renacechess/contracts/models.py` — 12 new Pydantic models
  - `tests/test_m27_runtime_recalibration_eval.py` — 25 comprehensive tests
- **Notable Features:**
  - RuntimeRecalibrationReportV1: Full paired evaluation result with metadata
  - RuntimeRecalibrationDeltaV1: Human-readable deltas with directionality
  - Paired evaluation: Baseline (gate disabled) vs recalibrated (gate enabled)
  - Per-bucket metrics: ECE, Brier, NLL (outcome) + entropy, rank stability (policy)
  - Deterministic outputs: SHA-256 hashes stable across runs
  - CI job validates artifacts and determinism
- **Governance:**
  - No Phase C contract changes (AdviceFactsV1, EloBucketDeltaFactsV1, CoachingDraftV1 untouched)
  - Default behavior unchanged (M26 guard job passes)
  - Recalibration opt-in only: Gate must be explicitly provided
  - Evaluation-only: No runtime activation (decision deferred to M28+)

**M28 Details:**
- **Objective:** Introduce governed decision framework for runtime recalibration activation
- **CI Runs:** 2 runs (1 transient coverage flake, 1 success)
- **Final CI Run:** 21578177807 (SUCCESS - All checks passing)
- **Final Coverage:** 91.10% (exceeds 90% threshold)
- **Test Count:** 831 passed, 1 skipped (36 new M28 tests)
- **PR:** #34 (merged)
- **Final Commit:** `003f712`
- **Audit:** `docs/milestones/PhaseD/M28/M28_audit.md`
- **Summary:** `docs/milestones/PhaseD/M28/M28_summary.md`
- **Key Files:**
  - `src/renacechess/eval/recalibration_decision_runner.py` — Decision runner
  - `src/renacechess/contracts/schemas/v1/runtime_recalibration_activation_policy.v1.schema.json` — Policy schema
  - `src/renacechess/contracts/schemas/v1/runtime_recalibration_decision.v1.schema.json` — Decision schema
  - `src/renacechess/contracts/models.py` — 8 new Pydantic models
  - `tests/test_m28_recalibration_decision.py` — 36 comprehensive tests
- **Notable Features:**
  - RuntimeRecalibrationActivationPolicyV1: Declarative activation policy with bucket/scope overrides
  - RuntimeRecalibrationDecisionV1: Human-readable decision artifact with evidence lineage
  - Three decision outcomes: rejected, restricted, activated
  - Conservative default (all buckets disabled)
  - CI job validates decision generation
- **Governance:**
  - No Phase C contract changes (AdviceFactsV1, EloBucketDeltaFactsV1, CoachingDraftV1 untouched)
  - Default behavior unchanged (M26 guard job passes)
  - Evidence-based decisions (M27 report hash referenced)
  - Framework only — actual activation requires explicit policy

**M29 Details:**
- **Objective:** Establish GPU training benchmark infrastructure for RTX 5090 Blackwell validation
- **Status:** ✅ Closed — Synthetic benchmark complete, real-data benchmark deferred to M31
- **Final Coverage:** 91%+ (exceeds 90% threshold)
- **Audit:** `docs/milestones/PhaseE/M29/M29_audit.md`
- **Summary:** `docs/milestones/PhaseE/M29/M29_summary.md`
- **Key Files:**
  - `scripts/benchmark_training.py` — Extended with GPU detection
  - `src/renacechess/contracts/models.py` — TrainingBenchmarkReportV1, EnvironmentMetadataV1
  - `src/renacechess/contracts/schemas/v1/training_benchmark_report.v1.schema.json` — Benchmark report schema
- **Notable Features:**
  - RTX 5090 Blackwell compatibility validated (no OOM, determinism preserved)
  - Synthetic benchmark mode (no production dataset required)
  - Time-to-train estimation (heuristic-v1, explicitly labeled)
  - Real-data benchmark intentionally deferred to M31 (no production v2 dataset manifest)
- **Phase E Status:** First Phase E milestone complete; benchmark infrastructure ready

**M30 Details:**
- **Objective:** Generate 10,000-position synthetic frozen eval set for release-grade calibration
- **Status:** ✅ Closed (MERGED)
- **PR:** #35
- **CI Run:** 21610395623 (all 10 jobs passed)
- **Merge Commit:** 9fe6d84aa1517636ea1c1501b572b98f41eb287e
- **Closed:** 2026-02-02
- **CI Run:** Pending
- **Key Files:**
  - `src/renacechess/contracts/models.py` — FrozenEvalManifestV2, EvalSetProvenanceV1, FrozenEvalRecordV2
  - `src/renacechess/contracts/schemas/v1/frozen_eval_manifest.v2.schema.json` — V2 manifest schema
  - `src/renacechess/contracts/schemas/v1/eval_set_provenance.v1.schema.json` — Provenance schema
  - `src/renacechess/frozen_eval/generator_v2.py` — Deterministic synthetic position generator
  - `data/frozen_eval_v2/manifest.json` — 10k-position frozen eval manifest
  - `data/frozen_eval_v2/provenance.json` — Provenance artifact
  - `data/frozen_eval_v2/shard_*.jsonl` — 10 data shards (1000 positions each)
  - `tests/test_m30_frozen_eval_v2.py` — 29 comprehensive tests
  - `.github/workflows/ci.yml` — Frozen Eval V2 Validation job
- **Notable Features:**
  - FrozenEvalManifestV2: Breaking schema (not backward-compatible with V1)
  - Synthetic positions: Chess-valid, algorithmically generated (not random tensors)
  - 7 skill buckets: Minimum 1,000 positions each (1,428-1,429 actual)
  - Deterministic generation: Fixed seed (42), reproducible across runs
  - Provenance artifact: Full lineage and audit notes
  - CI validation: Schema, hash, shard integrity, bucket minimums, position count
- **Audit Statement:**
  > "Frozen eval v2 is synthetic but chess-valid, and is intended for *relative* evaluation and calibration stability, not absolute strength claims."
- **Phase E Status:** Frozen eval ruler established; ready for M31 training and M32 evaluation

**M31 Details:**
- **Objective:** Execute one full, end-to-end training run producing reproducible checkpoints and metrics
- **Status:** 🚧 Implementation (artifacts created, awaiting execution)
- **Branch:** `m31-full-training-run`
- **Locked Decisions:**
  - Training data: ~100k positions (real chess data, NOT frozen eval v2)
  - Epochs: 10 (locked)
  - Precision: FP32 only (no AMP)
  - Checkpoints: Midpoint + final (hashes committed, files external)
  - Timeout: 12 hours hard limit
- **Key Files:**
  - `src/renacechess/contracts/schemas/v1/training_config_lock.v1.schema.json` — TrainingConfigLockV1 schema
  - `src/renacechess/contracts/schemas/v1/training_run_report.v1.schema.json` — TrainingRunReportV1 schema
  - `src/renacechess/contracts/models.py` — TrainingConfigLockV1, TrainingRunReportV1 Pydantic models
  - `src/renacechess/dataset/training_dataset_v2.py` — Production training dataset generator (~100k positions)
  - `src/renacechess/models/m31_training_runner.py` — M31 training execution module
  - `tests/test_m31_training_run.py` — Comprehensive M31 test suite
  - `.github/workflows/ci.yml` — M31 Schema Validation CI job
- **Notable Features:**
  - TrainingConfigLockV1: Immutable config proof with hash chain (code → data → config)
  - TrainingRunReportV1: Execution summary with checkpoint references (hashes, not files)
  - Training/Eval separation: Training data is disjoint from frozen eval v2 (different seeds, prefixes)
  - Determinism: Fixed seeds, canonical JSON, reproducible outputs
  - CI validation: Schema validation, unit tests, generator verification
- **Artifacts to Produce (during execution):**
  - `config_lock.json` — Locked training configuration
  - `training_run_report.json` — Execution summary
  - Policy checkpoint (external) + hash
  - Outcome checkpoint (external) + hash
- **Phase E Status:** ✅ CLOSED — Training Executed

**M32 Details:**
- **Objective:** Evaluate M31 trained checkpoints against frozen eval v2, comparing to baselines
- **Status:** ✅ Closed — Evaluation Executed
- **PR:** #38 (merged)
- **Execution Commit:** `89b9a4c`
- **Key Files:**
  - `src/renacechess/contracts/schemas/v1/post_train_eval_report.v1.schema.json` — PostTrainEvalReportV1 schema
  - `src/renacechess/contracts/schemas/v1/policy_eval_metrics.v1.schema.json` — PolicyEvalMetricsV1 schema
  - `src/renacechess/contracts/schemas/v1/outcome_eval_metrics.v1.schema.json` — OutcomeEvalMetricsV1 schema
  - `src/renacechess/contracts/schemas/v1/delta_metrics.v1.schema.json` — DeltaMetricsV1 schema
  - `src/renacechess/eval/post_train_eval.py` — Evaluation orchestrator
  - `tests/test_m32_post_train_eval.py` — 59 comprehensive tests
- **Artifacts Produced:**
  - `artifacts/m32_post_train_eval/post_train_eval_report.json` — Full evaluation report
- **Evaluation Results:**
  - Positions evaluated: 10,000 (100% of frozen eval v2)
  - Policy Top-1 Accuracy: 0.04% (trained) vs 0.51% (baseline) → degraded (expected)
  - No training overlap confirmed
  - Baseline seed: 1337 (fixed, recorded)
- **Known Limitation:** M31 policy lock uses `moveVocabSize: 4096` with narrow effective training distribution; eval degradation vs uniform baseline is expected (see `RELEASE_NOTES_v1.md`)
- **Referenced Artifacts:**
  - PostTrainEvalReportV1 — `artifacts/m32_post_train_eval/post_train_eval_report.json`
  - TrainingRunReportV1 — `artifacts/m31_training_run/training_run_report.json`
  - FrozenEvalManifestV2 — `data/frozen_eval_v2/manifest.json`

**M33 Details:**
- **Objective:** Produce a self-contained, auditor-friendly proof bundle demonstrating RenaceCHESS end-to-end integrity
- **Status:** ✅ Closed (MERGED)
- **PR:** #39 (merged)
- **Final Commit:** `4390d3c`
- **CI Runs:**
  - Run 1: 21620100537 (FAILURE - 3 jobs: lint, type check, CI test data)
  - Run 2: 21620697685 (FAILURE - 3 jobs: formatting, type annotation, CI test data)
  - Run 3: 21621142522 (SUCCESS - All 13 jobs passing)
- **Key Files:**
  - `src/renacechess/contracts/schemas/v1/external_proof_pack.v1.schema.json` — ExternalProofPackV1 schema
  - `src/renacechess/proof_pack/build_proof_pack.py` — Proof pack builder
  - `src/renacechess/proof_pack/verify_proof_pack.py` — Proof pack verifier
  - `src/renacechess/proof_pack/README_TEMPLATE.md` — README template
  - `tests/test_m33_proof_pack.py` — 12 comprehensive tests
- **Artifacts Produced:**
  - `proof_pack_v1/` — Complete proof bundle directory
  - `proof_pack_v1/proof_pack_manifest.json` — ExternalProofPackV1 manifest
  - `proof_pack_v1/README.md` — Executive summary and technical verification guide
  - All M30-M32 artifacts copied with hash verification
  - All required schemas included
- **Determinism Hash:** `sha256:6a69e1f801ca1c03d3aedcc2d8bb6ea86f87eb38e8e6322d9cea477ff398ca2f`
- **Referenced Artifacts:**
  - ExternalProofPackV1 — `proof_pack_v1/proof_pack_manifest.json`
  - FrozenEvalManifestV2 — `proof_pack_v1/frozen_eval/manifest.json`
  - EvalSetProvenanceV1 — `proof_pack_v1/frozen_eval/provenance.json`
  - TrainingConfigLockV1 — `proof_pack_v1/training/config_lock.json`
  - TrainingRunReportV1 — `proof_pack_v1/training/training_run_report.json`
  - PostTrainEvalReportV1 — `proof_pack_v1/evaluation/post_train_eval_report.json`

**M34 Details:**
- **Objective:** Formally lock RenaceCHESS v1 as a truthful, auditable, immutable research release
- **Status:** ✅ Closed (MERGED)
- **PR:** #40 (merged)
- **Final Commit:** `b480f1c` (pending CI)
- **Key Files:**
  - `src/renacechess/contracts/registry.py` — Contract registry generator and validator
  - `src/renacechess/contracts/models.py` — ContractEntryV1, ContractRegistryV1 models
  - `contracts/CONTRACT_REGISTRY_v1.json` — Immutable contract inventory (33 contracts)
  - `tests/test_m34_contract_registry.py` — 10 comprehensive tests
  - `.github/workflows/ci.yml` — 3 new release gates
- **Artifacts Produced:**
  - `contracts/CONTRACT_REGISTRY_v1.json` — 33 v1 contracts with schema hashes
  - `RELEASE_NOTES_v1.md` — v1.0.0 release notes
  - `docs/phases/PhaseE_closeout.md` — Phase E formal closeout
- **CI Release Gates:**
  - `release-dependency-freeze` — Blocks dependency changes
  - `release-contract-freeze` — Validates registry and blocks v1 schema changes
  - `release-proof-pack-verification` — Verifies M33 proof pack integrity
- **Governance:**
  - All v1 contracts frozen with schema hashes
  - CI gates enforce immutability
  - Future changes require v2+ versioning
- **Phase E Status:** ✅ **CLOSED**

**LiveM01 Details:**
- **Objective:** Add deterministic temperature scaling to BaselinePolicyV1 for skill-conditioned move distributions
- **Status:** ✅ Closed (TAGGED v0.2.0)
- **Tag:** `v0.2.0`
- **Tag Commit:** `3b959d97d0bb786934a4056d80ff0f88f3a68d2b`
- **Wheel SHA256:** `DB1C0B2B0AE8F696750055D3889157E7186D609887F3AC79EA9B30482FB3C3DD`
- **Version Bump:** 0.1.0 → 0.2.0
- **Key Files:**
  - `src/renacechess/models/baseline_v1.py` — Temperature scaling implementation (dual-key: named + Elo)
  - `tests/test_livem01_skill_conditioning.py` — 19 new tests (differentiation, entropy ordering, determinism)
  - `docs/milestones/Live/LiveM01/LiveM01_summary.md` — Milestone summary
  - `docs/milestones/Live/LiveM01/LiveM01_audit.md` — Milestone audit
- **Temperature Map (Named Keys):**
  - beginner → 1.6, intermediate → 1.2, advanced → 0.9, expert → 0.75, master → 0.6
- **Temperature Map (Elo Keys):**
  - lt_800, 800_999 → 1.6 | 1000_1199, 1200_1399 → 1.2 | 1400_1599, 1600_1799 → 0.9 | 1800_1999 → 0.75 | gte_2000 → 0.6
- **Entropy Monotonicity:** Confirmed (beginner > intermediate > advanced > expert > master)
- **Determinism:** Confirmed (same fen + skill → identical output across runs and instances)
- **Test Results:** 1028 passed, 1 skipped (full CI suite); 19 new + 16 prior model tests all passing
- **CI Run:** 22533660254
- **What Did Not Change:**
  - No schema changes, no contract changes, no `_encode_skill_bucket()` refactor
  - All M08 tests pass unchanged
  - Temperature scaling is additive, not a breaking change
- **Context:** Driven by RenaceCHESS-Live M09 (Skill Conditioning Exposure); this is the research-side prerequisite

**M35 Details:**
- **Objective:** Prevent accidental publication of private workflow surfaces (`docs/prompts/`, `docs/foundationdocs/`, `.cursorrules`) via `.gitignore`, Git index cleanup, scripted check, CI gate, and public documentation — without deleting local copies or changing contracts / models / proof pack.
- **Phase:** Phase F — Public Release Hardening (**closed**; Phase E remains closed; M35 does not reopen it).
- **Merge:** PR #43 (squash) — `0273dba28581d3e7439aa75fd433d0e49e3b81c0`
- **Post-merge main CI:** 25468691726 (success)
- **Key Files:**
  - `.gitignore` — Private path entries
  - `scripts/check_public_release_boundary.py` — `git ls-files` guard
  - `.github/workflows/ci.yml` — Boundary step in **Lint and Format** job
  - `docs/release/PUBLIC_REPO_BOUNDARY.md` — Boundary + reviewer checklist
  - `tests/test_m35_public_release_boundary.py` — Regression test
  - `docs/milestones/PhaseF/M35/` — Plan, summary, audit, toolcalls stub
- **Credential scanning:** `gitleaks` not added in M35; optional future milestone. Existing **pip-audit** + **bandit** CI unchanged.
- **Audit / Summary:** `docs/milestones/PhaseF/M35/M35_audit.md`, `M35_summary.md`

**M36 Details:**
- **Objective:** Create a single public onboarding path for contributors, auditors, and reviewers
- **Audit driver:** Full codebase audit in `docs/milestones/PhaseG/M36/M36_fullaudit.md` — Docs **3.5/5**; documentation fragmentation; no root `CONTRIBUTING.md` / consolidated Start Here path
- **Branch:** `m36-public-release-docs-onboarding`
- **Key files:**
  - `CONTRIBUTING.md`
  - `docs/GETTING_STARTED.md`
  - `docs/DOCS_INDEX.md`
  - `tests/test_m36_docs_navigation.py`
  - `docs/milestones/PhaseG/M36/M36_plan.md`, `M36_summary.md`, `M36_audit.md`
- **Notable features:**
  - Audience-based docs index
  - Public Start Here path (README + CONTRIBUTING)
  - Contributor setup and PR checklist
  - Public boundary linked from onboarding docs
- **No behavior changes:** Docs-only guardrail test; no schema/model/proof-pack/CI semantic changes
- **PR / CI:** PR #47 — merge commit `b83271560b0306f876195bce953c1f967dbe01ad` (squash on `main`; short `b832715`)

**M37 Details:**
- **Objective:** Add local DX shortcuts that make the M36 onboarding path executable.
- **Audit driver:** M36/M37 public-release readiness roadmap; M36 created onboarding docs, M37 adds command shortcuts.
- **PR:** [#48](https://github.com/m-cahill/RenaceCHESS/pull/48) (squash)
- **Implementation commit:** `cef888c3179ffdae00c6599fe4a614b9aa8ddd4e`
- **Merge commit:** `9e9c1478f866bf4d5e33d08087e2aa6f185b904b`
- **Pre-merge PR CI:** [25481712932](https://github.com/m-cahill/RenaceCHESS/actions/runs/25481712932) — success
- **Post-merge `main` CI:** [25483024592](https://github.com/m-cahill/RenaceCHESS/actions/runs/25483024592) — success
- **Key files:**
  - `Makefile`
  - `scripts/setup_dev.py`
  - `tests/test_m37_dx_shortcuts.py`
  - `CONTRIBUTING.md`
  - `docs/GETTING_STARTED.md`
  - `docs/DOCS_INDEX.md`
- **Notable features:**
  - `make verify` for common pre-PR checks
  - `make boundary-check` for public/private boundary verification
  - `make test-fast` for low-cost onboarding checks
  - conservative setup helper that does not mutate shell state by default
- **No behavior changes:** DX-only; no schema/model/proof-pack changes
- **Final verification (post-merge `main`):** boundary script pass; private paths untracked; M35/M36/M37 guardrail tests pass; `setup_dev.py` default is no-op install

**M38 Details:**
- **Objective:** Add credential scanning to CI and contributor workflows for public release readiness.
- **Audit driver:** Phase G roadmap; M35 established private boundary, M38 adds scanner enforcement.
- **PR / merge:** [#51](https://github.com/m-cahill/RenaceCHESS/pull/51) — squash merge commit **`14a386119d6f73b0d90c995d5eb7a29f1c2a4040`** (merged 2026-05-08 UTC).
- **Pre-merge CI (tip):** [25527801670](https://github.com/m-cahill/RenaceCHESS/actions/runs/25527801670) — success (**Security Scan** / credential step pass).
- **Post-merge `main` CI:** [25529051353](https://github.com/m-cahill/RenaceCHESS/actions/runs/25529051353) — success; **Security Scan** job [74931082954](https://github.com/m-cahill/RenaceCHESS/actions/runs/25529051353/job/74931082954) — **Credential scan (gitleaks current tree)** pass.
- **Allowlist review:** Path allowlists are limited to docs boundary + PhaseG/M38 milestone text + frozen-eval `shard_*.jsonl` regex + `tests/**/*.py` + `tests/fixtures/` (FEN / `recordKey` false positives for `generic-api-key`); dummy example regexes only. Documented in `docs/security/CREDENTIAL_SCANNING.md` and `M38_audit.md`.
- **gitleaks/gitleaks-action** `v2` resolved SHA: `ff98106e4c7b2bc287b24eaf42907196329070c7` (annotated tag `dcedce43c6f43de0b836d1fe38946645c9c638dc`). Blocking CI uses pinned **gitleaks CLI** `8.24.3` with **`git archive HEAD` → `gitleaks dir`** (tracked tree at `HEAD`); see `docs/security/CREDENTIAL_SCANNING.md`.
- **Key files:**
  - `.gitleaks.toml`
  - `.github/workflows/ci.yml`
  - `.github/workflows/credential-scan-full-history.yml`
  - `docs/security/CREDENTIAL_SCANNING.md`
  - `tests/test_m38_credential_scanner_config.py`
  - `Makefile`
- **Notable features:**
  - CI credential scan (blocking, tracked tree at `HEAD` only)
  - local `make secret-scan` / `make secret-scan-no-git` helpers
  - manual `workflow_dispatch` full-history workflow (reporting only)
  - documented response process for real secrets and false positives
  - private boundary remains enforced
- **No behavior changes:** security tooling only; no schema/model/proof-pack changes
- **Post-merge verification:** boundary script pass; private paths untracked; M35–M38 guardrail tests pass on `main`.

**M39 Details:**
- **Objective:** Resolve or formally govern Torch CVE debt before public release — **Outcome A (upgrade accepted).**
- **Audit driver:** Phase G roadmap — M39 closes deferred TORCH posture from CI (`TORCH-SEC-001`), replacing ignores with audited fix-backed versions after one bounded bump.
- **PR / merge:** [#52](https://github.com/m-cahill/RenaceCHESS/pull/52) — squash merge commit **`ab74a2d75918f7aaf7b881468ccf06c64d2f5b2c`** (merged 2026-05-09 UTC).
- **PR tip CI:** [25537724848](https://github.com/m-cahill/RenaceCHESS/actions/runs/25537724848) — success (**Security Scan** incl. pip-audit without Torch-specific ignores; **Test** with CPU-only Torch reinstall + setuptools restore from `pyproject.toml`; release gates).
- **Post-merge `main` CI:** [25587676084](https://github.com/m-cahill/RenaceCHESS/actions/runs/25587676084) — success (Run ID **25587676084**; head matches merge commit).
- **Torch import (Linux Test diagnostic, PR CI):** **`2.11.0+cpu`**, **`cuda_available` false** ([25537724848](https://github.com/m-cahill/RenaceCHESS/actions/runs/25537724848)).
- **Key files:**
  - `docs/security/TORCH_SECURITY_REVIEW.md`
  - `docs/milestones/PhaseG/M39/` (plan, summary, audit)
  - `docs/phases/PhaseG_closeout.md`
  - `pyproject.toml` (`torch>=2.8.0,<3`; `setuptools>=78.1.1,<82`)
  - `.github/workflows/ci.yml` (Security Scan pip-audit without Torch `--ignore-vuln`; Test job CPU-only Torch reinstall on `ubuntu-latest`)
  - `Makefile`, `tests/test_m39_torch_security_docs.py`
- **Torch before:** constraint `~=2.2.0`; typical resolve **2.2.x**.
- **Torch after:** lower bound **2.8.0** (`GHSA-887c` fix line); editable install resolves to latest in range (e.g. **2.11.0** on PyPI CPU wheels during implementation).
- **pip-audit before:** Torch + setuptools flagged without ignores; CI used ignores for Torch.
- **CI:** GitHub-hosted Linux **Test** job reinstalls Torch from the PyTorch **CPU** wheel index (`download.pytorch.org`) so imports succeed without CUDA/NCCL on `ubuntu-latest`; spec always matches checkout `pyproject.toml` (PR baseline vs head); **setuptools** is then reapplied from PyPI using the project's declared pin.
- **PR body:** include **`RELDEPS-EXCEPTION`** for `release-dependency-freeze`; open PR URL and CI URLs are recorded post-submit (not placeholders in-branch).
- **No behavior changes:** dependency / security-scan posture only; no schema/model/proof-pack semantic changes.
- **Post-merge verification:** boundary script pass; private paths untracked; M35–M39 guardrail tests pass; **`pip-audit`** clean (editable skip); Phase G **`main`** CI authoritative for coverage thresholds.

**M40 Details:**
- **Objective:** Final public release candidate review before any public release action (review/evidence only)
- **Branch:** `m40-public-release-candidate-review`
- **PR:** [#54](https://github.com/m-cahill/RenaceCHESS/pull/54)
- **PR head (current tip):** `df4fb4790c374f9aca7e9f2edb23e56c3713c74c`
- **Final Commit:** TBD (GitHub squash merge commit on `main`, if merged)
- **CI Run (tip / green):** [25612790368](https://github.com/m-cahill/RenaceCHESS/actions/runs/25612790368) — **SUCCESS**
- **Note:** Earlier green runs on this PR branch include [25594450506](https://github.com/m-cahill/RenaceCHESS/actions/runs/25594450506) (`44e24c1…`). A docs-only commit once failed **Test** overlap comparison ([25594294614](https://github.com/m-cahill/RenaceCHESS/actions/runs/25594294614)); branch was reset; subsequent full runs **SUCCESS**.
- **Verdict:** `APPROVE_PUBLIC_RC` (local + PR CI)
- **Key Files:**
  - `docs/milestones/PhaseG/M40/M40_public_release_candidate_review.md`
  - `docs/milestones/PhaseG/M40/M40_summary.md`
  - `docs/milestones/PhaseG/M40/M40_audit.md`
- **Release Candidate Review:**
  - Public boundary: PASS
  - Documentation: PASS (with frozen proof-pack manifest prose caveat in review doc)
  - Contract registry: PASS (CI-equivalent; Windows LF caveat in `M40_run1.md`)
  - Proof pack: PASS
  - Known deferrals: MyPy on `tests/`, benchmark thresholds, optional manifest prose reconciliation → M41+

---

**Last Updated:** 2026-05-09 (M40 PR [#54](https://github.com/m-cahill/RenaceCHESS/pull/54); CI **SUCCESS** [25612790368](https://github.com/m-cahill/RenaceCHESS/actions/runs/25612790368) at tip `df4fb4790c374f9aca7e9f2edb23e56c3713c74c`; not merged)


