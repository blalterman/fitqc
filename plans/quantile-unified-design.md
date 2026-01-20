# Unified Quantile-Based Stickiness Detection: Design Plan (Boundary + Interior)

**Status:** DRAFT - Updated to include interior detection
**Date:** 2026-01-19
**Goal:** Implement multi-curve quantile-based threshold detection for BOTH boundary and interior stickiness

---

## Executive Summary

**Extending the Boundary Plan to Interior:**

The original plan (`quantile-boundary-design.md`) proposed multi-curve quantile analysis for boundary detection. We now extend this to interior detection with appropriate adaptations.

**Key Insight:** Both boundary and interior use the same conceptual approach:
- **Inverse CDF multi-curve**: For each quantile q, find threshold where P(value < threshold) = q
- **Median aggregation**: Robust estimate across quantiles
- **Keep existing strengths**: Boundary keeps elbow detection; Interior keeps spike detection

**Critical Difference:**
- **Boundary**: Linear tolerance space, progressive grid
- **Interior**: Log-spaced epsilon space (already appropriate for multi-scale phenomena)

---

## Part 1: Interior-Specific Adaptations

### Current Interior Detection

From `interior.py` lines 14-25:

1. Transform to z-space: `z = |x - x0| / scale`
2. Search epsilon grid: `np.logspace(-12, -3, 50)` (log-spaced, NOT linear)
3. Compute mass curve: `P(z < eps)` for each eps
4. **Histogram spike detection**: Use `find_peaks` to detect narrow spike at z≈0
5. **Elbow detection**: Find eps_star from P(z < eps) curve

**Two outputs needed:**
- `spike_detected`: Boolean (from histogram analysis)
- `eps_star`: Threshold width (from elbow in mass curve)

### Why Interior Needs Different Grid Strategy

**Boundary uses progressive linear grid** because:
- Tolerance is a linear distance [0, 0.05]
- Stickiness tends to be in [0, 0.01] (tight)
- Progressive spacing concentrates resolution where needed

**Interior already uses log-spaced grid** because:
- Epsilon spans 9 orders of magnitude (10^-12 to 10^-3)
- Stickiness could be at machine precision (10^-12) or broader (10^-3)
- Log-spacing ensures each decade is sampled evenly

**Recommendation:** Keep log-spacing for interior, but consider **progressive log** if empirical data shows most spikes are in specific decade.

### Interior Quantile Analysis Strategy

**Option I-1: Standard Inverse CDF (Recommended)**

Same as boundary, but in epsilon-space:

```python
quantile_grid = (0.001, 0.005, 0.01, 0.02, 0.05, 0.10)
eps_grid = np.logspace(-12, -3, 50)

# Compute mass curve
z_mass_curve = np.array([np.mean(z_sorted < eps) for eps in eps_grid])

# For each quantile, find epsilon where mass = quantile
eps_at_quantile = np.zeros(len(quantile_grid))
for i, q in enumerate(quantile_grid):
    # Interpolate in log-space for eps (since grid is log-spaced)
    eps_at_quantile[i] = np.exp(np.interp(q, z_mass_curve, np.log(eps_grid)))

# Detect elbow in (quantile, epsilon) relationship
elbow_q = select_elbow(quantile_grid, eps_at_quantile,
                       curve="concave", direction="increasing")

# Aggregate across quantiles
eps_star = np.median([eps_i for eps_i in eps_at_quantile if eps_i is not None])
```

**Key differences from boundary:**
- Interpolate in LOG-SPACE for epsilon (because grid is log-spaced)
- Elbow detection might use `log_x=False` (quantile is linear) but `log_y=True` (epsilon is log)

**Spike detection stays independent:**
```python
# Histogram spike detection (unchanged)
hist, bin_edges = np.histogram(z_sorted, bins=n_bins)
peaks, properties = find_peaks(hist,
                               prominence=spike_prominence_min,
                               width=(0, spike_width_max))

spike_detected = len(peaks) > 0 and any(
    bin_edges[p] <= spike_location_max for p in peaks
)

# Quantile analysis only affects eps_star, not spike_detected
```

---

## Part 2: Unified Implementation Strategy

### Shared Components (Both Boundary and Interior)

**1. Median Aggregation Function** (can be shared):

```python
def _aggregate_elbows_median(
    elbows: list[float | None],
    min_agreement_frac: float = 0.5
) -> float | None:
    """Aggregate multiple elbow estimates via median.

    Works for both boundary tolerances and interior epsilons.
    """
    valid_elbows = [e for e in elbows if e is not None]

    if len(valid_elbows) < min_agreement_frac * len(elbows):
        return None  # Insufficient agreement

    return float(np.median(valid_elbows))
```

**2. Config Updates:**

```python
# In config.py

@dataclass
class InteriorConfig:
    # Existing fields...
    eps_log10_min: float = -12
    eps_log10_max: float = -3
    n_eps: int = 50

    # NEW: Quantile analysis support
    use_quantile_analysis: bool = False  # Opt-in initially
    quantile_grid: tuple[float, ...] = field(
        default_factory=lambda: (0.001, 0.005, 0.01, 0.02, 0.05, 0.10)
    )
    min_quantile_agreement: float = 0.5  # NEW: Configurable threshold

    # Existing spike detection params...
    spike_prominence_min: float = 10.0
    spike_width_max: float = 15.0
    spike_location_max: float = 0.1


@dataclass
class BoundaryConfig:
    # Existing fields...
    tol_min: float = 0.0
    tol_max: float = 0.05
    n_tols: int = 41

    # NEW: Grid mode selection
    grid_mode: str = "uniform"  # "uniform" or "progressive"

    # NEW: Quantile analysis (currently unused)
    use_quantile_analysis: bool = False  # Opt-in initially
    quantile_grid: tuple[float, ...] = field(
        default_factory=lambda: (0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10)
    )
    min_quantile_agreement: float = 0.5  # NEW: Configurable threshold
```

### Boundary-Specific Implementation

From original plan (`quantile-boundary-design.md`):

1. **Progressive grid** (Phase 1):
   ```python
   def _build_tolerance_grid(config: BoundaryConfig) -> NDArray[np.floating]:
       if config.grid_mode == "uniform":
           return np.linspace(config.tol_min, config.tol_max, config.n_tols)
       elif config.grid_mode == "progressive":
           # Denser near 0, coarser farther out
           return np.concatenate([
               np.linspace(0.0000, 0.0010, 11),
               np.linspace(0.0010, 0.0050, 17)[1:],
               np.linspace(0.0050, 0.0200, 13)[1:],
               np.linspace(0.0200, 0.0500, 7)[1:],
           ])
   ```

2. **Quantile curve computation** (Phase 2):
   ```python
   def _compute_quantile_curves_boundary(
       u_sorted: NDArray[np.floating],
       tol_grid: NDArray[np.floating],
       quantile_grid: NDArray[np.floating],
   ) -> tuple[NDArray[np.floating], list[float | None]]:
       """Compute tolerance at each quantile via inverse CDF."""
       mass_curve = np.array([tail_mass(u_sorted, tol) for tol in tol_grid])
       tol_at_quantile = np.interp(quantile_grid, mass_curve, tol_grid)

       # Detect elbow for each quantile (TODO: or detect in quantile space?)
       # Details TBD based on POC learnings

       return tol_at_quantile, elbows_per_quantile
   ```

3. **Integration** (Phase 4):
   ```python
   # In run_boundary_qc
   if config.use_quantile_analysis:
       tol_at_quantile, elbows = _compute_quantile_curves_boundary(
           u_sorted, tol_grid, config.quantile_grid
       )
       t_lo_star = _aggregate_elbows_median(elbows, config.min_quantile_agreement)
   else:
       # Original single-curve method
       t_lo_star = select_elbow(tol_grid, lower_mass_curve, ...)
   ```

### Interior-Specific Implementation

**1. Epsilon grid** (already log-spaced, no change needed):
   ```python
   def _build_epsilon_grid(config: InteriorConfig) -> NDArray[np.floating]:
       """Build log-spaced epsilon grid (unchanged from current)."""
       return np.logspace(config.eps_log10_min, config.eps_log10_max, config.n_eps)
   ```

**2. Quantile curve computation** (NEW):
   ```python
   def _compute_quantile_curves_interior(
       z_sorted: NDArray[np.floating],
       eps_grid: NDArray[np.floating],
       quantile_grid: NDArray[np.floating],
   ) -> tuple[NDArray[np.floating], list[float | None]]:
       """Compute epsilon at each quantile via inverse CDF in log-space."""

       # Mass curve in epsilon space
       z_mass_curve = np.array([np.mean(z_sorted < eps) for eps in eps_grid])

       # Interpolate in LOG-SPACE for epsilon (grid is log-spaced)
       log_eps_grid = np.log(eps_grid)
       log_eps_at_quantile = np.interp(quantile_grid, z_mass_curve, log_eps_grid)
       eps_at_quantile = np.exp(log_eps_at_quantile)

       # Detect elbows (TBD based on POC learnings)
       elbows_per_quantile = [...]  # Implementation TBD

       return eps_at_quantile, elbows_per_quantile
   ```

**3. Integration** (NEW):
   ```python
   # In run_interior_qc

   # Spike detection (UNCHANGED - orthogonal to threshold finding)
   hist, bin_edges = np.histogram(z_sorted, bins=config.n_bins)
   peaks, properties = find_peaks(hist,
                                  prominence=config.spike_prominence_min,
                                  width=(0, config.spike_width_max))
   spike_detected = _check_spike_at_x0(peaks, bin_edges, config.spike_location_max)

   # Threshold finding (NEW quantile-based option)
   if config.use_quantile_analysis:
       eps_at_quantile, elbows = _compute_quantile_curves_interior(
           z_sorted, eps_grid, config.quantile_grid
       )
       eps_star = _aggregate_elbows_median(elbows, config.min_quantile_agreement)
   else:
       # Original single-curve method
       eps_star = select_elbow(eps_grid, z_mass_curve, curve="concave",
                              direction="increasing", log_x=True)

   # BOTH outputs are returned (spike_detected AND eps_star)
   return InteriorResult(spike_detected=spike_detected, eps_star=eps_star, ...)
   ```

---

## Part 3: Updated Test Strategy

### Test Suite Structure (Unified)

```
tests/test_boundary_quantile.py   (14 tests from original plan)
tests/test_interior_quantile.py   (12 tests, adapted for interior)
tests/test_quantile_shared.py     (3 tests for shared utilities)
```

### Interior Test Groups

**Test Group I-1: Quantile Curve Computation (Interior)**

Similar to boundary but in epsilon/z-space:

#### Test I-1.1: `test_quantile_curve_uniform_z_is_linear`
```python
def test_quantile_curve_uniform_z_is_linear():
    """For uniform z-distribution, quantile curve should be linear in LOG-space."""
    # Generate uniform z in [10^-12, 10^-3]
    z = np.random.uniform(1e-12, 1e-3, size=10000)
    z_sorted = np.sort(z)

    quantile_grid = np.array([0.01, 0.05, 0.10, 0.20])
    eps_grid = np.logspace(-12, -3, 100)

    z_mass_curve = np.array([np.mean(z_sorted < eps) for eps in eps_grid])

    # Interpolate in log-space
    log_eps_at_quantile = np.interp(quantile_grid, z_mass_curve, np.log(eps_grid))
    eps_at_quantile = np.exp(log_eps_at_quantile)

    # For uniform z, eps should be linear in quantile (in log-space)
    from scipy.stats import linregress
    slope, intercept, r_value, _, _ = linregress(quantile_grid, np.log(eps_at_quantile))

    assert r_value**2 > 0.98, f"Should be linear in log-space, got R²={r_value**2}"
```

#### Test I-1.2: `test_quantile_curve_tight_spike_shows_elbow`
```python
def test_quantile_curve_tight_spike_shows_elbow():
    """For tight spike at x0, quantile curve should show clear elbow."""
    # Generate spike: 5% of samples within eps=1e-6 of x0
    z_spike = np.random.uniform(0, 1e-6, size=500)  # 5% in spike
    z_bulk = np.random.uniform(1e-6, 1e-3, size=9500)  # 95% elsewhere
    z = np.concatenate([z_spike, z_bulk])
    z_sorted = np.sort(z)

    quantile_grid = np.array([0.01, 0.02, 0.05, 0.10, 0.15, 0.20])
    eps_grid = np.logspace(-12, -3, 100)

    eps_at_quantile, _ = _compute_quantile_curves_interior(z_sorted, eps_grid, quantile_grid)

    # For q <= 0.05 (within spike), eps should be small
    assert eps_at_quantile[2] < 1e-5, "Spike region should need tiny epsilon"

    # For q > 0.05 (beyond spike), eps should jump
    assert eps_at_quantile[3] > 1e-5, "Beyond spike, epsilon should be larger"
```

**Test Group I-2: Spike Detection Independence**

Critical: Ensure quantile analysis doesn't break spike detection.

#### Test I-2.1: `test_spike_detection_unchanged_by_quantile_analysis`
```python
def test_spike_detection_unchanged_by_quantile_analysis():
    """Spike detection should give same result regardless of quantile analysis setting."""
    # Generate data with tight spike
    x_spike = generate_with_x0_spike(n=10000, x0=0.5, L=0.0, U=1.0,
                                      spike_frac=0.05, spike_width=1e-6, seed=42)

    config_single = InteriorConfig(use_quantile_analysis=False)
    config_multi = InteriorConfig(use_quantile_analysis=True)

    result_single = run_interior_qc(x_spike, x0=0.5, L=0.0, U=1.0, config=config_single)
    result_multi = run_interior_qc(x_spike, x0=0.5, L=0.0, U=1.0, config=config_multi)

    # Spike detection should be IDENTICAL
    assert result_single.spike_detected == result_multi.spike_detected, \
        "Spike detection must be independent of threshold method"

    # eps_star MAY differ (that's the point of multi-curve)
    # But both should detect the spike exists
    assert result_single.spike_detected is True
    assert result_multi.spike_detected is True
```

#### Test I-2.2: `test_broad_distribution_no_spike_detected`
```python
def test_broad_distribution_no_spike_detected():
    """Broad distribution centered at x0 should NOT trigger spike detection."""
    # Broad normal at x0 (natural clustering, not a spike)
    x = np.random.normal(loc=0.5, scale=0.15, size=10000)
    x = np.clip(x, 0.0, 1.0)

    config = InteriorConfig(use_quantile_analysis=True)
    result = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config)

    # Should NOT detect spike (histogram will be broad, not narrow)
    assert not result.spike_detected, \
        "Broad distribution should not trigger spike detection (width criterion)"

    # eps_star might be non-None (there's an elbow), but spike_detected should be False
```

**Test Group I-3: Integration Tests (Interior)**

#### Test I-3.1: `test_multi_curve_detects_tight_spike_better`
```python
def test_multi_curve_detects_tight_spike_better():
    """Multi-curve should give more accurate eps_star for tight spikes."""
    # Very tight spike: 3% at machine precision
    x = generate_with_x0_spike(n=10000, x0=0.5, L=0.0, U=1.0,
                                spike_frac=0.03, spike_width=1e-10, seed=42)

    config_old = InteriorConfig(use_quantile_analysis=False)
    config_new = InteriorConfig(use_quantile_analysis=True,
                                quantile_grid=(0.005, 0.01, 0.02, 0.03, 0.05))

    result_old = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config_old)
    result_new = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config_new)

    # Both should detect spike
    assert result_old.spike_detected and result_new.spike_detected

    # New method should give more accurate eps_star (closer to true 1e-10)
    assert result_new.eps_star is not None
    # We expect eps_star to be small (spike is tight)
    assert result_new.eps_star < 1e-6, \
        f"Should detect tight spike, got eps_star={result_new.eps_star}"
```

**Test Group I-4: Shared Utilities**

#### Test S-1: `test_aggregate_elbows_median_works_for_both`
```python
def test_aggregate_elbows_median_works_for_both():
    """Median aggregation should work for both boundary tols and interior eps."""
    # Boundary tolerances (linear scale)
    tol_elbows = [0.010, 0.011, 0.009, 0.010, 0.011]
    tol_result = _aggregate_elbows_median(tol_elbows)
    assert tol_result == pytest.approx(0.010, abs=0.001)

    # Interior epsilons (log scale, but aggregation is same)
    eps_elbows = [1e-6, 1.2e-6, 0.9e-6, 1.1e-6, 1.0e-6]
    eps_result = _aggregate_elbows_median(eps_elbows)
    assert eps_result == pytest.approx(1e-6, rel=0.1)
```

---

## Part 4: Implementation Phases (Updated)

### Phase 1: Infrastructure (Both)

**Boundary:**
- Add `grid_mode` to BoundaryConfig
- Implement `_build_tolerance_grid(config)`
- Tests: Progressive grid properties (2 tests)

**Interior:**
- Add `quantile_grid`, `use_quantile_analysis` to InteriorConfig
- Epsilon grid unchanged (already log-spaced)
- Tests: Config validation (1 test)

**Shared:**
- Implement `_aggregate_elbows_median(...)`
- Tests: Aggregation logic (2 tests)

**Estimated Time:** 3 hours

---

### Phase 2: Quantile Curve Computation (Both)

**Boundary:**
- Implement `_compute_quantile_curves_boundary(...)`
- Tests: Quantile curve properties for boundary (3 tests)

**Interior:**
- Implement `_compute_quantile_curves_interior(...)` (with log-space interpolation)
- Tests: Quantile curve properties for interior (3 tests)

**Estimated Time:** 4 hours

---

### Phase 3: Integration (Both)

**Boundary:**
- Update `run_boundary_qc` to use multi-curve when enabled
- Add `quantile_elbows` to BoundaryResult (optional field)
- Tests: End-to-end boundary detection (3 tests)

**Interior:**
- Update `run_interior_qc` to use multi-curve when enabled
- Keep spike detection independent
- Add `quantile_elbows` to InteriorResult (optional field)
- Tests: End-to-end interior detection (3 tests)
- Tests: Spike detection independence (2 tests)

**Estimated Time:** 5 hours

---

### Phase 4: Backward Compatibility & Edge Cases (Both)

**Both:**
- Tests: Single-curve mode still works (2 tests: boundary + interior)
- Tests: Edge cases (empty, single value, all at boundary/x0) (6 tests: 3×2)

**Estimated Time:** 3 hours

---

### Phase 5: Documentation

**Updates:**
- `config.py` docstrings for new fields
- `boundary.py` docstrings for multi-curve
- `interior.py` docstrings for multi-curve
- Examples showing both use cases
- Changelog entry

**Estimated Time:** 2 hours

---

### **Total Estimated Time:** ~17 hours (vs 15 hours for boundary-only)

---

## Part 5: Parallel Subagent Execution Strategy

To protect context and accelerate development, we'll use 4 parallel subagents:

### Agent 1: Boundary Implementation
**Tasks:**
- Phase 1 (Boundary): Progressive grid implementation + tests
- Phase 2 (Boundary): Quantile curve computation + tests
- Phase 3 (Boundary): Integration + tests

**Deliverable:**
- `src/fitqc/boundary.py` (updated)
- `tests/test_boundary_quantile.py` (new, 14 tests)

**Estimated Time:** ~6 hours

---

### Agent 2: Interior Implementation
**Tasks:**
- Phase 1 (Interior): Config updates + tests
- Phase 2 (Interior): Quantile curve computation (log-space) + tests
- Phase 3 (Interior): Integration (keeping spike detection separate) + tests

**Deliverable:**
- `src/fitqc/interior.py` (updated)
- `tests/test_interior_quantile.py` (new, 10 tests)

**Estimated Time:** ~6 hours

---

### Agent 3: Shared Utilities
**Tasks:**
- Phase 1 (Shared): Median aggregation + tests
- Phase 4: Backward compatibility tests (both boundary + interior)
- Phase 4: Edge case tests (both boundary + interior)

**Deliverable:**
- `src/fitqc/_quantile_utils.py` (new, shared functions)
- `tests/test_quantile_shared.py` (new, 3 tests)
- Backward compat tests added to existing test files

**Estimated Time:** ~4 hours

---

### Agent 4: Config Updates
**Tasks:**
- Phase 1: Update `BoundaryConfig` and `InteriorConfig`
- Phase 5: Documentation updates (docstrings, examples, changelog)
- Integration: Ensure all agents' code works together

**Deliverable:**
- `src/fitqc/config.py` (updated)
- Updated docstrings across all files
- `CHANGELOG.md` entry
- Example scripts demonstrating multi-curve

**Estimated Time:** ~3 hours

---

### Main Agent: Aggregation & Validation
**Tasks:**
- Launch 4 subagents in parallel
- Aggregate results from all agents
- Run full test suite to ensure integration
- Fix any cross-agent integration issues
- Final commit and push

**Estimated Time:** ~2 hours

---

## Part 6: Critical Design Questions

### Q1: For interior, should we add "progressive log" grid option?

**Current:** Log-spaced covers 10^-12 to 10^-3 evenly across decades

**Progressive log option:**
```python
# If empirical data shows most spikes in [10^-8, 10^-6], could do:
eps_grid = np.concatenate([
    np.logspace(-12, -8, 10),   # Coarse for ultra-tight
    np.logspace(-8, -6, 25),    # Dense in common region
    np.logspace(-6, -3, 15),    # Coarse for broad
])
```

**Recommendation:** Start with uniform log-spacing (current). Add progressive log only if 6M+ dataset shows specific concentration pattern.

---

### Q2: Should spike detection and quantile analysis share any logic?

**No.** They're orthogonal:
- **Spike detection**: Binary classifier (is there a spike?)
- **Quantile analysis**: Threshold estimator (how wide is it?)

Keep them completely separate in code.

---

### Q3: Should we expose quantile_elbows in results?

**Yes** (same as boundary plan):
- Add `quantile_elbows: dict[float, float | None] | None` to both BoundaryResult and InteriorResult
- Helps with debugging and transparency
- Users can ignore if not needed

---

## Part 7: Success Criteria

### Boundary Detection:
- ✓ Progressive grid has better resolution in [0, 0.01] than uniform
- ✓ Multi-curve detects tight pileups (0.3% range) with <50% error
- ✓ No increase in false positives on uniform data
- ✓ Backward compatible (single-curve still works)

### Interior Detection:
- ✓ Multi-curve gives more accurate eps_star for tight spikes (1e-10 to 1e-8)
- ✓ Spike detection unchanged (same binary classification)
- ✓ No false spikes on broad distributions (width criterion still works)
- ✓ Backward compatible (single-curve still works)

### Shared:
- ✓ Median aggregation robust to outliers (tested)
- ✓ All edge cases handled (empty, single value, extremes)

---

## Part 8: Validation Against Real Data

After implementation, you'll validate on the 6M+ dataset:

**Validation checklist:**
1. Run both single-curve and multi-curve on full dataset
2. Compare eps_star/t_star distributions
3. Check if multi-curve improves accuracy for known problematic cases
4. Verify no regressions on cases that already work
5. Decide whether to change defaults based on results

**We implement here; you validate externally.**

---

## Appendix: Key Differences Summary

| Aspect | Boundary | Interior |
|--------|----------|----------|
| **Space** | u ∈ [0,1] linear | z ∈ [10^-12, 10^-3] log |
| **Grid** | Progressive linear | Log-spaced (uniform in decades) |
| **Threshold** | Tolerance (linear) | Epsilon (log) |
| **Detection** | Elbow only | Spike (binary) + Elbow (threshold) |
| **Quantile curve** | Interpolate in linear space | Interpolate in log-space |
| **Aggregation** | Median of elbows | Median of elbows (same function) |
| **Independence** | N/A | Spike detection independent of quantile |

---

**READY TO IMPLEMENT?**

Should I proceed with launching 4 parallel subagents to implement this unified plan?
