# Test Quality Analysis: test_plot_filter_comparison.py

## Current State Assessment

### What's Missing

Comparing `tests/test_plot_filter_comparison.py` to existing test standards in:
- `tests/test_boundary.py`
- `tests/test_interior.py`
- `tests/test_plot_quantile_elbow_overlay.py`

### Critical Gaps

#### 1. **Smoke Tests Only - No Content Verification**

**Current tests:**
```python
def test_returns_figure(self):
    """Test that function returns a Figure object."""
    x = np.concatenate([...])
    fig = plot_bounds_filter_comparison(x, L=0.01, U=100.0, bins=50)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
```

**Standard from existing tests:**
```python
def test_compute_u_at_bounds(self):
    """Test that u=0 at L, u=1 at U, u=0.5 at midpoint."""
    x = np.array([0.0, 5.0, 10.0])
    u = compute_u(x, L=0.0, U=10.0)
    np.testing.assert_array_equal(u, [0.0, 0.5, 1.0])  # VERIFY EXACT VALUES
```

**Problem:** I check "does it return something" but not "does it return the RIGHT thing"

#### 2. **No Data Verification**

My tests don't verify:
- That filtered data is actually filtered correctly
- That histogram counts are correct
- That bin edges match between subplots
- That the data plotted matches expectations

**Should add:**
```python
def test_filtering_is_applied_correctly(self):
    """Verify that plot shows correct filtering of out-of-bounds samples.

    This is critical because we're visualizing the filtering that protects
    the boundary detection algorithm from failed fits and out-of-range values.
    The plot must accurately show what data is being removed.
    """
    # Create known data with exactly 100 out-of-bounds samples
    x = np.concatenate([
        np.array([0.0] * 100),  # Below L
        np.linspace(1.0, 10.0, 900)  # Valid
    ])

    fig = plot_bounds_filter_comparison(x, L=1.0, U=10.0, bins=50)

    # Verify title contains correct counts
    axes = fig.axes
    assert "1,000" in axes[0].get_title()  # Total samples
    assert "100" in axes[0].get_title()  # Out-of-bounds count
    assert "900" in axes[1].get_title()  # Retained samples

    # Could also verify histogram data directly
    plt.close(fig)
```

#### 3. **Inadequate Docstrings**

**Current:**
```python
def test_returns_figure(self):
    """Test that function returns a Figure object."""
```

**Standard from existing tests:**
```python
def test_interior_qc_signed_lognormal_no_false_spike(self):
    """Critical: signed log-normal with x0 approx 0 should NOT trigger false spike.

    Signed log-normal naturally has mass near zero, but it's BROAD, not a spike.
    The width criterion should prevent false positives.
    """
```

**Problem:** My docstrings don't explain:
- WHY the test matters scientifically
- WHAT behavior we're protecting against
- Background context for scientists

#### 4. **Missing Shape/Size/Dtype Checks**

**Should add:**
```python
def test_result_structure_and_data_integrity(self):
    """Verify plot structure and data consistency.

    The plot must have exactly 2 subplots with matching bin edges and
    y-axis scales for direct visual comparison. This ensures scientists
    can accurately assess the impact of filtering on their dataset.
    """
    x = np.random.uniform(0, 100, 1000)
    fig = plot_bounds_filter_comparison(x, L=0.0, U=100.0, bins=50)

    # Check structure
    assert len(fig.axes) == 2

    # Check that both axes have histograms
    for ax in fig.axes:
        patches = [p for p in ax.patches if p.get_height() > 0]
        assert len(patches) > 0, "Axis should have histogram bars"

    # Verify y-axis scales are matched
    y_lim_0 = fig.axes[0].get_ylim()
    y_lim_1 = fig.axes[1].get_ylim()
    assert y_lim_0 == y_lim_1, "Y-axes must match for direct comparison"

    plt.close(fig)
```

#### 5. **No Module-Level Docstring**

**Current:** None

**Standard from test_plot_quantile_elbow_overlay.py:**
```python
"""Tests for plot_quantile_elbow_overlay function.

This test module defines the expected API and behavior for the plot_quantile_elbow_overlay
function, which visualizes quantile elbow points from detection results (InteriorResult
or BoundaryResult with quantile analysis enabled).

The function should:
- Accept InteriorResult or BoundaryResult objects containing quantile_elbows data
- Return a matplotlib.figure.Figure object
- Visualize quantile values vs their detected elbow thresholds
- Use PlotConfig for styling (colormap, DPI, etc.)
- Handle edge cases like None elbows, empty dicts, single quantiles gracefully

Tests are marked as xfail since the function is not yet implemented (TDD approach).
"""
```

#### 6. **Missing Scientific Context Tests**

**Should add tests like:**
```python
def test_overplotted_histograms_enable_visual_comparison(self):
    """Test that original and filtered histograms use same bins for comparison.

    Scientific rationale: When filtering out failed fits or boundary artifacts,
    scientists need to see EXACTLY where the removed samples were located in
    the distribution. Using identical bin edges ensures direct visual alignment.
    """
    # Test implementation...
```

#### 7. **No Edge Case Documentation**

My tests cover edge cases but don't explain WHY they matter:

**Current:**
```python
def test_handles_all_out_of_bounds(self):
    """Test with data where all samples are out-of-bounds."""
```

**Should be:**
```python
def test_handles_all_out_of_bounds(self):
    """Test graceful handling when all samples are filtered (catastrophic fit failure).

    In real PPA12 data, we've seen cases where fitting algorithms completely fail,
    returning all samples at x=0 (np1, np2, w_const). The plot must handle this
    edge case without crashing and should visually communicate that ALL data was
    rejected, alerting the scientist to a serious data quality issue.
    """
```

## Comparison to Standards

### Existing Test Standards

| Aspect | Existing Tests | My Tests | Status |
|--------|----------------|----------|--------|
| Content verification | ✓ np.testing.assert_array_equal | ✗ Only isinstance checks | ❌ FAIL |
| Shape/size checks | ✓ Check array shapes, lengths | ✗ Only count axes | ❌ FAIL |
| Dtype checks | ✓ isinstance for types | ✓ Some isinstance | ⚠️ PARTIAL |
| Scientific context | ✓ Detailed docstrings | ✗ Minimal docstrings | ❌ FAIL |
| Edge case rationale | ✓ Explains why cases matter | ✗ Just describes what | ❌ FAIL |
| Module docstring | ✓ Comprehensive overview | ✗ None | ❌ FAIL |
| Exact value tests | ✓ Tests specific values | ✗ No value verification | ❌ FAIL |
| Integration tests | ✓ Uses real algorithms | ✓ Uses mock results | ✓ PASS |

### Score: **2/8 = 25%**

## Recommended Improvements

### 1. Add Module Docstring

```python
"""Tests for filter comparison plotting functions.

This module verifies the correctness of visualization functions that show the
impact of data filtering on PPA12 datasets. These plots are critical for
validating that our boundary and interior stickiness detection algorithms are
correctly excluding:

1. Failed fits (samples at x=0 when L>0)
2. Out-of-bounds samples (optimizer violations)
3. Samples stuck at initial guesses

The plotting functions must:
- Apply filtering identical to the detection algorithms
- Use consistent binning for before/after comparison
- Accurately report sample counts in titles
- Handle edge cases (all filtered, none filtered)

Scientific Context:
Real PPA12 data contains failed fits where the optimizer returns invalid values
(e.g., np1 has 16,695 samples at x=0 when L=0.01). These plots help scientists
verify that filtering is working correctly before trusting detection results.
"""
```

### 2. Add Content Verification Tests

```python
def test_bounds_filter_shows_correct_sample_counts(self):
    """Verify that plot titles accurately report filtering statistics.

    Scientists rely on the sample count information to assess data quality.
    Incorrect counts could lead to misinterpretation of filtering impact,
    especially when deciding whether to trust detection results from datasets
    with high rates of failed fits (e.g., np2 with 2.08% out-of-bounds).
    """
    # Create data with known out-of-bounds counts
    x = np.concatenate([
        np.full(237, -5.0),  # Below L
        np.full(163, 105.0),  # Above U
        np.random.uniform(0, 100, 9600)
    ])

    fig = plot_bounds_filter_comparison(x, L=0.0, U=100.0, bins=50)

    # Verify unfiltered subplot title
    unfiltered_title = fig.axes[0].get_title()
    assert "10,000" in unfiltered_title or "10000" in unfiltered_title
    assert "400" in unfiltered_title  # Total out-of-bounds

    # Verify filtered subplot title
    filtered_title = fig.axes[1].get_title()
    assert "9,600" in filtered_title or "9600" in filtered_title

    plt.close(fig)
```

### 3. Add Data Integrity Tests

```python
def test_bin_edges_consistent_between_subplots(self):
    """Verify that both subplots use identical histogram bin edges.

    Consistent binning is essential for visual comparison. If bins differ,
    scientists cannot accurately assess which bins lost samples during filtering.
    This is particularly important for identifying boundary stickiness patterns
    that span multiple bins (e.g., e_dv_pp with wider interior spike).
    """
    x = np.random.uniform(0, 100, 1000)
    fig = plot_bounds_filter_comparison(x, L=0.0, U=100.0, bins=50)

    # Extract histogram patches from both subplots
    patches_0 = fig.axes[0].patches
    patches_1 = fig.axes[1].patches

    # Verify same number of bins
    assert len(patches_0) == len(patches_1)

    # Verify bin edges align (within floating point tolerance)
    for p0, p1 in zip(patches_0, patches_1):
        assert abs(p0.get_x() - p1.get_x()) < 1e-10
        assert abs(p0.get_width() - p1.get_width()) < 1e-10

    plt.close(fig)
```

### 4. Add Realistic Scenario Tests

```python
def test_np1_realistic_scenario(self):
    """Test with data similar to real np1 dataset (16,695 failed fits at x=0).

    np1 is a beam density parameter with bounds L=0.01, U=100.0. In the real
    data, 1.67% of samples are at exactly x=0.0, indicating complete fit failures
    where the optimizer returned the initialization value. This test verifies
    that the plot correctly shows this pattern.
    """
    # Simulate np1-like data
    rng = np.random.default_rng(42)
    x = np.concatenate([
        np.zeros(1670),  # 1.67% failed fits at x=0
        rng.lognormal(mean=2.0, sigma=1.5, size=98330)
    ])

    fig = plot_bounds_filter_comparison(x, L=0.01, U=100.0, bins=1000)

    # Should have 2 subplots
    assert len(fig.axes) == 2

    # Unfiltered should show all 100k samples
    unfiltered_title = fig.axes[0].get_title()
    assert "100,000" in unfiltered_title or "100000" in unfiltered_title

    # Filtered should show ~98.3% retained
    filtered_title = fig.axes[1].get_title()
    # Check for approximately 98,330 samples (some may be above U)
    assert "98," in filtered_title or "97," in filtered_title

    plt.close(fig)
```

## Docstring Standards from Codebase

Looking at `src/fitqc/boundary.py` and `src/fitqc/interior.py`:

### Good Example (compute_u):
```python
def compute_u(x: np.ndarray, L: float, U: float) -> np.ndarray:
    """Compute normalized position in the parameter range [L, U].

    Formula: u = (x - L) / (U - L)

    This gives:
        u = 0   when x is at the lower bound L
        u = 1   when x is at the upper bound U
        u = 0.5 when x is at the midpoint

    Why no max() in the denominator (unlike compute_z)?
    ---------------------------------------------------
    Here we measure WHERE a value sits in the range, not how far it is from
    some reference point. The range [L, U] is fixed and symmetric—every value
    maps linearly to [0, 1]. There's no "reference point" that could be off-center.

    Compare to compute_z (interior.py), which measures distance from x0:
    - z uses max(x0 - L, U - x0) because x0 might be near one bound
    - If x0 = 1 with L = 0, U = 10: max distance is 9 (to U), not 1 (to L)
    - Without max(), z would exceed 1 for some values

    Here, u always stays in [0, 1] for values in [L, U] because we're just
    rescaling the range, not measuring distance from an off-center point.
    ```

**My docstrings should have:**
- Clear formula/definition
- Scientific context
- Comparison to related concepts
- Explanation of design decisions

## Action Items

1. ✗ Add comprehensive module docstring
2. ✗ Rewrite test docstrings with scientific context
3. ✗ Add content verification tests (sample counts, bin edges, titles)
4. ✗ Add data integrity tests (shapes, scales, consistency)
5. ✗ Add realistic scenario tests (np1, np2 patterns)
6. ✗ Add exact value verification where possible
7. ✗ Explain WHY each edge case matters
8. ✗ Add integration tests using real PPA12 data

## Impact Assessment

**Current tests provide:** Basic smoke testing (functions don't crash)

**Missing critical verification:**
- ❌ Filtering is applied correctly
- ❌ Plot data matches input data
- ❌ Visual elements (titles, labels) are accurate
- ❌ Edge cases are handled scientifically correctly
- ❌ Real-world scenarios work as expected

**Risk:** Without proper tests, we cannot guarantee that these plots accurately
represent the filtering being applied to PPA12 data. Scientists could make
incorrect decisions based on misleading visualizations.

**Recommendation:** REWRITE tests to meet quality standards before considering
this work complete.
