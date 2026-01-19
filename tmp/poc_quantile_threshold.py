"""Proof-of-concept: Quantile-based multi-curve threshold detection.

This module validates whether quantile-based multi-curve analysis improves
threshold detection for both boundary pileup (linear space) and interior
spikes (log space) compared to the current single-curve approach.

The key insight is that for data with boundary pileup, the relationship between
quantiles and their threshold values changes sharply at the true threshold,
creating an elbow that may be more robust than analyzing the mass curve alone.
"""

from typing import Any

import numpy as np
from numpy.typing import NDArray

from fitqc.selection import select_elbow
from fitqc.sortedops import tail_mass


def compute_quantile_threshold_curves(
    data_sorted: NDArray[np.floating],
    grid: NDArray[np.floating],
    quantile_grid: NDArray[np.floating],
    log_space: bool = False,
) -> tuple[NDArray[np.floating], list[float | None], dict[str, Any]]:
    """Compute quantile-threshold curves for multi-curve threshold detection.

    For each quantile q in quantile_grid, finds the threshold value where
    P(X < threshold) = q. This creates a curve mapping quantiles to thresholds,
    which can reveal structural breaks in the data distribution.

    The key diagnostic is the elbow in the (quantile, threshold) relationship,
    which indicates where the data transitions from boundary pileup to interior
    values.

    Args:
        data_sorted: Pre-sorted data array (ascending order).
        grid: Threshold values to evaluate. Should span the relevant data range.
        quantile_grid: Quantile values to compute thresholds for, in [0, 1].
        log_space: If True, work in log-space for threshold grid (useful for
            detecting interior spikes in log-transformed data).

    Returns:
        A tuple containing:
        - threshold_at_quantile: Array of threshold values achieving each quantile.
            Shape matches quantile_grid. threshold_at_quantile[i] is the threshold
            where P(X < threshold) = quantile_grid[i].
        - elbows: List containing detected elbow point(s) in the quantile-threshold
            curve, or [None] if no clear elbow found.
        - diagnostics: Dictionary with keys:
            - 'mass_curve': Array of P(X < threshold) for each threshold in grid
            - 'threshold_at_quantile': Same as first return value
            - 'ratio': threshold/quantile for each quantile (diagnostic for uniform data)
            - 'elbow_overall': Single elbow value (or None)

    Examples:
        >>> # Uniform data: threshold should be proportional to quantile
        >>> data = np.sort(np.random.uniform(0, 1, 1000))
        >>> grid = np.linspace(0, 1, 100)
        >>> quantile_grid = np.linspace(0.1, 0.9, 20)
        >>> thresh, elbows, diag = compute_quantile_threshold_curves(
        ...     data, grid, quantile_grid
        ... )
        >>> # For uniform data, ratio should be ~1
        >>> assert np.allclose(diag['ratio'], 1.0, atol=0.1)

        >>> # Data with boundary pileup: elbow at true threshold
        >>> data_pileup = np.concatenate([np.zeros(500), np.random.uniform(0, 1, 500)])
        >>> data_pileup = np.sort(data_pileup)
        >>> thresh, elbows, diag = compute_quantile_threshold_curves(
        ...     data_pileup, grid, quantile_grid
        ... )
        >>> # Should detect elbow near quantile 0.5
    """
    if len(data_sorted) == 0:
        # Handle empty data edge case
        n_quantiles = len(quantile_grid)
        return (
            np.full(n_quantiles, np.nan),
            [None],
            {
                "mass_curve": np.array([]),
                "threshold_at_quantile": np.full(n_quantiles, np.nan),
                "ratio": np.full(n_quantiles, np.nan),
                "elbow_overall": None,
            },
        )

    # Step 1: Compute mass curve - P(X < threshold) for each threshold in grid
    mass_curve = np.array([tail_mass(data_sorted, threshold) for threshold in grid])

    # Step 2: For each quantile, find the threshold where mass = quantile
    # Use linear interpolation to find threshold(quantile)
    threshold_at_quantile = np.interp(
        quantile_grid,
        mass_curve,  # x values (must be monotonic)
        grid,  # y values
    )

    # Step 3: Detect elbow in (quantile, threshold) relationship
    # For data with boundary pileup, this curve will have a sharp transition
    # when we move from the pileup region to the interior values
    elbow_overall = select_elbow(
        quantile_grid,
        threshold_at_quantile,
        curve="concave",  # Expect concave shape: slow rise then fast rise
        direction="increasing",
        log_x=log_space,
    )

    # Step 4: Compute ratio = threshold/quantile for diagnostics
    # For uniform data on [0, 1], this ratio should be ~1
    # For data with boundary pileup at 0, ratio will be small before the elbow,
    # then larger after the elbow
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = threshold_at_quantile / quantile_grid
        # Handle division by zero or near-zero quantiles
        ratio = np.where(quantile_grid > 1e-10, ratio, np.nan)

    # Package results
    diagnostics = {
        "mass_curve": mass_curve,
        "threshold_at_quantile": threshold_at_quantile,
        "ratio": ratio,
        "elbow_overall": elbow_overall,
    }

    return threshold_at_quantile, [elbow_overall], diagnostics


def compare_single_vs_multi_curve(
    data_sorted: NDArray[np.floating],
    grid: NDArray[np.floating],
    quantile_grid: NDArray[np.floating],
    log_space: bool = False,
    true_threshold: float | None = None,
) -> dict[str, Any]:
    """Compare single-curve vs multi-curve quantile-based threshold detection.

    This function evaluates two approaches:
    1. Single-curve (current): Find elbow in the mass curve P(X < threshold)
    2. Multi-curve (proposed): Find elbow in quantile-threshold relationship

    The multi-curve approach may be more robust for data with boundary pileup
    because it explicitly tracks how quantiles map to thresholds, making the
    structural break more apparent.

    Args:
        data_sorted: Pre-sorted data array (ascending order).
        grid: Threshold values to evaluate.
        quantile_grid: Quantile values for multi-curve analysis, in [0, 1].
        log_space: If True, work in log-space for threshold detection.
        true_threshold: Optional ground truth threshold for error computation.

    Returns:
        Dictionary with keys:
            - 'single_curve_elbow': Elbow from single-curve approach (float or None)
            - 'multi_curve_elbow': Elbow from multi-curve approach (float or None)
            - 'quantile_ratios': Array of threshold/quantile ratios
            - 'diagnostics': Full diagnostics from compute_quantile_threshold_curves
            - 'single_error': Absolute error if true_threshold provided (float or None)
            - 'multi_error': Absolute error if true_threshold provided (float or None)
            - 'mass_curve': Mass curve for single-curve approach

    Examples:
        >>> # Compare on uniform data
        >>> data = np.sort(np.random.uniform(0, 1, 1000))
        >>> grid = np.linspace(0, 1, 100)
        >>> quantile_grid = np.linspace(0.1, 0.9, 20)
        >>> results = compare_single_vs_multi_curve(data, grid, quantile_grid)
        >>> # Uniform data may not have clear elbows
        >>> print(f"Single: {results['single_curve_elbow']}")
        >>> print(f"Multi: {results['multi_curve_elbow']}")

        >>> # Compare on data with boundary pileup
        >>> data_pileup = np.concatenate([np.zeros(500), np.random.uniform(0, 1, 500)])
        >>> data_pileup = np.sort(data_pileup)
        >>> results = compare_single_vs_multi_curve(
        ...     data_pileup, grid, quantile_grid, true_threshold=0.01
        ... )
        >>> print(f"Single error: {results['single_error']}")
        >>> print(f"Multi error: {results['multi_error']}")
    """
    if len(data_sorted) == 0:
        # Handle empty data edge case
        return {
            "single_curve_elbow": None,
            "multi_curve_elbow": None,
            "quantile_ratios": np.array([]),
            "diagnostics": {},
            "single_error": None,
            "multi_error": None,
            "mass_curve": np.array([]),
        }

    # Approach 1: Single-curve (current approach)
    # Compute mass curve and find elbow in (threshold, mass) space
    mass_curve = np.array([tail_mass(data_sorted, threshold) for threshold in grid])

    single_curve_elbow = select_elbow(
        grid,
        mass_curve,
        curve="concave",  # Mass curve is concave (accelerating increase)
        direction="increasing",
        log_x=log_space,
    )

    # Approach 2: Multi-curve (proposed approach)
    # Compute quantile-threshold curves and find elbow
    threshold_at_quantile, elbows, diagnostics = compute_quantile_threshold_curves(
        data_sorted, grid, quantile_grid, log_space=log_space
    )

    multi_curve_elbow = elbows[0] if elbows else None

    # Compute errors if ground truth provided
    single_error = None
    multi_error = None

    if true_threshold is not None:
        if single_curve_elbow is not None:
            single_error = abs(single_curve_elbow - true_threshold)
        if multi_curve_elbow is not None:
            # multi_curve_elbow is in quantile space, need to convert to threshold
            # Actually, looking back at the code, elbow_overall from compute_quantile_threshold_curves
            # is the x-value (quantile) where the elbow occurs. We need the corresponding threshold.
            if multi_curve_elbow is not None:
                # Find the threshold at the elbow quantile
                elbow_threshold = np.interp(
                    multi_curve_elbow, quantile_grid, threshold_at_quantile
                )
                multi_error = abs(elbow_threshold - true_threshold)

    # Package results
    results = {
        "single_curve_elbow": single_curve_elbow,
        "multi_curve_elbow": multi_curve_elbow,
        "quantile_ratios": diagnostics.get("ratio", np.array([])),
        "diagnostics": diagnostics,
        "single_error": single_error,
        "multi_error": multi_error,
        "mass_curve": mass_curve,
    }

    return results


# ============================================================================
# Basic validation tests
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("POC: Quantile-based Multi-curve Threshold Detection")
    print("=" * 80)

    # Test 1: Uniform data - ratio should be ~1
    print("\nTest 1: Uniform data [0, 1]")
    print("-" * 80)
    np.random.seed(42)
    data_uniform = np.sort(np.random.uniform(0, 1, 1000))
    grid = np.linspace(0, 1, 100)
    quantile_grid = np.linspace(0.1, 0.9, 20)

    thresh, elbows, diag = compute_quantile_threshold_curves(
        data_uniform, grid, quantile_grid
    )

    print(f"Quantile grid: {quantile_grid[:5]} ... {quantile_grid[-5:]}")
    print(f"Threshold at quantile: {thresh[:5]} ... {thresh[-5:]}")
    print(f"Ratio (threshold/quantile): {diag['ratio'][:5]} ... {diag['ratio'][-5:]}")
    print(f"Mean ratio: {np.nanmean(diag['ratio']):.3f} (expected ~1.0 for uniform)")
    print(f"Std ratio: {np.nanstd(diag['ratio']):.3f}")
    print(f"Elbow detected: {elbows[0]}")

    # Test 2: Data with boundary pileup at 0
    print("\n\nTest 2: Data with 50% boundary pileup at 0")
    print("-" * 80)
    data_pileup = np.concatenate([np.zeros(500), np.random.uniform(0, 1, 500)])
    data_pileup = np.sort(data_pileup)

    thresh_pileup, elbows_pileup, diag_pileup = compute_quantile_threshold_curves(
        data_pileup, grid, quantile_grid
    )

    print(f"Quantile grid: {quantile_grid[:5]} ... {quantile_grid[-5:]}")
    print(
        f"Threshold at quantile: {thresh_pileup[:5]} ... {thresh_pileup[-5:]}"
    )
    print(
        f"Ratio (threshold/quantile): {diag_pileup['ratio'][:5]} ... {diag_pileup['ratio'][-5:]}"
    )
    print(
        f"Mean ratio (q < 0.5): {np.nanmean(diag_pileup['ratio'][quantile_grid < 0.5]):.3f}"
    )
    print(
        f"Mean ratio (q >= 0.5): {np.nanmean(diag_pileup['ratio'][quantile_grid >= 0.5]):.3f}"
    )
    print(f"Elbow detected at quantile: {elbows_pileup[0]}")
    if elbows_pileup[0] is not None:
        elbow_threshold = np.interp(
            elbows_pileup[0], quantile_grid, thresh_pileup
        )
        print(f"Corresponding threshold: {elbow_threshold:.6f}")

    # Test 3: Compare single vs multi-curve
    print("\n\nTest 3: Single-curve vs Multi-curve comparison (boundary pileup)")
    print("-" * 80)
    true_threshold = 0.01  # Small threshold to separate pileup from interior
    results = compare_single_vs_multi_curve(
        data_pileup, grid, quantile_grid, true_threshold=true_threshold
    )

    print(f"True threshold: {true_threshold}")
    print(f"Single-curve elbow (threshold): {results['single_curve_elbow']}")
    print(f"Multi-curve elbow (quantile): {results['multi_curve_elbow']}")
    if results['multi_curve_elbow'] is not None:
        multi_thresh = np.interp(
            results['multi_curve_elbow'],
            quantile_grid,
            results['diagnostics']['threshold_at_quantile'],
        )
        print(f"Multi-curve elbow (threshold): {multi_thresh:.6f}")
    print(f"Single-curve error: {results['single_error']}")
    print(f"Multi-curve error: {results['multi_error']}")

    # Test 4: Edge case - empty data
    print("\n\nTest 4: Edge case - empty data")
    print("-" * 80)
    data_empty = np.array([])
    thresh_empty, elbows_empty, diag_empty = compute_quantile_threshold_curves(
        data_empty, grid, quantile_grid
    )
    print(f"Threshold at quantile: {thresh_empty}")
    print(f"Elbows: {elbows_empty}")
    print(f"All NaN as expected: {np.all(np.isnan(thresh_empty))}")

    print("\n" + "=" * 80)
    print("All tests completed successfully!")
    print("=" * 80)
