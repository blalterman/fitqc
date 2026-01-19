# Refactor: Merge interior.py + boundary.py → stickiness.py

## Context

The fitqc package is complete with all tests passing. We now want to simplify the architecture by merging two modules that implement mathematically identical algorithms.

**Current state:**
- `src/fitqc/interior.py` - detects stickiness at x0 (initial guess)
- `src/fitqc/boundary.py` - detects stickiness at L (lower) and U (upper)

**Insight:** Both compute normalized distance from a reference point and detect spikes at z ≈ 0:
- Interior: z = |x - x0| / (U - L)
- Boundary lower: z = |x - L| / (U - L)
- Boundary upper: z = |x - U| / (U - L)

## Requirements

1. **Audit first, change second** - Read and understand all affected files before proposing changes
2. **Propositions required** - For EACH proposed change, provide:
   - **For:** Why this change improves the codebase
   - **Against:** What risks or downsides exist
   - **Decision:** Your recommendation with justification
3. **Tests must pass** - All existing tests must pass after refactor
4. **No functionality loss** - Every behavior must be preserved
5. **No redundancy** - Don't duplicate logic that can be shared

## Phase 1: Audit

Read these files completely:
- src/fitqc/interior.py
- src/fitqc/boundary.py
- tests/test_interior.py
- tests/test_boundary.py
- tests/test_spike_detection.py
- src/fitqc/__init__.py (check public exports)
- Any file that imports interior or boundary

Create a detailed analysis:
1. What functions exist in each module?
2. What is identical between them?
3. What differs (if anything)?
4. What are the public API entry points?
5. What tests cover each function?

## Phase 2: Design with Propositions

For the unified stickiness.py, propose:

### 2.1 Core Function Signature
Propose the unified `detect_stickiness()` function. Provide for/against propositions.

### 2.2 Backward Compatibility
Options:
- A) Delete interior.py/boundary.py entirely, update all imports
- B) Keep interior.py/boundary.py as thin wrappers that call stickiness.py
- C) Keep old function names as aliases in stickiness.py

Provide for/against for each option.

### 2.3 Test Strategy
Options:
- A) Merge test_interior.py + test_boundary.py → test_stickiness.py
- B) Keep separate test files, update imports
- C) Create new test_stickiness.py, keep old tests for regression

Provide for/against for each option.

### 2.4 Result Dataclass
Should InteriorResult and BoundaryResult merge into StickinessResult?
Provide for/against.

## Phase 3: Implementation

Only after Phase 2 decisions are made:
1. Create src/fitqc/stickiness.py
2. Update or remove interior.py/boundary.py
3. Update tests
4. Update __init__.py exports
5. Update any other imports

## Phase 4: Verification

1. Run full test suite: `pytest -v`
2. Verify no functionality lost
3. Run example: `python examples/run_array_qc.py`
4. Check imports are clean: `ruff check .`

## Constraints

- Do NOT proceed to implementation until audit is complete
- Do NOT make changes without stating for/against propositions
- Do NOT remove any test coverage
- Do NOT break the public API without explicit backward compatibility plan
