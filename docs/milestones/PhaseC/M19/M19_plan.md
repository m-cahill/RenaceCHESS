According to a document from **2026-01-31**, Phase B is cleanly closed and Phase C is explicitly queued to start at **M19 (“Define AdviceFacts contract”)**, with a small set of *high-leverage, low-effort* audit gaps to close immediately (pydantic/torch pins, lockfile, etc.).

## Proceeding into Phase C

* **Yes: proceed with M19 as the Phase C entry milestone.** The Phase B audit literally calls out M19 as the next architecture milestone (“Define AdviceFacts contract”).
* **Yes: we should slightly reevaluate Phase C sequencing**, but not by changing the spirit—by making it *more PR-sized and governance-aligned*: do the “facts contract” first, then “facts generation,” then “LLM translation,” then “coaching evaluation + CLI expansion.” (This matches the audit’s recommended ADR for coaching and the Phase C focus statement.)

The **Deferred Issues Registry** currently shows **no active deferred issues**, which is great—but the Phase B audit still lists a few *remaining gaps* that should be addressed promptly to keep audit posture high (pins, lockfile, security scan, CLI coverage).

---

# M19_plan — ADVICE-FACTS-CONTRACT-001 (Phase C Kickoff)

Hand this plan to Cursor as-is.

## 0) Milestone intent

**M19 defines the “AdviceFacts” contract**: a deterministic, schema-stable “facts only” artifact that downstream LLMs can translate into Elo-appropriate coaching *without inventing chess analysis*.

This is the Phase C equivalent of what the **Personality Safety Contract** was for Phase B: the hard boundary that keeps prose generation honest.

## 1) Scope

### In-scope

1. **AdviceFacts schema + Pydantic model (v1)**

   * New JSON Schema under `src/renacechess/contracts/schemas/v1/`
   * New Pydantic model in `src/renacechess/contracts/models.py` (or a dedicated contracts module file if that’s already a pattern)

2. **AdviceFacts contract doc (v1)**

   * New contract doc: `docs/contracts/ADVICE_FACTS_CONTRACT_v1.md`

3. **ADR for coaching truthfulness**

   * Create `docs/adr/ADR-COACHING-001.md` (“LLM coaching must use grounded facts only; no invention”). This is explicitly recommended in the Phase B audit for Phase C.

4. **Deterministic “builder” stub**

   * A small implementation that **constructs AdviceFactsV1 from already-computed signals** (policy distribution, W/D/L head outputs, HDI, structural cognition), with strict determinism rules.
   * No prose generation. No LLM calls.

5. **Audit posture quick wins (fold into M19 because they’re trivial)**

   * Pin **pydantic** and **torch** from `>=` to `~=` (explicitly called out as ~5 minutes).
   * Add a **requirements lockfile** (the audit suggests `pip freeze > requirements.txt`).
   * Add `.env` to `.gitignore` if missing (called out in audit “Phase 0 — Fix-First & Stabilize”).

> Rationale for folding these into M19: they reduce supply-chain drift risk and raise audit score without expanding Phase C semantics. The audit recommends doing them “Immediate (Today).”

### Out-of-scope (explicit)

* No LLM translation prompts/rules beyond the ADR
* No Elo-bucket delta reasoning implementation (that’s M20)
* No new training runs or benchmarks
* No new data ingestion
* No CLI expansion unless required to test the builder (keep it minimal)

## 2) Proposed AdviceFactsV1 contents (contract-level)

AdviceFacts should be *facts, not advice text*. Suggested fields:

### Required core

* `version`
* `generatedAt`
* `position`:

  * `fen`
  * `sideToMove`
* `context`:

  * `skillBucket` (or Elo bucket)
  * `timeControlBucket` / `timePressureBucket` (if already defined in conditioning)
* `policy`:

  * `topMoves`: ordered list of `{uci, prob}` (optionally SAN if already available deterministically)
  * `recommendedMove`: `{uci, prob}`
* `outcome`:

  * `pWin`, `pDraw`, `pLoss` (conditioned)
* `hdi`:

  * `value` (and any already-defined subcomponents if stable)
* `structuralCognition` (optional but supported):

  * summarized deltas derived from M11 features (mobility/weak squares/etc.)

### Determinism + audit fields

* `determinismHash`: SHA-256 of canonical JSON (stable key ordering, stable float rounding)
* `sourceContractVersions`: references to relevant frozen contracts (Input semantics v1, Structural cognition v1, etc.)

> Note: M19 should define the schema to *allow* richer “why tags” later (e.g., `explanationHints[]`) but **must not** implement speculative heuristics yet.

## 3) File/Module layout (suggested)

* `src/renacechess/contracts/schemas/v1/advice_facts.v1.schema.json` *(new)*
* `docs/contracts/ADVICE_FACTS_CONTRACT_v1.md` *(new)*
* `docs/adr/ADR-COACHING-001.md` *(new)*
* `src/renacechess/coaching/advice_facts.py` *(new builder stub; facts-only)*
* `tests/contracts/test_advice_facts_schema.py`
* `tests/coaching/test_advice_facts_determinism.py`

Add/import-linter rules if needed to keep **coaching** as bounded as personality modules (contracts-first, no hidden coupling).

## 4) Acceptance criteria (Definition of Done)

### Contract + schema

* [ ] AdviceFacts JSON Schema (v1) committed
* [ ] Pydantic model validates against schema
* [ ] Contract doc written and marked **FROZEN v1** once merged

### Determinism + safety

* [ ] Builder produces byte-stable JSON for same inputs (determinism test)
* [ ] Stable ordering for top moves (by prob desc, then move tiebreak)
* [ ] Canonical float rounding rule documented + tested
* [ ] No LLM usage anywhere in M19

### Audit posture quick wins (from Phase B audit)

* [ ] `pyproject.toml`: `pydantic~=2.10.0`, `torch~=2.2.0` (or your chosen compatible pins)
* [ ] `requirements.txt` committed as lockfile
* [ ] `.env` included in `.gitignore` if missing

### CI / tests

* [ ] CI stays truthful: no weakened gates; coverage ≥ 90%
* [ ] New tests added for schema + determinism
* [ ] All required checks green

## 5) Test plan (end-to-end appropriate)

1. **Schema roundtrip**

   * Create a minimal AdviceFacts fixture JSON
   * Validate with jsonschema
   * Validate with Pydantic
2. **Determinism**

   * Given a fixed input payload + fixed policy/outcome arrays → builder output identical across multiple runs
3. **Contract boundary check**

   * Ensure dict-instantiation uses alias rules consistent with Contract Input Semantics v1 (don’t reintroduce ambiguity).

## 6) Guardrails

* **No invention rule (ADR-COACHING-001):** LLMs may only translate AdviceFacts fields; they may not compute or infer chess claims not present in facts.
* **Facts-only artifact:** AdviceFacts must remain interpretable and measurable (like the Phase B evaluation artifacts).
* **Rollback path:** deleting the coaching module + schema must cleanly revert Phase C work without touching PoC/Phase B semantics.

## 7) Recommended Phase C milestone re-evaluation (lightweight)

Keep the Phase B audit’s Phase C outline, but split it slightly finer so CI remains low-churn:

* **M19:** AdviceFacts contract + supply-chain quick wins (this plan)
* **M20:** Elo-guidance *facts generation* (bucket delta reasoning + heuristic scaffolds), still no prose
* **M21:** LLM translation harness + offline coaching quality eval (still deterministic)
* **M22:** Coaching CLI expansion + close CLI coverage gap as coaching commands expand (audit explicitly suggests CLI coverage belongs in Phase C).

(Separately: **pip-audit** scanning is recommended by the audit, but it’s ~30 minutes and touches CI. If you want ultra-minimal M19, push pip-audit to M20; otherwise add it as an optional “M19.5” hardening addendum.)

---

If you want this maximally Cursor-friendly, name the branch something like:

* `m19-advice-facts-contract-001`

…and have Cursor implement strictly in the order:

1. pins + lockfile + gitignore (fast, reduces audit risk),
2. ADR + schema/model,
3. builder stub,
4. tests,
5. docs updates + milestone ledger entry.
