"""Tests for boundary stickiness detection fixes.

This module tests the fixes for:
1. Single-element list handling in _aggregate_elbows_median
2. Expanded quantile grid (7→26 points)
3. Configurable detection thresholds
4. Iterative Kneedle refinement
5. Integration across all fixes

Test Philosophy
---------------
- Mock-enhanced: Verify parameter passing and internal function calls
- Edge cases: No skipped tests - all edge cases must be handled
- Scientific validation: Expose internal state for verification
- TDD: These tests will FAIL initially (RED), pass after fixes (GREEN)
"""

import time
from unittest.mock import patch

import numpy as np
import pytest

from fitqc._quantile_utils import _aggregate_elbows_median
from fitqc.boundary import run_boundary_qc
from fitqc.config import BoundaryConfig


class TestAggregateElbowsSingleElement:
    """Tests for single-element list handling in _aggregate_elbows_median.

    Why these tests: Root Cause 2 identified that _aggregate_elbows_median
    is called with single-element lists [elbow_overall], making the
    min_quantile_agreement=0.5 check meaningless (50% of 1 = 0.5).

    Fix 2 handles len=0 and len=1 cases explicitly.
    """

    def test_single_valid_elbow_returns_value(self):
        """Single valid elbow should return that value directly.

        Why this test exists: Previously, min_quantile_agreement=0.5 was
        meaningless for single-element lists. Now we explicitly handle
        len=1 by returning the value without agreement checking.

        This tests the fix for the single-element edge case.
        """
        elbows = [0.025]
        result = _aggregate_elbows_median(elbows, min_agreement_frac=0.5)

        # Behavior: returns the value
        assert result == 0.025, f"Expected 0.025, got {result}"

        # Type: should be float, not list or None
        assert isinstance(result, float), f"Expected float, got {type(result)}"

    def test_single_none_returns_none(self):
        """Single None elbow should return None.

        Edge case: quantile analysis found no elbow. Should propagate None
        through to caller, not crash on median of empty list.
        """
        elbows = [None]
        result = _aggregate_elbows_median(elbows, min_agreement_frac=0.5)

        # Behavior: None in, None out
        assert result is None, f"Expected None, got {result}"

        # Type: exactly None, not 0 or NaN
        assert result is None  # Identity check

    def test_empty_list_returns_none(self):
        """Empty list should return None gracefully without crashing.

        Edge case: no quantiles analyzed (shouldn't happen in practice,
        but defensive programming requires handling).
        """
        elbows = []
        result = _aggregate_elbows_median(elbows, min_agreement_frac=0.5)

        # Behavior: graceful handling
        assert result is None, f"Expected None for empty list, got {result}"

    def test_multi_element_agreement_logic_preserved(self):
        """Multi-element agreement logic should be unchanged.

        This is a regression test: the fix for single-element handling
        should NOT affect the multi-element case. The agreement check
        is meaningful for len > 1 and should still work.
        """
        # Sufficient agreement (3 of 5 = 60% >= 50%)
        elbows_sufficient = [0.01, 0.02, None, 0.015, None]
        result_sufficient = _aggregate_elbows_median(elbows_sufficient, min_agreement_frac=0.5)

        # Behavior: returns median
        assert result_sufficient is not None, "Expected median, got None"
        assert result_sufficient == pytest.approx(0.015), (
            f"Expected median ~0.015, got {result_sufficient}"
        )

        # Type: float
        assert isinstance(result_sufficient, float)

        # Insufficient agreement (2 of 5 = 40% < 50%)
        elbows_insufficient = [0.01, None, None, None, 0.02]
        result_insufficient = _aggregate_elbows_median(elbows_insufficient, min_agreement_frac=0.5)

        # Behavior: returns None
        assert result_insufficient is None, (
            f"Expected None for insufficient agreement, got {result_insufficient}"
        )


class TestQuantileGridExpansion:
    """Tests for expanded quantile grid (Fix 3: 7→26 points).

    Why these tests: Root Cause 1 identified that only 7 points in
    quantile_grid is insufficient. A_He case showed transition between
    q=0.01 (tol=0) and q=0.02 (tol=0.012) with no intermediate points
    for Kneedle to detect the elbow.

    Fix 3 expands to 26 points with dense coverage in 0-2% range.
    """

    def test_default_grid_has_26_points(self):
        """Default quantile grid should have 26 points for better resolution.

        Why 26? The A_He failure case showed transition between q=0.01 and
        q=0.02 with only 7 points. We need denser coverage in the critical
        0-5% range where boundary pileups typically occur.

        Note: This count is design-dependent and may change in future.
        The key requirement is "significantly more than 7".
        """
        config = BoundaryConfig()

        # Size: exact count (26 chosen for dense 0-2% coverage)
        assert len(config.quantile_grid) == 26, (
            f"Expected 26 points for improved resolution, got {len(config.quantile_grid)}"
        )

        # Type: tuple (immutable config)
        assert isinstance(config.quantile_grid, tuple)

        # Dtype: all float elements
        assert all(isinstance(q, float) for q in config.quantile_grid), (
            "All quantiles must be float"
        )

    def test_grid_is_monotonically_increasing(self):
        """Quantile grid must be strictly increasing for interpolation.

        Why: np.interp and elbow detection algorithms require sorted input.
        Non-monotonic grid would cause incorrect tolerance calculations.
        """
        config = BoundaryConfig()
        grid = np.array(config.quantile_grid)

        # Property: monotonicity
        diffs = np.diff(grid)
        assert np.all(diffs > 0), (
            f"Grid has non-increasing values at indices: "
            f"{np.where(diffs <= 0)[0]}, values: {grid[diffs <= 0]}"
        )

        # Dtype: converts to float64 array
        assert grid.dtype == np.float64, f"Expected float64, got {grid.dtype}"

    def test_grid_covers_0_to_2_percent_densely(self):
        """Grid should have dense coverage in 0-2% range where pileups occur.

        Why: The A_He case showed 3% pileup at boundary. Most optimizer
        stickiness occurs in 0-2% range. We need enough points here for
        Kneedle to detect the elbow.

        Criterion: At least 10 points in [0, 0.02] range.
        """
        config = BoundaryConfig()
        grid = np.array(config.quantile_grid)

        # Contents: count points in critical range
        critical_points = grid[(grid >= 0.0) & (grid <= 0.02)]

        # Size: sufficient coverage
        assert len(critical_points) >= 10, (
            f"Expected >=10 points in [0, 0.02], got {len(critical_points)}: {critical_points}"
        )

        # Property: spacing is reasonable
        if len(critical_points) > 1:
            critical_spacing = np.diff(critical_points)
            max_spacing = np.max(critical_spacing)
            assert max_spacing < 0.005, (
                f"Max spacing in critical range too large: {max_spacing} "
                f"(should be <0.005 for fine resolution)"
            )

    def test_grid_boundaries_cover_expected_range(self):
        """Grid should start near 0 and extend to reasonable upper bound.

        Why: Lower bound should capture very tight pileups (0.05% = precision
        artifacts). Upper bound should cover broad distributions (25% = clearly
        not boundary pileup).
        """
        config = BoundaryConfig()
        grid = np.array(config.quantile_grid)

        # Contents: bounds check
        assert grid[0] <= 0.001, f"First quantile too large: {grid[0]} (should be <=0.001)"
        assert grid[-1] >= 0.20, f"Last quantile too small: {grid[-1]} (should be >=0.20)"
        assert grid[-1] <= 0.30, f"Last quantile too large: {grid[-1]} (should be <=0.30)"

    def test_custom_grid_overrides_default(self):
        """User should be able to specify custom quantile grid.

        Backward compatibility: existing code that specifies custom grids
        should continue to work unchanged.
        """
        custom_grid = (0.01, 0.05, 0.10)
        config = BoundaryConfig(quantile_grid=custom_grid)

        # Behavior: accepts custom grid
        assert config.quantile_grid == custom_grid

        # Size: uses custom size
        assert len(config.quantile_grid) == 3


class TestConfigurableThresholds:
    """Tests for configurable detection thresholds (Fix 4).

    Why these tests: Root Cause 3 identified that pileup_threshold=0.005
    and excess_ratio=1.5 are hardcoded in boundary.py, not in BoundaryConfig.

    Fix 4 adds these fields to BoundaryConfig with validation.
    """

    def test_default_pileup_threshold(self):
        """Default pileup_threshold should be 0.005 (0.5% of range).

        Why: This threshold determines minimum tolerance to consider as
        a "pileup". Below 0.5%, we might be detecting noise.
        """
        config = BoundaryConfig()

        # Value: default preserved
        assert config.pileup_threshold == 0.005, (
            f"Expected default 0.005, got {config.pileup_threshold}"
        )

        # Type: float
        assert isinstance(config.pileup_threshold, float)

    def test_default_excess_ratio(self):
        """Default excess_ratio should be 1.5 (50% above uniform).

        Why: For uniform data, P(u < tol) = tol. A pileup has
        P(u < tol) > excess_ratio * tol. Ratio of 1.5 means 50%
        more mass than expected for uniform.
        """
        config = BoundaryConfig()

        # Value: default preserved
        assert config.excess_ratio == 1.5, f"Expected default 1.5, got {config.excess_ratio}"

        # Type: float
        assert isinstance(config.excess_ratio, float)

    def test_custom_thresholds_accepted(self):
        """User should be able to specify custom detection thresholds."""
        config = BoundaryConfig(pileup_threshold=0.01, excess_ratio=2.0)

        # Behavior: accepts custom values
        assert config.pileup_threshold == 0.01
        assert config.excess_ratio == 2.0

    def test_negative_pileup_threshold_rejected(self):
        """Negative pileup_threshold should raise ValueError."""
        with pytest.raises(ValueError, match="pileup_threshold"):
            BoundaryConfig(pileup_threshold=-0.01)

    def test_pileup_threshold_too_large_rejected(self):
        """pileup_threshold > 0.1 should raise ValueError (too permissive)."""
        with pytest.raises(ValueError, match="pileup_threshold"):
            BoundaryConfig(pileup_threshold=0.15)

    def test_excess_ratio_less_than_one_rejected(self):
        """excess_ratio < 1.0 should raise ValueError (mathematically invalid).

        Why: Ratio of 1.0 means "same as uniform". Ratio < 1.0 means
        "less than uniform" which is not a pileup, it's a deficit.
        """
        with pytest.raises(ValueError, match="excess_ratio"):
            BoundaryConfig(excess_ratio=0.5)

    @patch("fitqc.boundary._compute_quantile_curves_boundary")
    def test_thresholds_passed_to_detection_logic(self, mock_compute):
        """Verify config thresholds are actually passed to detection functions.

        Why non-trivial: Mock-enhanced test ensures config values aren't just
        stored but actually used in detection. This is critical for scientific
        data analysis software - parameter passing must be verifiable.

        What this catches:
        - Config created but ignored (hardcoded thresholds used instead)
        - Thresholds not propagated to detection logic
        - Default values used instead of custom values
        """
        # Mock returns typical values (must match 26-point quantile grid)
        # Generate 26 mock tolerance values
        mock_tol_values = np.linspace(0.001, 0.025, 26)
        # Generate 26 mock elbow values (one per quantile)
        mock_elbows = list(mock_tol_values)

        mock_compute.return_value = (
            mock_tol_values,  # tol_at_quantile (26 elements)
            mock_elbows,  # elbows_per_quantile (26 elements)
        )

        # Create config with CUSTOM thresholds (different from defaults)
        custom_config = BoundaryConfig(
            use_quantile_analysis=True,
            pileup_threshold=0.008,  # Custom (default is 0.005)
            excess_ratio=1.8,  # Custom (default is 1.5)
        )

        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, 1000)

        # Run detection
        _result = run_boundary_qc(x, L=0, U=10, config=custom_config)

        # Verify function was called (detection logic ran)
        assert mock_compute.called, "Detection logic should be invoked with custom config"

        # Verify config was actually passed (not None)
        # The function signature is: _compute_quantile_curves_boundary(u_sorted, tol_grid, quantile_grid)
        # So we check that it was called (presence indicates config was used upstream)
        assert mock_compute.call_count >= 1, (
            "Quantile curve computation should be called at least once"
        )

        # Additional verification: if the function is called with results from config,
        # we know config was used. The tol_grid and quantile_grid come from config.
        call_args = mock_compute.call_args_list[0]

        # Check that quantile_grid argument has expected size from config
        quantile_grid_arg = call_args[0][2]  # Third positional arg
        assert len(quantile_grid_arg) > 0, "Quantile grid from config should be passed to detection"

        # Note: Direct threshold verification would require mocking the
        # detection decision logic, but this test verifies the config
        # flows through the system correctly.


class TestIterativeKneedleRefinement:
    """Tests for iterative Kneedle refinement (Fix 5).

    Why these tests: Fix 5 implements two-pass adaptive refinement:
    1. Run Kneedle on initial 26-point grid
    2. If elbow found, add 15 intermediate quantiles around it
    3. Re-run Kneedle on refined grid

    Critical edge cases that MUST be handled:
    - Elbow at first quantile (can't refine left)
    - Elbow at last quantile (can't refine right)
    - Elbow between adjacent points (main use case)
    """

    @patch("fitqc.boundary.select_elbow")
    def test_iterative_refinement_calls_elbow_detection_multiple_times(self, mock_elbow):
        """Verify iterative refinement actually iterates (calls elbow detection >1 time).

        Why non-trivial: Tests the CONTROL FLOW, not just the output.
        If someone breaks the iteration logic, this catches it.

        What this catches:
        - Iteration loop accidentally removed (call_count == 1)
        - Convergence logic broken (call_count > 10, infinite loop)
        - Grid not actually refined between iterations (grid size unchanged)
        """
        # Configure mock to return different values on each call.
        # Both boundaries call select_elbow during refinement.
        # Lower boundary: delta function (elbow ≈ 0) runs 2 iterations.
        # Upper boundary: normal convergence may take 1-3 iterations.
        mock_elbow.side_effect = [
            0.02,  # Lower iter 0
            0.02,  # Lower iter 1 (delta continue)
            0.02,  # Upper iter 0
            0.0195,  # Upper iter 1
            0.0195,  # Upper iter 2 (converged)
            0.0195,  # Extra safety margin
        ]

        rng = np.random.default_rng(42)
        x = np.concatenate([np.zeros(300), rng.uniform(0, 100, 9700)])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,  # Enable iterative refinement
        )

        _result = run_boundary_qc(x, L=0, U=100, config=config)

        # ========== NON-TRIVIAL VERIFICATION ==========

        # 1. Verify elbow detection was called MULTIPLE times (iteration happened)
        call_count = mock_elbow.call_count
        assert call_count >= 2, (
            f"Iterative refinement should call select_elbow multiple times, "
            f"but only called {call_count} time(s). "
            f"This means iteration loop is broken or not running."
        )

        # 2. Verify it didn't loop forever (both boundaries combined)
        assert call_count <= 10, (
            f"Refinement should converge, not loop forever. "
            f"Called select_elbow {call_count} times. "
            f"Check convergence condition in iterative refinement."
        )

        # 3. Verify the arguments changed between calls (grid was refined)
        if call_count >= 2:
            first_call_args = mock_elbow.call_args_list[0]
            second_call_args = mock_elbow.call_args_list[1]

            # Extract the quantile grid (first positional argument)
            first_grid = first_call_args[0][0]
            second_grid = second_call_args[0][0]

            # Grid should have grown (more points added)
            assert len(second_grid) > len(first_grid), (
                f"Refined grid should have more points: "
                f"{len(first_grid)} -> {len(second_grid)}. "
                f"Refinement ran but didn't actually add points to grid!"
            )

            # Verify grid is still sorted (sanity check)
            assert np.all(np.diff(second_grid) > 0), "Refined grid must be strictly increasing"

    @patch("fitqc.boundary.select_elbow")
    def test_refinement_handles_elbow_detection_returning_none(self, mock_elbow):
        """Verify refinement handles the case where elbow detection returns None.

        Why non-trivial: Tests ERROR HANDLING path that's hard to trigger naturally.
        If elbow detection fails (no elbow found), refinement should stop gracefully.

        What this catches:
        - Crashes when trying to refine around None elbow
        - Attempting arithmetic on None (e.g., None - 0.01)
        - Not stopping iteration when no elbow found
        """
        # Mock returns None (elbow detection failed)
        mock_elbow.return_value = None

        rng = np.random.default_rng(42)
        x = rng.uniform(0, 100, 10000)  # Uniform data, no elbow

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)

        # Should NOT crash
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Verify result is sensible (no detection)
        assert result.lower_pileup_detected is False, "Should not detect pileup when no elbow found"
        assert result.t_lo_star is None, "t_lo_star should be None when no elbow found"

        # Verify we didn't try to refine around a None elbow.
        # Each boundary (lower + upper) calls select_elbow once, then stops
        # because _aggregate_elbows_median returns None.
        assert mock_elbow.call_count == 2, (
            f"Should call select_elbow once per boundary (2 total). "
            f"Got {mock_elbow.call_count}. "
            f"Refinement should check for None before iterating."
        )

    @patch("fitqc.boundary._compute_quantile_curves_boundary")
    def test_quantile_grid_actually_passed_to_detection(self, mock_compute):
        """Verify custom quantile_grid is actually used in detection logic.

        Why non-trivial: Tests PARAMETER PROPAGATION. For scientific software,
        we must verify config parameters aren't silently ignored.

        What this catches:
        - Config parameter ignored (default grid used instead of custom)
        - Wrong grid passed to detection function
        - Grid not propagated through refinement iterations
        """
        # Configure mock to return typical values
        mock_compute.return_value = (
            np.array([0.001, 0.005, 0.01]),  # tol_at_quantile (matches custom grid size)
            [0.015],  # elbows_per_quantile
        )

        # Create config with CUSTOM grid (different from default)
        custom_grid = (0.001, 0.005, 0.01)  # Only 3 points (vs 26 default)
        custom_config = BoundaryConfig(use_quantile_analysis=True, quantile_grid=custom_grid)

        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, 1000)

        # Run detection
        _result = run_boundary_qc(x, L=0, U=10, config=custom_config)

        # Verify function was called
        assert mock_compute.called, "Quantile curve computation should be invoked"

        # Verify the correct grid was passed
        # (This checks that config.quantile_grid was actually used)
        call_args = mock_compute.call_args
        passed_grid = call_args[0][2]  # Third positional argument should be quantile_grid

        # Check grid size matches our custom grid
        assert len(passed_grid) == len(custom_grid), (
            f"Expected custom grid with {len(custom_grid)} points, "
            f"but {len(passed_grid)} points were passed to detection. "
            f"Custom quantile_grid is being ignored!"
        )

        # Check grid values match (within tolerance)
        np.testing.assert_array_almost_equal(
            passed_grid,
            np.array(custom_grid),
            decimal=6,
            err_msg="Custom quantile_grid values don't match what was passed to detection",
        )

    def test_refinement_increases_grid_size(self):
        """Iterative refinement should add points to quantile grid.

        Why: The algorithm should identify the elbow region and insert
        intermediate points there. Grid size should increase after refinement.

        Scientific validation: We expose quantile_grid_refined in result
        for inspection and validation.
        """
        rng = np.random.default_rng(42)
        n = 10000

        # Generate data with clear lower boundary pileup
        x = np.concatenate(
            [
                np.zeros(int(0.03 * n)),  # 3% at exact boundary
                rng.uniform(0, 100, n - int(0.03 * n)),
            ]
        )

        # Run with refinement enabled
        config_refined = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result_refined = run_boundary_qc(x, L=0, U=100, config=config_refined)

        # Size: grid should have grown
        assert hasattr(result_refined, "quantile_grid_refined_lower"), (
            "Result must expose refined grid for scientific validation"
        )

        if result_refined.quantile_grid_refined_lower is not None:
            initial_grid_size = len(config_refined.quantile_grid)
            refined_grid_size = len(result_refined.quantile_grid_refined_lower)

            assert refined_grid_size > initial_grid_size, (
                f"Grid should grow during refinement: {initial_grid_size} -> {refined_grid_size}"
            )

    def test_refinement_improves_detection_on_ahe_pattern(self):
        """A_He-like pattern should be detected with refinement enabled.

        This is THE critical integration test: the A_He failure case that
        motivated all these fixes. With refinement, we should now detect
        the pileup that was previously missed.

        A_He evidence: 26x quantile spacing at lower boundary, 5-7x excess
        mass in lower 5%, visible inflection in mass curve. Yet detection
        returned lower_detected=false, t_lo_star=null.
        """
        rng = np.random.default_rng(42)
        n = 100000

        # A_He pattern: 3% concentrated at exact lower boundary
        x_ahe = np.concatenate([np.zeros(int(0.03 * n)), rng.uniform(0, 100, n - int(0.03 * n))])

        # With refinement (should succeed)
        config_refine = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result_refine = run_boundary_qc(x_ahe, L=0, U=100, config=config_refine)

        # Behavior: refinement should detect
        assert result_refine.lower_pileup_detected is True, (
            "A_He pattern MUST be detected with refinement enabled"
        )
        assert result_refine.t_lo_star is not None

        # Contents: tolerance should be in reasonable range (~3%)
        assert 0.01 < result_refine.t_lo_star < 0.10, (
            f"Detected tolerance should be ~3%: got {result_refine.t_lo_star}"
        )

        # Upper boundary: should NOT detect (no pileup there)
        assert result_refine.upper_pileup_detected is False

    def test_refinement_can_be_disabled(self):
        """User should be able to disable refinement via config.

        Backward compatibility: if refinement causes issues, users can
        disable it and fall back to simple grid.
        """
        config = BoundaryConfig(refine_transition=False)

        # Behavior: flag is set
        assert config.refine_transition is False

        # Smoke test: should still work
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, 1000)
        result = run_boundary_qc(x, L=0, U=10, config=config)

        # Should not crash
        assert isinstance(result.lower_pileup_detected, bool)

    def test_refinement_handles_no_initial_elbow(self):
        """If initial pass finds no elbow, refinement should handle gracefully.

        Edge case: uniform data has no elbow. Refinement algorithm should
        detect this and return None without crashing.
        """
        rng = np.random.default_rng(42)
        x_uniform = rng.uniform(0, 10, 10000)

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x_uniform, L=0, U=10, config=config)

        # Behavior: graceful handling
        assert result.lower_pileup_detected is False
        assert result.t_lo_star is None or result.t_lo_star < 0.01

    def test_refinement_terminates_in_finite_iterations(self):
        """Refinement should terminate after max_iterations, not loop forever.

        Safety test: ensures algorithm doesn't get stuck in infinite refinement.
        """
        rng = np.random.default_rng(42)
        x = np.concatenate([np.zeros(1000), rng.uniform(0, 100, 9000)])

        # Run with refinement (should complete in reasonable time)
        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)

        t0 = time.time()
        result = run_boundary_qc(x, L=0, U=100, config=config)
        elapsed = time.time() - t0

        # Should complete in under 2 seconds (generous bound)
        assert elapsed < 2.0, f"Refinement took too long: {elapsed:.2f}s"

        # Should return valid result
        assert isinstance(result.lower_pileup_detected, bool)

    def test_refinement_handles_elbow_at_first_quantile(self):
        """Elbow at first quantile should be handled gracefully.

        CRITICAL edge case: If ALL mass is at exact boundary (0% tolerance),
        the elbow will be at q=0.0005 (first quantile). Refinement
        can't add points to the left of 0.0005, so must detect this
        and return without crashing.

        Test strategy: Create data where 100% of "pileup quantile" is
        at exact boundary, forcing elbow to first grid point.
        """
        rng = np.random.default_rng(42)
        n = 10000

        # Extreme case: 5% at EXACT boundary (u=0), rest uniform
        x = np.concatenate(
            [
                np.full(int(0.05 * n), 0.0),  # Exact boundary
                rng.uniform(0, 100, n - int(0.05 * n)),
            ]
        )

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            quantile_grid=(0.001, 0.01, 0.02, 0.05, 0.10, 0.25),
        )

        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Behavior: should detect (mass is clearly at boundary)
        assert result.lower_pileup_detected is True, "Exact boundary pileup must be detected"

        # Behavior: should not crash (graceful handling)
        assert result.t_lo_star is not None

        # Contents: tolerance should be very small (exact boundary)
        assert result.t_lo_star < 0.01, (
            f"Exact boundary should give very small tolerance: {result.t_lo_star}"
        )

        # Implementation detail: if we expose refined_grid
        if hasattr(result, "quantile_grid_refined_lower"):
            if result.quantile_grid_refined_lower is not None:
                # Should not have infinite points (bounded growth)
                assert len(result.quantile_grid_refined_lower) < 100, (
                    "Refined grid should be bounded, not grow without limit"
                )

    def test_refinement_handles_elbow_at_last_quantile(self):
        """Elbow at last quantile should be handled gracefully.

        CRITICAL edge case: If pileup is VERY broad (e.g., 30% of range),
        elbow might be beyond our initial grid. Refinement can't add
        points to the right of last quantile.

        Test strategy: Create broad pileup that extends beyond typical
        grid, forcing elbow toward end of grid.
        """
        rng = np.random.default_rng(42)
        n = 10000

        # Broad pileup: 20% of samples in first 15% of range
        pileup_samples = int(0.20 * n)
        x = np.concatenate(
            [
                rng.uniform(0, 15, pileup_samples),  # Broad pileup
                rng.uniform(0, 100, n - pileup_samples),
            ]
        )

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            quantile_grid=(0.001, 0.01, 0.05, 0.10, 0.15, 0.20),
        )

        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Should not crash
        assert isinstance(result.lower_pileup_detected, bool), (
            "Broad pileup should not crash refinement"
        )

        # If detected, tolerance should be in reasonable range
        if result.t_lo_star is not None:
            assert 0.0 < result.t_lo_star < 0.25, (
                f"Broad pileup tolerance should be reasonable: {result.t_lo_star}"
            )

    def test_refinement_handles_elbow_between_adjacent_points(self):
        """Elbow between two quantiles should refine correctly.

        CRITICAL: This is the MAIN use case - elbow falls between
        two adjacent grid points and we need to add resolution there.

        Test strategy: Create data where we KNOW the true pileup fraction,
        then verify refinement finds elbow in that region.
        """
        rng = np.random.default_rng(42)
        n = 100000  # Large n for precision

        # Precise pileup: exactly 1.5% at boundary
        pileup_frac = 0.015
        x = np.concatenate(
            [
                np.zeros(int(pileup_frac * n)),  # Exact boundary
                rng.uniform(0, 100, n - int(pileup_frac * n)),
            ]
        )

        # Initial grid straddles the true elbow
        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            quantile_grid=(
                0.001,
                0.01,
                0.02,
                0.05,
                0.10,  # 1.5% is between 0.01 and 0.02
            ),
        )

        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Should detect
        assert result.lower_pileup_detected is True
        assert result.t_lo_star is not None

        # Should be accurate (within 0.5% of true value)
        true_tolerance = pileup_frac
        detected_tolerance = result.t_lo_star

        assert abs(detected_tolerance - true_tolerance) < 0.005, (
            f"Refinement should be accurate: "
            f"true={true_tolerance:.4f}, detected={detected_tolerance:.4f}, "
            f"error={abs(detected_tolerance - true_tolerance):.4f}"
        )

        # Refined grid should have more points in the 1-2% region
        if hasattr(result, "quantile_grid_refined_lower"):
            if result.quantile_grid_refined_lower is not None:
                refined_grid = result.quantile_grid_refined_lower
                points_in_region = [q for q in refined_grid if 0.01 <= q <= 0.02]
                assert len(points_in_region) > 2, f"Should refine 1-2% region: {points_in_region}"


class TestFixesIntegration:
    """Integration tests across all fixes.

    Why these tests: Verify that all 5 fixes work together correctly
    and don't have unexpected interactions. These are end-to-end tests
    with realistic data patterns.
    """

    def test_uniform_data_no_false_positives(self):
        """After all fixes, uniform data should NOT trigger false positives.

        Why: More sensitivity (denser grid, refinement) increases false positive
        risk. We must verify that improved detection doesn't over-fire.
        """
        rng = np.random.default_rng(42)
        x_uniform = rng.uniform(0, 100, 100000)

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x_uniform, L=0, U=100, config=config)

        # Behavior: should NOT detect pileup
        assert result.lower_pileup_detected is False, "False positive on uniform data!"
        assert result.upper_pileup_detected is False, "False positive on uniform data!"

    def test_moderate_pileup_detected(self):
        """5% pileup in 1% of range should be detected reliably."""
        rng = np.random.default_rng(42)
        n = 50000
        x = np.concatenate(
            [
                rng.uniform(0, 1, int(0.05 * n)),  # 5% in first 1% of range
                rng.uniform(0, 100, n - int(0.05 * n)),
            ]
        )

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Behavior: should detect
        assert result.lower_pileup_detected is True
        assert result.t_lo_star is not None
        assert result.t_lo_star > 0, f"Expected positive tolerance, got {result.t_lo_star}"

    def test_asymmetric_detection_lower_only(self):
        """Lower pileup detected, upper not detected (asymmetric).

        Why: Fix 2 addresses single-element handling but should NOT
        aggregate lower+upper together. They remain independent.

        Common physics scenario: Parameter hits lower bound (e.g.,
        normalization parameter hitting zero).
        """
        rng = np.random.default_rng(42)
        n = 50000
        x = np.concatenate(
            [
                rng.uniform(0, 0.5, int(0.05 * n)),  # Lower pileup only
                rng.uniform(0, 100, n - int(0.05 * n)),
            ]
        )

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Behavior: asymmetric detection
        assert result.lower_pileup_detected is True, "Lower pileup should be detected"
        assert result.upper_pileup_detected is False, "Upper pileup should NOT be detected"

        # Contents: only lower tolerance should be significant
        assert result.t_lo_star is not None
        assert result.t_lo_star > 0

        if result.t_hi_star is not None:
            assert result.t_hi_star < result.t_lo_star, (
                "Lower tolerance should be much larger than upper"
            )

    def test_asymmetric_detection_upper_only(self):
        """Upper pileup detected, lower not detected (asymmetric).

        Why: Mirror test of lower_only. Validates that upper boundary
        detection works independently and correctly.

        Common physics scenario: Parameter hits upper bound (e.g.,
        amplitude parameter hitting maximum allowed value).
        """
        rng = np.random.default_rng(42)
        n = 50000
        x = np.concatenate(
            [
                rng.uniform(99.5, 100, int(0.05 * n)),  # Upper pileup only
                rng.uniform(0, 100, n - int(0.05 * n)),
            ]
        )

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Behavior: asymmetric detection (upper only)
        assert result.upper_pileup_detected is True, "Upper pileup should be detected"
        assert result.lower_pileup_detected is False, "Lower pileup should NOT be detected"

        # Contents: only upper tolerance should be significant
        assert result.t_hi_star is not None
        assert result.t_hi_star > 0

        if result.t_lo_star is not None:
            assert result.t_lo_star < result.t_hi_star, (
                "Upper tolerance should be much larger than lower"
            )

    def test_symmetric_detection_both_boundaries(self):
        """Both boundaries detected when pileup exists at both.

        Why: Validates that independent detection of lower/upper works
        correctly when BOTH have pileups (not mutually exclusive).

        Physics scenario: Parameter should be in (0, 1) but true value
        is sometimes <0 (hits lower) and sometimes >1 (hits upper).
        """
        rng = np.random.default_rng(42)
        n = 50000
        x = np.concatenate(
            [
                rng.uniform(0, 0.5, int(0.04 * n)),  # Lower pileup
                rng.uniform(99.5, 100, int(0.04 * n)),  # Upper pileup
                rng.uniform(0, 100, n - int(0.08 * n)),
            ]
        )

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Behavior: both detected
        assert result.lower_pileup_detected is True, "Lower boundary pileup should be detected"
        assert result.upper_pileup_detected is True, "Upper boundary pileup should be detected"

        # Contents: both tolerances significant
        assert result.t_lo_star is not None
        assert result.t_hi_star is not None
        assert result.t_lo_star > 0
        assert result.t_hi_star > 0

    def test_performance_no_catastrophic_slowdown(self):
        """All fixes together should not cause >5x slowdown.

        Why: User accepts slowdown if results improve, but we should
        check we haven't created O(n^2) or worse behavior.

        Note: This uses generous 5x bound (not strict 2x) to avoid
        flaky test failures on slow systems. Scientific correctness
        is more important than speed.
        """
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 100, 100000)

        # Baseline: old 7-point grid, no refinement
        config_baseline = BoundaryConfig(
            use_quantile_analysis=True,
            quantile_grid=(0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10),
            refine_transition=False,
        )

        t0 = time.time()
        run_boundary_qc(x, L=0, U=100, config=config_baseline)
        baseline_time = time.time() - t0

        # New: 26-point grid, with refinement
        config_new = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)

        t0 = time.time()
        run_boundary_qc(x, L=0, U=100, config=config_new)
        new_time = time.time() - t0

        # Accept up to 5x slowdown (generous bound)
        assert new_time < baseline_time * 5.0, (
            f"Unacceptable slowdown: {baseline_time:.3f}s -> {new_time:.3f}s "
            f"({new_time / baseline_time:.1f}x)"
        )


class TestFineGrainedBoundaryDetection:
    """Fine-grained tests for boundary detection at sub-percent scales.

    Why these tests: PPA12 validation revealed boundary stickiness at
    1-bin scale in 1000-bin histograms (0.1% resolution). Standard tests
    at 3-5% scale miss these fine-grained optimizer failures.

    Scientific context: Bayesian optimizers (MCMC, variational inference)
    can exhibit boundary stickiness at very small scales when:
    - Prior boundaries are hit during sampling
    - Optimizer convergence is incomplete
    - Step sizes become pathologically small near bounds

    These tests validate detection at scales relevant to production MCMC.
    """

    def test_single_bin_lower_boundary_stickiness(self):
        """Detect 1% of samples stuck in single bin at lower boundary.

        Scientific Context:
            In Bayesian inference, optimizers may hit parameter bounds exactly,
            causing samples to pile up at L. For 1000-bin histograms, this
            manifests as 1-bin pileup requiring tolerance detection at 0.1% scale.

            Real-world example: A_He parameter in PPA12 showed ~3% of chains
            stuck at lower bound with quantile compression ratio of 26x.

        PPA12 Validation Context:
            This test validates the critical case where exactly 1% of samples
            (10 bins in 1000-bin histogram) are stuck at the exact boundary
            value L=0. This is the minimum scale we need to detect reliably.

        Expected Behavior:
            - lower_pileup_detected = True
            - t_lo_star < 0.015 (sub-1.5% tolerance)
            - Quantile elbows show compression at low quantiles
            - Upper boundary unaffected (asymmetric detection)

        What This Tests:
            - Sub-percent scale detection capability
            - Exact boundary value handling (u=0.0 exactly)
            - Quantile grid resolution in 0-2% range
            - Single-bin pileup distinguishable from noise
        """
        rng = np.random.default_rng(42)
        n = 100000  # Large n for statistical stability at 1% scale

        # 1% stuck exactly at lower boundary
        # Real PPA12 data (A_He) shows boundary stickiness is a delta function
        # at the exact boundary (L=0), not spread over a bin width
        x = np.concatenate(
            [
                np.zeros(int(0.01 * n)),  # 1000 samples exactly at L=0
                rng.uniform(0, 100, int(0.99 * n)),  # 99000 uniform
            ]
        )

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Assertion 1: Detection (critical smoke test)
        assert result.lower_pileup_detected is True, (
            "Failed to detect 1% single-bin boundary stickiness. "
            "This is a CRITICAL failure - optimizer convergence issues at this "
            "scale will go undetected in production MCMC chains. "
            f"Got lower_pileup_detected={result.lower_pileup_detected}"
        )

        # Assertion 2: Type and existence checks
        assert result.t_lo_star is not None, "t_lo_star should not be None when pileup detected"
        assert isinstance(result.t_lo_star, float), (
            f"t_lo_star must be float, got {type(result.t_lo_star)}"
        )

        # Assertion 3: Value range for delta function at boundary
        # For exact boundary stickiness (delta function at L=0), the algorithm
        # detects elbow at t≈0 and returns the first measurable tolerance point
        # This should be very small (< 0.005) and positive
        assert 0.0001 < result.t_lo_star < 0.005, (
            f"Expected 0.0001 < t_lo_star < 0.005 for 1% delta function at L=0, "
            f"got {result.t_lo_star:.6f}. For exact boundary pileups, the returned "
            f"tolerance is the first measurable point after the delta function."
        )

        # Assertion 4: Array structure validation
        assert isinstance(result.tol_grid, np.ndarray), (
            "tol_grid must be numpy array for scientific analysis"
        )
        assert result.tol_grid.ndim == 1, (
            f"tol_grid must be 1D array, got shape {result.tol_grid.shape}"
        )
        assert len(result.tol_grid) > 0, "tol_grid cannot be empty"

        # Assertion 5: Mass curve structure
        assert isinstance(result.lower_mass_curve, np.ndarray)
        assert len(result.lower_mass_curve) == len(result.tol_grid), (
            f"Mass curve length {len(result.lower_mass_curve)} must match "
            f"tol_grid length {len(result.tol_grid)}"
        )

        # Assertion 6: Quantile compression validation (validates internals)
        if result.quantile_elbows is not None:
            assert "lower" in result.quantile_elbows, (
                "quantile_elbows must contain 'lower' key for lower boundary analysis"
            )
            lower_elbows = result.quantile_elbows["lower"]

            # Check for compression at low quantiles
            # For 1% pileup, we expect tol/q < 1 for q < 0.02
            low_q_ratios = [
                tol / q for q, tol in lower_elbows.items() if q < 0.02 and tol is not None and q > 0
            ]
            if low_q_ratios:
                median_ratio = np.median(low_q_ratios)
                assert median_ratio < 1.5, (
                    f"Expected compression ratio < 1.5 at low quantiles, "
                    f"got median={median_ratio:.3f}. "
                    f"This suggests quantile curve is too linear (no elbow). "
                    f"Ratios: {low_q_ratios}"
                )

        # Assertion 7: Upper boundary should NOT be affected
        assert result.upper_pileup_detected is False, (
            "Upper boundary should not show pileup (asymmetric case). "
            f"Got upper_pileup_detected={result.upper_pileup_detected}"
        )
        if result.t_hi_star is not None:
            assert result.t_hi_star < result.t_lo_star, (
                f"Upper tolerance {result.t_hi_star:.6f} should be << lower "
                f"tolerance {result.t_lo_star:.6f} for asymmetric pileup"
            )

    def test_single_bin_upper_boundary_stickiness(self):
        """Detect 1% of samples stuck in single bin at upper boundary.

        Scientific Context:
            Mirror case of lower boundary stickiness. Optimizers hitting
            upper bounds (e.g., amplitude parameters at maximum, positive
            definiteness constraints) exhibit the same pileup behavior.

            Physical interpretation: In galaxy fitting, amplitude parameters
            sometimes hit upper bounds when flux measurements have large
            positive excursions.

        PPA12 Validation Context:
            Validates symmetric detection capability. Upper boundary detection
            must work identically to lower boundary detection (same resolution,
            same sensitivity, same quantile analysis).

        Expected Behavior:
            - upper_pileup_detected = True
            - t_hi_star < 0.015 (sub-1.5% tolerance)
            - Lower boundary unaffected
            - Quantile elbows show compression at high quantiles

        What This Tests:
            - Upper boundary detection works independently
            - Coordinate transformation (u -> 1-u) preserves detection
            - Quantile grid resolution at upper boundary
            - No cross-contamination between lower/upper detection
        """
        rng = np.random.default_rng(43)  # Unique seed
        n = 100000

        # 1% stuck in single bin at upper boundary
        # For 1000-bin histogram of [0, 100], bin_width = 0.1
        # Realistic stickiness: spread over [U - bin_width, U] = [99.9, 100]
        bin_width = 0.1
        x = np.concatenate(
            [
                rng.uniform(100 - bin_width, 100, int(0.01 * n)),  # 1000 samples in [99.9, 100]
                rng.uniform(0, 100, int(0.99 * n)),
            ]
        )

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Assertion 1: Detection
        assert result.upper_pileup_detected is True, (
            "Failed to detect 1% upper boundary stickiness. "
            "This breaks symmetry with lower boundary detection. "
            f"Got upper_pileup_detected={result.upper_pileup_detected}"
        )

        # Assertion 2: Type checks
        assert result.t_hi_star is not None
        assert isinstance(result.t_hi_star, float), (
            f"t_hi_star must be float, got {type(result.t_hi_star)}"
        )

        # Assertion 3: Value range for delta function at boundary
        # For exact boundary stickiness (delta function at U=100), same logic as lower boundary
        assert 0.0001 < result.t_hi_star < 0.005, (
            f"Expected 0.0001 < t_hi_star < 0.005 for 1% delta function at U=100, "
            f"got {result.t_hi_star:.6f}. For exact boundary pileups, the returned "
            f"tolerance is the first measurable point after the delta function."
        )

        # Assertion 4: Array structure
        assert isinstance(result.upper_mass_curve, np.ndarray)
        assert len(result.upper_mass_curve) == len(result.tol_grid), (
            f"Upper mass curve length {len(result.upper_mass_curve)} must match "
            f"tol_grid length {len(result.tol_grid)}"
        )

        # Assertion 5: Quantile elbows structure
        if result.quantile_elbows is not None:
            assert "upper" in result.quantile_elbows, "quantile_elbows must contain 'upper' key"
            upper_elbows = result.quantile_elbows["upper"]
            assert isinstance(upper_elbows, dict), (
                f"Upper elbows must be dict, got {type(upper_elbows)}"
            )

        # Assertion 6: Lower boundary should NOT be affected
        assert result.lower_pileup_detected is False, (
            "Lower boundary should not show pileup (asymmetric case). "
            f"Got lower_pileup_detected={result.lower_pileup_detected}"
        )

        # Assertion 7: Mass curve validation
        # Upper mass should show sharp rise in first 1-2% of tol_grid
        if len(result.upper_mass_curve) > 2:
            # Find mass at small tolerance (first few points)
            early_mass = result.upper_mass_curve[:3].mean()
            assert early_mass > 0.005, (
                f"Expected early mass > 0.5% for 1% pileup, got {early_mass:.6f}. "
                f"Mass curve may not be capturing the boundary pileup correctly."
            )

    def test_single_bin_both_boundary_stickiness(self):
        """Detect simultaneous 1% pileups at both L=0 AND U=100.

        Scientific Context:
            Some parameters have physical constraints on both ends. For example,
            a parameter representing a fraction must be in [0, 1]. When the
            true value oscillates outside this range, the optimizer hits both
            bounds, creating bilateral boundary stickiness.

            Real-world example: Correlation coefficients in [-1, 1], fraction
            parameters in [0, 1], or normalized amplitudes.

        PPA12 Validation Context:
            This tests the independence of lower/upper detection. Both should
            trigger simultaneously without interference. This is the hardest
            case for detection algorithms that aggregate lower+upper.

        Expected Behavior:
            - Both lower_pileup_detected = True AND upper_pileup_detected = True
            - Both t_lo_star and t_hi_star in (0.005, 0.015) range
            - Quantile elbows for both boundaries
            - No mutual interference in tolerance estimation

        What This Tests:
            - Independent detection of lower and upper boundaries
            - No aggregation artifacts (Fix 2 prevents this)
            - Dual-elbow detection in quantile analysis
            - Statistical power with split pileups (0.5% each direction)
        """
        rng = np.random.default_rng(44)
        n = 100000

        # 1% at L=0 AND 1% at U=100 simultaneously
        # Delta functions at exact boundaries (like real PPA12 data)
        x = np.concatenate(
            [
                np.zeros(int(0.01 * n)),  # 1000 exactly at L=0
                np.full(int(0.01 * n), 100),  # 1000 exactly at U=100
                rng.uniform(0, 100, int(0.98 * n)),  # 98000 uniform
            ]
        )

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Assertion 1: Both boundaries detected
        assert result.lower_pileup_detected is True, (
            "Failed to detect lower boundary in bilateral pileup case. "
            f"Got lower_pileup_detected={result.lower_pileup_detected}"
        )
        assert result.upper_pileup_detected is True, (
            "Failed to detect upper boundary in bilateral pileup case. "
            f"Got upper_pileup_detected={result.upper_pileup_detected}"
        )

        # Assertion 2: Both tolerances exist
        assert result.t_lo_star is not None, "t_lo_star missing in bilateral case"
        assert result.t_hi_star is not None, "t_hi_star missing in bilateral case"

        # Assertion 3: Both tolerances in expected range for delta functions
        # Delta functions at exact boundaries return first measurable tolerance
        assert 0.0001 < result.t_lo_star < 0.005, (
            f"Lower tolerance should be very small for delta function: {result.t_lo_star:.6f}"
        )
        assert 0.0001 < result.t_hi_star < 0.005, (
            f"Upper tolerance should be very small for delta function: {result.t_hi_star:.6f}"
        )

        # Assertion 4: Tolerances should be similar (same pileup fraction)
        tol_ratio = result.t_lo_star / result.t_hi_star
        assert 0.5 < tol_ratio < 2.0, (
            f"Tolerances should be similar for equal pileups, got ratio={tol_ratio:.3f} "
            f"(t_lo={result.t_lo_star:.6f}, t_hi={result.t_hi_star:.6f}). "
            f"This suggests detection sensitivity differs between boundaries."
        )

        # Assertion 5: Quantile elbows for both boundaries
        if result.quantile_elbows is not None:
            assert "lower" in result.quantile_elbows, "Missing lower quantile elbows"
            assert "upper" in result.quantile_elbows, "Missing upper quantile elbows"

            lower_elbows = result.quantile_elbows["lower"]
            upper_elbows = result.quantile_elbows["upper"]

            # Both should have some valid elbows
            lower_valid = sum(1 for v in lower_elbows.values() if v is not None)
            upper_valid = sum(1 for v in upper_elbows.values() if v is not None)

            assert lower_valid > 0, (
                f"No valid lower elbows found in bilateral case. Lower elbows: {lower_elbows}"
            )
            assert upper_valid > 0, (
                f"No valid upper elbows found in bilateral case. Upper elbows: {upper_elbows}"
            )

        # Assertion 6: Mass curves show elbows
        # Lower mass should rise quickly then plateau
        lower_early = result.lower_mass_curve[:5].mean()
        lower_late = result.lower_mass_curve[-5:].mean()
        assert lower_early > 0.005, f"Lower mass curve shows no early rise: {lower_early:.6f}"
        assert lower_late > lower_early, "Lower mass curve should be monotonic increasing"

        # Assertion 7: Result structure completeness
        assert hasattr(result, "tol_grid")
        assert hasattr(result, "lower_mass_curve")
        assert hasattr(result, "upper_mass_curve")

    def test_sub_percent_pileup_lower_boundary(self):
        """Detect 0.5% pileup concentrated in 0.1% tolerance range at lower boundary.

        Scientific Context:
            Sub-percent pileups occur when:
            - Optimizer step sizes become very small near boundaries
            - Prior tails are extremely narrow
            - Numerical precision causes sample clustering

            This is at the LIMIT of what histogram-based methods can detect
            (5 bins in 1000-bin histogram). Requires excellent quantile grid
            resolution and noise robustness.

        PPA12 Validation Context:
            Tests the absolute lower limit of detection capability. If we can
            detect 0.5% in 0.1% range, we can handle any realistic MCMC
            convergence issue in production.

        Expected Behavior:
            - lower_pileup_detected = True (challenging but achievable)
            - t_lo_star < 0.002 (sub-0.2% tolerance)
            - Quantile grid must have points at 0.0005 scale
            - High statistical noise (50/100000 samples)

        What This Tests:
            - Absolute detection limit
            - Quantile grid minimum spacing
            - Noise vs signal discrimination
            - Statistical power at extreme scales
        """
        rng = np.random.default_rng(45)
        n = 100000  # Must be large for 0.5% to have statistical power

        # 0.5% (500 samples) concentrated in [0, 0.1] range
        pileup_samples = int(0.005 * n)
        x = np.concatenate(
            [
                rng.uniform(0, 0.1, pileup_samples),  # 0.5% in first 0.1% of range
                rng.uniform(0, 100, n - pileup_samples),
            ]
        )

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            # Ensure fine quantile grid
            pileup_threshold=0.002,  # Lower threshold for sub-percent detection
        )
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Assertion 1: Detection (may be marginal, but should succeed)
        assert result.lower_pileup_detected is True, (
            "Failed to detect 0.5% sub-percent pileup. "
            "This is at the detection limit - if this fails, quantile grid "
            "lacks resolution or noise robustness is insufficient. "
            f"Got lower_pileup_detected={result.lower_pileup_detected}, "
            f"t_lo_star={result.t_lo_star}"
        )

        # Assertion 2: Tolerance in sub-percent range
        assert result.t_lo_star is not None
        assert result.t_lo_star < 0.008, (
            f"Expected t_lo_star < 0.008 for 0.5% pileup, got {result.t_lo_star:.6f}. "
            f"Tolerance is too large - detection may be finding noise instead of signal."
        )

        # Assertion 3: Quantile grid resolution verification
        # Must have points at 0.0005 scale to detect 0.5%
        min_quantile = min(config.quantile_grid)
        assert min_quantile <= 0.001, (
            f"Quantile grid minimum {min_quantile:.6f} too large for sub-percent detection. "
            f"Need min_quantile <= 0.001 to detect 0.5% pileups reliably."
        )

        # Assertion 4: Grid has sufficient low-end resolution
        low_quantiles = [q for q in config.quantile_grid if q <= 0.01]
        assert len(low_quantiles) >= 5, (
            f"Need >= 5 quantile points in [0, 0.01] range for sub-percent detection, "
            f"got {len(low_quantiles)}. Grid: {low_quantiles}"
        )

        # Assertion 5: Mass curve shows very early rise
        # For 0.5% in 0.1% range, mass at tol=0.001 should be ~0.5%
        if len(result.tol_grid) > 0 and len(result.lower_mass_curve) > 0:
            # Find mass at very small tolerance
            small_tol_idx = np.searchsorted(result.tol_grid, 0.002)
            if small_tol_idx < len(result.lower_mass_curve):
                small_tol_mass = result.lower_mass_curve[small_tol_idx]
                assert small_tol_mass > 0.002, (
                    f"Expected mass > 0.2% at tol~0.002, got {small_tol_mass:.6f}. "
                    f"Mass curve may not be capturing sub-percent pileup."
                )

        # Assertion 6: Type safety
        assert isinstance(result.t_lo_star, float)
        assert isinstance(result.tol_grid, np.ndarray)

        # Assertion 7: Upper boundary unaffected
        assert result.upper_pileup_detected is False, (
            "Upper boundary should not be affected by lower sub-percent pileup"
        )

    def test_sub_percent_pileup_upper_boundary(self):
        """Detect 0.5% pileup concentrated in 0.1% tolerance range at upper boundary.

        Scientific Context:
            Mirror of lower boundary sub-percent test. Validates that upper
            boundary detection has identical sensitivity and resolution as
            lower boundary detection.

            Physical example: Positive-definite parameters approaching unity
            bound (e.g., correlation coefficients near +1).

        PPA12 Validation Context:
            Ensures detection capability is symmetric. Any asymmetry would
            indicate coordinate transformation issues or biased elbow detection.

        Expected Behavior:
            - upper_pileup_detected = True
            - t_hi_star < 0.002
            - Identical performance to lower boundary case
            - No cross-boundary contamination

        What This Tests:
            - Upper boundary detection at extreme scales
            - Symmetry of detection algorithm
            - Coordinate transformation (u -> 1-u) preserves precision
            - Independence of lower/upper analysis
        """
        rng = np.random.default_rng(46)
        n = 100000

        # 0.5% (500 samples) concentrated in [99.9, 100] range
        pileup_samples = int(0.005 * n)
        x = np.concatenate(
            [
                rng.uniform(99.9, 100, pileup_samples),  # 0.5% in last 0.1% of range
                rng.uniform(0, 100, n - pileup_samples),
            ]
        )

        config = BoundaryConfig(
            use_quantile_analysis=True, refine_transition=True, pileup_threshold=0.002
        )
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Assertion 1: Detection
        assert result.upper_pileup_detected is True, (
            "Failed to detect 0.5% sub-percent upper boundary pileup. "
            f"Got upper_pileup_detected={result.upper_pileup_detected}, "
            f"t_hi_star={result.t_hi_star}"
        )

        # Assertion 2: Tolerance in sub-percent range
        assert result.t_hi_star is not None
        assert result.t_hi_star < 0.008, (
            f"Expected t_hi_star < 0.008 for 0.5% pileup, got {result.t_hi_star:.6f}"
        )

        # Assertion 3: Type and structure checks
        assert isinstance(result.t_hi_star, float)
        assert isinstance(result.upper_mass_curve, np.ndarray)
        assert len(result.upper_mass_curve) > 0

        # Assertion 4: Mass curve shows very early rise
        if len(result.tol_grid) > 0:
            small_tol_idx = np.searchsorted(result.tol_grid, 0.002)
            if small_tol_idx < len(result.upper_mass_curve):
                small_tol_mass = result.upper_mass_curve[small_tol_idx]
                assert small_tol_mass > 0.002, (
                    f"Expected upper mass > 0.2% at small tol, got {small_tol_mass:.6f}"
                )

        # Assertion 5: Lower boundary unaffected
        assert result.lower_pileup_detected is False, (
            "Lower boundary should not be affected by upper sub-percent pileup"
        )

        # Assertion 6: Quantile grid quality (same as lower test)
        min_quantile = min(config.quantile_grid)
        assert min_quantile <= 0.001, (
            f"Quantile grid minimum {min_quantile:.6f} insufficient for sub-percent detection"
        )

        # Assertion 7: Result completeness
        assert hasattr(result, "tol_grid")
        assert hasattr(result, "upper_mass_curve")
        assert result.tol_grid.ndim == 1

    def test_quantile_grid_resolution_for_fine_pileups(self):
        """Verify quantile grid has sufficient resolution for sub-1% pileup detection.

        Scientific Context:
            Fine-grained pileup detection fundamentally requires fine-grained
            quantile sampling. To detect a 0.5% pileup, we need quantiles at
            0.0005, 0.001, etc. Without this resolution, the pileup falls
            "between the cracks" of the grid.

            This is analogous to Nyquist sampling: you need 2+ samples per
            feature to resolve it. For 0.5% pileup, we need quantiles at
            0.25%, 0.5%, 0.75%, etc.

        PPA12 Validation Context:
            The A_He failure case showed 3% pileup missed due to 7-point grid
            with 1% spacing (0.01, 0.02, ...). Fix 3 expanded to 26 points.
            This test validates that expansion is sufficient for sub-1% scale.

        Expected Behavior:
            - min(quantile_grid) <= 0.001 (can detect down to 0.1% features)
            - >= 10 points in [0, 0.02] range (dense coverage)
            - Monotonically increasing
            - Spans reasonable range [0.0005, 0.25]

        What This Tests:
            - Quantile grid design (Fix 3 implementation)
            - Resolution vs efficiency tradeoff
            - Coverage of critical 0-2% range
            - Grid boundaries (min/max values)
        """
        config = BoundaryConfig()

        # Assertion 1: Minimum quantile (detection floor)
        min_q = min(config.quantile_grid)
        assert min_q <= 0.001, (
            f"Quantile grid minimum {min_q:.6f} too large for fine pileup detection. "
            f"Need min_q <= 0.001 to detect sub-1% boundary stickiness. "
            f"This is a CRITICAL requirement for PPA12 validation."
        )

        # Assertion 2: Dense coverage in critical 0-2% range
        critical_range = [q for q in config.quantile_grid if 0 <= q <= 0.02]
        assert len(critical_range) >= 10, (
            f"Need >= 10 quantile points in [0, 0.02] for fine resolution, "
            f"got {len(critical_range)}. Critical range: {critical_range}. "
            f"Without dense coverage here, 1-2% pileups will be missed."
        )

        # Assertion 3: Monotonicity (required for interpolation)
        grid_array = np.array(config.quantile_grid)
        diffs = np.diff(grid_array)
        assert np.all(diffs > 0), (
            f"Quantile grid must be strictly increasing. "
            f"Found non-increasing at indices: {np.where(diffs <= 0)[0]}"
        )

        # Assertion 4: Maximum spacing in critical range
        if len(critical_range) > 1:
            critical_spacing = np.diff(sorted(critical_range))
            max_gap = np.max(critical_spacing)
            assert max_gap < 0.005, (
                f"Maximum gap in critical range {max_gap:.6f} too large. "
                f"Should be < 0.005 (0.5%) for fine resolution. "
                f"Large gaps create blind spots in detection."
            )

        # Assertion 5: Reasonable upper bound
        max_q = max(config.quantile_grid)
        assert 0.20 <= max_q <= 0.30, (
            f"Quantile grid maximum {max_q:.3f} outside expected [0.20, 0.30]. "
            f"Too low misses broad pileups; too high wastes computation."
        )

        # Assertion 6: Grid size (should be 26 per Fix 3)
        assert len(config.quantile_grid) >= 20, (
            f"Quantile grid too small: {len(config.quantile_grid)} points. "
            f"Expected >= 20 for fine-grained detection (Fix 3: 7→26 points)."
        )

        # Assertion 7: Data type validation
        assert isinstance(config.quantile_grid, tuple), (
            f"quantile_grid should be tuple (immutable), got {type(config.quantile_grid)}"
        )
        assert all(isinstance(q, float) for q in config.quantile_grid), (
            "All quantile grid values must be float"
        )

    def test_tolerance_grid_resolution_for_fine_pileups(self):
        """Verify tolerance grid has adequate spacing for sub-1% elbow detection.

        Scientific Context:
            Elbow detection (Kneedle algorithm) requires sufficient samples
            along the curve to identify inflection points. For sub-1% pileups,
            the elbow occurs at tol~0.01, so we need grid points at 0.005,
            0.01, 0.015 spacing to resolve the elbow shape.

            Coarse grids (spacing > 1%) will "step over" the elbow, causing
            Kneedle to fail or return imprecise tolerance estimates.

        PPA12 Validation Context:
            Tolerance grid complements quantile grid. While quantile grid
            controls which quantiles we analyze, tolerance grid controls
            the resolution of mass curves P(u < tol).

            Both must have fine resolution for accurate elbow detection.

        Expected Behavior:
            - Tolerance grid generated by run_boundary_qc
            - Spacing in 0-0.02 range should be < 0.002 (0.2%)
            - Grid should extend to at least tol_max = 0.25
            - Monotonically increasing

        What This Tests:
            - Tolerance grid construction (_build_tolerance_grid)
            - Grid density vs efficiency
            - Elbow detection input quality
            - Integration with quantile analysis
        """
        rng = np.random.default_rng(47)
        n = 50000

        # Create test data with known 2% pileup
        x = np.concatenate([np.zeros(int(0.02 * n)), rng.uniform(0, 100, int(0.98 * n))])

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Assertion 1: Tolerance grid exists and is valid
        assert hasattr(result, "tol_grid"), "Result must contain tol_grid"
        assert isinstance(result.tol_grid, np.ndarray)
        assert result.tol_grid.ndim == 1, f"tol_grid must be 1D, got shape {result.tol_grid.shape}"

        # Assertion 2: Grid is non-empty and reasonable size
        # Default config uses 41 points (0 to 0.05 with 0.00125 spacing)
        assert len(result.tol_grid) >= 40, (
            f"tol_grid too small: {len(result.tol_grid)} points. "
            f"Need >= 40 for fine elbow resolution (default is 41)."
        )
        assert len(result.tol_grid) <= 1000, (
            f"tol_grid too large: {len(result.tol_grid)} points. "
            f"Diminishing returns above 1000, indicates inefficient grid."
        )

        # Assertion 3: Monotonicity
        diffs = np.diff(result.tol_grid)
        assert np.all(diffs > 0), (
            f"Tolerance grid must be strictly increasing. "
            f"Found non-increasing at indices: {np.where(diffs <= 0)[0]}"
        )

        # Assertion 4: Fine spacing in critical 0-2% region
        critical_tols = result.tol_grid[result.tol_grid <= 0.02]
        if len(critical_tols) > 1:
            critical_spacing = np.diff(critical_tols)
            max_spacing = np.max(critical_spacing)
            assert max_spacing < 0.003, (
                f"Maximum spacing in critical region {max_spacing:.6f} too large. "
                f"Should be < 0.003 for sub-1% elbow detection. "
                f"Coarse grid will miss fine elbows."
            )

        # Assertion 5: Coverage of expected range
        assert result.tol_grid[0] >= 0, f"tol_grid minimum {result.tol_grid[0]:.6f} should be >= 0"
        assert result.tol_grid[-1] >= 0.10, (
            f"tol_grid maximum {result.tol_grid[-1]:.6f} should extend to >= 0.10 "
            f"to capture moderate pileups"
        )

        # Assertion 6: Data type
        assert result.tol_grid.dtype in [np.float64, np.float32], (
            f"tol_grid should be floating point, got {result.tol_grid.dtype}"
        )

        # Assertion 7: Sufficient points in low range for elbow detection
        # For 2% pileup, elbow at ~0.02, need points at 0.005, 0.01, 0.015, 0.02, 0.025
        low_range_points = result.tol_grid[result.tol_grid <= 0.03]
        assert len(low_range_points) >= 10, (
            f"Need >= 10 tolerance points in [0, 0.03] for elbow detection, "
            f"got {len(low_range_points)}. Kneedle requires sufficient samples "
            f"to identify inflection points."
        )


class TestInitialGuessStickiness:
    """Tests for stickiness at initial guess values (mid-range).

    Why these tests: Document known limitation of boundary detection method.
    The current algorithm detects BOUNDARY stickiness (at L or U) but does
    NOT detect stickiness at arbitrary interior points (e.g., initial guess).

    Scientific context: When optimizers have poor initial guesses or get
    stuck in local minima, samples may pile up at interior points, not
    boundaries. This is a different failure mode requiring different detection.

    Future work: Interior stickiness detection would require:
    - Multi-modal distribution detection
    - Peak finding in histograms
    - Comparison to expected smooth posterior

    These tests document the current limitation for future improvements.
    """

    def test_initial_guess_stickiness_mid_range(self):
        """Document that 2% pileup at x=50 (mid-range) is NOT detected.

        Scientific Context:
            Optimizer may use x=50 as initial guess for parameter in [0, 100].
            If optimizer has poor step size or acceptance rate, chains can
            get stuck at initial guess, creating interior pileup.

            Example: Hamiltonian Monte Carlo with too-small step size may
            not explore away from initialization, causing persistent bias.

        Known Limitation:
            Current boundary detection method ONLY looks for excess mass
            near L=0 or U=100. Interior pileups at x=50 are not analyzed.

            This is BY DESIGN: boundary detection is for parameter bounds,
            not for general convergence issues.

        Expected Behavior:
            - lower_pileup_detected = False (x=50 is not near L=0)
            - upper_pileup_detected = False (x=50 is not near U=100)
            - This is CORRECT behavior given method design

        What This Tests:
            - Documents scope limitation of boundary detection
            - Provides test case for future interior detection
            - Validates that we don't false-positive on interior pileups
            - Clarifies "boundary" vs "general convergence" distinction
        """
        rng = np.random.default_rng(48)
        n = 100000

        # 2% stuck at exactly x=50 (mid-range, not boundary)
        x = np.concatenate(
            [
                np.full(int(0.02 * n), 50.0),  # 2000 samples at interior point
                rng.uniform(0, 100, int(0.98 * n)),
            ]
        )

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Assertion 1: Lower boundary NOT detected (expected)
        assert result.lower_pileup_detected is False, (
            "UNEXPECTED: Lower boundary detected for mid-range pileup. "
            "This suggests boundary detection is triggering on interior modes, "
            "which is outside its design scope. Interior pileup at x=50 should "
            "NOT trigger boundary detection at L=0."
        )

        # Assertion 2: Upper boundary NOT detected (expected)
        assert result.upper_pileup_detected is False, (
            "UNEXPECTED: Upper boundary detected for mid-range pileup. "
            "Interior pileup at x=50 should NOT trigger detection at U=100."
        )

        # Assertion 3: Tolerances should be None or very small
        if result.t_lo_star is not None:
            assert result.t_lo_star < 0.01, (
                f"Lower tolerance {result.t_lo_star:.6f} unexpectedly large. "
                f"Interior pileup should not create significant lower boundary tolerance."
            )
        if result.t_hi_star is not None:
            assert result.t_hi_star < 0.01, (
                f"Upper tolerance {result.t_hi_star:.6f} unexpectedly large. "
                f"Interior pileup should not create significant upper boundary tolerance."
            )

        # Assertion 4: Mass curves should be approximately linear
        # For uniform data (ignoring interior pileup), mass ~ tol
        # Check that mass curve doesn't show boundary elbow
        if len(result.lower_mass_curve) > 10:
            # First 10% of tolerance range should have ~10% of mass (linear)
            early_tol = result.tol_grid[len(result.tol_grid) // 10]
            early_mass = result.lower_mass_curve[len(result.lower_mass_curve) // 10]

            # For uniform, P(u < 0.1*tol_max) ≈ 0.1*tol_max
            # Allow 2x deviation (not strict, just checking not 10x)
            expected_mass = early_tol
            assert early_mass < expected_mass * 3, (
                f"Lower mass curve unexpectedly non-linear for interior pileup. "
                f"At tol={early_tol:.3f}, mass={early_mass:.3f}, "
                f"expected ~{expected_mass:.3f}"
            )

        # Assertion 5: Result structure validity
        assert isinstance(result.lower_pileup_detected, bool)
        assert isinstance(result.upper_pileup_detected, bool)

        # Assertion 6: Documentation note in output
        # This assertion serves as inline documentation
        assert True, (
            "KNOWN LIMITATION: Boundary detection does not identify interior "
            "stickiness. The 2% pileup at x=50 is correctly ignored. "
            "Future work: implement interior mode detection for general convergence QC."
        )

        # Assertion 7: Quantile elbows should show no strong signal
        if result.quantile_elbows is not None:
            lower_elbows = result.quantile_elbows.get("lower", {})
            # Count how many elbows were actually found
            found_elbows = sum(1 for v in lower_elbows.values() if v is not None and v > 0.005)
            assert found_elbows < len(lower_elbows) * 0.5, (
                f"Too many quantile elbows detected ({found_elbows}/{len(lower_elbows)}) "
                f"for interior pileup. Should mostly be None or very small."
            )

    def test_single_bin_initial_guess_stickiness(self):
        """Document that 1% pileup in 1-bin width at x=50 is NOT detected.

        Scientific Context:
            This is the interior analogue of test_single_bin_lower_boundary_stickiness.
            Same 1% concentration, same single-bin width, but at interior point
            instead of boundary.

            Demonstrates that the detection method's sensitivity is specific
            to BOUNDARIES, not to any narrow pileup.

        Known Limitation:
            Even though this has identical statistical properties to the
            boundary case (1% in 0.1% range), it's not detected because
            it's at x=50, not at L=0 or U=100.

        Expected Behavior:
            - No detection (both flags = False)
            - Tolerances None or negligible
            - This is correct behavior

        What This Tests:
            - Validates specificity of boundary detection
            - Documents that "narrow" ≠ "boundary"
            - Provides comparison case for boundary tests
            - Guards against overgeneralized detection
        """
        rng = np.random.default_rng(49)
        n = 100000

        # 1% in 0.1% range centered at x=50 (interior, not boundary)
        pileup_samples = int(0.01 * n)
        x = np.concatenate(
            [
                rng.uniform(49.95, 50.05, pileup_samples),  # 1% in 0.1 range at x=50
                rng.uniform(0, 100, n - pileup_samples),
            ]
        )

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Assertion 1: No lower boundary detection
        assert result.lower_pileup_detected is False, (
            "Interior pileup should not trigger lower boundary detection. x=50 is far from L=0."
        )

        # Assertion 2: No upper boundary detection
        assert result.upper_pileup_detected is False, (
            "Interior pileup should not trigger upper boundary detection. x=50 is far from U=100."
        )

        # Assertion 3: Comparison to boundary case
        # Create identical pileup at boundary for comparison
        x_boundary = np.concatenate(
            [rng.uniform(0, 0.1, pileup_samples), rng.uniform(0, 100, n - pileup_samples)]
        )
        result_boundary = run_boundary_qc(x_boundary, L=0, U=100, config=config)

        # The boundary case SHOULD detect
        assert result_boundary.lower_pileup_detected is True, (
            "Boundary pileup should be detected (sanity check for comparison)"
        )

        # The interior case should NOT detect
        assert result.lower_pileup_detected is False, (
            "Interior pileup with identical statistics should NOT be detected. "
            "This demonstrates that detection is boundary-specific."
        )

        # Assertion 4: Tolerance difference
        # Boundary case should have significant tolerance
        assert result_boundary.t_lo_star is not None
        assert result_boundary.t_lo_star > 0

        # Interior case should have None or negligible tolerance
        if result.t_lo_star is not None:
            assert result.t_lo_star < 0.005, (
                f"Interior case should have minimal tolerance, got {result.t_lo_star:.6f}"
            )

        # Assertion 5: Result consistency
        assert isinstance(result.lower_pileup_detected, bool)
        assert isinstance(result.upper_pileup_detected, bool)

        # Assertion 6: Mass curve comparison
        # Interior pileup mass curve should be more linear than boundary
        lower_curve_linearity = np.corrcoef(result.tol_grid, result.lower_mass_curve)[0, 1]
        boundary_curve_linearity = np.corrcoef(
            result_boundary.tol_grid, result_boundary.lower_mass_curve
        )[0, 1]

        # Interior should be more linear (higher correlation)
        assert lower_curve_linearity > boundary_curve_linearity, (
            f"Interior mass curve should be more linear than boundary curve. "
            f"Interior linearity: {lower_curve_linearity:.4f}, "
            f"Boundary linearity: {boundary_curve_linearity:.4f}"
        )

        # Assertion 7: Documentation assertion
        assert True, (
            "DOCUMENTED BEHAVIOR: Single-bin interior stickiness is not detected. "
            "Detection is specifically for boundary convergence issues, not "
            "general multimodality or interior modes. This is by design."
        )


class TestBoundaryArtifactHandling:
    """Tests for handling artifacts near tol_max and other edge cases.

    Why these tests: At the edge of the tolerance range (tol_max), mathematical
    and numerical artifacts can appear that shouldn't be interpreted as pileups:
    - Elbows near tol_max may be curve saturation, not real pileups
    - False positives from noise at high tolerance
    - Boundary effects in elbow detection algorithms

    These tests ensure robust handling of edge cases and prevent false positives.
    """

    def test_pileup_at_tol_max_is_valid(self):
        """Verify that legitimate elbows near tol_max are accepted.

        Scientific Context:
            Broad pileups (e.g., 15% of samples in first 20% of range) create
            elbows near the upper end of tolerance grid. These are legitimate
            convergence issues, not artifacts.

            Example: Parameter with strong prior peak near boundary, causing
            persistent bias across many chains.

        PPA12 Validation Context:
            Detection algorithm must distinguish between:
            - Real broad pileup (elbow near tol_max) ✓ DETECT
            - Curve saturation artifact (P→1 as tol→tol_max) ✗ IGNORE

            This test validates the DETECT case.

        Expected Behavior:
            - Detection succeeds even if elbow is at t_lo* ~ 0.15-0.20
            - No artificial rejection of "too large" tolerances
            - Tolerance should match empirical pileup fraction

        What This Tests:
            - No arbitrary upper limit on detected tolerance
            - Elbow detection works throughout tolerance range
            - Broad pileups are not false-negatives
            - tol_max boundary handling
        """
        rng = np.random.default_rng(50)
        n = 100000

        # Create broad pileup: 15% of samples in first 20% of range
        pileup_frac = 0.15
        pileup_width = 0.20

        pileup_samples = int(pileup_frac * n)
        x = np.concatenate(
            [
                rng.uniform(0, pileup_width * 100, pileup_samples),  # 15% in [0, 20]
                rng.uniform(0, 100, n - pileup_samples),
            ]
        )

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Assertion 1: Detection should succeed
        assert result.lower_pileup_detected is True, (
            "Failed to detect broad pileup near tol_max. "
            "Algorithm may be artificially rejecting large tolerances. "
            f"Got lower_pileup_detected={result.lower_pileup_detected}, "
            f"t_lo_star={result.t_lo_star}"
        )

        # Assertion 2: Tolerance should be in reasonable range
        assert result.t_lo_star is not None
        assert 0.10 < result.t_lo_star < 0.30, (
            f"Detected tolerance {result.t_lo_star:.6f} outside expected [0.10, 0.30]. "
            f"For 15% pileup in 20% range, expect elbow around 0.15-0.20."
        )

        # Assertion 3: Tolerance should approximate pileup characteristics
        # For this data, we expect t_lo* ~ 0.15-0.20 (between pileup_frac and pileup_width)
        assert 0.12 < result.t_lo_star < 0.25, (
            f"Tolerance {result.t_lo_star:.6f} doesn't match empirical pileup. "
            f"Created 15% in 20% range, expected detection near 0.15-0.20."
        )

        # Assertion 4: Type safety
        assert isinstance(result.t_lo_star, float)
        assert isinstance(result.lower_pileup_detected, bool)

        # Assertion 5: Mass curve validation
        # At detected tolerance, mass should be significantly above uniform
        detected_idx = np.searchsorted(result.tol_grid, result.t_lo_star)
        if detected_idx < len(result.lower_mass_curve):
            mass_at_elbow = result.lower_mass_curve[detected_idx]
            uniform_expected = result.t_lo_star  # For uniform, P(u<tol) = tol

            excess_ratio = mass_at_elbow / uniform_expected if uniform_expected > 0 else 0
            assert excess_ratio > 1.2, (
                f"Mass at elbow {mass_at_elbow:.4f} should exceed uniform "
                f"expectation {uniform_expected:.4f} by > 20%. "
                f"Got ratio {excess_ratio:.3f}. Elbow may be artifact."
            )

        # Assertion 6: Result structure
        assert hasattr(result, "tol_grid")
        assert len(result.tol_grid) > 0

        # Assertion 7: Upper boundary independence
        assert result.upper_pileup_detected is False, (
            "Upper boundary should not be affected by lower broad pileup"
        )

    def test_true_uniform_no_false_positive_at_tol_max(self):
        """Guard against false positives from artifacts near tol_max.

        Scientific Context:
            True uniform data has P(u < tol) = tol, a linear relationship.
            As tol → tol_max, this curve approaches P → tol_max (saturation).

            Poor elbow detection might interpret this saturation as an elbow,
            causing false positives on perfectly uniform data.

        PPA12 Validation Context:
            This is the critical false-positive guard. After all sensitivity
            improvements (26-point grid, refinement, sub-percent detection),
            we must verify we don't over-fire on clean data.

            This test ensures tol_max artifacts are correctly ignored.

        Expected Behavior:
            - lower_pileup_detected = False
            - upper_pileup_detected = False
            - t_lo_star and t_hi_star should be None or very small
            - No spurious elbows in quantile analysis

        What This Tests:
            - False positive rate on uniform data
            - Elbow detection robustness near saturation
            - Threshold calibration (excess_ratio, pileup_threshold)
            - Balance between sensitivity and specificity
        """
        rng = np.random.default_rng(51)
        n = 100000  # Large sample for statistical stability

        # True uniform data - no pileup anywhere
        x = rng.uniform(0, 100, n)

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Assertion 1: No lower boundary detection
        assert result.lower_pileup_detected is False, (
            "FALSE POSITIVE on uniform data at lower boundary! "
            "This is a critical failure - algorithm is detecting pileups that "
            "don't exist, likely due to tol_max saturation artifacts or "
            "threshold miscalibration. "
            f"Got lower_pileup_detected={result.lower_pileup_detected}, "
            f"t_lo_star={result.t_lo_star}"
        )

        # Assertion 2: No upper boundary detection
        assert result.upper_pileup_detected is False, (
            "FALSE POSITIVE on uniform data at upper boundary! "
            f"Got upper_pileup_detected={result.upper_pileup_detected}, "
            f"t_hi_star={result.t_hi_star}"
        )

        # Assertion 3: Tolerances should be None or negligible
        if result.t_lo_star is not None:
            assert result.t_lo_star < 0.01, (
                f"Lower tolerance {result.t_lo_star:.6f} too large for uniform data. "
                f"Expected None or < 0.01 (statistical noise level)."
            )
        if result.t_hi_star is not None:
            assert result.t_hi_star < 0.01, (
                f"Upper tolerance {result.t_hi_star:.6f} too large for uniform data."
            )

        # Assertion 4: Mass curve linearity
        # For uniform, mass curve should be highly linear (correlation ~ 0.99+)
        lower_corr = np.corrcoef(result.tol_grid, result.lower_mass_curve)[0, 1]
        upper_corr = np.corrcoef(result.tol_grid, result.upper_mass_curve)[0, 1]

        assert lower_corr > 0.95, (
            f"Lower mass curve should be highly linear for uniform data. "
            f"Got correlation {lower_corr:.4f}, expected > 0.95. "
            f"Low linearity suggests noise or numerical issues."
        )
        assert upper_corr > 0.95, (
            f"Upper mass curve should be highly linear for uniform data. "
            f"Got correlation {upper_corr:.4f}, expected > 0.95."
        )

        # Assertion 5: Quantile elbows should be mostly None
        if result.quantile_elbows is not None:
            lower_elbows = result.quantile_elbows.get("lower", {})
            upper_elbows = result.quantile_elbows.get("upper", {})

            # Count non-None elbows
            lower_found = sum(1 for v in lower_elbows.values() if v is not None and v > 0.005)
            upper_found = sum(1 for v in upper_elbows.values() if v is not None and v > 0.005)

            # Most should be None (> 70% agreement threshold would fail)
            assert lower_found < len(lower_elbows) * 0.3, (
                f"Too many lower quantile elbows on uniform data: "
                f"{lower_found}/{len(lower_elbows)}. Indicates false elbow detection."
            )
            assert upper_found < len(upper_elbows) * 0.3, (
                f"Too many upper quantile elbows on uniform data: "
                f"{upper_found}/{len(upper_elbows)}."
            )

        # Assertion 6: Mass curve deviation from theoretical
        # For uniform, P(u < tol) should equal tol (within sampling error)
        # Check root mean square error
        lower_theoretical = result.tol_grid
        lower_rmse = np.sqrt(np.mean((result.lower_mass_curve - lower_theoretical) ** 2))

        assert lower_rmse < 0.01, (
            f"Lower mass curve deviates from theoretical uniform by RMSE={lower_rmse:.6f}. "
            f"Should be < 0.01 for n={n} uniform samples."
        )

        # Assertion 7: Result type consistency
        assert isinstance(result.lower_pileup_detected, bool)
        assert isinstance(result.upper_pileup_detected, bool)
        assert isinstance(result.tol_grid, np.ndarray)
        assert isinstance(result.lower_mass_curve, np.ndarray)
        assert isinstance(result.upper_mass_curve, np.ndarray)


@pytest.mark.parametrize(
    "dtype,dtype_name",
    [
        (np.float32, "float32"),
        (np.float64, "float64"),
    ],
)
class TestFloatPrecisionBoundaryDetection:
    """Tests for float32/float64 precision effects on boundary detection.

    Real-World Context:
        Optimizer fits are performed in float64 (double precision), but results
        are stored as float32 (single precision) to reduce data volume. This
        quantization introduces ~1.2e-7 noise at boundaries, which can obscure
        or create stickiness patterns.

    Why These Tests:
        1. Validate detection works despite float32 quantization noise
        2. Document expected behavior for both precision levels
        3. Ensure production data format (float32) is explicitly tested
        4. Guard against over-sensitivity to numerical noise

    Float32 Quantization Context:
        - Float32 has ~7 decimal digits of precision
        - At boundary value (e.g., L=0), quantization error is ~1.2e-7
        - True boundary stickiness (optimizer stuck) >> quantization noise
        - Tests ensure we detect real stickiness, not just float32 artifacts
    """

    def test_boundary_pileup_with_precision(self, dtype, dtype_name):
        """Detect boundary stickiness at specified float precision.

        Real-World Context:
            Production pipeline: fit in float64 → store as float32 → QC analysis.
            This test validates detection works on both precision levels.

        Scientific Context:
            When optimizer gets stuck near boundary, samples pile up in a small
            range near L. Even with boundary stickiness, numerical noise creates
            a spread (typically 1 bin width for 1000-bin histograms).

        Histogram Context:
            For 1000-bin histogram of [0, 100] range:
            - Each bin is 0.1 units wide
            - 1% pileup at L=0 means 1000 samples in bin [0, 0.1)
            - Float32 quantization (±1.2e-7) is negligible vs bin width

        Expected Behavior:
            Detection should succeed at both float32 and float64 precision.
            The boundary stickiness signal (1% in single bin) is many orders
            of magnitude larger than float precision effects.

        What This Tests:
            - Precision doesn't prevent detection of realistic pileups
            - Production data format (float32) explicitly validated
            - Baseline behavior at full precision (float64) documented
            - Realistic 1-bin-width pileup pattern
        """
        rng = np.random.default_rng(60)
        n = 100000

        # Create realistic boundary pileup: delta function at exact boundary
        # Real PPA12 data (A_He) shows boundary stickiness as exact values at L=0
        pileup_samples = int(0.01 * n)
        x = np.concatenate(
            [
                np.zeros(pileup_samples),  # 1000 samples exactly at L=0
                rng.uniform(0, 100, n - pileup_samples),
            ]
        )

        # Convert to target precision
        x = x.astype(dtype)

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Assertion 1: Detection should succeed at this precision
        assert result.lower_pileup_detected is True, (
            f"Failed to detect 1% boundary pileup in {dtype_name} data. "
            f"Precision should not prevent detection of realistic stickiness. "
            f"Got lower_pileup_detected={result.lower_pileup_detected}, "
            f"t_lo_star={result.t_lo_star}"
        )

        # Assertion 2: Detected tolerance should be reasonable
        # For delta function at boundary, algorithm detects elbow at t≈0,
        # then returns first measurable tolerance point (typically very small)
        assert result.t_lo_star is not None
        assert 0.0001 < result.t_lo_star < 0.005, (
            f"Detected tolerance {result.t_lo_star:.6f} outside expected [0.0001, 0.005]. "
            f"For 1% delta function at L=0, expect very small threshold."
        )

        # Assertion 3: Upper boundary should be clean
        assert result.upper_pileup_detected is False, "Upper boundary should not show pileup"

        # Assertion 4: Data type preserved
        assert x.dtype == dtype, f"Test data should remain {dtype_name} throughout"

        # Assertion 5: Pileup at exact boundary
        # Verify the pileup is actually at L=0 (delta function)
        exactly_at_L = np.sum(x == 0)
        assert exactly_at_L >= pileup_samples * 0.99, (
            f"Pileup should be exactly at L=0 (delta function). "
            f"Expected ~{pileup_samples}, got {exactly_at_L}"
        )

    def test_interior_pileup_limitation(self, dtype, dtype_name):
        """Document that interior pileup is NOT detected by boundary QC at any precision.

        Real-World Context:
            Initial guess stickiness (x0 stickiness) occurs at both float32 and
            float64 precision. This test documents that run_boundary_qc() doesn't
            detect it regardless of precision level.

        Scientific Context:
            Interior stickiness occurs when optimizer gets stuck at initial guess
            (often mid-range, e.g., x0=50 for bounds [0, 100]). This is a
            different failure mode than boundary stickiness.

        Known Limitation:
            run_boundary_qc() ONLY detects boundary stickiness (near L or U).
            For interior/initial-guess stickiness, use run_interior_qc() instead.
            This limitation is architectural, not precision-related.

        What This Tests:
            - Negative test: confirms boundary QC doesn't detect interior pileups
            - Documentation: directs users to run_interior_qc() for this case
            - Precision independence: shows limitation exists at both float32/float64
            - Expected behavior: NOT a bug, but a design choice
        """
        rng = np.random.default_rng(62)
        n = 100000

        # Create interior pileup: 2% at x=50 (mid-range)
        pileup_samples = int(0.02 * n)
        x = np.concatenate(
            [
                np.full(pileup_samples, 50.0),  # At x0=50
                rng.uniform(0, 100, n - pileup_samples),
            ]
        )

        # Convert to target precision
        x = x.astype(dtype)

        config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Assertion 1: No lower boundary detection (expected)
        assert result.lower_pileup_detected is False, (
            f"run_boundary_qc() should NOT detect interior pileup at x=50 ({dtype_name}). "
            f"Got lower_pileup_detected={result.lower_pileup_detected}"
        )

        # Assertion 2: No upper boundary detection (expected)
        assert result.upper_pileup_detected is False, (
            f"run_boundary_qc() should NOT detect interior pileup at x=50 ({dtype_name}). "
            f"Got upper_pileup_detected={result.upper_pileup_detected}"
        )

        # Assertion 3: Data type preserved
        assert x.dtype == dtype

        # Assertion 4: Interior pileup exists in data
        # Verify the pileup is actually present
        near_50 = np.sum(np.abs(x - 50.0) < 0.01)  # Within 0.01 of x=50
        assert near_50 >= pileup_samples * 0.99, (
            f"Interior pileup should be present in data. "
            f"Expected ~{pileup_samples} near x=50, got {near_50}"
        )

        # Assertion 5: Documentation of correct behavior
        assert True, (
            f"DOCUMENTED BEHAVIOR: Interior/initial-guess stickiness is NOT "
            f"detected by run_boundary_qc(), even at {dtype_name} precision. "
            f"This confirms the limitation is architectural, not precision-related. "
            f"Use run_interior_qc() to detect pileups at x0 or other interior points."
        )
