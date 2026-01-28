Perfect. Below is a **Cursor-ready, governance-clean M11 plan** that locks in Option B exactly as we discussed: **architecture, not agency**.

This is written to be copy-pasted as `docs/milestones/PoC/M11/M11_plan.md` and handed directly to Cursor.

---

# 📘 M11_plan — Structural Interpretability Expansion (v1)

**Project:** RenaceCHESS
**Phase:** Proof of Concept (PoC)
**Milestone:** **M11 — Structural Interpretability Expansion**
**Status:** PLANNED
**Predecessor:** M10 (CLOSED / IMMUTABLE)
**Successor:** M12 (Behavioral Consumers: Personalities / Coaching)

---

## 🎯 Milestone Objective (Single Sentence)

Introduce **piece-level and square-level structural cognition** into RenaceCHESS via deterministic, schema-first feature extraction and Context Bridge expansion — **without modifying move selection, policy behavior, or evaluation semantics**.

---

## 🚧 Non-Goals (Explicit)

M11 **MUST NOT**:

* ❌ Change the move policy or outcome head behavior
* ❌ Introduce personality shaping or preference reweighting
* ❌ Modify evaluation math or training loss
* ❌ Introduce runtime engine calls
* ❌ Alter frozen eval sets or existing metrics

This milestone is **structural only**.

---

## 🧱 Scope Overview

M11 adds **semantic resolution**, not agency.

### New Capabilities (Additive Only)

1. **Per-piece structural modeling**
2. **Square-level weak/strong/hole maps**
3. **Context Bridge vNext** (expanded LLM grounding payload)
4. **Structural Cognition Contract** (versioned invariants)
5. **Golden FEN test fixtures** to lock semantics

---

## 📦 Deliverables

### 1️⃣ `PerPieceFeaturesV1`

#### Description

A **piece-indexed, fixed-ordering tensor** that describes the structural state of every chess piece in human-interpretable terms.

#### Requirements

* Exactly **32 slots**, fixed ordering:

  * White: `K,Q,R_a,R_h,B_c,B_f,N_b,N_g,P_a..P_h`
  * Black: `k,q,r_a,r_h,b_c,b_f,n_b,n_g,p_a..p_h`
* Ordering **never changes**, even if pieces are captured.
* Pawns retain identity through promotion (promotion encoded via metadata).

#### Required Fields (minimum)

* identity: `slot_id`, `color`, `piece_type`
* location: `square` or `null`, `alive`
* mobility: `mobility_legal`, `mobility_safe`
* tension: `attacked_by`, `defended_by`, `net_defense`
* flags:

  * `is_hanging`
  * `is_pinned`
  * `is_restricted`
  * `is_dominated`
  * `is_attacker`
  * `is_defender_of_king`

#### Artifacts

* JSON Schema: `schemas/PerPieceFeaturesV1.json`
* Pydantic model: `models/structures/per_piece_v1.py`
* Extractor: `src/renacechess/features/per_piece.py`

---

### 2️⃣ `SquareMapFeaturesV1`

#### Description

Deterministic **square-level structural maps** describing long-term positional properties from each side’s perspective.

#### Required Maps

All maps are **side-relative** and length-64:

* `weak_for_white`
* `strong_for_white`
* `weak_for_black`
* `strong_for_black`
* `is_hole_for_white`
* `is_hole_for_black`

#### Definitions (v1, frozen)

* **Hole:** square that is pawn-uncontestable *and* controlled more by the opponent.
* **Weak/Strong:** derived from control differential, pawn contestability, and stability — **engine-free**.

#### Artifacts

* JSON Schema: `schemas/SquareMapFeaturesV1.json`
* Pydantic model: `models/structures/square_map_v1.py`
* Extractor: `src/renacechess/features/square_map.py`

---

### 3️⃣ Context Bridge vNext

#### Description

Extend the existing LLM Context Bridge payload to include **structural cognition**, enabling grounded, GM-level narrative without hallucination.

#### Additions

* Embed `PerPieceFeaturesV1`
* Embed `SquareMapFeaturesV1`
* Add semantic labels suitable for narrative seeding:

  * “dominated piece”
  * “hole on d5”
  * “overextended pawn”
  * “key defender”

#### Constraint

* Context Bridge remains **read-only** with respect to policy.
* No behavioral feedback loops.

---

### 4️⃣ Structural Cognition Contract (NEW)

#### Description

A **versioned constitutional document** defining what “structural cognition” means in RenaceCHESS.

#### Must Specify

* Piece indexing and identity rules
* Square-map semantics and invariants
* Determinism guarantees
* Backward-compatibility rules
* Explicit prohibition on behavioral impact at this layer

#### Artifact

* `docs/contracts/StructuralCognitionContract_v1.md`

This document is **authoritative** for all future cognition layers (M12+).

---

### 5️⃣ Golden FEN Test Set

#### Description

A small, curated set of FEN positions used to lock feature semantics.

#### Requirements

* 3–5 FENs covering:

  * holes / weak squares
  * dominated pieces
  * pawn structure tension
  * king defense roles
* For each FEN:

  * assert specific piece features
  * assert specific square-map cells
* Tests must be deterministic and stable.

#### Artifacts

* `tests/fixtures/fens_m11.json`
* `tests/test_per_piece_features_v1.py`
* `tests/test_square_map_features_v1.py`

---

## 🧪 Validation & CI Requirements

### Tests

* Unit tests for both extractors
* Invariant tests (slot count, ordering, determinism)
* Golden FEN assertions

### CI Rules

* No coverage regressions (existing M10 rules apply)
* New code must meet project coverage thresholds
* No schema drift without version bump

---

## 🔐 Governance & Audit Posture

* No eval math changes
* No training changes
* No runtime engine dependencies
* No weakening of CI gates
* Fully additive, reversible via feature flags if needed

M11 must be **audit-defensible** as a structural-only expansion.

---

## ✅ Exit Criteria

M11 is complete when:

* All schemas are versioned and validated
* Extractors produce deterministic output
* Context Bridge vNext emits new fields
* Golden FEN tests pass
* CI is green with no exceptions
* Structural Cognition Contract is approved and committed

---

## 🧭 Authorized Follow-On Work

After M11 closure:

* **M12:** First bounded personality module (pawn-mobility / space restriction)
* **M13:** Coaching UX, narrative tracing, or additional personalities

---

## 🏁 Final Statement

**M11 completes the RenaceCHESS PoC by freezing the cognitive substrate.**
All future intelligence layers build *on top*, not *inside*, this milestone.

---

If you’d like, next I can:

* generate the **Cursor clarifying-questions prompt**, or
* draft the **StructuralCognitionContract_v1.md**, or
* sketch the **PerPieceFeaturesV1 JSON schema** in full detail.

Just say the word.
