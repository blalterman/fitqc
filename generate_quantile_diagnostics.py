"""Generate quantile-based diagnostic plots for PPA12 datasets."""

import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from fitqc import (
    BoundaryConfig,
    PlotConfig,
    plot_boundary_diagnostics,
    plot_ecdf_tolerance_overlays,
    plot_histogram_tolerance_overlays,
    plot_interior_diagnostics,
    plot_quantile_elbow_overlay,
    plot_quantile_spacing_overlays,
    run_boundary_qc,
    run_interior_qc,
)

# Output directory for plots
output_dir = Path("figures")
output_dir.mkdir(exist_ok=True)

# Datasets to process
datasets = ["A_He", "e_dv_pp", "e_dv_ap", "np1", "np2", "w_const"]

# Configure boundary QC with progressive grid and quantile analysis
boundary_config = BoundaryConfig(
    use_quantile_analysis=True,
    refine_transition=True,
    grid_mode="progressive",
)

plot_config = PlotConfig()

# Tolerance levels for overlay plots
tols = np.array([0.0, 0.005, 0.01, 0.02, 0.03, 0.05])

print("Generating quantile diagnostic plots for PPA12 datasets...\n")

for dataset_name in datasets:
    print(f"{'=' * 60}")
    print(f"Processing {dataset_name}...")

    # Load data
    parquet_file = f"tests/data/{dataset_name}_test_sample.parquet"
    metadata_file = f"tests/data/{dataset_name}_test_metadata.json"

    table = pq.read_table(parquet_file)
    x = table.column("values").to_numpy()

    with open(metadata_file) as f:
        metadata = json.load(f)

    L = metadata["L"]
    U = metadata["U"]
    x0 = metadata.get("x0")
    name = metadata["name"]

    # Determine appropriate number of bins
    range_width = U - L
    if range_width > 100:
        bins = 500
    elif range_width > 50:
        bins = 300
    elif range_width > 10:
        bins = 200
    else:
        bins = 100

    print(f"  L={L}, U={U}, x0={x0}, n={len(x)}, bins={bins}")

    # Create output directory
    dataset_output_dir = output_dir / dataset_name
    dataset_output_dir.mkdir(parents=True, exist_ok=True)

    # Run boundary QC
    print("  Running boundary QC...")
    boundary_result = run_boundary_qc(x, L, U, boundary_config)

    # Print raw vs validated thresholds
    t_lo_raw = getattr(boundary_result, "t_lo_raw", None)
    t_hi_raw = getattr(boundary_result, "t_hi_raw", None)
    t_lo_star = boundary_result.t_lo_star
    t_hi_star = boundary_result.t_hi_star
    print(f"  Lower: t_lo_raw={t_lo_raw}  t_lo_star={t_lo_star}")
    print(f"  Upper: t_hi_raw={t_hi_raw}  t_hi_star={t_hi_star}")

    # Run interior QC if x0 is available
    interior_result = None
    if x0 is not None:
        print("  Running interior QC...")
        interior_result = run_interior_qc(x, x0, L, U)

    # --- Generate 7 figure types ---

    # 1. Interior diagnostics (skip if no x0)
    if interior_result is not None:
        fig = plot_interior_diagnostics(interior_result, plot_config)
        out = dataset_output_dir / f"{dataset_name}_interior_diagnostics.png"
        fig.savefig(out, bbox_inches="tight")
        print(f"  Saved: {out}")

    # 2. Boundary diagnostics
    fig = plot_boundary_diagnostics(boundary_result, plot_config)
    out = dataset_output_dir / f"{dataset_name}_boundary_diagnostics.png"
    fig.savefig(out, bbox_inches="tight")
    print(f"  Saved: {out}")

    # 3. Interior quantile elbows (skip if no x0)
    if interior_result is not None:
        fig = plot_quantile_elbow_overlay(interior_result, plot_config)
        out = dataset_output_dir / f"{dataset_name}_interior_elbows.png"
        fig.savefig(out, bbox_inches="tight")
        print(f"  Saved: {out}")

    # 4. Boundary quantile elbows
    fig = plot_quantile_elbow_overlay(boundary_result, plot_config)
    out = dataset_output_dir / f"{dataset_name}_boundary_elbows.png"
    fig.savefig(out, bbox_inches="tight")
    print(f"  Saved: {out}")

    # 5. Histogram tolerance overlays
    fig = plot_histogram_tolerance_overlays(x=x, L=L, U=U, tols=tols, bins=bins, config=plot_config)
    out = dataset_output_dir / f"{dataset_name}_histogram_overlays.png"
    fig.savefig(out, bbox_inches="tight")
    print(f"  Saved: {out}")

    # 6. ECDF tolerance overlays
    u = (x - L) / (U - L)
    fig = plot_ecdf_tolerance_overlays(u=u, tols=tols, side="both", config=plot_config)
    out = dataset_output_dir / f"{dataset_name}_ecdf_overlays.png"
    fig.savefig(out, bbox_inches="tight")
    print(f"  Saved: {out}")

    # 7. Quantile spacing overlays
    x_sorted = np.sort(x)
    fig = plot_quantile_spacing_overlays(
        x_sorted=x_sorted,
        L=L,
        U=U,
        tols=tols,
        q_max=0.15,
        n_quantiles=100,
        config=plot_config,
    )
    out = dataset_output_dir / f"{dataset_name}_spacing_overlays.png"
    fig.savefig(out, bbox_inches="tight")
    print(f"  Saved: {out}")

    print()

print("Done. All figures saved to figures/ subdirectories.")
