Below is a **paste-ready Cursor prompt** for **RenaceCHESS — M00 (small, enterprise-grade bootstrap)**. It focuses on: **repo scaffolding + CI truthfulness + versioned contracts + a deterministic “demo payload”** (no big data downloads, no ML training yet). It also bakes in the milestone/audit posture you’ve been using.

---

## Cursor handoff prompt — M00

```text
You are Cursor operating as an implementation agent for the RenaceCHESS project.

Milestone: M00 — Repository Bootstrap + Contract Skeleton + Deterministic Demo
Branch: m00-bootstrap (one branch per milestone)
Goal: Start small, stay auditable, and ensure end-to-end verification is green.

NON-NEGOTIABLE GOVERNANCE
- One milestone = one scoped change-set. No scope creep.
- Required checks must remain truthful. “Green = safe, Red = meaningful debt.”
- Add guardrails and tests as you go; do not defer basic correctness.
- Every milestone must produce: M00_plan, M00_summary, M00_audit (lightweight but real).
- Prefer deterministic artifacts + golden tests over “looks right” validation.

M00 SCOPE (IN)
1) Minimal repo skeleton (Python-first), with clean module boundaries.
2) Versioned JSON Schemas + matching Pydantic models for:
   - LLM Context Bridge payload (v1)
   - Dataset manifest (v1) — even if data ingestion is stubbed
3) Deterministic demo generator that:
   - Reads a small local PGN (checked into tests/)
   - Produces a deterministic “LLM Context Bridge” JSON payload
   - Validates against schema
   - Has a golden-file regression test
4) CI baseline (GitHub Actions) that runs:
   - ruff (lint + format check)
   - mypy (reasonable strictness for our tiny codebase)
   - pytest (+ coverage gate)
5) Minimal docs:
   - README that states: “Not Another Chess Engine; Cognitive Human Evaluation & Skill Simulation”
   - docs/ with an anchor doc + governance conventions + M00 docs

M00 SCOPE (OUT)
- No large-scale Lichess downloads.
- No real training pipeline yet.
- No GPU/TPU work.
- No complex UI.
- No engine integration beyond optional “contrast hooks” in doc text.

REPO STRUCTURE (target)
- pyproject.toml (ruff, mypy, pytest, coverage)
- src/renacechess/
    __init__.py
    cli.py                      (Typer or argparse; keep minimal)
    determinism.py              (canonical JSON + stable hashing helpers)
    contracts/
        __init__.py
        schemas/
            v1/
               context_bridge.schema.json
               dataset_manifest.schema.json
        models.py               (Pydantic models mirroring schemas)
    demo/
        __init__.py
        pgn_overlay.py          (demo generator: PGN -> payload)
- tests/
    data/
        sample.pgn
    golden/
        demo_payload.v1.json
    test_contracts_schema.py
    test_demo_payload_golden.py
    test_determinism.py

STEP-BY-STEP IMPLEMENTATION PLAN
0) Recon
   - Inspect current repo state. If empty repo, create the structure above.
   - Ensure Python packaging uses src-layout. Keep dependencies minimal.

1) Tooling + dependencies
   - Add runtime deps:
     - python-chess (for PGN parsing)
     - pydantic (v2) + pydantic-settings (only if needed)
     - jsonschema (or use pydantic json schema validation; but external jsonschema is fine)
   - Add dev deps:
     - ruff, mypy, pytest, pytest-cov, coverage
   - Add Makefile (or scripts/) with:
     - make lint
     - make type
     - make test
     - make demo   (runs demo and prints path to output)

2) Determinism helpers
   - Implement canonical JSON dump:
     - sorted keys
     - stable separators
     - UTF-8, no trailing whitespace
   - Implement stable hash helper (sha256 of canonical bytes).
   - Add tests proving:
     - stable output for same dict
     - hash stable across runs

3) Contracts (schemas + models)
   - Create schema v1 for “LLM Context Bridge” payload with these minimum fields:
     - position: { fen, sideToMove, legalMoves[] }
     - conditioning: { skillBucket, timePressureBucket, timeControlClass? }
     - policy: { topMoves: [{ uci, p }], entropy, topGap }
     - humanWDL: { pre: {w,d,l}, postByMove: { uci: {w,d,l} } }
     - hdi: { value, components: { entropy, topGap, wdlSensitivity } }
     - narrativeSeeds: [{ type, severity, facts[] }]
     - meta: { schemaVersion, generatedAt, inputHash }
   - Create schema v1 for dataset manifest (stub but real):
     - schemaVersion
     - createdAt
     - shardRefs[] (can be empty in M00)
     - filterConfigHash
     - splitAssignments (train/val/frozenEval) (can be empty)
   - Implement Pydantic models that match schemas exactly.
   - Add tests:
     - Model -> canonical JSON -> validates against JSON schema
     - Schema version string must be “v1”

4) Deterministic demo generator (no ML yet)
   - Add tests/data/sample.pgn with a short, valid PGN (tiny).
   - pgn_overlay.py should:
     - Parse PGN, step to a target ply (e.g., after move 6)
     - Compute FEN and legal moves via python-chess
     - Produce a *deterministic stub policy*:
       - Choose topMoves by sorting UCI legal moves alphabetically
       - Assign probabilities deterministically (e.g., geometric decay normalized)
     - Compute entropy/topGap deterministically
     - Produce a *deterministic stub humanWDL*:
       - Use a simple, deterministic mapping based on topGap/entropy (not “real” chess eval)
       - Ensure values are valid probabilities summing to 1
       - Provide postByMove for the same topMoves keys
     - Compute HDI from entropy/topGap + a simple sensitivity proxy
     - Fill narrativeSeeds with deterministic facts (no LLM calls)
     - Fill meta (schemaVersion=v1, generatedAt fixed in tests OR injected/overridable, inputHash from canonical inputs)
   - IMPORTANT: The demo must be stable across runs. For tests, freeze generatedAt.

5) Golden test + CLI
   - CLI command:
     - `python -m renacechess.cli demo --pgn tests/data/sample.pgn --out /tmp/demo.json`
   - Golden test:
     - Run generator with fixed params, compare canonical JSON bytes to tests/golden/demo_payload.v1.json
   - If golden changes, require intentional update + short justification in M00_audit.

6) CI (GitHub Actions)
   - Add .github/workflows/ci.yml with:
     - ubuntu-latest
     - python 3.11 (keep M00 small; we can expand matrix later)
     - pip cache
     - ruff check .
     - ruff format --check .
     - mypy (target src/)
     - pytest with coverage gate (set high; small codebase)
       - lines >= 90%, branches >= 85% (adjust only if truly necessary, but aim high)
   - Upload artifacts on failure:
     - junit xml (optional)
     - coverage.xml

7) Docs + milestone artifacts
   - Add docs/ with:
     - docs/ANCHOR.md (project anchor / north star, short)
     - docs/GOVERNANCE.md (milestone conventions: MNN_plan, MNN_summary, MNN_audit; “Green=Safe”)
     - docs/ASSUMED_GUARANTEES.md (state what we inherit from RediAI v3 / R2L and what we do NOT re-test)
   - Create milestone docs:
     - docs/milestones/M00_plan.md
     - docs/milestones/M00_summary.md
     - docs/milestones/M00_audit.md
   - M00_audit must explicitly list:
     - what was added
     - what is deferred (if anything) + rationale
     - evidence of CI green (workflow name, commit hash placeholder)

8) End-to-end verification (required)
   - Run locally (or in CI logs):
     - ruff check + format check
     - mypy
     - pytest
     - CLI demo command
   - Confirm CI is green on the PR before merge.

DELIVERABLE CHECKLIST (Definition of Done)
- Repo builds/tests cleanly on CI.
- Versioned schemas exist and are validated in tests.
- Deterministic demo payload generated + golden test passes.
- CLI demo command works.
- Coverage gates met.
- M00_plan/M00_summary/M00_audit committed in docs/milestones/.

OUTPUT FORMAT
- Open a PR from m00-bootstrap to main.
- Use conventional commits where reasonable.
- Include a concise PR description that maps changes to the deliverable checklist.

If you hit any ambiguity, make a best-effort decision consistent with “small + auditable + deterministic,” and document the choice in M00_audit rather than stalling.
```

---

## References you can embed in docs (optional but nice in M00)

* Lichess DB exports are **CC0** (so we can later build a reproducible pipeline around them). ([Lichess Database][1])
* The Maia line of work is strong precedent for *skill-conditioned human move prediction* (useful framing for RenaceCHESS). ([U of T Computer Science][2])
* Stockfish’s `UCI_ShowWDL` is a good “contrast layer” reference (engine WDL ≠ human WDL). ([Stockfish][3])

---

## Files already available in this chat (handy anchors)

* Phase XIV audit context (RediAI v3): 
* Audit enhancements baseline: 
* Testing enhancements baseline: 
* Full-stack enhancement prompt: 
* Phase XIV closeout (RediAI v3): 
* RenaceCHESS project anchor spec: 
* RenaceCHESS assumed guarantees/testing posture: 

If you want M00 to be even smaller, the one safe cut is: **skip dataset_manifest.schema.json** (keep only Context Bridge). Everything else I’d keep because it’s what makes M00 “real and verified,” not just scaffolding.

[1]: https://database.lichess.org/?utm_source=chatgpt.com "lichess.org open database"
[2]: https://www.cs.toronto.edu/~ashton/pubs/maia-kdd2020.pdf?utm_source=chatgpt.com "Aligning Superhuman AI with Human Behavior: Chess as a ..."
[3]: https://official-stockfish.github.io/docs/stockfish-wiki/UCI-%26-Commands.html?utm_source=chatgpt.com "UCI & Commands | Stockfish Docs"
