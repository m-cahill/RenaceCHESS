# M40 Plan — Public Release Candidate Review

**Phase:** G — Public Release Readiness  
**Type:** Review, evidence, and decision (not feature development)

## Objective

Answer: **Is the current repository state safe, coherent, reproducible, and appropriately documented for a public release candidate?**

## Branch

`m40-public-release-candidate-review` (from current `main` after M39 merge).

## Non-Goals

- No model retraining, contract semantics changes, or proof-pack hash changes
- No v2 contracts
- No weakening CI or hiding limitations

## Scope

1. Public boundary (tracked private paths, secrets)
2. Release artifacts (README, VISION, release notes, proof pack, contract registry, Phase E closeout)
3. Local verification (lint, format, MyPy as in CI, pytest, registry validation, proof-pack verification)
4. Known deferrals (TORCH-SEC-001 post-M39; test typing; benchmarks)

## Deliverables

- `M40_plan.md` (this file)
- `M40_public_release_candidate_review.md`
- `M40_run1.md`
- `M40_summary.md`
- `M40_audit.md`

## Acceptance

See `M40_public_release_candidate_review.md` executive verdict and `renacechess.md` M40 row when closed.
