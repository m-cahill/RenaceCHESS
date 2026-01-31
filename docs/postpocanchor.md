According to a document from **January 30, 2026** (the post-PoC full audit) and the **PoC v1.0 lock manifest dated January 28, 2026**, RenaceCHESS is in a strong “platform PoC” state (policy + outcome + HDI + structural cognition) and the _next best move_ is to **pay down a small set of audit-flagged governance / supply-chain items immediately**, then proceed into **M12+** with personalities + Elo-appropriate coaching built on the M11 substrate.

Below is the **thorough post-PoC anchor document** you asked for—written so a fresh chat (or a new contributor) can reconstruct what’s been decided, what’s locked, and what comes next.

* * *

RenaceCHESS Post-PoC Anchor Document
====================================

PoC v1.0 locked at M11, development continues with M12+
-------------------------------------------------------

### 0) Purpose of this anchor

This document defines:

1. **What the PoC v1.0 is (and is not)**, and what is immutably locked

2. **What the system can already generate** (models, eval reports, LLM payloads)

3. **What the full audit says to fix first** (so we keep audit score high continuously)

4. A **phase/milestone roadmap** for post-PoC development (M12+)

5. The plan for **Elo-appropriate LLM guidance** (grounded, non-hallucinatory)

6. A realistic view of **how much training we can do on your RTX 5090** (plus how to measure it)

* * *

1) What is locked (PoC v1.0)

----------------------------

PoC v1.0 is locked by:

* **Git tag:** `poc-v1.0`

* **Lock branch:** `poc-lock`

* **Release manifest:** `docs/POC_RELEASE_MANIFEST.md`

* **Guarantee:** future work must be additive; PoC semantics must not be redefined

Practical meaning:

* Anyone can `git checkout poc-v1.0` and reproduce the PoC behavior and artifacts as-of lock.

* Ongoing work continues on `main` (M12+), with the lock branch treated as read-only (ideally via branch protection).

* * *

2) What the PoC proves

----------------------

### 2.1 The “human triad” exists and is evaluable

Through M00–M11, the PoC establishes the core thesis: **compute truthful human-conditioned signals; let the LLM translate them.**

The PoC includes:

* A learned **human move policy baseline** (M08)

* A learned **human outcome head** (W/D/L) (M09)

* A **Human Difficulty Index** (HDI v1) (M07)

* Hardened CI governance and coverage posture (M10)

### 2.2 M11 adds structural cognition without changing behavior

M11 introduced **schema-first, deterministic structural features**:

* `PerPieceFeaturesV1` (piece-indexed tensor)

* `SquareMapFeaturesV1` (weak/strong/hole maps, side-relative)

* Context Bridge v2 expansion for richer LLM grounding  
  …and it explicitly does so **without changing move selection, evaluation semantics, or requiring engines at runtime**.

This is why post-PoC personalities and coaching are now “plug-ins,” not redesigns.

* * *

3) What training has actually happened so far?

----------------------------------------------

### What we can say confidently from the milestone log

* **M08 and M09 delivered “learned baselines”** (move policy; outcome head) and established the training/eval loop for those heads.

* The PoC emphasizes **deterministic evaluation on frozen eval sets**; training is **not** treated as an always-on CI activity (by design).

### What’s _not_ yet “fully done” (post-PoC work)

The PoC has proven _learnability and infrastructure_, but it has **not** yet done what I’d call a “production-grade training campaign,” meaning:

* a well-documented, repeatable multi-run benchmark suite (seeds, datasets, hyperparams),

* a curated set of published checkpoints,

* and a long-run quality sweep across Elo buckets / time controls.

That’s normal and actually preferable for a PoC lock. The right next step is a post-PoC training pack milestone (below).

* * *

4) Can we generate useful data if you field test it?

----------------------------------------------------

Yes—**but the type of “field test data” matters**, and we should separate two concepts:

### 4.1 “PoC-aligned field testing” (already valuable)

Even without adding new product surfaces, you can field test by:

* sampling real positions (your games, a small PGN stream, curated test suites),

* running the model to produce:
  
  * **top-k move distributions**
  
  * **W/D/L**
  
  * **HDI**
  
  * **structural cognition payload (M11)**

* and exporting reports/payloads for offline analysis and LLM coaching experiments.

That’s aligned with the PoC’s purpose: generate **truthful grounding data**.

### 4.2 “Product field testing” (not part of PoC v1.0, but a near-term milestone)

If by “field test” you mean:

* interactive UX,

* session logs,

* longitudinal tracking,

* automated personalized coaching loops,

…that’s **not** a PoC v1.0 commitment, but it becomes a clean post-PoC milestone once we have the “AdviceFacts” contract (see Elo guidance section).

* * *

5) Full audit: what should we address first?

--------------------------------------------

The full audit calls out a small number of “enterprise posture” items that are worth fixing _immediately_, because they improve trust and reduce future friction.

### Highest-priority fixes (do these first)

1. **Supply-chain hygiene**: pin GitHub Actions to commit SHAs; tighten dependency locking discipline. The audit flags supply-chain score as notably low and recommends immediate remediation steps.

2. **Module boundary enforcement**: add tooling (e.g., import boundary checks) to prevent gradual architecture drift; the audit explicitly recommends boundary enforcement as a governance guardrail.

3. **CLI coupling / orchestration boundaries**: the audit notes CLI surfaces can become accidental coupling points and suggests hardening that seam early (before more features accumulate).

These are exactly the kind of “small now, painful later” items that your **audit-as-active-governance** posture is designed to catch.

**Recommendation:** Make the first post-PoC milestone start by addressing these, then proceed to personalities/coaching on top of a cleaner base.

* * *

6) Post-PoC phases + milestone breakdown (approximate)

------------------------------------------------------

Below is a pragmatic breakdown that keeps milestones tight and auditable. It assumes we keep your labeling convention and avoid reopening PoC-locked semantics.

### Phase A — Post-PoC hardening + training readiness (M12–M14)

**M12 — POST-POC-HARDEN-001 (Audit Remediation Pack)**

* Pin Actions (SHA), dependency lock strategy, supply chain guardrails

* Import boundary / architectural guardrail added

* CLI surface hardening per audit  
  **Output:** audit score moves up; drift risk reduced.

**M13 — POC-README-001 (PoC README + Runbook)**

* A “single-page” README that states: what it is, what’s locked, how to run evals, how to reproduce key artifacts, where schemas live

* Explicitly references PoC lock semantics (tag/branch/manifest)

**M14 — TRAIN-PACK-001 (5090 Benchmark + Checkpoint Publishing Plan)**

* Add a repeatable local training benchmark harness (examples/sec, VRAM, step time)

* Define “publishable checkpoint” standard (naming, metadata, eval report link)

### Phase B — Personality framework (M15–M18)

**M15 — PERSONALITY-CONTRACT-001**

* Personality Safety Contract (bounded shaping only inside eval-safe window; all λ/thresholds versioned)

* `PersonalityModuleV1` interface and schema (auditable knobs)

**M16 — PERSONALITY-PAWNCLAMP-001**

* First GM-style personality: pawn pushes to restrict mobility (uses M11 piece/square features)

* Safety: only re-ranks within `top_k` or within `Δeval_cp >= -X` window (teacher-derived or policy-derived)

**M17 — PERSONALITY-LIBRARY-001**

* Add 2–3 additional archetypes (e.g., “Capablanca positional,” “Tactical maximalist”)

* Regression suite: personalities must not degrade core correctness beyond safety envelope

**M18 — PERSONA-EVAL-001**

* Personality evaluation reports: style metrics, divergence maps, “what changed” explainability

### Phase C — Elo-appropriate coaching (M19–M22)

**M19 — ADVICE-FACTS-CONTRACT-001**

* Create a schema for the LLM’s grounding payload for advice (“facts, not prose”)

**M20 — ELO-GUIDANCE-GEN-001**

* Implement auto-generated reasons via bucket deltas (details below)

**M21 — COACH-PROMPTPACK-001**

* Prompt contracts: “LLM translates facts → Elo-appropriate explanation”

* Strict “no invention” constraints + style tuning per bucket

**M22 — COACH-EVAL-001**

* Offline rubric scoring: correctness, complexity control, non-engine-speak, user comprehension tests

### Phase D — Data expansion + quality (M23–M30)

* Expand training coverage (openings/middlegames/endgames balance)

* Calibration and bucket fidelity

* Optional: offline Stockfish teacher annotations “piggybacked” during dataset builds (not used at runtime)

### Phase E — Field testing surfaces (M31+)

* Interactive harnesses, replay review, advice UX, exportable artifacts

This is “approximate,” but it’s intentionally shaped so each phase produces **auditable artifacts** and avoids scope bleed.

* * *

7) Elo-appropriate LLM guidance: how it works (grounded, auto-generated)

------------------------------------------------------------------------

Your attached guidance doc frames the key principle:

> Don’t ask the LLM to invent the explanation; ask it to **translate** a structured explanation derived from model signals and comparative distributions.

### 7.1 Core idea: “next-bucket deltas” as the source of _why_

We generate “why” by comparing:

* the player’s bucket move distribution vs.

* one (or more) **next higher** bucket distributions

Then we infer which human concepts explain the delta—e.g., development, king safety, pawn structure, piece activity, weak squares—using structured features (including M11). This is explicitly called out as a promising path in your guidance notes.

### 7.2 Advice pipeline (facts → translation)

1. **Compute candidate set**
   
   * `top_k` from current bucket policy
   
   * optionally include “teacher” best move offline (see Stockfish piggyback note)

2. **Compute comparative signals** for each candidate
   
   * Δprob(current bucket)
   
   * Δprob(next bucket)
   
   * ΔW/D/L, ΔHDI
   
   * Δstructural cognition (piece mobility, weak/strong square changes, pawn structure changes) (M11)

3. **Select 1–3 “reasons”**
   
   * reasons are chosen from a _frozen_ concept vocabulary (“Capablanca heuristic set” style), not ad-hoc prose
   
   * each reason must cite the underlying deltas

4. **LLM translation step**
   
   * The LLM receives only the structured “AdviceFacts” payload and produces Elo-appropriate language.
   
   * It is prohibited from adding new chess claims not present in the facts (the “truthful translator” posture).

### 7.3 What the LLM actually sees

It sees something like:

* “Your move was common in 1200–1400, but rare in 1600–1800.”

* “The higher bucket prefers move X because it increases opponent piece mobility restriction by Y and reduces your weak-square count by Z.”

* “This move is high-HDI; expect humans to miss reply R.”

Not engine speak. Not “+0.37”. Just _human-interpretable deltas_.

* * *

8) How the “pawn mobility restricting GM personality” fits (and why it’s safe)

------------------------------------------------------------------------------

You asked earlier about creating a GM-level agent that specializes in pawn pushes that restrict mobility. With M11, we can do this in a strictly bounded way:

* Use `PerPieceFeaturesV1` to quantify opponent piece mobility changes

* Use `SquareMapFeaturesV1` to quantify new holes / weak squares created and avoided

* Re-rank moves **only inside** a safety window (top-k / Δeval) so we never “sacrifice correctness for style.”

This is exactly the “structure, not agency” approach that made M11 so valuable.

* * *

9) RTX 5090 training reality: what can we expect?

-------------------------------------------------

### What we can ground confidently

Consumer RTX 5090 cards are widely listed with **32GB of GDDR7 VRAM** (board partner specs), which materially improves feasible batch sizes and model sizes compared to 24GB-class cards.【([ASUS](https://www.asus.com/us/motherboards-components/graphics-cards/tuf-gaming/tuf-rtx5090-32g-gaming/techspec/?utm_source=chatgpt.com "ASUS TUF Gaming GeForce RTX™ 5090 32GB GDDR7"))】

Performance uplift over prior-gen depends heavily on workload; in content-creation benchmarks, Puget Systems reports the RTX 5090 as ~**29% faster** than RTX 4090 in their roundup (not a training benchmark, but a directional signal). ([Puget Systems](https://www.pugetsystems.com/labs/articles/2025-consumer-gpu-content-creation-roundup/?utm_source=chatgpt.com "2025 Consumer GPU Content Creation Roundup"))

### The honest answer: “how much training” depends on 3 knobs

1. **Model size** (parameters, activation memory)

2. **Sequence/feature size** (your board encoding, history length, auxiliary heads)

3. **Batch size and optimizer** (AdamW vs fused optimizers, grad checkpointing)

So rather than guessing days/weeks, the enterprise-grade move is:

**M14 should measure examples/sec on your exact training script** and then compute training budgets in “positions processed per hour/day.”

A good rule of thumb once measured:

* If you can sustain **X positions/sec**, then:
  
  * **1M positions** ≈ `1,000,000 / X` seconds
  
  * **100M positions** ≈ `100,000,000 / X` seconds  
    …and you can convert that into “per-bucket” or “per-time-control” budgets.

### Practical expectation

With 32GB VRAM, you’ll typically be able to:

* push larger batches (or more history/features) before hitting VRAM limits,

* reduce gradient accumulation overhead,

* and run longer sweeps without constant OOM tuning.

But we should treat the exact throughput as an empirical number your harness produces—then lock it into the training plan.

(Also: since there have been occasional manufacturing quirks reported on small subsets of these cards, it’s worth validating your specific unit is behaving normally before long runs—but that’s optional.) The Verge ([The Verge](https://www.theverge.com/news/617901/nvidia-confirms-rare-rtx-5090-and-5070-ti-manufacturing-issue?utm_source=chatgpt.com "Nvidia confirms 'rare' RTX 5090 and 5070 Ti manufacturing issue"))

* * *

10) “What’s next” decision: do we act on the audit first?

---------------------------------------------------------

Yes: based on your stated audit posture, the full audit gives us clear “do these now” items that are small and high leverage (supply chain + boundary guardrails + CLI seam hardening).

So the cleanest path is:

* **M12 = Audit Remediation Pack (POST-POC-HARDEN-001)**

* then proceed to **Personality framework + pawn-clamp personality**

* then proceed to **Ele climbing, and prevents rework.

* * *

Appendix: “project overview” reference doc
------------------------------------------

The running project doc and milestone table you’ve been maintaining remains the canonical “at a glance” index.

* * *

If you want the _next actionable handoff_, say “Generate M12_plan” and I’ll produce the Cursor-ready plan with the same tight structure you used for M11 (deliverables, non-goals, guardrails, acceptance criteria, tests, and clos
