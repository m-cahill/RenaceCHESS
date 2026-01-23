# RenaceCHESS Dataset Format

This document describes the dataset format, build process, and deterministic rules for RenaceCHESS.

## Overview

RenaceCHESS datasets are collections of chess position evaluations stored in **JSON Lines (JSONL)** format. Each line contains a complete **Context Bridge payload** representing a single position with its human-conditioned move probabilities, WDL estimates, and difficulty metrics.

## Dataset Structure

A dataset consists of:

1. **Shard files** (`shards/shard_XXX.jsonl`): JSONL files containing position records
2. **Manifest file** (`manifest.json`): Metadata describing the dataset, shard references, and split assignments

### Shard Format

Each shard is a **JSON Lines** file where:
- Each line is a complete JSON object (Context Bridge payload)
- Lines are newline-delimited
- No trailing spaces
- Canonical JSON formatting (sorted keys, no whitespace)

Example shard line:
```json
{"position":{"fen":"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1","sideToMove":"white","legalMoves":["a2a3","a2a4",...]},"conditioning":{"skillBucket":"1200-1400","timePressureBucket":"NORMAL","timeControlClass":"blitz"},"policy":{"topMoves":[{"uci":"e2e4","p":0.45},...],"entropy":3.2,"topGap":0.15},"humanWDL":{"pre":{"w":0.55,"d":0.15,"l":0.30},"postByMove":{...}},"hdi":{"value":0.65,"components":{...}},"narrativeSeeds":[],"meta":{"schemaVersion":"v1","generatedAt":"2024-01-01T12:00:00","inputHash":"..."}}
```

### Manifest Format

The manifest is a JSON file conforming to the Dataset Manifest schema (v1):

```json
{
  "schemaVersion": "v1",
  "createdAt": "2024-01-01T12:00:00",
  "shardRefs": [
    {
      "shardId": "shard_000",
      "hash": "sha256-hex-hash",
      "path": "shards/shard_000.jsonl"
    }
  ],
  "filterConfigHash": "sha256-hex-hash",
  "splitAssignments": {
    "train": ["shard_000"],
    "val": ["shard_000"],
    "frozenEval": ["shard_000"]
  }
}
```

## Building Datasets

### CLI Command

```bash
renacechess dataset build \
  --pgn <file-or-dir> \
  --out <output-dir> \
  [--max-games N] \
  [--max-positions N] \
  [--start-ply X] \
  [--end-ply Y]
```

**Arguments:**
- `--pgn`: Path to PGN file or directory (can be specified multiple times)
- `--out`: Output directory for shards and manifest
- `--max-games`: Maximum number of games to process (global limit across all inputs)
- `--max-positions`: Maximum number of positions to process (global limit)
- `--start-ply`: Start processing from this ply number (inclusive, default: 0)
- `--end-ply`: Stop processing at this ply number (exclusive)

**Example:**
```bash
renacechess dataset build \
  --pgn games/2024/ \
  --out datasets/2024-jan/ \
  --max-positions 10000 \
  --start-ply 2 \
  --end-ply 50
```

### Programmatic API

```python
from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig
from pathlib import Path
from datetime import datetime

config = DatasetBuildConfig(
    pgn_paths=[Path("games/sample.pgn")],
    output_dir=Path("datasets/sample/"),
    max_positions=1000,
    start_ply=0,
    end_ply=40,
)

# Use frozen timestamp for deterministic outputs
build_dataset(config, generated_at=datetime(2024, 1, 1, 12, 0, 0))
```

## Deterministic Rules

### File Processing Order

1. **PGN files are processed in sorted order** (lexicographic by path)
2. **Games within a file are processed in file order**
3. **Positions within a game are processed by increasing ply number**

### Position Filtering

- `start_ply`: Applied uniformly to all games (positions before this ply are skipped)
- `end_ply`: Applied uniformly to all games (positions at or after this ply are skipped)
- Limits (`max_games`, `max_positions`) apply globally across all inputs

### Split Assignment

Splits are assigned deterministically based on a composite record key:

```python
record_key = f"{fen}:{ply}"
split_bucket = int(sha256(record_key)[:8], 16) % 100
```

**Split allocation:**
- `0-4` → `frozenEval` (5%)
- `5-14` → `val` (10%)
- `15-99` → `train` (85%)

### Shard Naming

Shards use sequential deterministic naming:
- `shard_000.jsonl`
- `shard_001.jsonl` (future multi-shard support)

### Hash Computation

- **Shard hash**: SHA-256 of the complete shard file content
- **Filter config hash**: SHA-256 of canonical JSON representation of build configuration

## Reproducibility

To reproduce a dataset exactly:

1. Use the same PGN input files (same paths, same content)
2. Use the same build configuration (same CLI arguments or config dict)
3. Use a frozen timestamp (or ensure `generated_at` is identical)

The same inputs + same config + same timestamp → **byte-identical outputs**.

## Schema Validation

Every record in a shard validates against the **Context Bridge schema (v1)**. The manifest validates against the **Dataset Manifest schema (v1)**.

Validation is enforced in tests and can be performed manually:

```python
import json
import jsonschema

# Validate a shard record
schema = json.load(open("src/renacechess/contracts/schemas/v1/context_bridge.schema.json"))
with open("datasets/sample/shards/shard_000.jsonl") as f:
    for line in f:
        if line.strip():
            record = json.loads(line)
            jsonschema.validate(record, schema)
```

## Future Enhancements

- Multi-shard strategies (size-based, count-based rollover)
- Per-game ply filtering
- Additional split strategies
- Compression support
- Streaming dataset readers

