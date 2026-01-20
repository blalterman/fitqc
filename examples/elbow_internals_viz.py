"""Example: Visualizing Elbow Detection Internals

Demonstrates plot_kneedle_internals() and plot_quantile_elbows_detailed()
for understanding how the Kneedle algorithm detects elbow points.
"""

import numpy as np

from fitqc import (
    InteriorConfig,
    PlotConfig,
    run_interior_qc,
)
from fitqc.plot import plot_kneedle_internals, plot_quantile_elbows_detailed


def main():
    """Run elbow detection visualization examples."""

    print("=" * 60)
    print("Elbow Detection Internals Visualization Example")
    print("=" * 60)

    # Configure plotting
    plot_config = PlotConfig(dpi=150, cmap="viridis")

    # ===================================================================
    # Example 1: Kneedle Internals on Synthetic Exponential Curve
    # ===================================================================
    print("\nExample 1: Kneedle internals on exponential saturation curve")
    print("-" * 60)

    x = np.linspace(0, 10, 100)
    y = 1 - np.exp(-x)  # Exponential saturation

    print(f"  Data: {len(x)} points from x=0 to x=10")
    print("  Curve: y = 1 - exp(-x)")

    fig1 = plot_kneedle_internals(
        x,
        y,
        curve="concave",
        direction="increasing",
        log_x=False,
        config=plot_config,
    )

    output_file1 = "elbow_internals_exponential.png"
    fig1.savefig(output_file1, bbox_inches="tight")
    print(f"  Saved: {output_file1}")

    # ===================================================================
    # Example 2: Interior QC with Quantile Analysis
    # ===================================================================
    print("\nExample 2: Interior QC with quantile elbow analysis")
    print("-" * 60)

    # Generate synthetic data with spike at x0=0.5
    rng = np.random.default_rng(42)
    n_spike = 500
    n_uniform = 9500

    x_spike = np.full(n_spike, 0.5)  # 5% stuck at x0
    x_uniform = rng.uniform(0.0, 1.0, n_uniform)
    data = np.concatenate([x_spike, x_uniform])

    print(f"  Data: {len(data)} samples (5% spike at x0=0.5)")

    # Run interior QC with quantile analysis
    interior_config = InteriorConfig(
        use_quantile_analysis=True,
        quantile_grid=(0.001, 0.005, 0.01, 0.02, 0.05, 0.10),
    )

    result = run_interior_qc(data, x0=0.5, L=0.0, U=1.0, config=interior_config)

    print(f"  Spike detected: {result.spike_detected}")
    if result.eps_star is not None:
        print(f"  Epsilon threshold (eps*): {result.eps_star:.2e}")

    # Visualize quantile elbows
    fig2 = plot_quantile_elbows_detailed(result, plot_config)
    output_file2 = "elbow_quantile_elbows_interior.png"
    fig2.savefig(output_file2, bbox_inches="tight")
    print(f"  Saved: {output_file2}")

    # Visualize Kneedle internals for mass curve
    fig3 = plot_kneedle_internals(
        result.eps_grid,
        result.mass_curve,
        curve="concave",
        direction="increasing",
        log_x=True,  # Epsilon is log-spaced
        config=plot_config,
    )
    output_file3 = "elbow_internals_mass_curve.png"
    fig3.savefig(output_file3, bbox_inches="tight")
    print(f"  Saved: {output_file3}")

    # ===================================================================
    # Example 3: Step Function (Edge Case)
    # ===================================================================
    print("\nExample 3: Step function (challenging edge case)")
    print("-" * 60)

    x_step = np.linspace(0, 10, 101)
    y_step = np.where(x_step < 5, 0.0, 1.0)

    print("  Data: Step function at x=5")

    fig4 = plot_kneedle_internals(
        x_step,
        y_step,
        curve="concave",
        direction="increasing",
        log_x=False,
        config=plot_config,
    )
    output_file4 = "elbow_internals_step_function.png"
    fig4.savefig(output_file4, bbox_inches="tight")
    print(f"  Saved: {output_file4}")

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
