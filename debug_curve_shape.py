#!/usr/bin/env python
"""Analyze the full (quantile, tolerance) curve to understand elbow detection."""
import numpy as np
import pyarrow.parquet as pq
import json
from fitqc.boundary import _compute_quantile_curves_boundary, compute_u, tail_mass
from fitqc.selection import select_elbow

# Load A_He data
with open('tests/data/A_He_test_metadata.json', 'r') as f:
    metadata = json.load(f)

table = pq.read_table('tests/data/A_He_test_sample.parquet')
x = table['values'].to_numpy()
L, U = metadata['L'], metadata['U']

# Compute u and sort
u = compute_u(x, L, U)
u_sorted = np.sort(u)

# Setup grids
tol_grid = np.linspace(0, 0.05, 501)
quantile_grid = np.linspace(0.0005, 0.25, 50)

print("="*80)
print("Full (Quantile, Tolerance) Curve Analysis")
print("="*80)

# Compute quantile curves
mass_curve = np.array([tail_mass(u_sorted, t) for t in tol_grid])
tol_at_quantile = np.interp(quantile_grid, mass_curve, tol_grid)

# Show full curve
print(f"\nFull (quantile, tolerance) relationship:")
print(f"{'Index':<7} {'Quantile':<12} {'Tolerance':<12} {'Ratio':<12} {'Derivative'}")
print("-"*70)

for i in range(len(quantile_grid)):
    q = quantile_grid[i]
    t = tol_at_quantile[i]
    ratio = t / q if q > 0 else 0

    # Compute derivative (slope)
    if i > 0:
        dq = q - quantile_grid[i-1]
        dt = t - tol_at_quantile[i-1]
        derivative = dt / dq if dq > 0 else 0
    else:
        derivative = 0

    print(f"{i:<7} {q:<12.6f} {t:<12.6f} {ratio:<12.2f} {derivative:<12.6f}")

# Detect elbow
elbow_q = select_elbow(quantile_grid, tol_at_quantile, curve="concave", direction="increasing")

print(f"\n{'='*80}")
print(f"Elbow Detection Result")
print(f"{'='*80}")
print(f"Detected elbow (quantile): {elbow_q}")

if elbow_q is not None:
    # Find index
    idx = np.argmin(np.abs(quantile_grid - elbow_q))
    print(f"Index in grid: {idx}")
    print(f"Quantile at elbow: {quantile_grid[idx]:.6f}")
    print(f"Tolerance at elbow: {tol_at_quantile[idx]:.6f}")

# Analyze what's happening around the true pileup boundary
pileup_frac = 0.01642  # 1.642% at exactly L=0
print(f"\n{'='*80}")
print(f"Analysis Around True Pileup Boundary (q ≈ {pileup_frac:.4f})")
print(f"{'='*80}")

# Find quantiles around the pileup
for i, q in enumerate(quantile_grid):
    if 0.010 <= q <= 0.030:
        t = tol_at_quantile[i]
        print(f"q={q:.6f}: t={t:.6f}, ratio={t/q if q > 0 else 0:.2f}")

# Try different elbow detection parameters
print(f"\n{'='*80}")
print(f"Testing Different Elbow Detection Strategies")
print(f"{'='*80}")

strategies = [
    ("concave", "increasing", False),
    ("convex", "increasing", False),
    ("concave", "decreasing", False),
    ("convex", "decreasing", False),
]

for curve, direction, log_x in strategies:
    elbow = select_elbow(quantile_grid, tol_at_quantile, curve=curve, direction=direction, log_x=log_x)
    print(f"curve={curve:<8} direction={direction:<10} log_x={log_x:<5} => elbow={elbow}")

# Manually look for the transition point
print(f"\n{'='*80}")
print(f"Manual Transition Detection")
print(f"{'='*80}")

# The transition should be where tolerance starts to deviate from 0
# Find first point where t > 0
for i, (q, t) in enumerate(zip(quantile_grid, tol_at_quantile)):
    if t > 1e-6:
        print(f"First non-zero tolerance at index {i}:")
        print(f"  quantile={q:.6f}, tolerance={t:.6f}")
        if i > 0:
            print(f"  Previous: quantile={quantile_grid[i-1]:.6f}, tolerance={tol_at_quantile[i-1]:.6f}")
        break

# Look for where ratio (t/q) stabilizes
print(f"\nLooking for where ratio t/q stabilizes:")
ratios = tol_at_quantile / quantile_grid
for i in range(len(quantile_grid)):
    if i > 0:
        ratio_change = abs(ratios[i] - ratios[i-1])
        if i < 15:  # First 15 points
            print(f"  i={i}: q={quantile_grid[i]:.6f}, ratio={ratios[i]:.2f}, change={ratio_change:.3f}")
