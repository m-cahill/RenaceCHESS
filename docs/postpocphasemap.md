

🔒 RenaceCHESS — Post-PoC Phase Map (LOCKED)
============================================

These phases are **program-level constructs**, not just milestone groupings. Each phase has a _definition of done_ that prevents drift.

* * *

🧱 Phase A — Post-PoC Hardening & Training Readiness
----------------------------------------------------

**Purpose:**  
Convert a locked PoC into a **safe, auditable, and train-ready platform** without changing model semantics.

**Starts:** Immediately after PoC v1.0 lock (M11 closed)  
**Ends:** When the system is:

* audit-clean,

* supply-chain hardened,

* and has a measured, reproducible training throughput profile.

### In scope

* Audit remediation

* Supply-chain hygiene

* Architectural boundary enforcement

* CLI / orchestration seam hardening

* Training benchmark harness (not full retraining)

### Explicitly _out of scope_

* Personalities

* Coaching behavior

* Retraining policy heads

### Milestones (expected)

* **M12 — POST-POC-HARDEN-001** (audit remediation pack)

* **M13 — POC-README-001** (PoC README + runbook)

* **M14 — TRAIN-PACK-001** (5090 benchmark + training plan)

### Phase A exit criteria

✔ Audit score materially improved  
✔ Actions pinned / dependencies locked  
✔ Module boundaries enforced  
✔ Measured examples/sec on your 5090  
✔ Clear training budget estimates documented

* * *

🧠 Phase B — Personality Framework & Style Modulation
-----------------------------------------------------

**Purpose:**  
Introduce **bounded behavioral variation** using the M11 structural substrate, without corrupting correctness.

**Starts:** After Phase A exit  
**Ends:** When personalities are:

* auditable,

* bounded,

* and evaluable as first-class artifacts.

### In scope

* Personality safety contract

* Style modules (pawn-clamp, positional, tactical)

* Style evaluation metrics

### Explicitly _out of scope_

* LLM coaching language

* UX

* Online learning

### Milestones (expected)

* **M15 — PERSONALITY-CONTRACT-001**

* **M16 — PERSONALITY-PAWNCLAMP-001**

* **M17 — PERSONALITY-LIBRARY-001**

* **M18 — PERSONA-EVAL-001**

### Phase B exit criteria

✔ Personalities cannot override correctness  
✔ Style deltas are measurable and explainable  
✔ No regression in base policy metrics  
✔ Personality behavior is versioned and reproducible

* * *

🗣️ Phase C — Elo-Appropriate Coaching & Explanation
----------------------------------------------------

**Purpose:**  
Turn RenaceCHESS from “correct signal generator” into a **human-appropriate explainer**.

This is where your _Capablanca-style heuristic translation_ idea fully lands.

**Starts:** After at least one stable personality exists  
**Ends:** When the system can reliably generate **Elo-appropriate, non-hallucinatory guidance**.

### In scope

* AdviceFacts schema

* Elo-bucket delta reasoning

* LLM translation contracts

* Coaching evaluation rubric

### Explicitly _out of scope_

* UI polish

* Longitudinal user modeling

* Online adaptation

### Milestones (expected)

* **M19 — ADVICE-FACTS-CONTRACT-001**

* **M20 — ELO-GUIDANCE-GEN-001**

* **M21 — COACH-PROMPTPACK-001**

* **M22 — COACH-EVAL-001**

### Phase C exit criteria

✔ LLM never invents chess facts  
✔ Advice complexity scales with Elo  
✔ Explanations cite model-derived deltas  
✔ Coaching quality is testable offline

* * *

📊 Phase D — Data Expansion, Calibration & Quality
--------------------------------------------------

**Purpose:**  
Scale _confidence_, not just capability.

This phase makes the system robust across:

* more openings,

* more time controls,

* more Elo bands.

**Starts:** After coaching logic is stable  
**Ends:** When calibration and coverage are demonstrably strong.

### In scope

* Dataset expansion

* Calibration refinement

* Optional offline teacher annotations (Stockfish piggyback)

* Bias / blind-spot analysis

### Explicitly _out of scope_

* Product UX

* Online learning

### Milestones (expected)

* **M23–M30** (multiple small, targeted data/quality milestones)

### Phase D exit criteria

✔ Calibration stable across buckets  
✔ No major opening / phase blind spots  
✔ Training runs are repeatable and documented

* * *

🧪 Phase E — Field Testing & Product Surfaces
---------------------------------------------

**Purpose:**  
Turn the system into something people can _interact with_.

**Starts:** When explanations are trustworthy  
**Ends:** When field data can be collected responsibly.

### In scope

* Interactive harnesses

* Replay analysis

* Coaching UX

* Exportable artifacts

### Explicitly _out of scope_

* Online self-training (unless explicitly approved later)

### Phase E exit criteria

✔ Clear separation between inference and learning  
✔ Field data governance defined  
✔ Product surfaces do not corrupt model truthfulness

* * *


