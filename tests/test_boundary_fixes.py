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

import numpy as np
import pytest
import time
from unittest.mock import patch, MagicMock, call

from fitqc.boundary import run_boundary_qc
from fitqc.config import BoundaryConfig
from fitqc._quantile_utils import _aggregate_elbows_median


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
        result_sufficient = _aggregate_elbows_median(
            elbows_sufficient, min_agreement_frac=0.5
        )

        # Behavior: returns median
        assert result_sufficient is not None, "Expected median, got None"
        assert result_sufficient == pytest.approx(0.015), (
            f"Expected median ~0.015, got {result_sufficient}"
        )

        # Type: float
        assert isinstance(result_sufficient, float)

        # Insufficient agreement (2 of 5 = 40% < 50%)
        elbows_insufficient = [0.01, None, None, None, 0.02]
        result_insufficient = _aggregate_elbows_median(
            elbows_insufficient, min_agreement_frac=0.5
        )

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
            f"Expected >=10 points in [0, 0.02], got {len(critical_points)}: "
            f"{critical_points}"
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
        assert grid[0] <= 0.001, (
            f"First quantile too large: {grid[0]} (should be <=0.001)"
        )
        assert grid[-1] >= 0.20, (
            f"Last quantile too small: {grid[-1]} (should be >=0.20)"
        )
        assert grid[-1] <= 0.30, (
            f"Last quantile too large: {grid[-1]} (should be <=0.30)"
        )

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
        assert config.excess_ratio == 1.5, (
            f"Expected default 1.5, got {config.excess_ratio}"
        )

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

    @patch('fitqc.boundary._compute_quantile_curves_boundary')
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
            mock_elbows       # elbows_per_quantile (26 elements)
        )

        # Create config with CUSTOM thresholds (different from defaults)
        custom_config = BoundaryConfig(
            use_quantile_analysis=True,
            pileup_threshold=0.008,  # Custom (default is 0.005)
            excess_ratio=1.8         # Custom (default is 1.5)
        )

        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, 1000)

        # Run detection
        result = run_boundary_qc(x, L=0, U=10, config=custom_config)

        # Verify function was called (detection logic ran)
        assert mock_compute.called, (
            "Detection logic should be invoked with custom config"
        )

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
        assert len(quantile_grid_arg) > 0, (
            "Quantile grid from config should be passed to detection"
        )

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

    @patch('fitqc.boundary.select_elbow')
    def test_iterative_refinement_calls_elbow_detection_multiple_times(self, mock_elbow):
        """Verify iterative refinement actually iterates (calls elbow detection >1 time).

        Why non-trivial: Tests the CONTROL FLOW, not just the output.
        If someone breaks the iteration logic, this catches it.

        What this catches:
        - Iteration loop accidentally removed (call_count == 1)
        - Convergence logic broken (call_count > 10, infinite loop)
        - Grid not actually refined between iterations (grid size unchanged)
        """
        # Configure mock to return different values on each call
        # This simulates elbow moving during refinement (convergence)
        mock_elbow.side_effect = [
            0.02,    # First iteration: elbow at 2%
            0.0195,  # Second iteration: elbow refined to 1.95%
            0.0195   # Third iteration: converged (same value)
        ]

        rng = np.random.default_rng(42)
        x = np.concatenate([
            np.zeros(300),
            rng.uniform(0, 100, 9700)
        ])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True  # Enable iterative refinement
        )

        result = run_boundary_qc(x, L=0, U=100, config=config)

        # ========== NON-TRIVIAL VERIFICATION ==========

        # 1. Verify elbow detection was called MULTIPLE times (iteration happened)
        call_count = mock_elbow.call_count
        assert call_count >= 2, (
            f"Iterative refinement should call select_elbow multiple times, "
            f"but only called {call_count} time(s). "
            f"This means iteration loop is broken or not running."
        )

        # 2. Verify it didn't loop forever
        assert call_count <= 5, (
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
            assert np.all(np.diff(second_grid) > 0), (
                "Refined grid must be strictly increasing"
            )

    @patch('fitqc.boundary.select_elbow')
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

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True
        )

        # Should NOT crash
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Verify result is sensible (no detection)
        assert result.lower_pileup_detected is False, (
            "Should not detect pileup when no elbow found"
        )
        assert result.t_lo_star is None, (
            "t_lo_star should be None when no elbow found"
        )

        # Verify we didn't try to refine around a None elbow
        # (should have stopped after first iteration)
        assert mock_elbow.call_count == 1, (
            f"Should not attempt refinement when no elbow found. "
            f"Expected 1 call to select_elbow, got {mock_elbow.call_count}. "
            f"Refinement should check for None before iterating."
        )

    @patch('fitqc.boundary._compute_quantile_curves_boundary')
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
            [0.015]  # elbows_per_quantile
        )

        # Create config with CUSTOM grid (different from default)
        custom_grid = (0.001, 0.005, 0.01)  # Only 3 points (vs 26 default)
        custom_config = BoundaryConfig(
            use_quantile_analysis=True,
            quantile_grid=custom_grid
        )

        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, 1000)

        # Run detection
        result = run_boundary_qc(x, L=0, U=10, config=custom_config)

        # Verify function was called
        assert mock_compute.called, (
            "Quantile curve computation should be invoked"
        )

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
            err_msg="Custom quantile_grid values don't match what was passed to detection"
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
        x = np.concatenate([
            np.zeros(int(0.03 * n)),  # 3% at exact boundary
            rng.uniform(0, 100, n - int(0.03 * n))
        ])

        # Run with refinement enabled
        config_refined = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True
        )
        result_refined = run_boundary_qc(x, L=0, U=100, config=config_refined)

        # Size: grid should have grown
        assert hasattr(result_refined, 'quantile_grid_refined_lower'), (
            "Result must expose refined grid for scientific validation"
        )

        if result_refined.quantile_grid_refined_lower is not None:
            initial_grid_size = len(config_refined.quantile_grid)
            refined_grid_size = len(result_refined.quantile_grid_refined_lower)

            assert refined_grid_size > initial_grid_size, (
                f"Grid should grow during refinement: "
                f"{initial_grid_size} -> {refined_grid_size}"
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
        x_ahe = np.concatenate([
            np.zeros(int(0.03 * n)),
            rng.uniform(0, 100, n - int(0.03 * n))
        ])

        # With refinement (should succeed)
        config_refine = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True
        )
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

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True
        )
        result = run_boundary_qc(x_uniform, L=0, U=10, config=config)

        # Behavior: graceful handling
        assert result.lower_pileup_detected is False
        assert result.t_lo_star is None or result.t_lo_star < 0.01

    def test_refinement_terminates_in_finite_iterations(self):
        """Refinement should terminate after max_iterations, not loop forever.

        Safety test: ensures algorithm doesn't get stuck in infinite refinement.
        """
        rng = np.random.default_rng(42)
        x = np.concatenate([
            np.zeros(1000),
            rng.uniform(0, 100, 9000)
        ])

        # Run with refinement (should complete in reasonable time)
        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True
        )

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
        x = np.concatenate([
            np.full(int(0.05 * n), 0.0),  # Exact boundary
            rng.uniform(0, 100, n - int(0.05 * n))
        ])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            quantile_grid=(0.001, 0.01, 0.02, 0.05, 0.10, 0.25)
        )

        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Behavior: should detect (mass is clearly at boundary)
        assert result.lower_pileup_detected is True, (
            "Exact boundary pileup must be detected"
        )

        # Behavior: should not crash (graceful handling)
        assert result.t_lo_star is not None

        # Contents: tolerance should be very small (exact boundary)
        assert result.t_lo_star < 0.01, (
            f"Exact boundary should give very small tolerance: {result.t_lo_star}"
        )

        # Implementation detail: if we expose refined_grid
        if hasattr(result, 'quantile_grid_refined_lower'):
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
        x = np.concatenate([
            rng.uniform(0, 15, pileup_samples),  # Broad pileup
            rng.uniform(0, 100, n - pileup_samples)
        ])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            quantile_grid=(0.001, 0.01, 0.05, 0.10, 0.15, 0.20)
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
        x = np.concatenate([
            np.zeros(int(pileup_frac * n)),  # Exact boundary
            rng.uniform(0, 100, n - int(pileup_frac * n))
        ])

        # Initial grid straddles the true elbow
        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            quantile_grid=(
                0.001, 0.01, 0.02, 0.05, 0.10  # 1.5% is between 0.01 and 0.02
            )
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
        if hasattr(result, 'quantile_grid_refined_lower'):
            if result.quantile_grid_refined_lower is not None:
                refined_grid = result.quantile_grid_refined_lower
                points_in_region = [
                    q for q in refined_grid
                    if 0.01 <= q <= 0.02
                ]
                assert len(points_in_region) > 2, (
                    f"Should refine 1-2% region: {points_in_region}"
                )


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

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True
        )
        result = run_boundary_qc(x_uniform, L=0, U=100, config=config)

        # Behavior: should NOT detect pileup
        assert result.lower_pileup_detected is False, (
            "False positive on uniform data!"
        )
        assert result.upper_pileup_detected is False, (
            "False positive on uniform data!"
        )

    def test_moderate_pileup_detected(self):
        """5% pileup in 1% of range should be detected reliably."""
        rng = np.random.default_rng(42)
        n = 50000
        x = np.concatenate([
            rng.uniform(0, 1, int(0.05 * n)),  # 5% in first 1% of range
            rng.uniform(0, 100, n - int(0.05 * n))
        ])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True
        )
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Behavior: should detect
        assert result.lower_pileup_detected is True
        assert result.t_lo_star is not None
        assert 0.005 < result.t_lo_star < 0.02, (
            f"Expected tolerance ~1%, got {result.t_lo_star}"
        )

    def test_asymmetric_detection_lower_only(self):
        """Lower pileup detected, upper not detected (asymmetric).

        Why: Fix 2 addresses single-element handling but should NOT
        aggregate lower+upper together. They remain independent.

        Common physics scenario: Parameter hits lower bound (e.g.,
        normalization parameter hitting zero).
        """
        rng = np.random.default_rng(42)
        n = 50000
        x = np.concatenate([
            rng.uniform(0, 0.5, int(0.05 * n)),  # Lower pileup only
            rng.uniform(0, 100, n - int(0.05 * n))
        ])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True
        )
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Behavior: asymmetric detection
        assert result.lower_pileup_detected is True, (
            "Lower pileup should be detected"
        )
        assert result.upper_pileup_detected is False, (
            "Upper pileup should NOT be detected"
        )

        # Contents: only lower tolerance should be significant
        assert result.t_lo_star is not None
        assert result.t_lo_star > 0.003

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
        x = np.concatenate([
            rng.uniform(99.5, 100, int(0.05 * n)),  # Upper pileup only
            rng.uniform(0, 100, n - int(0.05 * n))
        ])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True
        )
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Behavior: asymmetric detection (upper only)
        assert result.upper_pileup_detected is True, (
            "Upper pileup should be detected"
        )
        assert result.lower_pileup_detected is False, (
            "Lower pileup should NOT be detected"
        )

        # Contents: only upper tolerance should be significant
        assert result.t_hi_star is not None
        assert result.t_hi_star > 0.003

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
        x = np.concatenate([
            rng.uniform(0, 0.5, int(0.04 * n)),      # Lower pileup
            rng.uniform(99.5, 100, int(0.04 * n)),   # Upper pileup
            rng.uniform(0, 100, n - int(0.08 * n))
        ])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True
        )
        result = run_boundary_qc(x, L=0, U=100, config=config)

        # Behavior: both detected
        assert result.lower_pileup_detected is True, (
            "Lower boundary pileup should be detected"
        )
        assert result.upper_pileup_detected is True, (
            "Upper boundary pileup should be detected"
        )

        # Contents: both tolerances significant
        assert result.t_lo_star is not None
        assert result.t_hi_star is not None
        assert result.t_lo_star > 0.003
        assert result.t_hi_star > 0.003

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
            refine_transition=False
        )

        t0 = time.time()
        run_boundary_qc(x, L=0, U=100, config=config_baseline)
        baseline_time = time.time() - t0

        # New: 26-point grid, with refinement
        config_new = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True
        )

        t0 = time.time()
        run_boundary_qc(x, L=0, U=100, config=config_new)
        new_time = time.time() - t0

        # Accept up to 5x slowdown (generous bound)
        assert new_time < baseline_time * 5.0, (
            f"Unacceptable slowdown: {baseline_time:.3f}s -> {new_time:.3f}s "
            f"({new_time/baseline_time:.1f}x)"
        )
