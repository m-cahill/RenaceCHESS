# RenaceCHESS CLI Contract

**Version:** 1.0  
**Status:** FROZEN (M12 — POST-POC-HARDEN-001)  
**Last Updated:** 2026-01-30

---

## Purpose

This document defines the **explicit contract** for the RenaceCHESS command-line interface (CLI). It guarantees:

1. **Command surface** — What commands exist and their signatures
2. **Side-effect guarantees** — What each command does and does not do
3. **Error behavior** — How failures are handled and reported

This contract prevents accidental coupling, hidden side effects, and implicit training triggers.

---

## A) Command Surface

### Available Commands

| Command | Purpose | Output Artifacts |
|---------|---------|-----------------|
| `demo` | Generate demo payload from PGN | JSON file (stdout or `--out`) |
| `dataset build` | Build dataset shards from PGN/receipts | Shard JSONL files + manifest.json |
| `ingest lichess` | Ingest Lichess monthly database export | Ingest receipt JSON |
| `ingest url` | Ingest PGN from URL or local file | Ingest receipt JSON |
| `eval run` | Evaluate policy providers over dataset | eval_report.json |
| `eval generate-frozen` | Generate frozen evaluation manifest | frozen_eval_manifest.v1.json |
| `train-policy` | Train learned human policy baseline | model.pt + model_metadata.json |
| `train-outcome-head` | Train learned human outcome head (W/D/L) | outcome_head.pt + metadata.json |

---

## B) Side-Effect Guarantees

### Critical Guarantees

#### ❌ Commands that MUST NOT train models

The following commands are **read-only** and **MUST NOT** trigger training:

- `demo` — Generates JSON payloads only
- `dataset build` — Creates dataset shards only (no model weights)
- `ingest lichess` / `ingest url` — Downloads and caches PGN files only
- `eval run` — Evaluates existing models only (requires `--model-path` for learned policies)
- `eval generate-frozen` — Generates frozen eval manifest only

**Enforcement:** These commands do not import `renacechess.models.training` or `renacechess.models.training_outcome`.

#### ✅ Commands that explicitly train

Only the following commands trigger training:

- `train-policy` — Trains policy baseline model
- `train-outcome-head` — Trains outcome head model

**Enforcement:** These commands explicitly import training modules and are named with `train-` prefix.

#### ❌ Commands that MUST NOT mutate datasets

The following commands are **read-only** with respect to datasets:

- `eval run` — Reads dataset manifest, writes evaluation report only
- `eval generate-frozen` — Reads dataset manifest, writes frozen eval manifest only
- `demo` — Reads PGN, writes JSON payload only

**Enforcement:** No command writes to dataset shard directories or modifies manifest files.

#### ✅ Commands that create new artifacts

The following commands create new files/directories:

- `dataset build` — Creates shard JSONL files and manifest.json
- `ingest lichess` / `ingest url` — Creates ingest receipt JSON
- `train-policy` — Creates model.pt and model_metadata.json
- `train-outcome-head` — Creates outcome_head.pt and metadata.json
- `eval run` — Creates eval_report.json
- `eval generate-frozen` — Creates frozen_eval_manifest.v1.json

**Enforcement:** All output paths are explicitly specified via `--out` or `--out-dir` arguments.

---

## C) Error & Failure Behavior

### Exit Codes

| Exit Code | Meaning | Example |
|-----------|---------|---------|
| `0` | Success | Command completed without errors |
| `1` | User error | Invalid arguments, missing required files |
| `2` | System error | I/O failures, dependency errors |

### Error Handling Guarantees

1. **No partial writes on failure** — If a command fails, it does not leave partial artifacts in the output directory.

2. **Deterministic outputs** — Given the same inputs, commands produce byte-identical outputs (enforced via `determinism.py`).

3. **Clear error messages** — All errors are written to `stderr` with actionable messages.

4. **Validation before processing** — Commands validate all required inputs before starting work (fail fast).

### Example Error Scenarios

| Scenario | Behavior |
|----------|----------|
| Missing required file | Exit 1, error message to stderr |
| Invalid JSON schema | Exit 1, validation error details |
| Disk full during write | Exit 2, error message, no partial file |
| Network timeout (ingest) | Exit 2, error message, cache preserved |

---

## D) Training Commands (Explicit Contract)

### `train-policy`

**Side Effects:**
- ✅ Writes `model.pt` and `model_metadata.json` to `--out` directory
- ✅ Reads from `--dataset-manifest` (excludes frozen eval if `--frozen-eval-manifest` provided)
- ❌ Does NOT modify dataset shards
- ❌ Does NOT modify existing model files (creates new files only)

**Determinism:**
- Uses `--seed` (default: 42) for reproducible training
- Excludes frozen eval records deterministically (by hash)

### `train-outcome-head`

**Side Effects:**
- ✅ Writes `outcome_head.pt` and `outcome_head_v1_metadata.json` to `--out` directory
- ✅ Reads from `--dataset-manifest` (excludes frozen eval if `--frozen-eval-manifest` provided)
- ❌ Does NOT modify dataset shards
- ❌ Does NOT modify existing model files (creates new files only)

**Determinism:**
- Uses `--seed` (default: 42) for reproducible training
- Excludes frozen eval records deterministically (by hash)

---

## E) Evaluation Commands (Read-Only Contract)

### `eval run`

**Side Effects:**
- ✅ Reads dataset manifest and shards (read-only)
- ✅ Loads model from `--model-path` (if `learned.v1` policy)
- ✅ Writes `eval_report.json` to `--out` directory
- ❌ Does NOT modify models
- ❌ Does NOT modify datasets
- ❌ Does NOT trigger training

**Enforcement:** This command does not import training modules.

### `eval generate-frozen`

**Side Effects:**
- ✅ Reads dataset manifest and shards (read-only)
- ✅ Writes `frozen_eval_manifest.v1.json` to `--out` path
- ❌ Does NOT modify datasets
- ❌ Does NOT trigger training

**Enforcement:** This command does not import training modules.

---

## F) Import Boundary Guarantees

### CLI Module Dependencies

The `renacechess.cli` module:

- ✅ **MAY import:** All public APIs from other modules (dataset, eval, ingest, models, features)
- ❌ **MUST NOT import:** `renacechess.models.training` or `renacechess.models.training_outcome` except in explicit training command handlers

**Enforcement:** Import-linter contract `cli_is_orchestration_only` enforces this boundary.

### Training Command Isolation

Training commands (`train-policy`, `train-outcome-head`) import training modules **only within their command handlers**, not at module level.

**Example:**
```python
# ✅ CORRECT: Import inside handler
elif args.command == "train-policy":
    from renacechess.models.training import train_baseline_policy
    # ... use function ...

# ❌ INCORRECT: Import at module level
from renacechess.models.training import train_baseline_policy  # BAD
```

---

## G) Versioning & Compatibility

### Command Stability

- **Frozen commands** (M00-M11): Command signatures are frozen and will not change
- **New commands** (M12+): Must follow this contract and be documented here

### Backward Compatibility

- Commands accept legacy argument formats where documented (e.g., `--pgn` for backward compatibility)
- New optional arguments do not break existing invocations

---

## H) Testing Requirements

All CLI commands must have:

1. **Integration tests** — Test full command execution with real inputs
2. **Error path tests** — Test failure scenarios (missing files, invalid args)
3. **Side-effect verification** — Assert no unintended file modifications

**Location:** `tests/test_cli.py` and command-specific test files.

---

## I) Changes to This Contract

This contract is **frozen** as of M12. Changes require:

1. Milestone-level governance review
2. Update to this document
3. Verification that no existing commands violate new constraints

---

**Contract Status:** ✅ **FROZEN** (M12 — POST-POC-HARDEN-001)

