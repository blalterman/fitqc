# Stickiness Wrapper Implementation Plan

## Executive Summary

Add a thin wrapper `detect_stickiness()` function that provides a unified API over the existing `run_interior_qc()` and `run_boundary_qc()` functions. The existing modules remain unchanged.

**Branch:** Create fresh from `main`
**Approach:** Test-first development
**Risk level:** Low (additive change, no modifications to existing code)

---

## Design Decisions (Approved)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Extract to util.py | No | Commonalities already factored into `sortedops.py` and `selection.py` |
| Unified StickinessResult | No | Keep `InteriorResult` and `BoundaryResult`; return union type |
| Wrap compute_z/compute_u | No | Keep in original modules; wrapper provides detection only |
| Primary API | Yes | `detect_stickiness()` is primary; existing functions are "advanced" |
| Mode options | `"interior"`, `"lower"`, `"upper"`, `"all"` | Full flexibility |
| Scale options | `float \| "std" \| "iqr" \| "range"` | User choice for unbounded parameters |

---

## File Changes

| File | Action | Lines (est.) |
|------|--------|--------------|
| `src/fitqc/stickiness.py` | CREATE | ~200 |
| `src/fitqc/__init__.py` | MODIFY | +2 |
| `tests/test_stickiness.py` | CREATE | ~600 |

**Files NOT modified:**
- `src/fitqc/interior.py` — unchanged
- `src/fitqc/boundary.py` — unchanged
- `tests/test_interior.py` — unchanged
- `tests/test_boundary.py` — unchanged
- All other existing files — unchanged

---

## API Specification

### Function Signature

```python
def detect_stickiness(
    x: NDArray[np.floating],
    ref: float,
    L: float | None,
    U: float | None,
    mode: Literal["interior", "lower", "upper", "all"] = "all",
    scale: float | Literal["std", "iqr", "range"] | None = None,
    interior_config: InteriorConfig | None = None,
    boundary_config: BoundaryConfig | None = None,
) -> InteriorResult | BoundaryResult | tuple[InteriorResult, BoundaryResult]:
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `x` | `NDArray[np.floating]` | Fitted parameter values from optimization runs |
| `ref` | `float` | Reference point (x0 for interior, L for lower, U for upper) |
| `L` | `float \| None` | Lower bound; None if unbounded below |
| `U` | `float \| None` | Upper bound; None if unbounded above |
| `mode` | `Literal[...]` | Which stickiness check: `"interior"`, `"lower"`, `"upper"`, `"all"` |
| `scale` | `float \| str \| None` | Normalization scale for unbounded parameters |
| `interior_config` | `InteriorConfig \| None` | Config for interior detection |
| `boundary_config` | `BoundaryConfig \| None` | Config for boundary detection |

### Return Types by Mode

| Mode | Return Type | Description |
|------|-------------|-------------|
| `"interior"` | `InteriorResult` | x0 stickiness detection result |
| `"lower"` | `BoundaryResult` | Lower boundary result (upper fields None) |
| `"upper"` | `BoundaryResult` | Upper boundary result (lower fields None) |
| `"all"` | `tuple[InteriorResult, BoundaryResult]` | Both results |

### Scale Parameter Behavior

| Condition | Scale Behavior |
|-----------|----------------|
| Both L and U provided | Scale parameter ignored; uses `max(ref - L, U - ref)` |
| Either L or U is None | Scale parameter **required** |
| `scale=float` | Uses provided value directly |
| `scale="std"` | Uses `np.std(x)` |
| `scale="iqr"` | Uses `np.percentile(x, 75) - np.percentile(x, 25)` |
| `scale="range"` | Uses `np.max(x) - np.min(x)` |

### Validation Rules

| Condition | Error |
|-----------|-------|
| `mode="interior"` and (L is None or U is None) and scale is None | `ValueError` |
| `mode="lower"` and L is None | `ValueError` |
| `mode="upper"` and U is None | `ValueError` |
| `scale <= 0` | `ValueError` |
| `scale` is invalid string | `ValueError` |
| `mode` is invalid | `ValueError` |

---

## Implementation

The approved reference implementation is in `prompts/stickiness-wrapper-prompt.md` (Reference Implementation section).

**Files to create/modify:**
- `src/fitqc/stickiness.py` — Full implementation (~340 lines)
- `src/fitqc/__init__.py` — Add import and `__all__` entry
- `tests/test_stickiness.py` — Comprehensive tests (~51 tests)

---

## Execution Order

1. **Create branch from main**
2. **Write tests** (`tests/test_stickiness.py`)
3. **User approves tests**
4. **Implement** (`src/fitqc/stickiness.py`)
5. **Update exports** (`src/fitqc/__init__.py`)
6. **Run all tests** — new tests pass, existing tests still pass
7. **Run ruff** — fix linting issues
8. **Commit and push**

---

## Verification Criteria

```bash
# All tests pass (101 existing + ~59 new)
pytest -v

# Linting passes
ruff check .
ruff format --check .

# Example still works
python examples/run_array_qc.py

# New function importable
python -c "from fitqc import detect_stickiness; print(detect_stickiness)"
```

---

## Decision Log (Archival)

This section provides the full decision history with rationale, alternatives, and evidence.
For AI execution, use the lean prompt at `prompts/stickiness-wrapper-prompt.md`.

---

### D1: Thin Wrapper Architecture

**Decision:** Create thin wrapper over existing modules; do NOT merge `interior.py`/`boundary.py`

**Alternatives Considered:**
- A: Merge `interior.py` and `boundary.py` into unified `stickiness.py`
- B: Create thin wrapper that delegates to existing modules ✓

**Rationale:**
- Existing modules have 101 passing tests with well-defined behavior
- Interior and boundary detection are conceptually different (z-statistics vs tolerance curves)
- Merging would require extensive refactoring and test migration
- Thin wrapper achieves API simplification without touching working code

**Evidence:**
- `tests/test_interior.py`: 45 tests covering all edge cases
- `tests/test_boundary.py`: 56 tests for boundary detection
- Both modules independently reviewed and approved

**Failure Mode Avoided:** Breaking existing API consumers who depend on current function signatures

---

### D2: No util.py Extraction

**Decision:** Do NOT extract commonalities to `util.py`

**Alternatives Considered:**
- A: Create `util.py` with shared validation/array handling code
- B: Keep existing factorization as-is ✓

**Rationale:**
- Commonalities already properly factored into `sortedops.py` (O(n) percentile) and `selection.py` (quickselect)
- Adding util.py would create a fourth extraction layer with unclear boundaries
- Current structure has clear module responsibilities

**Evidence:**
- `src/fitqc/sortedops.py`: Single-pass statistics computation
- `src/fitqc/selection.py`: Quickselect algorithm
- No duplicated code identified between interior.py and boundary.py

**Failure Mode Avoided:** Over-abstraction leading to scattered, hard-to-follow code

---

### D3: Union Return Type

**Decision:** Return union type `InteriorResult | BoundaryResult`; do NOT create unified `StickinessResult`

**Alternatives Considered:**
- A: Create unified `StickinessResult` dataclass with all fields
- B: Return union of existing result types ✓

**Rationale:**
- `InteriorResult` has spike-related fields (`spike_detected`, `z_x0`, `spike_count`)
- `BoundaryResult` has tolerance-curve fields (`t_lo_star`, `t_hi_star`, `mass_curve`)
- These are semantically different; forcing into one type loses type safety
- Union type preserves domain semantics and mypy checking

**Evidence:**
- `InteriorResult` fields: `spike_detected`, `z_x0`, `spike_count`, `threshold_z`, `x0`
- `BoundaryResult` fields: `lower_pileup_detected`, `upper_pileup_detected`, `t_lo_star`, `t_hi_star`, `tol_grid`, `lower_mass_curve`, `upper_mass_curve`
- No meaningful overlap between field sets

**Failure Mode Avoided:** Loss of type safety and semantic confusion from jamming unrelated fields together

---

### D4: Do Not Wrap compute_z/compute_u

**Decision:** Do NOT wrap `compute_z` or `compute_u` in public API

**Alternatives Considered:**
- A: Expose `compute_z` and `compute_u` as part of wrapper API
- B: Keep as implementation details in original modules ✓

**Rationale:**
- These are intermediate computation functions, not user-facing
- Users want detection results, not raw statistics
- Exposing internals increases API surface without user benefit
- Original modules remain available for advanced users who need raw statistics

**Evidence:**
- `compute_z`: Called internally by `run_interior_qc`, returns z-statistic
- `compute_u`: Called internally by `run_boundary_qc`, returns normalized distances
- No use case identified for calling these directly

**Failure Mode Avoided:** API bloat; users confused about which function to call

---

### D5: Wrapper as Primary API

**Decision:** `detect_stickiness()` is the primary API; existing functions are "advanced"

**Alternatives Considered:**
- A: Keep existing functions as primary, wrapper as convenience
- B: Wrapper is primary entry point for new users ✓

**Rationale:**
- New users shouldn't need to understand interior vs boundary distinction
- Single entry point reduces cognitive load
- Advanced users still have direct access to underlying functions
- Documentation can emphasize wrapper while noting advanced options

**Evidence:**
- User feedback: "I just want to check if my parameter is sticky"
- Similar patterns in scikit-learn: `fit_predict()` wraps `fit()` + `predict()`

**Failure Mode Avoided:** New users overwhelmed by having to choose between multiple similar functions

---

### D6: Four Mode Options

**Decision:** Provide four modes: `"interior"`, `"lower"`, `"upper"`, `"all"`

**Alternatives Considered:**
- A: Only `"interior"` and `"boundary"` (2 modes)
- B: Only `"all"` (1 mode, always run everything)
- C: Four modes with granular control ✓

**Rationale:**
- Users may only care about one type of stickiness
- Running unnecessary checks wastes computation
- `"lower"` and `"upper"` allow asymmetric analysis (e.g., parameter only bounded below)
- `"all"` provides convenience for comprehensive check

**Evidence:**
- Existing codebase shows separate calls to `run_interior_qc` and `run_boundary_qc`
- Some parameters have only lower bounds (e.g., variance > 0)

**Failure Mode Avoided:** Forcing users to run unwanted checks; no way to check only one boundary

---

### D7: BoundaryResult Field Handling

**Decision:** `mode="lower"` and `mode="upper"` return `BoundaryResult` with unused fields set to `None`

**Alternatives Considered:**
- A: Create `LowerBoundaryResult` and `UpperBoundaryResult` types
- B: Return full `BoundaryResult` with unused fields as `None` ✓

**Rationale:**
- Avoids proliferation of similar dataclasses
- Consistent return type for boundary modes simplifies caller code
- `None` clearly indicates "not computed" vs "computed but no detection"
- Existing `BoundaryResult` already supports optional fields

**Evidence:**
- `BoundaryResult` defined with fields that can be None when not applicable
- Pattern used in scipy.optimize results (some fields None based on options)

**Failure Mode Avoided:** Type explosion; callers needing to handle multiple result types

---

### D8: Scale Parameter Required for Incomplete Bounds

**Decision:** Require `scale` parameter when `L` or `U` is `None`

**Alternatives Considered:**
- A: Auto-compute scale from data always
- B: Fail loudly if bounds incomplete and no scale provided ✓
- C: Use data range as implicit default

**Rationale:**
- Interior detection normalizes by `max(ref - L, U - ref)` — impossible without bounds
- Auto-computing from data can give misleading results (data-dependent threshold)
- Explicit scale forces user to think about appropriate normalization
- Error message guides user to valid options

**Evidence:**
- `run_interior_qc` signature requires L and U
- Auto-scale without user awareness led to false positives in testing

**Failure Mode Avoided:** Silent use of inappropriate scale leading to wrong detection

---

### D9: Scale Options

**Decision:** Scale options: `float | "std" | "iqr" | "range"`

**Alternatives Considered:**
- A: Only numeric scale
- B: Only string presets
- C: Both numeric and string presets ✓

**Rationale:**
- Numeric allows user to specify domain-specific scale
- `"std"` useful when data is approximately normal
- `"iqr"` robust to outliers (matches robust statistics theme)
- `"range"` useful when full spread is meaningful
- Covers common use cases while allowing customization

**Evidence:**
- scipy.stats functions often accept similar scale options
- IQR used elsewhere in fitqc for robust estimation

**Failure Mode Avoided:** User stuck without good scale option for their use case

---

### D10: Fresh Branch from Main

**Decision:** Create fresh branch from `main`, not from existing feature branches

**Alternatives Considered:**
- A: Branch from existing development branch
- B: Fresh branch from main ✓

**Rationale:**
- Ensures clean diff against production code
- Avoids inheriting unrelated changes
- Easier code review
- Standard practice for new features

**Failure Mode Avoided:** Merge conflicts; review confusion from unrelated changes

---

### D11: Test-First with Non-Trivial Assertions

**Decision:** Write tests first; require non-trivial assertions

**Alternatives Considered:**
- A: Write implementation first, add tests after
- B: Test-first development with strict assertion requirements ✓

**Rationale:**
- Tests clarify expected behavior before implementation
- Non-trivial assertions catch actual bugs (not just "it runs")
- Forces thinking through edge cases upfront
- Approved tests become specification

**Assertion Requirements:**
- No `assert X is not None` without additional checks
- Use `np.testing.assert_array_equal` for arrays
- Use `pytest.approx` for floats
- Use `pytest.raises` for expected errors
- Verify type, shape, dtype, and values

**Evidence:**
- Existing test files follow this pattern
- Past bugs caught by strict assertions in `test_interior.py`

**Failure Mode Avoided:** Tests that pass but don't verify behavior; implementation bugs slipping through
