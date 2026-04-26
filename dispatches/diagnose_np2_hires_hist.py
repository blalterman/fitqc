#!/usr/bin/env python
"""High-resolution histograms of np2 for interior FP verification.

``diagnose_interior_12.py`` reports np2 as a suspected algorithmic FP:
detector flags a spike at x0=0 with ``eps_star=1e-12`` (the grid floor),
but ``ground_truth_validation.csv`` says no interior stickiness is
visible in np2/np1 ratio plots.

This script produces a 4-panel figure zooming progressively into z~=0 so
the user can visually determine whether a real ultra-narrow spike
exists or whether the detection is a numeric-precision artifact. It
also prints sample-count statistics for |x| below several thresholds.

Output: ``figures/np2/np2_interior_hires.png`` + stdout stats.

Usage:
    python dispatches/diagnose_np2_hires_hist.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fitqc.config import InteriorConfig
from fitqc.interior import run_interior_qc

REPO = Path(__file__).resolve().parent.parent
PARAM = "np2"
X0 = 0.0  # assumed reference; np2 metadata has x0=null but CSV x0=0
OUT_PNG = REPO / "figures" / PARAM / f"{PARAM}_interior_hires.png"


def main() -> int:
    parquet = REPO / "tests" / "data" / f"{PARAM}_test_sample.parquet"
    meta_path = REPO / "tests" / "data" / f"{PARAM}_test_metadata.json"
    x = pq.read_table(parquet).column("values").to_numpy()
    with open(meta_path) as f:
        meta = json.load(f)
    L = float(meta["L"])
    U = float(meta["U"])

    max_dist = max(X0 - L, U - X0)
    z = np.abs(x - X0) / max_dist

    result = run_interior_qc(x, X0, L, U, InteriorConfig())

    print(f"=== {PARAM} | x0={X0} | L={L} U={U} max_dist={max_dist} ===")
    print(f"n_samples = {len(x)}")
    print(f"min |x-x0| = {np.min(np.abs(x - X0)):.6g}")
    print(f"max |x-x0| = {np.max(np.abs(x - X0)):.6g}")
    for thresh in (1e-6, 1e-4, 1e-2, 1e-1):
        n = int(np.sum(np.abs(x - X0) < thresh))
        print(f"  |x-x0| < {thresh:g}: {n} samples ({100 * n / len(x):.4f}%)")
    print(
        f"detector: spike_detected={result.spike_detected}, "
        f"spike_z_loc={result.spike_z_loc}, eps_star={result.eps_star}"
    )

    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # Panel (0,0): full z-range, default-resolution histogram
    ax = axes[0, 0]
    ax.hist(z, bins=500, color="steelblue", edgecolor="none")
    ax.set_title(f"{PARAM}: full z-range (500 bins)")
    ax.set_xlabel("z = |x - x0| / max_dist")
    ax.set_ylabel("counts")
    if result.spike_z_loc is not None:
        ax.axvline(
            result.spike_z_loc, color="red", lw=1, label=f"spike_z_loc={result.spike_z_loc:.3g}"
        )
        ax.legend()

    # Panel (0,1): zoom to z <= 0.1, 2000 bins, linear y
    ax = axes[0, 1]
    mask = z <= 0.1
    ax.hist(z[mask], bins=2000, range=(0, 0.1), color="steelblue", edgecolor="none")
    ax.set_title(f"{PARAM}: z <= 0.1 zoom (2000 bins, linear y)")
    ax.set_xlabel("z")
    ax.set_ylabel("counts")
    if result.spike_z_loc is not None:
        ax.axvline(result.spike_z_loc, color="red", lw=1)
    if result.eps_star is not None:
        ax.axvline(
            result.eps_star, color="orange", lw=1, ls="--", label=f"eps_star={result.eps_star:.2g}"
        )
        ax.legend()

    # Panel (1,0): same zoom, log y
    ax = axes[1, 0]
    ax.hist(z[mask], bins=2000, range=(0, 0.1), color="steelblue", edgecolor="none")
    ax.set_yscale("log")
    ax.set_title(f"{PARAM}: z <= 0.1 zoom (2000 bins, log y)")
    ax.set_xlabel("z")
    ax.set_ylabel("counts (log)")
    if result.spike_z_loc is not None:
        ax.axvline(result.spike_z_loc, color="red", lw=1)
    if result.eps_star is not None:
        ax.axvline(result.eps_star, color="orange", lw=1, ls="--")

    # Panel (1,1): ultra-zoom z <= 0.01, 2000 bins, log y
    ax = axes[1, 1]
    mask2 = z <= 0.01
    ax.hist(z[mask2], bins=2000, range=(0, 0.01), color="steelblue", edgecolor="none")
    ax.set_yscale("log")
    ax.set_title(f"{PARAM}: z <= 0.01 ultra-zoom (2000 bins, log y)")
    ax.set_xlabel("z")
    ax.set_ylabel("counts (log)")
    if result.spike_z_loc is not None and result.spike_z_loc <= 0.01:
        ax.axvline(result.spike_z_loc, color="red", lw=1)

    fig.suptitle(
        f"{PARAM} interior histogram resolution sweep "
        f"(detector: spike={result.spike_detected}, z_loc={result.spike_z_loc}, "
        f"eps_star={result.eps_star})"
    )
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(OUT_PNG, bbox_inches="tight", dpi=120)
    plt.close(fig)

    print(f"\nwrote {OUT_PNG.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
