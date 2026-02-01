# 📌 Milestone Summary — M19: ADVICE-FACTS-CONTRACT-001

**Project:** RenaceCHESS  
**Phase:** Phase C — Elo-Appropriate Coaching & Explanation  
**Milestone:** M19 — ADVICE-FACTS-CONTRACT-001  
**Timeframe:** 2026-01-31 → 2026-02-01  
**Status:** ✅ Closed

---

## 1. Milestone Objective

M19 establishes the foundational contract for Phase C coaching capabilities. Without this milestone:

- LLM coaching would have no grounded facts to translate
- Coaching outputs could hallucinate tactical analysis
- No determinism or auditability for coaching artifacts
- No import boundary isolating coaching from core model layers

This milestone answers: **What is the facts-only substrate for LLM coaching?**

The objective derives from `docs/postpocphasemap.md` Phase C entry requirements and `docs/foundationdocs/renacechessPhaseBaudit.md` recommendation for ADR-COACHING-001.

---

## 2. Scope Definition

### In Scope

| Component | Description |
|-----------|-------------|
| ADR-COACHING-001 | Coaching truthfulness ADR ("LLMs translate, not invent") |
| ADVICE_FACTS_CONTRACT_v1 | Frozen schema contract for facts-only artifacts |
| advice_facts.v1.schema.json | JSON Schema for validation |
| AdviceFactsV1, AdviceFactsInputsV1 | Pydantic models |
| coaching/advice_facts.py | Pure builder function |
| import-linter coaching-isolation | Architectural boundary enforcement |
| tests/test_m19_advice_facts.py | 27 tests (schema, determinism, ordering) |
| Audit quick wins | Pinned pydantic/torch, requirements.txt lockfile |

### Out of Scope

| Item | Reason |
|------|--------|
| Elo-bucket delta reasoning | Deferred to M20 |
| LLM translation harness | Deferred to M21 |
| Coaching CLI commands | Deferred to M22 |
| explanationHints population | M20+ placeholder |
| Provider orchestration | Builder is pure function; providers stay out of scope |

No scope changes occurred during execution.

---

## 3. Work Executed

### Artifacts Created

| Type | Count | Notes |
|------|-------|-------|
| New module | 1 | `coaching/` with `__init__.py`, `advice_facts.py` |
| New contract doc | 1 | `ADVICE_FACTS_CONTRACT_v1.md` |
| New ADR | 1 | `ADR-COACHING-001.md` |
| New JSON Schema | 1 | `advice_facts.v1.schema.json` |
| Pydantic models | 10 | AdviceFactsV1, inputs, sub-models |
| Test file | 1 | 27 tests |
| Import-linter contract | 1 | `coaching-isolation` |

### Configuration Changes

| File | Change |
|------|--------|
| `pyproject.toml` | Pinned `pydantic~=2.10.0`, `torch~=2.2.0` |
| `importlinter_contracts.ini` | Added `coaching-isolation` rule |
| `requirements.txt` | Generated full lockfile |

### Mechanical Fixes (Run 1 → Run 2)

| Fix | Type |
|-----|------|
| `ruff format .` | 4 files reformatted |
| AccuracyMetrics ConfigDict | Pre-existing MyPy issue resolved |

---

## 4. Validation & Evidence

### CI Runs

| Run | ID | Status | Duration |
|-----|-----|--------|----------|
| Run 1 | 21553586177 | ❌ Failed | 5m24s |
| Run 2 | 21553672113 | ✅ Success | 4m42s |

### Test Results

- **Tests:** 512 passed, 1 skipped
- **Coverage:** 91.33% (threshold: 90%)
- **M19-specific coverage:** 100% for coaching/advice_facts.py

### Validation Quality

| Check | Status |
|-------|--------|
| Schema validation (JSON Schema) | ✅ Tested |
| Pydantic model validation | ✅ Tested |
| Determinism (same inputs → same hash) | ✅ Tested |
| Move ordering (prob desc, UCI asc) | ✅ Tested |
| Float precision (6 decimals) | ✅ Tested |
| Outcome probability sum ≈ 1.0 | ✅ Tested |

---

## 5. CI / Automation Impact

### Import-Linter

All 3 contracts verified:

| Contract | Status |
|----------|--------|
| contracts-isolation | ✅ Kept |
| personality-isolation | ✅ Kept |
| coaching-isolation | ✅ Kept (new) |

### Workflow Changes

No workflow changes. Existing CI correctly:
- Blocked formatting issues (Run 1)
- Surfaced pre-existing MyPy issue (Run 1)
- Validated fix (Run 2)

This demonstrates "CI as active governance."

---

## 6. Issues & Exceptions

| Issue | Root Cause | Resolution |
|-------|------------|------------|
| Ruff format check failed | Files not formatted before commit | `ruff format .` applied |
| MyPy ConfigDict error | Pre-existing issue in AccuracyMetrics | Fixed with `populate_by_name=True` |

Both issues were non-semantic and did not affect M19 logic.

No new issues were introduced during this milestone.

---

## 7. Deferred Work

No new deferrals. `explanationHints` is a documented placeholder for M20+, not a deferral.

---

## 8. Governance Outcomes

### What is now provably true:

1. **Coaching has a grounded facts layer** — AdviceFacts artifacts contain only pre-computed signals
2. **LLMs cannot access core models** — coaching-isolation import-linter contract enforced
3. **Coaching is deterministic** — SHA-256 hash verifies reproducibility
4. **Schema is frozen** — ADVICE_FACTS_CONTRACT_v1 is immutable
5. **ADR governs Phase C** — ADR-COACHING-001 establishes "translate, not invent" principle

### Boundary Enforcement

```
[core: contracts, eval, features, models]
            |
            | ✅ coaching-isolation (FORBIDDEN)
            ↓
[coaching: advice_facts.py]
            |
            | ✅ can import contracts/models
            ↓
[LLM translation: M21+]
```

---

## 9. Exit Criteria Evaluation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| ADR-COACHING-001 exists | ✅ Met | `docs/adr/ADR-COACHING-001.md` |
| ADVICE_FACTS_CONTRACT_v1 frozen | ✅ Met | `docs/contracts/ADVICE_FACTS_CONTRACT_v1.md` |
| JSON Schema + Pydantic models | ✅ Met | Schema + 10 models in contracts/models.py |
| Pure builder function | ✅ Met | `build_advice_facts_v1()` accepts pre-computed signals |
| Import boundary enforced | ✅ Met | `coaching-isolation` contract kept |
| Tests passing | ✅ Met | 27 M19 tests, 512 total |
| Coverage ≥ 90% | ✅ Met | 91.33% |
| CI green | ✅ Met | Run 21553672113 |

All exit criteria met.

---

## 10. Final Verdict

**Milestone objectives met. Safe to proceed.**

M19 is a textbook Phase C entry run. The CI failure (Run 1) surfaced pre-existing tech debt and was resolved without semantic changes. No regressions, no scope creep.

---

## 11. Authorized Next Step

**Authorized:**
- ✅ Close M19
- ✅ Advance to M20 (Elo-bucket delta reasoning)
- ✅ Phase C is officially entered

**Not Authorized:**
- ❌ LLM translation (M21)
- ❌ Coaching CLI commands (M22)

---

## 12. Canonical References

| Reference | Location |
|-----------|----------|
| PR | https://github.com/m-cahill/RenaceCHESS/pull/25 |
| Merge Commit | `8404d9e` |
| CI Run (green) | 21553672113 |
| ADR | `docs/adr/ADR-COACHING-001.md` |
| Contract | `docs/contracts/ADVICE_FACTS_CONTRACT_v1.md` |
| Schema | `src/renacechess/contracts/schemas/v1/advice_facts.v1.schema.json` |
| Builder | `src/renacechess/coaching/advice_facts.py` |
| Tests | `tests/test_m19_advice_facts.py` |
| CI Analysis | `docs/milestones/PhaseC/M19/M19_run1.md` |

---

**Generated:** 2026-02-01  
**Author:** RenaceCHESS Governance

