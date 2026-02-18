# Code Simplification Design

**Date:** 2026-02-17
**Goal:** Remove redundancy and over-engineering from both backend (Python) and frontend (TypeScript)
**Constraints:** Preserve functionality, pass all tests, internal breaking changes OK

## Current State

| Area | Size | Issues |
|------|------|--------|
| Backend Python | ~16k lines | 9 classes in `user.py`, 10 in `rhythm_training.py`, several `pass` stubs |
| Frontend TS | ~12k lines | 814-line `AudioContext`, 619-line `practiceService`, 24 TODOs/console.logs |

## Approach: Hybrid (Automated + Targeted Deep Dives)

### Phase 1: Automated Cleanup

- Remove unused imports (Python + TypeScript)
- Remove dead code (`pass` stubs, unreachable branches)
- Remove `console.log` statements and stale TODOs
- Format/lint pass to establish baseline

### Phase 2: Hot Spot Analysis

Analyze the 6 identified files for over-engineering patterns:
- Classes that could be functions
- Inheritance hierarchies that could be flat
- Duplicate logic across classes
- Overly generic abstractions

### Phase 3: Targeted Refactoring

Simplify each hot spot based on analysis:
- Consolidate redundant classes
- Flatten unnecessary hierarchies
- Extract shared logic where genuinely needed

## Hot Spot Targets

| File | Current State | Simplification Goal |
|------|---------------|---------------------|
| `core/models/user.py` | 9 classes | Consolidate related classes, remove unused |
| `api/tala/rhythm_training.py` | 10 classes | Flatten hierarchy if over-abstracted |
| `api/gamification/achievements.py` | 8 classes | Reduce if classes could be data/functions |
| `api/error_handlers.py` | Multiple `pass` stubs | Remove dead code paths |
| `frontend/src/contexts/AudioContext.tsx` | 814 lines | Extract reusable logic, reduce duplication |
| `frontend/src/services/practiceService.ts` | 619 lines | Consolidate similar API calls |

## Verification Strategy

**After each change:**
- Run existing tests (`make test` for backend, `npm run lint` for frontend)
- Verify no regressions

**Rollback approach:**
- Commit after each phase
- If a hot spot refactor causes issues, revert and reassess

## Success Criteria

- All existing tests pass
- Reduced line count in hot spot files
- Fewer classes where consolidation makes sense
- No dead code or unused imports remaining
