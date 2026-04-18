#!/usr/bin/env python
"""Per-parameter overview PDF for the full swefc.h5 dataset.

Swefc analog of ``plot_all_ppa12_diagnostics.py``. Produces a single
multi-page PDF at ``figures/swefc_overview.pdf`` with one
``plot_parameter_overview`` page per ground-truth entry, using the full
``swefc.h5`` / ``ppa12_apeq`` data (not the parquet subsets).

Reads the twelve parameters and their (L, U, x0, interior_locations,
lower/upper/interior) from ``dispatches/ground_truth_swefc.json``. For
entries with multiple interior locations (e.g. ``e.w.a`` at 0 and -25),
emits one page per location with the interior detector re-run at that
location.

Does not modify ``src/fitqc/``; driver only.

Generated with Claude Code.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from fitqc import (  # noqa: E402
    BoundaryConfig,
    InteriorConfig,
    PlotConfig,
    plot_parameter_overview,
    run_boundary_qc,
    run_interior_qc,
)

H5 = REPO / "swefc.h5"
H5_KEY = "ppa12_apeq"
TRUTH = REPO / "dispatches" / "ground_truth_swefc.json"
OUT_PDF = REPO / "figures" / "swefc_overview.pdf"

# grid_mode="progressive_log" diverges from the harness
# (analyze_swefc_calibration.py uses "progressive"). The overview matches
# plot_all_ppa12_diagnostics.py so the visual convention parallels the
# existing diagnostic. Whether harness and overview should share a
# grid_mode is open in dispatch-detector-tuning-swefc-2026-04-18.md (O2).
BOUNDARY_CFG = BoundaryConfig(
    use_quantile_analysis=True,
    refine_transition=True,
    grid_mode="progressive_log",
)
INTERIOR_CFG = InteriorConfig(use_quantile_analysis=True)
PLOT_CFG = PlotConfig()


def _classify(detected: bool, expected: bool) -> str:
    if expected and detected:
        return "TP"
    if expected and not detected:
        return "FN"
    if not expected and detected:
        return "FP"
    return "TN"


def _tp_fn_status(
    entry: dict,
    lower_detected: bool,
    upper_detected: bool,
    interior_detected: bool | None,
) -> str:
    parts = [
        f"lower: {_classify(lower_detected, bool(entry['lower']))}",
        f"upper: {_classify(upper_detected, bool(entry['upper']))}",
    ]
    if interior_detected is not None:
        parts.append(f"interior: {_classify(interior_detected, bool(entry['interior']))}")
    return " | ".join(parts)


def process(df: pd.DataFrame, entry: dict, pdf: PdfPages) -> None:
    name = entry["parameter"]
    col = tuple(entry["column_tuple"])
    L = float(entry["L"])
    U = float(entry["U"])
    x0 = entry.get("x0")
    locations = [float(v) for v in entry.get("interior_locations", [])]

    t0 = time.time()
    x_raw = df[col].to_numpy(dtype=float)
    x = x_raw[np.isfinite(x_raw)]
    n_dropped = int(x_raw.size - x.size)

    b_res = run_boundary_qc(x, L, U, BOUNDARY_CFG)

    # Primary interior location selection.
    #
    # Ground truth distinguishes `x0` (optimizer initial guess — pipeline
    # metadata) from `interior_locations` (empirical spike centers from
    # visual inspection). They usually coincide, but not always: ab.a has
    # x0=0 (pipeline) while the interior spike is at x=1; e.w.a has x0=0
    # but two spikes at 0 and -25. For the *primary* overview page, use
    # the first empirical interior_location when one is asserted, so the
    # page shows the actual interior spike rather than the pipeline x0.
    # Fall back to x0 only when interior_locations is empty.
    primary_loc: float | None
    if locations:
        primary_loc = locations[0]
    elif x0 is not None:
        primary_loc = float(x0)
    else:
        primary_loc = None

    interior_primary = None
    if primary_loc is not None:
        interior_primary = run_interior_qc(x, primary_loc, L, U, INTERIOR_CFG)

    status = _tp_fn_status(
        entry,
        b_res.lower_pileup_detected,
        b_res.upper_pileup_detected,
        None if primary_loc is None else bool(interior_primary.spike_detected),
    )

    print(
        f"  {name:20s} n={x.size:>9d} dropped={n_dropped:>6d} {status}  ({time.time() - t0:.1f}s)"
    )

    fig = plot_parameter_overview(
        param_name=name,
        x=x,
        x0=primary_loc,
        L=L,
        U=U,
        interior_result=interior_primary,
        boundary_result=b_res,
        config=PLOT_CFG,
        tp_fn_status=status,
    )
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)

    # Secondary interior-location pages: any asserted location beyond
    # the primary gets its own page so the reader can see both spikes.
    for loc in locations:
        if primary_loc is not None and loc == primary_loc:
            continue
        i_secondary = run_interior_qc(x, loc, L, U, INTERIOR_CFG)
        status2 = _tp_fn_status(
            entry,
            b_res.lower_pileup_detected,
            b_res.upper_pileup_detected,
            bool(i_secondary.spike_detected),
        )
        fig = plot_parameter_overview(
            param_name=f"{name} (x0={loc:g})",
            x=x,
            x0=loc,
            L=L,
            U=U,
            interior_result=i_secondary,
            boundary_result=b_res,
            config=PLOT_CFG,
            tp_fn_status=status2,
        )
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)
        print(f"    + secondary page x0={loc:g} interior={i_secondary.spike_detected}")


def main() -> int:
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    if not H5.exists():
        print(f"missing {H5}", file=sys.stderr)
        return 2
    truth = json.loads(TRUTH.read_text())["parameters"]

    t0 = time.time()
    print(f"Loading {H5} / {H5_KEY} ...")
    df = pd.read_hdf(H5, key=H5_KEY)
    print(f"  rows: {len(df):,}")

    print(f"Writing {OUT_PDF.relative_to(REPO)} ...")
    with PdfPages(OUT_PDF) as pdf:
        for entry in truth:
            process(df, entry, pdf)

    print(f"\nDone in {time.time() - t0:.1f}s -> {OUT_PDF}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
