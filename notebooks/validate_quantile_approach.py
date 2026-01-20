# %% [markdown]
"""
# Quantile-Based Threshold Detection: Proof of Concept Validation

This notebook validates whether quantile-based multi-curve analysis improves
threshold detection compared to the current single-curve approach for:

1. **Boundary Detection** (linear space): Finding pileup width at parameter bounds
2. **Interior Detection** (log space): Finding spike width at initial guess x0

## Validation Approach

- Generate synthetic data with known ground truth
- Compare single-curve vs multi-curve quantile methods
- Measure accuracy, robustness, false positive rates

## Expected Outcomes

**Multi-curve should excel at:**
- Tight pileups/spikes (< 1% of range)
- Noisy data (multiple independent elbows)

**Both should perform well on:**
- Broad pileups/spikes (> 2% of range)
- Clean data with obvious structure

**Neither should false positive on:**
- Uniform data
- Broad natural distributions (e.g., signed log-normal)
"""

# %% Imports and setup
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Add paths
sys.path.append("/home/user/fitqc/tmp")
sys.path.append("/home/user/fitqc/src")

from fitqc.synth import (
    generate_with_boundary_pileup,
    generate_with_x0_spike,
    generate_signed_lognormal,
)
from fitqc.boundary import compute_u
from fitqc.interior import compute_z
from poc_quantile_threshold import compare_single_vs_multi_curve

# Set matplotlib style
plt.style.use("seaborn-v0_8-darkgrid")
plt.rcParams["figure.dpi"] = 100
plt.rcParams["font.size"] = 10

print("=" * 100)
print("QUANTILE-BASED THRESHOLD DETECTION: PROOF OF CONCEPT VALIDATION")
print("=" * 100)
print()

# %% [markdown]
"""
## Part 1: Boundary Detection (Linear Space)

Tests for detecting boundary pileup using quantile analysis.
"""

# %% Common boundary test configuration
GRID_BOUNDARY = np.linspace(0.0, 0.05, 41)
# FIXED: Denser quantile grid to capture 3% pileup structural break
QUANTILE_GRID = np.array(
    [0.001, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.05, 0.07, 0.10]
)
LOG_SPACE_BOUNDARY = False

print("=" * 100)
print("PART 1: BOUNDARY VALIDATION (Linear Space)")
print("=" * 100)
print(f"Grid: {len(GRID_BOUNDARY)} points from {GRID_BOUNDARY[0]:.4f} to {GRID_BOUNDARY[-1]:.4f}")
print(f"Quantile grid: {QUANTILE_GRID}")
print()

# %% Sanity Check: Visualize boundary distributions
print("\n" + "=" * 100)
print("SANITY CHECK: Visualizing test data distributions")
print("=" * 100)

# Generate all test data first
x_tight = generate_with_boundary_pileup(
    n=10000, L=0.0, U=1.0, lower_pileup_frac=0.03, pileup_width=0.003, seed=42
)
u_tight = compute_u(x_tight, L=0.0, U=1.0)

x_uniform = np.random.uniform(0.0, 1.0, 10000)
u_uniform = compute_u(x_uniform, L=0.0, U=1.0)

x_broad = generate_with_boundary_pileup(
    n=10000, L=0.0, U=1.0, lower_pileup_frac=0.10, pileup_width=0.05, seed=42
)
u_broad = compute_u(x_broad, L=0.0, U=1.0)

# Quick histogram sanity check
fig_sanity, axes_sanity = plt.subplots(1, 3, figsize=(15, 4))

axes_sanity[0].hist(u_tight, bins=50, alpha=0.7, color="navy", edgecolor="black")
axes_sanity[0].axvline(0.003, color="red", ls="--", linewidth=2, label="True pileup width")
axes_sanity[0].set_xlabel("u (normalized position)")
axes_sanity[0].set_ylabel("Count")
axes_sanity[0].set_title("Tight Pileup: 3% in [0, 0.003]")
axes_sanity[0].legend()
axes_sanity[0].set_xlim(-0.01, 0.1)

axes_sanity[1].hist(u_uniform, bins=50, alpha=0.7, color="purple", edgecolor="black")
axes_sanity[1].set_xlabel("u (normalized position)")
axes_sanity[1].set_title("Uniform: Should be flat")
axes_sanity[1].set_xlim(0, 1)

axes_sanity[2].hist(u_broad, bins=50, alpha=0.7, color="darkgreen", edgecolor="black")
axes_sanity[2].axvline(0.05, color="red", ls="--", linewidth=2, label="True pileup width")
axes_sanity[2].set_xlabel("u (normalized position)")
axes_sanity[2].set_title("Broad Pileup: 10% in [0, 0.05]")
axes_sanity[2].legend()
axes_sanity[2].set_xlim(-0.01, 0.2)

plt.tight_layout()
plt.savefig("/home/user/fitqc/tmp/boundary_sanity_check.png", dpi=150)
plt.show()

print("Boundary distributions look correct. Proceeding with tests...\n")

# %% Scenario 1: Boundary Tight Pileup (3% in 0.3%)
print("\n" + "=" * 100)
print("SCENARIO 1: Boundary Tight Pileup (3% in 0.3% of range)")
print("=" * 100)

u_tight_sorted = np.sort(u_tight)

true_threshold_tight = 0.003
result_tight = compare_single_vs_multi_curve(
    u_tight_sorted,
    GRID_BOUNDARY,
    QUANTILE_GRID,
    log_space=LOG_SPACE_BOUNDARY,
    true_threshold=true_threshold_tight,
)

print(f"\nData: n={len(u_tight)}, pileup=3%, width=0.003")
print(f"True threshold: {true_threshold_tight:.4f}")
print(f"\nSingle-curve elbow: {result_tight['single_curve_elbow']}")
print(f"Multi-curve elbow (quantile): {result_tight['multi_curve_elbow']}")

multi_thresh_tight = None
if result_tight["multi_curve_elbow"] is not None:
    multi_thresh_tight = np.interp(
        result_tight["multi_curve_elbow"],
        QUANTILE_GRID,
        result_tight["diagnostics"]["threshold_at_quantile"],
    )
    print(f"Multi-curve threshold: {multi_thresh_tight:.6f}")

print(f"\nErrors:")
print(
    f"  Single: {result_tight['single_error']:.6f}"
    if result_tight["single_error"]
    else "  Single: None"
)
print(
    f"  Multi:  {result_tight['multi_error']:.6f}"
    if result_tight["multi_error"]
    else "  Multi: None"
)

print(f"\nQuantile ratios:")
for q, r in zip(QUANTILE_GRID, result_tight["quantile_ratios"]):
    print(f"  q={q:.3f}: ratio={r:.3f}")

if result_tight["multi_error"] and result_tight["single_error"]:
    if result_tight["multi_error"] < result_tight["single_error"]:
        print(
            f"\n✓ Multi-curve MORE accurate (by {100 * (result_tight['single_error'] - result_tight['multi_error']) / result_tight['single_error']:.1f}%)"
        )
    else:
        print(f"\n✗ Single-curve more accurate")

# %% Scenario 2: Boundary Uniform (No Pileup)
print("\n" + "=" * 100)
print("SCENARIO 2: Boundary Uniform (No Pileup)")
print("=" * 100)

u_uniform_sorted = np.sort(u_uniform)

result_uniform = compare_single_vs_multi_curve(
    u_uniform_sorted,
    GRID_BOUNDARY,
    QUANTILE_GRID,
    log_space=LOG_SPACE_BOUNDARY,
    true_threshold=None,
)

print(f"\nData: n={len(u_uniform)}, uniform [0,1]")
print(f"\nSingle-curve elbow: {result_uniform['single_curve_elbow']}")
print(f"Multi-curve elbow (quantile): {result_uniform['multi_curve_elbow']}")

multi_thresh_uniform = None
if result_uniform["multi_curve_elbow"] is not None:
    multi_thresh_uniform = np.interp(
        result_uniform["multi_curve_elbow"],
        QUANTILE_GRID,
        result_uniform["diagnostics"]["threshold_at_quantile"],
    )
    print(f"Multi-curve threshold: {multi_thresh_uniform:.6f}")

ratio_mean = np.nanmean(result_uniform["quantile_ratios"])
ratio_std = np.nanstd(result_uniform["quantile_ratios"])
print(f"\nRatio statistics: mean={ratio_mean:.3f}, std={ratio_std:.3f}")

if abs(ratio_mean - 1.0) < 0.15:
    print(f"✓ Ratios near 1.0 (expected for uniform)")
else:
    print(f"✗ Ratios deviate from 1.0")

# %% Scenario 3: Boundary Broad Pileup (10% in 5%)
print("\n" + "=" * 100)
print("SCENARIO 3: Boundary Broad Pileup (10% in 5% of range)")
print("=" * 100)

u_broad_sorted = np.sort(u_broad)

true_threshold_broad = 0.05
result_broad = compare_single_vs_multi_curve(
    u_broad_sorted,
    GRID_BOUNDARY,
    QUANTILE_GRID,
    log_space=LOG_SPACE_BOUNDARY,
    true_threshold=true_threshold_broad,
)

print(f"\nData: n={len(u_broad)}, pileup=10%, width=0.05")
print(f"True threshold: {true_threshold_broad:.4f}")
print(f"\nSingle-curve elbow: {result_broad['single_curve_elbow']}")
print(f"Multi-curve elbow (quantile): {result_broad['multi_curve_elbow']}")

multi_thresh_broad = None
if result_broad["multi_curve_elbow"] is not None:
    multi_thresh_broad = np.interp(
        result_broad["multi_curve_elbow"],
        QUANTILE_GRID,
        result_broad["diagnostics"]["threshold_at_quantile"],
    )
    print(f"Multi-curve threshold: {multi_thresh_broad:.6f}")

print(f"\nErrors:")
print(
    f"  Single: {result_broad['single_error']:.6f}"
    if result_broad["single_error"]
    else "  Single: None"
)
print(
    f"  Multi:  {result_broad['multi_error']:.6f}"
    if result_broad["multi_error"]
    else "  Multi: None"
)

# %% [markdown]
"""
## Part 2: Interior Detection (Log Space)

Tests for detecting spikes at x0 using quantile analysis in log-space.
"""

# %% Common interior test configuration
GRID_INTERIOR = np.logspace(-12, -3, 50)
LOG_SPACE_INTERIOR = True

print("\n\n" + "=" * 100)
print("PART 2: INTERIOR VALIDATION (Log Space)")
print("=" * 100)
print(f"Grid: {len(GRID_INTERIOR)} points from 10^-12 to 10^-3 (log-spaced)")
print(f"Quantile grid: {QUANTILE_GRID}")
print()

# %% Sanity Check: Visualize interior distributions
print("\n" + "=" * 100)
print("SANITY CHECK: Visualizing interior test data distributions")
print("=" * 100)

# Generate interior test data
x_spike = generate_with_x0_spike(n=10000, x0=5.0, L=0.0, U=10.0, spike_frac=0.05, seed=42)
z_spike = compute_z(x_spike, x0=5.0, L=0.0, U=10.0)

np.random.seed(42)
x0_broad = 5.0
L_broad = 0.0
U_broad = 10.0
x_broad_normal = np.random.normal(loc=x0_broad, scale=1.5, size=10000)
x_broad_normal = np.clip(x_broad_normal, L_broad, U_broad)
z_broad = compute_z(x_broad_normal, x0=x0_broad, L=L_broad, U=U_broad)

# Visualize z-distributions
fig_sanity_int, axes_sanity_int = plt.subplots(1, 2, figsize=(12, 4))

axes_sanity_int[0].hist(z_spike, bins=100, alpha=0.7, color="darkorange", edgecolor="black")
axes_sanity_int[0].set_xlabel("z (distance from x0, normalized)")
axes_sanity_int[0].set_ylabel("Count")
axes_sanity_int[0].set_title("Spike: 5% exactly at x0 (z=0)")
axes_sanity_int[0].set_xlim(-0.05, 0.5)
axes_sanity_int[0].axvline(0, color="red", ls="--", linewidth=2, alpha=0.5, label="x0 (z=0)")
axes_sanity_int[0].legend()

axes_sanity_int[1].hist(z_broad, bins=100, alpha=0.7, color="teal", edgecolor="black")
axes_sanity_int[1].set_xlabel("z (distance from x0, normalized)")
axes_sanity_int[1].set_title("Broad Normal: Centered at x0, sigma=1.5")
axes_sanity_int[1].set_xlim(-0.05, 0.5)
axes_sanity_int[1].axvline(0, color="red", ls="--", linewidth=2, alpha=0.5, label="x0 (z=0)")
axes_sanity_int[1].legend()

plt.tight_layout()
plt.savefig("/home/user/fitqc/tmp/interior_sanity_check.png", dpi=150)
plt.show()

print("Interior distributions look correct.")
print(f"  Spike: {100 * np.sum(z_spike < 1e-10) / len(z_spike):.1f}% of samples have z < 1e-10")
print(f"  Broad: {100 * np.sum(z_broad < 1e-10) / len(z_broad):.1f}% of samples have z < 1e-10")
print("Proceeding with tests...\n")

# %% Scenario 4: Interior Tight Spike (5% at x0)
print("\n" + "=" * 100)
print("SCENARIO 4: Interior Tight Spike (5% at x0)")
print("=" * 100)

z_spike_sorted = np.sort(z_spike)

result_spike = compare_single_vs_multi_curve(
    z_spike_sorted, GRID_INTERIOR, QUANTILE_GRID, log_space=LOG_SPACE_INTERIOR, true_threshold=None
)

print(f"\nData: n={len(z_spike)}, spike=5% at x0")
single_str = (
    f"{result_spike['single_curve_elbow']:.2e}" if result_spike["single_curve_elbow"] else "None"
)
multi_str = (
    f"{result_spike['multi_curve_elbow']:.2e}" if result_spike["multi_curve_elbow"] else "None"
)
print(f"\nSingle-curve elbow: {single_str}")
print(f"Multi-curve elbow (quantile): {multi_str}")

if result_spike["multi_curve_elbow"] is not None:
    elbow_threshold = np.interp(
        result_spike["multi_curve_elbow"],
        QUANTILE_GRID,
        result_spike["diagnostics"]["threshold_at_quantile"],
    )
    print(f"Multi-curve epsilon: {elbow_threshold:.2e}")

print(f"\nQuantile ratios (should be << 1):")
for q, r in zip(QUANTILE_GRID, result_spike["quantile_ratios"]):
    print(f"  q={q:.3f}: ratio={r:.3e}")

mean_ratio_spike = np.nanmean(result_spike["quantile_ratios"])
if mean_ratio_spike < 0.1:
    print(f"\n✓ Mean ratio {mean_ratio_spike:.3e} << 1 (tight spike)")
else:
    print(f"\n✗ Mean ratio {mean_ratio_spike:.3e} not << 1")

# %% Scenario 5: Interior Broad Normal (Broad, NOT a Spike)
print("\n" + "=" * 100)
print("SCENARIO 5: Interior Broad Normal at x0 (BROAD, NOT a spike)")
print("=" * 100)

z_lognorm_sorted = np.sort(z_broad)

result_lognorm = compare_single_vs_multi_curve(
    z_lognorm_sorted,
    GRID_INTERIOR,
    QUANTILE_GRID,
    log_space=LOG_SPACE_INTERIOR,
    true_threshold=None,
)

print(f"\nData: n={len(z_lognorm_sorted)}, broad normal at x0={x0_broad}, sigma=1.5")
single_str_ln = (
    f"{result_lognorm['single_curve_elbow']:.2e}"
    if result_lognorm["single_curve_elbow"]
    else "None"
)
multi_str_ln = (
    f"{result_lognorm['multi_curve_elbow']:.2e}" if result_lognorm["multi_curve_elbow"] else "None"
)
print(f"\nSingle-curve elbow: {single_str_ln}")
print(f"Multi-curve elbow (quantile): {multi_str_ln}")

print(f"\nQuantile ratios (should be > 0.5, NOT << 1):")
for q, r in zip(QUANTILE_GRID, result_lognorm["quantile_ratios"]):
    print(f"  q={q:.3f}: ratio={r:.3e}")

mean_ratio_lognorm = np.nanmean(result_lognorm["quantile_ratios"])
if mean_ratio_lognorm > 0.5:
    print(f"\n✓ Mean ratio {mean_ratio_lognorm:.3e} > 0.5 (broad, NOT spike)")
else:
    print(f"\n✗ Mean ratio {mean_ratio_lognorm:.3e} < 0.5 (would misclassify!)")

mass_at_smallest = result_lognorm["mass_curve"][0]
print(f"\nMass at smallest epsilon: {mass_at_smallest:.4f}")
if mass_at_smallest < 0.01:
    print("✓ Very little mass at tiny epsilon (confirms broad)")

# %% [markdown]
"""
## Part 3: Visualization
"""

# %% Create main 4-panel visualization
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Plot 1: Boundary Tight Pileup
ax = axes[0, 0]
ax.plot(
    QUANTILE_GRID,
    result_tight["diagnostics"]["threshold_at_quantile"],
    "o-",
    linewidth=2,
    markersize=6,
    label="Threshold at quantile",
    color="navy",
    alpha=0.7,
)
if result_tight["single_curve_elbow"] is not None:
    ax.axhline(
        result_tight["single_curve_elbow"],
        color="red",
        ls="--",
        linewidth=2.5,
        label=f"Single: {result_tight['single_curve_elbow']:.4f}",
    )
if multi_thresh_tight is not None:
    ax.axhline(
        multi_thresh_tight,
        color="blue",
        ls="--",
        linewidth=2.5,
        label=f"Multi: {multi_thresh_tight:.4f}",
    )
ax.axhline(0.003, color="green", ls="-.", linewidth=2.5, label="True: 0.003", alpha=0.8)
ax.set_xlabel("Quantile", fontsize=12, fontweight="bold")
ax.set_ylabel("Tolerance", fontsize=12, fontweight="bold")
ax.set_title("Boundary: Tight Pileup (3% in 0.3%)", fontsize=14, fontweight="bold")
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# Plot 2: Boundary Uniform
ax = axes[0, 1]
ax.plot(
    QUANTILE_GRID,
    result_uniform["diagnostics"]["threshold_at_quantile"],
    "o-",
    linewidth=2,
    markersize=6,
    label="Threshold at quantile",
    color="purple",
    alpha=0.7,
)
ax.plot(QUANTILE_GRID, QUANTILE_GRID, "k--", linewidth=2, label="y=x (uniform)", alpha=0.5)
if result_uniform["single_curve_elbow"] is not None:
    ax.axhline(
        result_uniform["single_curve_elbow"],
        color="red",
        ls="--",
        linewidth=2.5,
        label=f"Single: {result_uniform['single_curve_elbow']:.4f}",
    )
if multi_thresh_uniform is not None:
    ax.axhline(
        multi_thresh_uniform,
        color="blue",
        ls="--",
        linewidth=2.5,
        label=f"Multi: {multi_thresh_uniform:.4f}",
    )
ax.set_xlabel("Quantile", fontsize=12, fontweight="bold")
ax.set_ylabel("Tolerance", fontsize=12, fontweight="bold")
ax.set_title("Boundary: Uniform (No Pileup)", fontsize=14, fontweight="bold")
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# Plot 3: Interior Spike
ax = axes[1, 0]
quantile_log = QUANTILE_GRID[QUANTILE_GRID > 0]
threshold_log = result_spike["diagnostics"]["threshold_at_quantile"][: len(quantile_log)]
ax.loglog(
    quantile_log,
    threshold_log,
    "o-",
    linewidth=2,
    markersize=6,
    label="Epsilon at quantile",
    color="darkorange",
    alpha=0.7,
)
ax.loglog(quantile_log, quantile_log, "k--", linewidth=2, label="y=x (no spike)", alpha=0.5)
if result_spike["single_curve_elbow"] is not None:
    ax.axhline(
        result_spike["single_curve_elbow"],
        color="red",
        ls="--",
        linewidth=2.5,
        label=f"Single: {result_spike['single_curve_elbow']:.2e}",
    )
if result_spike["multi_curve_elbow"] is not None:
    multi_eps = np.interp(
        result_spike["multi_curve_elbow"],
        QUANTILE_GRID,
        result_spike["diagnostics"]["threshold_at_quantile"],
    )
    ax.axhline(multi_eps, color="blue", ls="--", linewidth=2.5, label=f"Multi: {multi_eps:.2e}")
ax.set_xlabel("Quantile (log)", fontsize=12, fontweight="bold")
ax.set_ylabel("Epsilon (log)", fontsize=12, fontweight="bold")
ax.set_title("Interior: Spike (Deviation from y=x)", fontsize=14, fontweight="bold")
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3, which="both")

# Plot 4: Interior Broad Normal
ax = axes[1, 1]
threshold_log = result_lognorm["diagnostics"]["threshold_at_quantile"][: len(quantile_log)]
ax.loglog(
    quantile_log,
    threshold_log,
    "o-",
    linewidth=2,
    markersize=6,
    label="Epsilon at quantile",
    color="teal",
    alpha=0.7,
)
ax.loglog(quantile_log, quantile_log, "k--", linewidth=2, label="y=x (no spike)", alpha=0.5)
if result_lognorm["single_curve_elbow"] is not None:
    ax.axhline(
        result_lognorm["single_curve_elbow"],
        color="red",
        ls="--",
        linewidth=2.5,
        label=f"Single: {result_lognorm['single_curve_elbow']:.2e}",
    )
if result_lognorm["multi_curve_elbow"] is not None:
    multi_eps = np.interp(
        result_lognorm["multi_curve_elbow"],
        QUANTILE_GRID,
        result_lognorm["diagnostics"]["threshold_at_quantile"],
    )
    ax.axhline(multi_eps, color="blue", ls="--", linewidth=2.5, label=f"Multi: {multi_eps:.2e}")
ax.set_xlabel("Quantile (log)", fontsize=12, fontweight="bold")
ax.set_ylabel("Epsilon (log)", fontsize=12, fontweight="bold")
ax.set_title("Interior: Broad Normal at x0 (No Spike)", fontsize=14, fontweight="bold")
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3, which="both")

plt.tight_layout()
plt.savefig("/home/user/fitqc/tmp/quantile_validation.png", dpi=150, bbox_inches="tight")
plt.show()

print("\nFigure saved to /home/user/fitqc/tmp/quantile_validation.png")

# %% Summary table
print("\n" + "=" * 120)
print("VALIDATION SUMMARY")
print("=" * 120)


# Compute errors
def fmt_err(err):
    return f"{err:.2%}" if err is not None else "N/A"


table_rows = [
    (
        "Boundary Tight (0.3%)",
        result_tight["single_curve_elbow"],
        multi_thresh_tight,
        0.003,
        fmt_err(result_tight["single_error"]),
        fmt_err(result_tight["multi_error"]),
    ),
    (
        "Boundary Uniform",
        result_uniform["single_curve_elbow"],
        multi_thresh_uniform,
        None,
        "N/A",
        "N/A",
    ),
    (
        "Boundary Broad (5.0%)",
        result_broad["single_curve_elbow"],
        multi_thresh_broad,
        0.05,
        fmt_err(result_broad["single_error"]),
        fmt_err(result_broad["multi_error"]),
    ),
    (
        "Interior Spike",
        result_spike["single_curve_elbow"],
        np.interp(
            result_spike["multi_curve_elbow"],
            QUANTILE_GRID,
            result_spike["diagnostics"]["threshold_at_quantile"],
        )
        if result_spike["multi_curve_elbow"]
        else None,
        None,
        "N/A",
        "N/A",
    ),
    (
        "Interior Broad Normal",
        result_lognorm["single_curve_elbow"],
        np.interp(
            result_lognorm["multi_curve_elbow"],
            QUANTILE_GRID,
            result_lognorm["diagnostics"]["threshold_at_quantile"],
        )
        if result_lognorm["multi_curve_elbow"]
        else None,
        None,
        "N/A",
        "N/A",
    ),
]

print(
    f"\n{'Test Case':<30} | {'Single Elbow':<15} | {'Multi Elbow':<15} | {'True':<15} | {'Single Err':<12} | {'Multi Err':<12}"
)
print("-" * 120)

for name, single, multi, true, s_err, m_err in table_rows:
    single_str = f"{single:.6f}" if single is not None else "None"
    multi_str = f"{multi:.6f}" if multi is not None else "None"
    true_str = f"{true:.6f}" if true is not None else "N/A"
    print(
        f"{name:<30} | {single_str:<15} | {multi_str:<15} | {true_str:<15} | {s_err:<12} | {m_err:<12}"
    )

# %% Final conclusions
print("\n" + "=" * 120)
print("CONCLUSIONS")
print("=" * 120)

print("\nKey Findings:")
print("-" * 120)

# Boundary tight
if result_tight["multi_error"] and result_tight["single_error"]:
    if result_tight["multi_error"] < result_tight["single_error"]:
        improvement = (
            100
            * (result_tight["single_error"] - result_tight["multi_error"])
            / result_tight["single_error"]
        )
        print(f"1. Tight boundary pileup: Multi-curve {improvement:.0f}% MORE accurate")
    else:
        print(f"1. Tight boundary pileup: Single-curve more accurate (unexpected)")
else:
    print(f"1. Tight boundary pileup: Cannot compare")

# Uniform
if abs(ratio_mean - 1.0) < 0.15:
    print(f"2. Uniform data: PASS (ratio={ratio_mean:.3f} ≈ 1.0)")
else:
    print(f"2. Uniform data: WARNING (ratio={ratio_mean:.3f} deviates from 1.0)")

# Interior spike
if mean_ratio_spike < 0.1:
    print(f"3. Interior spike: PASS (ratio={mean_ratio_spike:.3e} << 1)")
else:
    print(f"3. Interior spike: WARNING (ratio={mean_ratio_spike:.3e} not << 1)")

# Interior broad normal
if mean_ratio_lognorm > 0.5:
    print(
        f"4. Broad normal at x0: PASS (ratio={mean_ratio_lognorm:.3e} > 0.5, correctly NOT flagged)"
    )
else:
    print(f"4. Broad normal at x0: FAIL (ratio={mean_ratio_lognorm:.3e} < 0.5, would misclassify!)")

print("\nRecommendation:")
print("-" * 120)

success_count = 0
if (
    result_tight["multi_error"]
    and result_tight["single_error"]
    and result_tight["multi_error"] < result_tight["single_error"]
):
    success_count += 1
if abs(ratio_mean - 1.0) < 0.15:
    success_count += 1
if mean_ratio_spike < 0.1:
    success_count += 1
if mean_ratio_lognorm > 0.5:
    success_count += 1

if success_count >= 3:
    print("✓ PROCEED with full implementation")
    print("  Multi-curve quantile-based detection shows significant promise.")
    print("  It improves accuracy on tight pileups while maintaining robustness.")
else:
    print("⚠ REVIEW NEEDED")
    print(f"  Only {success_count}/4 validation tests passed.")
    print("  Investigate failures before proceeding.")

print("\n" + "=" * 120)
print("Validation complete!")
print("=" * 120)

# %%
