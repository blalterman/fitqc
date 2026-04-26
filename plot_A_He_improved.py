"""Generate improved ultra-high-resolution histogram for A_He with proper z-ordering.

Key improvements:
- axvlines drawn BELOW histogram data using zorder
- Higher contrast colors
- More opaque histograms for better visibility
- Clearer visual hierarchy
"""

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

print("Generating improved ultra-high-resolution plots for A_He...")
print("Using z-order to place reference lines BELOW histogram data")
print(f"Parameter: {meta['name']}")
print(f"Bounds: L={L}, U={U}, x0={x0}")
print(f"Samples: {len(x):,}")

# Compute u-space
u = (x - L) / (U - L)

# Statistics
at_L = np.sum(x == L)
at_U = np.sum(x == U)
near_L_001 = np.sum(u < 0.001)
near_L_01 = np.sum(u < 0.01)
near_U_999 = np.sum(u > 0.999)
near_U_99 = np.sum(u > 0.99)

# Create comprehensive multi-panel figure (4 rows x 3 columns)
fig = plt.figure(figsize=(18, 18))

# 1. Raw data - full range (2000 bins)
ax1 = plt.subplot(4, 3, 1)
bins_raw_full = np.linspace(L, U, 2001)

# Draw reference lines FIRST with low z-order (will appear BEHIND)
ax1.axvline(L, color="darkred", linestyle="--", linewidth=2.5, label=f"L={L}", zorder=1, alpha=0.8)
ax1.axvline(U, color="darkred", linestyle="--", linewidth=2.5, label=f"U={U}", zorder=1, alpha=0.8)
if x0 is not None and x0 != L:  # Only draw if x0 doesn't coincide with L
    ax1.axvline(
        x0, color="darkorange", linestyle=":", linewidth=2.5, label=f"x0={x0}", zorder=1, alpha=0.8
    )

# Draw histogram ABOVE reference lines
counts_full, edges_full, _ = ax1.hist(
    x, bins=bins_raw_full, color="steelblue", edgecolor="none", alpha=0.85, zorder=2
)

ax1.set_xlabel("Raw value (x)", fontsize=10)
ax1.set_ylabel("Count", fontsize=10)
ax1.set_title(f"A_He Full Range (2000 bins)\n[{L}, {U}]", fontsize=11, fontweight="bold")
ax1.legend(fontsize=8, loc="upper right")
ax1.grid(True, alpha=0.2, zorder=0)  # Grid behind everything

# 2. Raw data - full range (2000 bins, LOG SCALE)
ax2 = plt.subplot(4, 3, 2)

# Reference lines BELOW
ax2.axvline(L, color="darkred", linestyle="--", linewidth=2.5, zorder=1, alpha=0.8)
ax2.axvline(U, color="darkred", linestyle="--", linewidth=2.5, zorder=1, alpha=0.8)
if x0 is not None and x0 != L:
    ax2.axvline(x0, color="darkorange", linestyle=":", linewidth=2.5, zorder=1, alpha=0.8)

# Histogram ABOVE
ax2.hist(x, bins=bins_raw_full, color="steelblue", edgecolor="none", alpha=0.85, zorder=2)

ax2.set_xlabel("Raw value (x)", fontsize=10)
ax2.set_ylabel("Count (log scale)", fontsize=10)
ax2.set_yscale("log")
ax2.set_title("A_He Full Range (2000 bins, LOG)", fontsize=11, fontweight="bold")
ax2.grid(True, alpha=0.2, which="both", zorder=0)

# 3. Near lower boundary - extreme zoom (x < L + 0.1)
ax3 = plt.subplot(4, 3, 3)
zoom_threshold_lower = L + 0.1
mask_zoom_lower = x < zoom_threshold_lower
x_zoom_lower = x[mask_zoom_lower]

if len(x_zoom_lower) > 0:
    bins_zoom_lower = np.linspace(L, zoom_threshold_lower, 201)

    # Reference line BELOW
    ax3.axvline(L, color="darkred", linestyle="--", linewidth=3, zorder=1, alpha=0.8)

    # Histogram ABOVE
    ax3.hist(
        x_zoom_lower,
        bins=bins_zoom_lower,
        color="darkgreen",
        edgecolor="none",
        alpha=0.85,
        zorder=2,
    )

    ax3.set_xlabel("Raw value (x)", fontsize=10)
    ax3.set_ylabel("Count (log scale)", fontsize=10)
    ax3.set_yscale("log")
    ax3.set_title(
        f"Near Lower Boundary (LOG)\nx < {zoom_threshold_lower} ({len(x_zoom_lower):,} samples)",
        fontsize=11,
        fontweight="bold",
    )
    ax3.grid(True, alpha=0.2, which="both", zorder=0)
else:
    ax3.text(0.5, 0.5, "No samples in range", ha="center", va="center", transform=ax3.transAxes)
    ax3.set_title(
        f"Near Lower Boundary\nx < {zoom_threshold_lower}", fontsize=11, fontweight="bold"
    )

# 4. U-space distribution (2000 bins)
ax4 = plt.subplot(4, 3, 4)
bins_u_full = np.linspace(0, 1, 2001)

# Reference lines BELOW
ax4.axvline(0, color="darkred", linestyle="--", linewidth=2.5, label="u=0 (L)", zorder=1, alpha=0.8)
ax4.axvline(1, color="darkred", linestyle="--", linewidth=2.5, label="u=1 (U)", zorder=1, alpha=0.8)

# Histogram ABOVE with high contrast color
ax4.hist(u, bins=bins_u_full, color="rebeccapurple", edgecolor="none", alpha=0.85, zorder=2)

ax4.set_xlabel("Normalized u = (x-L)/(U-L)", fontsize=10)
ax4.set_ylabel("Count", fontsize=10)
ax4.set_title("U-Space Full Distribution (2000 bins)", fontsize=11, fontweight="bold")
ax4.legend(fontsize=8, loc="upper right")
ax4.grid(True, alpha=0.2, zorder=0)

# 5. U-space LOG scale
ax5 = plt.subplot(4, 3, 5)

# Reference lines BELOW
ax5.axvline(0, color="darkred", linestyle="--", linewidth=2.5, zorder=1, alpha=0.8)
ax5.axvline(1, color="darkred", linestyle="--", linewidth=2.5, zorder=1, alpha=0.8)

# Histogram ABOVE
ax5.hist(u, bins=bins_u_full, color="rebeccapurple", edgecolor="none", alpha=0.85, zorder=2)

ax5.set_xlabel("Normalized u = (x-L)/(U-L)", fontsize=10)
ax5.set_ylabel("Count (log scale)", fontsize=10)
ax5.set_yscale("log")
ax5.set_title("U-Space Full Distribution (2000 bins, LOG)", fontsize=11, fontweight="bold")
ax5.grid(True, alpha=0.2, which="both", zorder=0)

# 6. U-space extreme zoom lower (u < 0.02)
ax6 = plt.subplot(4, 3, 6)
u_zoom_extreme_lower = u[u < 0.02]
bins_u_extreme_lower = np.linspace(0, 0.02, 201)

if len(u_zoom_extreme_lower) > 0:
    # Reference lines BELOW
    ax6.axvline(0, color="darkred", linestyle="--", linewidth=3, zorder=1, alpha=0.8)
    ax6.axvline(
        0.001, color="darkorange", linestyle=":", linewidth=2, label="u=0.001", zorder=1, alpha=0.7
    )
    ax6.axvline(0.01, color="gold", linestyle=":", linewidth=2, label="u=0.01", zorder=1, alpha=0.7)

    # Histogram ABOVE
    ax6.hist(
        u_zoom_extreme_lower,
        bins=bins_u_extreme_lower,
        color="firebrick",
        edgecolor="none",
        alpha=0.85,
        zorder=2,
    )

    ax6.set_xlabel("Normalized u", fontsize=10)
    ax6.set_ylabel("Count (log scale)", fontsize=10)
    ax6.set_yscale("log")
    ax6.set_title(
        f"U-Space Near Lower (LOG, u < 0.02)\n{len(u_zoom_extreme_lower):,} samples",
        fontsize=11,
        fontweight="bold",
    )
    ax6.legend(fontsize=8, loc="upper right")
    ax6.grid(True, alpha=0.2, which="both", zorder=0)
else:
    ax6.text(0.5, 0.5, "No samples in range", ha="center", va="center", transform=ax6.transAxes)

# 7. U-space zoom upper (u > 0.98)
ax7 = plt.subplot(4, 3, 7)
u_zoom_upper = u[u > 0.98]
bins_u_zoom_upper = np.linspace(0.98, 1.0, 201)

if len(u_zoom_upper) > 0:
    # Reference lines BELOW
    ax7.axvline(1, color="darkred", linestyle="--", linewidth=3, zorder=1, alpha=0.8)
    ax7.axvline(
        0.999, color="darkorange", linestyle=":", linewidth=2, label="u=0.999", zorder=1, alpha=0.7
    )
    ax7.axvline(0.99, color="gold", linestyle=":", linewidth=2, label="u=0.99", zorder=1, alpha=0.7)

    # Histogram ABOVE
    ax7.hist(
        u_zoom_upper,
        bins=bins_u_zoom_upper,
        color="darkslateblue",
        edgecolor="none",
        alpha=0.85,
        zorder=2,
    )

    ax7.set_xlabel("Normalized u", fontsize=10)
    ax7.set_ylabel("Count (log scale)", fontsize=10)
    ax7.set_yscale("log")
    ax7.set_title(
        f"U-Space Near Upper (LOG, u > 0.98)\n{len(u_zoom_upper):,} samples",
        fontsize=11,
        fontweight="bold",
    )
    ax7.legend(fontsize=8, loc="upper left")
    ax7.grid(True, alpha=0.2, which="both", zorder=0)
else:
    ax7.text(0.5, 0.5, "No samples in range", ha="center", va="center", transform=ax7.transAxes)

# 8. Cumulative distribution - lower boundary zoom (to see concentration patterns)
ax8 = plt.subplot(4, 3, 8)
u_sorted = np.sort(u)
cumulative = np.arange(1, len(u_sorted) + 1) / len(u_sorted)

# Reference lines BELOW
ax8.axvline(
    0.001, color="darkorange", linestyle=":", linewidth=2, label="u=0.001", zorder=1, alpha=0.7
)
ax8.axvline(0.01, color="gold", linestyle=":", linewidth=2, label="u=0.01", zorder=1, alpha=0.7)
ax8.axhline(
    near_L_001 / len(u), color="darkorange", linestyle=":", linewidth=1.5, zorder=1, alpha=0.5
)
ax8.axhline(near_L_01 / len(u), color="gold", linestyle=":", linewidth=1.5, zorder=1, alpha=0.5)

# CDF ABOVE
ax8.plot(u_sorted, cumulative, color="darkgreen", linewidth=2.5, zorder=2)

ax8.set_xlabel("Normalized u", fontsize=10)
ax8.set_ylabel("Cumulative Fraction", fontsize=10)
ax8.set_title("CDF - Lower Boundary Zoom", fontsize=11, fontweight="bold")
ax8.legend(fontsize=8, loc="lower right")
ax8.grid(True, alpha=0.2, zorder=0)
ax8.set_xlim(-0.01, 0.2)  # Extended below 0 to show out-of-bounds jumps

# 9. Cumulative distribution - upper boundary zoom
ax9 = plt.subplot(4, 3, 9)

# Reference lines BELOW
ax9.axvline(
    0.999, color="darkorange", linestyle=":", linewidth=2, label="u=0.999", zorder=1, alpha=0.7
)
ax9.axvline(0.99, color="gold", linestyle=":", linewidth=2, label="u=0.99", zorder=1, alpha=0.7)
ax9.axhline(
    near_U_999 / len(u), color="darkorange", linestyle=":", linewidth=1.5, zorder=1, alpha=0.5
)
ax9.axhline(near_U_99 / len(u), color="gold", linestyle=":", linewidth=1.5, zorder=1, alpha=0.5)

# CDF ABOVE
ax9.plot(u_sorted, cumulative, color="darkblue", linewidth=2.5, zorder=2)

ax9.set_xlabel("Normalized u", fontsize=10)
ax9.set_ylabel("Cumulative Fraction", fontsize=10)
ax9.set_title("CDF - Upper Boundary Zoom", fontsize=11, fontweight="bold")
ax9.legend(fontsize=8, loc="lower right")
ax9.grid(True, alpha=0.2, zorder=0)
ax9.set_xlim(0.8, 1.01)  # Extended above 1 to show out-of-bounds jumps

# 10. Cumulative distribution - full range
ax10 = plt.subplot(4, 3, 10)

# Reference lines BELOW
ax10.axvline(
    0.001, color="darkorange", linestyle=":", linewidth=1.5, label="u=0.001", zorder=1, alpha=0.5
)
ax10.axvline(0.01, color="gold", linestyle=":", linewidth=1.5, label="u=0.01", zorder=1, alpha=0.5)
ax10.axvline(0.99, color="gold", linestyle=":", linewidth=1.5, label="u=0.99", zorder=1, alpha=0.5)
ax10.axvline(
    0.999, color="darkorange", linestyle=":", linewidth=1.5, label="u=0.999", zorder=1, alpha=0.5
)

# Horizontal lines for concentrations
ax10.axhline(
    near_L_01 / len(u),
    color="red",
    linestyle="--",
    linewidth=1,
    zorder=1,
    alpha=0.3,
    label=f"Lower: {100 * near_L_01 / len(u):.2f}%",
)
ax10.axhline(
    1 - near_U_99 / len(u),
    color="blue",
    linestyle="--",
    linewidth=1,
    zorder=1,
    alpha=0.3,
    label=f"Upper: {100 * near_U_99 / len(u):.2f}%",
)

# CDF ABOVE
ax10.plot(u_sorted, cumulative, color="darkgreen", linewidth=2.5, zorder=2)

ax10.set_xlabel("Normalized u", fontsize=10)
ax10.set_ylabel("Cumulative Fraction", fontsize=10)
ax10.set_title("CDF - Full Range (extended)", fontsize=11, fontweight="bold")
ax10.legend(fontsize=7, loc="center right")
ax10.grid(True, alpha=0.2, zorder=0)
ax10.set_xlim(-0.01, 1.01)  # Extended to show out-of-bounds jumps if present

# 11 & 12. Summary statistics text (split into two columns)
ax11 = plt.subplot(4, 3, 11)
ax11.axis("off")

summary_text_left = f"""A_He (ALPHA PARTICLE ABUNDANCE)

Total: {len(x):,} samples
Bounds: L={L}, U={U}, x0={x0}

RAW DATA STATISTICS:
  Range: [{x.min():.6f}, {x.max():.6f}]
  Mean: {x.mean():.4f}
  Median: {np.median(x):.4f}
  Std: {x.std():.4f}

BOUNDARY EXACT VALUES:
  At L={L}: {at_L:,} samples
  At U={U}: {at_U:,} samples

OUT-OF-BOUNDS:
  Below L (u<0): 0
  Above U (u>1): 0
"""

summary_text_right = f"""LOWER BOUNDARY (u < threshold):
  u < 0.001: {near_L_001:,} ({100 * near_L_001 / len(x):.3f}%)
  u < 0.010: {near_L_01:,} ({100 * near_L_01 / len(x):.3f}%)

UPPER BOUNDARY (u > threshold):
  u > 0.999: {near_U_999:,} ({100 * near_U_999 / len(x):.3f}%)
  u > 0.990: {near_U_99:,} ({100 * near_U_99 / len(x):.3f}%)

METADATA EXPECTATIONS:
  expected_lower_stickiness:
    {meta.get("expected_lower_stickiness")}
  expected_upper_stickiness:
    {meta.get("expected_upper_stickiness")}

VISUALIZATION:
  ✓ Reference lines BELOW histograms
  ✓ Log scale on zoomed panels
  ✓ Z-order: grid(0) < lines(1) < data(2)
"""

ax11.text(
    0.05,
    0.5,
    summary_text_left,
    fontsize=8.5,
    family="monospace",
    verticalalignment="center",
    bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8, edgecolor="gray"),
)

ax12 = plt.subplot(4, 3, 12)
ax12.axis("off")

ax12.text(
    0.05,
    0.5,
    summary_text_right,
    fontsize=8.5,
    family="monospace",
    verticalalignment="center",
    bbox=dict(boxstyle="round", facecolor="lightcyan", alpha=0.8, edgecolor="gray"),
)

plt.suptitle(
    "A_He Ultra-High-Resolution Analysis (12 panels: histograms + CDFs)",
    fontsize=14,
    fontweight="bold",
    y=0.997,
)
plt.tight_layout(rect=[0, 0, 1, 0.995])

# Save
output_path = Path("figures/A_He/A_He_improved_analysis.png")
output_path.parent.mkdir(exist_ok=True, parents=True)
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\nSaved: {output_path}")

output_path_hires = Path("figures/A_He/A_He_improved_analysis_hires.png")
plt.savefig(output_path_hires, dpi=300, bbox_inches="tight")
print(f"Saved: {output_path_hires}")

plt.close()

print("\n✓ Improved visualization complete with proper z-ordering")
print("\nKey improvements:")
print("  - Reference lines (axvline) drawn with zorder=1 (BELOW histograms)")
print("  - Histograms drawn with zorder=2 (ABOVE reference lines)")
print("  - Grid drawn with zorder=0 (BEHIND everything)")
print("  - Higher contrast colors (darkred, firebrick, rebeccapurple)")
print("  - Increased alpha=0.85 for more opaque histograms")
print("  - Thicker reference lines (linewidth=2.5-3) for visibility")
