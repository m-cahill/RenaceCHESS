# RenaceCHESS Governance

## Milestone Conventions

Each milestone follows a structured workflow:

### Milestone Structure

- `MNN_plan.md` - Detailed implementation plan
- `MNN_toolcalls.md` - Log of all tool invocations
- `MNN_summary.md` - Milestone summary (generated post-completion)
- `MNN_audit.md` - Lightweight audit (what was added, what was deferred, CI evidence)

### Workflow Phases

1. **Phase 0: Initialization & Recovery** - Check toolcalls log, restate progress
2. **Phase 1: Plan Review** - Read plan, identify objective and definition of done
3. **Phase 2: Clarifying Questions** - Ask questions, wait for locked answers
4. **Phase 3: Implementation** - Create branch, implement, commit, create PR
5. **Phase 4: CI Monitoring & Analysis** - Monitor CI, create analysis document
6. **Phase 5: Governance Updates** - Update renacechess.md after CI green
7. **Phase 6: Audit & Summary** - Generate audit and summary documents
8. **Phase 7: Closeout** - Final verification and milestone closure

## CI Truthfulness Principle

**"Green = Safe, Red = Meaningful Debt"**

- Required checks must remain truthful
- No weakening of gates without explicit justification
- All deviations documented in milestone audit

## Scope Discipline

- One milestone = one scoped change-set
- No scope creep
- Deferred work explicitly documented with rationale

## Determinism

- Prefer deterministic artifacts + golden tests over "looks right" validation
- All outputs must be reproducible
- Canonical JSON serialization for all structured data

## Documentation Requirements

Every milestone must produce:

- Plan document (before implementation)
- Summary document (after completion)
- Audit document (what was added, deferred, CI evidence)

