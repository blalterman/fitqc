"""Test the accuracy of single-curve threshold detection on known scenarios."""

import numpy as np
from fitqc.boundary import run_boundary_qc
from fitqc.config import BoundaryConfig

print("=" * 80)
print("TESTING SINGLE-CURVE ACCURACY ON EXISTING TEST SCENARIOS")
print("=" * 80)

# Scenario 1: From test_boundary.py - 5% in first 1% of range
print("\nScenario 1: 5% of data in [0, 0.1] out of [0, 10] range")
print("-" * 80)
rng = np.random.default_rng(42)
x1 = rng.uniform(0, 10, size=10000)
x1[:500] = rng.uniform(0, 0.1, size=500)  # 5% near lower

result1 = run_boundary_qc(x1, L=0.0, U=10.0, config=BoundaryConfig())

true_threshold_norm = 0.1 / 10.0  # 0.01 in normalized space
print(f"True pileup region: [0, 0.1]")
print(f"True threshold (normalized): {true_threshold_norm:.4f}")
print(f"Detected t_lo_star: {result1.t_lo_star:.4f}")
print(f"Absolute error: {abs(result1.t_lo_star - true_threshold_norm):.4f}")
print(
    f"Relative error: {100 * abs(result1.t_lo_star - true_threshold_norm) / true_threshold_norm:.1f}%"
)
print(f"Pileup detected: {result1.lower_pileup_detected}")

# Scenario 2: Tighter pileup - 3% in 0.3%
print("\n\nScenario 2: 3% of data in [0, 0.03] out of [0, 10] range")
print("-" * 80)
rng = np.random.default_rng(42)
x2 = rng.uniform(0, 10, size=10000)
x2[:300] = rng.uniform(0, 0.03, size=300)

result2 = run_boundary_qc(x2, L=0.0, U=10.0, config=BoundaryConfig())

true_threshold_norm2 = 0.03 / 10.0  # 0.003
print(f"True pileup region: [0, 0.03]")
print(f"True threshold (normalized): {true_threshold_norm2:.4f}")
print(f"Detected t_lo_star: {result2.t_lo_star:.4f}")
print(f"Absolute error: {abs(result2.t_lo_star - true_threshold_norm2):.4f}")
print(
    f"Relative error: {100 * abs(result2.t_lo_star - true_threshold_norm2) / true_threshold_norm2:.1f}%"
)
print(f"Pileup detected: {result2.lower_pileup_detected}")

# Scenario 3: Broader pileup - 10% in 5%
print("\n\nScenario 3: 10% of data in [0, 0.5] out of [0, 10] range")
print("-" * 80)
rng = np.random.default_rng(42)
x3 = rng.uniform(0, 10, size=10000)
x3[:1000] = rng.uniform(0, 0.5, size=1000)

result3 = run_boundary_qc(x3, L=0.0, U=10.0, config=BoundaryConfig())

true_threshold_norm3 = 0.5 / 10.0  # 0.05
print(f"True pileup region: [0, 0.5]")
print(f"True threshold (normalized): {true_threshold_norm3:.4f}")
print(f"Detected t_lo_star: {result3.t_lo_star:.4f}")
print(f"Absolute error: {abs(result3.t_lo_star - true_threshold_norm3):.4f}")
print(
    f"Relative error: {100 * abs(result3.t_lo_star - true_threshold_norm3) / true_threshold_norm3:.1f}%"
)
print(f"Pileup detected: {result3.lower_pileup_detected}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("If relative errors are > 50%, the threshold detection is unreliable.")
print("This would explain why multi-curve also failed - the concept of")
print("'threshold at end of pileup' may not match what elbow detection finds.")
print("=" * 80)
