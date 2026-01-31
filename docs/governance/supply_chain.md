# RenaceCHESS Supply Chain Governance

**Version:** 1.0  
**Status:** ACTIVE (M12 — POST-POC-HARDEN-001)  
**Last Updated:** 2026-01-30

---

## Purpose

This document defines RenaceCHESS supply-chain hygiene policies and procedures. It ensures:

1. **Reproducible builds** — Same dependencies resolve to same versions
2. **Security** — Supply-chain attacks are mitigated via pinning
3. **Auditability** — All dependencies and actions are traceable

---

## A) Dependency Pinning Strategy

### Production Dependencies

**Policy:** Use **compatible release pinning** (`~=`) for all production dependencies.

**Rationale:**
- `~=` fixes major + minor versions (e.g., `pydantic~=2.5.0` allows `2.5.x`, blocks `2.6.0`)
- Allows security patches (patch version updates)
- Prevents breaking changes (major/minor version drift)
- Balances stability with security updates

**Example:**
```toml
# ✅ CORRECT: Compatible release pinning
dependencies = [
    "pydantic~=2.5.0",      # allows 2.5.0, 2.5.1, ... blocks 2.6.0
    "torch~=2.2.0",        # allows 2.2.0, 2.2.1, ... blocks 2.3.0
]

# ❌ INCORRECT: Unbounded version drift
dependencies = [
    "pydantic>=2.0.0",     # allows any 2.x, 3.x, ... (risky)
]
```

### Development Dependencies

**Policy:** Use `>=` for dev dependencies (linting, testing tools).

**Rationale:**
- Dev tools are not part of production artifacts
- Tool updates improve developer experience
- Breaking changes in dev tools are easier to detect and fix

**Example:**
```toml
[project.optional-dependencies]
dev = [
    "ruff>=0.1.0",         # OK: dev tool
    "pytest>=7.0.0",       # OK: dev tool
]
```

### Dependency Update Process

1. **Identify outdated dependencies:**
   ```bash
   pip list --outdated
   ```

2. **Update `pyproject.toml` with new `~=` pin:**
   ```toml
   "pydantic~=2.6.0"  # updated from ~=2.5.0
   ```

3. **Test locally:**
   ```bash
   pip install -e ".[dev]"
   make test
   ```

4. **Commit with descriptive message:**
   ```bash
   git commit -m "chore: update pydantic to ~=2.6.0"
   ```

5. **Verify CI passes** before merging.

---

## B) GitHub Actions Pinning

### Policy

**All GitHub Actions MUST be pinned to commit SHAs**, not semantic tags.

**Rationale:**
- Semantic tags (`@v4`, `@v5`) can be updated by action maintainers
- SHA pinning ensures immutable, reproducible workflow execution
- Mitigates supply-chain attacks via compromised action repositories

### Format

```yaml
# ✅ CORRECT: SHA pinning with comment
- uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5  # v4.1.1
- uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065  # v5.0.0

# ❌ INCORRECT: Semantic tag (risky)
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
```

### Finding Action SHAs

**Method 1: GitHub API**
```bash
gh api repos/actions/checkout/commits/v4 --jq '.sha'
```

**Method 2: GitHub Web UI**
1. Navigate to action repository (e.g., `actions/checkout`)
2. Find the release/tag (e.g., `v4.1.1`)
3. Copy the commit SHA from the tag page

### Action Update Process

1. **Identify action to update:**
   - Check action repository for new releases
   - Review release notes for security fixes

2. **Get new SHA:**
   ```bash
   gh api repos/actions/checkout/commits/v4.1.2 --jq '.sha'
   ```

3. **Update workflow file:**
   ```yaml
   - uses: actions/checkout@<new-sha>  # v4.1.2
   ```

4. **Update comment** to reflect new version tag

5. **Test workflow** (create test PR or run locally with `act`)

6. **Commit with descriptive message:**
   ```bash
   git commit -m "chore: update actions/checkout to v4.1.2 (SHA: <new-sha>)"
   ```

---

## C) Lockfile Strategy (Future)

### Current State

**M12 does NOT introduce a full lockfile** (e.g., `requirements.txt` with exact pins).

**Rationale:**
- `~=` pinning provides sufficient reproducibility for PoC phase
- Full lockfiles are better suited for "reproducible training pack" milestone (M14+)

### Future Lockfile Plan (M14+)

When training reproducibility becomes critical:

1. Generate `requirements.txt` via `pip freeze`
2. Commit lockfile to repository
3. Use `pip install -r requirements.txt` in CI/training scripts
4. Update lockfile when dependencies change

---

## D) Security Scanning (Deferred)

### Current State

**M12 does NOT include automated security scanning** (e.g., `pip-audit`, Dependabot).

**Rationale:**
- Security scanning is a Phase D/E concern (post-PoC scale)
- M12 focuses on supply-chain hardening (pinning), not vulnerability detection

### Future Security Scanning Plan

When security posture needs hardening:

1. Add `pip-audit` job to CI workflow
2. Configure Dependabot for dependency updates
3. Add SBOM generation (CycloneDX) for artifact provenance

**Reference:** See `docs/foundationdocs/renacechessPoCaudit.md` for detailed security recommendations.

---

## E) Dependency Audit Trail

### Current Dependencies

See `pyproject.toml` for complete dependency list.

**Production Dependencies (M12):**
- `python-chess~=1.999` — Chess position/move handling
- `pydantic~=2.5.0` — Data validation and serialization
- `jsonschema~=4.20.0` — JSON schema validation
- `requests~=2.31.0` — HTTP client for ingestion
- `torch~=2.2.0` — PyTorch for model training/inference
- `zstandard~=0.22.0` — Compression for dataset shards

**Development Dependencies:**
- `ruff>=0.1.0` — Linting and formatting
- `mypy>=1.0.0` — Type checking
- `pytest>=7.0.0` — Testing framework
- `pytest-cov>=4.0.0` — Coverage reporting
- `coverage>=7.0.0` — Coverage measurement

### Dependency Justification

Each production dependency must have a documented justification:

| Dependency | Justification |
|------------|---------------|
| `python-chess` | Core chess position/move representation (PoC requirement) |
| `pydantic` | Schema validation and contract enforcement (M00 requirement) |
| `jsonschema` | JSON schema validation for contracts (M00 requirement) |
| `requests` | HTTP client for Lichess ingestion (M02 requirement) |
| `torch` | Model training and inference (M08 requirement) |
| `zstandard` | Efficient compression for dataset shards (M01 requirement) |

---

## F) Supply Chain Risk Mitigation

### Risks Addressed by M12

| Risk | Mitigation | Status |
|------|------------|--------|
| Dependency version drift | `~=` pinning | ✅ Addressed |
| Compromised GitHub Actions | SHA pinning | ✅ Addressed |
| Unbounded dependency updates | Compatible release pinning | ✅ Addressed |

### Remaining Risks (Deferred)

| Risk | Mitigation | Deferred To |
|------|------------|-------------|
| Known CVEs in dependencies | Security scanning (`pip-audit`) | Phase D/E |
| Dependency confusion attacks | SBOM + provenance | Phase D/E |
| Supply-chain drift over time | Lockfile + automated updates | M14+ |

---

## G) Compliance Checklist

Before merging any PR that modifies dependencies or workflows:

- [ ] All production dependencies use `~=` pinning
- [ ] All GitHub Actions are pinned to commit SHAs (with version comments)
- [ ] Dependency updates are tested locally
- [ ] CI passes with new dependency versions
- [ ] This document is updated if policy changes

---

**Governance Status:** ✅ **ACTIVE** (M12 — POST-POC-HARDEN-001)

