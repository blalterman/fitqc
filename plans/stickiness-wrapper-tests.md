# Stickiness Wrapper Test Specifications

## Test Philosophy

Tests must be **non-trivial**: verify type, content, shape, dtype, and values.
No `assert X is not None` without additional substantive checks.

---

## Test File: `tests/test_stickiness.py`

**Total tests: ~59**

---

## 1. Module Structure Tests

### Class: `TestStickinessModuleStructure`

#### `test_detect_stickiness_importable_from_module`

```python
def test_detect_stickiness_importable_from_module(self):
    """Function must be importable from fitqc.stickiness."""
    from fitqc.stickiness import detect_stickiness

    assert callable(detect_stickiness)
    # Verify signature has expected parameters
    import inspect
    sig = inspect.signature(detect_stickiness)
    param_names = list(sig.parameters.keys())
    assert "x" in param_names
    assert "ref" in param_names
    assert "L" in param_names
    assert "U" in param_names
    assert "mode" in param_names
    assert "scale" in param_names
```

**Validates:** Import path, callable, signature parameters exist.

---

#### `test_detect_stickiness_importable_from_package`

```python
def test_detect_stickiness_importable_from_package(self):
    """Function must be importable from top-level fitqc package."""
    from fitqc import detect_stickiness

    assert callable(detect_stickiness)
```

**Validates:** Public API export in `__init__.py`.

---

#### `test_detect_stickiness_in_package_all`

```python
def test_detect_stickiness_in_package_all(self):
    """Function must be listed in fitqc.__all__."""
    import fitqc

    assert "detect_stickiness" in fitqc.__all__
```

**Validates:** Explicit public API declaration.

---

## 2. Mode Dispatch Tests

### Class: `TestModeDispatch`

#### `test_mode_interior_returns_interior_result`

```python
def test_mode_interior_returns_interior_result(self):
    """mode='interior' must return InteriorResult type."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.interior import InteriorResult

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="interior")

    assert isinstance(result, InteriorResult)
    assert hasattr(result, "spike_detected")
    assert hasattr(result, "eps_star")
    assert hasattr(result, "eps_grid")
    assert hasattr(result, "mass_curve")
    assert hasattr(result, "hist_counts")
    assert hasattr(result, "hist_edges")
```

**Validates:** Return type, all expected fields present.

---

#### `test_mode_lower_returns_boundary_result`

```python
def test_mode_lower_returns_boundary_result(self):
    """mode='lower' must return BoundaryResult type."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.boundary import BoundaryResult

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=0.0, L=0.0, U=10.0, mode="lower")

    assert isinstance(result, BoundaryResult)
```

**Validates:** Return type for lower mode.

---

#### `test_mode_upper_returns_boundary_result`

```python
def test_mode_upper_returns_boundary_result(self):
    """mode='upper' must return BoundaryResult type."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.boundary import BoundaryResult

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=10.0, L=0.0, U=10.0, mode="upper")

    assert isinstance(result, BoundaryResult)
```

**Validates:** Return type for upper mode.

---

#### `test_mode_all_returns_tuple`

```python
def test_mode_all_returns_tuple(self):
    """mode='all' must return tuple of (InteriorResult, BoundaryResult)."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.interior import InteriorResult
    from fitqc.boundary import BoundaryResult

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="all")

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], InteriorResult)
    assert isinstance(result[1], BoundaryResult)
```

**Validates:** Tuple structure, element types, length.

---

#### `test_mode_interior_result_matches_direct_call`

```python
def test_mode_interior_result_matches_direct_call(self):
    """Wrapper interior result must exactly match direct run_interior_qc call."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.interior import run_interior_qc

    rng = np.random.default_rng(42)
    x = rng.normal(5.0, 1.5, size=5000)
    x0, L, U = 5.0, 0.0, 10.0

    direct = run_interior_qc(x, x0=x0, L=L, U=U)
    wrapper = detect_stickiness(x, ref=x0, L=L, U=U, mode="interior")

    # Field-by-field equality
    assert wrapper.spike_detected == direct.spike_detected
    assert wrapper.spike_z_loc == direct.spike_z_loc
    assert wrapper.eps_star == direct.eps_star
    np.testing.assert_array_equal(wrapper.eps_grid, direct.eps_grid)
    np.testing.assert_array_equal(wrapper.mass_curve, direct.mass_curve)
    np.testing.assert_array_equal(wrapper.hist_counts, direct.hist_counts)
    np.testing.assert_array_equal(wrapper.hist_edges, direct.hist_edges)
```

**Validates:** Wrapper produces identical results to direct call.

---

#### `test_mode_all_interior_matches_direct_call`

```python
def test_mode_all_interior_matches_direct_call(self):
    """All mode interior component must match direct run_interior_qc call."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.interior import run_interior_qc

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=5000)
    x0, L, U = 5.0, 0.0, 10.0

    direct = run_interior_qc(x, x0=x0, L=L, U=U)
    interior_result, _ = detect_stickiness(x, ref=x0, L=L, U=U, mode="all")

    assert interior_result.spike_detected == direct.spike_detected
    np.testing.assert_array_equal(interior_result.eps_grid, direct.eps_grid)
    np.testing.assert_array_equal(interior_result.mass_curve, direct.mass_curve)
```

**Validates:** All mode interior component matches direct call.

---

#### `test_mode_all_boundary_matches_direct_call`

```python
def test_mode_all_boundary_matches_direct_call(self):
    """All mode boundary component must match direct run_boundary_qc call."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.boundary import run_boundary_qc

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=5000)
    L, U = 0.0, 10.0

    direct = run_boundary_qc(x, L=L, U=U)
    _, boundary_result = detect_stickiness(x, ref=5.0, L=L, U=U, mode="all")

    assert boundary_result.lower_pileup_detected == direct.lower_pileup_detected
    assert boundary_result.upper_pileup_detected == direct.upper_pileup_detected
    np.testing.assert_array_equal(boundary_result.tol_grid, direct.tol_grid)
    np.testing.assert_array_equal(boundary_result.lower_mass_curve, direct.lower_mass_curve)
    np.testing.assert_array_equal(boundary_result.upper_mass_curve, direct.upper_mass_curve)
```

**Validates:** All mode boundary component matches direct call.

---

## 3. Boundary Mode Field Handling Tests

### Class: `TestBoundaryModeFields`

#### `test_mode_lower_has_lower_fields_populated`

```python
def test_mode_lower_has_lower_fields_populated(self):
    """Lower mode must populate lower-boundary fields with valid data."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=0.0, L=0.0, U=10.0, mode="lower")

    # Lower fields must be populated and valid
    assert isinstance(result.lower_pileup_detected, bool)
    assert result.t_lo_star is None or isinstance(result.t_lo_star, float)
    assert isinstance(result.tol_grid, np.ndarray)
    assert result.tol_grid.ndim == 1
    assert len(result.tol_grid) > 0
    assert result.tol_grid.dtype in [np.float32, np.float64]
    assert isinstance(result.lower_mass_curve, np.ndarray)
    assert result.lower_mass_curve.shape == result.tol_grid.shape
    assert result.lower_mass_curve.dtype in [np.float32, np.float64]
    # Mass curve values must be probabilities
    assert np.all(result.lower_mass_curve >= 0.0)
    assert np.all(result.lower_mass_curve <= 1.0)
```

**Validates:** Type, ndim, shape, dtype, value range of lower fields.

---

#### `test_mode_lower_has_upper_fields_none`

```python
def test_mode_lower_has_upper_fields_none(self):
    """Lower mode must have upper-boundary fields set to None or False."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=0.0, L=0.0, U=10.0, mode="lower")

    # Upper fields must be None/False/empty
    assert result.upper_pileup_detected is False
    assert result.t_hi_star is None
    assert result.upper_mass_curve is None or len(result.upper_mass_curve) == 0
```

**Validates:** Upper fields correctly nulled for lower mode.

---

#### `test_mode_upper_has_upper_fields_populated`

```python
def test_mode_upper_has_upper_fields_populated(self):
    """Upper mode must populate upper-boundary fields with valid data."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=10.0, L=0.0, U=10.0, mode="upper")

    # Upper fields must be populated and valid
    assert isinstance(result.upper_pileup_detected, bool)
    assert result.t_hi_star is None or isinstance(result.t_hi_star, float)
    assert isinstance(result.upper_mass_curve, np.ndarray)
    assert result.upper_mass_curve.shape == result.tol_grid.shape
    assert np.all(result.upper_mass_curve >= 0.0)
    assert np.all(result.upper_mass_curve <= 1.0)
```

**Validates:** Type, shape, value range of upper fields.

---

#### `test_mode_upper_has_lower_fields_none`

```python
def test_mode_upper_has_lower_fields_none(self):
    """Upper mode must have lower-boundary fields set to None or False."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=10.0, L=0.0, U=10.0, mode="upper")

    # Lower fields must be None/False/empty
    assert result.lower_pileup_detected is False
    assert result.t_lo_star is None
    assert result.lower_mass_curve is None or len(result.lower_mass_curve) == 0
```

**Validates:** Lower fields correctly nulled for upper mode.

---

## 4. All Mode Tests

### Class: `TestAllMode`

#### `test_all_mode_returns_two_element_tuple`

```python
def test_all_mode_returns_two_element_tuple(self):
    """All mode must return exactly 2-element tuple."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="all")

    assert isinstance(result, tuple)
    assert len(result) == 2
```

**Validates:** Tuple type and exact length.

---

#### `test_all_mode_boundary_has_both_directions`

```python
def test_all_mode_boundary_has_both_directions(self):
    """All mode boundary result must have both lower and upper curves populated."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    _, boundary_result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="all")

    # Both curves must be populated arrays
    assert isinstance(boundary_result.lower_mass_curve, np.ndarray)
    assert isinstance(boundary_result.upper_mass_curve, np.ndarray)
    assert len(boundary_result.lower_mass_curve) > 0
    assert len(boundary_result.upper_mass_curve) > 0
    assert boundary_result.lower_mass_curve.shape == boundary_result.tol_grid.shape
    assert boundary_result.upper_mass_curve.shape == boundary_result.tol_grid.shape
```

**Validates:** Both mass curves populated with correct shapes.

---

## 5. Scale Parameter Tests

### Class: `TestScaleParameter`

#### `test_interior_bounded_ignores_scale`

```python
def test_interior_bounded_ignores_scale(self):
    """When L and U provided, scale parameter must be ignored."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    # Call with arbitrary scale value
    result_with_scale = detect_stickiness(
        x, ref=5.0, L=0.0, U=10.0, mode="interior", scale=999.0
    )
    result_without_scale = detect_stickiness(
        x, ref=5.0, L=0.0, U=10.0, mode="interior", scale=None
    )

    # Results must be identical (scale ignored)
    np.testing.assert_array_equal(result_with_scale.eps_grid, result_without_scale.eps_grid)
    np.testing.assert_array_equal(result_with_scale.mass_curve, result_without_scale.mass_curve)
```

**Validates:** Scale parameter has no effect when bounds provided.

---

#### `test_interior_unbounded_requires_scale`

```python
def test_interior_unbounded_requires_scale(self):
    """Interior mode with missing bounds must require scale parameter."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.normal(5.0, 2.0, size=1000)

    with pytest.raises(ValueError) as exc_info:
        detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale=None)

    # Error message must mention scale
    assert "scale" in str(exc_info.value).lower()
```

**Validates:** ValueError raised, error message helpful.

---

#### `test_interior_unbounded_with_float_scale`

```python
def test_interior_unbounded_with_float_scale(self):
    """Interior mode with explicit float scale must work for unbounded parameters."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.interior import InteriorResult

    rng = np.random.default_rng(42)
    x = rng.normal(5.0, 2.0, size=5000)

    result = detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale=5.0)

    assert isinstance(result, InteriorResult)
    assert isinstance(result.spike_detected, bool)
    assert isinstance(result.eps_grid, np.ndarray)
    assert len(result.eps_grid) > 0
    assert result.mass_curve.shape == result.eps_grid.shape
```

**Validates:** Works with explicit scale, returns valid result.

---

#### `test_interior_unbounded_with_std_scale`

```python
def test_interior_unbounded_with_std_scale(self):
    """scale='std' must use standard deviation for normalization."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.interior import InteriorResult

    rng = np.random.default_rng(42)
    x = rng.normal(loc=5.0, scale=2.0, size=10000)

    result = detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale="std")

    assert isinstance(result, InteriorResult)
    # For normal data centered at ref, no spike should be detected
    assert result.spike_detected is False
    # Mass curve should be valid probabilities
    assert np.all(result.mass_curve >= 0.0)
    assert np.all(result.mass_curve <= 1.0)
```

**Validates:** std scale produces valid result, no false positive on centered normal.

---

#### `test_interior_unbounded_with_iqr_scale`

```python
def test_interior_unbounded_with_iqr_scale(self):
    """scale='iqr' must use interquartile range for normalization."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.interior import InteriorResult

    rng = np.random.default_rng(42)
    x = rng.normal(loc=5.0, scale=2.0, size=10000)

    result = detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale="iqr")

    assert isinstance(result, InteriorResult)
    assert result.spike_detected is False
```

**Validates:** iqr scale produces valid result.

---

#### `test_interior_unbounded_with_range_scale`

```python
def test_interior_unbounded_with_range_scale(self):
    """scale='range' must use max-min for normalization."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.interior import InteriorResult

    rng = np.random.default_rng(42)
    x = rng.normal(loc=5.0, scale=2.0, size=10000)

    result = detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale="range")

    assert isinstance(result, InteriorResult)
    assert result.spike_detected is False
```

**Validates:** range scale produces valid result.

---

#### `test_scale_std_produces_sensible_normalization`

```python
def test_scale_std_produces_sensible_normalization(self):
    """std scale must produce z-values where ~68% are within 1 std of ref."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    # Normal distribution with known std
    x = rng.normal(loc=10.0, scale=2.0, size=10000)

    result = detect_stickiness(x, ref=10.0, L=None, U=None, mode="interior", scale="std")

    # With scale=std≈2.0, z = |x - ref| / 2.0
    # For normal(0, 2), |x - ref| / 2 has ~68% < 1.0
    # Find index closest to eps=1.0
    idx = np.argmin(np.abs(result.eps_grid - 1.0))
    mass_at_1 = result.mass_curve[idx]

    # Should be approximately 68% (within tolerance for finite sample)
    assert 0.55 < mass_at_1 < 0.80, f"Expected ~68% mass at 1 std, got {mass_at_1:.2%}"
```

**Validates:** Scale normalization produces statistically expected mass curve.

---

#### `test_lower_requires_L`

```python
def test_lower_requires_L(self):
    """mode='lower' must raise ValueError when L is None."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    with pytest.raises(ValueError) as exc_info:
        detect_stickiness(x, ref=0.0, L=None, U=10.0, mode="lower")

    assert "L" in str(exc_info.value) or "lower" in str(exc_info.value).lower()
```

**Validates:** Clear error for invalid lower mode configuration.

---

#### `test_upper_requires_U`

```python
def test_upper_requires_U(self):
    """mode='upper' must raise ValueError when U is None."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    with pytest.raises(ValueError) as exc_info:
        detect_stickiness(x, ref=10.0, L=0.0, U=None, mode="upper")

    assert "U" in str(exc_info.value) or "upper" in str(exc_info.value).lower()
```

**Validates:** Clear error for invalid upper mode configuration.

---

## 6. Validation Error Tests

### Class: `TestValidationErrors`

#### `test_invalid_mode_raises_valueerror`

```python
def test_invalid_mode_raises_valueerror(self):
    """Invalid mode must raise ValueError with mode mentioned."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    with pytest.raises(ValueError) as exc_info:
        detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="invalid")

    assert "mode" in str(exc_info.value).lower()
```

**Validates:** Error clarity for invalid mode.

---

#### `test_scale_zero_raises_error`

```python
def test_scale_zero_raises_error(self):
    """scale=0 must raise ValueError."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.normal(5.0, 2.0, size=1000)

    with pytest.raises(ValueError) as exc_info:
        detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale=0.0)

    assert "scale" in str(exc_info.value).lower() or "positive" in str(exc_info.value).lower()
```

**Validates:** Zero scale rejected.

---

#### `test_scale_negative_raises_error`

```python
def test_scale_negative_raises_error(self):
    """Negative scale must raise ValueError."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.normal(5.0, 2.0, size=1000)

    with pytest.raises(ValueError) as exc_info:
        detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale=-1.0)

    assert "scale" in str(exc_info.value).lower() or "positive" in str(exc_info.value).lower()
```

**Validates:** Negative scale rejected.

---

#### `test_invalid_scale_string_raises_error`

```python
def test_invalid_scale_string_raises_error(self):
    """Invalid scale string must raise ValueError."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.normal(5.0, 2.0, size=1000)

    with pytest.raises(ValueError) as exc_info:
        detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale="invalid")

    assert "scale" in str(exc_info.value).lower()
```

**Validates:** Unknown scale method rejected.

---

#### `test_interior_partial_bounds_requires_scale`

```python
def test_interior_partial_bounds_requires_scale(self):
    """Interior mode with only L (no U) must require scale."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    with pytest.raises(ValueError):
        detect_stickiness(x, ref=5.0, L=0.0, U=None, mode="interior", scale=None)
```

**Validates:** Partial bounds require scale.

---

## 7. Config Passthrough Tests

### Class: `TestConfigPassthrough`

#### `test_interior_config_affects_result`

```python
def test_interior_config_affects_result(self):
    """Custom InteriorConfig must affect eps_grid in result."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.config import InteriorConfig

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    default_result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="interior")

    custom_config = InteriorConfig(eps_log10_min=-6, eps_log10_max=-1, n_eps=20)
    custom_result = detect_stickiness(
        x, ref=5.0, L=0.0, U=10.0, mode="interior",
        interior_config=custom_config
    )

    # Grid length must match config
    assert len(custom_result.eps_grid) == 20
    assert len(default_result.eps_grid) != 20
    # Grid bounds must match config
    assert custom_result.eps_grid[0] == pytest.approx(10**-6, rel=0.01)
    assert custom_result.eps_grid[-1] == pytest.approx(10**-1, rel=0.01)
```

**Validates:** Config parameters propagate to result.

---

#### `test_boundary_config_affects_result`

```python
def test_boundary_config_affects_result(self):
    """Custom BoundaryConfig must affect tol_grid in result."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.config import BoundaryConfig

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    custom_config = BoundaryConfig(n_tols=25)
    result = detect_stickiness(
        x, ref=0.0, L=0.0, U=10.0, mode="lower",
        boundary_config=custom_config
    )

    assert len(result.tol_grid) == 25
```

**Validates:** Boundary config propagates.

---

#### `test_all_mode_uses_both_configs`

```python
def test_all_mode_uses_both_configs(self):
    """All mode must use both interior and boundary configs."""
    from fitqc.stickiness import detect_stickiness
    from fitqc.config import InteriorConfig, BoundaryConfig

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    interior_config = InteriorConfig(n_eps=15)
    boundary_config = BoundaryConfig(n_tols=18)

    interior_result, boundary_result = detect_stickiness(
        x, ref=5.0, L=0.0, U=10.0, mode="all",
        interior_config=interior_config,
        boundary_config=boundary_config
    )

    assert len(interior_result.eps_grid) == 15
    assert len(boundary_result.tol_grid) == 18
```

**Validates:** Both configs used in all mode.

---

## 8. Detection Correctness Tests

### Class: `TestDetectionCorrectness`

#### `test_detects_x0_spike_through_wrapper`

```python
def test_detects_x0_spike_through_wrapper(self):
    """Wrapper must detect x0 stickiness when present."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    n = 10000
    x0, L, U = 5.0, 0.0, 10.0

    # 90% uniform, 10% stuck at x0
    x = np.concatenate([
        rng.uniform(L, U, size=int(n * 0.9)),
        np.full(int(n * 0.1), x0)
    ])

    result = detect_stickiness(x, ref=x0, L=L, U=U, mode="interior")

    assert result.spike_detected is True
    assert result.eps_star is not None
    assert isinstance(result.eps_star, float)
    assert result.eps_star > 0
    assert result.spike_z_loc is not None
    assert result.spike_z_loc < 0.1  # Spike near z=0
```

**Validates:** Spike detection through wrapper works.

---

#### `test_no_false_positive_uniform_through_wrapper`

```python
def test_no_false_positive_uniform_through_wrapper(self):
    """Wrapper must not false-positive on clean uniform data."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=10000)

    result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="interior")

    assert result.spike_detected is False
```

**Validates:** No false positives.

---

#### `test_detects_lower_pileup_through_wrapper`

```python
def test_detects_lower_pileup_through_wrapper(self):
    """Wrapper must detect lower boundary pileup when present."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    n = 10000
    L, U = 0.0, 10.0

    # 90% uniform, 10% stuck at lower boundary
    x = np.concatenate([
        rng.uniform(L + 0.5, U, size=int(n * 0.9)),
        rng.uniform(L, L + 0.05, size=int(n * 0.1))
    ])

    result = detect_stickiness(x, ref=L, L=L, U=U, mode="lower")

    assert result.lower_pileup_detected is True
    assert result.t_lo_star is not None
```

**Validates:** Lower pileup detection through wrapper.

---

#### `test_detects_upper_pileup_through_wrapper`

```python
def test_detects_upper_pileup_through_wrapper(self):
    """Wrapper must detect upper boundary pileup when present."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    n = 10000
    L, U = 0.0, 10.0

    # 90% uniform, 10% stuck at upper boundary
    x = np.concatenate([
        rng.uniform(L, U - 0.5, size=int(n * 0.9)),
        rng.uniform(U - 0.05, U, size=int(n * 0.1))
    ])

    result = detect_stickiness(x, ref=U, L=L, U=U, mode="upper")

    assert result.upper_pileup_detected is True
    assert result.t_hi_star is not None
```

**Validates:** Upper pileup detection through wrapper.

---

#### `test_all_mode_detects_multiple_issues`

```python
def test_all_mode_detects_multiple_issues(self):
    """All mode must detect both x0 spike and boundary pileup when both present."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    n = 10000
    x0, L, U = 5.0, 0.0, 10.0

    # 80% uniform, 10% at x0, 10% at lower bound
    x = np.concatenate([
        rng.uniform(L + 0.5, U, size=int(n * 0.8)),
        np.full(int(n * 0.1), x0),
        rng.uniform(L, L + 0.05, size=int(n * 0.1))
    ])

    interior_result, boundary_result = detect_stickiness(x, ref=x0, L=L, U=U, mode="all")

    assert interior_result.spike_detected is True
    assert boundary_result.lower_pileup_detected is True
```

**Validates:** All mode detects multiple stickiness types.

---

## 9. Array Properties Tests

### Class: `TestArrayProperties`

#### `test_eps_grid_is_sorted_ascending`

```python
def test_eps_grid_is_sorted_ascending(self):
    """eps_grid must be sorted in ascending order."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="interior")

    assert np.all(np.diff(result.eps_grid) > 0), "eps_grid must be strictly increasing"
```

**Validates:** Grid ordering.

---

#### `test_mass_curve_values_in_zero_one`

```python
def test_mass_curve_values_in_zero_one(self):
    """Mass curve values must be probabilities in [0, 1]."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="interior")

    assert result.mass_curve.min() >= 0.0, "Mass curve has negative values"
    assert result.mass_curve.max() <= 1.0, "Mass curve exceeds 1.0"
```

**Validates:** Probability bounds.

---

#### `test_mass_curve_is_monotonic`

```python
def test_mass_curve_is_monotonic(self):
    """Mass curve P(z < eps) must be non-decreasing in eps."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="interior")

    diffs = np.diff(result.mass_curve)
    assert np.all(diffs >= -1e-10), "Mass curve must be monotonically non-decreasing"
```

**Validates:** CDF monotonicity.

---

#### `test_hist_counts_non_negative`

```python
def test_hist_counts_non_negative(self):
    """Histogram counts must all be non-negative."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="interior")

    assert np.all(result.hist_counts >= 0), "Histogram counts must be non-negative"
```

**Validates:** Histogram validity.

---

#### `test_hist_edges_length_consistent`

```python
def test_hist_edges_length_consistent(self):
    """hist_edges must have len(hist_counts) + 1 elements."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="interior")

    assert len(result.hist_edges) == len(result.hist_counts) + 1
```

**Validates:** Histogram structure.

---

#### `test_tol_grid_is_sorted_ascending`

```python
def test_tol_grid_is_sorted_ascending(self):
    """tol_grid must be sorted in ascending order."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    result = detect_stickiness(x, ref=0.0, L=0.0, U=10.0, mode="lower")

    assert np.all(np.diff(result.tol_grid) >= 0), "tol_grid must be non-decreasing"
```

**Validates:** Grid ordering for boundary.

---

## 10. Edge Cases

### Class: `TestEdgeCases`

#### `test_single_sample`

```python
def test_single_sample(self):
    """Single sample must not crash."""
    from fitqc.stickiness import detect_stickiness

    x = np.array([5.0])

    # Should not raise
    result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="interior")

    assert isinstance(result.spike_detected, bool)
```

**Validates:** Graceful handling of minimal input.

---

#### `test_all_samples_at_x0`

```python
def test_all_samples_at_x0(self):
    """All samples at x0 must detect spike."""
    from fitqc.stickiness import detect_stickiness

    x = np.full(1000, 5.0)

    result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="interior")

    assert result.spike_detected is True
```

**Validates:** Extreme spike case.

---

#### `test_ref_at_lower_bound`

```python
def test_ref_at_lower_bound(self):
    """ref=L must work for interior mode."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    # Should not raise
    result = detect_stickiness(x, ref=0.0, L=0.0, U=10.0, mode="interior")

    assert isinstance(result.spike_detected, bool)
```

**Validates:** Edge ref position.

---

#### `test_ref_at_upper_bound`

```python
def test_ref_at_upper_bound(self):
    """ref=U must work for interior mode."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=1000)

    # Should not raise
    result = detect_stickiness(x, ref=10.0, L=0.0, U=10.0, mode="interior")

    assert isinstance(result.spike_detected, bool)
```

**Validates:** Edge ref position.

---

#### `test_narrow_bounds`

```python
def test_narrow_bounds(self):
    """Very narrow bounds must not crash."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(0.0, 0.001, size=1000)

    result = detect_stickiness(x, ref=0.0005, L=0.0, U=0.001, mode="interior")

    assert isinstance(result.spike_detected, bool)
```

**Validates:** Numerical stability with small ranges.

---

#### `test_large_values`

```python
def test_large_values(self):
    """Large parameter values must not cause overflow."""
    from fitqc.stickiness import detect_stickiness

    rng = np.random.default_rng(42)
    x = rng.uniform(1e8, 1e9, size=1000)

    result = detect_stickiness(x, ref=5e8, L=1e8, U=1e9, mode="interior")

    assert isinstance(result.spike_detected, bool)
    assert np.all(np.isfinite(result.mass_curve))
```

**Validates:** Numerical stability with large values.

---

## Test Count Summary

| Category | Count |
|----------|-------|
| Module structure | 3 |
| Mode dispatch | 7 |
| Boundary mode fields | 4 |
| All mode | 2 |
| Scale parameter | 10 |
| Validation errors | 5 |
| Config passthrough | 3 |
| Detection correctness | 5 |
| Array properties | 6 |
| Edge cases | 6 |
| **Total** | **51** |
