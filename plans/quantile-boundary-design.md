# Comprehensive Quantile-Based Boundary Stickiness Detection: Design Plan

**Status:** DRAFT - Awaiting user approval before implementation
**Date:** 2026-01-19
**Goal:** Implement multi-curve quantile-based boundary pileup detection with progressive tolerance grids

---

## Executive Summary

**Current State:** Boundary detection uses a single mass curve `P(u < tol)` vs `tol` with uniform tolerance spacing. The `quantile_grid` config parameter exists but is unused.

**Proposed Change:** Implement true multi-curve quantile analysis with progressive (non-uniform) tolerance grids that concentrate resolution where stickiness actually occurs.

**Key Benefits:**
- Higher resolution detection of tight boundary pileups (0-1% of range)
- Robustness from multiple independent elbow detections across quantiles
- Reduced false positives from statistical noise
- Efficient computation by avoiding wasted samples far from boundaries

---

## Part 1: Current State Analysis

### What Works Today

```python
# In boundary.py lines 127-148
lower_mass_curve = np.array([tail_mass(u_sorted, tol) for tol in tol_grid])
t_lo_raw = select_elbow(tol_grid, lower_mass_curve, curve="concave", direction="increasing")
```

**Strengths:**
- Simple, easy to understand
- Works for obvious pileups (>2% of range)
- Single elbow = single decision point

**Weaknesses:**
1. **Uniform tolerance grid wastes resolution:**
   - 41 points from 0.0 to 0.05 = 0.125% spacing
   - Most real pileups are 0-1%, but we sample 1-5% with same density
   - Tight pileups (0.1-0.3%) may fall between grid points

2. **Single curve lacks robustness:**
   - One noisy region can corrupt the elbow
   - No cross-validation from multiple signals
   - Can't distinguish statistical noise from real structure

3. **Quantile grid documented but unused:**
   - Config has `quantile_grid = (0.01, 0.05, 0.10, 0.25, 0.50)`
   - Docstring promises "multiple curves, each potentially showing an elbow"
   - Implementation ignores this entirely

### Evidence from Test Data

From `test_stickiness.py` fixtures:
- `data_with_lower_pileup`: 5% pileup uniformly in [0, 0.1*range]
- `data_with_upper_pileup`: 5% pileup uniformly in [0.9*range, range]

These are **broad** pileups (10% of range). Real optimizer stickiness is often tighter:
- Float precision artifacts: 0.01-0.1% of range
- Constraint-hitting optimizers: 0.5-2% of range

Current grid spacing (0.125%) is marginal for these cases.

---

## Part 2: Design Decisions

### Decision 1: Tolerance Grid Strategy

#### Option 1A: Progressive Non-Uniform Grid (Recommended)

**Description:** Use denser spacing near boundaries, coarser farther out.

```python
# Example progressive grid (45 points total)
tol_grid = np.concatenate([
    np.linspace(0.0000, 0.0010, 11),  # 0-0.1%:   11 points, 0.01% spacing
    np.linspace(0.0010, 0.0050, 17)[1:],  # 0.1-0.5%: 16 points, 0.025% spacing
    np.linspace(0.0050, 0.0200, 13)[1:],  # 0.5-2%:   12 points, 0.125% spacing
    np.linspace(0.0200, 0.0500, 7)[1:],   # 2-5%:      6 points, 0.75% spacing
])
```

**Propositions FOR:**
- ✅ **Resolution where it matters:** 11 points in 0-0.1% vs current 1 point
- ✅ **Same total cost:** 45 points vs current 41, but better distributed
- ✅ **Backward compatible:** Doesn't change API or algorithm logic
- ✅ **Physical intuition:** Stickiness is tight; natural variation is broad
- ✅ **Easy to tune:** Can adjust breakpoints based on empirical data

**Propositions AGAINST:**
- ❌ **Assumes stickiness is always tight:** If real pileup is 3-5%, we waste resolution at 0-0.5%
- ❌ **Grid design requires domain knowledge:** What are the "right" breakpoints?
- ❌ **Harder to interpret:** Non-uniform spacing complicates visualization
- ❌ **May interact badly with elbow detection:** Kneedle algorithm expects roughly uniform sampling

**Evidence Required:**
- Test on synthetic data with pileups at different scales (0.1%, 0.5%, 1%, 2%, 5%)
- Verify elbow detection still works with non-uniform grids
- Compare detection precision vs uniform grid

---

#### Option 1B: Logarithmic Grid

**Description:** Use log-spacing like interior detection.

```python
tol_grid = np.logspace(-4, np.log10(0.05), 50)  # [0.0001, ..., 0.05]
```

**Propositions FOR:**
- ✅ **Consistent with interior API:** Both use log-spacing
- ✅ **Natural for multi-scale phenomena:** Captures precision effects and broad pileups
- ✅ **Works with select_elbow(log_x=True):** Proven path

**Propositions AGAINST:**
- ❌ **Tolerance is naturally linear:** Boundary proximity isn't multi-scale like epsilon
- ❌ **Wastes points at tiny tolerances:** Do we care about 0.01% vs 0.001%?
- ❌ **Conceptually wrong:** log(0) is undefined; starting at 0 is important

**Verdict:** Not recommended. Tolerances are linear distances, not scale factors.

---

#### Option 1C: Adaptive Two-Stage Grid

**Description:** Coarse scan, then refine around detected elbow.

```python
# Stage 1: Coarse uniform grid
coarse_tol = np.linspace(0.0, 0.05, 21)
coarse_elbow = find_elbow(coarse_tol, compute_mass_curve(coarse_tol))

# Stage 2: Fine grid around elbow
if coarse_elbow is not None:
    fine_tol = np.linspace(max(0, coarse_elbow - 0.01), coarse_elbow + 0.01, 41)
    fine_elbow = find_elbow(fine_tol, compute_mass_curve(fine_tol))
```

**Propositions FOR:**
- ✅ **Adapts to data automatically:** No hard-coded breakpoints
- ✅ **Optimal resolution:** Focuses compute where needed
- ✅ **Robust to unexpected pileup shapes:** Handles anything coarse scan finds

**Propositions AGAINST:**
- ❌ **Two-pass = harder to vectorize:** Must recompute mass curve
- ❌ **Complex to test:** Need tests for stage 1 only, stage 2 refinement, edge cases
- ❌ **Slower:** 2x the tail_mass calls (though still O(log n) each)
- ❌ **Ambiguous when no coarse elbow:** What if stage 1 finds nothing? Run stage 2 anyway?

**Verdict:** Over-engineered for initial implementation. Consider for future if progressive grid insufficient.

---

### Decision 2: Quantile Analysis Strategy

#### Option 2A: Inverse CDF Multi-Curve (Recommended)

**Description:** For each quantile q, track which tolerance achieves `P(u < tol) = q`.

```python
quantile_grid = (0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10)  # progressive!

# For each quantile, find the tolerance where mass = quantile
tol_at_quantile = np.zeros(len(quantile_grid))
for i, q in enumerate(quantile_grid):
    # Inverse lookup: find tol where lower_mass_curve ≈ q
    tol_at_quantile[i] = np.interp(q, lower_mass_curve, tol_grid)

# Now we have curve: (quantile, tolerance_to_achieve_it)
# For uniform data: tol ≈ q (linear relationship)
# For pileup: tol << q initially (many samples in small tolerance)
#             tol ≈ q later (back to uniform)
# Elbow shows transition from pileup to natural variation
```

**Physical Interpretation:**
- **Uniform data:** To capture 1% of samples, need tolerance ≈ 1% → tol/q ≈ 1
- **Pileup data:** To capture 1% of samples, need tolerance ≈ 0.1% → tol/q ≈ 0.1
- **Elbow location:** Quantile where tol/q ratio transitions from <1 to ≈1

**Propositions FOR:**
- ✅ **Multi-curve robustness:** Each quantile gives independent elbow estimate
- ✅ **Matches documented API:** Actually uses `quantile_grid` config parameter
- ✅ **Statistical interpretation:** "What tolerance captures the Nth percentile?"
- ✅ **Detects different pileup shapes:** Tight pileups show elbow at low quantiles; broad at high
- ✅ **Natural aggregation:** Median/mode of elbows across quantiles = robust estimate

**Propositions AGAINST:**
- ❌ **More complex than single curve:** Need to track N elbows, then aggregate
- ❌ **Interpolation artifacts:** `np.interp` can be noisy if mass_curve has plateaus
- ❌ **What if elbows disagree?** Need aggregation strategy (median? weighted average?)
- ❌ **Computational cost:** N quantiles × M tolerances, though still cheap

**Evidence Required:**
- Test that elbows from different quantiles converge for clean pileups
- Test behavior when quantiles give conflicting elbows (noisy data)
- Define aggregation strategy with mathematical justification

---

#### Option 2B: Direct Quantile Curves

**Description:** For each quantile q, compute `P(u < tol)` only on the q-quantile subset.

```python
# For q=0.05, look at only the bottom 5% of u values
u_bottom_5pct = u_sorted[:int(0.05 * len(u_sorted))]

# Now compute mass curve on this subset
# This isolates the extreme tail behavior
```

**Propositions FOR:**
- ✅ **Directly isolates tail behavior:** Each quantile focuses on different tail depth
- ✅ **Independent curves:** Less correlation between quantiles

**Propositions AGAINST:**
- ❌ **Small sample sizes:** 1% quantile on 1000 samples = 10 points → noisy
- ❌ **Loses context:** Can't compare tail vs body behavior
- ❌ **Unclear interpretation:** What does "mass curve on a subset" mean physically?

**Verdict:** Conceptually muddled. Option 2A is clearer.

---

#### Option 2C: No Quantile Analysis (Status Quo)

Keep single mass curve approach.

**Propositions FOR:**
- ✅ **Simple, works for obvious cases**
- ✅ **No implementation work**

**Propositions AGAINST:**
- ❌ **Leaves quantile_grid unused** (violates documented API)
- ❌ **Less robust to noise**
- ❌ **Misses documented feature**

**Verdict:** Not acceptable. We promised quantile analysis in the docs; we should deliver it.

---

### Decision 3: Aggregation Strategy for Multi-Curve Elbows

Given N elbows from N quantiles, how do we choose the "best" tolerance?

#### Option 3A: Median of Elbows (Recommended)

```python
elbows = [select_elbow(tol_grid, curve_for_quantile[i]) for i in range(N)]
elbows_valid = [e for e in elbows if e is not None]
if len(elbows_valid) >= N // 2:  # At least half found elbows
    t_star = float(np.median(elbows_valid))
else:
    t_star = None  # Not enough evidence
```

**Propositions FOR:**
- ✅ **Robust to outliers:** One bad quantile doesn't ruin estimate
- ✅ **Simple, well-defined:** Median is unambiguous
- ✅ **Threshold for confidence:** Require majority of quantiles to agree
- ✅ **Standard statistical practice:** Median is default robust estimator

**Propositions AGAINST:**
- ❌ **Loses information:** Doesn't use elbow "strength" or confidence
- ❌ **Arbitrary threshold:** Why N//2 and not 2*N//3?

---

#### Option 3B: Weighted Average by Quantile

```python
# Weight earlier quantiles more (they isolate pileup better)
weights = 1.0 / np.array(quantile_grid)  # Higher weight for lower quantiles
weighted_mean = np.average(elbows_valid, weights=weights[:len(elbows_valid)])
```

**Propositions FOR:**
- ✅ **Prioritizes tight pileups:** Low quantiles are more sensitive
- ✅ **Uses all information:** Doesn't discard any valid elbows

**Propositions AGAINST:**
- ❌ **Arbitrary weighting:** Why 1/q? Why not 1/q² or exp(-q)?
- ❌ **Sensitive to outliers:** Unlike median, one bad elbow skews result
- ❌ **Hard to justify mathematically**

---

#### Option 3C: Most Conservative (Minimum)

```python
t_star = min(elbows_valid)  # Tightest tolerance across all quantiles
```

**Propositions FOR:**
- ✅ **Conservative:** Minimizes false negatives
- ✅ **Physical meaning:** "Pileup extends at least this far"

**Propositions AGAINST:**
- ❌ **Over-sensitive:** One noisy low quantile = false positive
- ❌ **Ignores consensus:** Even if 6/7 quantiles agree at 0.01, one at 0.001 wins

**Verdict:** Too aggressive, will increase false positives.

---

### Decision 4: Elbow Detection Method

Should we change how elbows are found?

#### Option 4A: Keep Kneedle (Status Quo)

Use existing `select_elbow` with `curve="concave", direction="increasing"`.

**Propositions FOR:**
- ✅ **Proven algorithm:** Satopaa et al. 2011, well-cited
- ✅ **Already tested:** Works for interior detection
- ✅ **No new dependencies**

**Propositions AGAINST:**
- ❌ **May struggle with non-uniform grids:** Expects evenly spaced points
- ❌ **No confidence metric:** Returns elbow or None, no "strength" measure

---

#### Option 4B: Custom Elbow via Second Derivative

```python
# Compute discrete second derivative of mass curve
d2_mass = np.diff(np.diff(lower_mass_curve))
# Elbow = point of maximum negative curvature
elbow_idx = np.argmin(d2_mass) + 1  # +1 for indexing offset
t_star = tol_grid[elbow_idx]
```

**Propositions FOR:**
- ✅ **Direct mathematical definition:** Elbow = max curvature
- ✅ **Returns confidence:** Can use |d2_mass| as strength metric
- ✅ **Works with any grid spacing**

**Propositions AGAINST:**
- ❌ **Sensitive to noise:** Second derivative amplifies noise
- ❌ **Need smoothing:** Requires preprocessing (Savitzky-Golay filter?)
- ❌ **Reinventing the wheel:** Kneedle handles this robustly

**Verdict:** Not worth the complexity. Stick with Kneedle.

---

## Part 3: Test Specifications

### Test Philosophy

**NO shallow tests!** Every test must verify:
1. **Shape:** Array dimensions, length matching expectations
2. **Dtype:** Correct float64 vs float32 vs int types
3. **Values:** Numerical correctness, not just `is not None`
4. **Monotonicity:** Arrays that should be sorted/increasing
5. **Bounds:** Values in expected ranges [0, 1], etc.
6. **Edge cases:** Empty data, single point, all identical

### Test Suite Structure

```
tests/test_boundary_quantile.py
├── TestProgressiveGrid           (Decision 1)
├── TestQuantileCurveComputation  (Decision 2)
├── TestElbowAggregation          (Decision 3)
├── TestDetectionCorrectnessMultiCurve
└── TestRegressionVsSingleCurve
```

---

### Test Group 1: Progressive Grid Properties

#### Test 1.1: `test_progressive_grid_spacing_increases`

```python
def test_progressive_grid_spacing_increases():
    """Progressive grid should have increasing spacing as tol increases.

    Spacing should be:
    - Finest near 0 (where stickiness is)
    - Progressively coarser farther out
    """
    config = BoundaryConfig(
        tol_min=0.0,
        tol_max=0.05,
        n_tols=45,
        grid_mode="progressive"  # NEW config option
    )
    grid = _build_tolerance_grid(config)  # NEW internal function

    # Compute spacing between consecutive points
    spacings = np.diff(grid)

    # Verify properties:
    assert grid.dtype == np.float64, "Grid must be float64"
    assert len(grid) == 45, f"Expected 45 points, got {len(grid)}"
    assert grid[0] == 0.0, f"First point should be 0.0, got {grid[0]}"
    assert grid[-1] == pytest.approx(0.05), f"Last point should be 0.05, got {grid[-1]}"

    # Monotonicity
    assert np.all(np.diff(grid) > 0), "Grid must be strictly increasing"

    # Progressive spacing: partition into regions and verify spacing increases
    # Region 1: [0, 0.001] should have spacing ~ 0.0001
    region1_mask = grid <= 0.001
    region1_spacing = np.mean(spacings[region1_mask[:-1]])

    # Region 2: [0.001, 0.005] should have spacing ~ 0.00025
    region2_mask = (grid > 0.001) & (grid <= 0.005)
    region2_spacing = np.mean(spacings[region2_mask[:-1]])

    # Region 3: [0.005, 0.02] should have spacing ~ 0.00125
    region3_mask = (grid > 0.005) & (grid <= 0.02)
    region3_spacing = np.mean(spacings[region3_mask[:-1]])

    # Region 4: [0.02, 0.05] should have spacing ~ 0.0075
    region4_mask = grid > 0.02
    region4_spacing = np.mean(spacings[region4_mask[:-1]])

    # Verify progressive increase (with tolerance for edge effects)
    assert region1_spacing < region2_spacing, \
        f"Spacing should increase: R1={region1_spacing:.6f} >= R2={region2_spacing:.6f}"
    assert region2_spacing < region3_spacing, \
        f"Spacing should increase: R2={region2_spacing:.6f} >= R3={region3_spacing:.6f}"
    assert region3_spacing < region4_spacing, \
        f"Spacing should increase: R3={region3_spacing:.6f} >= R4={region4_spacing:.6f}"
```

**What this tests:**
- Grid construction logic
- Correct partitioning into regions
- Monotonically increasing spacing
- Numerical correctness of breakpoints

**Why it matters:**
- If spacing doesn't progressively increase, we haven't gained anything over uniform
- Catches off-by-one errors in region boundaries
- Verifies dtype consistency (important for precision)

---

#### Test 1.2: `test_progressive_grid_coverage_matches_uniform`

```python
def test_progressive_grid_coverage_matches_uniform():
    """Progressive grid should cover same range as uniform with comparable density.

    We're redistributing points, not adding/removing them. Total coverage
    (area under density curve) should be similar.
    """
    # Uniform grid (baseline)
    uniform_grid = np.linspace(0.0, 0.05, 41)

    # Progressive grid (new)
    config = BoundaryConfig(n_tols=45, grid_mode="progressive")
    progressive_grid = _build_tolerance_grid(config)

    # Both should span [0, 0.05]
    assert uniform_grid[0] == progressive_grid[0] == 0.0
    assert uniform_grid[-1] == pytest.approx(progressive_grid[-1])

    # For any tolerance in [0, 0.05], nearest neighbor in progressive grid
    # should be closer than in uniform grid on average in the region [0, 0.01]
    test_tols = np.linspace(0.0, 0.01, 100)  # Test points in tight region

    uniform_errors = []
    progressive_errors = []

    for t in test_tols:
        # Find nearest grid point
        uniform_nearest = uniform_grid[np.argmin(np.abs(uniform_grid - t))]
        progressive_nearest = progressive_grid[np.argmin(np.abs(progressive_grid - t))]

        uniform_errors.append(abs(t - uniform_nearest))
        progressive_errors.append(abs(t - progressive_nearest))

    # Progressive should have smaller mean error in [0, 0.01] region
    assert np.mean(progressive_errors) < np.mean(uniform_errors), \
        f"Progressive grid should have better resolution in tight region: " \
        f"prog={np.mean(progressive_errors):.6f} >= uniform={np.mean(uniform_errors):.6f}"
```

**What this tests:**
- Coverage equivalence (same span)
- Resolution improvement where it matters
- Trade-off is correct (better near 0, worse far out)

**Why it matters:**
- Ensures we're not accidentally under-sampling any region
- Quantifies the resolution improvement
- Validates the design trade-off

---

### Test Group 2: Quantile Curve Computation

#### Test 2.1: `test_quantile_curve_uniform_data_is_linear`

```python
def test_quantile_curve_uniform_data_is_linear():
    """For uniform data, quantile curve should be tol ≈ q (linear relationship).

    This is the null hypothesis: if there's no pileup, the tolerance needed
    to capture quantile q should be approximately q itself.
    """
    rng = np.random.default_rng(42)
    u = rng.uniform(0, 1, size=10000)
    u_sorted = np.sort(u)

    quantile_grid = np.array([0.001, 0.005, 0.01, 0.02, 0.05, 0.10])
    tol_grid = np.linspace(0.0, 0.15, 151)  # Dense for accurate interpolation

    # Compute mass curve
    lower_mass_curve = np.array([tail_mass(u_sorted, tol) for tol in tol_grid])

    # For each quantile, find tolerance where mass ≈ quantile
    tol_at_quantile = np.interp(quantile_grid, lower_mass_curve, tol_grid)

    # Verify properties
    assert tol_at_quantile.dtype == np.float64
    assert tol_at_quantile.shape == quantile_grid.shape
    assert np.all(tol_at_quantile > 0), "All tolerances must be positive"
    assert np.all(np.diff(tol_at_quantile) > 0), "Must be monotonically increasing"

    # For uniform data, tol ≈ q (within sampling error)
    # Expect ratio tol/q ≈ 1.0 ± 0.1 for large samples
    ratio = tol_at_quantile / quantile_grid

    np.testing.assert_allclose(ratio, 1.0, rtol=0.1, atol=0.01,
        err_msg=f"Uniform data should have tol/q ≈ 1, got {ratio}")

    # Verify linearity via R² test
    from scipy.stats import linregress
    slope, intercept, r_value, p_value, std_err = linregress(quantile_grid, tol_at_quantile)

    assert r_value**2 > 0.99, f"Should be linear (R²={r_value**2:.4f}), got R²={r_value**2:.4f}"
    assert slope == pytest.approx(1.0, abs=0.1), f"Slope should be ≈1, got {slope:.3f}"
    assert abs(intercept) < 0.01, f"Intercept should be ≈0, got {intercept:.3f}"
```

**What this tests:**
- Correct interpolation from mass curve
- Null hypothesis (uniform data gives linear relationship)
- Statistical validity (R² test)
- Array shape/dtype correctness

**Why it matters:**
- This is the baseline. If uniform data doesn't give linear, something is wrong.
- Provides quantitative threshold for "what is uniform enough"
- Tests the entire pipeline: tail_mass → interp → quantile curve

---

#### Test 2.2: `test_quantile_curve_tight_pileup_shows_elbow`

```python
def test_quantile_curve_tight_pileup_shows_elbow():
    """For tight pileup, quantile curve should show clear elbow at low quantiles.

    Tight pileup (e.g., 5% of data in 0.2% of range) means:
    - For q < 0.05: tol << q (can capture with tiny tolerance)
    - For q > 0.05: tol ≈ q (back to uniform behavior)
    - Elbow should occur around q ≈ 0.05
    """
    # Generate tight pileup: 5% of samples in [0, 0.002]
    x = generate_with_boundary_pileup(
        n=10000, L=0.0, U=1.0,
        lower_pileup_frac=0.05,
        pileup_width=0.002,
        seed=42
    )
    u = compute_u(x, L=0.0, U=1.0)
    u_sorted = np.sort(u)

    quantile_grid = np.array([0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20])
    tol_grid = np.linspace(0.0, 0.25, 251)

    lower_mass_curve = np.array([tail_mass(u_sorted, tol) for tol in tol_grid])
    tol_at_quantile = np.interp(quantile_grid, lower_mass_curve, tol_grid)

    # Compute ratio tol/q
    ratio = tol_at_quantile / quantile_grid

    # For q <= 0.05 (within pileup), ratio should be << 1
    pileup_region_mask = quantile_grid <= 0.05
    pileup_ratios = ratio[pileup_region_mask]
    assert np.all(pileup_ratios < 0.5), \
        f"Pileup region should have tol << q (ratio < 0.5), got {pileup_ratios}"

    # For q > 0.10 (beyond pileup), ratio should be ≈ 1
    uniform_region_mask = quantile_grid > 0.10
    uniform_ratios = ratio[uniform_region_mask]
    np.testing.assert_allclose(uniform_ratios, 1.0, rtol=0.15, atol=0.05,
        err_msg=f"Beyond pileup, should be uniform (ratio ≈ 1), got {uniform_ratios}")

    # Elbow detection on (quantile, tol) curve should find elbow around q=0.05
    elbow_q = select_elbow(quantile_grid, tol_at_quantile,
                           curve="concave", direction="increasing")

    assert elbow_q is not None, "Should detect elbow for pileup data"
    assert 0.03 <= elbow_q <= 0.08, \
        f"Elbow should be near q=0.05 (pileup fraction), got {elbow_q:.3f}"

    # The tolerance at the elbow should be the pileup width
    tol_at_elbow = np.interp(elbow_q, quantile_grid, tol_at_quantile)
    assert tol_at_elbow == pytest.approx(0.002, abs=0.001), \
        f"Tolerance at elbow should match pileup width (0.002), got {tol_at_elbow:.4f}"
```

**What this tests:**
- Detection of actual pileup in quantile space
- Elbow location matches known pileup parameters
- Regions before/after elbow have expected behavior
- Quantitative thresholds for "clear elbow"

**Why it matters:**
- This is the core capability: can we detect real pileups?
- Validates that elbow position has physical meaning (matches pileup width)
- Provides regression target (must continue detecting this case)

---

#### Test 2.3: `test_quantile_curve_shape_dtype_bounds`

```python
def test_quantile_curve_shape_dtype_bounds():
    """Quantile curve should have correct shape, dtype, and value bounds."""
    rng = np.random.default_rng(42)
    x = rng.uniform(0, 1, size=1000)
    u_sorted = np.sort(x)

    quantile_grid = np.array([0.01, 0.05, 0.10])
    tol_grid = np.linspace(0.0, 0.15, 100)

    mass_curve = np.array([tail_mass(u_sorted, tol) for tol in tol_grid])
    tol_at_quantile = np.interp(quantile_grid, mass_curve, tol_grid)

    # Shape
    assert tol_at_quantile.shape == (3,), \
        f"Shape should match quantile_grid, got {tol_at_quantile.shape}"

    # Dtype
    assert tol_at_quantile.dtype == np.float64, \
        f"Should be float64, got {tol_at_quantile.dtype}"

    # Bounds: tolerances must be in [0, tol_max]
    assert np.all(tol_at_quantile >= 0.0), \
        f"Tolerances must be non-negative, got min={tol_at_quantile.min()}"
    assert np.all(tol_at_quantile <= 0.15), \
        f"Tolerances must be <= tol_max, got max={tol_at_quantile.max()}"

    # Monotonicity
    assert np.all(np.diff(tol_at_quantile) >= 0), \
        "Tolerances must increase with quantiles (larger quantile needs larger tolerance)"

    # No NaN or inf
    assert not np.any(np.isnan(tol_at_quantile)), "Must not contain NaN"
    assert not np.any(np.isinf(tol_at_quantile)), "Must not contain inf"
```

**What this tests:**
- Basic array correctness
- Defensive checks against numerical issues

**Why it matters:**
- These are the tests that catch silly bugs
- Ensures downstream code can safely use the output

---

### Test Group 3: Elbow Aggregation

#### Test 3.1: `test_median_aggregation_robust_to_outliers`

```python
def test_median_aggregation_robust_to_outliers():
    """Median aggregation should ignore outlier elbows from noisy quantiles."""
    # Simulate elbow detection results from 7 quantiles
    # 6 agree at 0.010, 1 outlier at 0.040
    elbows = [0.010, 0.011, 0.009, 0.010, 0.040, 0.011, 0.010]

    result = _aggregate_elbows_median(elbows)

    # Median should be 0.010 (not affected by 0.040 outlier)
    assert result == pytest.approx(0.010, abs=0.001), \
        f"Median should be 0.010, got {result}"

    # Compare to mean (would be pulled by outlier)
    mean_result = np.mean(elbows)
    assert mean_result > 0.014, "Mean should be pulled up by outlier"
    assert result < mean_result, "Median should be more robust than mean"
```

**What this tests:**
- Correct implementation of median
- Robustness property vs mean

**Why it matters:**
- Validates design choice (median vs mean)
- Shows median provides robustness we want

---

#### Test 3.2: `test_aggregation_requires_majority_agreement`

```python
def test_aggregation_requires_majority_agreement():
    """Should return None if less than half of quantiles found elbows.

    If only 2 out of 7 quantiles detected elbows, there's not enough
    evidence for pileup. Return None rather than basing decision on
    weak minority signal.
    """
    # Only 2 out of 7 found elbows (rest are None)
    elbows_mostly_none = [None, 0.010, None, None, 0.012, None, None]

    result = _aggregate_elbows_median(elbows_mostly_none,
                                      min_agreement_frac=0.5)

    assert result is None, \
        "Should return None when <50% of quantiles found elbows"

    # Exactly 4 out of 7 (>50%) should succeed
    elbows_majority = [0.010, 0.011, None, 0.010, None, 0.009, None]

    result_majority = _aggregate_elbows_median(elbows_majority,
                                                min_agreement_frac=0.5)

    assert result_majority is not None, \
        "Should return value when >=50% found elbows"
    assert result_majority == pytest.approx(0.010, abs=0.001)
```

**What this tests:**
- Threshold logic for confidence
- Correct counting of None vs float values

**Why it matters:**
- Prevents false positives from weak signals
- Tests edge case (exactly 50% agreement)

---

### Test Group 4: End-to-End Detection Correctness

#### Test 4.1: `test_multi_curve_detects_tight_pileup_missed_by_single_curve`

```python
def test_multi_curve_detects_tight_pileup_missed_by_single_curve():
    """Multi-curve should detect tight pileups that single curve misses.

    Generate pileup at 0.3% of range (falls between uniform grid points).
    Single curve with uniform grid may miss it; multi-curve with progressive
    grid should catch it.
    """
    # Very tight pileup: 3% of samples in 0.3% of range
    x = generate_with_boundary_pileup(
        n=10000, L=0.0, U=1.0,
        lower_pileup_frac=0.03,
        pileup_width=0.003,
        seed=42
    )

    # Old method: single curve, uniform grid
    config_old = BoundaryConfig(n_tols=41, grid_mode="uniform")
    result_old = run_boundary_qc(x, L=0.0, U=1.0, config=config_old)

    # New method: multi-curve, progressive grid
    config_new = BoundaryConfig(
        n_tols=45,
        grid_mode="progressive",
        quantile_grid=(0.005, 0.01, 0.02, 0.03, 0.05, 0.10),
        use_quantile_analysis=True
    )
    result_new = run_boundary_qc(x, L=0.0, U=1.0, config=config_new)

    # New method should detect, old might not
    assert result_new.lower_pileup_detected, \
        "New method should detect tight pileup"

    # Verify detected tolerance is near true pileup width
    assert result_new.t_lo_star is not None
    assert result_new.t_lo_star == pytest.approx(0.003, abs=0.002), \
        f"Should detect pileup at ~0.003, got {result_new.t_lo_star:.4f}"

    # Old method may or may not detect (grid spacing is 0.125% = 0.00125)
    # We don't assert it fails (might get lucky), just that new is more precise
    if result_old.t_lo_star is not None:
        # If old method detected, new should give similar or better precision
        assert abs(result_new.t_lo_star - 0.003) <= abs(result_old.t_lo_star - 0.003), \
            "New method should be at least as accurate as old"
```

**What this tests:**
- Regression: new is better than old
- Detection of tight pileups
- Precision of tolerance estimate

**Why it matters:**
- This is the VALUE PROPOSITION of the whole change
- Provides evidence for why we're doing this work

---

#### Test 4.2: `test_multi_curve_no_false_positives_on_uniform`

```python
def test_multi_curve_no_false_positives_on_uniform():
    """Multi-curve should not increase false positives on clean data.

    More sophisticated detection shouldn't mean more false alarms.
    Uniform data should still be classified as no pileup.
    """
    rng = np.random.default_rng(42)
    x_uniform = rng.uniform(0, 1, size=10000)

    config = BoundaryConfig(
        n_tols=45,
        grid_mode="progressive",
        quantile_grid=(0.005, 0.01, 0.02, 0.05, 0.10),
        use_quantile_analysis=True
    )

    result = run_boundary_qc(x_uniform, L=0.0, U=1.0, config=config)

    # Should NOT detect pileup
    assert not result.lower_pileup_detected, \
        "Uniform data should not trigger lower pileup detection"
    assert not result.upper_pileup_detected, \
        "Uniform data should not trigger upper pileup detection"

    # If elbows found, they should be very small (near uniform expectation)
    if result.t_lo_star is not None:
        assert result.t_lo_star < 0.01, \
            f"Any detected tolerance should be tiny (<1%), got {result.t_lo_star:.4f}"
    if result.t_hi_star is not None:
        assert result.t_hi_star < 0.01, \
            f"Any detected tolerance should be tiny (<1%), got {result.t_hi_star:.4f}"
```

**What this tests:**
- False positive rate on null data
- Regression vs old method

**Why it matters:**
- Adding complexity should not sacrifice specificity
- Tests that aggregation thresholds are set correctly

---

#### Test 4.3: `test_multi_curve_handles_broad_pileup`

```python
def test_multi_curve_handles_broad_pileup():
    """Should still detect broad pileups (not just tight ones).

    Progressive grid concentrates resolution at small tolerances, but
    should still work for pileups at 2-5% of range.
    """
    # Broad pileup: 10% of samples in 5% of range
    x = generate_with_boundary_pileup(
        n=10000, L=0.0, U=1.0,
        lower_pileup_frac=0.10,
        pileup_width=0.05,
        seed=42
    )

    config = BoundaryConfig(
        n_tols=45,
        grid_mode="progressive",
        quantile_grid=(0.01, 0.02, 0.05, 0.10, 0.15),
        use_quantile_analysis=True
    )

    result = run_boundary_qc(x, L=0.0, U=1.0, config=config)

    assert result.lower_pileup_detected, "Should detect broad pileup"
    assert result.t_lo_star is not None

    # Tolerance should be in range [0.03, 0.07] (near 0.05 true width)
    assert 0.03 <= result.t_lo_star <= 0.07, \
        f"Should detect pileup near 0.05, got {result.t_lo_star:.3f}"
```

**What this tests:**
- No regression on broad pileups
- Grid covers full range adequately

**Why it matters:**
- Ensures we didn't over-optimize for tight pileups
- Validates that coarser spacing at large tolerances is still sufficient

---

### Test Group 5: Backward Compatibility

#### Test 5.1: `test_single_curve_mode_still_available`

```python
def test_single_curve_mode_still_available():
    """Old single-curve method should still work via config flag.

    For users who don't want the complexity of multi-curve, or for
    comparison/debugging, single-curve mode should remain available.
    """
    x = generate_with_boundary_pileup(
        n=10000, L=0.0, U=1.0,
        lower_pileup_frac=0.05,
        pileup_width=0.01,
        seed=42
    )

    config = BoundaryConfig(
        n_tols=41,
        grid_mode="uniform",
        use_quantile_analysis=False  # Explicit opt-out
    )

    result = run_boundary_qc(x, L=0.0, U=1.0, config=config)

    # Should work without errors
    assert isinstance(result, BoundaryResult)
    assert result.lower_pileup_detected  # Should still detect obvious pileup

    # Result should NOT have quantile-specific fields
    assert not hasattr(result, 'quantile_elbows'), \
        "Single-curve mode should not compute quantile elbows"
```

**What this tests:**
- Backward compatibility
- Config flag behavior

**Why it matters:**
- Doesn't break existing users
- Allows A/B testing of methods

---

### Test Group 6: Edge Cases

#### Test 6.1: `test_empty_array`

```python
def test_empty_array():
    """Should handle empty input gracefully."""
    x = np.array([], dtype=np.float64)

    config = BoundaryConfig(use_quantile_analysis=True)
    result = run_boundary_qc(x, L=0.0, U=1.0, config=config)

    assert not result.lower_pileup_detected
    assert not result.upper_pileup_detected
    assert result.t_lo_star is None
    assert result.t_hi_star is None
    assert isinstance(result.tol_grid, np.ndarray)
    assert len(result.lower_mass_curve) == len(result.tol_grid)
```

#### Test 6.2: `test_single_value`

```python
def test_single_value():
    """Single value should not crash or detect pileup."""
    x = np.array([0.5])

    config = BoundaryConfig(use_quantile_analysis=True)
    result = run_boundary_qc(x, L=0.0, U=1.0, config=config)

    # Should not detect pileup (insufficient data)
    assert not result.lower_pileup_detected
    assert not result.upper_pileup_detected
```

#### Test 6.3: `test_all_at_boundary`

```python
def test_all_at_boundary():
    """All samples at boundary should definitely detect pileup."""
    x = np.zeros(1000)  # All at lower bound

    config = BoundaryConfig(use_quantile_analysis=True)
    result = run_boundary_qc(x, L=0.0, U=1.0, config=config)

    assert result.lower_pileup_detected, "Should detect when all samples at L"
    assert result.t_lo_star is not None
    assert result.t_lo_star < 0.01, "All at boundary = very tight pileup"
```

---

## Part 4: Implementation Strategy

### Phase 1: Infrastructure (No Behavior Change)

**Goal:** Add new code paths without changing existing behavior.

**Tasks:**
1. Add `grid_mode` field to `BoundaryConfig` (default="uniform" for backward compat)
2. Implement `_build_tolerance_grid(config)` function
3. Add tests for grid construction (Test Group 1)
4. Verify old tests still pass

**Acceptance Criteria:**
- All existing tests pass
- New grid construction tested
- No changes to `run_boundary_qc` yet

---

### Phase 2: Quantile Curve Computation

**Goal:** Compute quantile curves alongside existing single curve.

**Tasks:**
1. Add `use_quantile_analysis` field to `BoundaryConfig` (default=False)
2. Implement `_compute_quantile_curves(u_sorted, tol_grid, quantile_grid)`
3. Add to `BoundaryResult`: optional `quantile_elbows` field
4. Add tests for quantile curve computation (Test Group 2)

**Acceptance Criteria:**
- When `use_quantile_analysis=True`, both methods run
- Both produce same result on clean data
- Tests verify quantile curves have expected properties

---

### Phase 3: Elbow Aggregation

**Goal:** Aggregate multiple elbows into single robust estimate.

**Tasks:**
1. Implement `_aggregate_elbows_median(elbows, min_agreement_frac=0.5)`
2. Integrate into `run_boundary_qc`: use aggregated elbow when enabled
3. Add tests for aggregation (Test Group 3)

**Acceptance Criteria:**
- Aggregation handles None values correctly
- Median is robust to outliers (tested)
- Confidence threshold works as expected

---

### Phase 4: Integration and End-to-End Testing

**Goal:** Full integration with detection logic.

**Tasks:**
1. Update `run_boundary_qc` to use quantile-based t_star when enabled
2. Add end-to-end tests (Test Group 4)
3. Add backward compatibility tests (Test Group 5)
4. Add edge case tests (Test Group 6)

**Acceptance Criteria:**
- Detects tight pileups better than old method
- No increase in false positives
- Old method still available via config
- All edge cases handled

---

### Phase 5: Documentation and Defaults

**Goal:** Document new features and set sensible defaults.

**Tasks:**
1. Update docstrings in `boundary.py` and `config.py`
2. Consider changing defaults:
   - `grid_mode="progressive"` (from "uniform")
   - `use_quantile_analysis=True` (from False)
   - `quantile_grid` adjusted to progressive values
3. Add example in docs showing multi-curve in action
4. Update changelog

**Acceptance Criteria:**
- Docstrings match implementation
- Examples run without errors
- User-facing API is clear

---

## Part 5: Open Questions for User Decision

### Q1: Should we change the defaults?

**Options:**
- A) Keep `grid_mode="uniform"`, `use_quantile_analysis=False` (safe, backward compatible)
- B) Change to `grid_mode="progressive"`, `use_quantile_analysis=True` (better detection, breaking change)
- C) Change defaults but add deprecation warning for 1-2 versions

**Recommendation:** Start with (A), plan for (C) after validation period.

---

### Q2: What should `quantile_grid` default values be?

**Current:** `(0.01, 0.05, 0.10, 0.25, 0.50)`

**Proposed:** `(0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10)` (progressive, matches tight pileup focus)

**Trade-off:**
- More quantiles = more robustness, but more compute
- Low quantiles (0.001) may be noisy for small samples (<1000)

**Recommendation:** Progressive quantile grid, but test on small samples (n=100, 500) to verify stability.

---

### Q3: Should we expose quantile elbows in result object?

**Options:**
- A) Only return aggregated `t_lo_star` (simple API)
- B) Add optional `quantile_elbows: dict[float, float | None]` field (transparency)

**Recommendation:** (B) for debugging and research; users can ignore if not needed.

---

### Q4: Minimum sample size for multi-curve?

Should we automatically fall back to single-curve for small samples?

```python
if len(x) < 1000 and config.use_quantile_analysis:
    warnings.warn("Sample size <1000, falling back to single-curve method")
    config.use_quantile_analysis = False
```

**Recommendation:** Yes, with warning. Low quantiles become unstable for n<500.

---

## Part 6: Success Metrics

### Before/After Comparison

Run on synthetic benchmark suite:

| Scenario | Old Method (uniform grid, single curve) | New Method (progressive grid, multi-curve) |
|----------|----------------------------------------|-------------------------------------------|
| Tight pileup (0.3%, 3% of samples) | Detection rate: ?% | Detection rate: ?% |
| Broad pileup (5%, 10% of samples) | Detection rate: ?% | Detection rate: ?% |
| Uniform data | False positive rate: ?% | False positive rate: ?% |
| Normal data centered at 0.5 | False positive rate: ?% | False positive rate: ?% |

**Goal:** New method should have:
- ≥20% improvement in tight pileup detection
- No regression on broad pileups (within 5%)
- ≤2% increase in false positive rate

---

## Part 7: Implementation Checklist

### Code Changes
- [ ] Add `grid_mode` to `BoundaryConfig`
- [ ] Implement `_build_tolerance_grid(config)`
- [ ] Add `use_quantile_analysis` to `BoundaryConfig`
- [ ] Implement `_compute_quantile_curves(...)`
- [ ] Implement `_aggregate_elbows_median(...)`
- [ ] Update `run_boundary_qc` to use new logic when enabled
- [ ] Add `quantile_elbows` field to `BoundaryResult`

### Tests
- [ ] Test Group 1: Progressive Grid (2 tests)
- [ ] Test Group 2: Quantile Curves (3 tests)
- [ ] Test Group 3: Elbow Aggregation (2 tests)
- [ ] Test Group 4: End-to-End Detection (3 tests)
- [ ] Test Group 5: Backward Compatibility (1 test)
- [ ] Test Group 6: Edge Cases (3 tests)

### Documentation
- [ ] Update `config.py` docstrings
- [ ] Update `boundary.py` docstrings
- [ ] Add example to docs
- [ ] Update changelog

### Validation
- [ ] Run benchmark suite (before/after comparison)
- [ ] Verify all old tests still pass
- [ ] Test on real data (if available)
- [ ] Get user approval before changing defaults

---

## Appendix: Risk Analysis

### High Risk
- **Kneedle struggles with non-uniform grids:** Mitigate by testing thoroughly
- **Aggregation threshold (50%) is arbitrary:** Mitigate by making it configurable

### Medium Risk
- **More complexity = more bugs:** Mitigate with comprehensive tests
- **Performance regression:** Mitigate by profiling (should be minimal, still O(log n) per query)

### Low Risk
- **API breaking changes:** Mitigated by using config flags, keeping defaults
- **Documentation drift:** Mitigated by updating docs in same PR

---

## Final Recommendation

**Recommended Path:**
1. Implement Option 1A (progressive grid) + Option 2A (inverse CDF multi-curve) + Option 3A (median aggregation)
2. Keep as opt-in feature initially (`use_quantile_analysis=False` by default)
3. Extensive testing per Test Groups 1-6
4. Benchmark on synthetic data
5. If benchmarks show ≥20% improvement without FP increase, change defaults in next release
6. Document the new capability with examples

**Estimated Implementation Time:**
- Phase 1: 2-3 hours
- Phase 2: 3-4 hours
- Phase 3: 2 hours
- Phase 4: 4-5 hours
- Phase 5: 1-2 hours
- **Total: ~15 hours of development + testing**

---

**AWAITING USER APPROVAL TO PROCEED**

Do you approve this plan? Any modifications needed before implementation?
