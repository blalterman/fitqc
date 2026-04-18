#!/usr/bin/env python
"""Probe two hypotheses the prototype_grid_candidates.py run left open:

H1: The tolerance grid needs higher log-density than 10/decade.
    Test `log_dense` = np.logspace(-7, -1, 121) (20/decade).

H2: The quantile_grid floor (5e-4) is above the fractional mass of some
    real pileups (np2 lower 3e-5, np1 5.5e-5, vx lower 8e-5), so Kneedle
    cannot see them regardless of tolerance grid. Test extending
    `quantile_grid` down to 1e-5 while keeping baseline progressive.

For each of the 12 PPA12 datasets, run run_boundary_qc and record
(t_lo_star, t_hi_star, lo_det, hi_det).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

import fitqc.boundary as bmod
from fitqc import BoundaryConfig

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


def load_datasets():
    ds = {}
    for p in PARAMS:
        v = pq.read_table(DATA_DIR / f"{p}_test_sample.parquet")["values"].to_numpy()
        m = json.loads((DATA_DIR / f"{p}_test_metadata.json").read_text())
        ds[p] = (v, m["L"], m["U"])
    return ds


def run(config, datasets, grid_fn=None):
    """Run run_boundary_qc on all 12; optionally monkey-patch tol grid."""
    if grid_fn is not None:
        orig = bmod._build_tolerance_grid
        grid = grid_fn()
        bmod._build_tolerance_grid = lambda cfg: grid
    try:
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
        return rows
    finally:
        if grid_fn is not None:
            bmod._build_tolerance_grid = orig


def baseline_progressive_grid():
    return np.concatenate(
        [
            np.linspace(0.0000, 0.0010, 11),
            np.linspace(0.0010, 0.0050, 17)[1:],
            np.linspace(0.0050, 0.0200, 13)[1:],
            np.linspace(0.0200, 0.0500, 7)[1:],
        ]
    )


def log_dense_grid():
    return np.logspace(-7, -1, 121)  # 20/decade over 6 decades


# Baseline quantile grid (default production)
Q_BASELINE = (
    0.0005,
    0.001,
    0.0015,
    0.002,
    0.0025,
    0.003,
    0.004,
    0.005,
    0.007,
    0.01,
    0.011,
    0.012,
    0.013,
    0.015,
    0.017,
    0.02,
    0.025,
    0.03,
    0.04,
    0.05,
    0.06,
    0.08,
    0.10,
    0.15,
    0.20,
    0.25,
)

# Quantile grid extended down to 1e-5 (covers np2 3e-5, np1 5.5e-5, vx 8e-5)
Q_EXTENDED = (
    1e-5,
    3e-5,
    1e-4,
    3e-4,
    *Q_BASELINE,
)


def main():
    datasets = load_datasets()

    configs = {
        "base (prog + Q_BASE)": (
            BoundaryConfig(
                use_quantile_analysis=True,
                refine_transition=True,
                grid_mode="progressive",
                quantile_grid=Q_BASELINE,
            ),
            None,
        ),
        "log_dense (20/dec) + Q_BASE": (
            BoundaryConfig(
                use_quantile_analysis=True,
                refine_transition=True,
                grid_mode="progressive",
                quantile_grid=Q_BASELINE,
            ),
            log_dense_grid,
        ),
        "prog + Q_EXTENDED": (
            BoundaryConfig(
                use_quantile_analysis=True,
                refine_transition=True,
                grid_mode="progressive",
                quantile_grid=Q_EXTENDED,
            ),
            None,
        ),
        "log (10/dec) + Q_EXTENDED": (
            BoundaryConfig(
                use_quantile_analysis=True,
                refine_transition=True,
                grid_mode="progressive",
                quantile_grid=Q_EXTENDED,
            ),
            lambda: np.logspace(-7, -1, 61),
        ),
    }

    results = {}
    for label, (cfg, grid_fn) in configs.items():
        print(f"Running: {label} ...", flush=True)
        results[label] = run(cfg, datasets, grid_fn)

    # Detection table
    print("\n=== Detection (lo,hi) — hard constraint: all (T,T) ===")
    print(f"{'Param':12s}" + "".join(f"{lbl:>30s}" for lbl in results))
    for p in PARAMS:
        row = f"{p:12s}"
        for lbl in results:
            r = results[lbl][p]
            tag = f"{'T' if r['lo_det'] else 'F'},{'T' if r['hi_det'] else 'F'}"
            row += f"{tag:>30s}"
        print(row)

    # t_star magnitudes
    print("\n=== t_lo_star ===")
    print(f"{'Param':12s}" + "".join(f"{lbl:>30s}" for lbl in results))
    for p in PARAMS:
        row = f"{p:12s}"
        for lbl in results:
            v = results[lbl][p]["t_lo_star"]
            row += f"{('None' if v is None else f'{v:.3e}'):>30s}"
        print(row)
    print("\n=== t_hi_star ===")
    print(f"{'Param':12s}" + "".join(f"{lbl:>30s}" for lbl in results))
    for p in PARAMS:
        row = f"{p:12s}"
        for lbl in results:
            v = results[lbl][p]["t_hi_star"]
            row += f"{('None' if v is None else f'{v:.3e}'):>30s}"
        print(row)

    # t_raw (primary-path)
    print("\n=== t_lo_raw (primary only; None=primary failed, falls to subgrid) ===")
    print(f"{'Param':12s}" + "".join(f"{lbl:>30s}" for lbl in results))
    for p in PARAMS:
        row = f"{p:12s}"
        for lbl in results:
            v = results[lbl][p]["t_lo_raw"]
            row += f"{('None' if v is None else f'{v:.3e}'):>30s}"
        print(row)
    print("\n=== t_hi_raw ===")
    print(f"{'Param':12s}" + "".join(f"{lbl:>30s}" for lbl in results))
    for p in PARAMS:
        row = f"{p:12s}"
        for lbl in results:
            v = results[lbl][p]["t_hi_raw"]
            row += f"{('None' if v is None else f'{v:.3e}'):>30s}"
        print(row)


if __name__ == "__main__":
    main()
