"""Audit filtering implementation to verify correctness.

This script:
1. Loads test data and runs actual boundary detection
2. Compares filtering methods (x-space vs u-space)
3. Creates overplotted visualizations to inspect cuts
4. Verifies consistency between plot functions and algorithm
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from fitqc.boundary import run_boundary_qc, compute_u
from fitqc.config import BoundaryConfig

# Test with A_He first (user mentioned this one specifically)
data_dir = Path("tests/data")
dataset_name = "A_He"

print(f"{'='*80}")
print(f"AUDITING FILTERING FOR {dataset_name}")
print(f"{'='*80}\n")

# Load data
x = pd.read_parquet(data_dir / f"{dataset_name}_test_sample.parquet")["values"].values
with open(data_dir / f"{dataset_name}_test_metadata.json") as f:
    meta = json.load(f)

L = meta["L"]
U = meta["U"]

print(f"Dataset: {meta['name']}")
print(f"Bounds: L={L}, U={U}")
print(f"Total samples: {len(x):,}\n")

# Method 1: X-space filtering (what plot_bounds_filter_comparison does)
print("METHOD 1: X-space filtering (plot function)")
x_filtered_method1 = x[(x >= L) & (x <= U)]
n_below_L_method1 = np.sum(x < L)
n_above_U_method1 = np.sum(x > U)
n_filtered_method1 = len(x_filtered_method1)

print(f"  Filtered using: (x >= {L}) & (x <= {U})")
print(f"  Below L: {n_below_L_method1:,}")
print(f"  Above U: {n_above_U_method1:,}")
print(f"  Retained: {n_filtered_method1:,} ({n_filtered_method1/len(x)*100:.2f}%)")

# Method 2: U-space filtering (what boundary.py does)
print("\nMETHOD 2: U-space filtering (boundary.py algorithm)")
u = compute_u(x, L, U)
out_of_bounds_mask = (u < 0) | (u > 1)
n_out_of_bounds = np.sum(out_of_bounds_mask)
n_below_method2 = np.sum(u < 0)
n_above_method2 = np.sum(u > 1)
u_filtered = u[~out_of_bounds_mask]
x_filtered_method2 = x[~out_of_bounds_mask]
n_filtered_method2 = len(x_filtered_method2)

print(f"  Filtered using: (u >= 0) & (u <= 1)")
print(f"  Below L (u<0): {n_below_method2:,}")
print(f"  Above U (u>1): {n_above_method2:,}")
print(f"  Retained: {n_filtered_method2:,} ({n_filtered_method2/len(x)*100:.2f}%)")

# Compare methods
print("\nCOMPARISON:")
if n_filtered_method1 == n_filtered_method2:
    print(f"  ✓ Methods produce SAME number of filtered samples")
else:
    print(f"  ✗ Methods produce DIFFERENT numbers!")
    print(f"    Difference: {abs(n_filtered_method1 - n_filtered_method2):,} samples")

# Check if the actual values are the same
if np.array_equal(np.sort(x_filtered_method1), np.sort(x_filtered_method2)):
    print(f"  ✓ Filtered datasets are IDENTICAL")
else:
    print(f"  ✗ Filtered datasets are DIFFERENT!")

# Examine the actual boundary values
print(f"\nBOUNDARY VALUE ANALYSIS:")
print(f"  Raw data range: [{x.min():.6f}, {x.max():.6f}]")
print(f"  Expected bounds: [{L}, {U}]")

# Check for samples exactly at boundaries
at_L = np.sum(x == L)
at_U = np.sum(x == U)
print(f"  Samples exactly at L={L}: {at_L}")
print(f"  Samples exactly at U={U}: {at_U}")

# Check for edge cases in u-space
print(f"\nU-SPACE EDGE CASES:")
u_at_L = u[x == L] if at_L > 0 else np.array([])
u_at_U = u[x == U] if at_U > 0 else np.array([])
if len(u_at_L) > 0:
    print(f"  u values at x=L: {u_at_L[:5]}")  # Show first 5
if len(u_at_U) > 0:
    print(f"  u values at x=U: {u_at_U[:5]}")  # Show first 5

# Find the most extreme u values
u_min_idx = np.argmin(u)
u_max_idx = np.argmax(u)
print(f"  Minimum u: {u[u_min_idx]:.10f} (x={x[u_min_idx]:.6f})")
print(f"  Maximum u: {u[u_max_idx]:.10f} (x={x[u_max_idx]:.6f})")

# Run actual boundary detection to see what it does
print(f"\nRUNNING ACTUAL BOUNDARY DETECTION:")
config = BoundaryConfig()
result = run_boundary_qc(x, L, U, config)

print(f"  Lower pileup detected: {result.lower_pileup_detected}")
print(f"  Upper pileup detected: {result.upper_pileup_detected}")
if result.t_lo_star is not None:
    print(f"  Lower threshold: {result.t_lo_star:.6f}")
if result.t_hi_star is not None:
    print(f"  Upper threshold: {result.t_hi_star:.6f}")

# Create visualization with overplotted data
print(f"\nCREATING OVERPLOTTED VISUALIZATION...")

fig, axes = plt.subplots(3, 2, figsize=(14, 12))

# 1. Raw histogram with boundary lines
ax = axes[0, 0]
bins = np.linspace(x.min(), x.max(), 201)
ax.hist(x, bins=bins, alpha=0.5, color='blue', label='All data', edgecolor='black', linewidth=0.5)
ax.axvline(L, color='red', linestyle='--', linewidth=2, label=f'L={L}')
ax.axvline(U, color='red', linestyle='--', linewidth=2, label=f'U={U}')
ax.set_xlabel('x')
ax.set_ylabel('Count (log scale)')
ax.set_yscale('log')
ax.set_title(f'{dataset_name}: Raw Data with Bounds')
ax.legend()
ax.grid(True, alpha=0.3, which='both')

# 2. Overplotted: original vs filtered
ax = axes[0, 1]
ax.hist(x, bins=bins, alpha=0.4, color='blue', label='Original', edgecolor='none')
ax.hist(x_filtered_method1, bins=bins, alpha=0.6, color='green', label='Filtered (x-space)', edgecolor='none')
ax.axvline(L, color='red', linestyle='--', linewidth=1, alpha=0.7)
ax.axvline(U, color='red', linestyle='--', linewidth=1, alpha=0.7)
ax.set_xlabel('x')
ax.set_ylabel('Count (log scale)')
ax.set_yscale('log')
ax.set_title('Overplotted: Original vs Filtered')
ax.legend()
ax.grid(True, alpha=0.3, which='both')

# 3. Difference histogram (what was removed)
ax = axes[1, 0]
x_removed = x[~((x >= L) & (x <= U))]
if len(x_removed) > 0:
    ax.hist(x_removed, bins=bins, alpha=0.7, color='red', label='Removed', edgecolor='black', linewidth=0.5)
    ax.axvline(L, color='darkred', linestyle='--', linewidth=2)
    ax.axvline(U, color='darkred', linestyle='--', linewidth=2)
    ax.set_xlabel('x')
    ax.set_ylabel('Count')
    ax.set_title(f'Removed Samples (n={len(x_removed):,})')
    ax.legend()
    ax.grid(True, alpha=0.3)
else:
    ax.text(0.5, 0.5, 'No samples removed', ha='center', va='center', transform=ax.transAxes)
    ax.set_title('Removed Samples (n=0)')

# 4. U-space distribution
ax = axes[1, 1]
bins_u = np.linspace(min(u.min(), 0), max(u.max(), 1), 201)
ax.hist(u, bins=bins_u, alpha=0.5, color='purple', edgecolor='black', linewidth=0.5)
ax.axvline(0, color='red', linestyle='--', linewidth=2, label='u=0 (L)')
ax.axvline(1, color='red', linestyle='--', linewidth=2, label='u=1 (U)')
ax.axvspan(-0.1, 0, alpha=0.2, color='red', label='Out-of-bounds')
ax.axvspan(1, 1.1, alpha=0.2, color='red')
ax.set_xlabel('u = (x-L)/(U-L)')
ax.set_ylabel('Count (log scale)')
ax.set_yscale('log')
ax.set_title('U-Space Distribution')
ax.legend()
ax.grid(True, alpha=0.3, which='both')

# 5. U-space near lower boundary (zoomed)
ax = axes[2, 0]
u_zoom_lower = u[u < 0.1]
bins_u_zoom = np.linspace(min(u.min(), 0), 0.1, 201)
ax.hist(u_zoom_lower, bins=bins_u_zoom, alpha=0.7, color='darkgreen', edgecolor='black', linewidth=0.5)
ax.axvline(0, color='red', linestyle='--', linewidth=2, label='u=0 (L)')
if result.t_lo_star is not None:
    ax.axvline(result.t_lo_star, color='orange', linestyle=':', linewidth=2, label=f't*={result.t_lo_star:.4f}')
ax.set_xlabel('u = (x-L)/(U-L)')
ax.set_ylabel('Count (log scale)')
ax.set_yscale('log')
ax.set_title('U-Space Near Lower Boundary (u < 0.1)')
ax.legend()
ax.grid(True, alpha=0.3, which='both')

# 6. U-space near upper boundary (zoomed)
ax = axes[2, 1]
u_zoom_upper = u[u > 0.9]
bins_u_zoom_upper = np.linspace(0.9, max(u.max(), 1), 201)
if len(u_zoom_upper) > 0:
    ax.hist(u_zoom_upper, bins=bins_u_zoom_upper, alpha=0.7, color='darkred', edgecolor='black', linewidth=0.5)
    ax.axvline(1, color='red', linestyle='--', linewidth=2, label='u=1 (U)')
    if result.t_hi_star is not None:
        # For upper boundary, t_hi_star is in terms of distance from U
        # So u > 1 - t_hi_star indicates stickiness
        u_upper_threshold = 1 - result.t_hi_star
        ax.axvline(u_upper_threshold, color='orange', linestyle=':', linewidth=2,
                   label=f'1-t*={u_upper_threshold:.4f}')
    ax.set_xlabel('u = (x-L)/(U-L)')
    ax.set_ylabel('Count (log scale)')
    ax.set_yscale('log')
    ax.set_title('U-Space Near Upper Boundary (u > 0.9)')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both')
else:
    ax.text(0.5, 0.5, 'No samples in u > 0.9', ha='center', va='center', transform=ax.transAxes)
    ax.set_title('U-Space Near Upper Boundary (u > 0.9)')

plt.tight_layout()

# Save
output_path = Path(f"figures/{dataset_name}_filtering_audit.png")
output_path.parent.mkdir(exist_ok=True)
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"Saved: {output_path}")

output_path_hires = Path(f"figures/{dataset_name}_filtering_audit_hires.png")
plt.savefig(output_path_hires, dpi=300, bbox_inches='tight')
print(f"Saved: {output_path_hires}")

plt.close()

print(f"\n{'='*80}")
print(f"AUDIT COMPLETE")
print(f"{'='*80}")
