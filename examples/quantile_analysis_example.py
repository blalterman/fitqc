"""Example showing single-curve vs multi-curve threshold detection.

This example demonstrates the difference between the default single-curve
detection and the optional multi-curve quantile-based detection for both
boundary and interior stickiness.

Multi-curve detection is particularly useful for:
- Very tight boundary pileups (< 0.5% of range)
- Very tight interior spikes (< 1e-8 width)
- Datasets where you want maximum robustness via median aggregation
"""

import numpy as np

from fitqc import detect_stickiness
from fitqc.config import BoundaryConfig, InteriorConfig


def example_boundary_detection():
    """Example of boundary detection with progressive grid and quantile analysis."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Boundary Detection with Progressive Grid")
    print("=" * 70)

    # Generate data with tight lower boundary pileup (0.3% of range)
    n_total = 10000
    n_stuck = 500  # 5% stuck at lower bound
    pileup_width = 0.003  # Very tight: 0.3% of range

    x_stuck = np.random.uniform(0.0, pileup_width, n_stuck)
    x_normal = np.random.uniform(0.0, 1.0, n_total - n_stuck)
    data = np.concatenate([x_stuck, x_normal])

    # Single-curve detection (default)
    print("\nRunning single-curve detection (default)...")
    result_single = detect_stickiness(data, mode="boundary", L=0.0, U=1.0, config=None)

    print(f"  Lower pileup detected: {result_single['boundary'].lower_pileup_detected}")
    print(f"  Threshold t_lo*: {result_single['boundary'].t_lo_star}")

    # Multi-curve detection with progressive grid
    print("\nRunning multi-curve detection with progressive grid...")
    config_boundary = BoundaryConfig(
        grid_mode="progressive",
        use_quantile_analysis=True,
        quantile_grid=(0.001, 0.005, 0.01, 0.02, 0.05),
    )

    result_multi = detect_stickiness(data, mode="boundary", L=0.0, U=1.0, config=config_boundary)

    print(f"  Lower pileup detected: {result_multi['boundary'].lower_pileup_detected}")
    print(f"  Threshold t_lo*: {result_multi['boundary'].t_lo_star}")

    if result_multi["boundary"].quantile_elbows:
        print("\n  Quantile elbows (lower boundary):")
        for q, elbow in result_multi["boundary"].quantile_elbows["lower"].items():
            print(f"    q={q:.3f} -> elbow at tol={elbow}")


def example_interior_detection():
    """Example of interior detection with quantile analysis."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Interior Detection with Quantile Analysis")
    print("=" * 70)

    # Generate data with tight spike at x0
    n_total = 10000
    n_stuck = 300  # 3% stuck at x0
    x0 = 0.5
    spike_width = 1e-8  # Very tight spike

    x_stuck = np.random.uniform(x0 - spike_width, x0 + spike_width, n_stuck)
    x_normal = np.random.uniform(0.0, 1.0, n_total - n_stuck)
    data = np.concatenate([x_stuck, x_normal])

    # Single-curve detection (default)
    print("\nRunning single-curve detection (default)...")
    result_single = detect_stickiness(data, mode="interior", x0=x0, L=0.0, U=1.0, config=None)

    print(f"  Spike detected: {result_single['interior'].spike_detected}")
    print(f"  Threshold eps*: {result_single['interior'].eps_star}")

    # Multi-curve detection
    print("\nRunning multi-curve detection...")
    config_interior = InteriorConfig(use_quantile_analysis=True, quantile_grid=(0.001, 0.01, 0.05))

    result_multi = detect_stickiness(
        data, mode="interior", x0=x0, L=0.0, U=1.0, config=config_interior
    )

    print(f"  Spike detected: {result_multi['interior'].spike_detected}")
    print(f"  Threshold eps*: {result_multi['interior'].eps_star}")

    if result_multi["interior"].quantile_elbows:
        print("\n  Quantile elbows:")
        for q, elbow in result_multi["interior"].quantile_elbows.items():
            print(f"    q={q:.3f} -> elbow at eps={elbow}")


def example_combined_detection():
    """Example showing both boundary and interior detection together."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Combined Boundary + Interior Detection")
    print("=" * 70)

    # Generate data with BOTH boundary pileup AND x0 spike
    n_total = 10000
    n_boundary = 300  # 3% at lower bound
    n_spike = 200  # 2% at x0
    x0 = 0.5

    x_boundary = np.random.uniform(0.0, 0.005, n_boundary)
    x_spike = np.full(n_spike, x0)  # Exactly at x0
    x_normal = np.random.uniform(0.0, 1.0, n_total - n_boundary - n_spike)
    data = np.concatenate([x_boundary, x_spike, x_normal])

    # Configure both detectors with quantile analysis
    config_boundary = BoundaryConfig(
        grid_mode="progressive",
        use_quantile_analysis=True,
        quantile_grid=(0.001, 0.005, 0.01, 0.02, 0.05),
    )

    config_interior = InteriorConfig(use_quantile_analysis=True, quantile_grid=(0.001, 0.01, 0.05))

    # Run combined detection
    print("\nRunning combined detection with multi-curve analysis...")
    result = detect_stickiness(
        data,
        mode="both",
        x0=x0,
        L=0.0,
        U=1.0,
        config_boundary=config_boundary,
        config_interior=config_interior,
    )

    # Boundary results
    print("\nBoundary Detection:")
    print(f"  Lower pileup: {result['boundary'].lower_pileup_detected}")
    print(f"  Upper pileup: {result['boundary'].upper_pileup_detected}")
    print(f"  t_lo*: {result['boundary'].t_lo_star}")
    print(f"  t_hi*: {result['boundary'].t_hi_star}")

    # Interior results
    print("\nInterior Detection:")
    print(f"  Spike detected: {result['interior'].spike_detected}")
    print(f"  eps*: {result['interior'].eps_star}")

    # Overall assessment
    has_issues = (
        result["boundary"].lower_pileup_detected
        or result["boundary"].upper_pileup_detected
        or result["interior"].spike_detected
    )

    print("\nOverall Assessment:")
    if has_issues:
        print("  WARNING: Stickiness detected! Investigate optimizer settings.")
    else:
        print("  OK: No stickiness detected.")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("QUANTILE-BASED STICKINESS DETECTION EXAMPLES")
    print("=" * 70)
    print("\nThese examples demonstrate the new multi-curve quantile analysis features")
    print("for both boundary and interior stickiness detection.")

    # Set random seed for reproducibility
    np.random.seed(42)

    # Run examples
    example_boundary_detection()
    example_interior_detection()
    example_combined_detection()

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
