#!/usr/bin/env python
"""Debug why upper boundary is showing false positive."""

import json

import numpy as np
import pyarrow.parquet as pq

from fitqc.boundary import compute_u, tail_mass

# Load A_He data
with open("tests/data/A_He_test_metadata.json") as f:
    metadata = json.load(f)

table = pq.read_table("tests/data/A_He_test_sample.parquet")
x = table["values"].to_numpy()
L, U = metadata["L"], metadata["U"]

print("=" * 80)
print("Upper Boundary Analysis")
print("=" * 80)

# Check upper boundary
u = compute_u(x, L, U)
u_from_upper = 1 - u  # Distance from upper bound

print(f"\nSamples near upper bound U={U}:")
print(f"  Exactly at U: {np.sum(x == U):,} ({100 * np.sum(x == U) / len(x):.3f}%)")

# Check distribution near upper bound
eps_values = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 0.05, 0.1]
print("\nProximity to upper bound:")
print(f"{'Tolerance':<12} {'Count':<10} {'Fraction':<10}")
print("-" * 40)
for eps in eps_values:
    count = np.sum(u_from_upper <= eps)
    frac = count / len(x)
    print(f"{eps:<12.2e} {count:>8,} {frac:>8.5f}")

# Check actual mass curve for upper boundary
u_sorted = np.sort(u_from_upper)
tol_grid = np.linspace(0, 0.05, 501)
mass_curve = np.array([tail_mass(u_sorted, tol) for tol in tol_grid])

print("\nMass curve for upper boundary (first 10 points):")
print(f"{'Tolerance':<12} {'Mass':<12} {'Expected (uniform)':<20} {'Excess'}")
print("-" * 70)
for i in range(min(10, len(tol_grid))):
    t = tol_grid[i]
    m = mass_curve[i]
    expected = t
    excess = m / t if t > 0 else 0
    print(f"{t:<12.6f} {m:<12.6f} {expected:<20.6f} {excess:>6.2f}x")

# Compute quantile curve
quantile_grid = np.linspace(0.0005, 0.25, 50)
tol_at_quantile = np.interp(quantile_grid, mass_curve, tol_grid)

print("\nQuantile curve for upper boundary (first 10 points):")
print(f"{'Quantile':<12} {'Tolerance':<12} {'Ratio (t/q)'}")
print("-" * 50)
for i in range(min(10, len(quantile_grid))):
    q = quantile_grid[i]
    t = tol_at_quantile[i]
    ratio = t / q if q > 0 else 0
    print(f"{q:<12.6f} {t:<12.6f} {ratio:>12.2f}")
