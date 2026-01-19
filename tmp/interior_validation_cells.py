"""Interior Validation: Quantile-based multi-curve threshold detection for log-space.

This module validates that quantile-based threshold detection correctly identifies
interior spikes (stickiness at x0) while avoiding false positives on broad distributions.

Test Scenarios
--------------
1. Tight Spike (5% at x0): Should detect very small epsilon threshold
2. Signed Log-Normal (Broad): Should NOT detect spike despite natural mass near zero
3. Precision-Limited Spike (3% exact zeros): Should detect machine-precision epsilon

The key diagnostic is the quantile ratio (threshold/quantile). For tight spikes,
these ratios should be << 1 across quantiles, indicating the threshold grows slower
than the quantile (mass is concentrated). For broad distributions, ratios should be
> 0.5, indicating more uniform spread.
"""

# %% Imports and setup
import numpy as np
import sys
sys.path.append('../tmp')
sys.path.append('../src')

from fitqc.synth import generate_with_x0_spike, generate_signed_lognormal
from fitqc.interior import compute_z
from poc_quantile_threshold import compare_single_vs_multi_curve

# Common grid parameters for all tests
grid_log = np.logspace(-12, -3, 50)
quantile_grid = np.array([0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10])

# %% Scenario 1: Tight Spike (5% at x0)
# ============================================================================
# EXPECTED: Very tight spike should have epsilon threshold near machine precision
# EXPECTED: Quantile ratios should be << 1 (threshold grows slower than quantile)
# ============================================================================

print("=" * 80)
print("SCENARIO 1: TIGHT SPIKE (5% at x0)")
print("=" * 80)

x_spike = generate_with_x0_spike(
    n=10000, x0=5.0, L=0.0, U=10.0,
    spike_frac=0.05,
    seed=42
)
z_spike = compute_z(x_spike, x0=5.0, L=0.0, U=10.0)
z_spike_sorted = np.sort(z_spike)

result_spike = compare_single_vs_multi_curve(
    z_spike_sorted, grid_log, quantile_grid,
    log_space=True, true_threshold=None
)

print("\nRESULTS:")
print(f"  Single-curve elbow: {result_spike['single_curve_elbow']:.2e if result_spike['single_curve_elbow'] else None}")
print(f"  Multi-curve elbow: {result_spike['multi_curve_elbow']:.2e if result_spike['multi_curve_elbow'] else None}")

print("\n  Quantile ratios (should be << 1 for tight spike):")
for q, r in zip(quantile_grid, result_spike['quantile_ratios']):
    print(f"    q={q:.3f}: ratio={r:.3e}")

print("\nINTERPRETATION:")
if result_spike['multi_curve_elbow'] is not None:
    # Find the threshold at the elbow quantile
    elbow_threshold = np.interp(
        result_spike['multi_curve_elbow'],
        quantile_grid,
        result_spike['diagnostics']['threshold_at_quantile']
    )
    print(f"  ✓ Elbow detected at quantile {result_spike['multi_curve_elbow']:.4f}")
    print(f"    -> Corresponding z-threshold: {elbow_threshold:.2e}")
    print(f"  ✓ This is the estimated spike width in z-space")
else:
    print("  ✗ No elbow detected (unexpected for tight spike)")

# Check ratios
mean_ratio = np.nanmean(result_spike['quantile_ratios'])
if mean_ratio < 0.1:
    print(f"  ✓ Mean ratio {mean_ratio:.3e} << 1 confirms tight spike")
else:
    print(f"  ✗ Mean ratio {mean_ratio:.3e} not << 1 (unexpected)")

# %% Scenario 2: Signed Log-Normal (Broad, NOT a Spike)
# ============================================================================
# CRITICAL TEST: This has natural mass near z=0 but is BROAD
# EXPECTED: Should find weak/no elbow
# EXPECTED: Quantile ratios should be > 0.5 (not << 1 like spike)
# ============================================================================

print("\n\n" + "=" * 80)
print("SCENARIO 2: SIGNED LOG-NORMAL (BROAD, NOT A SPIKE)")
print("=" * 80)

# Generate signed log-normal: natural mass near zero but BROAD
x_lognorm_raw = generate_signed_lognormal(n=10000, mu=-2, sigma=1.5, seed=42)

# Normalize to [0, 1] range for easier handling
x_min, x_max = x_lognorm_raw.min(), x_lognorm_raw.max()
x_lognorm = (x_lognorm_raw - x_min) / (x_max - x_min)

# Use x0 = 0.5 (center of normalized range)
x0_lognorm = 0.5
z_lognorm = compute_z(x_lognorm, x0=x0_lognorm, L=0.0, U=1.0)
z_lognorm_sorted = np.sort(z_lognorm)

result_lognorm = compare_single_vs_multi_curve(
    z_lognorm_sorted, grid_log, quantile_grid,
    log_space=True, true_threshold=None
)

print("\nRESULTS:")
print(f"  Single-curve elbow: {result_lognorm['single_curve_elbow']:.2e if result_lognorm['single_curve_elbow'] else None}")
print(f"  Multi-curve elbow: {result_lognorm['multi_curve_elbow']:.2e if result_lognorm['multi_curve_elbow'] else None}")

print("\n  Quantile ratios (should be > 0.5 for broad distribution, not << 1):")
for q, r in zip(quantile_grid, result_lognorm['quantile_ratios']):
    print(f"    q={q:.3f}: ratio={r:.3e}")

print("\nINTERPRETATION:")
if result_lognorm['multi_curve_elbow'] is None:
    print("  ✓ No elbow detected - correct for broad distribution")
else:
    elbow_threshold = np.interp(
        result_lognorm['multi_curve_elbow'],
        quantile_grid,
        result_lognorm['diagnostics']['threshold_at_quantile']
    )
    print(f"  ! Elbow detected at quantile {result_lognorm['multi_curve_elbow']:.4f}")
    print(f"    -> Corresponding z-threshold: {elbow_threshold:.2e}")
    print("    This may indicate weak structure, but check ratios...")

# Check ratios - key diagnostic
mean_ratio = np.nanmean(result_lognorm['quantile_ratios'])
if mean_ratio > 0.5:
    print(f"  ✓ Mean ratio {mean_ratio:.3e} > 0.5 confirms BROAD distribution")
    print("    -> NOT a tight spike (correct - should not flag as stickiness)")
else:
    print(f"  ✗ Mean ratio {mean_ratio:.3e} < 0.5 (would be misclassified as spike!)")

# Additional diagnostic: Check mass distribution
mass_at_smallest_eps = result_lognorm['mass_curve'][0]
print(f"\n  Mass at smallest epsilon ({grid_log[0]:.2e}): {mass_at_smallest_eps:.4f}")
if mass_at_smallest_eps < 0.01:
    print("    ✓ Very little mass at tiny epsilon - confirms BROAD, not spike")
else:
    print("    ! Significant mass at tiny epsilon - may look spike-like")

# %% Scenario 3: Precision-Limited Spike (3% exact zeros)
# ============================================================================
# EXPECTED: Should detect very tight spike with epsilon near machine precision
# EXPECTED: Quantile ratios should be extremely small (<< 0.001)
# EXPECTED: Elbow should be at very small quantile (near 0.03)
# ============================================================================

print("\n\n" + "=" * 80)
print("SCENARIO 3: PRECISION-LIMITED SPIKE (3% exact at x0)")
print("=" * 80)

# Generate data where 3% of samples are EXACTLY at x0 (z=0)
np.random.seed(42)
n_total = 10000
spike_frac = 0.03
n_spike = int(n_total * spike_frac)
n_uniform = n_total - n_spike

# Generate uniform background
x_background = np.random.uniform(0.0, 10.0, size=n_uniform)

# Create exact zeros at x0
x0_precision = 5.0
x_spike_exact = np.full(n_spike, x0_precision)

# Combine
x_precision = np.concatenate([x_background, x_spike_exact])
np.random.shuffle(x_precision)

# Transform to z-space
z_precision = compute_z(x_precision, x0=x0_precision, L=0.0, U=10.0)
z_precision_sorted = np.sort(z_precision)

result_precision = compare_single_vs_multi_curve(
    z_precision_sorted, grid_log, quantile_grid,
    log_space=True, true_threshold=None
)

print("\nRESULTS:")
print(f"  Single-curve elbow: {result_precision['single_curve_elbow']:.2e if result_precision['single_curve_elbow'] else None}")
print(f"  Multi-curve elbow: {result_precision['multi_curve_elbow']:.2e if result_precision['multi_curve_elbow'] else None}")

print("\n  Quantile ratios (should be << 0.001 for precision-limited spike):")
for q, r in zip(quantile_grid, result_precision['quantile_ratios']):
    print(f"    q={q:.3f}: ratio={r:.3e}")

print("\nINTERPRETATION:")
if result_precision['multi_curve_elbow'] is not None:
    elbow_threshold = np.interp(
        result_precision['multi_curve_elbow'],
        quantile_grid,
        result_precision['diagnostics']['threshold_at_quantile']
    )
    print(f"  ✓ Elbow detected at quantile {result_precision['multi_curve_elbow']:.4f}")
    print(f"    -> Corresponding z-threshold: {elbow_threshold:.2e}")

    # Check if elbow quantile is near the spike fraction
    if abs(result_precision['multi_curve_elbow'] - spike_frac) < 0.02:
        print(f"  ✓ Elbow quantile ≈ spike fraction ({spike_frac:.2%})")
    else:
        print(f"  ! Elbow quantile differs from spike fraction ({spike_frac:.2%})")
else:
    print("  ✗ No elbow detected (unexpected for precision-limited spike)")

# Check ratios
mean_ratio = np.nanmean(result_precision['quantile_ratios'])
if mean_ratio < 0.001:
    print(f"  ✓ Mean ratio {mean_ratio:.3e} << 0.001 confirms VERY tight spike")
    print("    -> Spike width is near machine precision")
elif mean_ratio < 0.1:
    print(f"  ✓ Mean ratio {mean_ratio:.3e} << 1 confirms tight spike")
else:
    print(f"  ✗ Mean ratio {mean_ratio:.3e} not << 1 (unexpected)")

# Check exact zeros
n_exact_zeros = np.sum(z_precision == 0)
print(f"\n  Exact zeros in z-space: {n_exact_zeros} / {n_total} ({100*n_exact_zeros/n_total:.1f}%)")
if n_exact_zeros == n_spike:
    print("    ✓ All spike samples have z = 0 (perfect precision)")
else:
    print(f"    ! Expected {n_spike} exact zeros")

# %% Summary comparison across all scenarios
print("\n\n" + "=" * 80)
print("SUMMARY: COMPARISON ACROSS ALL SCENARIOS")
print("=" * 80)

scenarios = [
    ("Tight Spike (5%)", result_spike),
    ("Signed Log-Normal", result_lognorm),
    ("Precision Spike (3%)", result_precision)
]

print("\n{:<25} {:>15} {:>15} {:>15}".format(
    "Scenario", "Single Elbow", "Multi Elbow", "Mean Ratio"
))
print("-" * 72)

for name, result in scenarios:
    single = f"{result['single_curve_elbow']:.2e}" if result['single_curve_elbow'] else "None"
    multi = f"{result['multi_curve_elbow']:.2e}" if result['multi_curve_elbow'] else "None"
    ratio = f"{np.nanmean(result['quantile_ratios']):.3e}"
    print(f"{name:<25} {single:>15} {multi:>15} {ratio:>15}")

print("\nKEY INSIGHTS:")
print("  1. Tight spikes: Mean ratio << 1 (threshold grows slower than quantile)")
print("  2. Broad distributions: Mean ratio > 0.5 (more uniform spread)")
print("  3. Precision spikes: Mean ratio << 0.001 (essentially machine precision)")
print("  4. Multi-curve elbow identifies the quantile where structure changes")
print("\nThese diagnostics enable robust spike detection in log-space!")
print("=" * 80)

# %%
