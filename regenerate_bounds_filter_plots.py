#!/usr/bin/env python3
"""Regenerate all bounds filter comparison plots with new zoom panel feature.

This script regenerates bounds filter comparison plots for all 12 PPA12 datasets,
now including the new zoom panel that shows out-of-bounds detail when applicable.
"""

import json
import numpy as np
import pyarrow.parquet as pq
from pathlib import Path
from fitqc import plot_bounds_filter_comparison

# All 12 PPA12 test datasets
ALL_DATASETS = [
    "A_He",
    "e_dv_pp", "e_dv_pp_2",
    "e_dv_ap", "e_dv_ap_2",
    "np1", "np2",
    "w_const",
    "xi_1", "xi_2",
    "u_1", "u_2",
]

def regenerate_dataset_plots(dataset_name: str):
    """Regenerate bounds filter comparison plots for a dataset."""
    print(f"Processing {dataset_name}...")

    # Load data
    parquet_file = f"tests/data/{dataset_name}_test_sample.parquet"
    metadata_file = f"tests/data/{dataset_name}_test_metadata.json"

    try:
        table = pq.read_table(parquet_file)
        x = table.column("values").to_numpy()

        with open(metadata_file) as f:
            metadata = json.load(f)

        L = metadata["L"]
        U = metadata["U"]
        name = metadata["name"]

    except FileNotFoundError as e:
        print(f"  SKIP: {e}")
        return False

    # Count out-of-bounds
    n_below = np.sum(x < L)
    n_above = np.sum(x > U)
    n_total = len(x)

    print(f"  L={L}, U={U}, samples={n_total:,}")
    print(f"  Out-of-bounds: {n_below + n_above:,} ({(n_below + n_above)/n_total:.2%})")

    # Determine appropriate number of bins based on dataset
    range_width = U - L
    if range_width > 100:
        bins = 500  # Large range (e.g., e_dv_ap: -150 to 150)
    elif range_width > 50:
        bins = 300  # Medium range (e.g., e_dv_pp: -75 to 75)
    elif range_width > 10:
        bins = 200  # Smaller range (e.g., A_He: 0 to 25)
    else:
        bins = 'auto'  # Very small range or complex distribution

    # Determine dataset family for subdirectory
    if dataset_name.startswith("e_dv_pp"):
        subdir = "e_dv_pp"
    elif dataset_name.startswith("e_dv_ap"):
        subdir = "e_dv_ap"
    elif dataset_name in ["xi_1", "xi_2"]:
        subdir = "xi"
    elif dataset_name in ["u_1", "u_2"]:
        subdir = "u"
    else:
        subdir = dataset_name

    # Create output directory
    output_dir = Path("figures") / subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create comparison plot with zoom panel (show_detail=True by default)
    fig = plot_bounds_filter_comparison(x, L, U, bins=bins, show_detail=True)

    # Save figures
    output_file = output_dir / f"{dataset_name}_bounds_filter_comparison.png"
    fig.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"  Saved: {output_file}")

    # Also save a high-res version
    output_file_hires = output_dir / f"{dataset_name}_bounds_filter_comparison_hires.png"
    fig.savefig(output_file_hires, dpi=300, bbox_inches="tight")
    print(f"  Saved: {output_file_hires}")

    import matplotlib.pyplot as plt
    plt.close(fig)

    print()
    return True

def main():
    """Regenerate all bounds filter comparison plots."""
    print("="*70)
    print("Regenerating Bounds Filter Comparison Plots with Zoom Panels")
    print("="*70)
    print()

    success_count = 0
    for dataset_name in ALL_DATASETS:
        if regenerate_dataset_plots(dataset_name):
            success_count += 1

    print("="*70)
    print(f"✓ Successfully regenerated plots for {success_count}/{len(ALL_DATASETS)} datasets")
    print("="*70)

if __name__ == "__main__":
    main()
