"""Generate ultra-high-resolution histogram for A_He dataset inspection."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Load A_He data
data_dir = Path("tests/data")
x = pd.read_parquet(data_dir / "A_He_test_sample.parquet")["values"].values
with open(data_dir / "A_He_test_metadata.json") as f:
    meta = json.load(f)

L = meta["L"]
U = meta["U"]
x0 = meta.get("x0")

print("Generating ultra-high-resolution plots for A_He...")
print(f"Parameter: {meta['name']}")
print(f"Bounds: L={L}, U={U}, x0={x0}")
print(f"Samples: {len(x):,}")
print(f"Range: [{x.min():.6f}, {x.max():.6f}]")

# Compute u-space
u = (x - L) / (U - L)

# Statistics
print("\nData Statistics:")
print(f"  Mean: {x.mean():.4f}")
print(f"  Median: {np.median(x):.4f}")
print(f"  Std: {x.std():.4f}")
print(f"  Min: {x.min():.6f}")
print(f"  Max: {x.max():.6f}")

print("\nBoundary Analysis:")
at_L = np.sum(x == L)
at_U = np.sum(x == U)
near_L_001 = np.sum(u < 0.001)
near_L_01 = np.sum(u < 0.01)
near_U_999 = np.sum(u > 0.999)
near_U_99 = np.sum(u > 0.99)

print(f"  Exactly at L={L}: {at_L} samples")
print(f"  Exactly at U={U}: {at_U} samples")
print(f"  u < 0.001: {near_L_001:,} ({100 * near_L_001 / len(x):.2f}%)")
print(f"  u < 0.010: {near_L_01:,} ({100 * near_L_01 / len(x):.2f}%)")
print(f"  u > 0.999: {near_U_999:,} ({100 * near_U_999 / len(x):.2f}%)")
print(f"  u > 0.990: {near_U_99:,} ({100 * near_U_99 / len(x):.2f}%)")

# Check for out-of-bounds
out_of_bounds_mask = (u < 0) | (u > 1)
n_out_of_bounds = np.sum(out_of_bounds_mask)
n_below = np.sum(u < 0)
n_above = np.sum(u > 1)

print("\nOut-of-Bounds Check:")
print(f"  Below L (u<0): {n_below}")
print(f"  Above U (u>1): {n_above}")
print(f"  Total OOB: {n_out_of_bounds}")

# Create comprehensive multi-panel figure
fig = plt.figure(figsize=(18, 14))

# 1. Raw data - full range (2000 bins)
ax1 = plt.subplot(3, 3, 1)
bins_raw_full = np.linspace(L, U, 2001)
counts_full, edges_full, _ = ax1.hist(
    x, bins=bins_raw_full, color="steelblue", edgecolor="none", alpha=0.7
)
ax1.axvline(L, color="red", linestyle="--", linewidth=1.5, label=f"L={L}")
ax1.axvline(U, color="red", linestyle="--", linewidth=1.5, label=f"U={U}")
if x0 is not None:
    ax1.axvline(x0, color="orange", linestyle="--", linewidth=1.5, label=f"x0={x0}")
ax1.set_xlabel("Raw value (x)", fontsize=10)
ax1.set_ylabel("Count", fontsize=10)
ax1.set_title(f"A_He Full Range (2000 bins)\n[{L}, {U}]", fontsize=11, fontweight="bold")
ax1.legend(fontsize=8)
ax1.grid(True, alpha=0.3)

# 2. Raw data - full range (2000 bins, LOG SCALE)
ax2 = plt.subplot(3, 3, 2)
ax2.hist(x, bins=bins_raw_full, color="steelblue", edgecolor="none", alpha=0.7)
ax2.axvline(L, color="red", linestyle="--", linewidth=1.5)
ax2.axvline(U, color="red", linestyle="--", linewidth=1.5)
if x0 is not None:
    ax2.axvline(x0, color="orange", linestyle="--", linewidth=1.5)
ax2.set_xlabel("Raw value (x)", fontsize=10)
ax2.set_ylabel("Count (log scale)", fontsize=10)
ax2.set_yscale("log")
ax2.set_title("A_He Full Range (2000 bins, LOG)", fontsize=11, fontweight="bold")
ax2.grid(True, alpha=0.3, which="both")

# 3. Near lower boundary - extreme zoom (x < L + 0.1)
ax3 = plt.subplot(3, 3, 3)
zoom_threshold_lower = L + 0.1
mask_zoom_lower = x < zoom_threshold_lower
x_zoom_lower = x[mask_zoom_lower]
if len(x_zoom_lower) > 0:
    bins_zoom_lower = np.linspace(L, zoom_threshold_lower, 201)
    ax3.hist(x_zoom_lower, bins=bins_zoom_lower, color="darkgreen", edgecolor="none", alpha=0.7)
    ax3.axvline(L, color="red", linestyle="--", linewidth=2)
    ax3.set_xlabel("Raw value (x)", fontsize=10)
    ax3.set_ylabel("Count", fontsize=10)
    ax3.set_title(
        f"Near Lower Boundary\nx < {zoom_threshold_lower} ({len(x_zoom_lower):,} samples)",
        fontsize=11,
        fontweight="bold",
    )
    ax3.grid(True, alpha=0.3)
else:
    ax3.text(0.5, 0.5, "No samples in range", ha="center", va="center", transform=ax3.transAxes)
    ax3.set_title(
        f"Near Lower Boundary\nx < {zoom_threshold_lower}", fontsize=11, fontweight="bold"
    )

# 4. U-space distribution (2000 bins)
ax4 = plt.subplot(3, 3, 4)
bins_u_full = np.linspace(0, 1, 2001)
ax4.hist(u, bins=bins_u_full, color="purple", edgecolor="none", alpha=0.7)
ax4.axvline(0, color="red", linestyle="--", linewidth=1.5, label="u=0 (L)")
ax4.axvline(1, color="red", linestyle="--", linewidth=1.5, label="u=1 (U)")
ax4.set_xlabel("Normalized u = (x-L)/(U-L)", fontsize=10)
ax4.set_ylabel("Count", fontsize=10)
ax4.set_title("U-Space Full Distribution (2000 bins)", fontsize=11, fontweight="bold")
ax4.legend(fontsize=8)
ax4.grid(True, alpha=0.3)

# 5. U-space LOG scale
ax5 = plt.subplot(3, 3, 5)
ax5.hist(u, bins=bins_u_full, color="purple", edgecolor="none", alpha=0.7)
ax5.axvline(0, color="red", linestyle="--", linewidth=1.5)
ax5.axvline(1, color="red", linestyle="--", linewidth=1.5)
ax5.set_xlabel("Normalized u = (x-L)/(U-L)", fontsize=10)
ax5.set_ylabel("Count (log scale)", fontsize=10)
ax5.set_yscale("log")
ax5.set_title("U-Space Full Distribution (2000 bins, LOG)", fontsize=11, fontweight="bold")
ax5.grid(True, alpha=0.3, which="both")

# 6. U-space extreme zoom lower (u < 0.02)
ax6 = plt.subplot(3, 3, 6)
u_zoom_extreme_lower = u[u < 0.02]
bins_u_extreme_lower = np.linspace(0, 0.02, 201)
if len(u_zoom_extreme_lower) > 0:
    ax6.hist(
        u_zoom_extreme_lower,
        bins=bins_u_extreme_lower,
        color="darkred",
        edgecolor="none",
        alpha=0.7,
    )
    ax6.axvline(0, color="red", linestyle="--", linewidth=2)
    ax6.axvline(0.001, color="orange", linestyle=":", linewidth=1.5, label="u=0.001")
    ax6.axvline(0.01, color="yellow", linestyle=":", linewidth=1.5, label="u=0.01")
    ax6.set_xlabel("Normalized u", fontsize=10)
    ax6.set_ylabel("Count", fontsize=10)
    ax6.set_title(
        f"U-Space Near Lower (u < 0.02)\n{len(u_zoom_extreme_lower):,} samples",
        fontsize=11,
        fontweight="bold",
    )
    ax6.legend(fontsize=8)
    ax6.grid(True, alpha=0.3)
else:
    ax6.text(0.5, 0.5, "No samples in range", ha="center", va="center", transform=ax6.transAxes)

# 7. U-space zoom upper (u > 0.98)
ax7 = plt.subplot(3, 3, 7)
u_zoom_upper = u[u > 0.98]
bins_u_zoom_upper = np.linspace(0.98, 1.0, 201)
if len(u_zoom_upper) > 0:
    ax7.hist(u_zoom_upper, bins=bins_u_zoom_upper, color="darkblue", edgecolor="none", alpha=0.7)
    ax7.axvline(1, color="red", linestyle="--", linewidth=2)
    ax7.axvline(0.999, color="orange", linestyle=":", linewidth=1.5, label="u=0.999")
    ax7.axvline(0.99, color="yellow", linestyle=":", linewidth=1.5, label="u=0.99")
    ax7.set_xlabel("Normalized u", fontsize=10)
    ax7.set_ylabel("Count", fontsize=10)
    ax7.set_title(
        f"U-Space Near Upper (u > 0.98)\n{len(u_zoom_upper):,} samples",
        fontsize=11,
        fontweight="bold",
    )
    ax7.legend(fontsize=8)
    ax7.grid(True, alpha=0.3)
else:
    ax7.text(0.5, 0.5, "No samples in range", ha="center", va="center", transform=ax7.transAxes)

# 8. Cumulative distribution (to see concentration patterns)
ax8 = plt.subplot(3, 3, 8)
u_sorted = np.sort(u)
cumulative = np.arange(1, len(u_sorted) + 1) / len(u_sorted)
ax8.plot(u_sorted, cumulative, color="green", linewidth=1.5)
ax8.axvline(0.001, color="orange", linestyle=":", linewidth=1, label="u=0.001")
ax8.axvline(0.01, color="red", linestyle=":", linewidth=1, label="u=0.01")
ax8.axhline(near_L_001 / len(u), color="orange", linestyle=":", linewidth=1, alpha=0.5)
ax8.axhline(near_L_01 / len(u), color="red", linestyle=":", linewidth=1, alpha=0.5)
ax8.set_xlabel("Normalized u", fontsize=10)
ax8.set_ylabel("Cumulative Fraction", fontsize=10)
ax8.set_title("Cumulative Distribution (CDF)", fontsize=11, fontweight="bold")
ax8.legend(fontsize=8)
ax8.grid(True, alpha=0.3)
ax8.set_xlim(0, 0.05)  # Focus on lower boundary region

# 9. Summary statistics text
ax9 = plt.subplot(3, 3, 9)
ax9.axis("off")

summary_text = f"""A_He (ALPHA PARTICLE ABUNDANCE) - DETAILED STATISTICS

Total samples: {len(x):,}
Bounds: L={L}, U={U}
x0 (initial guess): {x0}

RAW DATA RANGE:
  Min: {x.min():.6f}
  Max: {x.max():.6f}
  Mean: {x.mean():.4f}
  Median: {np.median(x):.4f}
  Std: {x.std():.4f}

BOUNDARY CONCENTRATION:
  At L={L} exactly: {at_L:,} samples
  At U={U} exactly: {at_U:,} samples

  Lower (u < 0.001): {near_L_001:,} ({100 * near_L_001 / len(x):.3f}%)
  Lower (u < 0.010): {near_L_01:,} ({100 * near_L_01 / len(x):.3f}%)
  Upper (u > 0.999): {near_U_999:,} ({100 * near_U_999 / len(x):.3f}%)
  Upper (u > 0.990): {near_U_99:,} ({100 * near_U_99 / len(x):.3f}%)

OUT-OF-BOUNDS:
  Below L (u<0): {n_below:,}
  Above U (u>1): {n_above:,}
  Total: {n_out_of_bounds:,}

METADATA EXPECTATIONS:
  expected_lower_stickiness: {meta.get("expected_lower_stickiness")}
  expected_upper_stickiness: {meta.get("expected_upper_stickiness")}
"""

ax9.text(
    0.05,
    0.5,
    summary_text,
    fontsize=9,
    family="monospace",
    verticalalignment="center",
    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
)

plt.suptitle(
    "A_He Ultra-High-Resolution Analysis (>2000 bins)", fontsize=14, fontweight="bold", y=0.995
)
plt.tight_layout(rect=[0, 0, 1, 0.99])

# Save
output_path = Path("figures/A_He_ultrahighres_analysis.png")
output_path.parent.mkdir(exist_ok=True)
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\nSaved: {output_path}")

output_path_hires = Path("figures/A_He_ultrahighres_analysis_hires.png")
plt.savefig(output_path_hires, dpi=300, bbox_inches="tight")
print(f"Saved: {output_path_hires}")

plt.close()

print("\n✓ Ultra-high-resolution analysis complete")
