

What the Benchmarks Prove
=========================

_M33 — External Proof Pack Narrative_
Executive Summary
-----------------

The benchmark runs conducted across **M29–M32** do **not** attempt to prove that RenaceCHESS is a strong chess engine.

They prove something more fundamental — and more rare:

> **That RenaceCHESS is an operationally real, deterministic, and scientifically honest human-modeling system whose results can be reproduced, audited, and trusted.**

This proof pack demonstrates end-to-end integrity: from data generation, to training, to evaluation, to reporting — without hidden computation, metric inflation, or unverifiable claims.

* * *

1. The System Trains and Evaluates End-to-End on Real Hardware

--------------------------------------------------------------

The benchmarks confirm that RenaceCHESS:

* Executes full training runs on modern GPU hardware (RTX 5090, Blackwell)

* Produces deterministic checkpoints

* Runs post-training evaluation against a frozen evaluation set

* Emits structured, schema-validated artifacts at every step

This is not a simulated pipeline or a partial prototype.  
It is a **working ML system**.

* * *

2. Compute and Memory Are Not the Bottleneck

--------------------------------------------

Synthetic and real runs demonstrate that:

* Training scales cleanly with batch size

* VRAM usage remains well below hardware limits

* FP32 training is stable and sufficient

* No numerical instability, divergence, or OOM behavior occurred

This establishes that **future capability improvements are data- and modeling-limited, not infrastructure-limited**.

* * *

3. Determinism Is Enforced, Not Assumed

---------------------------------------

Across all benchmarks:

* Dataset manifests are hash-locked

* Frozen evaluation sets are immutable and provably disjoint

* Training configurations are cryptographically bound to code commits

* Evaluation results can be recomputed from artifacts alone

Nothing depends on hidden state, mutable globals, or “trust me” execution.

> If an artifact changes, the system detects it.

* * *

4. Evaluation Results Are Honest — Even When They Are Unfavorable

-----------------------------------------------------------------

Post-training evaluation (M32) shows **degraded policy accuracy** relative to baseline.

This is **expected** and **correct**, because:

* The training run intentionally used a **restricted 8-move vocabulary**

* The frozen evaluation set contains positions requiring many additional legal moves

The system:

* Did not hide this mismatch

* Did not inflate metrics

* Did not reinterpret results favorably

* Reported deltas transparently

This proves that **metrics are not being gamed** and that evaluation is not a marketing surface.

* * *

5. Failures Were Detected, Not Masked

-------------------------------------

Several non-trivial issues occurred during benchmarking:

* Schema version mismatches

* Compatibility gaps between evaluation formats

* Coverage regressions caused by nondeterministic behavior

In every case:

* Execution halted or failed loudly

* The issue was isolated and fixed with minimal scope

* The fix was validated by CI

* Governance artifacts captured the resolution

This demonstrates that RenaceCHESS **fails safely and informatively** — a prerequisite for any system claiming scientific credibility.

* * *

6. What These Benchmarks Do _Not_ Claim

---------------------------------------

This proof pack **does not** claim that:

* The model is strong at chess

* Hyperparameters are optimal

* Calibration is complete

* The vocabulary is production-ready

Those are future, scoped milestones.

The benchmarks prove **infrastructure truth**, not competitive strength.

* * *

Final Claim
-----------

From these benchmarks, one conclusion is justified:

> **RenaceCHESS is a reproducible, auditable, human-modeling chess system whose results — good or bad — can be trusted.**

That is the necessary foundation for any future claims about intelligence, coaching quality, or human realism.

Everything that follows rests on this proof.

* * *


