# Personality Safety Contract v1.0

**Version:** 1.0  
**Status:** 🔒 FROZEN  
**Effective:** M15+  
**Last Updated:** 2026-01-31

---

## 1. Purpose

This contract defines **what a personality is, what it may do, and what it must never do** within RenaceCHESS.

Personalities enable **bounded behavioral variation** — style modulation that produces human-like diversity without corrupting correctness, legality, or base policy semantics.

---

## 2. Definitions

### 2.1 Personality

A **personality** is a deterministic transformation that:
- Takes a **base policy distribution** (from the learned human policy)
- Takes **structural context** (from M11 per-piece/square features)
- Takes **safety constraints** (envelope parameters)
- Produces a **modified policy distribution** within the allowed envelope

A personality is **NOT**:
- A new model or additional training
- An evaluation function override
- A move generator or legality checker
- A coaching or explanation system

### 2.2 Base Policy

The **base policy** is the learned human move probability distribution produced by `BaselinePolicyV1` or its successors. The base policy is the **ground truth** for human move prediction at a given skill/time bucket.

### 2.3 Safety Envelope

A **safety envelope** defines the bounded region within which a personality may operate. It includes:
- `top_k`: Maximum number of candidate moves considered
- `delta_p_max`: Maximum probability shift allowed per move
- `entropy_bounds`: Minimum and maximum allowed entropy
- `base_reachable`: Boolean flag ensuring base policy can be recovered

### 2.4 Structural Context

**Structural context** is the M11 feature set:
- `PerPieceFeaturesV1`: Per-piece mobility, tension, semantic flags
- `SquareMapFeaturesV1`: Square-level weak/strong/hole maps

Personalities may **read** structural context but may **never modify** it.

---

## 3. Allowed Interventions

A personality **MAY**:

| Intervention | Description | Constraint |
|--------------|-------------|------------|
| Re-rank moves | Change relative ordering within `top_k` | Must preserve legality |
| Shift probability mass | Increase/decrease move probabilities | Within `delta_p_max` per move |
| Sharpen distribution | Reduce entropy (more decisive) | Above `entropy_min` |
| Soften distribution | Increase entropy (more uncertain) | Below `entropy_max` |
| Cite structural features | Use M11 features to inform shaping | Read-only access |

---

## 4. Forbidden Actions

A personality **MUST NEVER**:

| Forbidden Action | Rationale |
|------------------|-----------|
| Suggest illegal moves | Legality is upstream of personality |
| Invent novel moves | Personalities transform, never generate |
| Override base policy outside `top_k` | Prevents unbounded divergence |
| Modify structural context | Features are computed facts, not opinions |
| Access or modify evaluation scores | Personalities are policy-only |
| Produce non-deterministic output | Same inputs → same outputs always |
| Contaminate frozen eval | Training/personality must exclude frozen sets |
| Exceed `delta_p_max` for any move | Hard constraint, not soft |

---

## 5. Required Invariants

Every personality implementation **MUST** satisfy:

### 5.1 Determinism

```
∀ inputs I:
    personality.apply(I) == personality.apply(I)
```

Given identical inputs (base policy, context, constraints), the output must be byte-identical across invocations.

### 5.2 Base Policy Reachability

```
∃ constraint_set C where:
    personality.apply(base_policy, context, C) == base_policy
```

There must exist a configuration where the personality produces the unmodified base policy. This ensures personalities are **optional layers**, not mandatory transformations.

### 5.3 Legality Preservation

```
∀ moves M in personality_output:
    M ∈ legal_moves(position)
```

A personality can never introduce illegal moves.

### 5.4 Probability Conservation

```
∑ personality_output.probabilities == 1.0
```

Output must be a valid probability distribution.

### 5.5 Envelope Compliance

```
∀ moves M:
    |personality_output[M] - base_policy[M]| <= delta_p_max
```

No individual move may shift beyond the declared envelope.

---

## 6. Safety Envelope Parameters

### 6.1 Minimal Required Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `top_k` | int | Maximum candidate moves | 5 |
| `delta_p_max` | float | Max probability shift per move | 0.15 |
| `entropy_min` | float | Minimum output entropy | 0.5 |
| `entropy_max` | float | Maximum output entropy | 3.0 |
| `base_reachable` | bool | Require identity config exists | true |

### 6.2 Envelope Validation

Before any personality transformation, the envelope **MUST** be validated:
- All parameters within documented bounds
- No contradictory constraints (e.g., `entropy_min > entropy_max`)
- `base_reachable=true` unless explicitly documented otherwise

---

## 7. Personality Lifecycle

### 7.1 Definition Phase (M15)

- Contract established (this document)
- Interface defined (`PersonalityModuleV1`)
- Configuration schema created
- No implementations

### 7.2 Implementation Phase (M16+)

- Concrete personalities created
- Each personality must prove invariant compliance
- Regression tests required

### 7.3 Evaluation Phase (M18+)

- Style metrics computed
- Divergence from base policy measured
- Explainability via M11 features required

---

## 8. Architectural Constraints

### 8.1 Module Boundaries

The `personality/` module:
- **MAY** import from: `contracts/`, `features/`
- **MUST NOT** be imported by: `contracts/`, `eval/`, `features/`, `models/`

Personalities are **downstream consumers** of truth, never producers.

### 8.2 No Training Coupling

Personalities operate at **inference time only**. They must never:
- Participate in training loops
- Modify model weights
- Access gradients

---

## 9. Relationship to Other Contracts

| Contract | Relationship |
|----------|--------------|
| `StructuralCognitionContract_v1.md` | Personality reads M11 features (no modification) |
| `CONTRACT_INPUT_SEMANTICS.md` | Personality config follows alias-only dict semantics |
| Frozen Eval Manifest | Personality must never contaminate frozen sets |

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-31 | Initial release (M15) |

---

## 11. Contract Statement

> **Personalities are bounded style transformations — they modify probability mass within safe envelopes, preserve all invariants, and never corrupt base policy correctness or legality.**

This contract is **FROZEN** as of M15. Any modifications require a new version with explicit migration path.

---

**Contract Authority:** RenaceCHESS Governance  
**Enforcement:** CI + Code Review + Import-Linter

