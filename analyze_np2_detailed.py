"""Detailed analysis of np2 to check for continuous vs spike patterns."""

import json
import numpy as np
import pandas as pd
from pathlib import Path

# Load np2 data
data_dir = Path("tests/data")
x = pd.read_parquet(data_dir / "np2_test_sample.parquet")["values"].values
with open(data_dir / "np2_test_metadata.json") as f:
    meta = json.load(f)

L = meta["L"]
U = meta["U"]
x0 = meta["x0"]

print("=" * 100)
print("np2 (BEAM DENSITY) - DETAILED ANALYSIS")
print("=" * 100)
print(f"\nParameter: {meta['name']}")
print(f"Bounds: L={L}, U={U}, x0={x0}")
print(f"Samples: {len(x):,}")
print(f"Notes: {meta.get('notes', 'N/A')}")

# Filter out-of-bounds for transformed analysis
valid_mask = (x >= L) & (x <= U)
x_valid = x[valid_mask]
n_oob = len(x) - len(x_valid)
print(f"\nOut-of-bounds: {n_oob} samples ({n_oob/len(x)*100:.2f}%)")

# Compute transforms
u = (x_valid - L) / (U - L)
z = np.abs(x_valid - x0) / (U - L) if x0 is not None else None

print("\n" + "=" * 100)
print("RAW DATA DISTRIBUTION (valid samples only)")
print("=" * 100)

# Create histogram of raw data
bins_raw = np.linspace(L, U, 51)
hist_raw, edges = np.histogram(x_valid, bins=bins_raw)
max_count = hist_raw.max()

print(f"\nHistogram: {len(bins_raw)-1} bins from {L} to {U}")
print(f"Max count in any bin: {max_count}")
print()

# Print ASCII histogram
for i in range(len(hist_raw)):
    bin_left = edges[i]
    bin_right = edges[i+1]
    count = hist_raw[i]
    bar_len = int(60 * count / max_count) if max_count > 0 else 0
    bar = '#' * bar_len
    print(f"{bin_left:8.2f} - {bin_right:8.2f}: {count:6d} | {bar}")

print("\n" + "=" * 100)
print("TRANSFORMED U-SPACE DISTRIBUTION (u = (x-L)/(U-L))")
print("=" * 100)

# High resolution near lower boundary
bins_u_lower = np.concatenate([
    np.linspace(0, 0.001, 21),  # Very fine near 0
    np.linspace(0.001, 0.01, 20),
    np.linspace(0.01, 0.1, 20),
    np.linspace(0.1, 1.0, 21),
])
hist_u_lower, edges_u_lower = np.histogram(u, bins=bins_u_lower)
max_count_u = hist_u_lower.max()

print(f"\nHistogram: {len(bins_u_lower)-1} bins, dense near u=0")
print(f"Max count: {max_count_u}")
print()
print("Focus on u < 0.1 (near lower boundary):")
print()

for i in range(min(60, len(hist_u_lower))):
    if edges_u_lower[i] >= 0.1:
        break
    bin_left = edges_u_lower[i]
    bin_right = edges_u_lower[i+1]
    count = hist_u_lower[i]
    pct = 100 * count / len(u)
    bar_len = int(60 * count / max_count_u) if max_count_u > 0 else 0
    bar = '#' * bar_len
    print(f"{bin_left:.6f} - {bin_right:.6f}: {count:6d} ({pct:5.2f}%) | {bar}")

print("\n" + "=" * 100)
print("INTERIOR (Z-SPACE) DISTRIBUTION (z = |x-x0|/(U-L))")
print("=" * 100)

if z is not None:
    # High resolution near x0
    bins_z = np.concatenate([
        np.linspace(0, 0.001, 21),
        np.linspace(0.001, 0.01, 20),
        np.linspace(0.01, 0.1, 20),
        np.linspace(0.1, 0.5, 21),
    ])
    hist_z, edges_z = np.histogram(z, bins=bins_z)
    max_count_z = hist_z.max()

    print(f"\nHistogram: {len(bins_z)-1} bins, dense near z=0")
    print(f"Max count: {max_count_z}")
    print()
    print("Focus on z < 0.1 (near x0):")
    print()

    for i in range(min(60, len(hist_z))):
        if edges_z[i] >= 0.1:
            break
        bin_left = edges_z[i]
        bin_right = edges_z[i+1]
        count = hist_z[i]
        pct = 100 * count / len(z)
        bar_len = int(60 * count / max_count_z) if max_count_z > 0 else 0
        bar = '#' * bar_len
        print(f"{bin_left:.6f} - {bin_right:.6f}: {count:6d} ({pct:5.2f}%) | {bar}")
else:
    print("\nNo x0 defined (moment-based parameter)")

print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)

# Compute proximity statistics
near_L_1e6 = np.sum(u < 1e-6)
near_L_1e5 = np.sum(u < 1e-5)
near_L_1e4 = np.sum(u < 1e-4)
near_L_1e3 = np.sum(u < 1e-3)
near_L_1e2 = np.sum(u < 1e-2)

print(f"\nLower boundary proximity (u < threshold):")
print(f"  u < 1e-6: {near_L_1e6:6d} samples ({100*near_L_1e6/len(u):5.2f}%)")
print(f"  u < 1e-5: {near_L_1e5:6d} samples ({100*near_L_1e5/len(u):5.2f}%)")
print(f"  u < 1e-4: {near_L_1e4:6d} samples ({100*near_L_1e4/len(u):5.2f}%)")
print(f"  u < 1e-3: {near_L_1e3:6d} samples ({100*near_L_1e3/len(u):5.2f}%)")
print(f"  u < 1e-2: {near_L_1e2:6d} samples ({100*near_L_1e2/len(u):5.2f}%)")

if z is not None:
    near_x0_1e6 = np.sum(z < 1e-6)
    near_x0_1e5 = np.sum(z < 1e-5)
    near_x0_1e4 = np.sum(z < 1e-4)
    near_x0_1e3 = np.sum(z < 1e-3)
    near_x0_1e2 = np.sum(z < 1e-2)

    print(f"\nInterior proximity (z < threshold):")
    print(f"  z < 1e-6: {near_x0_1e6:6d} samples ({100*near_x0_1e6/len(z):5.2f}%)")
    print(f"  z < 1e-5: {near_x0_1e5:6d} samples ({100*near_x0_1e5/len(z):5.2f}%)")
    print(f"  z < 1e-4: {near_x0_1e4:6d} samples ({100*near_x0_1e4/len(z):5.2f}%)")
    print(f"  z < 1e-3: {near_x0_1e3:6d} samples ({100*near_x0_1e3/len(z):5.2f}%)")
    print(f"  z < 1e-2: {near_x0_1e2:6d} samples ({100*near_x0_1e2/len(z):5.2f}%)")

print("\n" + "=" * 100)
print("INTERPRETATION")
print("=" * 100)

print("\nLower boundary pattern:")
if near_L_1e2 / len(u) > 0.5:
    print("  ⚠️  EXTREME CONCENTRATION at lower boundary (>50% within u<0.01)")
    print("  This is clear boundary stickiness, NOT a continuous distribution")
elif near_L_1e3 / len(u) > 0.05:
    print("  ⚠️  STRONG CONCENTRATION at lower boundary")
    print("  This suggests boundary stickiness")
elif near_L_1e3 / len(u) > 0.001:
    print("  ⚠️  MODERATE CONCENTRATION at lower boundary")
    print("  Possible boundary stickiness or edge effect")
else:
    print("  ✓  Appears continuous/uniform near lower boundary")

if z is not None:
    print("\nInterior (x0) pattern:")
    if near_x0_1e3 / len(z) > 0.05:
        print("  ⚠️  STRONG CONCENTRATION at x0")
        print("  This suggests interior stickiness")
    elif near_x0_1e3 / len(z) > 0.001:
        print("  ⚠️  MODERATE CONCENTRATION at x0")
        print("  Possible interior stickiness")
    else:
        print("  ✓  Appears continuous/uniform near x0")

print()
