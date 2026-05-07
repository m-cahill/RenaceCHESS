# RenaceCHESS Documentation Index

Audience-based entry points into the repo. Paths are repo-relative from the checkout root unless noted.

## New Contributors

- [`docs/GETTING_STARTED.md`](GETTING_STARTED.md) — fastest safe path from zero to verified checkout
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — workflows, gates, boundaries, checklist
- [`README.md`](../README.md) — project overview and common commands

## Auditors

- [`docs/release/PUBLIC_REPO_BOUNDARY.md`](release/PUBLIC_REPO_BOUNDARY.md) — tracked-file boundary and reviewer checklist
- [`contracts/CONTRACT_REGISTRY_v1.json`](../contracts/CONTRACT_REGISTRY_v1.json) — frozen v1 contract inventory with schema hashes
- [`proof_pack_v1/README.md`](../proof_pack_v1/README.md) — how to verify the external proof bundle
- [`RELEASE_NOTES_v1.md`](../RELEASE_NOTES_v1.md) — documented release claims and limitations

## Researchers / Reviewers

- [`VISION.md`](../VISION.md) — north star and scope semantics
- [`docs/ANCHOR.md`](ANCHOR.md) — project anchor narrative
- [`renacechess.md`](../renacechess.md) — milestone source of truth, governance, frozen contract list pointers

For coaching design intent, see [ADR-COACHING-001](adr/ADR-COACHING-001.md).

## Contract Consumers

- [`contracts/CONTRACT_REGISTRY_v1.json`](../contracts/CONTRACT_REGISTRY_v1.json)
- [`src/renacechess/contracts/schemas/v1/`](../src/renacechess/contracts/schemas/v1/)
- Markdown contract semantics where frozen: [`docs/contracts/`](contracts/)

Canonical dict/kwargs rules: [CONTRACT_INPUT_SEMANTICS.md](contracts/CONTRACT_INPUT_SEMANTICS.md).

## Milestone History

- [`docs/milestones/`](milestones/)
- [`renacechess.md`](../renacechess.md) — authoritative milestone table and phase status

Phase G (public release readiness) artifacts: [`docs/milestones/PhaseG/M36/`](milestones/PhaseG/M36/) and successors.

## Public Release Boundary

- [`docs/release/PUBLIC_REPO_BOUNDARY.md`](release/PUBLIC_REPO_BOUNDARY.md)

Sanity checks contributors should run locally are listed in [CONTRIBUTING.md](../CONTRIBUTING.md).
