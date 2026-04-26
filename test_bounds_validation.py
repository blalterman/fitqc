"""Test the bounds validation logging in run_boundary_qc."""

import json
import logging
import sys

import pyarrow.parquet as pq

from fitqc.boundary import run_boundary_qc
from fitqc.config import BoundaryConfig

# Configure logging to show warnings
logging.basicConfig(
    level=logging.WARNING, format="%(levelname)s - %(name)s - %(message)s", stream=sys.stdout
)

# Load np1 test data
print("Loading np1 test data...")
table = pq.read_table("tests/data/np1_test_sample.parquet")
x = table.column("values").to_numpy()

# Load metadata
with open("tests/data/np1_test_metadata.json") as f:
    metadata = json.load(f)

L = metadata["L"]
U = metadata["U"]

print(f"\nParameter bounds: L={L}, U={U}")
print(f"Total samples: {len(x)}")
print(f"Min value: {x.min()}")
print(f"Max value: {x.max()}")
print(f"Samples at 0.0: {(x == 0.0).sum()}")
print(f"Samples below L: {(x < L).sum()}")
print(f"Samples above U: {(x > U).sum()}")

# Run boundary QC - should trigger warning
print("\n" + "=" * 70)
print("Running boundary QC with validation enabled...")
print("=" * 70 + "\n")

config = BoundaryConfig(
    use_quantile_analysis=True,
    refine_transition=True,
    grid_mode="progressive",
)

result = run_boundary_qc(x, L, U, config)

print("\nResults:")
print(f"  Lower pileup detected: {result.lower_pileup_detected}")
print(f"  Upper pileup detected: {result.upper_pileup_detected}")
print(f"  t_lo_star: {result.t_lo_star}")
print(f"  t_hi_star: {result.t_hi_star}")

print("\n✓ Test complete. The warning should have been logged above.")
