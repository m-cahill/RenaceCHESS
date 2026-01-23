# R2L Project Source of Truth

**README-to-Lab: MicroLab Synthesizer**

This document is the authoritative source of truth for the R2L project. It tracks milestones, database schema, migrations, and governance decisions.

---

## Project Overview

**R2L (README-to-Lab)** is a "Kaggle replacement mode" for foundation-model research, focused on the `question → disposable system → evidence-bearing artifacts` loop.

**Primary Purpose:** Generate minimal research systems that produce verifiable, reproducible artifacts from research questions.

**Architecture:**
- **Backend:** Python 3.11+ (FastAPI, Pydantic, Phi canary adapter)
- **Frontend:** TypeScript/React (Vite, Vitest, Playwright)
- **CI/CD:** GitHub Actions (multi-language CI, Netlify + Render deploy)
- **Security:** Bandit, pip-audit, Gitleaks, OpenSSF Scorecard
- **SBOM:** CycloneDX SBOM generation

---

## Milestone Tracking

| Milestone | Objective | Status | Commit | CI Run | Notes |
|-----------|-----------|--------|--------|--------|-------|
| **M00** | Bootstrap R2L repo + Phi canary + guardrails | ✅ **CLOSED** | 83359ac | [Run 9](https://github.com/m-cahill/r2l/actions/runs/21158688099) | All 7 required jobs passed; optional jobs handled correctly; zero technical debt |
| **M01** | R2L Governance Tightening (Pre-Phase-XV) | ✅ **CLOSED** | 21c5f2d | [Run 1](https://github.com/m-cahill/r2l/actions/runs/21159804131) | Coverage thresholds raised to M01 levels; MyPy overrides quarantined; zero technical debt |
| **M71** | Phase XV Re-charter & Golden Path Lock | ✅ **CLOSED** | 83e9fe5 | [Run 1](https://github.com/m-cahill/r2l/actions/runs/21160889520) | Phase XV consumer posture established; canonical Golden Path designated; execution contract documented |
| **M72** | Deterministic Runner & Manifest Enforcement | ✅ **CLOSED** | 1387c78 | [Run 2](https://github.com/m-cahill/r2l/actions/runs/21163360322) | Determinism enforced via canonical JSON, bundle hash, and CI determinism gate; all required checks passed |
| **M73** | Artifact Schema & Hash Contract | ✅ **CLOSED** | a961b6e | [Run 2](https://github.com/m-cahill/r2l/actions/runs/21165112520) | Schema validation and versioning for structured artifacts; CI schema gate added; all required checks passed |
| **M74** | Adapter Contract Enforcement (Phi + MedGemma stub) | ✅ **CLOSED** | dfe06f6 | [Run 3](https://github.com/m-cahill/r2l/actions/runs/21166508626) | Adapter contract explicitly defined and enforced; MedGemma stub added; CI adapter contract gate added; provider-agnostic artifact generation proven |
| **M75** | Consumer Certification CI Job | ✅ **CLOSED** | 7490d3c | [Run 1](https://github.com/m-cahill/r2l/actions/runs/21167631593) | Single certification verdict job aggregating determinism, schema-validation, and adapter-contract signals; certification verdict CI-enforced; machine-readable certification artifact |
| **M02** | Post-Phase-XV Expansion Guardrails | ✅ **CLOSED** | 674af55 | [Run 1](https://github.com/m-cahill/r2l/actions/runs/21186669307) | Post-Phase-XV Expansion Guardrails established with explicit capabilities, prohibitions, invariants, and expansion rules; all Phase XV guarantees preserved; zero runtime impact; documentation-only milestone |
| **M03** | Real Model Execution (Single-Question, Guarded) | ✅ **CLOSED** | 0c86855 | [Run 7](https://github.com/m-cahill/r2l/actions/runs/21191178138) | Real Phi execution capability introduced with configurable mode (default: stub); all Phase XV guarantees preserved; CI uses deterministic stub for certification; real execution opt-in and out-of-band from CI determinism guarantees; all quality gates passing |
| **M04** | Multi-Question Lab Orchestration (Stubbed, Deterministic) | ✅ **CLOSED** | 0ca70c9 | [Run 6](https://github.com/m-cahill/r2l/actions/runs/21194880437) | Multi-question orchestration introduced with deterministic ordering and fail-fast certification; all Phase XV guarantees preserved; backward compatibility maintained; code quality improved through disciplined refactoring; all quality gates passing |
| **M05** | Operational Hardening of Multi-Question Orchestration | ✅ **CLOSED** | 74ec0a2 | [Run 4](https://github.com/m-cahill/r2l/actions/runs/21200793925) | Operational hardening introduced (input limits, timeouts, transactional writes, structured logging); all Phase XV guarantees preserved; backward compatibility maintained; error taxonomy established; all tests passing (74/74), coverage 85.42%; one non-blocking CI toolchain issue documented (INFRA-CI-001) |
| **M06** | INFRA-CI: Ruff Format Determinism Fix | ✅ **CLOSED** | bcccc19 | [Run 10](https://github.com/m-cahill/r2l/actions/runs/21230602600) | Resolved INFRA-CI-001; ruff pinned, config determinism, `.gitattributes` LF enforcement; self-extracting diagnostics; Radon complexity reduced; all required checks green |
| **M07** | Branch Protections + Merge Discipline | ✅ **CLOSED** | 26ab185 | [PR #16](https://github.com/m-cahill/r2l/pull/16) | Branch protection enforced; 11 required checks enforced on merge; direct push blocked; admin bypass disabled; governance documentation complete |

**M00 Closure Date:** 2026-01-20  
**M00 Achievement:** Governed, auditable, multi-language CI system with real security, supply-chain, testing, and policy enforcement—at bootstrap.

**M01 Closure Date:** 2026-01-20  
**M01 Achievement:** Governance discipline locked in with milestone-indexed coverage thresholds and explicitly quarantined type overrides. Phase-XV-ready self-discipline established.

**M71 Closure Date:** 2026-01-20  
**M71 Achievement:** Phase XV consumer posture established, canonical Golden Path designated (`examples/hello-lab/README.md`), execution contract documented. Zero runtime changes, all required CI checks passed.

**M72 Closure Date:** 2026-01-20  
**M72 Achievement:** Determinism enforced and proven via canonical JSON serialization, bundle hash generation, and CI determinism gate. R2L is now a provably deterministic consumer certification harness with byte-stable outputs validated by CI.

**M73 Closure Date:** 2026-01-20  
**M73 Achievement:** Schema validation enforced and proven via JSON Schema (v1.0), artifact versioning, and CI schema validation gate. R2L artifacts are now deterministic (M72), schema-validated (M73), and versioned. Structural correctness is enforced by CI, and schema validation is fail-fast and pre-hash.

**M74 Closure Date:** 2026-01-20  
**M74 Achievement:** Adapter contract explicitly defined and enforced; MedGemma stub adapter added; CI adapter contract enforcement gate added. R2L adapters are now contract-bound and provider-agnostic. CI can now prove that provider choice does not affect artifact correctness, structure, or guarantees. Phase XV certification core is complete end-to-end.

**M75 Closure Date:** 2026-01-20  
**M75 Achievement:** Single certification verdict job established; certification verdict CI-enforced; machine-readable certification artifact generated. R2L now emits a single, authoritative consumer-certification verdict that aggregates all Phase XV enforcement signals. Phase XV is institutionally certifiable.

**M02 Closure Date:** 2026-01-20  
**M02 Achievement:** Post-Phase-XV Expansion Guardrails established with explicit governance boundaries. Post-Phase-XV expansion capabilities, prohibitions, invariants, and expansion rules are documented and auditable. All Phase XV guarantees explicitly preserved as non-negotiable constraints. Zero runtime impact, zero technical debt. Post-Phase-XV expansion governance discipline established.

**M03 Closure Date:** 2026-01-20  
**M03 Achievement:** Real Phi execution capability introduced with configurable mode (default: stub). All Phase XV guarantees preserved. CI continues to use deterministic stub for certification. Real execution is opt-in via `PHI_EXECUTION_MODE=real` and out-of-band from CI determinism guarantees. Coverage exclusions explicit and justified. MyPy checks passing with `warn_unused_ignores` respected. First Post-Phase-XV capability milestone completed without compromising Phase XV guarantees.

**M04 Closure Date:** 2026-01-21  
**M04 Achievement:** Multi-question orchestration capability introduced with deterministic ordering and fail-fast certification semantics. All Phase XV guarantees preserved (determinism, schema validation, adapter contract, binary certification). Backward compatibility maintained (single-question Golden Path unchanged). Code quality improved through disciplined refactoring (Radon complexity reduced, helper functions extracted). Pre-commit hooks introduced for developer ergonomics. Compositional execution core established—orchestration is no longer a special case. Second Post-Phase-XV capability milestone completed without compromising Phase XV guarantees.

**M05 Closure Date:** 2026-01-21  
**M05 Achievement:** Operational hardening introduced (input limits, timeouts, transactional writes, structured logging) while preserving all Phase XV guarantees. All functional requirements met, all tests passing (74/74), coverage 85.42%. Error taxonomy established with deterministic error codes and consistent HTTP status mapping. Transactional artifact writes ensure atomic finalization. Structured logging provides machine-readable event streams. Backward compatibility maintained (single-question Golden Path unchanged). Operational discipline established as first-class concern. One non-blocking CI toolchain issue documented (INFRA-CI-001). Third Post-Phase-XV capability milestone completed without compromising Phase XV guarantees.

**M06 Closure Date:** 2026-01-22  
**M06 Achievement:** INFRA-CI-001 resolved. Ruff format determinism verified in CI under pinned ruff (`==0.14.13`), deterministic invocation (`python -m ruff`), and config determinism (`working-directory: backend`). Prevention guardrails: `.gitattributes` LF enforcement; self-extracting diagnostics artifact. Lint step order ensures format check runs before Radon. Radon complexity reduced via minimal refactor; all required checks green. No gate weakening.

**M07 Closure Date:** 2026-01-22  
**M07 Achievement:** Branch protections and merge discipline established. `main` branch is now protected with 11 required CI checks enforced on merge. Direct pushes blocked (verified via GH006 rejection). Admin bypass disabled. Merge method set to squash-only. Governance documentation complete: `required-checks.md`, `branch-protection.md`, `merge-discipline.md`, `branch-protection-checklist.md`. CI truthfulness is now enforced by GitHub, not just cultural. PR template added for milestone discipline.

---

## Phase XV — Consumer Certification Posture

**Status:** ✅ **CLOSED** (2026-01-20)

**Phase XV Outcome:**

Phase XV successfully transformed R2L from a platform-in-progress into a **provably correct, deterministic, schema-validated, provider-agnostic consumer certification harness** with CI-enforced guarantees.

**Phase XV Achievements:**
- ✅ Deterministic execution enforced (M72)
- ✅ Schema-validated artifacts enforced (M73)
- ✅ Provider-agnostic adapters enforced (M74)
- ✅ Single certification verdict established (M75)

**Phase XV Guarantees:**
- R2L can produce a single, CI-enforced, machine-readable verdict certifying that a run is deterministic, schema-valid, and provider-agnostic
- Certification verdict is binary (CERTIFIED / NOT CERTIFIED) and CI-enforced
- All Phase XV guarantees are provably enforced by CI

**Phase XV Documentation:**
- `docs/milestones/phaseXV/PHASE_XV_CLOSEOUT.md` — Phase XV closeout summary
- `docs/milestones/phaseXV/PHASE_XV_AUDIT.md` — Phase XV meta-audit
- All milestone documentation (M71–M75) complete

**Authorized Next Phases:**
- Post-Phase-XV Expansion (M02+): Capability expansion (real MedGemma, multi-question labs, research orchestration)
- Pause: Phase XV provides portfolio-grade certification artifact suitable for external audit

**Any further work belongs to Post-Phase-XV expansion (M03+) or later.**

---

## Coverage Ramp Policy

Phase-appropriate coverage thresholds to prevent premature perfectionism while maintaining real enforcement.

### Frontend Coverage Thresholds

| Phase | Lines | Functions | Branches | Statements |
|-------|-------|-----------|----------|------------|
| **M00** (Bootstrap) | 75% | 50% | 70% | 75% |
| **M01** (Stabilization) | 80% | 65% | 75% | 80% |
| **M02+** (Production) | 85% | 85% | 85% | 85% |

**Rationale:**
- **M00:** Bootstrap entry points (e.g., `main.tsx`) have minimal testable logic; thresholds calibrated for phase
- **M01:** UI stabilizes; thresholds increase to reflect production readiness
- **M02+:** Full production thresholds; all entry points properly tested

**Current Phase:** M01  
**Current Thresholds:** See `frontend/vite.config.ts` thresholds configuration (M01 levels: 80% lines, 65% functions, 75% branches, 80% statements)

### Backend Coverage Thresholds

| Phase | Lines | Branches |
|-------|-------|----------|
| **M00+** | 85% | 80% |

**Rationale:** Backend contracts and runner logic require high coverage from bootstrap to ensure correctness.

**Current Configuration:** See `backend/.coveragerc`

---

## Database Schema

_(No database schema yet—will be added when data persistence is introduced)_

---

## Migrations

_(No migrations yet—will be added when database schema is introduced)_

---

## Policy Decisions

### MyPy Type Checking

**Decision:** Use targeted overrides to ignore missing imports for FastAPI ecosystem packages.

**Configuration:** See `backend/pyproject.toml` `[tool.mypy.overrides]`

**Rationale:**
- Preserves strictness for our code
- Avoids false negatives from ecosystem typing gaps
- Keeps the door open to tightening later (M02+)

**Modules Overridden:**
- `pydantic.*`
- `fastapi.*`
- `fastapi.middleware.*`
- `uvicorn.*`

**M01 Update:** Overrides explicitly quarantined with comment block marking them as ecosystem exceptions (not precedent). Any expansion requires explicit milestone decision.

### CI Optional Jobs

**Decision:** Make Dependency Review and Build Provenance explicitly optional with `continue-on-error: true`.

**Rationale:**
- These features require GitHub Advanced Security or repository settings
- Clean skips with explanation preserve CI truthfulness
- Prevents false failures for forks and local testing

**Jobs:**
- Dependency Review: Skip message explains Dependency Graph requirement
- Build Provenance: Skip message explains attestations API requirement
- Netlify Preview: Skips cleanly when secrets not set

### SBOM Generation

**Decision:** Use CycloneDX SBOM generation via `cyclonedx-py environment` subcommand.

**Command:** `cyclonedx-py environment -o sbom.cdx.json`

**Rationale:**
- Standardized SBOM format for supply chain transparency
- Required artifact for enterprise/government compliance
- Generated on every CI run and uploaded as artifact

---

## Architecture Decisions

### Phi Canary Adapter

**Decision:** Use Microsoft Phi model as the canary adapter for M00.

**Rationale:**
- Small, deterministic, fast, cost-effective
- Suitable for control group experiments and CI canaries
- Clear adapter boundary (all model-specific logic in adapters)

**Location:** `backend/src/r2l/adapters/phi.py`

### Model Adapter Boundary

**Decision:** All model-specific logic resides in adapter implementations.

**Architecture:**
- `ModelAdapter` Protocol/ABC defines the interface
- Each model has its own adapter implementation
- Runner is model-agnostic and works with any adapter

**Rationale:**
- Clear separation of concerns
- Enables multi-model parity testing
- Prevents model-specific logic from contaminating core system

---

## Phase XV — Consumer Certification Posture (Historical)

**Status:** ✅ **CLOSED** (2026-01-20)

During Phase XV, R2L functions strictly as a **consumer certification harness** for RediAI v3.

### Core Principles

1. **R2L is a consumer, not a platform**
   - R2L _consumes_ RediAI v3
   - R2L does **not** evolve independently in this phase
   - Any change requiring RediAI v3 modification is **out of scope**

2. **RediAI v3 is a read-only provider**
   - RediAI v3 is treated as a read-only dependency
   - No Phase XV milestone may require changes to v3 internals
   - Integration must be pinned to release tags only

3. **Golden Path exclusivity**
   - Exactly **one** canonical execution path is supported: `examples/hello-lab/README.md`
   - All CI certification uses this single path
   - No alternate "example" paths may claim parity during Phase XV

4. **Determinism expectation**
   - Phase XV execution must be deterministic and reproducible
   - Two identical runs with the same seed must produce byte-stable or schema-stable outputs
   - Explicit determinism enforcement is introduced in M72+

5. **Explicit scope boundaries**
   - Any work that expands R2L into a general-purpose platform is **post-Phase-XV expansion**
   - Deployment surface changes are **post-Phase-XV expansion**
   - Model-dependent runtime variability beyond adapters is **post-Phase-XV expansion**

### Phase XV Execution Contract

The Phase XV execution contract is declared in:
- **Governance:** This section (`r2l.md`) — defines what is allowed
- **Operational:** `examples/hello-lab/README.md` — defines what to run

**Contract Elements:**
- One canonical README (`examples/hello-lab/README.md`)
- One command to execute the Golden Path
- Required artifacts: run manifest (`manifest.json`, naming subject to M72 enforcement), artifacts directory, bundle hash (or placeholder), report, trace pack, repro pack
- Determinism: byte-stable or schema-stable outputs (explicit choice in M72)

**Enforcement:**
- M71: Contract declared (documentation-only)
- M72: Contract enforced (determinism, manifest hardening, bundle hash, CI determinism gate)
- M73: Contract enforced (artifact schema validation and versioning, CI schema gate, structural invariants documented)
- M74: Contract enforced (adapter contract validation, CI adapter contract gate, provider-agnostic artifact generation)
- M75: Contract enforced (consumer certification verdict, single CI gate, certification artifact)

### Consumer Certification (M75)

**Status:** Active (M75+)

R2L provides a **single, authoritative consumer certification verdict** that answers: _"Is this run consumer-certified?"_

**Certification Requirements:**
- All prerequisite enforcement jobs must pass:
  - **Determinism Enforcement** (M72): Byte-stable outputs validated
  - **Schema Validation** (M73): Artifacts conform to versioned schemas
  - **Adapter Contract Enforcement** (M74): Adapters are contract-compliant and provider-agnostic

**Certification Verdict:**
- **CERTIFIED**: All prerequisite checks passed
- **NOT CERTIFIED**: Any prerequisite check failed, skipped, or cancelled

**Certification Artifact:**
- `certification.json` — Machine-readable certification verdict
  - `certified`: Boolean verdict
  - `phase`: "XV"
  - `milestone`: "M75"
  - `checks`: Status of each prerequisite check (pass/fail)
  - `timestamp`: ISO 8601 timestamp
  - `commit`: Git commit SHA

**CI Enforcement:**
- `consumer-certification` job is a **required check**
- Job depends on: `determinism`, `schema-validation`, `adapter-contract`
- Job fails if any prerequisite fails or if certification verdict is NOT CERTIFIED
- Certification artifact is uploaded as CI artifact

**Governance:**
- Certification is **binary** (CERTIFIED / NOT CERTIFIED)
- Certification is **CI-enforced** (no manual override)
- Certification is **Phase XV-complete** (all Phase XV guarantees validated)

---

## Deployment

### Backend

**Target:** Render (via deploy hooks)  
**Binding:** `0.0.0.0:8000`  
**Configuration:** See `ops/DEPLOYMENT.md`

### Frontend

**Target:** Netlify (PR previews + production)  
**Default API URL:** `http://localhost:8000` (configurable via `VITE_API_URL`)  
**Configuration:** See `ops/DEPLOYMENT.md`

---

## Security

### Security Scanning

- **Bandit:** Static analysis for security issues
- **pip-audit:** Dependency vulnerability scanning
- **Gitleaks:** Secret detection
- **OpenSSF Scorecard:** Security health metrics

### SBOM

- **Format:** CycloneDX (JSON)
- **Generation:** Automated on every CI run
- **Location:** `sbom.cdx.json` (uploaded as CI artifact)

---

## Documentation

- **User Docs:** `README.md`
- **Security:** `SECURITY.md`
- **Deployment:** `ops/DEPLOYMENT.md`
- **Model Adapters:** `ops/MODEL_ADAPTERS.md`
- **QA & Evidence:** `docs/qa.md`
- **Sphinx Docs:** `docs/` (published to GitHub Pages)

---

## Development Guidelines

1. **Read `r2l.md` first** before writing or modifying code
2. **Update `r2l.md` immediately** after completing a major feature or milestone
3. **Preserve modularity** — all changes must maintain or improve separation of concerns
4. **Document explicitly** — prefer clarity over cleverness
5. **Follow established patterns** unless there is a documented reason to deviate

---

**Last Updated:** 2026-01-22 (M07 Closure)  
**Maintained By:** R2L Contributors

