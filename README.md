# RenaceCHESS

**Not Another Chess Engine; it's a Cognitive Human Evaluation & Skill Simulation**

RenaceCHESS is a human-centered chess intelligence system that predicts what move a human of a given skill (and time pressure) is likely to play, estimates human win/draw/loss chances for that same skill level, and provides LLM-groundable context for real-time, natural-language coaching and broadcast narrative.

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
# Build dataset from PGN files
python -m renacechess.cli dataset build \
  --pgn tests/data/sample.pgn \
  --out datasets/sample/ \
  --max-positions 1000 \
  --start-ply 0 \
  --end-ply 40
```

See [Dataset Documentation](docs/DATASETS.md) for detailed format and usage.

### Development

```bash
# Run linter
make lint

# Run type checker
make type

# Run tests
make test

# Generate demo
make demo
```

## Project Structure

```
renacechess/
├── src/renacechess/
│   ├── contracts/          # Versioned schemas and Pydantic models
│   ├── dataset/            # Dataset builder (PGN → JSONL + manifest)
│   ├── demo/               # Deterministic demo payload generator
│   ├── cli.py              # CLI entry point
│   └── determinism.py     # Canonical JSON and hashing helpers
├── tests/
│   ├── data/               # Test data (sample PGN)
│   ├── golden/             # Golden file regression tests
│   └── test_*.py           # Test suite
└── docs/                   # Documentation
```

## Documentation

- [Project Anchor](docs/ANCHOR.md) - Project vision and north star
- [Governance](docs/GOVERNANCE.md) - Milestone conventions and workflow
- [Assumed Guarantees](docs/ASSUMED_GUARANTEES.md) - What we inherit from RediAI v3
- [Dataset Format](docs/DATASETS.md) - Dataset structure, build process, and deterministic rules

## License

MIT

