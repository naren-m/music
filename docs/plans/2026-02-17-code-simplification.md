# Code Simplification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove redundancy and over-engineering from both backend (Python) and frontend (TypeScript)

**Architecture:** Three-phase approach: (1) automated cleanup of dead code and unused imports, (2) analysis of 6 hot spot files, (3) targeted refactoring based on findings. Each phase commits separately for easy rollback.

**Tech Stack:** Python (Flask), TypeScript (React), pytest, ESLint

---

## Phase 1: Automated Cleanup

### Task 1: Verify Baseline Tests Pass

**Files:**
- None modified

**Step 1: Run backend tests**

```bash
cd /Users/narenmudivarthy/Projects/music
make test
```

Expected: All tests pass

**Step 2: Run frontend lint**

```bash
cd /Users/narenmudivarthy/Projects/music/frontend
npm run lint
```

Expected: No errors (warnings OK)

---

### Task 2: Remove Dead Python Code (pass stubs)

**Files:**
- Modify: `api/error_handlers.py`
- Modify: `modules/swara/trainer.py`

**Step 1: Find all empty pass stubs**

```bash
grep -rn "pass$" api core modules --include="*.py"
```

Review each result. Remove `pass` statements that are:
- Inside empty except blocks with TODO comments
- Placeholder methods that are never called

**Step 2: Remove dead pass stubs in api/error_handlers.py**

Lines to examine: 115, 288, 338
- If the function/block does nothing, remove the entire block
- If it's a valid placeholder (abstract method), keep it

**Step 3: Remove dead pass stubs in modules/swara/trainer.py**

Line 552: Remove if unused

**Step 4: Run backend tests**

```bash
make test
```

Expected: All tests pass

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor: remove dead pass stubs from error handlers and trainer"
```

---

### Task 3: Remove console.log Statements (Frontend)

**Files:**
- Multiple frontend files

**Step 1: Find all console.log statements**

```bash
cd /Users/narenmudivarthy/Projects/music/frontend
grep -rn "console.log" src --include="*.ts" --include="*.tsx"
```

**Step 2: Remove debug console.logs**

Remove any `console.log` that:
- Logs debug/temp info
- Was clearly added during development

Keep any `console.log` that:
- Logs critical errors (`console.error`)
- Is part of intentional user feedback

**Step 3: Run frontend lint**

```bash
npm run lint
```

Expected: No errors

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: remove debug console.log statements"
```

---

### Task 4: Remove Stale TODOs

**Files:**
- Multiple files

**Step 1: Find all TODOs**

```bash
grep -rn "TODO\|FIXME" api core modules frontend/src --include="*.py" --include="*.ts" --include="*.tsx"
```

**Step 2: Evaluate each TODO**

For each TODO:
- If the feature is already implemented elsewhere, remove the TODO
- If the TODO is outdated/no longer relevant, remove it
- If the TODO is still valid, leave it

**Step 3: Run tests**

```bash
make test
cd frontend && npm run lint
```

Expected: All pass

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: remove stale TODO comments"
```

---

## Phase 2: Hot Spot Analysis

### Task 5: Analyze core/models/user.py (9 classes)

**Files:**
- Read: `core/models/user.py`

**Step 1: List all classes and their purposes**

Document:
- `SkillLevel` (Enum) - Purpose?
- `SubscriptionTier` (Enum) - Purpose?
- `UserPreferences` (dataclass) - Purpose?
- `ModuleProgress` (dataclass) - Purpose?
- `Achievement` (dataclass) - Purpose?
- `LearningGoal` (dataclass) - Purpose?
- `PracticeSession` (dataclass) - Purpose?
- `UserProfile` (dataclass) - Purpose?
- `UserModel` (class) - Purpose?

**Step 2: Identify consolidation opportunities**

- Are any classes only used internally by another?
- Could any class be a simple dict or namedtuple?
- Are there duplicate fields across classes?

**Step 3: Document findings in this file**

Add analysis notes below:

```
[ANALYSIS: core/models/user.py]
Consolidation opportunities:
- TBD
Classes to keep:
- TBD
Classes to merge/remove:
- TBD
```

---

### Task 6: Analyze api/tala/rhythm_training.py (10 classes)

**Files:**
- Read: `api/tala/rhythm_training.py`

**Step 1: List all classes**

**Step 2: Identify hierarchy depth**

- Is there deep inheritance that could be flattened?
- Are there abstract classes with only one implementation?

**Step 3: Document findings**

```
[ANALYSIS: api/tala/rhythm_training.py]
Hierarchy issues:
- TBD
Consolidation opportunities:
- TBD
```

---

### Task 7: Analyze api/gamification/achievements.py (8 classes)

**Files:**
- Read: `api/gamification/achievements.py`

**Step 1: List all classes**

**Step 2: Identify if classes could be data/functions**

- Are there classes that just hold data (could be dicts)?
- Are there classes with only one method (could be functions)?

**Step 3: Document findings**

```
[ANALYSIS: api/gamification/achievements.py]
Classes that could be functions:
- TBD
Classes that could be dicts:
- TBD
```

---

### Task 8: Analyze frontend/src/contexts/AudioContext.tsx (814 lines)

**Files:**
- Read: `frontend/src/contexts/AudioContext.tsx`

**Step 1: Identify major sections**

- What state does this context manage?
- What functions does it expose?
- Are there large inline functions that could be extracted?

**Step 2: Look for duplication**

- Similar WebSocket handlers?
- Similar state update patterns?

**Step 3: Document findings**

```
[ANALYSIS: AudioContext.tsx]
Extractable utilities:
- TBD
Duplicate patterns:
- TBD
Lines that could be reduced:
- TBD
```

---

### Task 9: Analyze frontend/src/services/practiceService.ts (619 lines)

**Files:**
- Read: `frontend/src/services/practiceService.ts`

**Step 1: Identify all API calls**

- How many similar fetch patterns exist?
- Is there a common error handling pattern duplicated?

**Step 2: Document findings**

```
[ANALYSIS: practiceService.ts]
API calls that could share a helper:
- TBD
Duplicate error handling:
- TBD
```

---

## Phase 3: Targeted Refactoring

### Task 10: Refactor api/error_handlers.py

**Files:**
- Modify: `api/error_handlers.py`

Based on Phase 2 analysis, implement identified simplifications.

**Step 1: Make changes based on analysis**

**Step 2: Run tests**

```bash
make test
```

**Step 3: Commit**

```bash
git add api/error_handlers.py
git commit -m "refactor: simplify error handlers"
```

---

### Task 11: Refactor core/models/user.py

**Files:**
- Modify: `core/models/user.py`

Based on Phase 2 analysis, consolidate classes.

**Step 1: Implement consolidations identified in Task 5**

**Step 2: Update any imports in files that use these classes**

```bash
grep -rn "from core.models.user import" api modules
```

**Step 3: Run tests**

```bash
make test
```

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: consolidate user model classes"
```

---

### Task 12: Refactor api/tala/rhythm_training.py

**Files:**
- Modify: `api/tala/rhythm_training.py`

Based on Phase 2 analysis, flatten hierarchy.

**Step 1: Implement simplifications identified in Task 6**

**Step 2: Run tests**

```bash
make test
```

**Step 3: Commit**

```bash
git add api/tala/rhythm_training.py
git commit -m "refactor: flatten rhythm training class hierarchy"
```

---

### Task 13: Refactor api/gamification/achievements.py

**Files:**
- Modify: `api/gamification/achievements.py`

Based on Phase 2 analysis, convert classes to functions/data.

**Step 1: Implement simplifications identified in Task 7**

**Step 2: Run tests**

```bash
make test
```

**Step 3: Commit**

```bash
git add api/gamification/achievements.py
git commit -m "refactor: simplify achievements module"
```

---

### Task 14: Refactor frontend/src/contexts/AudioContext.tsx

**Files:**
- Modify: `frontend/src/contexts/AudioContext.tsx`
- Possibly create: `frontend/src/hooks/useAudioWebSocket.ts` (if extraction needed)

Based on Phase 2 analysis, extract utilities and reduce duplication.

**Step 1: Implement simplifications identified in Task 8**

**Step 2: Run lint**

```bash
cd frontend && npm run lint
```

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: simplify AudioContext, extract utilities"
```

---

### Task 15: Refactor frontend/src/services/practiceService.ts

**Files:**
- Modify: `frontend/src/services/practiceService.ts`

Based on Phase 2 analysis, consolidate API patterns.

**Step 1: Implement simplifications identified in Task 9**

**Step 2: Run lint**

```bash
cd frontend && npm run lint
```

**Step 3: Commit**

```bash
git add frontend/src/services/practiceService.ts
git commit -m "refactor: consolidate practiceService API patterns"
```

---

### Task 16: Final Verification

**Step 1: Run full test suite**

```bash
make test
```

**Step 2: Run frontend checks**

```bash
cd frontend && npm run lint && npm run build
```

**Step 3: Compare line counts**

```bash
wc -l core/models/user.py api/tala/rhythm_training.py api/gamification/achievements.py api/error_handlers.py
wc -l frontend/src/contexts/AudioContext.tsx frontend/src/services/practiceService.ts
```

Document before/after comparison.

**Step 4: Final commit (if any remaining changes)**

```bash
git add -A
git commit -m "refactor: complete code simplification pass"
```

---

## Analysis Notes

(To be filled during Phase 2 execution)

### core/models/user.py
```
[ANALYSIS PENDING]
```

### api/tala/rhythm_training.py
```
[ANALYSIS PENDING]
```

### api/gamification/achievements.py
```
[ANALYSIS PENDING]
```

### frontend/src/contexts/AudioContext.tsx
```
[ANALYSIS PENDING]
```

### frontend/src/services/practiceService.ts
```
[ANALYSIS PENDING]
```
