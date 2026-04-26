#!/usr/bin/env python
"""Multipanel histogram diagnostic for swefc.h5 / ppa12_apeq fit parameters.

One row per quantity. Three columns per row:
    col 1 - linear x, full data
    col 2 - log x, x > 0 subset (log-spaced bins)
    col 3 - log |x|, x < 0 subset (log-spaced bins)

Bin width per panel: 0.1 * min(FD_width, Doane_width) computed on the data
actually being binned (log10-transformed for cols 2 and 3). _err columns are
quantile-clipped to [0.1%, 99.9%] before binning.

Generated with Claude Code.
"""

from __future__ import annotations

import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

REPO = Path(__file__).resolve().parent.parent
H5 = REPO / "swefc.h5"
OUT_DIR = REPO / "figures"
OUT_DIR.mkdir(exist_ok=True)
OUT_PDF = OUT_DIR / "swefc_fit_param_histograms.pdf"

MAX_BINS = 200_000

BASE_PARAMS = [
    ("v_param.x.p1", ("v_param", "x", "p1"), False),
    ("v_param.y.p1", ("v_param", "y", "p1"), False),
    ("v_param.z.p1", ("v_param", "z", "p1"), False),
    ("w.const", ("w", "const", ""), False),
    ("n_param.p1", ("n_param", "", "p1"), False),
    ("n_param.p2", ("n_param", "", "p2"), False),
    ("e.w.p1", ("e", "w", "p1"), False),
    ("e.w.p2", ("e", "w", "p2"), False),
    ("e.w.a", ("e", "w", "a"), False),
    ("e.dv.pp", ("e", "dv", "pp"), False),
    ("e.dv.ap", ("e", "dv", "ap"), False),
    ("ab.a", ("ab", "", "a"), False),
]

ERR_PARAMS = [
    ("v_err.x.p1", ("v_err", "x", "p1"), True),
    ("v_err.y.p1", ("v_err", "y", "p1"), True),
    ("v_err.z.p1", ("v_err", "z", "p1"), True),
    ("w_err.const", ("w_err", "const", ""), True),
    ("n_err.p1", ("n_err", "", "p1"), True),
    ("n_err.p2", ("n_err", "", "p2"), True),
    ("e_err.w.p1", ("e_err", "w", "p1"), True),
    ("e_err.w.p2", ("e_err", "w", "p2"), True),
    ("e_err.w.a", ("e_err", "w", "a"), True),
    ("e_err.dv.pp", ("e_err", "dv", "pp"), True),
    ("e_err.dv.ap", ("e_err", "dv", "ap"), True),
    ("ab_err.a", ("ab_err", "", "a"), True),
]

B_FIELD = [
    ("b.x", ("b", "x", ""), False),
    ("b.y", ("b", "y", ""), False),
    ("b.z", ("b", "z", ""), False),
]


def _target_width(values: np.ndarray) -> float | None:
    """0.1 * min(FD width, Doane width); None if degenerate."""
    if values.size < 2 or np.unique(values).size < 2:
        return None
    try:
        fd = np.histogram_bin_edges(values, bins="fd")
        doane = np.histogram_bin_edges(values, bins="doane")
    except ValueError:
        return None
    widths = []
    if len(fd) > 1:
        widths.append(float(fd[1] - fd[0]))
    if len(doane) > 1:
        widths.append(float(doane[1] - doane[0]))
    widths = [w for w in widths if w > 0]
    if not widths:
        return None
    return 0.1 * min(widths)


def _edges(lo: float, hi: float, bin_width: float, *, label: str) -> tuple[np.ndarray, int, bool]:
    """Return (edges, n_bins_used, was_capped)."""
    span = hi - lo
    if span <= 0 or bin_width <= 0:
        return np.array([]), 0, False
    n = int(np.ceil(span / bin_width))
    capped = False
    if n > MAX_BINS:
        print(f"    WARN: {label}: {n} bins requested, capping at {MAX_BINS}")
        n = MAX_BINS
        capped = True
    # np.linspace keeps the grid on a clean [lo, hi] range irrespective of
    # floating-point drift that np.arange would accumulate for large n.
    return np.linspace(lo, hi, n + 1), n, capped


def _draw_hist_line(ax, values: np.ndarray, edges: np.ndarray) -> None:
    """Compute histogram with np.histogram and plot as a steps-mid line.

    Zero-count bins are masked to NaN so they render as gaps on a log y-axis
    rather than clipping to -inf.
    """
    counts, _ = np.histogram(values, bins=edges)
    centers = 0.5 * (edges[:-1] + edges[1:])
    y = counts.astype(float)
    y[y == 0] = np.nan
    ax.plot(centers, y, drawstyle="steps-mid", color="steelblue", linewidth=0.6)
    ax.set_yscale("log")
    ax.tick_params(axis="both", labelsize=6)


def _hist_linear(ax, values: np.ndarray, row_label: str) -> int:
    if values.size == 0:
        _empty_panel(ax, "no data")
        return 0
    bw = _target_width(values)
    if bw is None:
        _empty_panel(ax, "no bin width")
        return 0
    edges, n, _ = _edges(float(values.min()), float(values.max()), bw, label=f"{row_label} linear")
    if edges.size == 0:
        _empty_panel(ax, "degenerate range")
        return 0
    _draw_hist_line(ax, values, edges)
    return n


def _hist_log(ax, positive_values: np.ndarray, row_label: str, *, side: str) -> int:
    """Log-spaced bins over strictly-positive values."""
    empty_msg = "no x > 0" if side == "pos" else "no x < 0"
    if positive_values.size == 0:
        _empty_panel(ax, empty_msg)
        return 0
    positive_values = positive_values[positive_values > 0]
    if positive_values.size == 0:
        _empty_panel(ax, empty_msg)
        return 0
    log_v = np.log10(positive_values)
    bw_log = _target_width(log_v)
    if bw_log is None:
        _empty_panel(ax, "no bin width")
        return 0
    log_edges, n, _ = _edges(
        float(log_v.min()), float(log_v.max()), bw_log, label=f"{row_label} log-{side}"
    )
    if log_edges.size == 0:
        _empty_panel(ax, "degenerate range")
        return 0
    edges = 10.0**log_edges
    _draw_hist_line(ax, positive_values, edges)
    ax.set_xscale("log")
    return n


def _empty_panel(ax, msg: str) -> None:
    ax.text(
        0.5, 0.5, msg, ha="center", va="center", transform=ax.transAxes, fontsize=8, color="gray"
    )
    ax.set_xticks([])
    ax.set_yticks([])


def _render_row(axes, row_label: str, series: pd.Series, is_err: bool) -> str:
    ax_lin, ax_pos, ax_neg = axes
    v = series.to_numpy(dtype=float)
    v = v[np.isfinite(v)]
    n_finite = v.size

    clip_note = ""
    if is_err and n_finite > 0:
        lo_q, hi_q = np.quantile(v, [0.001, 0.999])
        before = v.size
        v = v[(v >= lo_q) & (v <= hi_q)]
        clip_note = f" clip=[{lo_q:.4g},{hi_q:.4g}] drop={before - v.size}"

    n_lin = _hist_linear(ax_lin, v, row_label)
    n_pos = _hist_log(ax_pos, v[v > 0], row_label, side="pos")
    n_neg = _hist_log(ax_neg, -v[v < 0], row_label, side="neg")

    ax_lin.set_ylabel(row_label, fontsize=7, rotation=0, labelpad=45, ha="right", va="center")

    return (
        f"  {row_label:20s} n_finite={n_finite:>9d}{clip_note}"
        f"  bins: lin={n_lin} pos={n_pos} neg={n_neg}"
    )


def main() -> None:
    t0 = time.time()
    print(f"Loading {H5} ...")
    df = pd.read_hdf(H5, key="ppa12_apeq")
    print(f"  rows: {len(df):,}")

    chisq = df[("chisq", "", "")].to_numpy(dtype=float)
    dof = df[("dof", "", "")].to_numpy(dtype=float)
    n_dof0 = int((dof == 0).sum())
    n_dofneg = int((dof < 0).sum())
    print(f"  dof == 0: {n_dof0:,}  dof < 0: {n_dofneg:,}  (dof <= 0 dropped from chisq/dof)")
    mask = dof > 0
    chisq_over_dof = chisq[mask] / dof[mask]

    quantities: list[tuple[str, pd.Series, bool]] = []
    for lbl, col, is_err in BASE_PARAMS:
        quantities.append((lbl, df[col], is_err))
    for lbl, col, is_err in ERR_PARAMS:
        quantities.append((lbl, df[col], is_err))
    quantities.append(("chisq", pd.Series(chisq), False))
    quantities.append(("dof", pd.Series(dof), False))
    quantities.append(("chisq/dof", pd.Series(chisq_over_dof), False))
    for lbl, col, is_err in B_FIELD:
        quantities.append((lbl, df[col], is_err))

    n_rows = len(quantities)
    print(f"  quantities: {n_rows}")

    fig_h = 1.8 * n_rows
    fig, axes = plt.subplots(n_rows, 3, figsize=(13, fig_h), constrained_layout=True)
    axes[0, 0].set_title("linear x", fontsize=9)
    axes[0, 1].set_title("log x  (x > 0)", fontsize=9)
    axes[0, 2].set_title("log |x|  (x < 0)", fontsize=9)

    print("\nPer-quantity summary:")
    for i, (lbl, ser, is_err) in enumerate(quantities):
        line = _render_row(axes[i], lbl, ser, is_err)
        print(line)

    fig.suptitle("swefc.h5 / ppa12_apeq  fit parameter distributions", fontsize=11)

    print(f"\nWriting {OUT_PDF} ...")
    with PdfPages(OUT_PDF) as pdf:
        pdf.savefig(fig, dpi=150)
    plt.close(fig)
    print(f"Done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
