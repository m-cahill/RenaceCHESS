# Getting Started with RenaceCHESS

This guide is for anyone who wants to **run**, **inspect**, or **change** RenaceCHESS quickly and safely.

## What RenaceCHESS Is

**Human-centered chess intelligence**: it predicts likely **human move choices**, **human win/draw/loss** chances for a modeled skill/time context, and produces **structured, LLM-groundable context** (not free-form speculative analysis).

## What It Is Not

- Not a superhuman chess engine
- Not a Stockfish/Leela replacement
- Not a production SaaS product
- Not an LLM that “figures out” chess on its own; coaching is grounded in contracts and deterministic facts per project ADRs.

For the full framing, see [VISION.md](../VISION.md) and [RELEASE_NOTES_v1.md](../RELEASE_NOTES_v1.md).

## 5-Minute Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Minimum Python version: see `requires-python` in [`pyproject.toml`](../pyproject.toml).

## Fast Local Verification

```bash
make verify
```

If `make` is unavailable, run:

```bash
python scripts/check_public_release_boundary.py
ruff check .
ruff format --check .
mypy src/renacechess
pytest tests/test_m38_credential_scanner_config.py tests/test_m37_dx_shortcuts.py tests/test_m36_docs_navigation.py tests/test_m35_public_release_boundary.py --no-cov
```

Optional — if [gitleaks](https://github.com/gitleaks/gitleaks) is installed:

```bash
make secret-scan
```

See [`docs/security/CREDENTIAL_SCANNING.md`](security/CREDENTIAL_SCANNING.md) for scope (CI blocking gate vs manual full-history) and what to do if a **secret** is found.

## Run a Quick Verification

```bash
ruff check .
ruff format --check .
lint-imports --config=importlinter_contracts.ini
mypy src/renacechess
pytest tests/test_m35_public_release_boundary.py --no-cov
pytest tests/test_m36_docs_navigation.py --no-cov
```

For the full suite (includes coverage thresholds from project defaults):

```bash
pytest
```

## Run a Demo

Generate a deterministic demo payload from sample PGN:

```bash
python -m renacechess.cli demo --pgn tests/data/sample.pgn --out demo.json
```

See [README.md](../README.md) for dataset build, ingestion, and other CLI flows.

## Understand the Release Artifacts

| Artifact / doc | Purpose |
|----------------|---------|
| [`contracts/CONTRACT_REGISTRY_v1.json`](../contracts/CONTRACT_REGISTRY_v1.json) | Immutable inventory of frozen v1 JSON Schemas with hashes |
| [`proof_pack_v1/`](../proof_pack_v1/) | Self-contained external verification bundle (see `proof_pack_v1/README.md`) |
| [`RELEASE_NOTES_v1.md`](../RELEASE_NOTES_v1.md) | v1.0.0 release claims and limits |
| [`docs/release/PUBLIC_REPO_BOUNDARY.md`](release/PUBLIC_REPO_BOUNDARY.md) | What must not leak into public history |

CI includes jobs that enforce contract freeze, dependency freeze on PRs, and proof-pack verification — see [.github/workflows/ci.yml](../.github/workflows/ci.yml).

## Where to Go Next

| Audience | Start with |
|---------|-------------|
| **Contributors** | [CONTRIBUTING.md](../CONTRIBUTING.md) |
| **Auditors** | [Documentation index § Auditors](DOCS_INDEX.md#auditors) |
| **Researchers** | [VISION.md](../VISION.md), [RELEASE_NOTES_v1.md](../RELEASE_NOTES_v1.md), [docs/ANCHOR.md](ANCHOR.md) |
| **Release reviewers** | [PUBLIC_REPO_BOUNDARY.md](release/PUBLIC_REPO_BOUNDARY.md) |

The full navigation map lives in [`docs/DOCS_INDEX.md`](DOCS_INDEX.md).
