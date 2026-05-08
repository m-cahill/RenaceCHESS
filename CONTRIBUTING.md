# Contributing to RenaceCHESS

## Start Here

- Read [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)
- Review [`docs/DOCS_INDEX.md`](docs/DOCS_INDEX.md)
- Review [`docs/release/PUBLIC_REPO_BOUNDARY.md`](docs/release/PUBLIC_REPO_BOUNDARY.md)

## Local Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Developer Shortcuts

The canonical commands remain the plain Python/Ruff/MyPy/Pytest commands below. For convenience, M37 adds a `Makefile` with aliases:

```bash
make help
make verify
make test-fast
make boundary-check
```

A conservative setup helper prints recommended venv steps and installs dev dependencies only when you pass `--install`:

```bash
python scripts/setup_dev.py
python scripts/setup_dev.py --install
```

These shortcuts do not replace CI. They are local convenience wrappers.

## Common Verification

```bash
ruff check .
ruff format --check .
lint-imports --config=importlinter_contracts.ini
mypy src/renacechess
pytest tests/test_m35_public_release_boundary.py --no-cov
pytest
```

CI uses Python **3.12** and runs the above categories of checks; local Python **3.11+** is supported per [`pyproject.toml`](pyproject.toml).

## Milestone Workflow

- Work in small milestone branches (for example `m36-public-release-docs-onboarding`).
- Keep scope narrow and aligned with the milestone plan.
- Update [`renacechess.md`](renacechess.md) when the milestone changes tracked status or governance.
- Add or update milestone plan, summary, and audit documents under [`docs/milestones/`](docs/milestones/) as required by governance.
- Do not merge without explicit maintainer approval.

## Public Boundary

These paths must **not** be committed to public branches (they may exist locally):

- `docs/prompts/`
- `docs/foundationdocs/`
- `.cursorrules`

Checks:

```bash
python scripts/check_public_release_boundary.py
git ls-files docs/prompts docs/foundationdocs .cursorrules
```

The second command must print nothing (empty output means those paths are not tracked).

See [`docs/release/PUBLIC_REPO_BOUNDARY.md`](docs/release/PUBLIC_REPO_BOUNDARY.md) for rationale and reviewer checklist.

## Contract Rules

- **v1 contracts are frozen.** Do not edit v1 JSON Schema files under `src/renacechess/contracts/schemas/v1/` or change hashed entries in [`contracts/CONTRACT_REGISTRY_v1.json`](contracts/CONTRACT_REGISTRY_v1.json) without the release-exception process documented in milestone and CI commentary.
- New contract surfaces should use **v2+** (or newer) versioning and governance, not silent edits to v1.
- Do not rewrite [`proof_pack_v1/`](proof_pack_v1/) artifacts casually; integrity is gated in CI (`release-proof-pack-verification`).

Sanctioned dependency bumps on merged release branches may require the `RELDEPS-EXCEPTION` token in the PR body; see `.github/workflows/ci.yml` (`release-dependency-freeze` job).

## Pull Request Checklist

- [ ] Scope matches the milestone / issue.
- [ ] `ruff check .`, `ruff format --check .`, `mypy src/renacechess`, and `pytest` pass locally when feasible (**Linux CI is authoritative** if Windows coverage or tooling differs).
- [ ] **Credential scan:** optional locally with `make secret-scan` if [gitleaks](https://github.com/gitleaks/gitleaks) is installed; **CI always runs** the blocking `gitleaks` current-tree scan in **Security Scan** (see [`docs/security/CREDENTIAL_SCANNING.md`](docs/security/CREDENTIAL_SCANNING.md)).
- [ ] **`pip-audit`:** optional locally (`pip-audit --desc on --progress-spinner off` after `pip install -e ".[dev]"`); mirrors the **dependency vulnerability scan** step in **Security Scan** (see [`docs/security/TORCH_SECURITY_REVIEW.md`](docs/security/TORCH_SECURITY_REVIEW.md)).
- [ ] `python scripts/check_public_release_boundary.py` passes.
- [ ] `git ls-files docs/prompts docs/foundationdocs .cursorrules` produces no output.
- [ ] Documentation updated when behavior or process changes; onboarding links preserved (see [`tests/test_m36_docs_navigation.py`](tests/test_m36_docs_navigation.py)).
