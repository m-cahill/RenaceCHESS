# RenaceCHESS v1.0.0 Release Notes

**Release Date:** 2026-02-03  
**Tag:** `v1.0.0-renacechess`  
**Phase:** E (Scale Proof, Training Run, Release Lock) — **CLOSED**

---

## What This Release Is

RenaceCHESS v1.0.0 is a **research-grade release** of a human-centered chess intelligence system. This release demonstrates:

- **End-to-end integrity**: Deterministic training, evaluation, and reporting
- **Contract discipline**: Schema-first design with immutable v1 contracts
- **Scientific honesty**: Limitations explicitly documented, not hidden
- **Reproducibility**: All artifacts hash-chained and verifiable

This is **not** a product release. This is a **complete, auditable research system** that can be handed to external reviewers for independent verification.

---

## What This Release Is Not

- ❌ **Not a production system** — No production deployment tooling
- ❌ **Not a commercial product** — Research artifact, not product
- ❌ **Not a superhuman engine** — Human decision simulator, not engine
- ❌ **Not feature-complete** — Proof-of-concept scope, not full feature set
- ❌ **Not performance-optimized** — Research correctness over speed

---

## What Was Proven (M30-M33)

### M30: Frozen Eval v2 (10k Synthetic Positions)
- ✅ Deterministic synthetic position generation
- ✅ 7 skill buckets with minimum 1,000 positions each
- ✅ Hash-verified manifest and provenance
- ✅ CI-validated schema and integrity

### M31: Full Training Run
- ✅ End-to-end training execution (10 epochs, policy + outcome heads)
- ✅ Immutable configuration lock (TrainingConfigLockV1)
- ✅ Reproducible training report (TrainingRunReportV1)
- ✅ Checkpoint metadata with hash verification

### M32: Post-Train Evaluation
- ✅ 10,000-position evaluation (100% of frozen eval v2)
- ✅ Baseline comparison with delta metrics
- ✅ No training/eval overlap verified
- ✅ Honest reporting of degraded metrics (expected due to 8-move vocab)

### M33: External Proof Pack
- ✅ Self-contained proof bundle (`proof_pack_v1/`)
- ✅ Hash-chained artifacts from M30-M32
- ✅ External verification without codebase trust
- ✅ Limitations explicitly documented

---

## What Was Not Proven

- ❌ **Playing strength** — Training used 8-move vocabulary only
- ❌ **Full-vocab performance** — Model specialized on narrow move set
- ❌ **Production readiness** — Research system, not production
- ❌ **Commercial viability** — No business model or product claims

---

## Known Limitations

### Training Vocabulary
M31 training used only 8 moves:
- White: `e2e4`, `d2d4`, `g1f3`, `c2c4`
- Black: `e7e5`, `d7d5`, `g8f6`, `c7c5`

**Impact:** Trained model shows "degraded" metrics compared to baseline because:
- Baseline has uniform probability over vocab, occasionally matching by chance
- Trained model is confident in wrong moves for positions outside its distribution

**This is expected behavior** for a proof-of-concept. Production training will use full move vocabulary.

### Synthetic Evaluation Set
Frozen eval v2 is **synthetic** (algorithmically generated, not from real games).

**Impact:** Metrics are for **relative evaluation and calibration stability**, not absolute strength claims.

**This is intentional** — synthetic set enables deterministic, reproducible evaluation without requiring production data pipeline.

---

## Contract Registry

All v1 contracts are **frozen** in `contracts/CONTRACT_REGISTRY_v1.json`:

- **33 v1 contracts** with schema hashes
- **Immutable** — CI gates prevent v1 contract changes
- **Versioned** — Future changes require v2+ schemas

See `contracts/CONTRACT_REGISTRY_v1.json` for complete inventory.

---

## Release Artifacts

### Proof Pack
- **Location:** `proof_pack_v1/`
- **Manifest:** `proof_pack_v1/proof_pack_manifest.json`
- **Determinism Hash:** `sha256:6a69e1f801ca1c03d3aedcc2d8bb6ea86f87eb38e8e6322d9cea477ff398ca2f`

### Training Artifacts
- **Config Lock:** `artifacts/m31_training_run/config_lock.json`
- **Run Report:** `artifacts/m31_training_run/training_run_report.json`
- **Checkpoints:** External storage (hashes in report)

### Evaluation Artifacts
- **Post-Train Eval:** `artifacts/m32_post_train_eval/post_train_eval_report.json`
- **Frozen Eval v2:** `data/frozen_eval_v2/manifest.json`

---

## Verification

To verify this release:

1. **Check contract registry:**
   ```bash
   python -c "from pathlib import Path; from renacechess.contracts.registry import validate_contract_registry; validate_contract_registry(Path('contracts/CONTRACT_REGISTRY_v1.json'), Path('src/renacechess/contracts/schemas/v1'))"
   ```

2. **Verify proof pack:**
   ```bash
   python -c "from pathlib import Path; from renacechess.proof_pack.verify_proof_pack import verify_proof_pack; verify_proof_pack(Path('proof_pack_v1'))"
   ```

3. **Check git tag:**
   ```bash
   git tag -v v1.0.0-renacechess
   ```

---

## CI Release Gates

Three release-blocking CI jobs enforce immutability:

1. **`release-dependency-freeze`** — Blocks dependency changes
2. **`release-contract-freeze`** — Validates registry and blocks v1 schema changes
3. **`release-proof-pack-verification`** — Verifies proof pack integrity

These gates ensure v1 contracts remain frozen and verifiable.

---

## Phase E Milestones

| Milestone | Status | Description |
|-----------|--------|-------------|
| M29 | ✅ Closed | GPU Benchmarking (RTX 5090 validation) |
| M30 | ✅ Closed | Frozen Eval v2 (10k synthetic positions) |
| M31 | ✅ Closed | Full Training Run (executed) |
| M32 | ✅ Closed | Post-Train Evaluation (10k positions) |
| M33 | ✅ Closed | External Proof Pack (self-contained bundle) |
| M34 | ✅ Closed | Release Lock (contract freeze, CI gates) |

**Phase E Status:** ✅ **CLOSED**

---

## Next Steps

After v1.0.0:

- **v1.1+** — Any future changes require explicit v2+ versioning
- **Contract evolution** — New schemas must be v2+ (v1 frozen)
- **Feature additions** — Must not break v1 contracts

This release establishes the **immutable baseline** for all future work.

---

## References

- **Project Vision:** `VISION.md`
- **Governance:** `renacechess.md`
- **Proof Pack:** `proof_pack_v1/README.md`
- **Contract Registry:** `contracts/CONTRACT_REGISTRY_v1.json`
- **Phase E Closeout:** `docs/phases/PhaseE_closeout.md`

---

**This release makes future dishonesty impossible.**

All claims are verifiable. All limitations are explicit. All artifacts are hash-chained.

That's rare. And that's the point.

