"""Generate high-resolution matplotlib histograms for np2 dataset."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Load np2 data
data_dir = Path("tests/data")
x = pd.read_parquet(data_dir / "np2_test_sample.parquet")["values"].values
with open(data_dir / "np2_test_metadata.json") as f:
    meta = json.load(f)

L = meta["L"]
U = meta["U"]
x0 = meta["x0"]

print("Generating high-resolution plots for np2...")
print(f"Parameter: {meta['name']}")
print(f"Bounds: L={L}, U={U}, x0={x0}")
print(f"Samples: {len(x):,}")

# Filter out-of-bounds
valid_mask = (x >= L) & (x <= U)
x_valid = x[valid_mask]
n_oob = len(x) - len(x_valid)
print(f"Out-of-bounds: {n_oob} samples ({n_oob / len(x) * 100:.2f}%)")

# Compute u-space
u = (x_valid - L) / (U - L)

# Create figure with multiple subplots
fig = plt.figure(figsize=(16, 12))

# 1. Raw data distribution (1000 bins)
ax1 = plt.subplot(3, 2, 1)
bins_raw = np.linspace(L, U, 1001)
counts, edges, _ = ax1.hist(x_valid, bins=bins_raw, color="steelblue", edgecolor="none", alpha=0.7)
ax1.set_xlabel("Raw value (x)", fontsize=12)
ax1.set_ylabel("Count", fontsize=12)
ax1.set_title(
    f"np2 Raw Distribution (1000 bins)\n{len(x_valid):,} samples in [{L}, {U}]",
    fontsize=13,
    fontweight="bold",
)
ax1.grid(True, alpha=0.3)
ax1.axvline(L, color="red", linestyle="--", linewidth=1, alpha=0.5, label=f"L={L}")
if x0 is not None:
    ax1.axvline(x0, color="orange", linestyle="--", linewidth=1, alpha=0.5, label=f"x0={x0}")
ax1.legend()

# 2. Raw data - zoomed to first 10% of range
ax2 = plt.subplot(3, 2, 2)
range_10pct = L + 0.1 * (U - L)
mask_zoom = x_valid < range_10pct
bins_zoom = np.linspace(L, range_10pct, 201)
ax2.hist(x_valid[mask_zoom], bins=bins_zoom, color="darkred", edgecolor="none", alpha=0.7)
ax2.set_xlabel("Raw value (x)", fontsize=12)
ax2.set_ylabel("Count", fontsize=12)
ax2.set_title(
    f"np2 Near Lower Boundary (zoomed)\nFirst 10% of range: [{L:.2f}, {range_10pct:.2f}]",
    fontsize=13,
    fontweight="bold",
)
ax2.grid(True, alpha=0.3)
ax2.axvline(L, color="red", linestyle="--", linewidth=1, alpha=0.5, label=f"L={L}")
ax2.legend()

# 3. U-space full distribution (1000 bins)
ax3 = plt.subplot(3, 2, 3)
bins_u = np.linspace(0, 1, 1001)
ax3.hist(u, bins=bins_u, color="mediumseagreen", edgecolor="none", alpha=0.7)
ax3.set_xlabel("Normalized u = (x-L)/(U-L)", fontsize=12)
ax3.set_ylabel("Count", fontsize=12)
ax3.set_title("np2 U-Space Distribution (1000 bins)", fontsize=13, fontweight="bold")
ax3.grid(True, alpha=0.3)
ax3.axvline(0, color="red", linestyle="--", linewidth=1, alpha=0.5, label="u=0 (L)")
ax3.axvline(1, color="red", linestyle="--", linewidth=1, alpha=0.5, label="u=1 (U)")
ax3.legend()

# 4. U-space - zoomed to u < 0.1
ax4 = plt.subplot(3, 2, 4)
mask_u_zoom = u < 0.1
bins_u_zoom = np.linspace(0, 0.1, 201)
ax4.hist(u[mask_u_zoom], bins=bins_u_zoom, color="darkgreen", edgecolor="none", alpha=0.7)
ax4.set_xlabel("Normalized u = (x-L)/(U-L)", fontsize=12)
ax4.set_ylabel("Count", fontsize=12)
ax4.set_title("np2 U-Space Near Lower Boundary (u < 0.1)", fontsize=13, fontweight="bold")
ax4.grid(True, alpha=0.3)
ax4.axvline(0, color="red", linestyle="--", linewidth=1, alpha=0.5, label="u=0 (L)")
ax4.axvline(0.01, color="orange", linestyle="--", linewidth=1, alpha=0.5, label="u=0.01")
ax4.legend()

# 5. U-space - extreme zoom u < 0.02
ax5 = plt.subplot(3, 2, 5)
mask_u_extreme = u < 0.02
bins_u_extreme = np.linspace(0, 0.02, 201)
ax5.hist(u[mask_u_extreme], bins=bins_u_extreme, color="purple", edgecolor="none", alpha=0.7)
ax5.set_xlabel("Normalized u = (x-L)/(U-L)", fontsize=12)
ax5.set_ylabel("Count", fontsize=12)
ax5.set_title("np2 U-Space Extreme Zoom (u < 0.02)", fontsize=13, fontweight="bold")
ax5.grid(True, alpha=0.3)
ax5.axvline(0, color="red", linestyle="--", linewidth=2, alpha=0.7, label="u=0 (L)")
ax5.axvline(0.001, color="orange", linestyle="--", linewidth=1, alpha=0.5, label="u=0.001")
ax5.axvline(0.01, color="yellow", linestyle="--", linewidth=1, alpha=0.5, label="u=0.01")
ax5.legend()

# 6. Summary statistics text
ax6 = plt.subplot(3, 2, 6)
ax6.axis("off")

# Compute statistics
near_L_001 = np.sum(u < 0.001)
near_L_01 = np.sum(u < 0.01)
near_L_02 = np.sum(u < 0.02)
near_L_05 = np.sum(u < 0.05)

summary_text = f"""np2 (BEAM DENSITY) - SUMMARY STATISTICS

Total samples: {len(x):,}
Out-of-bounds: {n_oob:,} ({n_oob / len(x) * 100:.2f}%)
Valid samples: {len(x_valid):,}

LOWER BOUNDARY CONCENTRATION:
  u < 0.001: {near_L_001:6,} samples ({100 * near_L_001 / len(u):5.2f}%)
  u < 0.010: {near_L_01:6,} samples ({100 * near_L_01 / len(u):5.2f}%)
  u < 0.020: {near_L_02:6,} samples ({100 * near_L_02 / len(u):5.2f}%)
  u < 0.050: {near_L_05:6,} samples ({100 * near_L_05 / len(u):5.2f}%)

INTERPRETATION:
{"✓ EXTREME lower boundary stickiness" if near_L_01 / len(u) > 0.5 else "? Moderate concentration"}
{"  (>50% within u<0.01)" if near_L_01 / len(u) > 0.5 else ""}

METADATA STATUS:
  Current: expected_lower_stickiness = false
  Should be: expected_lower_stickiness = true

This is NOT a continuous distribution.
This is a clear boundary stickiness spike.
"""

ax6.text(
    0.1,
    0.5,
    summary_text,
    fontsize=11,
    family="monospace",
    verticalalignment="center",
    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
)

plt.tight_layout()

# Save figure
output_path = Path("figures/np2_highres_histogram_analysis.png")
output_path.parent.mkdir(exist_ok=True)
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\nSaved: {output_path}")

# Save high-resolution version
output_path_hires = Path("figures/np2_highres_histogram_analysis_hires.png")
plt.savefig(output_path_hires, dpi=300, bbox_inches="tight")
print(f"Saved: {output_path_hires}")

plt.close()

print("\n✓ High-resolution plots generated successfully")
