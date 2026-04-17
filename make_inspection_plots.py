#!/usr/bin/env python
"""Generate boundary inspection histograms and ground truth CSV.

Produces:
  dispatches/boundary_inspection.pdf  — multi-page PDF, 2 pages per parameter
  dispatches/ground_truth_validation.csv — empty template for manual annotation

Each parameter gets:
  Page 1: Linear-x histograms (top: linear-y, bottom: log-y)
  Page 2: Log-x histograms (top: linear-y, bottom: log-y), split by sign
"""

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyarrow.parquet as pq
from matplotlib.backends.backend_pdf import PdfPages

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
DATA_DIR = Path(__file__).parent / "tests" / "data"
OUT_DIR = Path(__file__).parent / "dispatches"

LOG_X_MIN = 1e-5  # Clip log-x values below this


def load_dataset(name):
    values = pq.read_table(DATA_DIR / f"{name}_test_sample.parquet")["values"].to_numpy()
    with open(DATA_DIR / f"{name}_test_metadata.json") as f:
        meta = json.load(f)
    return values, meta


def boundary_counts(x, L, U, x0):
    """Compute sample counts at and near boundaries."""
    at_L = int(np.sum(x == L))
    at_U = int(np.sum(x == U))
    below_L = int(np.sum(x < L))
    above_U = int(np.sum(x > U))
    rng = U - L
    near_L_1pct = int(np.sum((x >= L) & (x < L + 0.01 * rng)))
    near_U_1pct = int(np.sum((x > U - 0.01 * rng) & (x <= U)))
    at_x0 = int(np.sum(x == x0)) if x0 is not None else None
    return {
        "at_L": at_L,
        "at_U": at_U,
        "below_L": below_L,
        "above_U": above_U,
        "near_L_1pct": near_L_1pct,
        "near_U_1pct": near_U_1pct,
        "at_x0": at_x0,
    }


def _stats_text(counts):
    c = counts
    stats = (
        f"at L: {c['at_L']:,}   near L (1%): {c['near_L_1pct']:,}   "
        f"below L: {c['below_L']:,}\n"
        f"at U: {c['at_U']:,}   near U (1%): {c['near_U_1pct']:,}   "
        f"above U: {c['above_U']:,}"
    )
    if c["at_x0"] is not None:
        stats += f"\nat x0: {c['at_x0']:,}"
    return stats


def _add_markers(ax, L, U, x0, use_abs=False):
    """Add vertical lines for L, U, x0 behind histogram data."""

    def v(val):
        return abs(val) if use_abs else val

    if L is not None:
        lv = v(L)
        if lv > 0 or not use_abs:
            ax.axvline(lv, color="red", ls="--", lw=1.5, label=f"L={L}", zorder=0)
    if U is not None:
        uv = v(U)
        if uv > 0 or not use_abs:
            ax.axvline(uv, color="darkred", ls="--", lw=1.5, label=f"U={U}", zorder=0)
    if x0 is not None:
        xv = v(x0)
        if xv > 0 or not use_abs:
            ax.axvline(xv, color="orange", ls="--", lw=1.5, label=f"x0={x0}", zorder=0)


def page_linear_x(pdf, name, x, meta, counts):
    """Page 1: linear-x, two panels (linear-y on top, log-y on bottom)."""
    L, U, x0 = meta["L"], meta["U"], meta.get("x0")
    n_bins = min(1000, max(300, len(x) // 100))
    stats = _stats_text(counts)

    fig, (ax_lin, ax_log) = plt.subplots(2, 1, figsize=(11, 8.5), sharex=True)

    for ax, yscale in [(ax_lin, "linear"), (ax_log, "log")]:
        _add_markers(ax, L, U, x0)
        ax.hist(x, bins=n_bins, color="steelblue", edgecolor="none", alpha=0.8)
        if yscale == "log":
            ax.set_yscale("log")
        ax.set_ylabel(f"Count ({yscale} y)")
        ax.legend(loc="upper right", fontsize=8)

    ax_log.set_xlabel("Parameter value")
    fig.suptitle(f"{name} — linear x (n={len(x):,})\n{stats}", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    pdf.savefig(fig)
    plt.close(fig)


def page_log_x(pdf, name, x, meta, counts):
    """Page 2: log-x, two panels (linear-y on top, log-y on bottom), split by sign."""
    L, U, x0 = meta["L"], meta["U"], meta.get("x0")

    x_pos = x[x > 0]
    x_neg = x[x < 0]
    n_zero = int(np.sum(x == 0))
    has_pos = len(x_pos) > 0
    has_neg = len(x_neg) > 0

    if has_pos and has_neg:
        fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
        (ax_neg_lin, ax_pos_lin) = axes[0]
        (ax_neg_log, ax_pos_log) = axes[1]

        for ax_neg, yscale in [(ax_neg_lin, "linear"), (ax_neg_log, "log")]:
            _hist_log_x(ax_neg, np.abs(x_neg))
            _add_signed_markers(ax_neg, L, U, x0, negative=True)
            ax_neg.set_title(f"x < 0 (|x|, n={len(x_neg):,})", fontsize=9)
            ax_neg.set_ylabel(f"Count ({yscale} y)", fontsize=8)
            if yscale == "log":
                ax_neg.set_yscale("log")
            ax_neg.legend(loc="upper right", fontsize=7)

        for ax_pos, yscale in [(ax_pos_lin, "linear"), (ax_pos_log, "log")]:
            _hist_log_x(ax_pos, x_pos)
            _add_signed_markers(ax_pos, L, U, x0, negative=False)
            ax_pos.set_title(f"x > 0 (n={len(x_pos):,})", fontsize=9)
            ax_pos.set_ylabel(f"Count ({yscale} y)", fontsize=8)
            if yscale == "log":
                ax_pos.set_yscale("log")
            ax_pos.legend(loc="upper right", fontsize=7)

        ax_neg_log.set_xlabel("|x| (log scale)")
        ax_pos_log.set_xlabel("x (log scale)")

    elif has_pos:
        fig, (ax_lin, ax_log) = plt.subplots(2, 1, figsize=(11, 8.5))
        for ax, yscale in [(ax_lin, "linear"), (ax_log, "log")]:
            _hist_log_x(ax, x_pos)
            _add_markers(
                ax,
                L if L > 0 else None,
                U if U > 0 else None,
                x0 if (x0 is not None and x0 > 0) else None,
            )
            ax.set_ylabel(f"Count ({yscale} y)")
            if yscale == "log":
                ax.set_yscale("log")
            ax.legend(loc="upper right", fontsize=8)
        ax_log.set_xlabel("x (log scale)")

    elif has_neg:
        fig, (ax_lin, ax_log) = plt.subplots(2, 1, figsize=(11, 8.5))
        for ax, yscale in [(ax_lin, "linear"), (ax_log, "log")]:
            _hist_log_x(ax, np.abs(x_neg))
            for label, val in [("L", L), ("U", U)]:
                if val is not None and val < 0:
                    ax.axvline(
                        abs(val),
                        color="red",
                        ls="--",
                        lw=1.5,
                        label=f"|{label}|={abs(val)}",
                        zorder=0,
                    )
            ax.set_ylabel(f"Count ({yscale} y)")
            if yscale == "log":
                ax.set_yscale("log")
            ax.legend(loc="upper right", fontsize=8)
        ax_log.set_xlabel("|x| (log scale)")

    else:
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.text(
            0.5,
            0.5,
            f"{name}: all values are zero ({n_zero:,})",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=14,
        )

    title = f"{name} — log x"
    if n_zero > 0:
        title += f"  ({n_zero:,} zeros excluded)"
    fig.suptitle(title, fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)


def _hist_log_x(ax, x_abs):
    """Plot histogram with log-spaced bins, clipping to LOG_X_MIN."""
    x_clipped = x_abs[x_abs >= LOG_X_MIN]
    if len(x_clipped) == 0:
        ax.text(
            0.5, 0.5, f"All values < {LOG_X_MIN}", ha="center", va="center", transform=ax.transAxes
        )
        return
    lo = max(np.log10(x_clipped.min()), np.log10(LOG_X_MIN))
    hi = np.log10(x_clipped.max())
    if lo >= hi:
        hi = lo + 1
    bins = np.logspace(lo, hi, 300)
    ax.hist(x_clipped, bins=bins, color="steelblue", edgecolor="none", alpha=0.8)
    ax.set_xscale("log")
    n_dropped = len(x_abs) - len(x_clipped)
    if n_dropped > 0:
        ax.text(
            0.02,
            0.95,
            f"{n_dropped:,} samples < {LOG_X_MIN} clipped",
            transform=ax.transAxes,
            fontsize=7,
            va="top",
            color="gray",
        )


def _add_signed_markers(ax, L, U, x0, negative):
    """Add boundary markers for a sign-split log-x panel."""
    bounds = {}
    if negative:
        if L is not None and L < 0:
            bounds["L"] = abs(L)
        if U is not None and U < 0:
            bounds["U"] = abs(U)
        if x0 is not None and x0 < 0:
            bounds["x0"] = abs(x0)
    else:
        if L is not None and L > 0:
            bounds["L"] = L
        if U is not None and U > 0:
            bounds["U"] = U
        if x0 is not None and x0 > 0:
            bounds["x0"] = x0
    for label, val in bounds.items():
        color = "orange" if label == "x0" else "red"
        prefix = "|" if negative else ""
        suffix = "|" if negative else ""
        ax.axvline(
            val, color=color, ls="--", lw=1.5, label=f"{prefix}{label}{suffix}={val}", zorder=0
        )


def make_csv():
    """Create CSV template for ground truth annotation."""
    out = OUT_DIR / "ground_truth_validation.csv"
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["parameter", "L", "U", "x0", "lower", "upper", "interior"])
        for name in PARAMS:
            with open(DATA_DIR / f"{name}_test_metadata.json") as mf:
                meta = json.load(mf)
            writer.writerow([name, meta["L"], meta["U"], meta.get("x0", ""), "", "", ""])
    print(f"CSV written to {out}")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    out_pdf = OUT_DIR / "boundary_inspection.pdf"

    print("Generating inspection histograms...")
    with PdfPages(str(out_pdf)) as pdf:
        for name in PARAMS:
            print(f"  {name}...", flush=True)
            values, meta = load_dataset(name)
            x = values[np.isfinite(values)]
            L, U, x0 = meta["L"], meta["U"], meta.get("x0")
            counts = boundary_counts(x, L, U, x0)

            page_linear_x(pdf, name, x, meta, counts)
            page_log_x(pdf, name, x, meta, counts)

    print(f"PDF written to {out_pdf}")
    make_csv()


if __name__ == "__main__":
    main()
