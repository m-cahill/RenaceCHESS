Perfect — this is exactly the right moment to be precise and boring in the _good_ way 😄  
Below is a **Cursor-ready, enterprise-grade milestone plan for M29**, written to slot cleanly into your governance workflow and hand off without ambiguity.

* * *

**M29_plan — GPU-BENCHMARKING-001**
===================================

**Phase:** Phase E — Scale, Proof & Release  
**Milestone ID:** M29  
**Title:** GPU Benchmarking & Training Time Estimation  
**Status:** Planned  
**Owner:** Human (local execution) + Cursor (docs + tooling)  
**CI Impact:** **None (local-only execution)**

* * *

1. Milestone Intent

-------------------

Establish **empirical, hardware-specific training performance characteristics** for RenaceCHESS on the **RTX 5090**, sufficient to:

1. Estimate **full training wall-clock time** for realistic dataset sizes

2. Validate **training feasibility** under Phase E scope

3. Produce **reproducible benchmark artifacts** suitable for external proof packs

4. Inform go/no-go decisions for M31 (full training run)

This milestone is **measurement-only**.  
It introduces **no new modeling ideas**, **no runtime behavior changes**, and **no CI gating**.

* * *

2. Explicit Non-Goals (Hard Constraints)

----------------------------------------

M29 explicitly does **not**:

* modify model architectures

* tune hyperparameters for quality

* introduce new loss functions or heads

* change dataset semantics

* alter CI pipelines or thresholds

* perform full training

This milestone answers **“How long will this take?”**, not **“How good is it?”**.

* * *

3. Scope of Measurement

-----------------------

### 3.1 Hardware & Environment

Benchmarks must capture and record:

* GPU: **RTX 5090**

* VRAM size

* Driver version

* CUDA version

* PyTorch version

* OS + Python version

* CPU + RAM (for data loader context)

All environment metadata must be emitted into the benchmark artifact.

* * *

### 3.2 Training Axes to Measure

Each benchmark run should explicitly vary **one axis at a time** while holding others constant:

| Axis                           | Values                             |
| ------------------------------ | ---------------------------------- |
| Batch size                     | e.g. 64 / 128 / 256                |
| Sequence length / feature size | current frozen model input         |
| Dataset shard size             | small (sanity), medium, large      |
| Precision                      | FP32 vs AMP (if already supported) |
| Heads                          | policy only vs policy + outcome    |

> ⚠️ No speculative features. Only configurations already supported in main.

* * *

### 3.3 Core Metrics to Capture

Each run must report:

* steps/sec

* samples/sec

* GPU utilization %

* VRAM peak usage

* per-epoch wall time

* time spent in:
  
  * data loading
  
  * forward pass
  
  * backward pass
  
  * optimizer step

Optional (nice-to-have, not required):

* power draw (if easily accessible)

* CPU bottlenecks

* * *

4. Deliverables

---------------

### 4.1 Benchmark Artifact (Required)

Produce a **versioned, schema-validated artifact**, e.g.:
    TrainingBenchmarkReportV1

Minimum required fields:

* environment metadata

* model config hash

* dataset manifest hash

* run matrix

* raw measurements

* derived estimates:
  
  * time / epoch
  
  * time / N samples
  
  * projected full training time

Artifacts must be deterministic **given identical inputs**.

* * *

### 4.2 Time-to-Train Estimator (Required)

From empirical data, derive:

* projected wall-clock time for:
  
  * M31 single full training run
  
  * optional re-runs (best-of-N)

* sensitivity analysis:
  
  * batch size vs memory ceiling
  
  * diminishing returns curves

Estimator must be **explicitly labeled heuristic**, not a guarantee.

* * *

### 4.3 Documentation (Required)

Add:

* `docs/milestones/PhaseE/M29/M29_summary.md`

* `docs/milestones/PhaseE/M29/M29_audit.md`

Audit must explicitly state:

* what was measured

* what was not measured

* sources of uncertainty

* assumptions carried forward to M31

* * *

5. Execution Model

------------------

### 5.1 Where This Runs

* **Local only**

* Never in CI

* CI responsibility ends at:
  
  * schema validation
  
  * artifact parsing
  
  * estimator sanity checks (if applicable)

* * *

### 5.2 Cursor Responsibilities

Cursor should:

1. Add or refine benchmark runner scripts (if needed)

2. Define the benchmark artifact schema

3. Ensure deterministic logging and hashing

4. Prepare doc templates

5. Ensure **no CI regression risk**

Cursor must **not** attempt to execute benchmarks.

* * *

### 5.3 Human Responsibilities

You will:

1. Execute benchmark commands locally

2. Upload artifacts into the repo

3. Validate results against expectations

4. Decide whether results justify proceeding to M31

* * *

6. Guardrails & Governance

--------------------------

### 6.1 CI Guardrails

* No new CI jobs

* No GPU assumptions in CI

* Any accidental CI coupling → immediate rollback

* * *

### 6.2 Audit Posture

M29 audit must answer:

> “Do we now have enough evidence to responsibly commit to full training?”

Possible audit outcomes:

* **Proceed to M31**

* **Proceed with constraints** (e.g. reduced dataset)

* **Pause Phase E** pending resource change

All are valid outcomes.

* * *

7. Exit Criteria (Binary)

-------------------------

M29 is considered **complete** when:

* ✅ Benchmark artifact exists and validates

* ✅ Time-to-train estimate is documented

* ✅ Environment is fully recorded

* ✅ No CI changes occurred

* ✅ Audit explicitly recommends or rejects M31

* * *

8. Next Milestone Dependencies

------------------------------

| Milestone | Dependency on M29                      |
| --------- | -------------------------------------- |
| **M30**   | Uses estimator to size frozen eval set |
| **M31**   | Requires M29 go-decision               |
| **M33**   | Consumes benchmark artifacts           |

* * *

9. Open Questions (for Cursor Clarification Pass)

-------------------------------------------------

Cursor should ask (expected):

1. Exact batch sizes to test

2. Whether AMP is enabled by default

3. Dataset shard sizes to include

4. Preferred naming for benchmark artifact

5. Whether power metrics are required

These are **expected clarifications**, not gaps.

* * *

### ✅ Ready for Cursor Handoff

If you want, next we can:

* Pre-answer likely Cursor clarifying questions

* Draft the **benchmark artifact schema** up front

* Decide whether to pre-declare M29.5 (docs-only contingency)

You’re doing this _exactly_ the right way: measure first, commit later.
