#!/usr/bin/env python
"""Investigate false positives in np1 and A_He datasets."""
import numpy as np
import pyarrow.parquet as pq
import json
from pathlib import Path

def investigate_np1():
    """Investigate np1 lower boundary false positive."""
    print("="*80)
    print("Investigating np1 Lower Boundary False Positive")
    print("="*80)

    data_dir = Path("tests/data")
    with open(data_dir / "np1_test_metadata.json") as f:
        meta = json.load(f)

    table = pq.read_table(data_dir / "np1_test_sample.parquet")
    x = table['values'].to_numpy()

    L = meta['L']  # 0.01
    U = meta['U']  # 100.0

    print(f"\nParameter bounds: L={L}, U={U}")
    print(f"Total samples: {len(x):,}")

    # Check samples below L
    below_L = x < L
    at_L = x == L
    above_L_near = (x > L) & (x < L * 10)

    print(f"\nSamples relative to L={L}:")
    print(f"  Below L (x < {L}): {np.sum(below_L):,} ({100*np.sum(below_L)/len(x):.3f}%)")
    print(f"  Exactly at L: {np.sum(at_L):,}")
    print(f"  Between L and 10*L: {np.sum(above_L_near):,} ({100*np.sum(above_L_near)/len(x):.3f}%)")

    # Look at the samples below L
    if np.sum(below_L) > 0:
        samples_below = x[below_L]
        print(f"\nSamples below L={L}:")
        print(f"  Count: {len(samples_below):,}")
        print(f"  Min: {samples_below.min():.10f}")
        print(f"  Max: {samples_below.max():.10f}")
        print(f"  Exactly at 0.0: {np.sum(samples_below == 0.0):,}")

        # Histogram of samples below L
        print(f"\n  Distribution of samples below L:")
        bins = [0, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, L]
        for i in range(len(bins)-1):
            count = np.sum((samples_below >= bins[i]) & (samples_below < bins[i+1]))
            if count > 0:
                print(f"    [{bins[i]:.2e}, {bins[i+1]:.2e}): {count:,} samples")

    # U-space calculation
    u = (x - L) / (U - L)
    print(f"\nU-space analysis:")
    print(f"  u_min: {u.min():.10f}")
    print(f"  u_max: {u.max():.10f}")
    print(f"  Samples with u < 0: {np.sum(u < 0):,} (these are BELOW L!)")
    print(f"  Samples with u < 1e-6: {np.sum(u < 1e-6):,}")

    # The issue: samples below L create negative u values, but algorithm sees them as boundary
    print(f"\n" + "="*80)
    print("DIAGNOSIS:")
    print("="*80)
    print(f"The {np.sum(below_L):,} samples below L={L} create negative u-values.")
    print(f"When sorted, these become u_sorted[0:n] where u < 0.")
    print(f"The algorithm detects this as a 'pileup' at the lower boundary.")
    print(f"\nBut these samples are OUTSIDE the parameter bounds!")
    print(f"This is either:")
    print(f"  (a) A data quality issue (samples should be clipped to L)")
    print(f"  (b) An algorithm issue (should filter u < 0 as invalid)")
    print(f"  (c) Expected behavior (L is a soft bound, not hard constraint)")


def investigate_a_he_upper():
    """Investigate A_He upper boundary false positive."""
    print("\n\n" + "="*80)
    print("Investigating A_He Upper Boundary False Positive")
    print("="*80)

    data_dir = Path("tests/data")
    with open(data_dir / "A_He_test_metadata.json") as f:
        meta = json.load(f)

    table = pq.read_table(data_dir / "A_He_test_sample.parquet")
    x = table['values'].to_numpy()

    L = meta['L']  # 0.0
    U = meta['U']  # 25.0

    print(f"\nParameter bounds: L={L}, U={U}")
    print(f"Total samples: {len(x):,}")

    # Upper boundary analysis
    exactly_at_U = np.sum(x == U)
    print(f"\nUpper boundary:")
    print(f"  Exactly at U={U}: {exactly_at_U:,} ({100*exactly_at_U/len(x):.3f}%)")

    # Expected says False, but we have 0.45%
    expected_upper = meta['fitqc_test']['expected_upper_stickiness']
    print(f"  Expected upper stickiness: {expected_upper}")

    # Check the distribution near U
    near_U_ranges = [
        (U - 0.001, U),
        (U - 0.01, U - 0.001),
        (U - 0.1, U - 0.01),
        (U - 1.0, U - 0.1),
    ]

    print(f"\n  Distribution near U:")
    for low, high in near_U_ranges:
        count = np.sum((x >= low) & (x < high))
        print(f"    [{low:.3f}, {high:.3f}): {count:,} samples")

    # U-space analysis
    u = (x - L) / (U - L)
    u_from_upper = 1 - u

    print(f"\nU-space from upper boundary:")
    for tol in [1e-6, 1e-5, 1e-4, 1e-3, 1e-2]:
        count = np.sum(u_from_upper <= tol)
        frac = count / len(x)
        excess = frac / tol if tol > 0 else 0
        print(f"  u_from_upper <= {tol:.2e}: {count:>6,} ({frac:.5f}), excess={excess:>6.1f}x")

    print(f"\n" + "="*80)
    print("DIAGNOSIS:")
    print("="*80)
    print(f"There are {exactly_at_U:,} samples ({100*exactly_at_U/len(x):.3f}%) exactly at U={U}.")
    print(f"This gives a {4530.0:.0f}x excess at u < 1e-6 from the upper bound.")
    print(f"\nThe metadata says expected_upper_stickiness=False, but:")
    print(f"  - 0.45% pileup is detectable (similar to e_dv_ap's 0.62% at lower)")
    print(f"  - Algorithm is working correctly")
    print(f"\nPossible explanations:")
    print(f"  (a) Metadata is incorrect - there IS upper boundary stickiness")
    print(f"  (b) 0.45% is below the 'significance threshold' for A_He")
    print(f"  (c) This is a known false positive case")


if __name__ == "__main__":
    investigate_np1()
    investigate_a_he_upper()
