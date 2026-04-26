"""np2 combined filter comparison with log-scaled x-axis.

np2 has a heavily right-skewed distribution (L=0.01, U=100). Linear binning
compresses the low-value structure where the boundary pileup lives. This script
uses logarithmic bins to spread out the lower end for visual inspection.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyarrow.parquet as pq

from fitqc import BoundaryConfig, run_boundary_qc, run_interior_qc
from fitqc.boundary import compute_u

# Load data
table = pq.read_table("tests/data/np2_test_sample.parquet")
x = table.column("values").to_numpy()
with open("tests/data/np2_test_metadata.json") as f:
    meta = json.load(f)

L, U = meta["L"], meta["U"]
x0 = meta.get("x0")
print(f"np2: L={L}, U={U}, x0={x0}, n={len(x)}")

# Run detection
config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True, grid_mode="progressive")
boundary = run_boundary_qc(x, L, U, config)
interior = run_interior_qc(x, x0, L, U) if x0 is not None else None

print(f"  lower: detected={boundary.lower_pileup_detected}, t_lo*={boundary.t_lo_star}")
print(f"  upper: detected={boundary.upper_pileup_detected}, t_hi*={boundary.t_hi_star}")

# Build masks
u = compute_u(x, L, U)
valid = np.isfinite(x)
boundary_mask = valid & (u >= 0) & (u <= 1)
if boundary.lower_pileup_detected and boundary.t_lo_star is not None:
    boundary_mask &= u > boundary.t_lo_star
if boundary.upper_pileup_detected and boundary.t_hi_star is not None:
    boundary_mask &= u < (1 - boundary.t_hi_star)

interior_mask = np.ones(len(x), dtype=bool)
if interior is not None and interior.spike_detected and interior.eps_star is not None:
    z = np.abs(x - x0) / (U - L)
    interior_mask = z > interior.eps_star

combined_mask = boundary_mask & interior_mask

x_orig = x[valid]
x_filtered = x[combined_mask]

# Log-spaced bins from L to U
n_bins = 200
bin_edges = np.geomspace(max(L, 1e-3), U, n_bins + 1)

fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=150)

# Top-left: Original (log-x, linear-y)
axes[0, 0].hist(
    x_orig,
    bins=bin_edges,
    histtype="stepfilled",
    alpha=0.7,
    color="steelblue",
    edgecolor="black",
    linewidth=0.3,
)
axes[0, 0].set_xscale("log")
axes[0, 0].axvline(L, color="red", ls="--", lw=1, alpha=0.5)
axes[0, 0].axvline(U, color="red", ls="--", lw=1, alpha=0.5)
if x0 is not None:
    axes[0, 0].axvline(x0, color="orange", ls="--", lw=1.5, alpha=0.7)
axes[0, 0].set_title(f"Original (n={len(x_orig):,})")
axes[0, 0].set_ylabel("Count")
axes[0, 0].grid(True, alpha=0.3)

# Top-right: Combined overlay (log-x, linear-y)
axes[0, 1].hist(
    x_orig,
    bins=bin_edges,
    histtype="stepfilled",
    alpha=0.5,
    color="#888888",
    edgecolor="none",
    label="Original",
)
axes[0, 1].hist(
    x_filtered,
    bins=bin_edges,
    histtype="stepfilled",
    alpha=0.85,
    color="#d62728",
    edgecolor="black",
    linewidth=0.3,
    label="Filtered",
)
axes[0, 1].set_xscale("log")
axes[0, 1].axvline(L, color="green", ls="--", lw=1, alpha=0.5)
axes[0, 1].axvline(U, color="green", ls="--", lw=1, alpha=0.5)
axes[0, 1].legend(fontsize=9)
removed = len(x_orig) - len(x_filtered)
axes[0, 1].set_title(f"Combined Filter (removed={removed:,} [{removed / len(x_orig):.2%}])")
axes[0, 1].set_ylabel("Count")
axes[0, 1].grid(True, alpha=0.3)

# Bottom-left: Original (log-x, log-y)
axes[1, 0].hist(
    x_orig,
    bins=bin_edges,
    histtype="stepfilled",
    alpha=0.7,
    color="steelblue",
    edgecolor="black",
    linewidth=0.3,
)
axes[1, 0].set_xscale("log")
axes[1, 0].set_yscale("log")
axes[1, 0].axvline(L, color="red", ls="--", lw=1, alpha=0.5)
axes[1, 0].axvline(U, color="red", ls="--", lw=1, alpha=0.5)
if x0 is not None:
    axes[1, 0].axvline(x0, color="orange", ls="--", lw=1.5, alpha=0.7)
axes[1, 0].set_title("Original — log-log")
axes[1, 0].set_xlabel("Parameter value")
axes[1, 0].set_ylabel("Count (log)")
axes[1, 0].grid(True, alpha=0.3)

# Bottom-right: Combined overlay (log-x, log-y)
axes[1, 1].hist(
    x_orig,
    bins=bin_edges,
    histtype="stepfilled",
    alpha=0.5,
    color="#888888",
    edgecolor="none",
    label="Original",
)
axes[1, 1].hist(
    x_filtered,
    bins=bin_edges,
    histtype="stepfilled",
    alpha=0.85,
    color="#d62728",
    edgecolor="black",
    linewidth=0.3,
    label="Filtered",
)
axes[1, 1].set_xscale("log")
axes[1, 1].set_yscale("log")
axes[1, 1].axvline(L, color="green", ls="--", lw=1, alpha=0.5)
axes[1, 1].axvline(U, color="green", ls="--", lw=1, alpha=0.5)
axes[1, 1].legend(fontsize=9)
axes[1, 1].set_title("Combined Filter — log-log")
axes[1, 1].set_xlabel("Parameter value")
axes[1, 1].set_ylabel("Count (log)")
axes[1, 1].grid(True, alpha=0.3)

fig.suptitle("np2 — Log-X Binned Filter Comparison", fontsize=14, fontweight="bold")
fig.tight_layout()

out = Path("figures/np2")
out.mkdir(parents=True, exist_ok=True)
fig.savefig(out / "np2_logx_filter_comparison_hires.png", dpi=300, bbox_inches="tight")
print(f"Saved: {out / 'np2_logx_filter_comparison_hires.png'}")
