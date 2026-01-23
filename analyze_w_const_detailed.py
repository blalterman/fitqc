"""Detailed analysis of w_const to verify out-of-bounds samples."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

# Load w_const data
data_dir = Path("tests/data")
x = pd.read_parquet(data_dir / "w_const_test_sample.parquet")["values"].values
with open(data_dir / "w_const_test_metadata.json") as f:
    meta = json.load(f)

L = meta["L"]
U = meta["U"]

print("=" * 100)
print("w_const (THERMAL SPEED) - DETAILED ANALYSIS")
print("=" * 100)
print(f"\nParameter: {meta['name']}")
print(f"Bounds: L={L}, U={U}")
print(f"Samples: {len(x):,}")
print(f"Notes: {meta.get('notes', 'N/A')}")

# Check out-of-bounds
below_L = x < L
above_U = x > U
in_bounds = (x >= L) & (x <= U)

n_below = np.sum(below_L)
n_above = np.sum(above_U)
n_valid = np.sum(in_bounds)

print("\n" + "=" * 100)
print("OUT-OF-BOUNDS ANALYSIS")
print("=" * 100)
print(f"\nBelow L={L}: {n_below} samples ({n_below / len(x) * 100:.2f}%)")
print(f"Above U={U}: {n_above} samples ({n_above / len(x) * 100:.2f}%)")
print(f"In bounds:   {n_valid} samples ({n_valid / len(x) * 100:.2f}%)")

# Analyze out-of-bounds samples
if n_below > 0:
    x_below = x[below_L]
    print("\nOut-of-bounds samples BELOW L:")
    print(f"  Min: {x_below.min():.4f}")
    print(f"  Max: {x_below.max():.4f}")
    print(f"  Mean: {x_below.mean():.4f}")
    print(f"  Median: {np.median(x_below):.4f}")
    print(f"  At exactly 0.0: {np.sum(x_below == 0.0)}")

if n_above > 0:
    x_above = x[above_U]
    print("\nOut-of-bounds samples ABOVE U:")
    print(f"  Min: {x_above.min():.4f}")
    print(f"  Max: {x_above.max():.4f}")
    print(f"  Mean: {x_above.mean():.4f}")
    print(f"  Median: {np.median(x_above):.4f}")

print("\n" + "=" * 100)
print("RAW DATA DISTRIBUTION (high resolution)")
print("=" * 100)

# Create high-resolution histogram including out-of-bounds region
x_min = min(x.min(), L - 1)
x_max = max(x.max(), U + 1)

# Dense bins near boundaries and in out-of-bounds regions
bins_raw = np.concatenate(
    [
        np.linspace(x_min, L, 21),  # Out-of-bounds below L
        np.linspace(L, L + 10, 21),  # Near lower bound
        np.linspace(L + 10, U - 10, 20),  # Middle
        np.linspace(U - 10, U, 21),  # Near upper bound
        np.linspace(U, x_max, 21),  # Out-of-bounds above U
    ]
)

hist_raw, edges = np.histogram(x, bins=bins_raw)
max_count = hist_raw.max()

print(f"\nHistogram: {len(bins_raw) - 1} bins")
print(f"Range: [{x_min:.1f}, {x_max:.1f}]")
print(f"Max count: {max_count}")
print("\nShowing bins with >0 samples:")
print()

for i in range(len(hist_raw)):
    if hist_raw[i] == 0:
        continue
    bin_left = edges[i]
    bin_right = edges[i + 1]
    count = hist_raw[i]
    pct = 100 * count / len(x)
    bar_len = int(60 * count / max_count) if max_count > 0 else 0
    bar = "#" * bar_len

    # Mark special regions
    if bin_right <= L:
        region = "[OUT-OF-BOUNDS: BELOW L]"
    elif bin_left >= U:
        region = "[OUT-OF-BOUNDS: ABOVE U]"
    elif abs(bin_left - L) < 1 or abs(bin_right - L) < 1:
        region = "[NEAR L]"
    elif abs(bin_left - U) < 1 or abs(bin_right - U) < 1:
        region = "[NEAR U]"
    else:
        region = ""

    print(f"{bin_left:8.2f} - {bin_right:8.2f}: {count:6d} ({pct:5.2f}%) | {bar} {region}")

print("\n" + "=" * 100)
print("U-SPACE DISTRIBUTION (valid samples only)")
print("=" * 100)

x_valid = x[in_bounds]
u = (x_valid - L) / (U - L)

# High resolution near boundaries
bins_u = np.concatenate(
    [
        np.linspace(0, 0.01, 21),
        np.linspace(0.01, 0.1, 20),
        np.linspace(0.1, 0.9, 20),
        np.linspace(0.9, 0.99, 20),
        np.linspace(0.99, 1.0, 21),
    ]
)

hist_u, edges_u = np.histogram(u, bins=bins_u)
max_count_u = hist_u.max()

print(f"\nHistogram: {len(bins_u) - 1} bins, dense near boundaries")
print(f"Max count: {max_count_u}")
print()

# Show lower boundary region
print("Lower boundary region (u < 0.1):")
for i in range(len(hist_u)):
    if edges_u[i] >= 0.1:
        break
    bin_left = edges_u[i]
    bin_right = edges_u[i + 1]
    count = hist_u[i]
    pct = 100 * count / len(u)
    bar_len = int(60 * count / max_count_u) if max_count_u > 0 else 0
    bar = "#" * bar_len
    print(f"{bin_left:.6f} - {bin_right:.6f}: {count:6d} ({pct:5.2f}%) | {bar}")

print()
print("Upper boundary region (u > 0.9):")
for i in range(len(hist_u)):
    if edges_u[i] < 0.9:
        continue
    bin_left = edges_u[i]
    bin_right = edges_u[i + 1]
    count = hist_u[i]
    pct = 100 * count / len(u)
    bar_len = int(60 * count / max_count_u) if max_count_u > 0 else 0
    bar = "#" * bar_len
    print(f"{bin_left:.6f} - {bin_right:.6f}: {count:6d} ({pct:5.2f}%) | {bar}")

print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)

# Proximity statistics for valid samples
near_L_1e3 = np.sum(u < 1e-3)
near_L_1e2 = np.sum(u < 1e-2)
near_U_1e3 = np.sum(u > 1 - 1e-3)
near_U_1e2 = np.sum(u > 1 - 1e-2)

print("\nValid samples boundary proximity:")
print(f"  Lower (u < 1e-3): {near_L_1e3:6d} ({100 * near_L_1e3 / len(u):5.2f}%)")
print(f"  Lower (u < 1e-2): {near_L_1e2:6d} ({100 * near_L_1e2 / len(u):5.2f}%)")
print(f"  Upper (u > 1-1e-3): {near_U_1e3:6d} ({100 * near_U_1e3 / len(u):5.2f}%)")
print(f"  Upper (u > 1-1e-2): {near_U_1e2:6d} ({100 * near_U_1e2 / len(u):5.2f}%)")

print("\n" + "=" * 100)
print("INTERPRETATION")
print("=" * 100)

if n_below > 0:
    print("\n⚠️  OUT-OF-BOUNDS SAMPLES BELOW L:")
    print(f"  {n_below} samples ({n_below / len(x) * 100:.2f}%) are below L={L}")
    x_below = x[below_L]
    if np.sum(x_below == 0.0) > n_below * 0.9:
        print("  Most samples at exactly 0.0 → Likely FAILED FITS (similar to np1)")
    else:
        print(f"  Samples distributed in range [{x_below.min():.2f}, {x_below.max():.2f}]")
        print("  This may indicate a different kind of data quality issue")

if near_U_1e2 / len(u) > 0.005:
    print("\n✓ UPPER BOUNDARY STICKINESS DETECTED:")
    print(f"  {near_U_1e2} samples ({100 * near_U_1e2 / len(u):.2f}%) within u>0.99")
    print("  This confirms expected_upper_stickiness=true in metadata")
else:
    print("\n✗ No significant upper boundary stickiness")

print()
