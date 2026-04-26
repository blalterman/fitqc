#!/usr/bin/env python
"""Zoom plots for ab.a to locate the real interior x0.

Ground truth asserts interior=True with interior_locations=[0], but the
swefc calibration harness misses it. The ground-truth note says 'L and
x0 coincide at 0 - boundary and interior stickiness overlap. Internal
sticky point to be estimated from ab.a [0, 2.5] zoom plot.'

This script produces fine-binned histograms over several zoom ranges so
the user can pick the actual spike location.

Generated with Claude Code.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
H5 = REPO / "swefc.h5"
OUT = REPO / "figures" / "ab_a_interior_zoom.pdf"
COL = ("ab", "", "a")

ZOOMS = [
    ("full [0, 25]", 0.0, 25.0, 0.02),
    ("[0, 2.5]", 0.0, 2.5, 0.002),
    ("[0, 0.5]", 0.0, 0.5, 0.0005),
    ("[0, 0.1]", 0.0, 0.1, 0.0001),
    ("[0, 0.01]", 0.0, 0.01, 1e-5),
    ("[2, 8]", 2.0, 8.0, 0.01),  # check for secondary mode
]


def main() -> None:
    df = pd.read_hdf(H5, key="ppa12_apeq")
    x = df[COL].to_numpy(dtype=float)
    x = x[np.isfinite(x)]
    print(f"ab.a: n={x.size:,}  range=[{x.min():g}, {x.max():g}]")
    print(f"      n(x==0)={int((x == 0).sum()):,}")
    print(f"      n(x<1e-6)={int((np.abs(x) < 1e-6).sum()):,}")
    print(f"      n(x<1e-3)={int((np.abs(x) < 1e-3).sum()):,}")
    print(f"      n(x<0.01)={int((np.abs(x) < 0.01).sum()):,}")
    print(f"      n(x<0.1)={int((np.abs(x) < 0.1).sum()):,}")
    print(f"      n(x<1.0)={int((np.abs(x) < 1.0).sum()):,}")
    print(f"      n(x<2.5)={int((np.abs(x) < 2.5).sum()):,}")

    # Find candidate spike locations: bins with anomalously high counts
    # at coarse scale
    print("\nTop 20 densest bins on [0, 25] with 0.01 width:")
    edges = np.arange(0.0, 25.0001, 0.01)
    counts, _ = np.histogram(x, bins=edges)
    top = np.argsort(counts)[::-1][:20]
    for i in top:
        print(f"  x in [{edges[i]:.4f}, {edges[i + 1]:.4f}]  count={counts[i]:,}")

    fig, axes = plt.subplots(len(ZOOMS), 1, figsize=(11, 2.4 * len(ZOOMS)), constrained_layout=True)
    for ax, (label, lo, hi, bw) in zip(axes, ZOOMS, strict=True):
        mask = (x >= lo) & (x <= hi)
        vals = x[mask]
        edges = np.arange(lo, hi + bw, bw)
        ax.hist(vals, bins=edges, color="steelblue", histtype="step", linewidth=0.6)
        ax.set_yscale("log")
        ax.set_title(f"ab.a zoom {label}  (n={vals.size:,}, bw={bw:g})", fontsize=9)
        ax.set_xlabel("ab.a")
        ax.tick_params(axis="both", labelsize=7)
    fig.savefig(OUT, dpi=150)
    plt.close(fig)
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
