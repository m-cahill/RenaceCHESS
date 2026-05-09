# M40 — Public Release Candidate Review

## 1. Executive Verdict

**Verdict:** `APPROVE_PUBLIC_RC`

The repository is suitable as a **public release candidate**: public boundary is clean, primary documentation is claim-bounded, frozen proof pack and contract registry verify under CI-equivalent checks, and local quality gates match authoritative CI scope. Residual items are **non-blocking** for RC and are listed for optional M41 follow-up.

---

## 2. Scope

Review-only public release candidate assessment: boundary safety, narrative coherence of release artifacts, verification evidence, and classification of known deferrals. No product or model behavior changes in M40.

---

## 3. Public Boundary Review

**Commands run:**

- `git ls-files .cursorrules`, `docs/prompts`, `docs/manuals`, `docs/company_secrets`, `out` — **no tracked files**
- `git status --short` — no unintended tracked changes; local-only untracked paths noted in `M40_run1.md`
- `git grep` for common secret patterns — **no hits**
- `python scripts/check_public_release_boundary.py` — **pass**

**Findings:**

- None blocking. M35/M38 posture (ignore + CI boundary + credential scan) remains consistent with a public-safe tree.

**Verdict:** **PASS**

---

## 4. Documentation Review

**Files reviewed:**

- `README.md`
- `VISION.md`
- `RELEASE_NOTES_v1.md`
- `renacechess.md` (Source of Truth)
- `proof_pack_v1/README.md`
- `docs/release/PUBLIC_REPO_BOUNDARY.md` (referenced from README)
- `docs/security/CREDENTIAL_SCANNING.md` (referenced from README)

**Findings:**

- README clearly states what the project **is** and **is not** (not an engine, not production, not Stockfish replacement) and points to install/dev shortcuts.
- VISION and release notes reinforce human-centered scope and explicit limitations; **`RELEASE_NOTES_v1.md`** and **`docs/phases/PhaseE_closeout.md`** were aligned in this branch with **`TrainingConfigLockV1`** `moveVocabSize: 4096` and the narrow effective training regime.
- **Source of Truth / Phase G:** `renacechess.md` (M32 caveat) and `docs/phases/PhaseG_closeout.md` updated for M40 traceability.

**Verdict:** **PASS**

---

## 5. Release Artifact Review

**Artifacts reviewed:**

- `contracts/CONTRACT_REGISTRY_v1.json`
- `proof_pack_v1/proof_pack_manifest.json`
- `docs/phases/PhaseE_closeout.md`

**Findings:**

- Contract registry is presented as immutable v1 inventory; validation passes when schema files match repository LF bytes (see `M40_run1.md`).
- Proof pack verifies end-to-end with `verify_proof_pack`.
- **`proof_pack_manifest.json` limitations** include a line (“only 8 moves trained”) that is **not literally consistent** with `training_vocabulary.move_count: 4096` in the same manifest. The **numeric and config-lock fields are treated as authoritative** for vocabulary size; the bullet text is a **legacy wording inconsistency inside frozen JSON**. M40 does **not** rewrite the manifest (would change hashes and violate freeze). **M41 (or a dedicated proof-pack governance milestone)** may reconcile manifest prose via a formal regeneration if desired.

**Verdict:** **PASS** with documented frozen-manifest wording caveat (non-blocking for RC if external-facing docs are clear)

---

## 6. Verification Evidence

**Commands:**

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src/renacechess
pytest -q
python -c "from pathlib import Path; from renacechess.contracts.registry import validate_contract_registry; assert validate_contract_registry(Path('contracts/CONTRACT_REGISTRY_v1.json'), Path('src/renacechess/contracts/schemas/v1'))"
python -c "from pathlib import Path; from renacechess.proof_pack.verify_proof_pack import verify_proof_pack; assert verify_proof_pack(Path('proof_pack_v1'))"
```

**Results:**

- Ruff: pass
- MyPy: **CI scope** `src/renacechess` pass; `mypy src tests` fails — see `M40_run1.md`
- Pytest: 1044 passed, 1 skipped; coverage 90.56%
- Registry validation: pass (canonical LF tree)
- Proof pack: pass
- **TORCH-SEC-001:** Prior audits flagged Torch CVE debt; **M39 resolved** with bounded upgrade and documented posture (`docs/security/TORCH_SECURITY_REVIEW.md`). M40 **local pip-audit**: no known vulns (editable skip). **Residual:** `resolved` / `not observed` in this verification window.

Full transcript: `docs/milestones/PhaseG/M40/M40_run1.md`.

---

## 7. Known Deferrals

| Issue | Classification | Release blocking? | Rationale | Next milestone |
| ----- | -------------- | ----------------: | --------- | -------------- |
| MyPy on full `tests/` tree | DX / typing hygiene | No | CI gate is `mypy src/renacechess`; expanding scope is optional | M41+ |
| pytest-benchmark thresholds | Performance governance | No | Benchmarks upload artifacts; thresholds were explicitly deferred since M23 | M41+ |
| Proof pack manifest limitation bullet vs `move_count` | Frozen JSON prose consistency | No | Authoritative fields + config lock + updated public docs; changing manifest requires hash/regeneration governance | M41 optional |
| Wider test-marker discipline | Test taxonomy | No | Disclosed improvement; does not affect release safety claims | M41+ |

---

## 8. Public Claim Boundary

**Approved claims**

- Research-grade, human-centered move and W/D/L modeling with skill/time conditioning
- Schema-first v1 contracts with registry + CI freeze gates
- Deterministic artifacts, proof pack, and honest limitation reporting
- LLM-grounded coaching **facts** with hallucination-control posture (not “the LLM calculates chess”)

**Forbidden claims (must not imply)**

- Production deployment or commercial readiness as a product
- Engine strength / Stockfish replacement
- Hiding M31/M32 degradation or synthetic-eval limits

---

## 9. Recommendation

**`APPROVE_PUBLIC_RC`**

**Rationale:**

- No private prompts/manuals/secrets tracked; boundary script and grep clean
- README / VISION / release notes remain bounded and explicit after vocabulary wording alignment
- Registry validation and proof-pack verification succeed under the same substantive checks as CI
- Quality gates pass in authoritative CI scope; `mypy src tests` failure is out-of-scope for current CI
- TORCH-SEC-001 addressed in M39; no new residual observed in M40 pip-audit spot check

**Not authorized by this milestone (still):** tagging, publishing packages, GitHub Releases, or repository visibility changes — **M41** or an explicit release command.

**Merge boundary (completed 2026-05-09):** Maintainer-authorized **squash merge** of PR [#54](https://github.com/m-cahill/RenaceCHESS/pull/54) landed review/evidence docs on `main` as commit **`f175c8999a70772c6a2df0246cc92efd17c73097`**. Final PR head: **`e65fc462178540f7316b4d3bac318141d77d31ec`**. Pre-merge PR CI: [25612956250](https://github.com/m-cahill/RenaceCHESS/actions/runs/25612956250) — **success**. Post-merge `main` CI: [25614956502](https://github.com/m-cahill/RenaceCHESS/actions/runs/25614956502) — **success**.
