# Test Failure Investigation: Comprehensive Findings

**Date:** 2026-01-23
**Investigator:** Claude (Sonnet 4.5)
**Branch:** `claude/fitqc-ppa12-validation-vwKdg`
**Failures:** 16 tests (test_boundary_fixes.py: 13, test_boundary_quantile.py: 3)

---

## Executive Summary

**ROOT CAUSE IDENTIFIED:** Delta function special-case handling incorrectly triggers for near-boundary pileups.

The boundary detection algorithm has special logic to handle "delta function" pileups (samples stuck exactly at L or U boundaries). This special case triggers when the detected elbow is smaller than `pileup_threshold` (default 0.005). When triggered, it returns the first measurable grid point (~0.0001) instead of the actual elbow value (~0.003).

**Impact:**
- Detection WORKS (pileups are found correctly)
- Threshold VALUES are incorrect (10-30x too tight)
- Tests fail on assertion about threshold magnitude

**Fix Strategy:** Adjust the delta function detection logic or pileup_threshold value to distinguish between:
1. Samples exactly AT boundary (delta function) → use first grid point
2. Samples NEAR boundary (spread pileup) → use actual elbow value

---

## Investigation Timeline

### Phase 1: Git History Analysis

**Key Commits Affecting Boundary Detection:**

1. **fd02b5d** (2026-01-20): "implement PPA12 validation fixes"
   - Expanded quantile grid from 7 to 26 points
   - Made detection thresholds configurable (pileup_threshold, excess_ratio)
   - Implemented iterative kneedle refinement
   - **Status at commit:** 23/33 tests passing (70%)
   - **Note:** Tests were ALREADY failing when this was committed

2. **de9f737** (2026-01-20): "correct elbow detection for delta function pileups"
   - Changed from `curve="concave"` to `curve="convex"` for quantile detection
   - Added quantile→tolerance conversion
   - Relaxed delta function threshold from 1e-10 to pileup_threshold (0.005)
   - **Validated on:** Real A_He PPA12 data (1,642/100,000 samples at L=0)
   - **Result:** t_lo_star=0.00125 correctly detected

3. **7beb0c7** (2026-01-20): "update assertions for delta function behavior"
   - Updated test expectations from [0.005, 0.015] to [0.0001, 0.005]
   - **Status after update:** 35/48 tests passing (73%)

**Conclusion:** The test suite has been in a failing state for several days. This is ongoing development work, not a regression introduced by my documentation changes.

---

## Phase 2: Test Failure Analysis

### Example: test_multi_curve_detects_tight_pileup

**Test Setup:**
```python
rng = np.random.default_rng(42)
x_pileup = rng.uniform(0.0, 0.003, size=300)  # 3% tight pileup in [0, 0.003]
x_bulk = rng.uniform(0.0, 1.0, size=9700)     # 97% uniform in [0, 1.0]
x = np.concatenate([x_pileup, x_bulk])

config = BoundaryConfig(
    n_tols=45,
    grid_mode="progressive",
    quantile_grid=(0.005, 0.01, 0.02, 0.03, 0.05, 0.10),
    use_quantile_analysis=True,
)
result = run_boundary_qc(x, L=0.0, U=1.0, config=config)
```

**Test Expectation:**
```python
assert result.t_lo_star == pytest.approx(0.003, abs=0.002)
# Expects: 0.001 to 0.005
```

**Actual Result:**
```python
result.t_lo_star = 0.0001  # 10x tighter than minimum expected
```

**Why Test Expects 0.003:**
- Pileup width is 0.003 (samples in [0, 0.003])
- Test assumes threshold should match pileup extent
- Reasonable expectation for spread pileups

### Detailed Findings

**Distribution Check:**
```
Samples in [0, 0.001]: 121  (1.21%)
Samples in [0, 0.002]: 223  (2.23%)
Samples in [0, 0.003]: 331  (3.31%) ← Matches ~300 pileup samples
Samples in [0, 0.005]: 356  (3.56%)
```

**Quantile Elbows Detected:**
```python
quantile_elbows['lower'] = {
    0.005: 0.00042,   # 0.5% quantile → tolerance
    0.01:  0.00086,   # 1% quantile → tolerance
    0.02:  0.00178,   # 2% quantile → tolerance
    0.03:  0.00265,   # 3% quantile → tolerance ← Close to 0.003!
    0.05:  0.02157,   # 5% quantile → tolerance
    0.1:   0.05,      # 10% quantile → tolerance
}
```

**Elbow Detection Result (when isolated):**
```
Detected elbow: quantile=0.03, tolerance=0.00297 ≈ 0.003 ✓
```

**Conclusion:** The quantile curve analysis correctly identifies the pileup at ~0.003. The problem occurs in post-processing.

---

## Phase 3: Root Cause Identification

### Code Flow Analysis

**Path taken by test** (use_quantile_analysis=True, refine_transition=False):

1. **Compute quantile curves** (`_compute_quantile_curves_boundary`):
   - For each quantile q, find tolerance t where P(u<t) = q
   - Detect elbow in (quantile, tolerance) curve
   - **Result:** `t_lo_raw` ≈ 0.00297

2. **Check for excess mass** (`check_excess_mass`):
   - Validate that elbow represents real pileup
   - **TRIGGER POINT:** Special case for `t_star < pileup_threshold`

### The Delta Function Special Case

**Source:** `src/fitqc/boundary.py`, lines 641-662

```python
def check_excess_mass(t_star, mass_curve):
    if t_star is None:
        return False, None

    # Special case: elbow at very small t indicates delta function at boundary
    if t_star < pileup_threshold:  # pileup_threshold = 0.005
        # Find first non-zero tolerance point to measure the pileup
        for idx in range(1, min(5, len(tol_grid))):
            t_check = tol_grid[idx]
            if t_check > 1e-10:  # Found measurable tolerance
                mass_check = mass_curve[idx]
                if mass_check > t_check * excess_ratio:
                    # Valid pileup detected
                    # Return the measurement tolerance (not the elbow value)
                    return True, float(t_check)  # ← Returns tol_grid[1] = 0.0001
        return False, None

    # Normal case: t_star >= pileup_threshold
    # ... regular handling ...
```

### Root Cause Mechanism

**For our test case:**

1. Elbow correctly detected at t_lo_raw ≈ 0.00297
2. Check: Is 0.00297 < pileup_threshold (0.005)? → **YES**
3. Special case triggers: "This is a delta function pileup"
4. Find first grid point: tol_grid[1] = 0.0001
5. Check mass: mass_curve[1] > 0.0001 * 1.5? → **YES** (3% >> 0.015%)
6. **Return 0.0001 instead of 0.00297**

**Result:** t_lo_star = 0.0001 (the first grid point, not the actual elbow)

### Design Intent vs. Reality

**Delta function special case was designed for:**
- Optimizer stickiness exactly AT boundary (samples at L=0 or U=1)
- Example: A_He PPA12 data with 1.64% samples at exactly L=0
- Elbow detection may be unstable near t≈0 due to numerical issues
- Solution: Use first measurable grid point as conservative threshold

**Problem:** The special case also triggers for:
- Spread pileups NEAR boundary (samples in [0, 0.003])
- Where elbow detection works correctly
- Returning first grid point is too conservative

**Threshold Comparison:**
```
Delta function case (A_He PPA12):
  - Samples at exactly L=0 (integer multiple of machine epsilon)
  - True pileup "width": ~0 (point mass)
  - First grid point (0.00125): reasonable approximation

Spread pileup case (test):
  - Samples uniform in [0, 0.003]
  - True pileup width: 0.003
  - First grid point (0.0001): 30x too tight
```

---

## Phase 4: Additional Test Failures

All 16 failures follow the same pattern:

### test_boundary_fixes.py (13 failures)

**Iterative Refinement Tests (5 failures):**
- Tests expect refinement to improve detection
- Algorithm likely works but thresholds differ from expectations

**Integration Tests (4 failures):**
- `test_moderate_pileup_detected`: Threshold too tight
- `test_asymmetric_detection_*`: Similar threshold issues
- `test_symmetric_detection_both_boundaries`: Both boundaries affected

**Fine-Grained Detection (1 failure):**
- `test_tolerance_grid_resolution_for_fine_pileups`: Grid resolution vs. threshold interaction

**Initial Guess Stickiness (1 failure):**
- `test_single_bin_initial_guess_stickiness`: Likely related to tight threshold detection

**Artifact Handling (2 failures):**
- `test_pileup_at_tol_max_is_valid`: Edge case near tol_max
- `test_true_uniform_no_false_positive_at_tol_max`: False positive from tight thresholds

### test_boundary_quantile.py (3 failures)

**Quantile Curve Tests (1 failure):**
- `test_quantile_curve_tight_pileup_shows_elbow`: Elbow detected but threshold too tight

**Multi-Curve Integration (2 failures):**
- `test_multi_curve_detects_tight_pileup`:
  - Expected: 0.003 ± 0.002
  - Actual: 0.0001
  - Ratio: 0.03x (30x too tight)

- `test_multi_curve_handles_broad_pileup`:
  - Expected: ≥ 0.02
  - Actual: 0.0126
  - Ratio: 0.63x (not as tight but still fails)

---

## Analysis: Algorithm Behavior

### Is the Algorithm Working Correctly?

**YES, for its design goals:**
- ✅ Detects pileups correctly (lower_pileup_detected = True)
- ✅ Elbow detection finds correct transition point
- ✅ Handles delta functions (real A_He PPA12 data validates)
- ✅ Conservative thresholds avoid missing samples

**NO, for test expectations:**
- ❌ Thresholds don't match pileup extent
- ❌ Special case triggers inappropriately for spread pileups
- ❌ Returns first grid point instead of actual elbow for small pileups

### Algorithm Trade-offs

**Conservative vs. Accurate:**

The current algorithm prioritizes **conservative detection** (don't miss samples) over **accurate characterization** (match pileup width).

| Approach | t_lo_star | Interpretation |
|----------|-----------|----------------|
| Current (0.0001) | First grid point | "Remove everything within 0.01% of boundary" |
| Expected (0.003) | Actual elbow | "Remove everything within 0.3% of boundary" |

**Both are valid** depending on use case:
- **Conservative:** Ensures all stuck samples removed, even at cost of false positives
- **Accurate:** Better characterizes actual pileup extent, less aggressive filtering

### Scientific Correctness

**From optimization perspective:**
- Samples in [0, 0.003] represent ~3% of data
- If this indicates optimizer issues, should ALL these samples be flagged?
- Or only samples very close to L=0?

**The answer depends on:**
1. What caused the pileup (optimizer stickiness vs. true parameter distribution)
2. Whether samples at 0.0015 are "safe" or "suspicious"
3. Scientific domain knowledge about the parameter

**Current algorithm says:**
"Be conservative. If there's ANY pileup structure, flag samples very close to the boundary."

**Tests expect:**
"Characterize the pileup extent accurately."

---

## Configuration Analysis

### Relevant BoundaryConfig Parameters

```python
@dataclass
class BoundaryConfig:
    pileup_threshold: float = 0.005     # ← KEY PARAMETER
    excess_ratio: float = 1.5
    min_quantile_agreement: float = 0.5
    n_tols: int = 41
    tol_max: float = 0.05
    grid_mode: str = "progressive"
    quantile_grid: tuple[float, ...] = (...)
    use_quantile_analysis: bool = False
    refine_transition: bool = False
```

**pileup_threshold = 0.005:**
- Triggers delta function handling when elbow < 0.005
- Appropriate for exact boundary stickiness
- Too high for spread pileups in [0, 0.003]

**Possible values:**
- 0.005 (current): Triggers for test pileups → returns grid point
- 0.001: Would not trigger for test pileups → returns actual elbow
- 0.01: Even more conservative → more tests fail

---

## Recommended Solutions

### Option 1: Adjust pileup_threshold (Quick Fix)

**Change:**
```python
pileup_threshold: float = 0.001  # Down from 0.005
```

**Effect:**
- Spread pileups with t>0.001 use actual elbow
- Delta functions with t<0.001 still get special handling
- Tests with pileup widths ≥0.001 should pass

**Pros:**
- Simple one-line change
- Preserves delta function handling
- Tests likely pass with this adjustment

**Cons:**
- Arbitrary threshold (why 0.001 not 0.0005?)
- Doesn't fundamentally solve ambiguity
- Future test cases might still fail

**Risk:** MINIMAL - Easy to revert, well-understood impact

---

### Option 2: Improve Delta Function Detection (Better Fix)

**Change:** Add heuristic to distinguish delta vs. spread pileups

**Implementation:**
```python
def check_excess_mass(t_star, mass_curve):
    if t_star is None:
        return False, None

    # Check if this is a true delta function (point mass at boundary)
    # vs. a spread pileup (distributed over small range)
    if t_star < pileup_threshold:
        # Measure pileup "sharpness"
        mass_at_elbow = np.interp(t_star, tol_grid, mass_curve)
        mass_at_half_elbow = np.interp(t_star / 2, tol_grid, mass_curve)

        # Delta function: mass accumulates rapidly near t=0
        # Spread pileup: mass accumulates gradually up to t_star
        sharpness = mass_at_half_elbow / (mass_at_elbow + 1e-10)

        if sharpness > 0.8:  # >80% of mass in first half → delta function
            # Use first measurable grid point
            for idx in range(1, min(5, len(tol_grid))):
                t_check = tol_grid[idx]
                if t_check > 1e-10:
                    mass_check = mass_curve[idx]
                    if mass_check > t_check * excess_ratio:
                        return True, float(t_check)
            return False, None
        else:
            # Spread pileup: use actual elbow
            pass  # Fall through to normal handling

    # Normal case: use actual elbow...
    mass_at_elbow = np.interp(t_star, tol_grid, mass_curve)
    has_pileup = mass_at_elbow > t_star * excess_ratio
    return has_pileup, float(t_star) if has_pileup else None
```

**Pros:**
- Distinguishes delta from spread based on data characteristics
- Preserves correct handling for both cases
- More scientifically principled

**Cons:**
- More complex logic
- Introduces new parameter (sharpness threshold)
- Needs validation on real data

**Risk:** MEDIUM - More complex, needs thorough testing

---

### Option 3: Update Test Expectations (Pragmatic Fix)

**Change:** Update tests to expect conservative thresholds

**Implementation:**
```python
# OLD
assert result.t_lo_star == pytest.approx(0.003, abs=0.002)

# NEW
assert result.t_lo_star is not None
assert result.t_lo_star < 0.003  # Conservative: tighter than pileup width
assert result.lower_pileup_detected  # Detection works
```

**Rationale:**
- Algorithm's conservative behavior may be intentional
- Tests should verify detection, not exact threshold magnitude
- Threshold values are heuristics, not ground truth

**Pros:**
- Respects current algorithm design
- Tests remain meaningful (verify detection works)
- No algorithm changes needed

**Cons:**
- Doesn't address root ambiguity (delta vs. spread)
- Tests become less specific
- May hide future regressions in threshold quality

**Risk:** LOW - Tests still verify core functionality

---

### Option 4: Add Configuration Parameter (Most Flexible)

**Change:** Make delta function handling configurable

**Implementation:**
```python
@dataclass
class BoundaryConfig:
    # ... existing fields ...
    use_conservative_thresholds: bool = True  # New parameter
    delta_threshold: float = 0.001  # Separate from pileup_threshold
```

**Usage:**
```python
# Conservative mode (current behavior)
config = BoundaryConfig(use_conservative_thresholds=True)
# → Returns first grid point for small elbows

# Accurate mode (for tests/analysis)
config = BoundaryConfig(use_conservative_thresholds=False)
# → Returns actual elbow value
```

**Pros:**
- Maximum flexibility
- Both behaviors available
- Users can choose based on use case
- Tests can use accurate mode

**Cons:**
- More parameters to document/maintain
- Risk of confusion about which to use
- Doesn't solve fundamental ambiguity

**Risk:** LOW - Backward compatible (default preserves current behavior)

---

## Comparison of Solutions

| Solution | Complexity | Test Impact | Algorithm Impact | Risk | Recommendation |
|----------|------------|-------------|------------------|------|----------------|
| **Option 1:** Adjust threshold | LOW | Most tests pass | Minimal | MINIMAL | ⭐ **Quick fix** |
| **Option 2:** Improve detection | HIGH | Tests pass | Better handling | MEDIUM | **Long-term fix** |
| **Option 3:** Update tests | LOW | All pass | None | LOW | **Pragmatic** |
| **Option 4:** Add config | MEDIUM | Tests pass | Backward compatible | LOW | **Flexible** |

---

## Recommended Approach: Phased Implementation

### Phase 1: Quick Fix (1-2 hours)

**Goal:** Unblock PR with minimal changes

**Action:** Option 1 - Adjust pileup_threshold
```python
# src/fitqc/config.py
pileup_threshold: float = 0.001  # Down from 0.005
```

**Verification:**
1. Run failing tests: `pytest tests/test_boundary_quantile.py -v`
2. Check how many pass with new threshold
3. Adjust further if needed (try 0.0005, 0.002, etc.)
4. Run full test suite
5. Commit with message explaining temporary fix

**Expected outcome:** 10-14 of 16 tests pass

---

### Phase 2: Test Updates (1-2 hours)

**Goal:** Make tests more robust

**Action:** Option 3 - Update test expectations for remaining failures

**For tests that still fail after Phase 1:**
```python
# Instead of exact value assertions
assert result.t_lo_star == pytest.approx(expected, abs=tolerance)

# Use range assertions
assert result.t_lo_star is not None
assert result.t_lo_star <= expected_max  # Conservative thresholds are tighter
assert result.lower_pileup_detected  # Verify detection works
```

**Expected outcome:** All 16 tests pass

---

### Phase 3: Algorithm Improvement (4-6 hours, future work)

**Goal:** Better distinguish delta vs. spread pileups

**Action:** Option 2 - Implement sharpness heuristic

**Steps:**
1. Research delta function characteristics in real data
2. Design and implement sharpness metric
3. Validate on PPA12 datasets (A_He and others)
4. Create test cases for both delta and spread scenarios
5. Document decision logic in docstrings

**Expected outcome:** Robust handling of both pileup types

---

## Documentation Build Issue (Secondary)

**Issue:** 4 Sphinx intersphinx warnings

**Root Cause:** Network proxy blocking HTTPS connections (403 Forbidden)

**Impact:**
- Local builds with `-W` flag fail
- CI may or may not be affected (depends on CI network setup)

**Solutions:**

1. **Quick fix:** Don't use `-W` flag locally
2. **Better fix:** Download inventories manually and commit them
3. **Best fix:** Configure proxy bypass for docs.python.org, etc.

**Priority:** LOW - Doesn't block PR if CI has internet access

---

## Next Steps: User Decision Required

### Immediate Action

**Please choose an approach:**

**A) Phased approach (recommended):**
   - Phase 1: Adjust pileup_threshold (quick PR unblock)
   - Phase 2: Update test expectations (robust tests)
   - Phase 3: Algorithm improvement (future work)
   - Timeline: 2-4 hours for Phases 1-2

**B) Algorithm fix first:**
   - Implement Option 2 (sharpness heuristic)
   - More thorough but takes longer
   - Timeline: 4-6 hours

**C) Test updates only:**
   - Update all test expectations
   - Fastest path to green CI
   - Algorithm unchanged
   - Timeline: 1-2 hours

### Questions

1. **Conservative vs. Accurate:** Do you want the algorithm to be:
   - Conservative (flag more samples, lower false negatives)
   - Accurate (match pileup extent, better characterization)

2. **Risk tolerance:** Are you comfortable with:
   - Quick threshold adjustment (Phase 1)
   - Or prefer thorough algorithm review first

3. **Test philosophy:** Should tests verify:
   - Exact threshold values (current approach)
   - Detection works + reasonable thresholds (more flexible)

---

## Files for Reference

**Source code:**
- `src/fitqc/boundary.py` (lines 641-677: delta function special case)
- `src/fitqc/config.py` (line 234: pileup_threshold default)

**Tests:**
- `tests/test_boundary_fixes.py` (13 failures)
- `tests/test_boundary_quantile.py` (3 failures)

**Debug scripts:**
- `/home/user/fitqc/debug_test_failure.py` (full test case)
- `/home/user/fitqc/debug_elbow_detection.py` (isolated elbow detection)
- `/home/user/fitqc/debug_quantile_curve.png` (visualization)

---

**Status:** ⏳ **AWAITING USER DECISION ON FIX APPROACH**
