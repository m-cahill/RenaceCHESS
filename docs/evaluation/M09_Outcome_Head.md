# M09: Human Outcome Head (W/D/L) v1 Specification

## Overview

The Human Outcome Head v1 is a minimal, interpretable learned model that predicts **Win / Draw / Loss probabilities** for human players conditioned on position, skill level, and time pressure. This milestone completes the **human evaluation triad**:

| Signal | Status |
|--------|--------|
| Human move prediction | ✅ M08 |
| Human difficulty (HDI) | ✅ M07 |
| **Human outcome likelihood (W/D/L)** | ✅ **M09** |

## Architecture

### Model Design

**OutcomeHeadV1** is a **single linear layer** (logistic regression):

```
features → Linear → 3 logits (W/D/L)
```

**Input Features:**
- FEN encoding (hashed, same as M08 policy baseline)
- Skill bucket (categorical, 8 categories)
- Time control class (categorical, 5 categories)

**Output:**
- 3 logits → softmax → `{w, d, l}` probabilities

**Constraints:**
- ❌ No hidden layers
- ❌ No HDI as input feature (avoids circular dependency)
- ❌ No hyperparameter tuning
- ❌ No joint training with policy

### Feature Representation

The outcome head uses **exactly the same feature representation** as the M08 policy baseline:

- FEN hash vocabulary: 10,000
- Skill bucket vocabulary: 8 (7 buckets + unknown)
- Time control vocabulary: 5 (bullet/blitz/rapid/classical/unknown)
- Hidden dimension: 128 (for embeddings)

This ensures the outcome head is a **parallel consumer** of the same features, not a refactor.

## Training

### Loss Function

**Training:** Cross-entropy loss (standard 3-class classification)

**Evaluation Metrics:**
- Cross-entropy (log loss)
- Brier score
- Expected Calibration Error (ECE) with 10-bin equal-width calibration

### Training Data

**Source:** M01–M03 JSONL shards (same as policy training)

**Exclusions:**
- Frozen eval records (explicitly excluded)
- Records without game results
- Non-train split records

**Labels:**
- Derived from game result metadata (from mover's perspective)
- Mapped to class indices: win=0, draw=1, loss=2

### Determinism

- Fixed random seed (default: 42)
- Deterministic dataloader order (no shuffle)
- Same inputs → identical outputs

### Training Command

```bash
renacechess model train-outcome-head \
  --dataset-manifest manifest.json \
  --frozen-eval-manifest frozen_eval.json \
  --out output_dir \
  --epochs 10 \
  --seed 42
```

## Evaluation

### Calibration

**ECE Computation:**
- 10 bins, equal-width
- Range: [0.0, 1.0)
- Strategy: Aggregate (not per-class)
- Metric: Expected Calibration Error

**Determinism Rules:**
- Fixed bin edges
- Stable ordering
- Edge case: 1.0 goes in last bin

### Integration with Evaluation Harness

The outcome head integrates with the existing evaluation harness:

```bash
renacechess eval run \
  --dataset-manifest manifest.json \
  --policy learned.v1 \
  --model-path policy_model.pt \
  --outcome-head-path outcome_head_dir \
  --conditioned-metrics \
  --frozen-eval-manifest frozen_eval.json \
  --out output_dir
```

**Requirements:**
- `--outcome-head-path` must point to directory containing:
  - `outcome_head_v1.pt` (model weights)
  - `outcome_head_v1_metadata.json` (metadata)

**Frozen Eval Enforcement:**
- Outcome evaluation **requires** frozen eval manifest (same as conditioned metrics)
- Training **never** touches frozen eval

## Evaluation Report v5

### Schema Behavior

**Conditional, Additive:**
- `outcome_metrics` present **only if** outcome head is used
- v4 reports still validate unchanged
- v5 schema allows absence of outcome section

**Structure:**
```json
{
  "schemaVersion": "eval_report.v5",
  "outcomeMetrics": {
    "totalPredictions": 1000,
    "crossEntropy": 0.523,
    "brierScore": 0.312,
    "ece": 0.089
  },
  "outcomeMetricsBySkill": {...},
  "outcomeMetricsByTimeControl": {...},
  "outcomeMetricsByTimePressure": {...}
}
```

### Backward Compatibility

- ✅ v3 reports still validate
- ✅ v4 reports still validate
- ✅ v5 reports without outcome metrics validate
- ✅ Presence of outcome metrics is optional

## HDI Integration

### Outcome Sensitivity Replacement

When an outcome head exists, HDI's outcome sensitivity component uses the **learned signal** instead of the proxy:

**Before (M07):**
- Outcome sensitivity: `entropy * (1 - topGap)` (proxy)
- Source: `"proxy"`

**After (M09):**
- Outcome sensitivity: Derived from outcome head predictions
- Source: `"outcome_head"`

**Note:** This replacement happens **during evaluation**, not during training. The outcome head does not use HDI as an input feature (avoids circular dependency).

## Scientific Limitations

### Human Data ≠ Optimal Play

The outcome head predicts **human outcomes**, not engine outcomes. This is intentional:

- Human players make mistakes
- Human outcomes reflect skill/time-conditioned reality
- Engine evaluation (Stockfish) is explicitly excluded

### Calibration Expectations

For M09 (minimal baseline):
- Calibration may not be perfect
- ECE < 0.2 is reasonable for a linear model
- Future milestones may improve calibration

## Model Artifacts

### File Naming

- Model weights: `outcome_head_v1.pt`
- Metadata: `outcome_head_v1_metadata.json`

### Metadata Contents

```json
{
  "model_type": "OutcomeHeadV1",
  "epochs": 10,
  "batch_size": 32,
  "learning_rate": 0.001,
  "seed": 42,
  "manifest_path": "...",
  "frozen_eval_manifest_path": "...",
  "loss_function": "CrossEntropyLoss"
}
```

## Exit Criteria

M09 is complete when:

- ✅ Outcome head can be trained locally
- ✅ Outcome probabilities are produced deterministically
- ✅ Outcome metrics evaluate cleanly on frozen eval
- ✅ Eval report v5 validates
- ✅ CI remains green
- ✅ No M08 or earlier contracts are weakened

## Future Work (Explicitly Out of Scope)

- ❌ Engine evaluation (Stockfish)
- ❌ Joint policy + outcome training
- ❌ Hyperparameter tuning
- ❌ Neural architecture experimentation
- ❌ Training in CI
- ❌ Dashboarding or visualization
- ❌ Elo recomputation

Any of the above requires an explicit future milestone.

## References

- **M08:** First Learned Human Policy Baseline
- **M07:** Human Difficulty Index (HDI) v1
- **M06:** Conditioned, Frozen Human Evaluation
- **VISION.md:** Project vision and PoC objectives

