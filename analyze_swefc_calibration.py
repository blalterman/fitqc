#!/usr/bin/env python
"""Calibration harness: swefc.h5 vs dispatches/ground_truth_swefc.json.

Driver only. Reuses the public ``run_boundary_qc`` and ``run_interior_qc``
entry points with the BoundaryConfig matched to ``analyze_overrides.py``.
Does not modify ``analyze_overrides.py`` or anything under ``src/fitqc/``.

Per-parameter output: booleans for lower / upper / interior detection,
compared against the user-arbitrated ground truth in
``dispatches/ground_truth_swefc.json`` (bullet-list values).

Generated with Claude Code.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

import fitqc.boundary as bmod
import fitqc.interior as imod
from fitqc import BoundaryConfig, InteriorConfig

REPO = Path(__file__).resolve().parent
DEFAULT_H5 = REPO / "swefc.h5"
DEFAULT_TRUTH = REPO / "dispatches" / "ground_truth_swefc.json"
DEFAULT_REPORT = REPO / "dispatches" / "swefc_calibration_report.md"
DEFAULT_FIGURE = REPO / "figures" / "swefc_calibration_report.pdf"
H5_KEY = "ppa12_apeq"

BOUNDARY_CFG = BoundaryConfig(
    use_quantile_analysis=True,
    refine_transition=True,
    grid_mode="progressive",
)
INTERIOR_CFG = InteriorConfig(use_quantile_analysis=True)


@dataclass
class ParamResult:
    name: str
    truth_lower: bool
    truth_upper: bool
    truth_interior: bool
    column_tuple: tuple[str, ...]
    x0: float | None
    L: float
    U: float
    interior_locations: list[float]
    detected_lower: bool
    detected_upper: bool
    detected_interior: bool
    t_lo_star: float | None
    t_hi_star: float | None
    interior_hits: list[
        tuple[float, float | None]
    ]  # (location, eps_star) pairs where spike detected
    n_samples: int
    n_dropped_nan: int
    note: str

    @property
    def lower_ok(self) -> bool:
        return self.detected_lower == self.truth_lower

    @property
    def upper_ok(self) -> bool:
        return self.detected_upper == self.truth_upper

    @property
    def interior_ok(self) -> bool:
        return self.detected_interior == self.truth_interior

    @property
    def all_ok(self) -> bool:
        return self.lower_ok and self.upper_ok and self.interior_ok


def load_truth(path: Path) -> list[dict]:
    with open(path) as f:
        payload = json.load(f)
    return payload["parameters"]


def load_swefc(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"HDF5 file not found: {path}")
    return pd.read_hdf(path, key=H5_KEY)


def _extract_values(df: pd.DataFrame, column_tuple: list[str]) -> np.ndarray:
    col = tuple(column_tuple)
    series = df[col]
    values = series.to_numpy(dtype=float)
    return values


def run_one(df: pd.DataFrame, entry: dict) -> ParamResult:
    """Run boundary + interior detection for one ground-truth entry."""
    values_raw = _extract_values(df, entry["column_tuple"])
    finite_mask = np.isfinite(values_raw)
    values = values_raw[finite_mask]
    n_dropped = int(values_raw.size - values.size)

    L = float(entry["L"])
    U = float(entry["U"])
    x0 = entry["x0"]

    b_res = bmod.run_boundary_qc(values, L=L, U=U, config=BOUNDARY_CFG)

    # Interior detection per asserted location in ground truth. A parameter
    # can assert multiple interior spikes (e.g. e.w.a at 0 and -25); the
    # single-x0 detector checks one location at a time, so iterate and
    # OR-aggregate. interior_locations is empty when truth says no spike.
    interior_locations = [float(v) for v in entry.get("interior_locations", [])]
    interior_hits: list[tuple[float, float | None]] = []
    for loc in interior_locations:
        i_res = imod.run_interior_qc(values, x0=loc, L=L, U=U, config=INTERIOR_CFG)
        if i_res.spike_detected:
            eps = float(i_res.eps_star) if i_res.eps_star is not None else None
            interior_hits.append((loc, eps))
    detected_interior = len(interior_hits) > 0

    return ParamResult(
        name=entry["parameter"],
        truth_lower=bool(entry["lower"]),
        truth_upper=bool(entry["upper"]),
        truth_interior=bool(entry["interior"]),
        column_tuple=tuple(entry["column_tuple"]),
        x0=None if x0 is None else float(x0),
        L=L,
        U=U,
        interior_locations=interior_locations,
        detected_lower=bool(b_res.lower_pileup_detected),
        detected_upper=bool(b_res.upper_pileup_detected),
        detected_interior=detected_interior,
        t_lo_star=(float(b_res.t_lo_star) if b_res.t_lo_star is not None else None),
        t_hi_star=(float(b_res.t_hi_star) if b_res.t_hi_star is not None else None),
        interior_hits=interior_hits,
        n_samples=int(values.size),
        n_dropped_nan=n_dropped,
        note=entry.get("note", "") or "",
    )


def _fmt_bool_cell(truth: bool, detected: bool) -> str:
    mark = "PASS" if truth == detected else "FAIL"
    return f"{str(detected).lower()} ({mark})"


def _fmt_float(v: float | None) -> str:
    return "—" if v is None else f"{v:.3g}"


def write_report(results: list[ParamResult], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total = len(results)
    lo_pass = sum(r.lower_ok for r in results)
    up_pass = sum(r.upper_ok for r in results)
    in_pass = sum(r.interior_ok for r in results)
    all_pass = sum(r.all_ok for r in results)

    lines: list[str] = []
    lines.append("# swefc.h5 calibration report")
    lines.append("")
    lines.append(f"- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Dataset: `swefc.h5` key `{H5_KEY}`")
    lines.append("- Ground truth: `dispatches/ground_truth_swefc.json`")
    lines.append(
        "- Config: "
        '`BoundaryConfig(use_quantile_analysis=True, refine_transition=True, grid_mode="progressive")`, '
        "`InteriorConfig(use_quantile_analysis=True)`"
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Lower pass: **{lo_pass}/{total}**")
    lines.append(f"- Upper pass: **{up_pass}/{total}**")
    lines.append(f"- Interior pass: **{in_pass}/{total}**")
    lines.append(f"- All-three pass: **{all_pass}/{total}**")
    lines.append("")

    lines.append("## Per-parameter results")
    lines.append("")
    header = (
        "| parameter | n | lower (truth/detected) | upper (truth/detected) | "
        "interior (truth/detected) | t_lo_star | t_hi_star | interior hits (loc: eps*) |"
    )
    sep = "|" + "---|" * 8
    lines.append(header)
    lines.append(sep)
    for r in results:
        loc_truth = ",".join(f"{v:g}" for v in r.interior_locations) or "—"
        hits = ", ".join(f"{loc:g}: {_fmt_float(eps)}" for loc, eps in r.interior_hits) or "—"
        lines.append(
            f"| `{r.name}` | {r.n_samples} | {str(r.truth_lower).lower()}/{_fmt_bool_cell(r.truth_lower, r.detected_lower)} | {str(r.truth_upper).lower()}/{_fmt_bool_cell(r.truth_upper, r.detected_upper)} | [{loc_truth}] {str(r.truth_interior).lower()}/{_fmt_bool_cell(r.truth_interior, r.detected_interior)} | "
            f"{_fmt_float(r.t_lo_star)} | {_fmt_float(r.t_hi_star)} | {hits} |"
        )
    lines.append("")

    mismatches = [r for r in results if not r.all_ok]
    lines.append("## Mismatches")
    lines.append("")
    if not mismatches:
        lines.append("None — all 12 parameters match ground truth on lower/upper/interior.")
    else:
        for r in mismatches:
            axes = []
            if not r.lower_ok:
                axes.append(f"lower: truth={r.truth_lower} detected={r.detected_lower}")
            if not r.upper_ok:
                axes.append(f"upper: truth={r.truth_upper} detected={r.detected_upper}")
            if not r.interior_ok:
                axes.append(f"interior: truth={r.truth_interior} detected={r.detected_interior}")
            lines.append(f"- `{r.name}` — {'; '.join(axes)}")
            if r.note:
                lines.append(f"  - note: {r.note}")
    lines.append("")

    out_path.write_text("\n".join(lines))


def write_figure(df: pd.DataFrame, results: list[ParamResult], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = len(results)
    ncols = 3
    nrows = int(np.ceil(n / ncols))
    with PdfPages(out_path) as pdf:
        fig, axes = plt.subplots(nrows, ncols, figsize=(13, 3.0 * nrows), constrained_layout=True)
        axes = np.atleast_2d(axes)
        for idx, r in enumerate(results):
            ax = axes[idx // ncols, idx % ncols]
            v = df[r.column_tuple].to_numpy(dtype=float)
            v = v[np.isfinite(v)]
            if v.size:
                ax.hist(v, bins=200, color="steelblue", histtype="step", linewidth=0.6)
            ax.set_yscale("log")
            ax.axvline(r.L, color="red", lw=0.8, ls="--", label=f"L={r.L:g}")
            ax.axvline(r.U, color="red", lw=0.8, ls="--", label=f"U={r.U:g}")
            # Asserted interior locations (orange dotted, one per location).
            for loc in r.interior_locations:
                ax.axvline(loc, color="orange", lw=0.8, ls=":")
            # Detected boundary cuts (green, thin).
            if r.t_lo_star is not None:
                ax.axvline(r.L + r.t_lo_star * (r.U - r.L), color="green", lw=0.6)
            if r.t_hi_star is not None:
                ax.axvline(r.U - r.t_hi_star * (r.U - r.L), color="green", lw=0.6)
            # Detected interior spike locations (magenta, thicker) to
            # distinguish "asserted but not detected" from "detected".
            for loc, _eps in r.interior_hits:
                ax.axvline(loc, color="magenta", lw=1.2, ls="-", alpha=0.7)
            status = "OK" if r.all_ok else "FAIL"
            ax.set_title(f"{r.name}  [{status}]  n={r.n_samples}", fontsize=8)
            ax.tick_params(axis="both", labelsize=6)
        # hide unused axes
        for k in range(n, nrows * ncols):
            axes[k // ncols, k % ncols].set_visible(False)
        fig.suptitle("swefc.h5 calibration — histograms with L/U/x0 + detected cuts", fontsize=10)
        pdf.savefig(fig, dpi=150)
        plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--h5", type=Path, default=DEFAULT_H5)
    ap.add_argument("--truth", type=Path, default=DEFAULT_TRUTH)
    ap.add_argument("--output-report", type=Path, default=DEFAULT_REPORT)
    ap.add_argument("--output-figure", type=Path, default=DEFAULT_FIGURE)
    ap.add_argument("--param", default=None, help="optional single-parameter filter")
    args = ap.parse_args(argv)

    t0 = time.time()
    print(f"Loading ground truth from {args.truth} ...")
    entries = load_truth(args.truth)
    if args.param is not None:
        entries = [e for e in entries if e["parameter"] == args.param]
        if not entries:
            print(f"No ground-truth entry named {args.param!r}", file=sys.stderr)
            return 2

    print(f"Loading {args.h5} ...")
    df = load_swefc(args.h5)
    print(f"  rows: {len(df):,}")

    results: list[ParamResult] = []
    for e in entries:
        t_param = time.time()
        r = run_one(df, e)
        dt = time.time() - t_param
        print(
            f"  {r.name:20s}  n={r.n_samples:>9d}  "
            f"lower={_fmt_bool_cell(r.truth_lower, r.detected_lower)}  "
            f"upper={_fmt_bool_cell(r.truth_upper, r.detected_upper)}  "
            f"interior={_fmt_bool_cell(r.truth_interior, r.detected_interior)}  "
            f"({dt:.1f}s)"
        )
        results.append(r)

    print(f"\nWriting report to {args.output_report} ...")
    write_report(results, args.output_report)
    print(f"Writing figure to {args.output_figure} ...")
    write_figure(df, results, args.output_figure)

    total = len(results)
    all_pass = sum(r.all_ok for r in results)
    print(f"\nDone in {time.time() - t0:.1f}s  —  all-three pass: {all_pass}/{total}")

    return 0 if all_pass == total else 1


if __name__ == "__main__":
    sys.exit(main())
