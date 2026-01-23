#!/usr/bin/env python
"""Debug elbow detection for A_He data."""

import json

import numpy as np
import pyarrow.parquet as pq

from fitqc.boundary import _compute_quantile_curves_boundary, compute_u, tail_mass

# Load A_He data
with open("tests/data/A_He_test_metadata.json") as f:
    metadata = json.load(f)

table = pq.read_table("tests/data/A_He_test_sample.parquet")
x = table["values"].to_numpy()
L, U = metadata["L"], metadata["U"]

# Compute u and sort
u = compute_u(x, L, U)
u_sorted = np.sort(u)

# Setup grids (same as default config)
tol_grid = np.linspace(0, 0.05, 501)
quantile_grid = np.linspace(0.0005, 0.25, 50)

print("=" * 80)
print("Debugging Elbow Detection for A_He Data")
print("=" * 80)
print("\nData characteristics:")
print(f"  N samples: {len(x):,}")
print(f"  Exactly at L=0: {np.sum(x == 0):,} ({100 * np.sum(x == 0) / len(x):.3f}%)")
print(f"  u_min: {u_sorted[0]:.15f}")
print(f"  u_max: {u_sorted[-1]:.15f}")

print(f"\n{'=' * 80}")
print("Quantile Curve Computation")
print("=" * 80)

# Compute quantile curves
tol_at_quantile, elbows = _compute_quantile_curves_boundary(u_sorted, tol_grid, quantile_grid)

print(f"\nElbow detected: {elbows[0]}")
print(f"Type of elbow: {type(elbows[0])}")

# Show first 10 (quantile, tolerance) pairs
print("\nFirst 10 (quantile, tolerance) pairs:")
print(f"{'Index':<7} {'Quantile':<12} {'Tolerance':<12} {'Ratio (tol/q)':<15}")
print("-" * 60)
for i in range(min(10, len(quantile_grid))):
    q = quantile_grid[i]
    t = tol_at_quantile[i]
    ratio = t / q if q > 0 else np.inf
    marker = " <-- ELBOW" if elbows[0] is not None and abs(q - elbows[0]) < 1e-10 else ""
    print(f"{i:<7} {q:<12.6f} {t:<12.6f} {ratio:<15.2f}{marker}")

print(f"\n{'=' * 80}")
print("Understanding the Elbow Value")
print("=" * 80)

if elbows[0] is not None:
    print(f"\nDetected elbow value: {elbows[0]:.6f}")
    print(f"tol_grid range: [{tol_grid[0]:.6f}, {tol_grid[-1]:.6f}]")
    print(f"quantile_grid range: [{quantile_grid[0]:.6f}, {quantile_grid[-1]:.6f}]")
    print(
        f"\nIs elbow in quantile_grid range? {quantile_grid[0] <= elbows[0] <= quantile_grid[-1]}"
    )
    print(f"Is elbow in tol_grid range? {tol_grid[0] <= elbows[0] <= tol_grid[-1]}")

    # Find where this elbow value appears
    if quantile_grid[0] <= elbows[0] <= quantile_grid[-1]:
        print("\n=> Elbow appears to be a QUANTILE value")
        # Find corresponding tolerance
        idx = np.argmin(np.abs(quantile_grid - elbows[0]))
        print(f"   At quantile={quantile_grid[idx]:.6f}, tolerance={tol_at_quantile[idx]:.6f}")
    elif tol_grid[0] <= elbows[0] <= tol_grid[-1]:
        print("\n=> Elbow appears to be a TOLERANCE value")

print(f"\n{'=' * 80}")
print("Mass Curve Analysis")
print("=" * 80)

# Compute mass at different tolerances
mass_curve = np.array([tail_mass(u_sorted, t) for t in tol_grid])

print("\nFirst 10 tolerance values and corresponding mass:")
print(f"{'Tolerance':<12} {'Mass P(u<tol)':<15} {'Expected (uniform)':<20} {'Excess'}")
print("-" * 70)
for i in range(min(10, len(tol_grid))):
    t = tol_grid[i]
    m = mass_curve[i]
    expected = t  # For uniform distribution
    excess = m / t if t > 0 else np.inf
    print(f"{t:<12.6f} {m:<15.6f} {expected:<20.6f} {excess:>6.1f}x")
