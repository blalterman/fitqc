"""Generate bounds filter comparison plots for all PPA12 test datasets."""

import json
import pyarrow.parquet as pq
from pathlib import Path

from fitqc import plot_bounds_filter_comparison

# Output directory for plots
output_dir = Path("figures")
output_dir.mkdir(exist_ok=True)

# List of datasets to process
datasets = ["A_He", "e_dv_pp", "e_dv_ap", "np1"]

print("Generating bounds filter comparison plots for PPA12 datasets...\n")

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
    name = metadata["name"]

    # Determine appropriate number of bins based on dataset
    # Use more bins for larger ranges
    range_width = U - L
    if range_width > 100:
        bins = 500  # Large range (e.g., e_dv_ap: -150 to 150)
    elif range_width > 50:
        bins = 300  # Medium range (e.g., e_dv_pp: -75 to 75)
    elif range_width > 10:
        bins = 200  # Smaller range (e.g., A_He: 0 to 25)
    else:
        bins = 'auto'  # Very small range or complex distribution

    print(f"  L={L}, U={U}, range={range_width:.1f}, bins={bins}")

    # Create comparison plot
    fig = plot_bounds_filter_comparison(x, L, U, bins=bins)

    # Save figure
    output_file = output_dir / f"{dataset_name}_bounds_filter_comparison.png"
    fig.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"  Saved: {output_file}")

    # Also save a high-res version for presentations
    output_file_hires = output_dir / f"{dataset_name}_bounds_filter_comparison_hires.png"
    fig.savefig(output_file_hires, dpi=300, bbox_inches="tight")
    print(f"  Saved: {output_file_hires}")

    print()

print(f"✓ All plots saved to {output_dir}/")
print("\nFiles generated:")
for dataset_name in datasets:
    print(f"  - {dataset_name}_bounds_filter_comparison.png")
    print(f"  - {dataset_name}_bounds_filter_comparison_hires.png")
