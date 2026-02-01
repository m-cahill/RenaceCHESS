According to a document from the M22 audit and Phase C audit, Phase D’s highest-leverage “first hardening” work is **(1) add security scanning to CI, (2) add performance regression benchmarks, and (3) raise CLI coverage (noted at ~72% in the audit)**—all **additive** and low-blast-radius. 

Below is a **Cursor-ready milestone plan** for **M23**.

---

# M23_plan — PHASE-D-HARDENING-001

**Phase:** D (Human Evaluation / UX / Interaction layers) — *Foundational hardening before we add new surfaces/providers*
**Milestone intent:** Address audit-flagged deficiencies with minimal architectural disturbance.

## 0) Milestone framing

### Objective

Implement **enterprise-grade guardrails** that were explicitly called out as “missing” in audit:

1. **Security scanning** in CI: `pip-audit` + `bandit` 
2. **Performance regression** harness in CI using `pytest-benchmark`, starting with the recommended “Context Bridge latency” test shape 
3. **CLI coverage uplift** to ≥90% line coverage for `src/renacechess/cli.py` (audit notes CLI coverage deficiency) 
4. Add *local guardrail* to prevent repeat of format/lint-only CI failures: **pre-commit hooks** (recommended in audit). 

### Non-goals (explicitly out of scope for M23)

* No changes to **frozen** Phase C contracts/prompting (AdviceFactsV1, DeltaFactsV1, Coaching*V1, prompt v1).
* No real LLM provider integration (Phase D will do this later; keep M23 purely hardening).
* No UI/UX work, no new coaching semantics, no new engines.

---

## 1) Deliverables checklist (what must exist at PR merge)

### A) New CI security job (required check)

* Add `security` job to `.github/workflows/ci.yml`:

  * installs project deps (or minimal deps) + installs `pip-audit` and `bandit`
  * runs:

    * `pip-audit` (configured to work with current dependency setup; see implementation notes below)
    * `bandit -r src/renacechess -ll` (and exclude tests if needed)
* Job must be SHA-pinned actions (same posture as existing CI).

**Acceptance criteria**

* CI shows a distinct **Security Scan** job that passes on main.
* Fails loudly on findings (no “soft pass”), unless explicitly deferred with rationale in the milestone docs.

### B) Performance regression harness (low-flake posture)

* Add `pytest-benchmark` to dev dependencies.
* Create a small benchmark test module, e.g. `tests/test_m23_perf_benchmarks.py` with:

  * `@pytest.mark.benchmark`
  * a **single “Context Bridge latency” benchmark** using representative FEN(s), aligned with the audit’s recommended pattern. 
* Add a CI job `perf` (recommended: required if stable, otherwise optional-but-visible with explicit rationale in plan).

**Acceptance criteria**

* Benchmark tests run in CI (either as required check or clearly labeled optional check).
* Benchmark outputs are uploaded as artifacts (JSON) for inspection.
* Any thresholds are **conservative** to avoid flakiness (start with “smoke-level” assertions; tighten in later milestone if needed).

### C) CLI coverage uplift to ≥90% for `cli.py`

* Add tests to exercise:

  * top-level `main()` dispatch for existing subcommands
  * help/usage paths
  * invalid argument paths
  * error handling branches (exit codes)
* Use the same “direct main() calls” technique that worked well in M22 tests. 

**Acceptance criteria**

* `coverage` report shows `src/renacechess/cli.py` ≥ 90% line coverage.
* Overall suite remains ≥90% (standing gate).

### D) Pre-commit guardrail (dev-only, not CI-breaking)

* Add `.pre-commit-config.yaml` with:

  * `ruff` (lint)
  * `ruff-format` (format)
* Update README or CONTRIBUTING with “one-liner” install/use.
* This directly addresses the audit’s “format/lint run locally” recommendation. 

**Acceptance criteria**

* `pre-commit install` works locally.
* No CI dependency on pre-commit (CI remains source-of-truth).

### E) M23 governance artifacts

Create:

* `docs/milestones/PhaseD/M23/M23_plan.md`
* `docs/milestones/PhaseD/M23/M23_toolcalls.md`
* (post-run) `M23_run1.md`, `M23_audit.md`, `M23_summary.md`
* Update `renacechess.md` to add M23 row (status OPEN → CLOSED at closeout).

---

## 2) PR-sized execution plan (Cursor-friendly sequence)

### PR1 — “M23: Security Scan Job”

1. Add `pip-audit` + `bandit` job to CI.
2. Ensure actions are SHA-pinned.
3. Add minimal documentation under `docs/security/` or inside M23 plan notes (how to run locally).

**Guardrails**

* Keep job isolated: no changes to existing lint/type/test jobs.
* If `pip-audit` needs a lock/requirements export, implement the smallest working approach first (see Implementation Notes).

### PR2 — “M23: Benchmark Harness + CI Perf Job”

1. Add `pytest-benchmark` and a `tests/test_m23_perf_benchmarks.py`.
2. Add a CI job `perf` that runs only benchmark-marked tests:

   * `pytest -m benchmark --benchmark-only ...`
3. Upload benchmark JSON artifact.

**Guardrails**

* Avoid strict microsecond thresholds initially; prefer conservative smoke thresholds.
* Keep the benchmark suite tiny (1–3 tests max).

### PR3 — “M23: CLI Coverage Uplift”

1. Add new tests targeting uncovered `cli.py` branches.
2. Verify `cli.py` line coverage ≥90%.
3. Ensure no snapshot brittleness (assert structured outputs / exit codes).

### PR4 — “M23: Pre-commit + DX note”

1. Add `.pre-commit-config.yaml` with ruff + ruff-format.
2. Add short docs snippet: install + run.

---

## 3) Implementation notes (to prevent churn)

### pip-audit reality check

The audit suggested a `--require-hashes` style invocation, but that only works cleanly if we have a hashed lock/requirements file. 
**M23 approach:**

* Start with a working CI scan (even if it’s environment-based), then optionally add lockfile rigor in a later milestone if desired.

### Performance check stability

Hosted CI runners vary. For M23:

* Start with **smoke-level** thresholds + artifact upload.
* Tighten thresholds later after we observe variance across a few runs.

---

## 4) Exit criteria (merge gate)

M23 is **CLOSEABLE** only when:

* CI includes **Security Scan** job passing on main. 
* CI includes **Perf** benchmark execution (required or explicitly optional with documented rationale).
* `cli.py` coverage ≥90% and overall ≥90%.
* Pre-commit config exists + documented.
* M23 audit shows **no new deferrals** unless explicitly justified.

---

## 5) Deferred registry (allowed, but must be explicit)

If anything must be deferred, limit to **one** of:

* SBOM generation (CycloneDX) as a release-only concern
* Dependency upper-bound tightening (e.g., `pydantic<3`)
  Both are mentioned as opportunities in audits, but M23 should prioritize the **three missing CI controls** first. 

---

## 6) Suggested branch / naming

* Branch: `m23-phase-d-hardening-001`
* Milestone title: **M23 — PHASE-D-HARDENING-001: Security + Perf + CLI Coverage**

---

If Cursor follows this plan, M23 becomes the “Phase D runway”: we fix the audit-noted missing controls first, then proceed to Phase D’s actual product-facing work (human eval loops, UX surfaces, real provider integration) on top of a stronger CI truth posture.
