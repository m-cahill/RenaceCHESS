

* * *

Should Phase E be the last phase?
---------------------------------

**Yes, if you define Phase E as “v1 release-quality proof.”**  
You can always leave an “optional Phase F” bucket for UI/provider integrations later, but Phase E can be the final phase for the **core RenaceCHESS system**.

What Phase E should accomplish (as a final phase):

1. **GPU benchmark → time-to-train model** on your actual RTX 5090 setup

2. **A full training run** that produces versioned, reproducible checkpoints + reports

3. **Evaluation at scale** (calibration + runtime gating effects) on a larger frozen set than the tiny fixtures

4. **Release lock**: model card, reproducibility pack, “how to re-run” artifacts, and governance closeout

* * *

Phase map: remaining phases + milestones (proposed)
---------------------------------------------------

### Phase E — Scale Proof, Training Run, Release Lock (FINAL)

> Theme: **no new “ideas”** — just scale, measure, train, validate, and lock.

| Milestone | Name                         | Goal                                                                                                              | Output artifacts (examples)                                                         | CI posture                                                                                           |
| --------- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **M29**   | **GPU-BENCHMARKING-001**     | Benchmark _your_ RTX 5090 and produce a time-to-train estimator                                                   | `TrainingBenchmarkReportV1`, `TrainingTimeEstimateV1`                               | CI validates schemas + CPU stub runner; GPU runs local-only                                          |
| **M30**   | **FROZEN-EVAL-SCALESET-001** | Create a larger frozen eval set (still deterministic) for “real” calibration metrics                              | `FrozenEvalManifestV2` + shards, `EvalSetProvenanceV1`                              | CI validates manifest + sampling determinism                                                         |
| **M31**   | **FULL-TRAINING-RUN-001**    | Run one end-to-end training session (policy + outcome) and emit a reproducible training report                    | `TrainingRunReportV1`, checkpoints, `TrainingConfigLockV1`                          | CI validates report schema + config lock; training local-only                                        |
| **M32**   | **POST-TRAIN-EVAL-PACK-001** | Evaluate trained checkpoints on the scaled frozen set (calibration + M25 recalibration + M26 gating + M27 deltas) | `CalibrationMetricsV1`, `RecalibrationParametersV1`, `RuntimeRecalibrationReportV1` | CI runs evaluation on the scaled set (CPU OK if feasible; otherwise “small-set + schema validation”) |
| **M33**   | **EXTERNAL-PROOF-PACK-001**  | Produce a shareable proof pack: reproducibility, metrics, and “what it is” docs                                   | “proof pack” folder + scripts + pinned refs                                         | CI ensures pack builds and checksums                                                                 |
| **M34**   | **RELEASE-LOCK-001**         | Tag a v1 release candidate, freeze contracts, finalize docs, close Phase E                                        | Release notes, `PhaseE_closeout.md`                                                 | CI hard gates (no new deps, no contract drift)                                                       |

**Why this works:** it makes Phase E the **capstone**: you end with a trained artifact + validated evaluation + a benchmark-driven estimate that tells you what training “costs” on your 5090.

Also: your **DeferredIssuesRegistry currently shows no active deferrals**, so Phase E can start clean, with only whatever you intentionally carry forward from the “full audit” you mentioned.

* * *


------------------------------------------------------
