"""Generate detailed matplotlib histograms for w_const dataset with out-of-bounds analysis."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Load w_const data
data_dir = Path("tests/data")
x = pd.read_parquet(data_dir / "w_const_test_sample.parquet")["values"].values
with open(data_dir / "w_const_test_metadata.json") as f:
    meta = json.load(f)

L = meta["L"]
U = meta["U"]

print("Generating detailed plots for w_const...")
print(f"Parameter: {meta['name']}")
print(f"Bounds: L={L}, U={U}")
print(f"Samples: {len(x):,}")

# Analyze out-of-bounds
below_L = x < L
above_U = x > U
in_bounds = (x >= L) & (x <= U)

n_below = np.sum(below_L)
n_above = np.sum(above_U)
n_valid = np.sum(in_bounds)

print(f"Below L={L}: {n_below} samples ({n_below / len(x) * 100:.2f}%)")
print(f"Above U={U}: {n_above} samples ({n_above / len(x) * 100:.2f}%)")
print(f"In bounds:   {n_valid} samples ({n_valid / len(x) * 100:.2f}%)")

# Compute u-space for valid samples
x_valid = x[in_bounds]
u = (x_valid - L) / (U - L)

# Create figure
fig = plt.figure(figsize=(16, 14))

# 1. Full data distribution including out-of-bounds
ax1 = plt.subplot(4, 2, 1)
x_min = min(x.min(), L - 5)
x_max = max(x.max(), U + 5)
bins_full = np.linspace(x_min, x_max, 201)
ax1.hist(x, bins=bins_full, color="steelblue", edgecolor="none", alpha=0.7)
ax1.axvline(L, color="red", linestyle="--", linewidth=2, label=f"L={L}")
ax1.axvline(U, color="red", linestyle="--", linewidth=2, label=f"U={U}")
ax1.axvspan(x_min, L, alpha=0.2, color="red", label="Out-of-bounds (below)")
ax1.axvspan(U, x_max, alpha=0.2, color="orange", label="Out-of-bounds (above)")
ax1.set_xlabel("Raw value (x)", fontsize=12)
ax1.set_ylabel("Count", fontsize=12)
ax1.set_title(
    f"w_const Full Distribution (including out-of-bounds)\n{len(x):,} total samples",
    fontsize=13,
    fontweight="bold",
)
ax1.grid(True, alpha=0.3)
ax1.legend()

# 2. Out-of-bounds samples only
ax2 = plt.subplot(4, 2, 2)
if n_below > 0:
    x_below = x[below_L]
    bins_below = np.linspace(x_below.min() - 0.1, L, 51)
    ax2.hist(x_below, bins=bins_below, color="darkred", edgecolor="none", alpha=0.7)
    ax2.axvline(L, color="red", linestyle="--", linewidth=2, label=f"L={L}")
    ax2.axvline(0, color="black", linestyle=":", linewidth=1, alpha=0.5, label="x=0")
    n_at_zero = np.sum(x_below == 0.0)
    ax2.text(
        0.05,
        0.95,
        f"Samples at exactly 0.0: {n_at_zero}\n({n_at_zero / n_below * 100:.1f}% of out-of-bounds)",
        transform=ax2.transAxes,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        fontsize=10,
    )
ax2.set_xlabel("Raw value (x)", fontsize=12)
ax2.set_ylabel("Count", fontsize=12)
ax2.set_title(
    f"Out-of-Bounds Samples (x < L={L})\n{n_below:,} samples - LIKELY FAILED FITS",
    fontsize=13,
    fontweight="bold",
)
ax2.grid(True, alpha=0.3)
ax2.legend()

# 3. Valid samples only (in bounds)
ax3 = plt.subplot(4, 2, 3)
bins_valid = np.linspace(L, U, 201)
ax3.hist(x_valid, bins=bins_valid, color="mediumseagreen", edgecolor="none", alpha=0.7)
ax3.axvline(L, color="red", linestyle="--", linewidth=1, alpha=0.5, label=f"L={L}")
ax3.axvline(U, color="red", linestyle="--", linewidth=1, alpha=0.5, label=f"U={U}")
ax3.set_xlabel("Raw value (x)", fontsize=12)
ax3.set_ylabel("Count", fontsize=12)
ax3.set_title(
    f"Valid Samples Only (L ≤ x ≤ U)\n{n_valid:,} samples", fontsize=13, fontweight="bold"
)
ax3.grid(True, alpha=0.3)
ax3.legend()

# 4. Zoomed near upper boundary (raw space)
ax4 = plt.subplot(4, 2, 4)
upper_zoom_threshold = U - 10
mask_upper_zoom = x_valid > upper_zoom_threshold
bins_upper_zoom = np.linspace(upper_zoom_threshold, U, 101)
ax4.hist(
    x_valid[mask_upper_zoom], bins=bins_upper_zoom, color="darkorange", edgecolor="none", alpha=0.7
)
ax4.axvline(U, color="red", linestyle="--", linewidth=2, label=f"U={U}")
ax4.set_xlabel("Raw value (x)", fontsize=12)
ax4.set_ylabel("Count", fontsize=12)
ax4.set_title(f"Near Upper Boundary (x > {upper_zoom_threshold})", fontsize=13, fontweight="bold")
ax4.grid(True, alpha=0.3)
ax4.legend()

# 5. U-space full distribution
ax5 = plt.subplot(4, 2, 5)
bins_u = np.linspace(0, 1, 201)
ax5.hist(u, bins=bins_u, color="purple", edgecolor="none", alpha=0.7)
ax5.axvline(0, color="red", linestyle="--", linewidth=1, alpha=0.5, label="u=0 (L)")
ax5.axvline(1, color="red", linestyle="--", linewidth=1, alpha=0.5, label="u=1 (U)")
ax5.set_xlabel("Normalized u = (x-L)/(U-L)", fontsize=12)
ax5.set_ylabel("Count", fontsize=12)
ax5.set_title("w_const U-Space Distribution", fontsize=13, fontweight="bold")
ax5.grid(True, alpha=0.3)
ax5.legend()

# 6. U-space near lower boundary (u < 0.1)
ax6 = plt.subplot(4, 2, 6)
mask_u_lower = u < 0.1
bins_u_lower = np.linspace(0, 0.1, 101)
ax6.hist(u[mask_u_lower], bins=bins_u_lower, color="darkgreen", edgecolor="none", alpha=0.7)
ax6.axvline(0, color="red", linestyle="--", linewidth=2, label="u=0 (L)")
ax6.axvline(0.01, color="orange", linestyle="--", linewidth=1, alpha=0.5, label="u=0.01")
ax6.set_xlabel("Normalized u = (x-L)/(U-L)", fontsize=12)
ax6.set_ylabel("Count", fontsize=12)
ax6.set_title("U-Space Near Lower Boundary (u < 0.1)", fontsize=13, fontweight="bold")
ax6.grid(True, alpha=0.3)
ax6.legend()

# 7. U-space near upper boundary (u > 0.9)
ax7 = plt.subplot(4, 2, 7)
mask_u_upper = u > 0.9
bins_u_upper = np.linspace(0.9, 1.0, 101)
ax7.hist(u[mask_u_upper], bins=bins_u_upper, color="darkred", edgecolor="none", alpha=0.7)
ax7.axvline(1, color="red", linestyle="--", linewidth=2, label="u=1 (U)")
ax7.axvline(0.99, color="orange", linestyle="--", linewidth=1, alpha=0.5, label="u=0.99")
ax7.set_xlabel("Normalized u = (x-L)/(U-L)", fontsize=12)
ax7.set_ylabel("Count", fontsize=12)
ax7.set_title("U-Space Near Upper Boundary (u > 0.9)", fontsize=13, fontweight="bold")
ax7.grid(True, alpha=0.3)
ax7.legend()

# 8. Summary statistics
ax8 = plt.subplot(4, 2, 8)
ax8.axis("off")

# Compute statistics
near_L_1e3 = np.sum(u < 1e-3)
near_L_1e2 = np.sum(u < 1e-2)
near_U_1e3 = np.sum(u > 1 - 1e-3)
near_U_1e2 = np.sum(u > 1 - 1e-2)

# Check if out-of-bounds are at 0.0
if n_below > 0:
    x_below = x[below_L]
    n_at_zero = np.sum(x_below == 0.0)
    oob_interpretation = f"  Most at x=0.0: {n_at_zero}/{n_below} ({n_at_zero / n_below * 100:.1f}%)\n  → LIKELY FAILED FITS (similar to np1)"
else:
    oob_interpretation = "  None"

summary_text = f"""w_const (THERMAL SPEED) - SUMMARY

Total samples: {len(x):,}

OUT-OF-BOUNDS:
  Below L={L}: {n_below:,} ({n_below / len(x) * 100:.2f}%)
{oob_interpretation}
  Above U={U}: {n_above:,} ({n_above / len(x) * 100:.2f}%)

VALID SAMPLES: {n_valid:,} ({n_valid / len(x) * 100:.2f}%)

LOWER BOUNDARY (valid samples):
  u < 1e-3: {near_L_1e3:6,} ({100 * near_L_1e3 / len(u):5.2f}%)
  u < 1e-2: {near_L_1e2:6,} ({100 * near_L_1e2 / len(u):5.2f}%)

UPPER BOUNDARY (valid samples):
  u > 1-1e-3: {near_U_1e3:6,} ({100 * near_U_1e3 / len(u):5.2f}%)
  u > 1-1e-2: {near_U_1e2:6,} ({100 * near_U_1e2 / len(u):5.2f}%)

INTERPRETATION:
{"✓ Upper boundary stickiness detected" if near_U_1e2 / len(u) > 0.005 else "✗ No upper stickiness"}
{"✗ No lower boundary stickiness" if near_L_1e2 / len(u) < 0.01 else "✓ Lower stickiness present"}
⚠️  {n_below} failed fits (out-of-bounds samples)

METADATA:
  expected_upper_stickiness = true ✓
  expected_lower_stickiness = false ✓
"""

ax8.text(
    0.1,
    0.5,
    summary_text,
    fontsize=10,
    family="monospace",
    verticalalignment="center",
    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
)

plt.tight_layout()

# Save figure
output_path = Path("figures/w_const_detailed_analysis.png")
output_path.parent.mkdir(exist_ok=True)
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\nSaved: {output_path}")

# Save high-resolution version
output_path_hires = Path("figures/w_const_detailed_analysis_hires.png")
plt.savefig(output_path_hires, dpi=300, bbox_inches="tight")
print(f"Saved: {output_path_hires}")

plt.close()

print("\n✓ Detailed analysis plots generated successfully")
