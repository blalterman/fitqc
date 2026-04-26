#!/usr/bin/env python
"""Generate verification plots requested from ground truth review.

1. np2/np1 ratio histogram to check for interior stickiness
2. vx zoomed to (-250, -200) to estimate upper stickiness range
3. e_w_a zoomed to (-40, -20) linear-x to find two interior spikes
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyarrow.parquet as pq
from matplotlib.backends.backend_pdf import PdfPages

DATA_DIR = Path(__file__).parent / "tests" / "data"
OUT_DIR = Path(__file__).parent / "dispatches"


def load(name):
    values = pq.read_table(DATA_DIR / f"{name}_test_sample.parquet")["values"].to_numpy()
    with open(DATA_DIR / f"{name}_test_metadata.json") as f:
        meta = json.load(f)
    return values, meta


def page_np2_np1_ratio(pdf):
    """np2/np1 ratio to check for interior stickiness in np2.

    np2 is beam density, np1 is core density. x0=0 for np2 means the beam
    was initialized at zero. Plotting the ratio reveals whether np2 values
    cluster at specific fractions of np1.
    """
    np2_vals, _np2_meta = load("np2")
    _np1_vals, _ = load("np1")

    # np1 has 1M samples, np2 has 100k — they're independent subsamples
    # from the same 7.5M parent. We can't pair them row-by-row.
    # Instead, plot np2 values on a log scale to see interior structure.

    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))

    # Top-left: np2 zoomed near x0=0, linear x
    ax = axes[0, 0]
    mask = (np2_vals >= -0.5) & (np2_vals <= 2.0)
    ax.hist(np2_vals[mask], bins=500, color="steelblue", edgecolor="none", alpha=0.8)
    ax.axvline(0.0, color="orange", ls="--", lw=1.5, label="x0=0", zorder=0)
    ax.axvline(0.01, color="red", ls="--", lw=1.5, label="L=0.01", zorder=0)
    ax.set_title(f"np2 near x0=0 (n={mask.sum():,} in [-0.5, 2.0])", fontsize=10)
    ax.set_xlabel("np2 value")
    ax.set_ylabel("Count (linear)")
    ax.legend(fontsize=8)

    # Top-right: same but log-y
    ax = axes[0, 1]
    ax.hist(np2_vals[mask], bins=500, color="steelblue", edgecolor="none", alpha=0.8)
    ax.axvline(0.0, color="orange", ls="--", lw=1.5, label="x0=0", zorder=0)
    ax.axvline(0.01, color="red", ls="--", lw=1.5, label="L=0.01", zorder=0)
    ax.set_yscale("log")
    ax.set_title("Same, log y", fontsize=10)
    ax.set_xlabel("np2 value")
    ax.set_ylabel("Count (log)")
    ax.legend(fontsize=8)

    # Bottom-left: np2 full range log-x (positive only)
    ax = axes[1, 0]
    pos = np2_vals[np2_vals > 1e-5]
    bins = np.logspace(np.log10(1e-5), np.log10(pos.max()), 300)
    ax.hist(pos, bins=bins, color="steelblue", edgecolor="none", alpha=0.8)
    ax.set_xscale("log")
    ax.axvline(0.01, color="red", ls="--", lw=1.5, label="L=0.01", zorder=0)
    ax.set_title(f"np2 x > 1e-5, log x (n={len(pos):,})", fontsize=10)
    ax.set_xlabel("np2 (log scale)")
    ax.set_ylabel("Count (linear)")
    ax.legend(fontsize=8)

    # Bottom-right: same log-y
    ax = axes[1, 1]
    ax.hist(pos, bins=bins, color="steelblue", edgecolor="none", alpha=0.8)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.axvline(0.01, color="red", ls="--", lw=1.5, label="L=0.01", zorder=0)
    ax.set_title("Same, log y", fontsize=10)
    ax.set_xlabel("np2 (log scale)")
    ax.set_ylabel("Count (log)")
    ax.legend(fontsize=8)

    n_at_zero = int(np.sum(np2_vals == 0))
    n_at_L = int(np.sum(np2_vals == 0.01))
    n_below_L = int(np.sum(np2_vals < 0.01))
    fig.suptitle(
        f"np2 interior check — at x=0: {n_at_zero:,}, at L=0.01: {n_at_L:,}, "
        f"below L: {n_below_L:,}",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    pdf.savefig(fig)
    plt.close(fig)


def page_vx_upper_zoom(pdf):
    """vx zoomed to (-250, -200) — same binning as boundary_inspection, just xlim.

    U=-200 for vx. The user noted the upper stickiness looks wide in log space.
    """
    vx_vals, _ = load("vx")
    x = vx_vals[np.isfinite(vx_vals)]
    n_bins = min(1000, max(300, len(x) // 100))

    fig, (ax_lin, ax_log) = plt.subplots(2, 1, figsize=(11, 8.5))

    for ax, yscale in [(ax_lin, "linear"), (ax_log, "log")]:
        ax.axvline(-200, color="darkred", ls="--", lw=1.5, label="U=-200", zorder=0)
        ax.axvline(-1200, color="red", ls="--", lw=1.5, label="L=-1200", zorder=0)
        ax.hist(x, bins=n_bins, color="steelblue", edgecolor="none", alpha=0.8)
        ax.set_xlim(-250, -200)
        ax.xaxis.set_minor_locator(plt.MultipleLocator(1))
        ax.tick_params(which="minor", length=3)
        if yscale == "log":
            ax.set_yscale("log")
        ax.set_ylabel(f"Count ({yscale} y)")
        ax.set_xlabel("vx (km/s)")
        ax.legend(fontsize=8)

    n_at_U = int(np.sum(vx_vals == -200))
    n_near_U_5 = int(np.sum((vx_vals >= -205) & (vx_vals <= -200)))
    n_near_U_10 = int(np.sum((vx_vals >= -210) & (vx_vals <= -200)))
    fig.suptitle(
        f"vx upper zoom (same bins as inspection) — at U=-200: {n_at_U:,}, "
        f"[-205,-200]: {n_near_U_5:,}, [-210,-200]: {n_near_U_10:,}",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    pdf.savefig(fig)
    plt.close(fig)


def page_e_w_a_interior(pdf):
    """e_w_a zoomed to (-40, -20) to find two interior spikes.

    Same binning as boundary_inspection, just xlim. Secondary spike at ~-25.
    """
    vals, _ = load("e_w_a")
    x = vals[np.isfinite(vals)]
    n_bins = min(1000, max(300, len(x) // 100))

    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))

    # Top row: (-40, -20) tight zoom
    for ax, yscale in [(axes[0, 0], "linear"), (axes[0, 1], "log")]:
        ax.axvline(0, color="orange", ls="--", lw=1.5, label="x0=0", zorder=0)
        ax.axvline(-25, color="green", ls="--", lw=1.5, label="~-25", zorder=0)
        ax.axvline(-60, color="red", ls="--", lw=1.5, label="L=-60", zorder=0)
        ax.hist(x, bins=n_bins, color="steelblue", edgecolor="none", alpha=0.8)
        ax.set_xlim(-40, -20)
        if yscale == "log":
            ax.set_yscale("log")
        ax.set_ylabel(f"Count ({yscale} y)", fontsize=8)
        ax.set_xlabel("e_w_a (%)")
        ax.set_title("[-40, -20]", fontsize=10)
        ax.legend(fontsize=7)

    # Bottom row: (-60, 20) wider context showing both spikes
    for ax, yscale in [(axes[1, 0], "linear"), (axes[1, 1], "log")]:
        ax.axvline(0, color="orange", ls="--", lw=1.5, label="x0=0", zorder=0)
        ax.axvline(-25, color="green", ls="--", lw=1.5, label="~-25", zorder=0)
        ax.axvline(-60, color="red", ls="--", lw=1.5, label="L=-60", zorder=0)
        ax.hist(x, bins=n_bins, color="steelblue", edgecolor="none", alpha=0.8)
        ax.set_xlim(-60, 20)
        if yscale == "log":
            ax.set_yscale("log")
        ax.set_ylabel(f"Count ({yscale} y)", fontsize=8)
        ax.set_xlabel("e_w_a (%)")
        ax.set_title("[-60, 20]", fontsize=10)
        ax.legend(fontsize=7)

    n_at_x0 = int(np.sum(vals == 0))
    n_at_L = int(np.sum(vals == -60))
    n_at_m25 = int(np.sum(vals == -25))
    fig.suptitle(
        f"e_w_a interior check — at x0=0: {n_at_x0:,}, "
        f"at x=-25: {n_at_m25:,}, at L=-60: {n_at_L:,}",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    pdf.savefig(fig)
    plt.close(fig)


def page_np2_over_np1(pdf):
    """np2/np1 ratio histogram to check for interior stickiness in np2.

    Loads paired data from swefc.h5, computes ratio, subsamples to match
    the test data fraction (100k / 7,549,989).
    """
    import pandas as pd

    print("    Loading swefc.h5...", flush=True)
    df = pd.read_hdf("swefc.h5", "ppa12_apeq")

    np1_col = ("n_param", "", "p1")
    np2_col = ("n_param", "", "p2")
    np1_vals = df[np1_col].values
    np2_vals = df[np2_col].values

    # Compute ratio where np1 > 0
    valid = np.isfinite(np1_vals) & np.isfinite(np2_vals) & (np1_vals > 0)
    ratio = np2_vals[valid] / np1_vals[valid]
    print(f"    {len(ratio):,} valid ratio values from {len(df):,} rows", flush=True)

    # Subsample to match test fraction (100k / 7,549,989)
    n_test = 100_000
    frac = n_test / len(df)
    rng = np.random.default_rng(42)
    n_sub = int(len(ratio) * frac)
    idx = rng.choice(len(ratio), size=n_sub, replace=False)
    ratio_sub = ratio[idx]
    print(f"    Subsampled to {len(ratio_sub):,} values (frac={frac:.4f})", flush=True)

    # Page 1: linear-x
    n_bins = min(1000, max(300, len(ratio_sub) // 100))
    fig, (ax_lin, ax_log) = plt.subplots(2, 1, figsize=(11, 8.5))

    for ax, yscale in [(ax_lin, "linear"), (ax_log, "log")]:
        ax.axvline(0, color="orange", ls="--", lw=1.5, label="x0=0 (np2)", zorder=0)
        ax.hist(ratio_sub, bins=n_bins, color="steelblue", edgecolor="none", alpha=0.8)
        if yscale == "log":
            ax.set_yscale("log")
        ax.set_ylabel(f"Count ({yscale} y)")
        ax.legend(fontsize=8)

    ax_log.set_xlabel("np2 / np1")
    n_at_zero = int(np.sum(ratio_sub == 0))
    n_negative = int(np.sum(ratio_sub < 0))
    fig.suptitle(
        f"np2/np1 ratio — linear x (n={len(ratio_sub):,})\n"
        f"at ratio=0: {n_at_zero:,}, negative: {n_negative:,}",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    pdf.savefig(fig)
    plt.close(fig)

    # Page 2: log-x (split by sign)
    r_pos = ratio_sub[ratio_sub > 1e-5]
    r_neg = ratio_sub[ratio_sub < 0]
    n_zero_region = int(np.sum((ratio_sub >= 0) & (ratio_sub < 1e-5)))
    has_pos = len(r_pos) > 0
    has_neg = len(r_neg) > 0

    if has_pos and has_neg:
        fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
        for row, yscale in enumerate(["linear", "log"]):
            ax_n = axes[row, 0]
            abs_neg = np.abs(r_neg)
            lo = max(np.log10(abs_neg.min()), np.log10(1e-5))
            hi = np.log10(abs_neg.max())
            if lo >= hi:
                hi = lo + 1
            bins_n = np.logspace(lo, hi, 300)
            ax_n.hist(abs_neg, bins=bins_n, color="steelblue", edgecolor="none", alpha=0.8)
            ax_n.set_xscale("log")
            if yscale == "log":
                ax_n.set_yscale("log")
            ax_n.set_title(f"ratio < 0 (|r|, n={len(r_neg):,})", fontsize=9)
            ax_n.set_ylabel(f"Count ({yscale} y)", fontsize=8)
            ax_n.set_xlabel("|np2/np1| (log)")

            ax_p = axes[row, 1]
            lo = max(np.log10(r_pos.min()), np.log10(1e-5))
            hi = np.log10(r_pos.max())
            if lo >= hi:
                hi = lo + 1
            bins_p = np.logspace(lo, hi, 300)
            ax_p.hist(r_pos, bins=bins_p, color="steelblue", edgecolor="none", alpha=0.8)
            ax_p.set_xscale("log")
            if yscale == "log":
                ax_p.set_yscale("log")
            ax_p.set_title(f"ratio > 0 (n={len(r_pos):,})", fontsize=9)
            ax_p.set_ylabel(f"Count ({yscale} y)", fontsize=8)
            ax_p.set_xlabel("np2/np1 (log)")

    elif has_pos:
        fig, (ax_lin, ax_log) = plt.subplots(2, 1, figsize=(11, 8.5))
        lo = max(np.log10(r_pos.min()), np.log10(1e-5))
        hi = np.log10(r_pos.max())
        if lo >= hi:
            hi = lo + 1
        bins_p = np.logspace(lo, hi, 300)
        for ax, yscale in [(ax_lin, "linear"), (ax_log, "log")]:
            ax.hist(r_pos, bins=bins_p, color="steelblue", edgecolor="none", alpha=0.8)
            ax.set_xscale("log")
            if yscale == "log":
                ax.set_yscale("log")
            ax.set_ylabel(f"Count ({yscale} y)")
            ax.set_xlabel("np2/np1 (log)")
    else:
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.text(
            0.5,
            0.5,
            "No positive ratio values above 1e-5",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )

    title = "np2/np1 ratio — log x"
    if n_zero_region > 0:
        title += f"  ({n_zero_region:,} values in [0, 1e-5) excluded)"
    fig.suptitle(title, fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)


def page_np2_fraction(pdf):
    """np2/(np1+np2) fraction histogram — the beam density fraction."""
    import pandas as pd

    print("    Loading swefc.h5...", flush=True)
    df = pd.read_hdf("swefc.h5", "ppa12_apeq")

    np1_col = ("n_param", "", "p1")
    np2_col = ("n_param", "", "p2")
    np1_vals = df[np1_col].values
    np2_vals = df[np2_col].values

    total = np1_vals + np2_vals
    valid = np.isfinite(np1_vals) & np.isfinite(np2_vals) & (total > 0)
    frac_vals = np2_vals[valid] / total[valid]
    print(f"    {len(frac_vals):,} valid fraction values", flush=True)

    # Subsample to match test fraction
    n_test = 100_000
    sample_frac = n_test / len(df)
    rng = np.random.default_rng(42)
    n_sub = int(len(frac_vals) * sample_frac)
    idx = rng.choice(len(frac_vals), size=n_sub, replace=False)
    frac_sub = frac_vals[idx]
    print(f"    Subsampled to {len(frac_sub):,} values", flush=True)

    # Page 1: linear-x
    n_bins = min(1000, max(300, len(frac_sub) // 100))
    fig, (ax_lin, ax_log) = plt.subplots(2, 1, figsize=(11, 8.5))

    for ax, yscale in [(ax_lin, "linear"), (ax_log, "log")]:
        ax.axvline(0, color="orange", ls="--", lw=1.5, label="np2=0", zorder=0)
        ax.hist(frac_sub, bins=n_bins, color="steelblue", edgecolor="none", alpha=0.8)
        if yscale == "log":
            ax.set_yscale("log")
        ax.set_ylabel(f"Count ({yscale} y)")
        ax.legend(fontsize=8)

    ax_log.set_xlabel("np2 / (np1 + np2)")
    n_at_zero = int(np.sum(frac_sub == 0))
    n_negative = int(np.sum(frac_sub < 0))
    fig.suptitle(
        f"np2/(np1+np2) — linear x (n={len(frac_sub):,})\n"
        f"at 0: {n_at_zero:,}, negative: {n_negative:,}",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    pdf.savefig(fig)
    plt.close(fig)

    # Page 2: log-x (split by sign)
    f_pos = frac_sub[frac_sub > 1e-5]
    f_neg = frac_sub[frac_sub < 0]
    n_zero_region = int(np.sum((frac_sub >= 0) & (frac_sub < 1e-5)))
    has_pos = len(f_pos) > 0
    has_neg = len(f_neg) > 0

    if has_pos and has_neg:
        fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
        for row, yscale in enumerate(["linear", "log"]):
            ax_n = axes[row, 0]
            abs_neg = np.abs(f_neg)
            lo = max(np.log10(abs_neg.min()), np.log10(1e-5))
            hi = np.log10(abs_neg.max())
            if lo >= hi:
                hi = lo + 1
            ax_n.hist(
                abs_neg,
                bins=np.logspace(lo, hi, 300),
                color="steelblue",
                edgecolor="none",
                alpha=0.8,
            )
            ax_n.set_xscale("log")
            if yscale == "log":
                ax_n.set_yscale("log")
            ax_n.set_title(f"frac < 0 (|f|, n={len(f_neg):,})", fontsize=9)
            ax_n.set_ylabel(f"Count ({yscale} y)", fontsize=8)
            ax_n.set_xlabel("|np2/(np1+np2)| (log)")

            ax_p = axes[row, 1]
            lo = max(np.log10(f_pos.min()), np.log10(1e-5))
            hi = np.log10(f_pos.max())
            if lo >= hi:
                hi = lo + 1
            ax_p.hist(
                f_pos, bins=np.logspace(lo, hi, 300), color="steelblue", edgecolor="none", alpha=0.8
            )
            ax_p.set_xscale("log")
            if yscale == "log":
                ax_p.set_yscale("log")
            ax_p.set_title(f"frac > 0 (n={len(f_pos):,})", fontsize=9)
            ax_p.set_ylabel(f"Count ({yscale} y)", fontsize=8)
            ax_p.set_xlabel("np2/(np1+np2) (log)")

    elif has_pos:
        fig, (ax_lin, ax_log) = plt.subplots(2, 1, figsize=(11, 8.5))
        lo = max(np.log10(f_pos.min()), np.log10(1e-5))
        hi = np.log10(f_pos.max())
        if lo >= hi:
            hi = lo + 1
        bins_p = np.logspace(lo, hi, 300)
        for ax, yscale in [(ax_lin, "linear"), (ax_log, "log")]:
            ax.hist(f_pos, bins=bins_p, color="steelblue", edgecolor="none", alpha=0.8)
            ax.set_xscale("log")
            if yscale == "log":
                ax.set_yscale("log")
            ax.set_ylabel(f"Count ({yscale} y)")
            ax.set_xlabel("np2/(np1+np2) (log)")
    else:
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.text(
            0.5,
            0.5,
            "No positive fraction values above 1e-5",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )

    title = "np2/(np1+np2) — log x"
    if n_zero_region > 0:
        title += f"  ({n_zero_region:,} values in [0, 1e-5) excluded)"
    fig.suptitle(title, fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    out_pdf = OUT_DIR / "boundary_verification.pdf"

    print("Generating verification plots...")
    with PdfPages(str(out_pdf)) as pdf:
        print("  np2 interior check...", flush=True)
        page_np2_np1_ratio(pdf)
        print("  np2/np1 ratio...", flush=True)
        page_np2_over_np1(pdf)
        print("  np2/(np1+np2) fraction...", flush=True)
        page_np2_fraction(pdf)
        print("  vx upper zoom...", flush=True)
        page_vx_upper_zoom(pdf)
        print("  e_w_a interior...", flush=True)
        page_e_w_a_interior(pdf)

    print(f"PDF written to {out_pdf}")


if __name__ == "__main__":
    main()
