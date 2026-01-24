# M04 Tool Calls Log

**Milestone:** M04  
**Status:** 🔄 **IN PROGRESS**

---

## Tool Call Entries

### 2026-01-23 - Phase 0 & 1: Initialization & Plan Review

**Tool:** `read_file`  
**Purpose:** Read M04 plan document to understand objective and DoD  
**Files:** `docs/milestones/PoC/M04/M04_plan.md`  
**Status:** ✅ Complete

**Tool:** `read_file`  
**Purpose:** Review CLI structure to understand command patterns  
**Files:** `src/renacechess/cli.py`  
**Status:** ✅ Complete

**Tool:** `read_file`  
**Purpose:** Review contract models to understand schema patterns  
**Files:** `src/renacechess/contracts/models.py` (partial)  
**Status:** ✅ Complete

**Tool:** `read_file`  
**Purpose:** Review dataset manifest structure for v2 format  
**Files:** `src/renacechess/dataset/manifest.py`  
**Status:** ✅ Complete

**Tool:** `codebase_search`  
**Purpose:** Understand dataset record structure and ground truth move field  
**Files:** Multiple (docs, schemas, builder)  
**Status:** ✅ Complete

**Tool:** `read_file`  
**Purpose:** Review determinism utilities for stable hashing  
**Files:** `src/renacechess/determinism.py`  
**Status:** ✅ Complete

**Tool:** `read_file`  
**Purpose:** Review demo payload generation to understand record structure  
**Files:** `src/renacechess/demo/pgn_overlay.py` (partial)  
**Status:** ✅ Complete

### 2026-01-23 - Phase 2: Clarifying Questions Resolution

**Decision:** Defer ground-truth accuracy metrics. Focus on policy validity metrics:
- Illegal move rate
- Top-K legal coverage  
- Policy entropy
- Output cardinality
- Records evaluated

**Rationale:** Current dataset records represent decision contexts, not decisions. Adding `chosenMove` would violate milestone discipline and require retroactive schema changes.

**Status:** ✅ Locked - Proceeding to Phase 3 (Implementation)

### 2026-01-23 - Phase 3: Implementation - Phases 1-3 Complete

**Tool:** `write`  
**Purpose:** Create eval package with interfaces, baselines, metrics, runner, report modules  
**Files:** `src/renacechess/eval/*.py`  
**Status:** ✅ Complete

**Tool:** `search_replace`  
**Purpose:** Add CLI command `renacechess eval run`  
**Files:** `src/renacechess/cli.py`  
**Status:** ✅ Complete

**Tool:** `write`  
**Purpose:** Create unit tests for baselines and metrics  
**Files:** `tests/test_eval_baselines.py`, `tests/test_eval_metrics.py`  
**Status:** ✅ Complete

**Tool:** `write`  
**Purpose:** Create integration/golden test for determinism  
**Files:** `tests/test_eval_integration.py`  
**Status:** ✅ Complete

**Tool:** `write`  
**Purpose:** Create evaluation documentation  
**Files:** `docs/EVALUATION.md`  
**Status:** ✅ Complete

### 2026-01-23 - Phase 3: Implementation - Phase 1 (Contracts)

**Tool:** `run_terminal_cmd`  
**Purpose:** Check git status and create branch m04-eval-harness  
**Files:** N/A  
**Status:** ✅ Complete

**Tool:** `write`  
**Purpose:** Create eval_report.v1.schema.json with policy validity metrics  
**Files:** `src/renacechess/contracts/schemas/v1/eval_report.v1.schema.json`  
**Status:** ✅ Complete

**Tool:** `search_replace`  
**Purpose:** Add EvalReportV1 Pydantic models to contracts/models.py  
**Files:** `src/renacechess/contracts/models.py`  
**Status:** ✅ Complete
