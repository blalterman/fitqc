#!/usr/bin/env python
"""Example: Complete quantile-based detection and visualization workflow.

This example demonstrates the full workflow of combining quantile-based
stickiness detection with comprehensive visualization:

1. Generate synthetic data with BOTH x0 spike AND boundary pileup
2. Run interior QC with use_quantile_analysis=True
3. Run boundary QC with use_quantile_analysis=True
4. Visualize quantile elbow results with plot_quantile_elbow_overlay()
5. Create tolerance overlay visualizations for deeper diagnostics
6. Save all figures to files

This is the recommended workflow for thorough stickiness analysis when
you need both robust detection and visual confirmation of issues.

Usage:
    python examples/quantile_viz_workflow.py

Outputs:
    - quantile_viz_interior_diagnostics.png
    - quantile_viz_boundary_diagnostics.png
    - quantile_viz_interior_elbows.png
    - quantile_viz_boundary_elbows.png
    - quantile_viz_histogram_overlays.png
    - quantile_viz_ecdf_overlays.png
    - quantile_viz_spacing_overlays.png
"""

import numpy as np

from fitqc import (
    BoundaryConfig,
    InteriorConfig,
    PlotConfig,
    run_boundary_qc,
    run_interior_qc,
)
from fitqc.plot import (
    plot_boundary_diagnostics,
    plot_ecdf_tolerance_overlays,
    plot_histogram_tolerance_overlays,
    plot_interior_diagnostics,
    plot_quantile_elbow_overlay,
    plot_quantile_spacing_overlays,
)


def generate_mixed_pathology_data(
    n: int,
    L: float,
    U: float,
    x0: float,
    spike_frac: float = 0.03,
    lower_pileup_frac: float = 0.05,
    upper_pileup_frac: float = 0.02,
    seed: int = 42,
) -> np.ndarray:
    """Generate synthetic data with BOTH x0 spike AND boundary pileup.

    This creates a pathological dataset that exhibits multiple stickiness
    artifacts simultaneously - a realistic worst-case scenario when optimizer
    settings are misconfigured.

    Args:
        n: Total number of samples
        L: Lower bound
        U: Upper bound
        x0: Initial guess value (spike location)
        spike_frac: Fraction of samples stuck at x0
        lower_pileup_frac: Fraction stuck near lower bound
        upper_pileup_frac: Fraction stuck near upper bound
        seed: Random seed for reproducibility

    Returns:
        Array with mixed pathologies
    """
    rng = np.random.default_rng(seed)

    # Calculate sample counts
    n_spike = int(n * spike_frac)
    n_lower = int(n * lower_pileup_frac)
    n_upper = int(n * upper_pileup_frac)
    n_normal = n - n_spike - n_lower - n_upper

    range_width = U - L
    pileup_width = 0.005  # Very tight: 0.5% of range

    # Generate each component
    x_spike = np.full(n_spike, x0)  # Exactly at x0
    x_lower = rng.uniform(L, L + range_width * pileup_width, n_lower)
    x_upper = rng.uniform(U - range_width * pileup_width, U, n_upper)
    x_normal = rng.uniform(L, U, n_normal)

    # Combine and shuffle
    result = np.concatenate([x_spike, x_lower, x_upper, x_normal])
    rng.shuffle(result)

    return result


def print_section_header(title: str) -> None:
    """Print a formatted section header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def print_subsection(title: str) -> None:
    """Print a formatted subsection header."""
    print()
    print(f"--- {title} ---")
    print()


def main():
    """Run the complete quantile-based detection and visualization workflow."""
    print_section_header("fitqc: Quantile-Based Detection + Visualization Workflow")

    # =========================================================================
    # STEP 1: Generate synthetic data with mixed pathologies
    # =========================================================================
    print_subsection("Step 1: Generate Synthetic Data")

    n_samples = 10000
    L, U = 0.0, 10.0
    x0 = 5.0  # Initial guess in the middle of range

    print(f"Generating {n_samples} samples with mixed pathologies:")
    print(f"  - Bounds: [{L}, {U}]")
    print(f"  - Initial guess x0: {x0}")
    print("  - x0 spike: ~3% of samples")
    print("  - Lower boundary pileup: ~5% of samples (within 0.5% of L)")
    print("  - Upper boundary pileup: ~2% of samples (within 0.5% of U)")

    data = generate_mixed_pathology_data(
        n=n_samples,
        L=L,
        U=U,
        x0=x0,
        spike_frac=0.03,
        lower_pileup_frac=0.05,
        upper_pileup_frac=0.02,
        seed=42,
    )

    print(f"\nData generated: {len(data)} samples")
    print(f"  Range: [{data.min():.4f}, {data.max():.4f}]")
    print(f"  Mean: {data.mean():.4f}")
    print(f"  Samples exactly at x0: {np.sum(data == x0)}")

    # =========================================================================
    # STEP 2: Configure QC with quantile analysis enabled
    # =========================================================================
    print_subsection("Step 2: Configure QC with Quantile Analysis")

    # Interior config: detect x0 spike with multi-curve analysis
    interior_config = InteriorConfig(
        use_quantile_analysis=True,
        quantile_grid=(0.001, 0.005, 0.01, 0.02, 0.05, 0.10),
        min_quantile_agreement=0.5,
    )
    print("Interior QC Configuration:")
    print(f"  use_quantile_analysis: {interior_config.use_quantile_analysis}")
    print(f"  quantile_grid: {interior_config.quantile_grid}")
    print(f"  min_quantile_agreement: {interior_config.min_quantile_agreement}")

    # Boundary config: detect pileup with progressive grid and multi-curve analysis
    boundary_config = BoundaryConfig(
        grid_mode="progressive",
        use_quantile_analysis=True,
        quantile_grid=(0.001, 0.002, 0.005, 0.01, 0.02, 0.05),
        min_quantile_agreement=0.5,
    )
    print("\nBoundary QC Configuration:")
    print(f"  grid_mode: {boundary_config.grid_mode}")
    print(f"  use_quantile_analysis: {boundary_config.use_quantile_analysis}")
    print(f"  quantile_grid: {boundary_config.quantile_grid}")
    print(f"  min_quantile_agreement: {boundary_config.min_quantile_agreement}")

    # Plot config: lower DPI for faster example execution
    plot_config = PlotConfig(
        dpi=150,
        figsize_interior=(14, 5),
        figsize_boundary=(14, 5),
        figsize_tolerance=(12, 5),
    )

    # =========================================================================
    # STEP 3: Run Interior QC (x0 stickiness detection)
    # =========================================================================
    print_subsection("Step 3: Run Interior QC (x0 Stickiness)")

    interior_result = run_interior_qc(
        x=data,
        x0=x0,
        L=L,
        U=U,
        config=interior_config,
    )

    print("Interior QC Results:")
    print(f"  Spike detected: {interior_result.spike_detected}")
    print(f"  Threshold eps*: {interior_result.eps_star}")

    if interior_result.spike_detected:
        print(f"  Spike z-location: {interior_result.spike_z_loc}")

    if interior_result.quantile_elbows:
        print("\n  Quantile elbow thresholds (multi-curve analysis):")
        for q, eps in sorted(interior_result.quantile_elbows.items()):
            eps_str = f"{eps:.2e}" if eps is not None else "None"
            print(f"    q={q:.3f} -> eps={eps_str}")

    # =========================================================================
    # STEP 4: Run Boundary QC (L/U pileup detection)
    # =========================================================================
    print_subsection("Step 4: Run Boundary QC (Boundary Pileup)")

    boundary_result = run_boundary_qc(
        x=data,
        L=L,
        U=U,
        config=boundary_config,
    )

    print("Boundary QC Results:")
    print(f"  Lower pileup detected: {boundary_result.lower_pileup_detected}")
    print(f"  Upper pileup detected: {boundary_result.upper_pileup_detected}")
    print(f"  Threshold t_lo*: {boundary_result.t_lo_star}")
    print(f"  Threshold t_hi*: {boundary_result.t_hi_star}")

    if boundary_result.quantile_elbows:
        print("\n  Quantile elbow thresholds (multi-curve analysis):")
        for boundary_name in ["lower", "upper"]:
            elbows = boundary_result.quantile_elbows.get(boundary_name, {})
            if elbows:
                print(f"    {boundary_name.capitalize()} boundary:")
                for q, tol in sorted(elbows.items()):
                    tol_str = f"{tol:.4f}" if tol is not None else "None"
                    print(f"      q={q:.3f} -> tol={tol_str}")

    # =========================================================================
    # STEP 5: Create Standard Diagnostic Plots
    # =========================================================================
    print_subsection("Step 5: Create Standard Diagnostic Plots")

    # Interior diagnostics
    print("Creating interior diagnostics plot...")
    fig_interior = plot_interior_diagnostics(interior_result, plot_config)
    output_interior = "quantile_viz_interior_diagnostics.png"
    fig_interior.savefig(output_interior, bbox_inches="tight")
    print(f"  Saved: {output_interior}")
    print("    - Panel 1: Histogram of z-values (distance from x0)")
    print("    - Panel 2: Mass curve P(z < eps) linear scale")
    print("    - Panel 3: Mass curve log scale with elbow marked")

    # Boundary diagnostics
    print("\nCreating boundary diagnostics plot...")
    fig_boundary = plot_boundary_diagnostics(boundary_result, plot_config)
    output_boundary = "quantile_viz_boundary_diagnostics.png"
    fig_boundary.savefig(output_boundary, bbox_inches="tight")
    print(f"  Saved: {output_boundary}")
    print("    - Panel 1: Lower boundary mass curve P(u < tol)")
    print("    - Panel 2: Upper boundary mass curve P(u > 1-tol)")
    print("    - Panel 3: Log magnitude comparison")

    # =========================================================================
    # STEP 6: Create Quantile Elbow Overlay Plots
    # =========================================================================
    print_subsection("Step 6: Create Quantile Elbow Overlay Plots")

    # Interior quantile elbows
    print("Creating interior quantile elbow overlay...")
    fig_interior_elbows = plot_quantile_elbow_overlay(interior_result, plot_config)
    output_interior_elbows = "quantile_viz_interior_elbows.png"
    fig_interior_elbows.savefig(output_interior_elbows, bbox_inches="tight")
    print(f"  Saved: {output_interior_elbows}")
    print("    Shows relationship between quantile levels and detected eps thresholds")
    print("    Red dashed line = eps* (median of valid elbows)")

    # Boundary quantile elbows
    print("\nCreating boundary quantile elbow overlay...")
    fig_boundary_elbows = plot_quantile_elbow_overlay(boundary_result, plot_config)
    output_boundary_elbows = "quantile_viz_boundary_elbows.png"
    fig_boundary_elbows.savefig(output_boundary_elbows, bbox_inches="tight")
    print(f"  Saved: {output_boundary_elbows}")
    print("    - Left panel: Lower boundary quantile vs tolerance")
    print("    - Right panel: Upper boundary quantile vs tolerance")
    print("    Red dashed line = t* (median of valid elbows)")

    # =========================================================================
    # STEP 7: Create Tolerance Overlay Visualizations
    # =========================================================================
    print_subsection("Step 7: Create Tolerance Overlay Visualizations")

    # Define tolerance levels to visualize
    tols = np.array([0.0, 0.005, 0.01, 0.02, 0.03, 0.05])
    print(f"Visualizing tolerance levels: {tols}")

    # Histogram tolerance overlays
    print("\nCreating histogram tolerance overlays...")
    fig_hist = plot_histogram_tolerance_overlays(
        x=data,
        L=L,
        U=U,
        tols=tols,
        bins=80,
        config=plot_config,
    )
    output_hist = "quantile_viz_histogram_overlays.png"
    fig_hist.savefig(output_hist, bbox_inches="tight")
    print(f"  Saved: {output_hist}")
    print("    - Left: Shows data after lower boundary cuts at each tolerance")
    print("    - Right: Shows data after upper boundary cuts at each tolerance")
    print("    Watch the boundary pileup 'disappear' as tolerance increases")

    # ECDF tolerance overlays
    print("\nCreating ECDF tolerance overlays...")
    u = (data - L) / (U - L)  # Normalize to [0, 1]
    fig_ecdf = plot_ecdf_tolerance_overlays(
        u=u,
        tols=tols,
        side="both",
        config=plot_config,
    )
    output_ecdf = "quantile_viz_ecdf_overlays.png"
    fig_ecdf.savefig(output_ecdf, bbox_inches="tight")
    print(f"  Saved: {output_ecdf}")
    print("    - Left: ECDF near lower boundary (u near 0)")
    print("    - Right: ECDF near upper boundary (u near 1)")
    print("    Deviation from diagonal (y=x) indicates pileup")

    # Quantile spacing overlays
    print("\nCreating quantile spacing overlays...")
    x_sorted = np.sort(data)
    fig_spacing = plot_quantile_spacing_overlays(
        x_sorted=x_sorted,
        L=L,
        U=U,
        tols=tols,
        q_max=0.15,  # Show first 15% of quantiles
        n_quantiles=100,
        config=plot_config,
    )
    output_spacing = "quantile_viz_spacing_overlays.png"
    fig_spacing.savefig(output_spacing, bbox_inches="tight")
    print(f"  Saved: {output_spacing}")
    print("    Shows spacing between consecutive quantiles near lower tail")
    print("    Compressed spacing (low dq) indicates pileup")

    # =========================================================================
    # STEP 8: Summary and Interpretation
    # =========================================================================
    print_subsection("Step 8: Summary and Interpretation")

    # Summarize detection results
    issues_found = []
    if interior_result.spike_detected:
        issues_found.append(f"x0 spike (eps*={interior_result.eps_star:.2e})")
    if boundary_result.lower_pileup_detected:
        issues_found.append(f"lower boundary pileup (t*={boundary_result.t_lo_star:.4f})")
    if boundary_result.upper_pileup_detected:
        issues_found.append(f"upper boundary pileup (t*={boundary_result.t_hi_star:.4f})")

    if issues_found:
        print("ISSUES DETECTED:")
        for issue in issues_found:
            print(f"  - {issue}")
        print("\nRecommendations:")
        print("  1. Check optimizer convergence criteria (may be too loose)")
        print("  2. Verify parameter bounds are appropriate for the model")
        print("  3. Consider using different initial guesses or starting strategies")
        print("  4. Review the diagnostic plots for visual confirmation")
    else:
        print("No stickiness issues detected.")

    # Summary of outputs
    print("\nGenerated Visualization Files:")
    all_outputs = [
        output_interior,
        output_boundary,
        output_interior_elbows,
        output_boundary_elbows,
        output_hist,
        output_ecdf,
        output_spacing,
    ]
    for output in all_outputs:
        print(f"  - {output}")

    print_section_header("Workflow Complete")

    # =========================================================================
    # BONUS: Usage tips for integrating into your own workflow
    # =========================================================================
    print("Integration Tips:")
    print("-" * 50)
    print()
    print("1. For batch processing multiple parameters:")
    print("   from fitqc import run_qc, QCSpec")
    print("   spec = QCSpec(param_names=[...], x0={...}, bounds={...})")
    print("   report, masks = run_qc(params_dict, spec)")
    print()
    print("2. For JSON-serializable results (logging/storage):")
    print("   report_dict = report.to_dict()")
    print("   import json; json.dumps(report_dict)")
    print()
    print("3. To customize quantile grids for your data scale:")
    print("   # For very tight pileups (< 0.1% of range):")
    print("   config = BoundaryConfig(")
    print("       quantile_grid=(0.0001, 0.0005, 0.001, 0.005, 0.01),")
    print("       use_quantile_analysis=True")
    print("   )")
    print()
    print("4. To use the unified detect_stickiness API:")
    print("   from fitqc import detect_stickiness")
    print("   result = detect_stickiness(data, mode='both', x0=x0, L=L, U=U)")
    print()


if __name__ == "__main__":
    main()
