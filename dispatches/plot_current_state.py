#!/usr/bin/env python
"""Current-state overview: all 24 (parameter, side) boundary detections.

One-page summary figure with 12 rows (parameters) x 2 columns (lower, upper).
Each mini-panel shows the near-boundary mass curve with the detected t_star
annotated. Title color encodes correctness vs CSV ground truth:
    green = TP  (detected as expected)
    red   = FN  (missed; should have detected)
    gray  = n/a (ground truth says not sticky — none in this data set)

Output: dispatches/current_state_overview.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyze_overrides import CONFIG, PARAMS, load_datasets

from fitqc.boundary import compute_u, run_boundary_qc, tail_mass

OUT = Path(__file__).resolve().parent / "current_state_overview.pdf"

# Fine tolerance axis for near-boundary mass curves (log-spaced).
TOLS = np.logspace(-7, -0.3, 80)  # 1e-7 to ~0.5 of range


def mass_curve(u_sorted: np.ndarray, tols: np.ndarray) -> np.ndarray:
    return np.array([tail_mass(u_sorted, t) for t in tols])


def main() -> int:
    datasets = load_datasets()

    fig, axes = plt.subplots(12, 2, figsize=(10, 24), sharex=True)
    fig.suptitle(
        "Boundary detection — current state across all PPA12 parameters\n"
        "mass curves near u=0 (lower) and u=1 (upper), with detected t_star",
        fontsize=12,
    )

    n_tp = n_fn = 0

    for row, name in enumerate(PARAMS):
        ds = datasets[name]
        u = compute_u(ds["values"], ds["L"], ds["U"])
        u = u[(u >= 0) & (u <= 1)]
        u_sorted = np.sort(u)
        one_minus_u_sorted = np.sort(1.0 - u)

        result = run_boundary_qc(ds["values"], L=ds["L"], U=ds["U"], config=CONFIG)

        for col, (side, curve_u, t_star, det, expected) in enumerate(
            [
                (
                    "lower",
                    u_sorted,
                    result.t_lo_star,
                    result.lower_pileup_detected,
                    ds["expected"]["expected_lower_stickiness"],
                ),
                (
                    "upper",
                    one_minus_u_sorted,
                    result.t_hi_star,
                    result.upper_pileup_detected,
                    ds["expected"]["expected_upper_stickiness"],
                ),
            ]
        ):
            ax = axes[row, col]
            masses = mass_curve(curve_u, TOLS)
            ax.loglog(TOLS, masses, color="steelblue", lw=1.2, label="mass(tol)")
            # Uniform reference line: mass = tol
            ax.loglog(TOLS, TOLS, color="gray", ls=":", lw=0.8, label="uniform")
            # 1.5x uniform (excess_ratio)
            ax.loglog(TOLS, 1.5 * TOLS, color="gray", ls="--", lw=0.6, label="1.5x uniform")

            if t_star is not None and t_star > 0:
                ax.axvline(t_star, color="darkorange", lw=1.5, ls="-")
                ax.text(
                    t_star,
                    ax.get_ylim()[1] * 0.5,
                    f" t*={t_star:.1e}",
                    color="darkorange",
                    fontsize=7,
                    va="top",
                )

            # Classification color
            if expected and det:
                cls, color = "TP", "green"
                n_tp += 1
            elif expected and not det:
                cls, color = "FN", "red"
                n_fn += 1
            else:
                cls, color = "n/a", "gray"

            ax.set_title(f"{name} {side}  [{cls}]", color=color, fontsize=9)
            ax.set_xlim(1e-7, 0.5)
            ax.set_ylim(1e-6, 1.0)
            ax.grid(True, which="both", alpha=0.2)
            if row == 11:
                ax.set_xlabel("tolerance (normalized)")
            if col == 0:
                ax.set_ylabel("mass")

    axes[0, 1].legend(loc="lower right", fontsize=7)
    fig.text(
        0.5,
        0.005,
        f"TP = {n_tp}   FN = {n_fn}   (fix: sub-grid excess-mass fallback, commit 44447a0)",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.01, 1, 0.985))
    fig.savefig(OUT, bbox_inches="tight")
    print(f"Saved: {OUT}")
    print(f"TP = {n_tp}   FN = {n_fn}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
