# M36 — Summary

**Milestone:** Public Release Documentation Onboarding  
**Status:** 🚧 Implementation / open PR (update to ✅ Closed after merge and post-merge CI)  
**Phase:** G — Public Release Readiness  

## What Shipped

- Root [`CONTRIBUTING.md`](../../../../CONTRIBUTING.md) — setup, verification commands, milestone habits, public boundary, contract rules, PR checklist.
- [`docs/GETTING_STARTED.md`](../../../../docs/GETTING_STARTED.md) — 5-minute setup, verification, demo command, release artifact pointers, next steps by audience.
- [`docs/DOCS_INDEX.md`](../../../../docs/DOCS_INDEX.md) — audience-based map (contributors, auditors, researchers, contract consumers, milestones).
- [`README.md`](../../../../README.md) — “Start Here” links into the three onboarding docs + public boundary.
- [`tests/test_m36_docs_navigation.py`](../../../../tests/test_m36_docs_navigation.py) — regression that required files exist and README mentions key paths.
- [`renacechess.md`](../../../../renacechess.md) — M36 row, Phase G ACTIVE, M36–M39 roadmap table.
- **Input audit artifact (not milestone audit):** [`M36_fullaudit.md`](M36_fullaudit.md) moved under Phase G; milestone closeout audit is [`M36_audit.md`](M36_audit.md).

## What Did Not Change

- No application code, schemas, contract registry hashes, or proof-pack payloads.
- No CI workflow semantics (only new test collected by default pytest discovery).
- No Makefile, gitleaks, or Torch work (deferred to M37–M39).

## Verification (local)

```bash
python scripts/check_public_release_boundary.py
git ls-files docs/prompts docs/foundationdocs .cursorrules
pytest tests/test_m36_docs_navigation.py --no-cov
pytest tests/test_m35_public_release_boundary.py --no-cov
```

## Post-merge

After merge: confirm `main` CI green; then set M36 status and dates in `renacechess.md` and update this summary closing line.
