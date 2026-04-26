#!/usr/bin/env python
"""Prototype 3 tolerance-grid candidates for boundary detection.

Runs `run_boundary_qc` on each of the 12 PPA12 test datasets under each
candidate tolerance grid and compares `t_star` magnitudes against the
empirically-derived "true" pileup widths from
`dispatches/boundary-fn-diagnostics-2026-04-17.md`.

Candidates:
  - log: np.logspace(-7, -1, 61). Uniform log density over 7 decades.
  - hybrid: progressive (current) 0..0.05 + np.logspace(-7,-4,19) prepended.
  - piecewise: dense log 1e-7..1e-4 (20 pts) + linear 1e-4..0.05 (20 pts).

Analysis-only: monkey-patches `fitqc.boundary._build_tolerance_grid`, does
NOT modify production code. Output table lists (param, side, t_star,
delta_decades) for the 10 FN-diagnostic cases with known true widths.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

import fitqc.boundary as bmod
from fitqc import BoundaryConfig

# --------------------------------------------------------------------------
# Datasets

DATA_DIR = Path(__file__).parent.parent / "tests" / "data"
PARAMS = [
    "A_He",
    "e_dv_ap",
    "e_dv_pp",
    "np1",
    "np2",
    "vx",
    "vy",
    "vz",
    "w_const",
    "e_w_p1",
    "e_w_p2",
    "e_w_a",
]

# True widths from boundary-fn-diagnostics-2026-04-17.md ("True scale" col).
# These are the 10 cases where empirical pileup widths have been measured.
# (param, side, true_tol_normalized).
TRUE_WIDTHS = [
    ("e_dv_ap", "lower", 1e-3),
    ("vy", "lower", 1e-7),
    ("vy", "upper", 1e-7),
    ("vz", "lower", 1e-7),
    ("vz", "upper", 1e-7),
    ("e_w_p1", "upper", 1e-3),
    ("np1", "upper", 1e-7),
    ("np2", "upper", 1e-5),
    ("vx", "lower", 1e-7),
    ("e_w_p2", "upper", 1e-7),
]


def load_datasets():
    datasets = {}
    for name in PARAMS:
        vals = pq.read_table(DATA_DIR / f"{name}_test_sample.parquet")["values"].to_numpy()
        meta = json.loads((DATA_DIR / f"{name}_test_metadata.json").read_text())
        datasets[name] = (vals, meta["L"], meta["U"])
    return datasets


# --------------------------------------------------------------------------
# Candidate grid definitions


def grid_log():
    return np.logspace(-7, -1, 61)


def grid_hybrid():
    fine = np.logspace(-7, -4, 19)
    coarse = np.concatenate(
        [
            np.linspace(0.0000, 0.0010, 11),
            np.linspace(0.0010, 0.0050, 17)[1:],
            np.linspace(0.0050, 0.0200, 13)[1:],
            np.linspace(0.0200, 0.0500, 7)[1:],
        ]
    )
    return np.unique(np.concatenate([fine, coarse]))


def grid_piecewise():
    fine = np.logspace(-7, -4, 20)
    mid = np.linspace(1e-4, 0.05, 20)[1:]
    return np.unique(np.concatenate([fine, mid]))


def grid_progressive_plus_log_prefix():
    """Progressive grid, sparsely extended below 1e-4 with a few log points.
    Minimal perturbation to the existing progressive shape."""
    prefix = np.array([1e-7, 1e-6, 1e-5])
    coarse = np.concatenate(
        [
            np.linspace(0.0000, 0.0010, 11),
            np.linspace(0.0010, 0.0050, 17)[1:],
            np.linspace(0.0050, 0.0200, 13)[1:],
            np.linspace(0.0200, 0.0500, 7)[1:],
        ]
    )
    return np.unique(np.concatenate([prefix, coarse]))


CANDIDATES = {
    "log": grid_log,
    "hybrid": grid_hybrid,
    "piecewise": grid_piecewise,
    "prog+log-prefix": grid_progressive_plus_log_prefix,
}

# --------------------------------------------------------------------------
# Driver


def run_with_grid(grid_fn, datasets):
    orig = bmod._build_tolerance_grid
    grid = grid_fn()
    bmod._build_tolerance_grid = lambda cfg: grid
    try:
        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            grid_mode="progressive",
        )
        rows = {}
        for name in PARAMS:
            x, L, U = datasets[name]
            r = bmod.run_boundary_qc(x, L, U, config)
            rows[name] = {
                "t_lo_raw": r.t_lo_raw,
                "t_lo_star": r.t_lo_star,
                "t_hi_raw": r.t_hi_raw,
                "t_hi_star": r.t_hi_star,
                "lo_det": r.lower_pileup_detected,
                "hi_det": r.upper_pileup_detected,
            }
        return rows, len(grid)
    finally:
        bmod._build_tolerance_grid = orig


def delta_decades(t_star, true_tol):
    if t_star is None or t_star <= 0:
        return float("inf")
    return abs(np.log10(t_star) - np.log10(true_tol))


def main():
    print("Loading 12 PPA12 datasets...", flush=True)
    datasets = load_datasets()

    # Baseline (progressive mode) for reference
    baseline_rows, baseline_n = run_with_grid(
        lambda: np.concatenate(
            [
                np.linspace(0.0, 0.0010, 11),
                np.linspace(0.0010, 0.0050, 17)[1:],
                np.linspace(0.0050, 0.0200, 13)[1:],
                np.linspace(0.0200, 0.0500, 7)[1:],
            ]
        ),
        datasets,
    )

    candidates = {"baseline(progressive)": (baseline_rows, baseline_n)}
    for label, fn in CANDIDATES.items():
        print(f"Running candidate: {label} ...", flush=True)
        candidates[label] = run_with_grid(fn, datasets)

    # Detection invariance check
    print("\n=== Detection (lo_det, hi_det) — must all be (T, T) ===")
    header = "Param       " + "".join(f"{lbl:>20s}" for lbl in candidates)
    print(header)
    for name in PARAMS:
        row = f"{name:12s}"
        for _lbl, (rows, _) in candidates.items():
            r = rows[name]
            row += f"  {('T' if r['lo_det'] else 'F')},{'T' if r['hi_det'] else 'F'}".rjust(20)
        print(row)

    # t_star magnitudes
    print("\n=== t_star magnitudes (%.2e) ===")
    for side in ("lo", "hi"):
        print(f"\n  t_{side}_star:")
        print("Param       " + "".join(f"{lbl:>22s}" for lbl in candidates))
        for name in PARAMS:
            row = f"{name:12s}"
            key = f"t_{side}_star"
            for _lbl, (rows, _) in candidates.items():
                v = rows[name][key]
                if v is None:
                    row += "                  None"
                else:
                    row += f"  {v:20.6e}"
            print(row)

    # t_raw (primary-path result) to distinguish primary vs subgrid fallback
    print(
        "\n=== t_raw (primary-path, None=primary failed) — shows which cases fall through to subgrid fallback ==="
    )
    for side in ("lo", "hi"):
        print(f"\n  t_{side}_raw:")
        print("Param       " + "".join(f"{lbl:>22s}" for lbl in candidates))
        for name in PARAMS:
            row = f"{name:12s}"
            key = f"t_{side}_raw"
            for _lbl, (rows, _) in candidates.items():
                v = rows[name][key]
                if v is None:
                    row += "                  None"
                else:
                    row += f"  {v:20.6e}"
            print(row)

    # Delta vs true widths for known FN-diag cases
    print("\n=== |log10(t_star) - log10(true)| for 10 FN-diag cases ===")
    print("Param / Side / TrueW  " + "".join(f"{lbl:>18s}" for lbl in candidates))
    totals = {lbl: 0.0 for lbl in candidates}
    within_1_decade = {lbl: 0 for lbl in candidates}
    for param, side, true_w in TRUE_WIDTHS:
        row = f"{param:10s} {side:5s} {true_w:.0e} "
        for lbl, (rows, _) in candidates.items():
            tkey = f"t_{'lo' if side == 'lower' else 'hi'}_star"
            d = delta_decades(rows[param][tkey], true_w)
            if d == float("inf"):
                row += "               inf"
            else:
                row += f"  {d:16.2f}"
                totals[lbl] += d
                if d <= 1.0:
                    within_1_decade[lbl] += 1
        print(row)

    print("\n=== Summary ===")
    print(f"{'Candidate':<22s}  {'Gridsize':>8s}  {'TotalΔdec':>10s}  {'Within±1dec/10':>15s}")
    for lbl, (_, n) in candidates.items():
        print(f"{lbl:<22s}  {n:>8d}  {totals[lbl]:>10.2f}  {within_1_decade[lbl]:>15d}")


if __name__ == "__main__":
    main()
