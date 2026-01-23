"""Generate interior and combined filter comparison plots for PPA12 datasets."""

import json
from pathlib import Path

import pyarrow.parquet as pq

from fitqc import (
    BoundaryConfig,
    plot_combined_filter_comparison,
    plot_interior_filter_comparison,
    run_boundary_qc,
    run_interior_qc,
)

# Output directory for plots
output_dir = Path("figures")
output_dir.mkdir(exist_ok=True)

# List of datasets to process
datasets = ["A_He", "e_dv_pp", "e_dv_ap", "np1"]

# Configure boundary QC with progressive grid and quantile analysis
boundary_config = BoundaryConfig(
    use_quantile_analysis=True,
    refine_transition=True,
    grid_mode="progressive",
)

print("Generating interior and combined filter comparison plots for PPA12 datasets...\n")

for dataset_name in datasets:
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
        bins = "auto"

    print(f"  L={L}, U={U}, x0={x0}, bins={bins}")

    # Determine dataset family for subdirectory
    if dataset_name.startswith("e_dv_pp"):
        subdir = "e_dv_pp"
    elif dataset_name.startswith("e_dv_ap"):
        subdir = "e_dv_ap"
    else:
        subdir = dataset_name

    # Create output directory
    dataset_output_dir = output_dir / subdir
    dataset_output_dir.mkdir(parents=True, exist_ok=True)

    # Run boundary QC
    print("  Running boundary QC...")
    boundary_result = run_boundary_qc(x, L, U, boundary_config)

    # Run interior QC if x0 is available
    interior_result = None
    if x0 is not None:
        print("  Running interior QC...")
        interior_result = run_interior_qc(x, x0, L, U)

        # Create interior filter comparison plot
        print("  Creating interior filter comparison plot...")
        fig = plot_interior_filter_comparison(x, x0, L, U, interior_result, bins=bins)
        output_file_hires = (
            dataset_output_dir / f"{dataset_name}_interior_filter_comparison_hires.png"
        )
        fig.savefig(output_file_hires, dpi=300, bbox_inches="tight")
        print(f"  Saved: {output_file_hires}")
    else:
        print("  Skipping interior QC (x0 is None)")

    # Create combined filter comparison plot
    print("  Creating combined filter comparison plot...")
    fig = plot_combined_filter_comparison(x, x0, L, U, interior_result, boundary_result, bins=bins)
    output_file_hires = dataset_output_dir / f"{dataset_name}_combined_filter_comparison_hires.png"
    fig.savefig(output_file_hires, dpi=300, bbox_inches="tight")
    print(f"  Saved: {output_file_hires}")

    print()

print(f"✓ All plots saved to {output_dir}/ subdirectories")
print("\nGenerated plots (300 DPI high-res only):")
for dataset_name in datasets:
    print(f"  {dataset_name}:")
    if dataset_name in ["A_He", "e_dv_pp", "e_dv_ap"]:
        print(f"    - {dataset_name}_interior_filter_comparison_hires.png")
    print(f"    - {dataset_name}_combined_filter_comparison_hires.png")
