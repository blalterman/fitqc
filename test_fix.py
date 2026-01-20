#!/usr/bin/env python
"""Test the fix for elbow detection on A_He data."""
import numpy as np
import pyarrow.parquet as pq
import json
from fitqc.boundary import run_boundary_qc
from fitqc.config import BoundaryConfig

# Load A_He data
with open('tests/data/A_He_test_metadata.json', 'r') as f:
    metadata = json.load(f)

table = pq.read_table('tests/data/A_He_test_sample.parquet')
x = table['values'].to_numpy()
L, U = metadata['L'], metadata['U']

print("="*80)
print("Testing Fixed Elbow Detection on A_He Data")
print("="*80)
print(f"\nData characteristics:")
print(f"  N samples: {len(x):,}")
print(f"  Exactly at L=0: {np.sum(x == 0):,} ({100*np.sum(x==0)/len(x):.3f}%)")
print(f"  Expected: lower_stickiness=True, upper_stickiness=False")

# Test with default config
print(f"\n{'='*80}")
print("Test 1: Default Config")
print("="*80)
config_default = BoundaryConfig(use_quantile_analysis=True, refine_transition=True)
result_default = run_boundary_qc(x, L=L, U=U, config=config_default)

print(f"\nResults:")
print(f"  Lower pileup detected: {result_default.lower_pileup_detected}")
print(f"  Upper pileup detected: {result_default.upper_pileup_detected}")
print(f"  t_lo_star: {result_default.t_lo_star}")
print(f"  t_hi_star: {result_default.t_hi_star}")

if result_default.lower_pileup_detected:
    print(f"  ✓ SUCCESS: Detected lower boundary pileup!")
else:
    print(f"  ✗ FAILED: Did not detect lower boundary pileup")

# Test with sensitive config
print(f"\n{'='*80}")
print("Test 2: Sensitive Config (lower threshold)")
print("="*80)
config_sensitive = BoundaryConfig(
    use_quantile_analysis=True,
    refine_transition=True,
    pileup_threshold=0.0002
)
result_sensitive = run_boundary_qc(x, L=L, U=U, config=config_sensitive)

print(f"\nResults:")
print(f"  Lower pileup detected: {result_sensitive.lower_pileup_detected}")
print(f"  Upper pileup detected: {result_sensitive.upper_pileup_detected}")
print(f"  t_lo_star: {result_sensitive.t_lo_star}")
print(f"  t_hi_star: {result_sensitive.t_hi_star}")

if result_sensitive.lower_pileup_detected:
    print(f"  ✓ SUCCESS: Detected lower boundary pileup!")
else:
    print(f"  ✗ FAILED: Did not detect lower boundary pileup")

# Show quantile elbows if available
if result_sensitive.quantile_elbows and 'lower' in result_sensitive.quantile_elbows:
    print(f"\n{'='*80}")
    print("Quantile Elbows (first 10, lower boundary)")
    print("="*80)
    lower_elbows = result_sensitive.quantile_elbows['lower']
    for i, (q, elbow) in enumerate(list(lower_elbows.items())[:10]):
        if elbow is not None:
            print(f"  q={q:.6f}: elbow at t={elbow:.6f}")
        else:
            print(f"  q={q:.6f}: elbow=None")
