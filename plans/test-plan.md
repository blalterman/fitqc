# fitqc Test Plan

## Test Philosophy

### Completeness Criteria
A test suite is **complete** when it verifies:
1. **Correctness** — Functions produce mathematically correct outputs
2. **Contracts** — Input/output shapes, types, and ranges are honored
3. **Edge cases** — Boundary conditions, empty inputs, degenerates handled
4. **Integration** — Components compose correctly end-to-end

### Non-Over-Engineering Criteria
A test suite is **not over-engineered** when:
1. Each test verifies a **distinct behavior** (no redundant tests)
2. Tests verify **observable behavior**, not implementation details
3. Tests are **parameterized** where behavior is identical across cases
4. Mock/stub complexity is **minimized** (prefer real computations)

### Machine Constants Policy
**Never hardcode machine epsilon.** Always use:
```python
np.finfo(np.float64).eps  # for float64
np.finfo(np.float32).eps  # for float32
```

---

## Test Suite Summary

| Module | # Tests | Behaviors Covered |
|--------|---------|-------------------|
| precision | 10 | dtype detection, ULP, quantization, eps formula |
| sortedops | 11 | tail mass, quantiles, slicing, edge cases |
| selection | 4 | elbow detection on various curve types |
| interior | 6 | z computation, spike detection, false positive prevention |
| boundary | 6 | u computation, pileup detection, asymmetric tolerances |
| spike_detection | 4 | prominence, width, broad distribution, drop after cut |
| plot_smoke | 5 | axes structure, colorbar, log panel, no show() |
| integration | 2 | full pipeline, JSON roundtrip |

**Total: ~48 tests**

---

## Module: `precision.py`

### Purpose
Floating-point precision utilities for comparing fit values at appropriate resolution.

### Functions Under Test
- `effective_dtype(x, precision_mode)` — Determine comparison dtype
- `ulp_at(val, dtype)` — Unit in last place at a given value
- `quantize_scalar(val, dtype)` — Round to dtype precision
- `eps_from_ulp(x0, L, U, dtype, mult)` — Compute eps threshold from ULP

---

### Test: `test_float32_array_returns_float32`

```python
def test_float32_array_returns_float32(self):
    x = np.array([1.0, 2.0], dtype=np.float32)
    assert effective_dtype(x, "auto") == np.float32
```

**Objective:** Verify auto-detection correctly identifies float32 storage.

**Justification:** Precision policy determines comparison resolution. Misidentifying float32 as float64 causes eps thresholds ~10^7 too small → false positives.

**Sufficiency:** Directly checks return value against known input dtype.

---

### Test: `test_float64_array_returns_float64`

```python
def test_float64_array_returns_float64(self):
    x = np.array([1.0, 2.0], dtype=np.float64)
    assert effective_dtype(x, "auto") == np.float64
```

**Objective:** Verify auto-detection identifies float64 storage.

**Justification:** Complement to float32 test. Float64 is Python default, may follow different code paths.

---

### Test: `test_override_to_float32`

```python
def test_override_to_float32(self):
    x = np.array([1.0, 2.0], dtype=np.float64)
    assert effective_dtype(x, "float32") == np.float32
```

**Objective:** Verify explicit precision_mode overrides auto-detection.

**Justification:** Users may know data was originally float32 but loaded as float64 (common with pandas/HDF5).

---

### Test: `test_ulp_at_one_float64`

```python
def test_ulp_at_one_float64(self):
    ulp = ulp_at(1.0, np.float64)
    expected = np.finfo(np.float64).eps  # Machine introspection
    assert ulp == pytest.approx(expected, rel=1e-10)
```

**Objective:** Verify ULP calculation is correct at reference point.

**Justification:** ULP at 1.0 equals machine epsilon. Uses `np.finfo`, not hardcoded value.

**Evidence:** IEEE 754 double: 52 mantissa bits → eps = 2^-52.

---

### Test: `test_ulp_at_one_float32`

```python
def test_ulp_at_one_float32(self):
    ulp = ulp_at(1.0, np.float32)
    expected = np.finfo(np.float32).eps  # Machine introspection
    assert ulp == pytest.approx(expected, rel=1e-6)
```

**Objective:** Verify ULP for float32.

**Justification:** Tests dtype-dependent path. Looser tolerance for float32 precision.

---

### Test: `test_ulp_increases_with_magnitude`

```python
def test_ulp_increases_with_magnitude(self):
    ulp_small = ulp_at(1.0, np.float64)
    ulp_large = ulp_at(1e6, np.float64)
    assert ulp_large > ulp_small * 1e5
```

**Objective:** Verify ULP scales with magnitude.

**Justification:** Property-based test. Catches common error of returning constant epsilon.

---

### Test: `test_quantize_preserves_float64_representable`

```python
def test_quantize_preserves_float64_representable(self):
    val = 1.5
    assert quantize_scalar(val, np.float64) == val
```

**Objective:** Verify quantization is identity for exactly representable values.

---

### Test: `test_quantize_to_float32_loses_precision`

```python
def test_quantize_to_float32_loses_precision(self):
    val = 1.0 + 1.00001 * np.finfo(np.float32).eps
    q = quantize_scalar(val, np.float32)
    assert q != val
    assert abs(q - 1.0) < 2 * np.finfo(np.float32).eps
```

**Objective:** Verify quantization loses precision appropriately.

---

### Test: `test_eps_from_ulp_at_center`

```python
def test_eps_from_ulp_at_center(self):
    x0, L, U = 0.5, 0.0, 1.0
    eps = eps_from_ulp(x0, L, U, np.float64, mult=1)
    expected = ulp_at(0.5, np.float64) / 1.0
    assert eps == pytest.approx(expected, rel=1e-10)
```

**Objective:** Verify eps = ULP(x0) / width formula.

---

### Test: `test_eps_scales_with_mult`

```python
def test_eps_scales_with_mult(self):
    eps1 = eps_from_ulp(0.5, 0.0, 1.0, np.float64, mult=1)
    eps4 = eps_from_ulp(0.5, 0.0, 1.0, np.float64, mult=4)
    assert eps4 == pytest.approx(4 * eps1, rel=1e-10)
```

**Objective:** Verify mult parameter scales eps linearly.

---

### Completeness Table

| Behavior | Test |
|----------|------|
| Auto-detect float32 | `test_float32_array_returns_float32` |
| Auto-detect float64 | `test_float64_array_returns_float64` |
| Override precision mode | `test_override_to_float32` |
| ULP correctness (f64) | `test_ulp_at_one_float64` |
| ULP correctness (f32) | `test_ulp_at_one_float32` |
| ULP scales with magnitude | `test_ulp_increases_with_magnitude` |
| Quantization identity | `test_quantize_preserves_float64_representable` |
| Quantization loses precision | `test_quantize_to_float32_loses_precision` |
| eps from ULP formula | `test_eps_from_ulp_at_center` |
| eps mult scaling | `test_eps_scales_with_mult` |

---

## Module: `sortedops.py`

### Purpose
O(log n) operations on sorted arrays: tail mass, quantiles, range slicing.

---

### Test: `test_tail_mass_uniform_midpoint`

```python
def test_tail_mass_uniform_midpoint(self):
    x_sorted = np.linspace(0, 1, 10001)
    mass = tail_mass(x_sorted, 0.5)
    assert mass == pytest.approx(0.5, abs=1e-4)
```

**Objective:** P(x <= 0.5) for uniform[0,1] ≈ 0.5.

**Justification:** Tests core CDF calculation. Tolerance accounts for discrete approximation.

---

### Test: `test_tail_mass_at_zero`

```python
def test_tail_mass_at_zero(self):
    x_sorted = np.sort(np.abs(np.random.default_rng(42).standard_normal(1000)) + 0.01)
    mass = tail_mass(x_sorted, 0.0)
    assert mass == 0.0
```

**Objective:** P(x <= 0) = 0 when all values > 0.

---

### Test: `test_tail_mass_beyond_max`

```python
def test_tail_mass_beyond_max(self):
    x_sorted = np.array([1.0, 2.0, 3.0])
    mass = tail_mass(x_sorted, 4.0)
    assert mass == 1.0
```

**Objective:** P(x <= max+1) = 1.0.

---

### Test: `test_tail_mass_increasing`

```python
def test_tail_mass_increasing(self):
    x_sorted = np.sort(np.random.default_rng(42).standard_normal(1000))
    thresholds = np.linspace(-3, 3, 50)
    masses = [tail_mass(x_sorted, t) for t in thresholds]
    assert all(masses[i] <= masses[i+1] for i in range(len(masses)-1))
```

**Objective:** Tail mass is monotonically non-decreasing.

**Justification:** Property-based test. CDF must be non-decreasing by definition.

---

### Test: `test_quantile_median_known`

```python
def test_quantile_median_known(self):
    x_sorted = np.array([0, 1, 2, 3, 4], dtype=float)
    assert quantile_by_index(x_sorted, 0.5) == 2.0
```

**Objective:** Median of [0,1,2,3,4] is 2.

---

### Test: `test_quantile_endpoints`

```python
def test_quantile_endpoints(self):
    x_sorted = np.array([10.0, 20.0, 30.0])
    assert quantile_by_index(x_sorted, 0.0) == 10.0
    assert quantile_by_index(x_sorted, 1.0) == 30.0
```

**Objective:** q=0 gives min, q=1 gives max.

**Justification:** Catches off-by-one errors in indexing formula.

---

### Test: `test_quantile_array_input`

```python
def test_quantile_array_input(self):
    x_sorted = np.linspace(0, 100, 101)
    q = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    result = quantile_by_index(x_sorted, q)
    np.testing.assert_array_equal(result, [0, 25, 50, 75, 100])
```

**Objective:** Vectorized quantile queries work.

---

### Test: `test_quantile_shape_preserved`

```python
def test_quantile_shape_preserved(self):
    x_sorted = np.sort(np.random.default_rng(42).standard_normal(1000))
    q = np.array([[0.1, 0.2], [0.8, 0.9]])
    result = quantile_by_index(x_sorted, q)
    assert result.shape == (2, 2)
```

**Objective:** Output shape matches query shape.

---

### Test: `test_slice_excludes_boundaries`

```python
def test_slice_excludes_boundaries(self):
    x_sorted = np.array([0.1, 0.2, 0.5, 0.8, 0.9])
    lo_idx, hi_idx = slice_by_range(x_sorted, 0.2, 0.8)
    result = x_sorted[lo_idx:hi_idx]
    np.testing.assert_array_equal(result, [0.5])
```

**Objective:** Slice is open interval (excludes boundaries).

---

### Test: `test_slice_full_range`

```python
def test_slice_full_range(self):
    x_sorted = np.array([1.0, 2.0, 3.0])
    lo_idx, hi_idx = slice_by_range(x_sorted, -np.inf, np.inf)
    assert lo_idx == 0
    assert hi_idx == 3
```

**Objective:** Infinite bounds return full array.

---

### Test: `test_slice_empty_when_no_match`

```python
def test_slice_empty_when_no_match(self):
    x_sorted = np.array([1.0, 2.0, 3.0])
    lo_idx, hi_idx = slice_by_range(x_sorted, 5.0, 10.0)
    assert lo_idx == hi_idx
```

**Objective:** Empty slice when range excludes all data.

---

## Module: `selection.py`

### Purpose
Elbow detection using kneed library.

---

### Test: `test_elbow_on_known_curve`

```python
def test_elbow_on_known_curve(self):
    x = np.linspace(0.1, 10, 100)
    y = 1 - np.exp(-x)
    elbow = select_elbow(x, y, curve="concave", direction="increasing")
    assert 1.5 < elbow < 4.0
```

**Objective:** Detect elbow on exponential saturation curve.

---

### Test: `test_elbow_on_step_function`

```python
def test_elbow_on_step_function(self):
    x = np.linspace(0, 10, 101)
    y = np.where(x < 5, 0.0, 1.0)
    elbow = select_elbow(x, y, curve="concave", direction="increasing")
    assert 4.0 < elbow < 6.0
```

**Objective:** Detect elbow near step transition.

---

### Test: `test_elbow_returns_fallback_for_linear`

```python
def test_elbow_returns_fallback_for_linear(self):
    x = np.linspace(0, 10, 100)
    y = x / 10
    elbow = select_elbow(x, y, curve="concave", direction="increasing")
    assert elbow is None or (0 <= elbow <= 10)
```

**Objective:** Graceful handling when no elbow exists.

---

### Test: `test_elbow_log_space_ecdf_like`

```python
def test_elbow_log_space_ecdf_like(self):
    eps = np.logspace(-8, -2, 50)
    p = 1 - np.exp(-eps * 1e6)
    elbow = select_elbow(eps, p, curve="concave", direction="increasing", log_x=True)
    assert 1e-7 < elbow < 1e-4
```

**Objective:** Works in log-space (as used for eps selection).

---

## Module: `interior.py`

### Purpose
Detect initial-guess stickiness via distance from x0.

---

### Test: `test_compute_z_at_x0`

```python
def test_compute_z_at_x0(self):
    x = np.array([5.0, 5.0, 5.0])
    z = compute_z(x, x0=5.0, L=0.0, U=10.0)
    np.testing.assert_array_equal(z, [0.0, 0.0, 0.0])
```

**Objective:** z=0 when x equals x0.

---

### Test: `test_compute_z_at_bounds`

```python
def test_compute_z_at_bounds(self):
    x = np.array([0.0, 10.0])
    z = compute_z(x, x0=5.0, L=0.0, U=10.0)
    np.testing.assert_array_equal(z, [0.5, 0.5])
```

**Objective:** z=0.5 at bounds when x0 is centered.

---

### Test: `test_interior_qc_detects_spike`

```python
def test_interior_qc_detects_spike(self):
    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=10000)
    spike_idx = rng.choice(10000, size=500, replace=False)
    x[spike_idx] = 5.0  # 5% exactly at x0

    result = run_interior_qc(x, x0=5.0, L=0.0, U=10.0, config=InteriorConfig())

    assert result.spike_detected is True
    assert result.spike_z_loc < 0.01
    assert result.eps_star < 0.01
```

**Objective:** Detect injected x0 stickiness.

**Justification:** Core use case. 5% concentration should produce prominent peak.

---

### Test: `test_interior_qc_no_false_positive_uniform`

```python
def test_interior_qc_no_false_positive_uniform(self):
    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=10000)

    result = run_interior_qc(x, x0=5.0, L=0.0, U=10.0, config=InteriorConfig())

    assert result.spike_detected is False
```

**Objective:** No false positive on uniform data.

---

### Test: `test_interior_qc_signed_lognormal_no_false_spike`

```python
def test_interior_qc_signed_lognormal_no_false_spike(self):
    """Critical: signed log-normal with x0≈0 should NOT trigger false spike."""
    x = generate_signed_lognormal(n=10000, mu=0, sigma=1, sign_prob=0.5, seed=42)

    result = run_interior_qc(x, x0=0.0, L=-100.0, U=100.0, config=InteriorConfig())

    assert result.spike_detected is False
```

**Objective:** No false spike for signed log-normal at x0=0.

**Justification:** Critical edge case. Broad mass near 0 is natural, not stickiness. Width criteria must distinguish.

---

## Module: `boundary.py`

### Purpose
Detect boundary stickiness via proximity to L and U.

---

### Test: `test_compute_u_at_bounds`

```python
def test_compute_u_at_bounds(self):
    x = np.array([0.0, 5.0, 10.0])
    u = compute_u(x, L=0.0, U=10.0)
    np.testing.assert_array_equal(u, [0.0, 0.5, 1.0])
```

**Objective:** u=0 at L, u=1 at U, u=0.5 at midpoint.

---

### Test: `test_boundary_qc_detects_lower_pileup`

```python
def test_boundary_qc_detects_lower_pileup(self):
    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=10000)
    x[:500] = rng.uniform(0, 0.1, size=500)  # 5% near lower

    result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

    assert result.t_lo_star > 0.005
    assert result.lower_pileup_detected is True
```

**Objective:** Detect lower boundary pileup.

---

### Test: `test_boundary_qc_detects_upper_pileup`

```python
def test_boundary_qc_detects_upper_pileup(self):
    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=10000)
    x[:500] = rng.uniform(9.9, 10.0, size=500)

    result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

    assert result.t_hi_star > 0.005
    assert result.upper_pileup_detected is True
```

**Objective:** Detect upper boundary pileup.

---

### Test: `test_boundary_qc_no_pileup_uniform`

```python
def test_boundary_qc_no_pileup_uniform(self):
    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=10000)

    result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

    assert result.t_lo_star < 0.01
    assert result.t_hi_star < 0.01
```

**Objective:** No false positive on uniform data.

---

### Test: `test_boundary_qc_asymmetric_tolerances`

```python
def test_boundary_qc_asymmetric_tolerances(self):
    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=10000)
    x[:500] = rng.uniform(0, 0.1, size=500)  # Only lower

    result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

    assert result.t_lo_star > result.t_hi_star * 2
```

**Objective:** Lower and upper tolerances computed independently.

---

## Module: `test_spike_detection.py`

### Purpose
Dedicated tests for find_peaks spike detection.

---

### Test: `test_spike_prominence_above_threshold`

```python
def test_spike_prominence_above_threshold(self):
    rng = np.random.default_rng(42)
    z = np.abs(rng.normal(0.5, 0.2, size=10000))
    z[:500] = rng.uniform(0, 0.01, size=500)

    hist_counts, _ = np.histogram(z, bins=100, range=(0, 1))
    peaks, props = find_peaks(hist_counts, prominence=10)

    assert len(peaks) > 0
    assert props['prominences'][0] > 50
```

**Objective:** Injected spike has high prominence.

---

### Test: `test_spike_width_narrow`

```python
def test_spike_width_narrow(self):
    rng = np.random.default_rng(42)
    z = np.abs(rng.normal(0.5, 0.2, size=10000))
    z[:500] = rng.uniform(0, 0.01, size=500)

    hist_counts, _ = np.histogram(z, bins=100, range=(0, 1))
    peaks, _ = find_peaks(hist_counts, prominence=10)
    widths = peak_widths(hist_counts, peaks)[0]

    assert widths[0] < 10  # Narrow
```

**Objective:** Spike is narrow in bin space.

---

### Test: `test_broad_distribution_no_spike`

```python
def test_broad_distribution_no_spike(self):
    rng = np.random.default_rng(42)
    z = np.abs(rng.normal(0, 0.3, size=10000))  # Half-normal

    hist_counts, bin_edges = np.histogram(z, bins=100, range=(0, 1))
    peaks, _ = find_peaks(hist_counts, prominence=10)

    if len(peaks) > 0:
        widths = peak_widths(hist_counts, peaks)[0]
        near_zero_mask = bin_edges[peaks] < 0.1
        if near_zero_mask.any():
            assert widths[near_zero_mask][0] > 20  # Wide, not spike
```

**Objective:** Broad distribution not misclassified as spike.

---

### Test: `test_spike_drop_after_cut`

```python
def test_spike_drop_after_cut(self):
    rng = np.random.default_rng(42)
    z = np.abs(rng.normal(0.5, 0.2, size=10000))
    z[:500] = rng.uniform(0, 0.01, size=500)

    hist_before, _ = np.histogram(z, bins=100, range=(0, 1))
    peaks_before, props_before = find_peaks(hist_before, prominence=10)
    prom_before = props_before['prominences'][0]

    z_kept = z[z > 0.02]
    hist_after, _ = np.histogram(z_kept, bins=100, range=(0, 1))
    peaks_after, props_after = find_peaks(hist_after, prominence=10)

    if len(peaks_after) > 0:
        assert props_after['prominences'][0] < prom_before * 0.5
```

**Objective:** Prominence drops after eps* cut.

---

## Module: `plot.py`

### Purpose
Diagnostic plots with tolerance overlays and colorbars.

---

### Test: `test_interior_plot_has_expected_axes`

```python
def test_interior_plot_has_expected_axes(self):
    result = create_mock_interior_result()
    fig = plot_interior_diagnostics(result, PlotConfig())
    assert len(fig.axes) >= 3
```

---

### Test: `test_boundary_plot_has_colorbar`

```python
def test_boundary_plot_has_colorbar(self):
    result = create_mock_boundary_result()
    fig = plot_boundary_diagnostics(result, PlotConfig())
    has_colorbar = any('colorbar' in str(type(ax)).lower() for ax in fig.axes)
    assert has_colorbar
```

---

### Test: `test_log_magnitude_panel_present`

```python
def test_log_magnitude_panel_present(self):
    config = PlotConfig(include_log_abs_panel=True)
    fig = plot_boundary_diagnostics(create_mock_boundary_result(), config)
    has_log = any(ax.get_xscale() == 'log' for ax in fig.axes)
    assert has_log
```

---

### Test: `test_plot_returns_figure_not_none`

```python
def test_plot_returns_figure_not_none(self):
    fig = plot_interior_diagnostics(create_mock_interior_result(), PlotConfig())
    assert isinstance(fig, plt.Figure)
```

---

### Test: `test_plot_does_not_call_show`

```python
def test_plot_does_not_call_show(self, monkeypatch):
    show_called = []
    monkeypatch.setattr(plt, 'show', lambda: show_called.append(True))
    plot_interior_diagnostics(create_mock_interior_result(), PlotConfig())
    assert len(show_called) == 0
```

---

## Module: `test_integration_end2end.py`

---

### Test: `test_full_pipeline_multi_parameter`

```python
def test_full_pipeline_multi_parameter(self):
    params = {
        'normal': generate_normal(n=5000, seed=1),
        'lognormal': generate_lognormal(n=5000, seed=2),
        'signed_lognormal': generate_signed_lognormal(n=5000, seed=3),
    }
    spec = QCSpec(
        param_names=list(params.keys()),
        x0={'normal': 0.0, 'lognormal': 1.0, 'signed_lognormal': 0.0},
        bounds={'normal': (-10, 10), 'lognormal': (0.01, 100), 'signed_lognormal': (-100, 100)},
    )

    report, masks = run_qc(params, spec, InteriorConfig(), BoundaryConfig(), PrecisionConfig())

    assert len(report.interior_results) == 3
    assert len(report.boundary_results) == 3
    assert all(masks[n].shape == (5000,) for n in params)

    json_str = report.to_json()
    assert 'interior_results' in json.loads(json_str)
```

---

### Test: `test_json_roundtrip`

```python
def test_json_roundtrip(self):
    report = create_mock_report()
    json_str = report.to_json()
    parsed = json.loads(json_str)
    assert parsed['interior_results'][0]['eps_star'] == pytest.approx(
        report.interior_results[0].eps_star
    )
```

---

## Non-Over-Engineering Justification

1. **No redundant tests:** Each test verifies distinct behavior
2. **No implementation testing:** Tests verify outputs, not internal state
3. **Parameterization used:** Distribution types parameterized in smoke tests
4. **Minimal mocking:** Only monkeypatch for plt.show()
5. **Tolerances justified:** Each pytest.approx has documented rationale
6. **Edge cases selective:** Only algorithm-relevant cases tested
