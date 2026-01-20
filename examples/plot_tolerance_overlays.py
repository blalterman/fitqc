#!/usr/bin/env python
"""Example: Tolerance-overlay visualizations for boundary diagnostics.

This example demonstrates the tolerance-overlay visualization functions:
1. plot_histogram_tolerance_overlays - Shows histogram changes with tolerance cuts
2. plot_ecdf_tolerance_overlays - Shows ECDF changes near boundaries
3. plot_quantile_spacing_overlays - Shows quantile spacing compression

These visualizations help you understand how different tolerance thresholds
affect the detection of boundary pile-up in your fitted parameters.

Usage:
    python examples/plot_tolerance_overlays.py

Outputs:
    - histogram_tolerance_overlay.png
    - ecdf_tolerance_overlay.png
    - quantile_spacing_overlay.png
"""

import numpy as np

from fitqc.config import PlotConfig
from fitqc.plot import (
    plot_ecdf_tolerance_overlays,
    plot_histogram_tolerance_overlays,
    plot_quantile_spacing_overlays,
)
from fitqc.synth import generate_with_boundary_pileup


def main():
    """Demonstrate tolerance-overlay visualizations."""
    print("=" * 60)
    print("fitqc Example: Tolerance-Overlay Visualizations")
    print("=" * 60)
    print()

    # Generate synthetic data with boundary pile-up
    np.random.seed(42)
    n_samples = 5000
    L, U = 0.0, 10.0

    print(f"Generating {n_samples} samples with boundary pile-up...")
    x = generate_with_boundary_pileup(
        n=n_samples,
        L=L,
        U=U,
        lower_pileup_frac=0.15,  # 15% pile-up at lower boundary
        upper_pileup_frac=0.08,  # 8% pile-up at upper boundary
        seed=42,
    )
    print(f"  Bounds: [{L}, {U}]")
    print("  Lower pile-up: ~15% of samples")
    print("  Upper pile-up: ~8% of samples")
    print()

    # Configure plotting
    config = PlotConfig(
        dpi=150,  # Lower DPI for faster rendering in examples
        figsize_tolerance=(14, 6),
    )

    # Define tolerance levels to visualize
    tols = np.array([0.0, 0.01, 0.02, 0.03, 0.04, 0.05])
    print(f"Visualizing {len(tols)} tolerance levels: {tols}")
    print()

    # Example 1: Histogram tolerance overlays
    print("Creating histogram tolerance overlays...")
    fig1 = plot_histogram_tolerance_overlays(
        x=x,
        L=L,
        U=U,
        tols=tols,
        bins=80,
        config=config,
    )
    output1 = "histogram_tolerance_overlay.png"
    fig1.savefig(output1, bbox_inches="tight")
    print(f"  ✓ Saved to: {output1}")
    print("    Left panel:  Shows data after removing lower boundary samples")
    print("    Right panel: Shows data after removing upper boundary samples")
    print("    Notice how pile-up near boundaries 'disappears' as tolerance increases")
    print()

    # Example 2: ECDF tolerance overlays
    print("Creating ECDF tolerance overlays...")
    # Normalize to [0, 1]
    u = (x - L) / (U - L)
    fig2 = plot_ecdf_tolerance_overlays(
        u=u,
        tols=tols,
        side="both",  # Show both lower and upper boundaries
        config=config,
    )
    output2 = "ecdf_tolerance_overlay.png"
    fig2.savefig(output2, bbox_inches="tight")
    print(f"  ✓ Saved to: {output2}")
    print("    Left panel:  ECDF near lower boundary (u ≈ 0)")
    print("    Right panel: ECDF near upper boundary (u ≈ 1)")
    print("    Deviation from diagonal (y=x) indicates pile-up")
    print()

    # Example 3: Quantile spacing overlays
    print("Creating quantile spacing overlays...")
    x_sorted = np.sort(x)
    fig3 = plot_quantile_spacing_overlays(
        x_sorted=x_sorted,
        L=L,
        U=U,
        tols=tols,
        q_max=0.15,  # Show first 15% of quantiles
        n_quantiles=100,
        config=config,
    )
    output3 = "quantile_spacing_overlay.png"
    fig3.savefig(output3, bbox_inches="tight")
    print(f"  ✓ Saved to: {output3}")
    print("    Shows spacing between consecutive quantiles near lower tail")
    print("    Compressed spacing (low dq) indicates pile-up")
    print("    Higher tolerance removes pile-up → more uniform spacing")
    print()

    # Additional usage examples
    print("-" * 60)
    print("Advanced Usage Tips:")
    print("-" * 60)
    print()

    print("1. Custom tolerance ranges:")
    print("   tols = np.linspace(0, 0.1, 21)  # Finer grid, higher max")
    print()

    print("2. Focus on single boundary (ECDF):")
    print("   fig = plot_ecdf_tolerance_overlays(u, side='lower')")
    print("   fig = plot_ecdf_tolerance_overlays(u, side='upper')")
    print()

    print("3. Change colormap:")
    print("   config = PlotConfig(cmap='viridis')")
    print("   # Other options: 'plasma', 'coolwarm', 'RdYlBu_r'")
    print()

    print("4. Quantile spacing without bounds (for pre-filtered data):")
    print("   fig = plot_quantile_spacing_overlays(x_sorted)")
    print("   # All tolerance levels show same data")
    print()

    print("5. Adjust figure size:")
    print("   config = PlotConfig(figsize_tolerance=(16, 8))")
    print()

    print("=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
