#!/usr/bin/env python
"""Deep dive on the 10 boundary FNs.

For each FN, compute:
- Mass at very fine tolerances (well below the current quantile_grid floor 0.0005)
  to check whether there's a sub-grid pileup the Kneedle can't see.
- Mass curve shape near the boundary so we can tell pileup vs anti-pileup.
- For Group 1 (t_raw exists, mass < t*1.5): the actual mass/uniform ratio.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyze_overrides import CONFIG, load_datasets

from fitqc.boundary import compute_u, run_boundary_qc, tail_mass

# (parameter, side) FN list verified against override_review_results.md baseline
FNS = [
    ("e_dv_ap", "lower"),
    ("vy", "lower"),
    ("vy", "upper"),
    ("vz", "lower"),
    ("vz", "upper"),
    ("e_w_p1", "upper"),
    ("np1", "upper"),
    ("np2", "upper"),
    ("vx", "lower"),
    ("e_w_p2", "upper"),
]

FINE_TOLS = [
    1e-7,
    1e-6,
    1e-5,
    1e-4,
    3e-4,
    5e-4,
    1e-3,
    3e-3,
    5e-3,
    1e-2,
    3e-2,
    5e-2,
    1e-1,
]


def fine_tail_mass_lower(values, L, U, tol):
    u = compute_u(values, L, U)
    u = u[(u >= 0) & (u <= 1)]
    u_sorted = np.sort(u)
    return tail_mass(u_sorted, tol)


def fine_tail_mass_upper(values, L, U, tol):
    u = compute_u(values, L, U)
    u = u[(u >= 0) & (u <= 1)]
    u_sorted = np.sort(u)
    # Upper-side: P(u > 1-tol) computed via P(1-u < tol) where 1-u is reversed.
    # Equivalent: 1 - tail_mass on (1 - reversed(u_sorted)).
    upper_u = np.sort(1.0 - u_sorted)
    return tail_mass(upper_u, tol)


def main() -> int:
    datasets = load_datasets()

    print("# Deep FN diagnostics\n")
    for name, side in FNS:
        ds = datasets[name]
        result = run_boundary_qc(ds["values"], L=ds["L"], U=ds["U"], config=CONFIG)
        if side == "lower":
            t_raw = result.t_lo_raw
            t_star = result.t_lo_star
            det = result.lower_pileup_detected

            def fine_mass(t, ds=ds):
                return fine_tail_mass_lower(ds["values"], ds["L"], ds["U"], t)
        else:
            t_raw = result.t_hi_raw
            t_star = result.t_hi_star
            det = result.upper_pileup_detected

            def fine_mass(t, ds=ds):
                return fine_tail_mass_upper(ds["values"], ds["L"], ds["U"], t)

        print(f"## {name} {side}")
        print(f"- t_raw = {t_raw}, t_star = {t_star}, det = {det}")
        print(f"- L = {ds['L']}, U = {ds['U']}, n = {len(ds['values'])}")
        print("- fine mass(tol):")
        for tol in FINE_TOLS:
            m = fine_mass(tol)
            ratio = m / tol if tol > 0 else float("inf")
            note = ""
            if ratio >= 1.5:
                note = "  *** excess (mass/tol >= 1.5)"
            print(f"    tol={tol:.0e}  mass={m:.6f}  ratio={ratio:6.2f}{note}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
