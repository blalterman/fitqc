"""High-resolution np2 analysis with ~1000 histogram bins."""

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
print("np2 (BEAM DENSITY) - HIGH RESOLUTION ANALYSIS (~1000 BINS)")
print("=" * 100)
print(f"\nParameter: {meta['name']}")
print(f"Bounds: L={L}, U={U}, x0={x0}")
print(f"Samples: {len(x):,}")

# Filter out-of-bounds
valid_mask = (x >= L) & (x <= U)
x_valid = x[valid_mask]
n_oob = len(x) - len(x_valid)
print(f"Out-of-bounds: {n_oob} samples ({n_oob/len(x)*100:.2f}%)")

print("\n" + "=" * 100)
print("RAW DATA DISTRIBUTION - HIGH RESOLUTION (1000 bins)")
print("=" * 100)

# Create 1000-bin histogram
bins_raw = np.linspace(L, U, 1001)
hist_raw, edges = np.histogram(x_valid, bins=bins_raw)
max_count = hist_raw.max()

print(f"\nHistogram: {len(bins_raw)-1} bins from {L} to {U}")
print(f"Bin width: {(U-L)/1000:.4f}")
print(f"Max count in any bin: {max_count}")
print()
print("Showing first 100 bins (near lower boundary):")
print()

for i in range(100):
    bin_left = edges[i]
    bin_right = edges[i+1]
    count = hist_raw[i]
    pct = 100 * count / len(x_valid)
    bar_len = int(60 * count / max_count) if max_count > 0 else 0
    bar = '#' * bar_len

    # Highlight bins with significant concentration
    if count > 100:
        marker = " <<<"
    else:
        marker = ""

    print(f"{bin_left:8.4f} - {bin_right:8.4f}: {count:6d} ({pct:5.2f}%) | {bar}{marker}")

print("\n" + "=" * 100)
print("TRANSFORMED U-SPACE - HIGH RESOLUTION (1000 bins)")
print("=" * 100)

u = (x_valid - L) / (U - L)

# Create 1000-bin u-space histogram
bins_u = np.linspace(0, 1, 1001)
hist_u, edges_u = np.histogram(u, bins=bins_u)
max_count_u = hist_u.max()

print(f"\nHistogram: {len(bins_u)-1} bins from 0 to 1")
print(f"Bin width: {1/1000:.6f}")
print(f"Max count: {max_count_u}")
print()
print("Showing first 100 bins (u=0 to u=0.1):")
print()

for i in range(100):
    bin_left = edges_u[i]
    bin_right = edges_u[i+1]
    count = hist_u[i]
    pct = 100 * count / len(u)
    bar_len = int(60 * count / max_count_u) if max_count_u > 0 else 0
    bar = '#' * bar_len

    if count > 100:
        marker = " <<<"
    else:
        marker = ""

    print(f"{bin_left:.6f} - {bin_right:.6f}: {count:6d} ({pct:5.2f}%) | {bar}{marker}")

print("\n" + "=" * 100)
print("INTERPRETATION")
print("=" * 100)

# Check for continuous vs spike pattern
# For continuous exponential decay, we expect smooth decrease
# For spike, we expect sharp drop-off

# Compute bin-to-bin ratios in first 50 bins
print("\nBin-to-bin ratio analysis (first 50 bins):")
print("For continuous distribution: ratios should be ~1.0")
print("For spike: ratios show sharp drop-off")
print()

ratios = []
for i in range(1, min(50, len(hist_u))):
    if hist_u[i-1] > 0:
        ratio = hist_u[i] / hist_u[i-1]
        ratios.append(ratio)
        if i <= 20:  # Show first 20
            print(f"  Bin {i-1:2d} → Bin {i:2d}: {ratio:.3f}")

if ratios:
    mean_ratio = np.mean(ratios[:20])
    std_ratio = np.std(ratios[:20])
    print(f"\nMean ratio (first 20): {mean_ratio:.3f} ± {std_ratio:.3f}")

    if mean_ratio > 0.9 and std_ratio < 0.1:
        print("→ CONTINUOUS distribution (gradual, uniform decrease)")
    else:
        print("→ SPIKE pattern (sharp, discontinuous change)")

# Summary statistics
print(f"\n" + "=" * 100)
print("SUMMARY STATISTICS")
print("=" * 100)

near_L_001 = np.sum(u < 0.001)
near_L_01 = np.sum(u < 0.01)
near_L_02 = np.sum(u < 0.02)
near_L_05 = np.sum(u < 0.05)

print(f"\nLower boundary concentration:")
print(f"  u < 0.001: {near_L_001:6d} samples ({100*near_L_001/len(u):5.2f}%)")
print(f"  u < 0.010: {near_L_01:6d} samples ({100*near_L_01/len(u):5.2f}%)")
print(f"  u < 0.020: {near_L_02:6d} samples ({100*near_L_02/len(u):5.2f}%)")
print(f"  u < 0.050: {near_L_05:6d} samples ({100*near_L_05/len(u):5.2f}%)")

print("\n" + "=" * 100)
print("CONCLUSION")
print("=" * 100)

if near_L_01 / len(u) > 0.5:
    print("\n✓ EXTREME lower boundary stickiness confirmed (>50% within u<0.01)")
    print("  This is NOT a continuous distribution")
    print("  Metadata should be corrected: expected_lower_stickiness: false → true")
else:
    print("\n? Unclear pattern - requires visual inspection")

print()
