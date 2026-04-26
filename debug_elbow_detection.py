"""Debug elbow detection in quantile curve."""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fitqc.boundary import compute_u, tail_mass
from fitqc.selection import select_elbow

# Replicate test case
rng = np.random.default_rng(42)
x_pileup = rng.uniform(0.0, 0.003, size=300)  # 3% tight pileup
x_bulk = rng.uniform(0.0, 1.0, size=9700)  # 97% uniform
x = np.concatenate([x_pileup, x_bulk])

# Compute u values
L, U = 0.0, 1.0
u = compute_u(x, L, U)
u_sorted = np.sort(u)

# Create tolerance grid (simple version for debugging)
tol_max = 0.05
n_tols = 45
tol_grid = np.linspace(0, tol_max, n_tols)

# Quantile grid from test
quantile_grid = np.array([0.005, 0.01, 0.02, 0.03, 0.05, 0.10])

# Compute mass curve
mass_curve = np.array([tail_mass(u_sorted, tol) for tol in tol_grid])

# For each quantile, find tolerance where mass = quantile
tol_at_quantile = np.interp(quantile_grid, mass_curve, tol_grid)

print("=" * 80)
print("ELBOW DETECTION DEBUG")
print("=" * 80)

print(f"\nQuantile grid: {quantile_grid}")
print(f"Tolerance at each quantile: {tol_at_quantile}")

print(f"\nData for elbow detection:")
print(f"  X-axis (quantile): {quantile_grid}")
print(f"  Y-axis (tolerance): {tol_at_quantile}")

# Plot the curve
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(quantile_grid, tol_at_quantile, 'o-', label='Quantile → Tolerance')
ax.axline((0, 0), slope=1, color='red', linestyle='--', alpha=0.5, label='Uniform (y=x)')
ax.set_xlabel('Quantile (fraction of samples)')
ax.set_ylabel('Tolerance (fraction of range)')
ax.set_title('Quantile vs Tolerance Curve (Pileup Detection)')
ax.legend()
ax.grid(True, alpha=0.3)
fig.savefig('/home/user/fitqc/debug_quantile_curve.png', dpi=150, bbox_inches='tight')
print(f"\nSaved plot to debug_quantile_curve.png")

# Detect elbow (convex, increasing)
print(f"\nAttempting elbow detection with select_elbow:")
print(f"  - curve='convex'")
print(f"  - direction='increasing'")

elbow_quantile = select_elbow(
    quantile_grid, tol_at_quantile, curve="convex", direction="increasing"
)

print(f"\nDetected elbow:")
print(f"  - elbow_quantile (x-coordinate): {elbow_quantile}")

if elbow_quantile is not None:
    # Convert to tolerance space
    elbow_tol = np.interp(elbow_quantile, quantile_grid, tol_at_quantile)
    print(f"  - elbow_tol (y-coordinate): {elbow_tol}")

    # Find where this is on the curve
    idx = np.where(np.isclose(quantile_grid, elbow_quantile))[0]
    if len(idx) > 0:
        print(f"  - Elbow is at quantile_grid[{idx[0]}] = {quantile_grid[idx[0]]}")
        print(f"  - Corresponding tol_at_quantile[{idx[0]}] = {tol_at_quantile[idx[0]]}")

    print(f"\n  Interpretation:")
    print(f"    The algorithm detected an elbow at quantile={elbow_quantile:.4f},")
    print(f"    which corresponds to tolerance={elbow_tol:.6f}.")
    print(f"    This means {elbow_quantile*100:.2f}% of samples are within")
    print(f"    {elbow_tol*100:.4f}% of the boundary.")
else:
    print(f"  - No elbow detected (returned None)")
    elbow_tol = None

# Show what we expect
print(f"\nExpected behavior:")
print(f"  - Pileup width: 0.003 (0.3% of range)")
print(f"  - Pileup fraction: 300/10000 = 3%")
print(f"  - Expected elbow around: quantile=0.03, tolerance=0.003")
print(f"  - Actual elbow: quantile={elbow_quantile}, tolerance={elbow_tol if elbow_quantile else 'None'}")

# Check if we're using the first grid point after 0
if elbow_tol is not None and elbow_tol < 0.001:
    print(f"\n⚠️  WARNING: Detected tolerance ({elbow_tol:.6f}) is very small!")
    print(f"   This is {elbow_tol/0.003*100:.1f}% of the true pileup width.")
    print(f"   Possible issues:")
    print(f"   1. Elbow detection is too sensitive (detects early transition)")
    print(f"   2. Quantile curve shape not well-suited for elbow detection")
    print(f"   3. Need different curve type or parameters")
