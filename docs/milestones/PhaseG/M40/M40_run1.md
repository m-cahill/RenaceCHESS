# M40 Run 1 — Verification Log

**Branch:** `m40-public-release-candidate-review`  
**Recorded:** 2026-05-08  
**PR:** [#54](https://github.com/m-cahill/RenaceCHESS/pull/54) — workflow [25594812746](https://github.com/m-cahill/RenaceCHESS/actions/runs/25594812746) **SUCCESS** for tip `e84adc43cbd9feb7d22a6ba244dc83a9cc50aeee`  

## Starting point

After `git pull --ff-only origin main`:

- **`main` tip SHA:** `4b2567ced3fd160da34c1c4a50373ace150576b1`
- **Branch tip:** Single squashed milestone commit on `m40-public-release-candidate-review` — use `git rev-parse HEAD` on that branch when opening the PR (differs from squash-merge commit on `main`).

**Environment:** Windows 10, Python 3.11.9 (project venv `.venv-m36`), repo `c:\coding\renacechess`.

## 1. Public boundary

### Commands

```powershell
git ls-files .cursorrules
git ls-files docs/prompts
git ls-files docs/manuals
git ls-files docs/company_secrets
git ls-files out
git status --short
```

**Result:** No output for `git ls-files` (paths not tracked). `git status` showed only untracked local items (`.venv-m36/`, `LICENSE`, `docs/renacechess_fullaudit.md`) — not part of the tracked release tree.

### Boundary script

```powershell
python scripts/check_public_release_boundary.py
```

**Output:**

```text
Public release boundary check passed: no private paths are tracked.
```

### Secret pattern grep

```powershell
git grep -n -I -E "(OPENAI_API_KEY|ANTHROPIC_API_KEY|GITHUB_TOKEN|PRIVATE KEY|BEGIN RSA|password=|secret=|api_key=)" -- .
```

**Result:** No matches (exit 0, no lines).

---

## 2. Dependency install

```powershell
python -m pip install -e ".[dev]"
```

**Result:** Success (exit 0).

---

## 3. Ruff

```powershell
ruff check .
ruff format --check .
```

**Output:**

```text
All checks passed!
170 files already formatted
```

---

## 4. MyPy

### Command from milestone brief

```powershell
mypy src tests
```

**Result:** **Failed** (many errors in `tests/` and fixtures; `tests` are not in the CI MyPy target).

### CI-equivalent command

From `.github/workflows/ci.yml` (Lint and Type Check job):

```powershell
mypy src/renacechess
```

**Output:**

```text
Success: no issues found in 71 source files
```

**Note:** For release-candidate evidence, **`mypy src/renacechess`** is the authoritative gate; expanding MyPy to `tests/` is a separate hygiene milestone.

---

## 5. Pytest

```powershell
pytest -q
```

**Output (abridged):** `1044 passed, 1 skipped` in ~60s; coverage **90.56%** (meets 90% gate).

---

## 6. Contract registry validation

### First attempt (working-tree EOL)

```powershell
python -c "from pathlib import Path; from renacechess.contracts.registry import validate_contract_registry; assert validate_contract_registry(Path('contracts/CONTRACT_REGISTRY_v1.json'), Path('src/renacechess/contracts/schemas/v1'))"
```

**Result:** **Failed** with hash mismatch on `advice_facts.v1.schema.json` (working copy had CRLF; Git warned CRLF would be replaced by LF).

### After canonical tree restore

```powershell
git restore src/renacechess/contracts/schemas/v1/advice_facts.v1.schema.json
python -c "from pathlib import Path; from renacechess.contracts.registry import validate_contract_registry; assert validate_contract_registry(Path('contracts/CONTRACT_REGISTRY_v1.json'), Path('src/renacechess/contracts/schemas/v1'))"
```

**Output:**

```text
SUCCESS: Contract registry validation passed
```

**Note:** On Windows, ensure schema JSON matches repository EOL (`.gitattributes`: `*.json text eol=lf`) before hashing; CI on `ubuntu-latest` uses LF by checkout default.

---

## 7. Proof pack verification

```powershell
python -c "from pathlib import Path; from renacechess.proof_pack.verify_proof_pack import verify_proof_pack; assert verify_proof_pack(Path('proof_pack_v1'))"
```

**Output:**

```text
verify_proof_pack: OK
```

---

## 8. pip-audit (spot check)

```powershell
pip-audit
```

**Output:** No known vulnerabilities found; editable project `renacechess` skipped (not on PyPI).

---

## Summary

| Check                         | Result |
|------------------------------|--------|
| Public boundary              | Pass   |
| `ruff check` / `format`      | Pass   |
| `mypy src/renacechess`       | Pass   |
| `mypy src tests`             | Fail (non-authoritative) |
| `pytest -q`                  | Pass   |
| Contract registry validation | Pass (after LF working tree) |
| Proof pack verification      | Pass   |
| pip-audit                    | Pass (local) |
