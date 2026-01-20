"""Boundary validation test cases for quantile-based threshold detection.

This module contains executable test scenarios validating that quantile-based
multi-curve threshold detection works better than single-curve for boundary
pileup detection.

Execute cells sequentially to run validation tests.
"""

# Cell 1: Imports and setup
# ============================================================================

import sys
import numpy as np

# Add path for POC functions
sys.path.append("/home/user/fitqc/tmp")

from fitqc.synth import generate_with_boundary_pileup
from fitqc.boundary import compute_u
from poc_quantile_threshold import compare_single_vs_multi_curve

# Common test configuration
GRID = np.linspace(0.0, 0.05, 41)
QUANTILE_GRID = np.array([0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10])
LOG_SPACE = False

print("=" * 80)
print("BOUNDARY VALIDATION: Quantile-based Threshold Detection")
print("=" * 80)
print(f"Grid: {len(GRID)} points from {GRID[0]:.4f} to {GRID[-1]:.4f}")
print(f"Quantile grid: {QUANTILE_GRID}")
print(f"Log space: {LOG_SPACE}")
print()


# Cell 2: Scenario 1 - Tight Pileup (3% in 0.3% of range)
# ============================================================================

print("\n" + "=" * 80)
print("SCENARIO 1: Tight Pileup (3% in 0.3% of range)")
print("=" * 80)

# Generate data with tight boundary pileup
x_tight = generate_with_boundary_pileup(
    n=10000,
    L=0.0,
    U=1.0,
    lower_pileup_frac=0.03,  # 3% of data at boundary
    pileup_width=0.003,  # 0.3% of range (tight!)
    seed=42,
)

# Transform to u-space
u_tight = compute_u(x_tight, L=0.0, U=1.0)
u_tight_sorted = np.sort(u_tight)

print(f"\nData generated: n={len(u_tight)}")
print(f"Lower pileup fraction: 3%")
print(f"Pileup width: 0.003 (0.3% of range)")
print(f"Expected ground truth threshold: 0.003")

# Test both approaches
true_threshold_tight = 0.003
result_tight = compare_single_vs_multi_curve(
    u_tight_sorted, GRID, QUANTILE_GRID, log_space=LOG_SPACE, true_threshold=true_threshold_tight
)

# Print results
print("\n" + "-" * 80)
print("RESULTS: Tight Pileup")
print("-" * 80)
print(f"True threshold: {true_threshold_tight:.4f}")
print(f"\nSingle-curve elbow (threshold): {result_tight['single_curve_elbow']}")
print(f"Multi-curve elbow (quantile): {result_tight['multi_curve_elbow']}")

if result_tight["multi_curve_elbow"] is not None:
    multi_thresh_tight = np.interp(
        result_tight["multi_curve_elbow"],
        QUANTILE_GRID,
        result_tight["diagnostics"]["threshold_at_quantile"],
    )
    print(f"Multi-curve threshold: {multi_thresh_tight:.6f}")
else:
    multi_thresh_tight = None
    print("Multi-curve threshold: None (no elbow detected)")

print(
    f"\nSingle-curve error: {result_tight['single_error']:.6f}"
    if result_tight["single_error"] is not None
    else "\nSingle-curve error: None"
)
print(
    f"Multi-curve error: {result_tight['multi_error']:.6f}"
    if result_tight["multi_error"] is not None
    else "Multi-curve error: None"
)

print(f"\nQuantile-to-threshold ratios:")
for q, r in zip(QUANTILE_GRID, result_tight["quantile_ratios"]):
    print(f"  q={q:.3f}: ratio={r:.3f}")

# Interpretation
print("\n" + "-" * 80)
print("INTERPRETATION:")
print("-" * 80)
print("For tight pileup, we expect:")
print("  - Single-curve may struggle to detect the narrow pileup region")
print("  - Multi-curve should show clear elbow near q=0.03 (pileup fraction)")
print("  - Ratios should be very small (<< 1) before elbow, then increase")
if result_tight["multi_error"] is not None and result_tight["single_error"] is not None:
    if result_tight["multi_error"] < result_tight["single_error"]:
        print(
            f"\n  VALIDATION: Multi-curve is MORE accurate (error {result_tight['multi_error']:.6f} vs {result_tight['single_error']:.6f})"
        )
    else:
        print(
            f"\n  WARNING: Single-curve is more accurate (error {result_tight['single_error']:.6f} vs {result_tight['multi_error']:.6f})"
        )
print()


# Cell 3: Scenario 2 - Uniform (No Pileup)
# ============================================================================

print("\n" + "=" * 80)
print("SCENARIO 2: Uniform (No Pileup)")
print("=" * 80)

# Generate uniform data
np.random.seed(42)
x_uniform = np.random.uniform(0.0, 1.0, 10000)

# Transform to u-space (should remain uniform [0,1])
u_uniform = compute_u(x_uniform, L=0.0, U=1.0)
u_uniform_sorted = np.sort(u_uniform)

print(f"\nData generated: n={len(u_uniform)}")
print(f"Distribution: Uniform [0, 1]")
print(f"Expected: No pileup, no clear elbow")

# Test both approaches (no true threshold for uniform data)
result_uniform = compare_single_vs_multi_curve(
    u_uniform_sorted,
    GRID,
    QUANTILE_GRID,
    log_space=LOG_SPACE,
    true_threshold=None,  # No ground truth for uniform
)

# Print results
print("\n" + "-" * 80)
print("RESULTS: Uniform Data")
print("-" * 80)
print(f"Single-curve elbow (threshold): {result_uniform['single_curve_elbow']}")
print(f"Multi-curve elbow (quantile): {result_uniform['multi_curve_elbow']}")

if result_uniform["multi_curve_elbow"] is not None:
    multi_thresh_uniform = np.interp(
        result_uniform["multi_curve_elbow"],
        QUANTILE_GRID,
        result_uniform["diagnostics"]["threshold_at_quantile"],
    )
    print(f"Multi-curve threshold: {multi_thresh_uniform:.6f}")
else:
    multi_thresh_uniform = None
    print("Multi-curve threshold: None (no elbow detected)")

print(f"\nQuantile-to-threshold ratios:")
for q, r in zip(QUANTILE_GRID, result_uniform["quantile_ratios"]):
    print(f"  q={q:.3f}: ratio={r:.3f}")

# Compute ratio statistics
ratio_mean = np.nanmean(result_uniform["quantile_ratios"])
ratio_std = np.nanstd(result_uniform["quantile_ratios"])
print(f"\nRatio statistics:")
print(f"  Mean: {ratio_mean:.3f}")
print(f"  Std: {ratio_std:.3f}")

# Interpretation
print("\n" + "-" * 80)
print("INTERPRETATION:")
print("-" * 80)
print("For uniform data, we expect:")
print("  - No clear elbow in either approach (or very weak elbow)")
print("  - Ratios should be approximately 1.0 ± 0.15")
print("  - For uniform [0,1], threshold ≈ quantile (linear relationship)")

within_tolerance = np.abs(ratio_mean - 1.0) < 0.15
if within_tolerance:
    print(f"\n  VALIDATION: Ratios are within tolerance (mean={ratio_mean:.3f}, expected ~1.0)")
else:
    print(f"\n  WARNING: Ratios deviate from expected (mean={ratio_mean:.3f}, expected ~1.0)")

if result_uniform["single_curve_elbow"] is None and result_uniform["multi_curve_elbow"] is None:
    print("  VALIDATION: Both methods correctly found no strong elbow")
elif (
    result_uniform["single_curve_elbow"] is not None
    or result_uniform["multi_curve_elbow"] is not None
):
    print("  NOTE: Weak elbows detected, but expected for uniform data edge effects")
print()


# Cell 4: Scenario 3 - Broad Pileup (10% in 5% of range)
# ============================================================================

print("\n" + "=" * 80)
print("SCENARIO 3: Broad Pileup (10% in 5% of range)")
print("=" * 80)

# Generate data with broad boundary pileup
x_broad = generate_with_boundary_pileup(
    n=10000,
    L=0.0,
    U=1.0,
    lower_pileup_frac=0.10,  # 10% of data at boundary
    pileup_width=0.05,  # 5% of range (broad)
    seed=42,
)

# Transform to u-space
u_broad = compute_u(x_broad, L=0.0, U=1.0)
u_broad_sorted = np.sort(u_broad)

print(f"\nData generated: n={len(u_broad)}")
print(f"Lower pileup fraction: 10%")
print(f"Pileup width: 0.05 (5% of range)")
print(f"Expected ground truth threshold: 0.05")

# Test both approaches
true_threshold_broad = 0.05
result_broad = compare_single_vs_multi_curve(
    u_broad_sorted, GRID, QUANTILE_GRID, log_space=LOG_SPACE, true_threshold=true_threshold_broad
)

# Print results
print("\n" + "-" * 80)
print("RESULTS: Broad Pileup")
print("-" * 80)
print(f"True threshold: {true_threshold_broad:.4f}")
print(f"\nSingle-curve elbow (threshold): {result_broad['single_curve_elbow']}")
print(f"Multi-curve elbow (quantile): {result_broad['multi_curve_elbow']}")

if result_broad["multi_curve_elbow"] is not None:
    multi_thresh_broad = np.interp(
        result_broad["multi_curve_elbow"],
        QUANTILE_GRID,
        result_broad["diagnostics"]["threshold_at_quantile"],
    )
    print(f"Multi-curve threshold: {multi_thresh_broad:.6f}")
else:
    multi_thresh_broad = None
    print("Multi-curve threshold: None (no elbow detected)")

print(
    f"\nSingle-curve error: {result_broad['single_error']:.6f}"
    if result_broad["single_error"] is not None
    else "\nSingle-curve error: None"
)
print(
    f"Multi-curve error: {result_broad['multi_error']:.6f}"
    if result_broad["multi_error"] is not None
    else "Multi-curve error: None"
)

print(f"\nQuantile-to-threshold ratios:")
for q, r in zip(QUANTILE_GRID, result_broad["quantile_ratios"]):
    print(f"  q={q:.3f}: ratio={r:.3f}")

# Interpretation
print("\n" + "-" * 80)
print("INTERPRETATION:")
print("-" * 80)
print("For broad pileup, we expect:")
print("  - Both methods should detect the pileup region")
print("  - Elbow should occur near q=0.10 (pileup fraction)")
print("  - Broader pileup may be easier to detect than tight pileup")
print("  - Both approaches should have reasonable accuracy")

if result_broad["multi_error"] is not None and result_broad["single_error"] is not None:
    if result_broad["multi_error"] < result_broad["single_error"]:
        print(
            f"\n  VALIDATION: Multi-curve is MORE accurate (error {result_broad['multi_error']:.6f} vs {result_broad['single_error']:.6f})"
        )
    elif result_broad["single_error"] < result_broad["multi_error"]:
        print(
            f"\n  NOTE: Single-curve is more accurate for broad pileup (error {result_broad['single_error']:.6f} vs {result_broad['multi_error']:.6f})"
        )
    else:
        print(f"\n  NOTE: Both methods have similar accuracy")
else:
    print("\n  WARNING: One or both methods failed to detect elbow")
print()


# Cell 5: Summary and Comparison
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY: Comparison Across Scenarios")
print("=" * 80)

print("\n" + "-" * 80)
print("Scenario Comparison Table")
print("-" * 80)

print(
    f"{'Scenario':<20} {'True Thresh':<12} {'Single Elbow':<15} {'Multi Elbow':<15} {'Single Error':<15} {'Multi Error':<15}"
)
print("-" * 92)

# Tight pileup
single_tight_str = (
    f"{result_tight['single_curve_elbow']:.6f}"
    if result_tight["single_curve_elbow"] is not None
    else "None"
)
multi_tight_str = f"{multi_thresh_tight:.6f}" if multi_thresh_tight is not None else "None"
single_err_tight = (
    f"{result_tight['single_error']:.6f}" if result_tight["single_error"] is not None else "None"
)
multi_err_tight = (
    f"{result_tight['multi_error']:.6f}" if result_tight["multi_error"] is not None else "None"
)
print(
    f"{'Tight (3% in 0.3%)':<20} {true_threshold_tight:<12.6f} {single_tight_str:<15} {multi_tight_str:<15} {single_err_tight:<15} {multi_err_tight:<15}"
)

# Uniform
single_uniform_str = (
    f"{result_uniform['single_curve_elbow']:.6f}"
    if result_uniform["single_curve_elbow"] is not None
    else "None"
)
multi_uniform_str = f"{multi_thresh_uniform:.6f}" if multi_thresh_uniform is not None else "None"
print(
    f"{'Uniform':<20} {'N/A':<12} {single_uniform_str:<15} {multi_uniform_str:<15} {'N/A':<15} {'N/A':<15}"
)

# Broad pileup
single_broad_str = (
    f"{result_broad['single_curve_elbow']:.6f}"
    if result_broad["single_curve_elbow"] is not None
    else "None"
)
multi_broad_str = f"{multi_thresh_broad:.6f}" if multi_thresh_broad is not None else "None"
single_err_broad = (
    f"{result_broad['single_error']:.6f}" if result_broad["single_error"] is not None else "None"
)
multi_err_broad = (
    f"{result_broad['multi_error']:.6f}" if result_broad["multi_error"] is not None else "None"
)
print(
    f"{'Broad (10% in 5%)':<20} {true_threshold_broad:<12.6f} {single_broad_str:<15} {multi_broad_str:<15} {single_err_broad:<15} {multi_err_broad:<15}"
)

print("\n" + "-" * 80)
print("Key Findings:")
print("-" * 80)

# Count wins
tight_winner = (
    "Multi"
    if (
        result_tight["multi_error"] is not None
        and result_tight["single_error"] is not None
        and result_tight["multi_error"] < result_tight["single_error"]
    )
    else "Single"
)
broad_winner = (
    "Multi"
    if (
        result_broad["multi_error"] is not None
        and result_broad["single_error"] is not None
        and result_broad["multi_error"] < result_broad["single_error"]
    )
    else "Single"
)

print(f"1. Tight pileup: {tight_winner}-curve is more accurate")
print(f"2. Broad pileup: {broad_winner}-curve is more accurate")
print(f"3. Uniform data: Ratio mean = {ratio_mean:.3f} (expected ~1.0)")

print("\nConclusion:")
if tight_winner == "Multi" or broad_winner == "Multi":
    print("  Multi-curve quantile-based detection shows promise for boundary pileup.")
    print("  It provides competitive or better accuracy compared to single-curve.")
else:
    print("  Single-curve remains competitive. Further investigation needed.")

print("\n" + "=" * 80)
print("All validation tests completed!")
print("=" * 80)
