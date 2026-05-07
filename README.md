# RenaceCHESS

**Not Another Chess Engine; it's a Cognitive Human Evaluation & Skill Simulation**

RenaceCHESS is a human-centered chess intelligence system that predicts what move a human of a given skill (and time pressure) is likely to play, estimates human win/draw/loss chances for that same skill level, and provides LLM-groundable context for real-time, natural-language coaching and broadcast narrative.

## Start Here

- New to the project? Read [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md).
- Contributing? Read [`CONTRIBUTING.md`](CONTRIBUTING.md).
- Looking for the documentation map? Read [`docs/DOCS_INDEX.md`](docs/DOCS_INDEX.md).
- Reviewing public-release boundaries? Read [`docs/release/PUBLIC_REPO_BOUNDARY.md`](docs/release/PUBLIC_REPO_BOUNDARY.md).

## Common Developer Shortcuts

If `make` is available:

```bash
make help
make verify
make test-fast
```

Without `make`, use the commands listed in [`CONTRIBUTING.md`](CONTRIBUTING.md).

## What This Project Is and Is Not

### This Project **Is**

- A **probabilistic human decision model**: Predicts human move choices conditioned on skill and time pressure
- A **skill-conditioned human outcome model**: Estimates human win/draw/loss probabilities (not engine self-play)
- A **context-grounding layer**: Turns probabilities into stable, structured payloads for LLM coaching/broadcast
- A **research-grade system**: Complete, auditable, reproducible research artifact (v1.0.0)

### This Project **Is Not**

- ❌ A new superhuman engine
- ❌ A replacement for Stockfish/Leela
- ❌ A purely "chatty" LLM chess coach (we explicitly avoid hallucination by grounding advice in calibrated probabilities)
- ❌ A production system (research artifact, not product)
- ❌ A commercial product (no business model or product claims)

See [VISION.md](VISION.md) for the complete project vision and [RELEASE_NOTES_v1.md](RELEASE_NOTES_v1.md) for v1.0.0 release details.

## Overview

The endgame is *not* "stronger-than-Stockfish." The endgame is a **human decision & difficulty simulator** that supports:

- Creator tooling (recaps, highlights, "why humans miss this")
- Coaching (skill/time-conditioned advice)
- "Chessmaster-style" controllable personalities (aggression/defense, material vs positional emphasis, concept attention like passed pawns/king safety) **without collapsing into "always play the engine #1 move."**

## Installation

```bash
# Install dependencies
pip install -e ".[dev]"
```

## Usage

### Generate Demo Payload

```bash
# Generate demo payload from PGN
python -m renacechess.cli demo --pgn tests/data/sample.pgn --out demo.json
```

### Build Dataset

```bash
# Build dataset from PGN files (backward compatible)
python -m renacechess.cli dataset build \
  --pgn tests/data/sample.pgn \
  --out datasets/sample/ \
  --shard-size 10000 \
  --max-positions 1000 \
  --start-ply 0 \
  --end-ply 40

# Build dataset from ingest receipts (recommended for provenance)
python -m renacechess.cli dataset build \
  --receipt ingested/lichess-2024-01.json \
  --out datasets/2024-jan/ \
  --shard-size 10000 \
  --cache-dir ~/.renacechess/cache
```

See [Dataset Documentation](docs/DATASETS.md) for detailed format and usage.

### Ingest Lichess Database Exports

```bash
# Ingest a monthly dump (with decompression)
renacechess ingest lichess \
  --month 2024-01 \
  --out ./ingested/ \
  --decompress

# Ingest from local file
renacechess ingest url \
  --url /path/to/file.pgn \
  --out ./ingested/
```

See [Ingestion Documentation](docs/INGESTION.md) for detailed usage and cache management.

### Development

```bash
make help       # list all targets
make verify     # boundary + lint + format-check + type + fast guardrail tests
make lint
make format-check
make type
make test
make demo
```

Without `make`, use the commands in [`CONTRIBUTING.md`](CONTRIBUTING.md).

### Pre-commit Hooks (Optional)

For local lint/format guardrails before committing:

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

**Note:** CI remains the source of truth. Pre-commit hooks are for local convenience only.

## Project Structure

```
renacechess/
├── src/renacechess/
│   ├── contracts/          # Versioned schemas and Pydantic models
│   ├── dataset/            # Dataset builder (PGN → JSONL + manifest)
│   ├── demo/               # Deterministic demo payload generator
│   ├── ingest/             # Lichess ingestion pipeline (download, cache, decompress)
│   ├── cli.py              # CLI entry point
│   └── determinism.py      # Canonical JSON and hashing helpers
├── tests/
│   ├── data/               # Test data (sample PGN, fixtures)
│   ├── golden/             # Golden file regression tests
│   └── test_*.py           # Test suite
└── docs/                   # Documentation
```

## Documentation

- **Start here:** [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`docs/DOCS_INDEX.md`](docs/DOCS_INDEX.md) · [`docs/release/PUBLIC_REPO_BOUNDARY.md`](docs/release/PUBLIC_REPO_BOUNDARY.md)
- [Public repository boundary](docs/release/PUBLIC_REPO_BOUNDARY.md) - Which paths are private vs public-eligible (M35)
- [Project Vision](VISION.md) - Complete project vision and north star
- [Release Notes v1.0.0](RELEASE_NOTES_v1.md) - v1.0.0 release details and limitations
- [Project Anchor](docs/ANCHOR.md) - Project vision and north star
- [Governance](docs/GOVERNANCE.md) - Milestone conventions and workflow
- [Assumed Guarantees](docs/ASSUMED_GUARANTEES.md) - What we inherit from RediAI v3
- [Dataset Format](docs/DATASETS.md) - Dataset structure, build process, and deterministic rules
- [Ingestion](docs/INGESTION.md) - Lichess database export ingestion and cache management
- [Proof Pack](proof_pack_v1/README.md) - External verification bundle (M33)

## License

Apache 2.0 — See [LICENSE](LICENSE) for details.

