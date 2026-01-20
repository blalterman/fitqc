"""Analyze all PPA12 test datasets to validate metadata and identify patterns."""

import json
from pathlib import Path
import numpy as np
import pandas as pd

data_dir = Path("tests/data")

# All datasets
datasets = [
    "A_He", "e_dv_ap", "e_dv_pp", "np1", "np2",
    "vx", "vy", "vz", "w_const",
    "e_w_p1", "e_w_p2", "e_w_a",
]

results = []

for name in datasets:
    # Load data
    parquet_path = data_dir / f"{name}_test_sample.parquet"
    meta_path = data_dir / f"{name}_test_metadata.json"

    x = pd.read_parquet(parquet_path)["values"].values
    with open(meta_path) as f:
        meta = json.load(f)

    L = meta["L"]
    U = meta["U"]
    x0 = meta["x0"]
    expected = meta["fitqc_test"]

    # Compute u-space
    u = (x - L) / (U - L)

    # Boundary analysis
    at_lower = np.sum(np.abs(u) < 1e-10)
    at_upper = np.sum(np.abs(u - 1) < 1e-10)
    below_lower = np.sum(u < 0)
    above_upper = np.sum(u > 1)

    # Interior analysis (if x0 exists)
    if x0 is not None:
        z = np.abs(x - x0) / (U - L)
        at_x0 = np.sum(z < 1e-10)
        near_x0_001 = np.sum(z < 0.001)
    else:
        at_x0 = 0
        near_x0_001 = 0

    # Proximity to boundaries
    near_lower_1e6 = np.sum((u >= 0) & (u < 1e-6))
    near_lower_1e3 = np.sum((u >= 0) & (u < 1e-3))
    near_lower_1e2 = np.sum((u >= 0) & (u < 1e-2))

    near_upper_1e6 = np.sum((u <= 1) & (u > 1 - 1e-6))
    near_upper_1e3 = np.sum((u <= 1) & (u > 1 - 1e-3))
    near_upper_1e2 = np.sum((u <= 1) & (u > 1 - 1e-2))

    results.append({
        "name": name,
        "n": len(x),
        "L": L,
        "U": U,
        "x0": x0 if x0 is not None else "null",
        # Out of bounds
        "below_L": below_lower,
        "above_U": above_upper,
        # Lower boundary
        "at_L": at_lower,
        "near_L_1e6": near_lower_1e6,
        "near_L_1e3": near_lower_1e3,
        "near_L_1e2": near_lower_1e2,
        "pct_L_1e2": f"{100 * near_lower_1e2 / len(x):.2f}%",
        "exp_lower": expected["expected_lower_stickiness"],
        # Upper boundary
        "at_U": at_upper,
        "near_U_1e6": near_upper_1e6,
        "near_U_1e3": near_upper_1e3,
        "near_U_1e2": near_upper_1e2,
        "pct_U_1e2": f"{100 * near_upper_1e2 / len(x):.2f}%",
        "exp_upper": expected["expected_upper_stickiness"],
        # Interior
        "at_x0": at_x0,
        "near_x0": near_x0_001,
        "pct_x0": f"{100 * near_x0_001 / len(x):.2f}%" if x0 is not None else "N/A",
        "exp_interior": expected["expected_interior_stickiness"],
    })

# Print summary table
print("=" * 140)
print("PPA12 TEST DATASET ANALYSIS")
print("=" * 140)
print()

# Table 1: Dataset overview
print("DATASET OVERVIEW")
print("-" * 140)
print(f"{'Dataset':<12} {'n':>10} {'L':>10} {'U':>10} {'x0':>10} {'OOB (below,above)':>20}")
print("-" * 140)
for r in results:
    print(f"{r['name']:<12} {r['n']:>10,} {r['L']:>10} {r['U']:>10} {str(r['x0']):>10} ({r['below_L']:>6},{r['above_U']:>6})")
print()

# Table 2: Lower boundary characteristics
print("LOWER BOUNDARY CHARACTERISTICS")
print("-" * 140)
print(f"{'Dataset':<12} {'at_L':>8} {'u<1e-6':>8} {'u<1e-3':>8} {'u<1e-2':>8} {'%':>8} {'Expected':>10}")
print("-" * 140)
for r in results:
    exp_mark = "YES" if r["exp_lower"] else "NO"
    print(f"{r['name']:<12} {r['at_L']:>8} {r['near_L_1e6']:>8} {r['near_L_1e3']:>8} {r['near_L_1e2']:>8} {r['pct_L_1e2']:>8} {exp_mark:>10}")
print()

# Table 3: Upper boundary characteristics
print("UPPER BOUNDARY CHARACTERISTICS")
print("-" * 140)
print(f"{'Dataset':<12} {'at_U':>8} {'u>1-1e-6':>10} {'u>1-1e-3':>10} {'u>1-1e-2':>10} {'%':>8} {'Expected':>10}")
print("-" * 140)
for r in results:
    exp_mark = "YES" if r["exp_upper"] else "NO"
    print(f"{r['name']:<12} {r['at_U']:>8} {r['near_U_1e6']:>10} {r['near_U_1e3']:>10} {r['near_U_1e2']:>10} {r['pct_U_1e2']:>8} {exp_mark:>10}")
print()

# Table 4: Interior characteristics
print("INTERIOR (x0) CHARACTERISTICS")
print("-" * 140)
print(f"{'Dataset':<12} {'x0':>10} {'at_x0':>8} {'z<1e-3':>8} {'%':>8} {'Expected':>10}")
print("-" * 140)
for r in results:
    exp_mark = "YES" if r["exp_interior"] else "NO"
    print(f"{r['name']:<12} {str(r['x0']):>10} {r['at_x0']:>8} {r['near_x0']:>8} {r['pct_x0']:>8} {exp_mark:>10}")
print()

# Categorization
print("DATASET CATEGORIZATION BY STICKINESS PATTERNS")
print("-" * 120)

categories = {
    "Bilateral boundary + interior": [],
    "Bilateral boundary only": [],
    "Lower boundary + interior": [],
    "Upper boundary + interior": [],
    "Upper boundary only": [],
    "Interior only": [],
    "No stickiness (negative controls)": [],
    "Data quality issues": [],
}

for r in results:
    exp = {
        "lower": r["exp_lower"],
        "upper": r["exp_upper"],
        "interior": r["exp_interior"],
    }
    has_oob = r["below_L"] > 0 or r["above_U"] > 0

    if has_oob:
        categories["Data quality issues"].append(f"{r['name']} (OOB: {r['below_L']}+{r['above_U']})")
    elif exp["lower"] and exp["upper"] and exp["interior"]:
        categories["Bilateral boundary + interior"].append(f"{r['name']} (L:{r['pct_L_1e2']}, U:{r['pct_U_1e2']}, x0:{r['pct_x0']})")
    elif exp["lower"] and exp["upper"]:
        categories["Bilateral boundary only"].append(f"{r['name']} (L:{r['pct_L_1e2']}, U:{r['pct_U_1e2']})")
    elif exp["lower"] and exp["interior"]:
        categories["Lower boundary + interior"].append(f"{r['name']} (L:{r['pct_L_1e2']}, x0:{r['pct_x0']})")
    elif exp["upper"] and exp["interior"]:
        categories["Upper boundary + interior"].append(f"{r['name']} (U:{r['pct_U_1e2']}, x0:{r['pct_x0']})")
    elif exp["upper"]:
        categories["Upper boundary only"].append(f"{r['name']} (U:{r['pct_U_1e2']})")
    elif exp["interior"]:
        categories["Interior only"].append(f"{r['name']} (x0:{r['pct_x0']})")
    else:
        categories["No stickiness (negative controls)"].append(r["name"])

for category, datasets in categories.items():
    if datasets:
        print(f"\n{category}:")
        for ds in datasets:
            print(f"  - {ds}")

print()
print("=" * 120)
