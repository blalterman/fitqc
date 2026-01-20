"""Comprehensive audit of filtering for all PPA12 datasets."""

import json
import numpy as np
import pandas as pd
from pathlib import Path

from fitqc.boundary import run_boundary_qc, compute_u
from fitqc.config import BoundaryConfig

data_dir = Path("tests/data")

# All 12 PPA12 datasets
datasets = [
    "A_He", "e_dv_ap", "e_dv_pp", "np1", "np2",
    "vx", "vy", "vz", "w_const", "e_w_a", "e_w_p1", "e_w_p2"
]

print(f"{'='*100}")
print(f"COMPREHENSIVE FILTERING AUDIT - ALL PPA12 DATASETS")
print(f"{'='*100}\n")

summary_results = []

for dataset_name in datasets:
    print(f"\n{'-'*100}")
    print(f"Dataset: {dataset_name}")
    print(f"{'-'*100}")

    # Load data
    x = pd.read_parquet(data_dir / f"{dataset_name}_test_sample.parquet")["values"].values
    with open(data_dir / f"{dataset_name}_test_metadata.json") as f:
        meta = json.load(f)

    L = meta["L"]
    U = meta["U"]

    print(f"Bounds: L={L}, U={U}")
    print(f"Total samples: {len(x):,}")

    # X-space filtering
    x_filtered_xspace = x[(x >= L) & (x <= U)]
    n_below_L_xspace = np.sum(x < L)
    n_above_U_xspace = np.sum(x > U)
    n_filtered_xspace = len(x_filtered_xspace)

    # U-space filtering
    u = compute_u(x, L, U)
    out_of_bounds_mask = (u < 0) | (u > 1)
    n_below_L_uspace = np.sum(u < 0)
    n_above_U_uspace = np.sum(u > 1)
    u_filtered = u[~out_of_bounds_mask]
    x_filtered_uspace = x[~out_of_bounds_mask]
    n_filtered_uspace = len(x_filtered_uspace)

    # Compare
    methods_match = (n_filtered_xspace == n_filtered_uspace)
    datasets_identical = np.array_equal(np.sort(x_filtered_xspace), np.sort(x_filtered_uspace))

    print(f"\nX-space filtering:")
    print(f"  Below L: {n_below_L_xspace:,} ({n_below_L_xspace/len(x)*100:.2f}%)")
    print(f"  Above U: {n_above_U_xspace:,} ({n_above_U_xspace/len(x)*100:.2f}%)")
    print(f"  Retained: {n_filtered_xspace:,} ({n_filtered_xspace/len(x)*100:.2f}%)")

    print(f"\nU-space filtering:")
    print(f"  Below L (u<0): {n_below_L_uspace:,} ({n_below_L_uspace/len(x)*100:.2f}%)")
    print(f"  Above U (u>1): {n_above_U_uspace:,} ({n_above_U_uspace/len(x)*100:.2f}%)")
    print(f"  Retained: {n_filtered_uspace:,} ({n_filtered_uspace/len(x)*100:.2f}%)")

    status = "✓ PASS" if (methods_match and datasets_identical) else "✗ FAIL"
    print(f"\nVerification: {status}")
    if not methods_match:
        print(f"  ✗ Different number of samples: {n_filtered_xspace} vs {n_filtered_uspace}")
    if not datasets_identical:
        print(f"  ✗ Filtered datasets are not identical")

    # Run boundary detection
    config = BoundaryConfig()
    result = run_boundary_qc(x, L, U, config)

    print(f"\nBoundary detection:")
    print(f"  Lower pileup: {result.lower_pileup_detected}")
    print(f"  Upper pileup: {result.upper_pileup_detected}")
    if result.t_lo_star is not None:
        print(f"  Lower threshold: {result.t_lo_star:.6f}")
    if result.t_hi_star is not None:
        print(f"  Upper threshold: {result.t_hi_star:.6f}")

    # Check for out-of-bounds samples at specific values
    if n_below_L_xspace > 0:
        x_below = x[x < L]
        n_at_zero = np.sum(x_below == 0.0)
        if n_at_zero > 0:
            print(f"\n  ⚠️  {n_at_zero} out-of-bounds samples at exactly 0.0 (likely FAILED FITS)")

    # Store summary
    summary_results.append({
        'dataset': dataset_name,
        'n_total': len(x),
        'n_below_L': n_below_L_xspace,
        'n_above_U': n_above_U_xspace,
        'n_out_of_bounds': n_below_L_xspace + n_above_U_xspace,
        'pct_out_of_bounds': (n_below_L_xspace + n_above_U_xspace) / len(x) * 100,
        'methods_match': methods_match,
        'datasets_identical': datasets_identical,
        'lower_detected': result.lower_pileup_detected,
        'upper_detected': result.upper_pileup_detected,
    })

# Print summary table
print(f"\n\n{'='*100}")
print(f"SUMMARY TABLE")
print(f"{'='*100}\n")

header = f"{'Dataset':<12} {'Total':>10} {'Below L':>10} {'Above U':>10} {'Out-of-Bounds':>12} {'%OOB':>8} {'Match':>7} {'Lower':>7} {'Upper':>7}"
print(header)
print("-" * len(header))

for result in summary_results:
    match_symbol = "✓" if result['methods_match'] and result['datasets_identical'] else "✗"
    lower_symbol = "✓" if result['lower_detected'] else "✗"
    upper_symbol = "✓" if result['upper_detected'] else "✗"

    print(f"{result['dataset']:<12} {result['n_total']:>10,} {result['n_below_L']:>10,} {result['n_above_U']:>10,} "
          f"{result['n_out_of_bounds']:>12,} {result['pct_out_of_bounds']:>7.2f}% {match_symbol:>7} {lower_symbol:>7} {upper_symbol:>7}")

print(f"\n{'='*100}")

# Check for failures
failures = [r for r in summary_results if not (r['methods_match'] and r['datasets_identical'])]
if failures:
    print(f"\n⚠️  FAILURES DETECTED in {len(failures)} dataset(s):")
    for f in failures:
        print(f"  - {f['dataset']}")
else:
    print(f"\n✓ ALL DATASETS PASS: X-space and U-space filtering produce identical results")

# Datasets with out-of-bounds
oob_datasets = [r for r in summary_results if r['n_out_of_bounds'] > 0]
if oob_datasets:
    print(f"\n📊 {len(oob_datasets)} dataset(s) have out-of-bounds samples:")
    for r in oob_datasets:
        print(f"  - {r['dataset']}: {r['n_out_of_bounds']:,} samples ({r['pct_out_of_bounds']:.2f}%)")

print(f"\n{'='*100}")
