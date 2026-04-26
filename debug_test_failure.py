"""Debug script to investigate test_multi_curve_detects_tight_pileup failure."""

import numpy as np
from fitqc.boundary import run_boundary_qc
from fitqc.config import BoundaryConfig

# Replicate test case exactly
rng = np.random.default_rng(42)
x_pileup = rng.uniform(0.0, 0.003, size=300)  # 3% tight pileup
x_bulk = rng.uniform(0.0, 1.0, size=9700)  # 97% uniform
x = np.concatenate([x_pileup, x_bulk])

config_new = BoundaryConfig(
    n_tols=45,
    grid_mode="progressive",
    quantile_grid=(0.005, 0.01, 0.02, 0.03, 0.05, 0.10),
    use_quantile_analysis=True,
)

result_new = run_boundary_qc(x, L=0.0, U=1.0, config=config_new)

print("=" * 80)
print("TEST CASE: test_multi_curve_detects_tight_pileup")
print("=" * 80)
print(f"\nData setup:")
print(f"  - Pileup samples: 300 in range [0.0, 0.003]  (3% of data, 0.3% of range)")
print(f"  - Bulk samples: 9700 in range [0.0, 1.0]")
print(f"  - Total: 10000 samples")
print(f"  - True pileup width: 0.003")

print(f"\nDetection results:")
print(f"  - Lower pileup detected: {result_new.lower_pileup_detected}")
print(f"  - Upper pileup detected: {result_new.upper_pileup_detected}")
print(f"  - t_lo_star: {result_new.t_lo_star}")
print(f"  - t_hi_star: {result_new.t_hi_star}")

print(f"\nTest expectation:")
print(f"  - Expected t_lo_star: 0.003 ± 0.002  (range: 0.001 to 0.005)")
print(f"  - Actual t_lo_star: {result_new.t_lo_star}")
print(f"  - Ratio (actual/expected): {result_new.t_lo_star / 0.003:.2f}x")

if result_new.t_lo_star < 0.001:
    print(f"  - ❌ FAILED: Detection is {0.001 / result_new.t_lo_star:.1f}x tighter than minimum expected")
elif result_new.t_lo_star > 0.005:
    print(f"  - ❌ FAILED: Detection is {result_new.t_lo_star / 0.005:.1f}x looser than maximum expected")
else:
    print(f"  - ✅ PASSED: Within expected range")

print(f"\nQuantile elbows:")
if result_new.quantile_elbows:
    for key, value in result_new.quantile_elbows.items():
        print(f"  - {key}: {value}")

print(f"\nLower mass curve statistics:")
if result_new.lower_mass_curve is not None:
    print(f"  - Min: {result_new.lower_mass_curve.min():.6f}")
    print(f"  - Max: {result_new.lower_mass_curve.max():.6f}")
    print(f"  - Mean: {result_new.lower_mass_curve.mean():.6f}")

print(f"\nTolerance grid:")
if result_new.tol_grid is not None:
    print(f"  - Length: {len(result_new.tol_grid)}")
    print(f"  - Min: {result_new.tol_grid.min():.6f}")
    print(f"  - Max: {result_new.tol_grid.max():.6f}")
    print(f"  - First 10 values: {result_new.tol_grid[:10]}")

print(f"\nAnalysis:")
print(f"  The algorithm detected a threshold of {result_new.t_lo_star:.6f}, which is")
print(f"  {result_new.t_lo_star/0.003*100:.1f}% of the true pileup width (0.003).")
print(f"")
print(f"  Possible causes:")
print(f"  1. Algorithm detects first significant deviation from uniform, not pileup width")
print(f"  2. Elbow detection is too sensitive (detects early transition)")
print(f"  3. Grid resolution causes detection at first grid point after t=0")
print(f"  4. Aggregation across quantiles picks minimum rather than median")

# Check actual distribution
u = (x - 0.0) / (1.0 - 0.0)
u_lower = u[u <= 0.5]
if len(u_lower) > 0:
    print(f"\nActual distribution check:")
    print(f"  - Samples in [0, 0.001]: {np.sum((x >= 0) & (x <= 0.001))}")
    print(f"  - Samples in [0, 0.002]: {np.sum((x >= 0) & (x <= 0.002))}")
    print(f"  - Samples in [0, 0.003]: {np.sum((x >= 0) & (x <= 0.003))}")
    print(f"  - Samples in [0, 0.005]: {np.sum((x >= 0) & (x <= 0.005))}")
    print(f"  - Samples in [0, 0.010]: {np.sum((x >= 0) & (x <= 0.010))}")
