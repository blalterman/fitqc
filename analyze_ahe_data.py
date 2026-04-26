#!/usr/bin/env python
"""Analyze A_He real-world test data to understand boundary stickiness patterns."""

import json

import numpy as np
import pyarrow.parquet as pq

from fitqc.boundary import run_boundary_qc
from fitqc.config import BoundaryConfig

# Load metadata
with open("tests/data/A_He_test_metadata.json") as f:
    metadata = json.load(f)

print("=" * 80)
print("A_He Real-World Data Analysis")
print("=" * 80)
print("\nMetadata:")
print(f"  Parameter: {metadata['name']}")
print(f"  Bounds: L={metadata['L']}, U={metadata['U']} {metadata['units']}")
print(f"  Initial guess: x0={metadata['x0']}")
print(f"  Expected lower stickiness: {metadata['fitqc_test']['expected_lower_stickiness']}")
print(f"  Expected interior stickiness: {metadata['fitqc_test']['expected_interior_stickiness']}")
print(f"  Sample size: {metadata['n_samples']:,} (from {metadata['n_samples_full']:,} total)")

# Load data
table = pq.read_table("tests/data/A_He_test_sample.parquet")
x = table["values"].to_numpy()
L, U = metadata["L"], metadata["U"]
x0 = metadata["x0"]

print(f"\n{'=' * 80}")
print("Data Statistics")
print("=" * 80)
print(f"  N samples: {len(x):,}")
print(f"  Data type: {x.dtype}")
print(f"  Min: {x.min():.6f}")
print(f"  Max: {x.max():.6f}")
print(f"  Mean: {x.mean():.6f}")
print(f"  Median: {np.median(x):.6f}")
print(f"  Std: {x.std():.6f}")

# Compute u (normalized to [0, 1])
u = (x - L) / (U - L)

print(f"\n{'=' * 80}")
print("Boundary Stickiness Analysis (Raw Counts)")
print("=" * 80)

# Count samples at exact boundaries
exactly_at_L = np.sum(x == L)
exactly_at_U = np.sum(x == U)
exactly_at_x0 = np.sum(x == x0)

print("\nExact boundary values:")
print(f"  Exactly at L={L}: {exactly_at_L:,} samples ({100 * exactly_at_L / len(x):.3f}%)")
print(f"  Exactly at U={U}: {exactly_at_U:,} samples ({100 * exactly_at_U / len(x):.3f}%)")
print(f"  Exactly at x0={x0}: {exactly_at_x0:,} samples ({100 * exactly_at_x0 / len(x):.3f}%)")

# Check for near-boundary samples (within small epsilon)
eps_values = [1e-15, 1e-10, 1e-7, 1e-5, 0.0001, 0.001, 0.01, 0.1, 0.25, 0.5, 1.0]

print(f"\n{'=' * 80}")
print("Near-Boundary Sample Counts (Cumulative)")
print("=" * 80)
print(f"{'Epsilon':<12} {'Near L=0':<15} {'Near U=25':<15} {'Near x0=0':<15}")
print("-" * 80)

for eps in eps_values:
    near_L = np.sum(x <= L + eps)
    near_U = np.sum(x >= U - eps)
    near_x0 = np.sum(np.abs(x - x0) <= eps)

    print(
        f"{eps:<12.2e} {near_L:>6} ({100 * near_L / len(x):>5.2f}%)  "
        f"{near_U:>6} ({100 * near_U / len(x):>5.2f}%)  "
        f"{near_x0:>6} ({100 * near_x0 / len(x):>5.2f}%)"
    )

# High-resolution histogram near lower boundary
print(f"\n{'=' * 80}")
print("High-Resolution Histogram: Lower Boundary [0, 2.5]")
print("=" * 80)

# Create very fine bins near boundary
n_bins_fine = 1000
x_near_lower = x[x <= 2.5]
hist, bin_edges = np.histogram(x_near_lower, bins=n_bins_fine, range=(0, 2.5))
bin_width = bin_edges[1] - bin_edges[0]

print(f"\nBin width: {bin_width:.6f} {metadata['units']}")
print(f"Total samples in [0, 2.5]: {len(x_near_lower):,} ({100 * len(x_near_lower) / len(x):.2f}%)")

# Show first 20 bins (near L=0)
print("\nFirst 20 bins (closest to L=0):")
print(f"{'Bin':<5} {'Range':<25} {'Count':<10} {'Fraction':<12} {'Cumulative'}")
print("-" * 80)

cumulative = 0
for i in range(min(20, len(hist))):
    cumulative += hist[i]
    print(
        f"{i:<5} [{bin_edges[i]:>8.5f}, {bin_edges[i + 1]:>8.5f})  "
        f"{hist[i]:>6}     {100 * hist[i] / len(x):>6.3f}%      "
        f"{100 * cumulative / len(x):>6.3f}%"
    )

# Find mode (highest bin)
max_bin_idx = np.argmax(hist)
max_bin_count = hist[max_bin_idx]
max_bin_range = (bin_edges[max_bin_idx], bin_edges[max_bin_idx + 1])

print("\nMode (highest bin):")
print(f"  Bin {max_bin_idx}: [{max_bin_range[0]:.5f}, {max_bin_range[1]:.5f})")
print(f"  Count: {max_bin_count:,} ({100 * max_bin_count / len(x):.3f}%)")

# Analyze normalized u-space
print(f"\n{'=' * 80}")
print("U-Space Analysis (Normalized [0, 1])")
print("=" * 80)

u = (x - L) / (U - L)
print(f"  Min u: {u.min():.10f}")
print(f"  Max u: {u.max():.10f}")

# Check u-space boundary concentration
u_thresholds = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 0.05, 0.1]
print("\nCumulative mass in u-space:")
print(
    f"{'u threshold':<15} {'P(u < tol)':<15} {'Samples':<12} {'Expected (uniform)':<20} {'Excess'}"
)
print("-" * 90)

for tol in u_thresholds:
    mass = np.sum(u < tol) / len(u)
    samples = np.sum(u < tol)
    expected = tol  # For uniform
    excess = mass / tol if tol > 0 else 0
    print(f"{tol:<15.2e} {mass:<15.6f} {samples:>10,}  {expected:<20.6f} {excess:>6.2f}x")

print(f"\n{'=' * 80}")
print("Histogram Resolution Analysis")
print("=" * 80)

# What bin width corresponds to 1000-bin histogram?
range_width = U - L
bin_width_1000 = range_width / 1000
bin_width_1000_u = bin_width_1000 / range_width

print(f"For 1000-bin histogram of [{L}, {U}]:")
print(f"  Bin width (x-space): {bin_width_1000:.4f} {metadata['units']}")
print(f"  Bin width (u-space): {bin_width_1000_u:.6f}")
print(
    f"  Samples in first bin [0, {bin_width_1000:.4f}): {np.sum(x < bin_width_1000):,} ({100 * np.sum(x < bin_width_1000) / len(x):.3f}%)"
)

# Distribution characterization
print(f"\n{'=' * 80}")
print("Distribution Shape")
print("=" * 80)

percentiles = [0.1, 0.5, 1, 2, 5, 10, 25, 50, 75, 90, 95, 98, 99, 99.5, 99.9]
print("\nPercentiles:")
print(f"{'Percentile':<12} {'Value':<12} {'U-value'}")
print("-" * 50)
for p in percentiles:
    val = np.percentile(x, p)
    u_val = (val - L) / (U - L)
    print(f"{p:>6.1f}%      {val:>8.4f}      {u_val:.6f}")

# Run actual boundary QC to see what current algorithm detects
print(f"\n{'=' * 80}")
print("Current Algorithm Detection (Default Config)")
print("=" * 80)

config_default = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
result_default = run_boundary_qc(x, L=L, U=U, config=config_default)

print(f"\nWith default config (pileup_threshold={config_default.pileup_threshold}):")
print(f"  Lower pileup detected: {result_default.lower_pileup_detected}")
print(f"  Upper pileup detected: {result_default.upper_pileup_detected}")
print(f"  t_lo_star: {result_default.t_lo_star}")
print(f"  t_hi_star: {result_default.t_hi_star}")

# Try with lower threshold
config_sensitive = BoundaryConfig(
    use_quantile_analysis=True, refine_transition=True, pileup_threshold=0.0002
)
result_sensitive = run_boundary_qc(x, L=L, U=U, config=config_sensitive)

print(f"\nWith sensitive config (pileup_threshold={config_sensitive.pileup_threshold}):")
print(f"  Lower pileup detected: {result_sensitive.lower_pileup_detected}")
print(f"  Upper pileup detected: {result_sensitive.upper_pileup_detected}")
print(f"  t_lo_star: {result_sensitive.t_lo_star}")
print(f"  t_hi_star: {result_sensitive.t_hi_star}")

# Compare quantile elbows
if result_sensitive.quantile_elbows:
    print("\nQuantile elbows (sensitive config, lower boundary, first 10):")
    lower_elbows = result_sensitive.quantile_elbows["lower"]
    for _i, (q, elbow) in enumerate(list(lower_elbows.items())[:10]):
        print(f"  q={q:.4f}: elbow at t={elbow:.6f}")
