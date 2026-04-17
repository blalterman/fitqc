#!/usr/bin/env python
"""Per-parameter diagnostic plots for ALL 12 PPA12 datasets.

Wraps generate_quantile_diagnostics.py's plotting with the full dataset
list, so we get the 7-figure suite for every parameter under the current
(post-fix) detection logic. Results land in figures/<param>/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fitqc import (
    BoundaryConfig,
    InteriorConfig,
    PlotConfig,
    plot_boundary_diagnostics,
    plot_ecdf_tolerance_overlays,
    plot_histogram_tolerance_overlays,
    plot_interior_diagnostics,
    plot_quantile_elbow_overlay,
    plot_quantile_spacing_overlays,
    run_boundary_qc,
    run_interior_qc,
)

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "figures"
OUT.mkdir(exist_ok=True)

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

boundary_config = BoundaryConfig(
    use_quantile_analysis=True,
    refine_transition=True,
    grid_mode="progressive",
)
plot_config = PlotConfig()
tols = np.array([0.0, 0.005, 0.01, 0.02, 0.03, 0.05])


def process(name: str) -> None:
    print(f"=== {name} ===")
    parquet = REPO / "tests" / "data" / f"{name}_test_sample.parquet"
    meta_file = REPO / "tests" / "data" / f"{name}_test_metadata.json"
    x = pq.read_table(parquet).column("values").to_numpy()
    with open(meta_file) as f:
        meta = json.load(f)

    L = meta["L"]
    U = meta["U"]
    x0 = meta.get("x0")

    range_width = U - L
    if range_width > 100:
        bins = 500
    elif range_width > 50:
        bins = 300
    elif range_width > 10:
        bins = 200
    else:
        bins = 100

    ds_out = OUT / name
    ds_out.mkdir(parents=True, exist_ok=True)

    boundary_result = run_boundary_qc(x, L, U, boundary_config)
    print(
        f"  t_lo_raw={boundary_result.t_lo_raw}  t_lo_star={boundary_result.t_lo_star}  "
        f"lo_det={boundary_result.lower_pileup_detected}"
    )
    print(
        f"  t_hi_raw={boundary_result.t_hi_raw}  t_hi_star={boundary_result.t_hi_star}  "
        f"hi_det={boundary_result.upper_pileup_detected}"
    )

    interior_result = None
    if x0 is not None:
        interior_result = run_interior_qc(x, x0, L, U, InteriorConfig(use_quantile_analysis=True))

    saved = []

    if interior_result is not None:
        fig = plot_interior_diagnostics(interior_result, plot_config)
        p = ds_out / f"{name}_interior_diagnostics.png"
        fig.savefig(p, bbox_inches="tight")
        saved.append(p)

    fig = plot_boundary_diagnostics(boundary_result, plot_config)
    p = ds_out / f"{name}_boundary_diagnostics.png"
    fig.savefig(p, bbox_inches="tight")
    saved.append(p)

    if interior_result is not None:
        fig = plot_quantile_elbow_overlay(interior_result, plot_config)
        p = ds_out / f"{name}_interior_elbows.png"
        fig.savefig(p, bbox_inches="tight")
        saved.append(p)

    fig = plot_quantile_elbow_overlay(boundary_result, plot_config)
    p = ds_out / f"{name}_boundary_elbows.png"
    fig.savefig(p, bbox_inches="tight")
    saved.append(p)

    fig = plot_histogram_tolerance_overlays(x=x, L=L, U=U, tols=tols, bins=bins, config=plot_config)
    p = ds_out / f"{name}_histogram_overlays.png"
    fig.savefig(p, bbox_inches="tight")
    saved.append(p)

    u = (x - L) / (U - L)
    fig = plot_ecdf_tolerance_overlays(u=u, tols=tols, side="both", config=plot_config)
    p = ds_out / f"{name}_ecdf_overlays.png"
    fig.savefig(p, bbox_inches="tight")
    saved.append(p)

    x_sorted = np.sort(x)
    fig = plot_quantile_spacing_overlays(
        x_sorted=x_sorted,
        L=L,
        U=U,
        tols=tols,
        q_max=0.15,
        n_quantiles=100,
        config=plot_config,
    )
    p = ds_out / f"{name}_spacing_overlays.png"
    fig.savefig(p, bbox_inches="tight")
    saved.append(p)

    for s in saved:
        print(f"  saved {s.relative_to(REPO)}")


def main() -> int:
    for name in PARAMS:
        process(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
