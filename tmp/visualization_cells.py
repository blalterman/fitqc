"""
Visualization cells for quantile-based boundary detection validation.

This file contains matplotlib code to visualize the comparison between
single-curve and multi-curve quantile analysis for both boundary and
interior detection.

Assumes the following variables are available from running the validation tests:
- result_tight: Results from boundary tight pileup test (0.3% at boundary)
- result_uniform: Results from boundary uniform test
- result_broad: Results from boundary broad pileup test (5% at boundary)
- result_spike: Results from interior spike test
- result_lognorm: Results from interior signed log-normal test
- quantile_grid: The quantile grid used for analysis
"""

# %%
# Cell 1: Imports and Setup
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Set matplotlib style for better-looking plots
plt.style.use("seaborn-v0_8-darkgrid")
plt.rcParams["figure.dpi"] = 100
plt.rcParams["font.size"] = 10

# %%
# Cell 2: Plot 1 - Boundary Tight Pileup (3% in 0.3%)
# Assumes: result_tight, quantile_grid from boundary validation

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Plot 1: Boundary Tight Pileup
ax = axes[0, 0]
ax.plot(
    quantile_grid,
    result_tight["diagnostics"]["threshold_at_quantile"],
    "o-",
    linewidth=2,
    markersize=6,
    label="Threshold at quantile",
    color="navy",
    alpha=0.7,
)

# Mark single-curve elbow
if result_tight["single_curve_elbow"] is not None:
    ax.axhline(
        result_tight["single_curve_elbow"],
        color="red",
        ls="--",
        linewidth=2.5,
        label=f"Single elbow: {result_tight['single_curve_elbow']:.4f}",
    )

# Mark multi-curve elbow (convert from quantile to threshold)
if result_tight["multi_curve_elbow"] is not None:
    multi_thresh = np.interp(
        result_tight["multi_curve_elbow"],
        quantile_grid,
        result_tight["diagnostics"]["threshold_at_quantile"],
    )
    ax.axhline(
        multi_thresh, color="blue", ls="--", linewidth=2.5, label=f"Multi elbow: {multi_thresh:.4f}"
    )

# Mark ground truth
ax.axhline(0.003, color="green", ls="-.", linewidth=2.5, label="True boundary: 0.003", alpha=0.8)

ax.set_xlabel("Quantile", fontsize=12, fontweight="bold")
ax.set_ylabel("Tolerance", fontsize=12, fontweight="bold")
ax.set_title("Boundary: Tight Pileup (3% in 0.3%)", fontsize=14, fontweight="bold")
ax.legend(fontsize=10, loc="best")
ax.grid(True, alpha=0.3)

# %%
# Cell 3: Plot 2 - Boundary Uniform (Should be Linear)
# Assumes: result_uniform, quantile_grid from boundary validation

ax = axes[0, 1]
ax.plot(
    quantile_grid,
    result_uniform["diagnostics"]["threshold_at_quantile"],
    "o-",
    linewidth=2,
    markersize=6,
    label="Threshold at quantile",
    color="purple",
    alpha=0.7,
)

# Add y=x reference line (for uniform, threshold ≈ quantile)
ax.plot(quantile_grid, quantile_grid, "k--", linewidth=2, label="y=x (uniform)", alpha=0.5)

# Mark single-curve elbow (should be None or very weak)
if result_uniform["single_curve_elbow"] is not None:
    ax.axhline(
        result_uniform["single_curve_elbow"],
        color="red",
        ls="--",
        linewidth=2.5,
        label=f"Single elbow: {result_uniform['single_curve_elbow']:.4f}",
    )

# Mark multi-curve elbow (should be None or very weak)
if result_uniform["multi_curve_elbow"] is not None:
    multi_thresh = np.interp(
        result_uniform["multi_curve_elbow"],
        quantile_grid,
        result_uniform["diagnostics"]["threshold_at_quantile"],
    )
    ax.axhline(
        multi_thresh, color="blue", ls="--", linewidth=2.5, label=f"Multi elbow: {multi_thresh:.4f}"
    )

ax.set_xlabel("Quantile", fontsize=12, fontweight="bold")
ax.set_ylabel("Tolerance", fontsize=12, fontweight="bold")
ax.set_title("Boundary: Uniform (Should be Linear)", fontsize=14, fontweight="bold")
ax.legend(fontsize=10, loc="best")
ax.grid(True, alpha=0.3)

# %%
# Cell 4: Plot 3 - Interior Spike (Log-Log Scale)
# Assumes: result_spike, quantile_grid from interior validation

ax = axes[1, 0]

# Log-log plot
quantile_log = quantile_grid[quantile_grid > 0]  # Exclude zero if present
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

# Add y=x reference line
ax.loglog(quantile_log, quantile_log, "k--", linewidth=2, label="y=x (no spike)", alpha=0.5)

# Mark single-curve elbow
if result_spike["single_curve_elbow"] is not None:
    ax.axhline(
        result_spike["single_curve_elbow"],
        color="red",
        ls="--",
        linewidth=2.5,
        label=f"Single elbow: {result_spike['single_curve_elbow']:.4e}",
    )

# Mark multi-curve elbow (convert from quantile to threshold)
if result_spike["multi_curve_elbow"] is not None:
    multi_thresh = np.interp(
        result_spike["multi_curve_elbow"],
        quantile_grid,
        result_spike["diagnostics"]["threshold_at_quantile"],
    )
    ax.axhline(
        multi_thresh, color="blue", ls="--", linewidth=2.5, label=f"Multi elbow: {multi_thresh:.4e}"
    )

ax.set_xlabel("Quantile (log scale)", fontsize=12, fontweight="bold")
ax.set_ylabel("Epsilon (log scale)", fontsize=12, fontweight="bold")
ax.set_title("Interior: Spike (Sharp Deviation from y=x)", fontsize=14, fontweight="bold")
ax.legend(fontsize=10, loc="best")
ax.grid(True, alpha=0.3, which="both")

# %%
# Cell 5: Plot 4 - Interior Signed Log-Normal (Should Follow y=x)
# Assumes: result_lognorm, quantile_grid from interior validation

ax = axes[1, 1]

# Log-log plot
quantile_log = quantile_grid[quantile_grid > 0]  # Exclude zero if present
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

# Add y=x reference line
ax.loglog(quantile_log, quantile_log, "k--", linewidth=2, label="y=x (no spike)", alpha=0.5)

# Mark single-curve elbow (should be None or very weak)
if result_lognorm["single_curve_elbow"] is not None:
    ax.axhline(
        result_lognorm["single_curve_elbow"],
        color="red",
        ls="--",
        linewidth=2.5,
        label=f"Single elbow: {result_lognorm['single_curve_elbow']:.4e}",
    )

# Mark multi-curve elbow (should be None or very weak)
if result_lognorm["multi_curve_elbow"] is not None:
    multi_thresh = np.interp(
        result_lognorm["multi_curve_elbow"],
        quantile_grid,
        result_lognorm["diagnostics"]["threshold_at_quantile"],
    )
    ax.axhline(
        multi_thresh, color="blue", ls="--", linewidth=2.5, label=f"Multi elbow: {multi_thresh:.4e}"
    )

ax.set_xlabel("Quantile (log scale)", fontsize=12, fontweight="bold")
ax.set_ylabel("Epsilon (log scale)", fontsize=12, fontweight="bold")
ax.set_title("Interior: Signed Log-Normal (Close to y=x, No Spike)", fontsize=14, fontweight="bold")
ax.legend(fontsize=10, loc="best")
ax.grid(True, alpha=0.3, which="both")

# %%
# Cell 6: Adjust layout and save figure
plt.tight_layout()
plt.savefig("/home/user/fitqc/tmp/quantile_validation.png", dpi=150, bbox_inches="tight")
plt.show()

print("Figure saved to /home/user/fitqc/tmp/quantile_validation.png")

# %%
# Cell 7: Summary Table
# Assumes: All result variables (result_tight, result_uniform, result_broad, result_spike, result_lognorm)


def compute_error(detected, true):
    """Compute relative error between detected and true values."""
    if detected is None or true is None:
        return None
    if true == 0:
        return abs(detected - true)
    return abs(detected - true) / abs(true)


# Prepare data for table
table_data = []

# Boundary: Tight Pileup (0.3%)
true_tight = 0.003
single_elbow_tight = result_tight["single_curve_elbow"]
multi_elbow_tight = None
if result_tight["multi_curve_elbow"] is not None:
    multi_elbow_tight = np.interp(
        result_tight["multi_curve_elbow"],
        quantile_grid,
        result_tight["diagnostics"]["threshold_at_quantile"],
    )
single_error_tight = compute_error(single_elbow_tight, true_tight)
multi_error_tight = compute_error(multi_elbow_tight, true_tight)

table_data.append(
    {
        "Test Case": "Boundary Tight (0.3%)",
        "Single Elbow": f"{single_elbow_tight:.6f}" if single_elbow_tight else "None",
        "Multi Elbow": f"{multi_elbow_tight:.6f}" if multi_elbow_tight else "None",
        "True": f"{true_tight:.3f}",
        "Single Error": f"{single_error_tight:.2%}" if single_error_tight is not None else "N/A",
        "Multi Error": f"{multi_error_tight:.2%}" if multi_error_tight is not None else "N/A",
    }
)

# Boundary: Uniform (should have no/weak elbow)
single_elbow_uniform = result_uniform["single_curve_elbow"]
multi_elbow_uniform = None
if result_uniform["multi_curve_elbow"] is not None:
    multi_elbow_uniform = np.interp(
        result_uniform["multi_curve_elbow"],
        quantile_grid,
        result_uniform["diagnostics"]["threshold_at_quantile"],
    )

table_data.append(
    {
        "Test Case": "Boundary Uniform",
        "Single Elbow": f"{single_elbow_uniform:.6f}" if single_elbow_uniform else "None",
        "Multi Elbow": f"{multi_elbow_uniform:.6f}" if multi_elbow_uniform else "None",
        "True": "N/A (no boundary)",
        "Single Error": "N/A",
        "Multi Error": "N/A",
    }
)

# Boundary: Broad Pileup (5%)
true_broad = 0.05
single_elbow_broad = result_broad["single_curve_elbow"]
multi_elbow_broad = None
if result_broad["multi_curve_elbow"] is not None:
    multi_elbow_broad = np.interp(
        result_broad["multi_curve_elbow"],
        quantile_grid,
        result_broad["diagnostics"]["threshold_at_quantile"],
    )
single_error_broad = compute_error(single_elbow_broad, true_broad)
multi_error_broad = compute_error(multi_elbow_broad, true_broad)

table_data.append(
    {
        "Test Case": "Boundary Broad (5%)",
        "Single Elbow": f"{single_elbow_broad:.6f}" if single_elbow_broad else "None",
        "Multi Elbow": f"{multi_elbow_broad:.6f}" if multi_elbow_broad else "None",
        "True": f"{true_broad:.3f}",
        "Single Error": f"{single_error_broad:.2%}" if single_error_broad is not None else "N/A",
        "Multi Error": f"{multi_error_broad:.2%}" if multi_error_broad is not None else "N/A",
    }
)

# Interior: Spike (qualitative - should detect spike)
single_elbow_spike = result_spike["single_curve_elbow"]
multi_elbow_spike = None
if result_spike["multi_curve_elbow"] is not None:
    multi_elbow_spike = np.interp(
        result_spike["multi_curve_elbow"],
        quantile_grid,
        result_spike["diagnostics"]["threshold_at_quantile"],
    )

table_data.append(
    {
        "Test Case": "Interior Spike",
        "Single Elbow": f"{single_elbow_spike:.6e}" if single_elbow_spike else "None",
        "Multi Elbow": f"{multi_elbow_spike:.6e}" if multi_elbow_spike else "None",
        "True": "N/A (qualitative)",
        "Single Error": "N/A",
        "Multi Error": "N/A",
    }
)

# Interior: Signed Log-Normal (should have no/weak spike)
single_elbow_lognorm = result_lognorm["single_curve_elbow"]
multi_elbow_lognorm = None
if result_lognorm["multi_curve_elbow"] is not None:
    multi_elbow_lognorm = np.interp(
        result_lognorm["multi_curve_elbow"],
        quantile_grid,
        result_lognorm["diagnostics"]["threshold_at_quantile"],
    )

table_data.append(
    {
        "Test Case": "Interior Signed Log-Normal",
        "Single Elbow": f"{single_elbow_lognorm:.6e}" if single_elbow_lognorm else "None",
        "Multi Elbow": f"{multi_elbow_lognorm:.6e}" if multi_elbow_lognorm else "None",
        "True": "N/A (no spike expected)",
        "Single Error": "N/A",
        "Multi Error": "N/A",
    }
)

# %%
# Cell 8: Print formatted table
print("\n" + "=" * 120)
print("QUANTILE-BASED BOUNDARY DETECTION: VALIDATION SUMMARY")
print("=" * 120)
print(
    f"{'Test Case':<30} | {'Single Elbow':<15} | {'Multi Elbow':<15} | {'True':<20} | {'Single Error':<15} | {'Multi Error':<15}"
)
print("-" * 120)

for row in table_data:
    print(
        f"{row['Test Case']:<30} | {row['Single Elbow']:<15} | {row['Multi Elbow']:<15} | {row['True']:<20} | {row['Single Error']:<15} | {row['Multi Error']:<15}"
    )

print("=" * 120)
print()

# %%
# Cell 9: Create detailed diagnostic plots for each test case
# This cell creates individual plots with more detail

fig_detail, axes_detail = plt.subplots(3, 2, figsize=(16, 18))

# Detailed Plot 1: Boundary Tight - with curvature
ax = axes_detail[0, 0]
ax.plot(
    quantile_grid,
    result_tight["diagnostics"]["threshold_at_quantile"],
    "o-",
    linewidth=2,
    markersize=6,
    label="Threshold",
    color="navy",
    alpha=0.7,
)
ax.axhline(0.003, color="green", ls="-.", linewidth=2.5, label="True: 0.003", alpha=0.8)
if result_tight["single_curve_elbow"] is not None:
    ax.axhline(
        result_tight["single_curve_elbow"],
        color="red",
        ls="--",
        linewidth=2,
        label=f"Single: {result_tight['single_curve_elbow']:.4f}",
    )
if result_tight["multi_curve_elbow"] is not None:
    multi_thresh = np.interp(
        result_tight["multi_curve_elbow"],
        quantile_grid,
        result_tight["diagnostics"]["threshold_at_quantile"],
    )
    ax.axhline(multi_thresh, color="blue", ls="--", linewidth=2, label=f"Multi: {multi_thresh:.4f}")
ax.set_xlabel("Quantile", fontsize=11)
ax.set_ylabel("Tolerance", fontsize=11)
ax.set_title("Boundary Tight (0.3%): Threshold Curve", fontsize=12, fontweight="bold")
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Detailed Plot 2: Boundary Tight - curvature
ax = axes_detail[0, 1]
if "curvature" in result_tight["diagnostics"]:
    ax.plot(
        quantile_grid,
        result_tight["diagnostics"]["curvature"],
        "o-",
        linewidth=2,
        markersize=4,
        label="Curvature",
        color="darkred",
    )
    ax.set_xlabel("Quantile", fontsize=11)
    ax.set_ylabel("Curvature", fontsize=11)
    ax.set_title("Boundary Tight: Curvature Analysis", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color="black", ls="-", linewidth=0.5, alpha=0.5)

# Detailed Plot 3: Boundary Uniform - linear check
ax = axes_detail[1, 0]
ax.plot(
    quantile_grid,
    result_uniform["diagnostics"]["threshold_at_quantile"],
    "o-",
    linewidth=2,
    markersize=6,
    label="Threshold",
    color="purple",
    alpha=0.7,
)
ax.plot(quantile_grid, quantile_grid, "k--", linewidth=2, label="y=x", alpha=0.5)
residuals = result_uniform["diagnostics"]["threshold_at_quantile"] - quantile_grid
ax.plot(
    quantile_grid,
    residuals + quantile_grid,
    "s-",
    linewidth=1,
    markersize=4,
    label=f"Residual (max={np.max(np.abs(residuals)):.4f})",
    color="orange",
    alpha=0.6,
)
ax.set_xlabel("Quantile", fontsize=11)
ax.set_ylabel("Tolerance", fontsize=11)
ax.set_title("Boundary Uniform: Linearity Check", fontsize=12, fontweight="bold")
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Detailed Plot 4: Boundary Broad
ax = axes_detail[1, 1]
ax.plot(
    quantile_grid,
    result_broad["diagnostics"]["threshold_at_quantile"],
    "o-",
    linewidth=2,
    markersize=6,
    label="Threshold",
    color="darkgreen",
    alpha=0.7,
)
ax.axhline(0.05, color="green", ls="-.", linewidth=2.5, label="True: 0.05", alpha=0.8)
if result_broad["single_curve_elbow"] is not None:
    ax.axhline(
        result_broad["single_curve_elbow"],
        color="red",
        ls="--",
        linewidth=2,
        label=f"Single: {result_broad['single_curve_elbow']:.4f}",
    )
if result_broad["multi_curve_elbow"] is not None:
    multi_thresh = np.interp(
        result_broad["multi_curve_elbow"],
        quantile_grid,
        result_broad["diagnostics"]["threshold_at_quantile"],
    )
    ax.axhline(multi_thresh, color="blue", ls="--", linewidth=2, label=f"Multi: {multi_thresh:.4f}")
ax.set_xlabel("Quantile", fontsize=11)
ax.set_ylabel("Tolerance", fontsize=11)
ax.set_title("Boundary Broad (5%): Threshold Curve", fontsize=12, fontweight="bold")
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Detailed Plot 5: Interior Spike - deviation from y=x
ax = axes_detail[2, 0]
quantile_log = quantile_grid[quantile_grid > 0]
threshold_log = result_spike["diagnostics"]["threshold_at_quantile"][: len(quantile_log)]
ax.loglog(
    quantile_log,
    threshold_log,
    "o-",
    linewidth=2,
    markersize=6,
    label="Epsilon",
    color="darkorange",
    alpha=0.7,
)
ax.loglog(quantile_log, quantile_log, "k--", linewidth=2, label="y=x", alpha=0.5)
deviation = np.log10(threshold_log) - np.log10(quantile_log)
ax2 = ax.twinx()
ax2.plot(
    quantile_log,
    deviation,
    "s-",
    linewidth=1,
    markersize=4,
    label="Log deviation",
    color="red",
    alpha=0.5,
)
ax2.set_ylabel("Log10(epsilon) - Log10(quantile)", fontsize=10, color="red")
ax2.tick_params(axis="y", labelcolor="red")
ax.set_xlabel("Quantile (log)", fontsize=11)
ax.set_ylabel("Epsilon (log)", fontsize=11)
ax.set_title("Interior Spike: Deviation Analysis", fontsize=12, fontweight="bold")
ax.legend(loc="upper left", fontsize=9)
ax2.legend(loc="upper right", fontsize=9)
ax.grid(True, alpha=0.3, which="both")

# Detailed Plot 6: Interior Log-Normal - should be uniform
ax = axes_detail[2, 1]
quantile_log = quantile_grid[quantile_grid > 0]
threshold_log = result_lognorm["diagnostics"]["threshold_at_quantile"][: len(quantile_log)]
ax.loglog(
    quantile_log,
    threshold_log,
    "o-",
    linewidth=2,
    markersize=6,
    label="Epsilon",
    color="teal",
    alpha=0.7,
)
ax.loglog(quantile_log, quantile_log, "k--", linewidth=2, label="y=x", alpha=0.5)
deviation = np.log10(threshold_log) - np.log10(quantile_log)
ax2 = ax.twinx()
ax2.plot(
    quantile_log,
    deviation,
    "s-",
    linewidth=1,
    markersize=4,
    label=f"Log deviation (std={np.std(deviation):.3f})",
    color="purple",
    alpha=0.5,
)
ax2.set_ylabel("Log10(epsilon) - Log10(quantile)", fontsize=10, color="purple")
ax2.tick_params(axis="y", labelcolor="purple")
ax.set_xlabel("Quantile (log)", fontsize=11)
ax.set_ylabel("Epsilon (log)", fontsize=11)
ax.set_title("Interior Log-Normal: Uniformity Check", fontsize=12, fontweight="bold")
ax.legend(loc="upper left", fontsize=9)
ax2.legend(loc="upper right", fontsize=9)
ax.grid(True, alpha=0.3, which="both")

plt.tight_layout()
plt.savefig("/home/user/fitqc/tmp/quantile_validation_detailed.png", dpi=150, bbox_inches="tight")
plt.show()

print("Detailed figure saved to /home/user/fitqc/tmp/quantile_validation_detailed.png")

# %%
# Cell 10: Performance comparison summary
print("\n" + "=" * 100)
print("PERFORMANCE ANALYSIS")
print("=" * 100)

print("\nBoundary Detection (Tight and Broad cases):")
print("-" * 100)

# Tight case
if single_error_tight is not None and multi_error_tight is not None:
    if multi_error_tight < single_error_tight:
        improvement = (single_error_tight - multi_error_tight) / single_error_tight * 100
        print(
            f"  Tight (0.3%): Multi-curve is BETTER by {improvement:.1f}% (errors: {single_error_tight:.2%} vs {multi_error_tight:.2%})"
        )
    elif single_error_tight < multi_error_tight:
        degradation = (multi_error_tight - single_error_tight) / multi_error_tight * 100
        print(
            f"  Tight (0.3%): Single-curve is BETTER by {degradation:.1f}% (errors: {single_error_tight:.2%} vs {multi_error_tight:.2%})"
        )
    else:
        print(f"  Tight (0.3%): Methods are EQUIVALENT (both {single_error_tight:.2%})")
else:
    print(
        f"  Tight (0.3%): Cannot compare (single: {single_error_tight}, multi: {multi_error_tight})"
    )

# Broad case
if single_error_broad is not None and multi_error_broad is not None:
    if multi_error_broad < single_error_broad:
        improvement = (single_error_broad - multi_error_broad) / single_error_broad * 100
        print(
            f"  Broad (5.0%): Multi-curve is BETTER by {improvement:.1f}% (errors: {single_error_broad:.2%} vs {multi_error_broad:.2%})"
        )
    elif single_error_broad < multi_error_broad:
        degradation = (multi_error_broad - single_error_broad) / multi_error_broad * 100
        print(
            f"  Broad (5.0%): Single-curve is BETTER by {degradation:.1f}% (errors: {single_error_broad:.2%} vs {multi_error_broad:.2%})"
        )
    else:
        print(f"  Broad (5.0%): Methods are EQUIVALENT (both {single_error_broad:.2%})")
else:
    print(
        f"  Broad (5.0%): Cannot compare (single: {single_error_broad}, multi: {multi_error_broad})"
    )

print("\nControl Cases (should have no/weak elbow):")
print("-" * 100)

# Check if uniform correctly has no elbow
uniform_has_elbow = (single_elbow_uniform is not None) or (multi_elbow_uniform is not None)
if not uniform_has_elbow:
    print("  Uniform: PASS - No elbows detected (as expected)")
else:
    print(
        f"  Uniform: WARNING - Elbows detected when none expected (single: {single_elbow_uniform}, multi: {multi_elbow_uniform})"
    )

# Check log-normal
lognorm_has_elbow = (single_elbow_lognorm is not None) or (multi_elbow_lognorm is not None)
if not lognorm_has_elbow:
    print("  Log-Normal: PASS - No elbows detected (as expected)")
else:
    print(
        f"  Log-Normal: INFO - Elbows detected (single: {single_elbow_lognorm}, multi: {multi_elbow_lognorm})"
    )

print("\nInterior Spike Detection:")
print("-" * 100)

spike_detected = (single_elbow_spike is not None) or (multi_elbow_spike is not None)
if spike_detected:
    print(
        f"  Spike: PASS - Elbow detected (single: {single_elbow_spike}, multi: {multi_elbow_spike})"
    )
else:
    print("  Spike: WARNING - No elbow detected when spike was expected")

print("=" * 100)
print()
