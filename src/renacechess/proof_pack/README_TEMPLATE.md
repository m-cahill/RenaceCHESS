# RenaceCHESS External Proof Pack v1

**Project:** RenaceCHESS — Cognitive Human Evaluation & Skill Simulation  
**Phase:** E (Scale Proof, Training Run, Release Lock)  
**Milestones Included:** M30, M31, M32  
**Generated:** {generated_date}

---

## Executive Summary

This proof pack demonstrates RenaceCHESS's end-to-end integrity, determinism, and scientific honesty through a complete training and evaluation cycle. The pack contains all artifacts, schemas, and hashes necessary for independent verification without requiring trust in the codebase.

**What This Pack Proves:**

- **Pipeline Integrity:** Training → evaluation → reporting is end-to-end consistent
- **Contract Discipline:** Schema-first design survived real execution
- **Scientific Honesty:** Degraded results are reported, not hidden or reframed
- **Reproducibility:** All artifacts are hash-chained and replayable

**What This Pack Does NOT Prove:**

- Chess playing strength (training vocabulary too constrained)
- Full-vocab performance (only {move_vocab_size} moves trained)
- Absolute model quality (synthetic eval set, not real games)

**Key Limitation:**

The training run used a constrained vocabulary of {move_vocab_size} moves. This causes expected degradation in evaluation metrics compared to baseline because the trained model is specialized to a narrow move distribution, while the baseline has uniform probability over the vocabulary and occasionally matches correct moves by chance. The infrastructure validation objective was achieved; production training will use full move vocabulary.

---

## Technical Verification Guide

### Manifest Structure

The proof pack contains:

- `proof_pack_manifest.json` — Top-level manifest (ExternalProofPackV1 schema)
- `frozen_eval/` — Frozen evaluation set artifacts (M30)
- `training/` — Training artifacts (M31)
- `evaluation/` — Post-training evaluation artifacts (M32)
- `schemas/` — JSON schemas required to validate all included artifacts

### Hash Verification

All artifacts include SHA-256 hashes. To verify integrity:

1. **Recompute hash of each artifact:**
   ```bash
   sha256sum frozen_eval/manifest.json
   sha256sum training/config_lock.json
   # ... etc
   ```

2. **Compare against manifest:**
   - Check `artifacts.frozenEval.manifestHash`
   - Check `artifacts.training.configLockHash`
   - Check `hashChain` section for causal relationships

3. **Verify manifest determinism hash:**
   - Load `proof_pack_manifest.json`
   - Remove `determinismHash` field
   - Compute SHA-256 of canonical JSON
   - Compare against `determinismHash` in manifest

### Schema Validation

All JSON artifacts validate against their respective schemas:

- `frozen_eval/manifest.json` → `schemas/frozen_eval_manifest.v2.schema.json`
- `training/config_lock.json` → `schemas/training_config_lock.v1.schema.json`
- `training/training_run_report.json` → `schemas/training_run_report.v1.schema.json`
- `evaluation/post_train_eval_report.json` → `schemas/post_train_eval_report.v1.schema.json`
- `proof_pack_manifest.json` → `schemas/external_proof_pack.v1.schema.json`

Use any JSON Schema validator (e.g., `ajv`, `jsonschema` Python library) to validate.

### Checkpoint Files

**Important:** Checkpoint files (`.pt` model files) are **NOT included** in this proof pack. They are stored externally. The manifest includes:

- SHA-256 hashes of checkpoint files
- File sizes
- Expected filenames

To verify checkpoints (if you have access):

1. Locate checkpoint files externally
2. Compute SHA-256 hash
3. Compare against `artifacts.training.checkpoints.policy.hash` or `artifacts.training.checkpoints.outcome.hash`

### Limitations (Technical)

**Training Vocabulary Constraint:**

Training used a constrained vocabulary of {move_vocab_size} moves. This causes expected degradation in evaluation metrics compared to baseline because:

1. The trained model is specialized to a narrow move distribution
2. The baseline has uniform probability over the vocabulary and occasionally matches correct moves by chance
3. The frozen eval v2 set contains positions requiring many moves outside the training vocabulary

**Synthetic Evaluation Set:**

Frozen eval v2 is a synthetic, chess-valid evaluation set generated algorithmically from curated FEN seeds. It is intended for relative evaluation and calibration stability, not absolute strength claims. All positions are chess-valid but not drawn from real game data.

**Scope Boundaries:**

This proof pack demonstrates infrastructure correctness and reproducibility. It does not demonstrate:

- Chess playing strength (vocabulary too constrained)
- Full-vocab performance (only {move_vocab_size} moves trained)
- Absolute model quality (synthetic eval set, not real games)

---

## Verification Commands

### Python Verification

```python
from pathlib import Path
from renacechess.proof_pack.verify_proof_pack import verify_proof_pack

proof_pack_dir = Path("proof_pack_v1")
is_valid, errors = verify_proof_pack(proof_pack_dir)

if is_valid:
    print("✅ Proof pack verification passed")
else:
    print("❌ Proof pack verification failed:")
    for error in errors:
        print(f"  - {error}")
```

### Manual Hash Verification

```bash
# Verify frozen eval manifest
sha256sum frozen_eval/manifest.json
# Compare against artifacts.frozenEval.manifestHash in manifest

# Verify training config lock
sha256sum training/config_lock.json
# Compare against artifacts.training.configLockHash in manifest

# Verify all artifacts similarly...
```

---

## Artifact Provenance

- **M30 (Frozen Eval v2):** Synthetic 10,000-position evaluation set
- **M31 (Training Run):** Full training execution (10 epochs, policy + outcome heads)
- **M32 (Post-Train Eval):** Evaluation of trained checkpoints against frozen eval v2

All artifacts are hash-chained to prove causal relationships and prevent tampering.

---

## Contact

For questions about this proof pack, refer to:
- Project documentation: `docs/`
- Milestone plans: `docs/milestones/PhaseE/M30/`, `M31/`, `M32/`, `M33/`
- Source code: `src/renacechess/proof_pack/`

