# RenaceCHESS Evaluation Harness

This document describes the evaluation harness for policy providers over dataset manifests.

## Overview

The evaluation harness (`renacechess eval`) provides a deterministic, offline-first system for evaluating policy providers (baselines or models) over dataset manifests. It focuses on **policy validity metrics** rather than ground-truth accuracy, since dataset records represent decision contexts (positions) rather than decisions (moves).

## What Evaluation Does

The evaluation harness measures:

1. **Illegal Move Rate**: Percentage of records where the policy emits a move not in `legalMoves`
2. **Top-K Legal Coverage**: Whether the policy's top-K outputs intersect `legalMoves`
3. **Policy Entropy**: Shannon entropy of the policy's probability distribution (if applicable)
4. **Output Cardinality**: Number of unique moves emitted across the dataset
5. **Records Evaluated**: Total number of records processed

These metrics help characterize policy behavior, detect degenerate outputs, and verify determinism.

## What Evaluation Does NOT Do (M04 Scope)

The following are **explicitly deferred** to future milestones:

- **Ground-truth accuracy metrics**: Requires labeled records with `chosenMove` field (deferred to M05+)
- **Stockfish-based evaluation**: Engine dependency (deferred to M05+)
- **Lichess-style accuracy**: Engine-derived metrics (deferred to M05+)
- **Engine-vs-engine arenas**: SPRT harness (deferred to M05+)
- **Training loop**: Model training (out of scope for M04)

## Running Evaluation

### Basic Usage

```bash
renacechess eval run \
  --dataset-manifest <path-to-manifest.json> \
  --policy <policy-id> \
  --out <output-dir>
```

### Example

```bash
# Build a dataset first
renacechess dataset build \
  --pgn tests/data/sample.pgn \
  --out /tmp/dataset

# Run evaluation
renacechess eval run \
  --dataset-manifest /tmp/dataset/manifest.json \
  --policy baseline.first_legal \
  --out /tmp/eval_results
```

The evaluation report will be written to `eval_report.json` in the output directory.

## Policy Baseline IDs

M04 provides two baseline policy providers:

- **`baseline.first_legal`**: Deterministic baseline that always picks the first legal move (sorted alphabetically)
- **`baseline.uniform_random`**: Uniform random policy that selects from legal moves with equal probability (deterministic seeded RNG)

## Evaluation Report Format

The evaluation report (`eval_report.json`) conforms to the `eval_report.v1` schema and includes:

- **Schema version**: `"eval_report.v1"`
- **Dataset identity**: `datasetDigest` and `assemblyConfigHash` from manifest
- **Policy identifier**: Which policy was evaluated
- **Evaluation config hash**: Stable hash of evaluation configuration
- **Overall metrics**: Aggregated metrics across all records
- **Per-split metrics**: Metrics broken down by split (train/val/frozenEval) if applicable

### Metrics Structure

```json
{
  "recordsEvaluated": 1000,
  "illegalMoveRate": "0.0000",
  "topKLegalCoverage": {
    "top1": "100.0000",
    "top3": "100.0000"
  },
  "policyEntropy": {
    "mean": "3.4567",
    "stddev": null
  },
  "uniqueMovesEmitted": 50
}
```

## Determinism Guarantees

The evaluation harness provides **byte-stable outputs**:

- Same dataset manifest + same policy + same config → byte-identical report
- Deterministic seeded RNG for random policies (seed derived from dataset digest + policy ID + config hash)
- Fixed-decimal string formatting for all float metrics (ensures byte-stability)
- Canonical JSON serialization (sorted keys, no whitespace)

## Streaming Evaluation

The evaluation harness processes dataset shards **line-by-line** (streaming JSONL):

- No full dataset buffering required
- Memory-efficient for large datasets
- Processes shards in deterministic order (from manifest)

## CLI Options

### `renacechess eval run`

- `--dataset-manifest <path>` (required): Path to dataset manifest v2 (`manifest.json`)
- `--policy <id>` (required): Policy identifier (e.g., `baseline.uniform_random`)
- `--out <dir>` (required): Output directory (will write `eval_report.json`)
- `--max-records <n>` (optional): Maximum number of records to evaluate (default: no limit)
- `--created-at <iso>` (optional, testing only): Override creation timestamp (ISO 8601 format)

## Error Handling

The evaluation harness fails fast on:

- Missing dataset manifest
- Schema version mismatch (only v2 manifests supported in M04)
- Unknown policy ID
- Missing shard files
- Invalid dataset records

## Future Work (Post-M04)

- **M05+**: Ground-truth accuracy metrics (requires labeled records)
- **M05+**: Stockfish-based evaluation and lichess-style accuracy
- **M05+**: Engine-vs-engine arenas and SPRT harness
- **M05+**: Model training integration

## See Also

- [Dataset Format](DATASETS.md) - Dataset structure and manifest format
- [Governance](GOVERNANCE.md) - Milestone workflow and governance

