#!/usr/bin/env python
"""Comprehensive analysis of all PPA12 test datasets."""
import numpy as np
import pyarrow.parquet as pq
import json
from pathlib import Path
from fitqc.boundary import run_boundary_qc
from fitqc.config import BoundaryConfig

def analyze_dataset(name: str):
    """Analyze a single test dataset."""
    data_dir = Path("tests/data")

    # Load metadata
    with open(data_dir / f"{name}_test_metadata.json") as f:
        meta = json.load(f)

    # Load data
    table = pq.read_table(data_dir / f"{name}_test_sample.parquet")
    x = table['values'].to_numpy()

    L = meta['L']
    U = meta['U']
    x0 = meta.get('x0')

    print("="*80)
    print(f"Dataset: {name}")
    print("="*80)
    print(f"Parameter: {meta.get('name', name)}")
    print(f"Bounds: L={L}, U={U}, x0={x0}")
    print(f"Units: {meta.get('units', 'N/A')}")
    print(f"Sample size: {len(x):,} (from {meta.get('n_samples_full', 'N/A'):,} total)")

    # Expected results from metadata
    expected = meta.get('fitqc_test', {})
    print(f"\nExpected (from metadata):")
    print(f"  Lower stickiness: {expected.get('expected_lower_stickiness', 'N/A')}")
    print(f"  Upper stickiness: {expected.get('expected_upper_stickiness', 'N/A')}")
    print(f"  Interior stickiness: {expected.get('expected_interior_stickiness', 'N/A')}")

    # Basic statistics
    print(f"\nBasic statistics:")
    print(f"  Min: {x.min():.6f}")
    print(f"  Max: {x.max():.6f}")
    print(f"  Mean: {x.mean():.6f}")
    print(f"  Std: {x.std():.6f}")

    # Boundary analysis
    print(f"\nBoundary analysis:")

    # Exact boundary counts
    exactly_at_L = np.sum(x == L)
    exactly_at_U = np.sum(x == U)
    print(f"  Exactly at L={L}: {exactly_at_L:,} ({100*exactly_at_L/len(x):.3f}%)")
    print(f"  Exactly at U={U}: {exactly_at_U:,} ({100*exactly_at_U/len(x):.3f}%)")

    # Near boundary counts (within machine epsilon)
    near_L = np.sum(np.abs(x - L) < 1e-10)
    near_U = np.sum(np.abs(x - U) < 1e-10)
    if near_L != exactly_at_L or near_U != exactly_at_U:
        print(f"  Near L (within 1e-10): {near_L:,} ({100*near_L/len(x):.3f}%)")
        print(f"  Near U (within 1e-10): {near_U:,} ({100*near_U/len(x):.3f}%)")

    # U-space analysis
    u = (x - L) / (U - L)
    u_sorted = np.sort(u)

    print(f"\nU-space proximity to boundaries:")
    tolerances = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 0.05, 0.1]

    print(f"  Lower boundary (u < tol):")
    for tol in tolerances:
        count_lower = np.sum(u < tol)
        frac_lower = count_lower / len(u)
        excess_lower = frac_lower / tol if tol > 0 else 0
        if count_lower > 0:
            print(f"    tol={tol:.2e}: {count_lower:>6,} samples ({frac_lower:>7.4f}), excess={excess_lower:>6.1f}x")

    print(f"  Upper boundary (u > 1-tol):")
    for tol in tolerances:
        count_upper = np.sum(u > 1 - tol)
        frac_upper = count_upper / len(u)
        excess_upper = frac_upper / tol if tol > 0 else 0
        if count_upper > 0:
            print(f"    tol={tol:.2e}: {count_upper:>6,} samples ({frac_upper:>7.4f}), excess={excess_upper:>6.1f}x")

    # Interior stickiness (if x0 is defined)
    if x0 is not None:
        print(f"\nInterior stickiness analysis (x0={x0}):")
        exactly_at_x0 = np.sum(x == x0)
        print(f"  Exactly at x0: {exactly_at_x0:,} ({100*exactly_at_x0/len(x):.3f}%)")

        # Check proximity to x0
        distances_from_x0 = np.abs(x - x0)
        for tol_abs in [1e-6, 1e-4, 1e-2, 0.1, 1.0, 10.0]:
            count_near = np.sum(distances_from_x0 < tol_abs)
            frac_near = count_near / len(x)
            if count_near > exactly_at_x0:  # Only print if there are samples beyond exact matches
                print(f"  Within {tol_abs}: {count_near:,} ({frac_near:.4f})")

    # Run boundary QC
    print(f"\nBoundary QC Results:")
    config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
    result = run_boundary_qc(x, L=L, U=U, config=config)

    print(f"  Lower pileup detected: {result.lower_pileup_detected}")
    print(f"  Upper pileup detected: {result.upper_pileup_detected}")
    print(f"  t_lo_star: {result.t_lo_star}")
    print(f"  t_hi_star: {result.t_hi_star}")

    # Comparison with expected
    print(f"\nValidation:")
    lower_match = result.lower_pileup_detected == expected.get('expected_lower_stickiness', None)
    upper_match = result.upper_pileup_detected == expected.get('expected_upper_stickiness', None)

    lower_status = "✓ PASS" if lower_match else "✗ FAIL"
    upper_status = "✓ PASS" if upper_match else "✗ FAIL"

    if expected.get('expected_lower_stickiness') is not None:
        print(f"  Lower: {lower_status} (expected={expected['expected_lower_stickiness']}, got={result.lower_pileup_detected})")
    if expected.get('expected_upper_stickiness') is not None:
        print(f"  Upper: {upper_status} (expected={expected['expected_upper_stickiness']}, got={result.upper_pileup_detected})")

    print()
    return result

# Analyze all datasets
if __name__ == "__main__":
    datasets = ["A_He", "e_dv_pp", "e_dv_ap", "np1"]

    results = {}
    for name in datasets:
        try:
            results[name] = analyze_dataset(name)
        except Exception as e:
            print(f"ERROR analyzing {name}: {e}")
            print()

    # Summary table
    print("="*80)
    print("SUMMARY TABLE")
    print("="*80)
    print(f"{'Dataset':<15} {'Lower Exp':<12} {'Lower Det':<12} {'Upper Exp':<12} {'Upper Det':<12} {'Status'}")
    print("-"*80)

    for name in datasets:
        if name in results:
            data_dir = Path("tests/data")
            with open(data_dir / f"{name}_test_metadata.json") as f:
                meta = json.load(f)
            expected = meta.get('fitqc_test', {})
            result = results[name]

            lower_exp = str(expected.get('expected_lower_stickiness', 'N/A'))
            lower_det = str(result.lower_pileup_detected)
            upper_exp = str(expected.get('expected_upper_stickiness', 'N/A'))
            upper_det = str(result.upper_pileup_detected)

            lower_ok = lower_exp == 'N/A' or (lower_exp.lower() == lower_det.lower())
            upper_ok = upper_exp == 'N/A' or (upper_exp.lower() == upper_det.lower())

            status = "✓ PASS" if (lower_ok and upper_ok) else "✗ FAIL"

            print(f"{name:<15} {lower_exp:<12} {lower_det:<12} {upper_exp:<12} {upper_det:<12} {status}")
