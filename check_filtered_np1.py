"""Check what remains in np1 data after filtering out-of-bounds samples."""

import json

import numpy as np
import pyarrow.parquet as pq

# Load np1 test data
table = pq.read_table("tests/data/np1_test_sample.parquet")
x = table.column("values").to_numpy()

# Load metadata
with open("tests/data/np1_test_metadata.json") as f:
    metadata = json.load(f)

L = metadata["L"]
U = metadata["U"]

# Filter to valid samples
valid_mask = (x >= L) & (x <= U)
x_filtered = x[valid_mask]

# Compute u-values for filtered data
u_filtered = (x_filtered - L) / (U - L)

print(f"Original data: {len(x)} samples")
print(f"Filtered data: {len(x_filtered)} samples ({len(x_filtered) / len(x) * 100:.2f}%)")
print()
print("Filtered data statistics:")
print(f"  Min: {x_filtered.min()}")
print(f"  Max: {x_filtered.max()}")
print(f"  Median: {np.median(x_filtered)}")
print()

# Check for concentration near lower boundary
print("U-space analysis of filtered data:")
for tol in [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 0.05]:
    count = np.sum(u_filtered < tol)
    frac = count / len(u_filtered)
    expected_frac = tol  # For uniform
    excess = frac / tol if tol > 0 else 0
    print(f"  u < {tol:8.6f}: {count:6d} samples ({frac:6.2%}), excess ratio: {excess:7.1f}x")

# Check samples very close to L
print(f"\nSamples near L={L}:")
for delta in [0.0, 0.001, 0.01, 0.1, 1.0]:
    count = np.sum((x_filtered >= L) & (x_filtered < L + delta))
    frac = count / len(x_filtered)
    print(f"  [{L:6.2f}, {L + delta:6.2f}): {count:6d} samples ({frac:6.2%})")
