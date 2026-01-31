# Checkpoint Publication Standard

**Version:** 1.0.0  
**Status:** 📋 DEFINED (no checkpoints published in M14)  
**Milestone:** M14 — TRAIN-PACK-001  
**Last Updated:** 2026-01-31

---

## Purpose

This document defines the **standard requirements for publishing RenaceCHESS training checkpoints**. It establishes naming conventions, required metadata, artifact requirements, and verification procedures.

**Important:** M14 establishes the publication standard only. No checkpoints are produced or published as part of M14.

---

## 1. Naming Convention

### 1.1 Checkpoint File Names

Checkpoint files MUST follow this naming pattern:

```
{model_type}-v{major}.{minor}.{patch}-{dataset_digest}-{timestamp}.pt
```

**Components:**

| Component | Description | Example |
|-----------|-------------|---------|
| `model_type` | Model identifier (lowercase, hyphenated) | `policy`, `outcome-head` |
| `v{major}.{minor}.{patch}` | Model architecture version | `v1.0.0` |
| `dataset_digest` | First 8 chars of dataset manifest digest | `a1b2c3d4` |
| `timestamp` | ISO 8601 date (YYYYMMDD) | `20260131` |

**Examples:**

```
policy-v1.0.0-a1b2c3d4-20260131.pt
outcome-head-v1.0.0-5f6e7d8c-20260201.pt
```

### 1.2 Metadata File Names

Metadata files MUST accompany checkpoints with the same base name:

```
{checkpoint_name}.metadata.json
```

**Example:**

```
policy-v1.0.0-a1b2c3d4-20260131.pt
policy-v1.0.0-a1b2c3d4-20260131.metadata.json
```

---

## 2. Required Metadata

Every published checkpoint MUST include a metadata file with the following fields:

### 2.1 Mandatory Fields

```json
{
  "schemaVersion": "1.0.0",
  "modelType": "BaselinePolicyV1",
  "modelVersion": "1.0.0",
  "checkpointName": "policy-v1.0.0-a1b2c3d4-20260131.pt",
  "checkpointHash": "sha256:abc123...",
  "createdAt": "2026-01-31T12:00:00Z",
  "training": {
    "epochs": 10,
    "batchSize": 32,
    "learningRate": 0.001,
    "seed": 42,
    "totalSteps": 100000,
    "finalLoss": 0.456
  },
  "dataset": {
    "manifestPath": "data/manifest.json",
    "manifestDigest": "sha256:def456...",
    "totalRecords": 500000,
    "trainRecords": 425000
  },
  "frozenEval": {
    "manifestPath": "data/frozen_eval_manifest.json",
    "manifestHash": "sha256:789abc...",
    "exclusionVerified": true
  },
  "environment": {
    "pythonVersion": "3.12.1",
    "torchVersion": "2.2.0+cu121",
    "device": "cuda:0 (NVIDIA RTX 5090)"
  },
  "evaluation": {
    "reportPath": "eval/policy-v1.0.0-a1b2c3d4-eval.json",
    "frozenEvalAccuracy": 0.423,
    "frozenEvalNLL": 1.234
  },
  "determinism": {
    "seedFixed": true,
    "reproducible": true,
    "reproductionInstructions": "See training/configs/policy_v1.0.0.yaml"
  }
}
```

### 2.2 Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `schemaVersion` | string | Metadata schema version |
| `modelType` | string | Model class name |
| `modelVersion` | string | Model architecture version |
| `checkpointName` | string | Filename of checkpoint |
| `checkpointHash` | string | SHA-256 hash of checkpoint file |
| `createdAt` | string | ISO 8601 timestamp |
| `training.*` | object | Training hyperparameters and results |
| `dataset.*` | object | Dataset information |
| `frozenEval.*` | object | Frozen eval exclusion verification |
| `environment.*` | object | Training environment details |
| `evaluation.*` | object | Evaluation results on frozen eval set |
| `determinism.*` | object | Reproducibility information |

---

## 3. Required Artifacts

A complete checkpoint publication MUST include:

### 3.1 Core Artifacts

| Artifact | Required | Description |
|----------|----------|-------------|
| `{name}.pt` | ✅ Yes | PyTorch model weights |
| `{name}.metadata.json` | ✅ Yes | Checkpoint metadata |
| `{name}.eval.json` | ✅ Yes | Frozen eval report |

### 3.2 Optional Artifacts

| Artifact | Required | Description |
|----------|----------|-------------|
| `{name}.config.yaml` | ⚪ Optional | Training configuration used |
| `{name}.training_log.json` | ⚪ Optional | Per-epoch training metrics |
| `{name}.optimizer.pt` | ⚪ Optional | Optimizer state (for resumption) |

---

## 4. Evaluation Requirements

### 4.1 Mandatory Evaluation

Every published checkpoint MUST be evaluated on the **frozen eval set** before publication:

```bash
renacechess eval run \
    --manifest <frozen_eval_manifest> \
    --policy learned:<checkpoint_path> \
    --output <eval_report.json>
```

### 4.2 Required Metrics

The evaluation report MUST include:

| Metric | Description |
|--------|-------------|
| Accuracy | Overall move prediction accuracy |
| Top-5 Accuracy | Move in top-5 predictions |
| NLL | Negative log-likelihood |
| Calibration | Calibration error (ECE) |
| Per-Bucket Metrics | Metrics by skill/time bucket |

### 4.3 Evaluation Report Format

```json
{
  "schemaVersion": "v5",
  "evaluatedAt": "2026-01-31T12:00:00Z",
  "checkpointPath": "path/to/checkpoint.pt",
  "frozenEvalManifest": "path/to/frozen_eval_manifest.json",
  "metrics": {
    "accuracy": 0.423,
    "top5Accuracy": 0.678,
    "nll": 1.234,
    "calibrationError": 0.05
  },
  "conditionedMetrics": {
    "bySkillBucket": { ... },
    "byTimePressure": { ... }
  }
}
```

---

## 5. Determinism Requirements

### 5.1 Reproducibility Standard

Published checkpoints MUST be reproducible:

1. **Fixed Seeds**: Training must use explicit random seeds
2. **Deterministic Operations**: PyTorch deterministic mode enabled
3. **Configuration Capture**: Exact training configuration recorded
4. **Environment Capture**: Python, PyTorch, CUDA versions recorded

### 5.2 Reproduction Verification

Before publication, verify reproducibility:

```bash
# Train with same config twice
python -m renacechess.models.training --config training.yaml --output run1/
python -m renacechess.models.training --config training.yaml --output run2/

# Compare final weights (should be identical)
diff run1/model.pt run2/model.pt
```

---

## 6. Versioning Rules

### 6.1 When to Bump Versions

| Change Type | Version Component | Example |
|-------------|-------------------|---------|
| Architecture change | Major | v1.0.0 → v2.0.0 |
| Feature addition | Minor | v1.0.0 → v1.1.0 |
| Training fix/retrain | Patch | v1.0.0 → v1.0.1 |

### 6.2 Version Compatibility

- **Major**: Breaking changes; not compatible with previous loaders
- **Minor**: Additive changes; backward compatible
- **Patch**: No interface changes; drop-in replacement

---

## 7. Publication Checklist

Before publishing a checkpoint, verify:

- [ ] Checkpoint file exists and is loadable
- [ ] Metadata file is complete and valid JSON
- [ ] Frozen eval exclusion verified (`exclusionVerified: true`)
- [ ] Evaluation report generated on frozen eval set
- [ ] Checksum matches recorded hash
- [ ] Training configuration is archived
- [ ] Reproducibility test passed
- [ ] No PoC semantics altered (M14+ requirement)

---

## 8. Storage and Distribution

### 8.1 Local Storage

Checkpoints should be stored in a standard directory structure:

```
checkpoints/
  policy/
    policy-v1.0.0-a1b2c3d4-20260131.pt
    policy-v1.0.0-a1b2c3d4-20260131.metadata.json
    policy-v1.0.0-a1b2c3d4-20260131.eval.json
  outcome-head/
    outcome-head-v1.0.0-5f6e7d8c-20260201.pt
    outcome-head-v1.0.0-5f6e7d8c-20260201.metadata.json
    outcome-head-v1.0.0-5f6e7d8c-20260201.eval.json
```

### 8.2 Remote Distribution (Future)

When checkpoints are published remotely:

1. All files must be hosted together
2. Checksums must be verifiable
3. Metadata must include download URLs
4. Version manifest must be maintained

---

## 9. Governance

### 9.1 Publication Authority

Checkpoint publication requires:

1. Passing CI (no failing tests)
2. Frozen eval report attached
3. Reproducibility verification
4. Review approval (if applicable)

### 9.2 Deprecation

To deprecate a checkpoint:

1. Add `deprecated: true` to metadata
2. Add `deprecationReason` field
3. Point to replacement checkpoint
4. Do NOT delete deprecated checkpoints

---

## 10. Examples

### 10.1 Complete Publication Set

```
checkpoints/policy/
├── policy-v1.0.0-a1b2c3d4-20260131.pt            # Model weights
├── policy-v1.0.0-a1b2c3d4-20260131.metadata.json # Full metadata
├── policy-v1.0.0-a1b2c3d4-20260131.eval.json     # Eval report
└── policy-v1.0.0-a1b2c3d4-20260131.config.yaml   # Training config
```

### 10.2 Minimal Valid Metadata

```json
{
  "schemaVersion": "1.0.0",
  "modelType": "BaselinePolicyV1",
  "modelVersion": "1.0.0",
  "checkpointName": "policy-v1.0.0-a1b2c3d4-20260131.pt",
  "checkpointHash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "createdAt": "2026-01-31T12:00:00Z",
  "training": {
    "epochs": 10,
    "seed": 42
  },
  "dataset": {
    "manifestDigest": "sha256:abc123..."
  },
  "frozenEval": {
    "exclusionVerified": true
  },
  "evaluation": {
    "frozenEvalAccuracy": 0.423
  },
  "determinism": {
    "reproducible": true
  }
}
```

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-31 | 1.0.0 | Initial standard created (M14) |

---

**Standard Defined:** 2026-01-31  
**Status:** No checkpoints produced in M14 (definition only)

