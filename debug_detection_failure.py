#!/usr/bin/env python
"""Debug why 1% delta function at L=0 is not being detected."""

import numpy as np

from fitqc.boundary import run_boundary_qc
from fitqc.config import BoundaryConfig

# Replicate exact test data
rng = np.random.default_rng(42)
n = 100000

x = np.concatenate(
    [
        np.zeros(int(0.01 * n)),  # 1000 samples exactly at L=0
        rng.uniform(0, 100, int(0.99 * n)),  # 99000 uniform
    ]
)

config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)

# Add debug prints to understand what's happening
print("=" * 80)
print("Debug: 1% Delta Function Detection")
print("=" * 80)
print(f"Exactly at L=0: {np.sum(x == 0)} ({100 * np.sum(x == 0) / len(x):.2f}%)")

result = run_boundary_qc(x, L=0, U=100, config=config)

print("\nResult:")
print(f"  lower_pileup_detected: {result.lower_pileup_detected}")
print(f"  t_lo_star: {result.t_lo_star}")

# Check quantile elbows
if result.quantile_elbows and "lower" in result.quantile_elbows:
    lower_elbows = result.quantile_elbows["lower"]
    print("\nQuantile elbows (first 20):")
    for _i, (q, elbow) in enumerate(list(lower_elbows.items())[:20]):
        print(f"  q={q:.6f}: elbow={elbow}")

    # Check how many are at 0
    elbows_list = list(lower_elbows.values())
    n_zero = sum(1 for e in elbows_list if e is not None and abs(e) < 1e-10)
    n_nonzero = sum(1 for e in elbows_list if e is not None and abs(e) >= 1e-10)
    n_none = sum(1 for e in elbows_list if e is None)

    print("\nElbow statistics:")
    print(f"  Elbows at t≈0: {n_zero}")
    print(f"  Elbows at t>0: {n_nonzero}")
    print(f"  Elbows = None: {n_none}")

    # Check median
    valid_elbows = [e for e in elbows_list if e is not None]
    if valid_elbows:
        median_elbow = np.median(valid_elbows)
        print(f"  Median of valid elbows: {median_elbow}")

# Check mass curve
print("\nMass curve (first 10 points):")
print(f"{'Tolerance':<12} {'Mass':<12} {'Expected':<12} {'Excess'}")
print("-" * 60)
for i in range(min(10, len(result.tol_grid))):
    t = result.tol_grid[i]
    m = result.lower_mass_curve[i]
    expected = t
    excess = m / t if t > 0 else np.inf
    print(f"{t:<12.6f} {m:<12.6f} {expected:<12.6f} {excess:>8.2f}x")

# Test the check_excess_mass logic manually
print("\nManual check_excess_mass simulation:")
excess_ratio = config.excess_ratio
pileup_threshold = config.pileup_threshold
print(f"  excess_ratio={excess_ratio}, pileup_threshold={pileup_threshold}")

# Assume t_star = 0 (from median of elbows)
t_star = 0.0
if t_star < 1e-10:
    print(f"  t_star={t_star} < 1e-10: TRUE (delta function case)")
    for idx in range(1, min(5, len(result.tol_grid))):
        t_check = result.tol_grid[idx]
        mass_check = result.lower_mass_curve[idx]
        if t_check > 1e-10:
            ratio = mass_check / (t_check * excess_ratio)
            passes = mass_check > t_check * excess_ratio
            print(
                f"    idx={idx}: t_check={t_check:.6f}, mass={mass_check:.6f}, ratio={ratio:.2f}, passes={passes}"
            )
            if passes:
                print(f"      => Should return (True, {t_check})")
                break
