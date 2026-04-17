#!/usr/bin/env python
"""Throwaway diagnostic: run boundary QC on all 24 (parameter, side) cases.

Establishes a TP-regression baseline before changing boundary.py. After each
fix, re-run and diff against baseline to catch any TP -> FN flip in seconds
(vs ~90s for analyze_overrides.py).

Mirrors analyze_overrides.py:load_datasets and uses the same all-on
production config (use_quantile_analysis=True, refine_transition=True,
grid_mode="progressive"). Compares detection booleans against
ground_truth_validation.csv.

Usage:
    python dispatches/diagnose_boundary_24.py [--csv]

Without --csv, prints a markdown table for human review. With --csv, prints
machine-readable rows for diffing across runs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyze_overrides import (
    CONFIG,
    PARAMS,
    load_datasets,
)

from fitqc.boundary import run_boundary_qc


def _fmt(x: float | None) -> str:
    return "None" if x is None else f"{x:.6f}"


def _mass_at(curve: np.ndarray, tol_grid: np.ndarray, t: float | None) -> float | None:
    if t is None:
        return None
    idx = int(np.searchsorted(tol_grid, t))
    if idx >= len(curve):
        idx = len(curve) - 1
    return float(curve[idx])


def diagnose(name: str, ds: dict, *, side: str) -> dict:
    result = run_boundary_qc(ds["values"], L=ds["L"], U=ds["U"], config=CONFIG)
    if side == "lower":
        t_raw = result.t_lo_raw
        t_star = result.t_lo_star
        det = result.lower_pileup_detected
        expected = ds["expected"]["expected_lower_stickiness"]
        mass = _mass_at(result.lower_mass_curve, result.tol_grid, t_raw)
    else:
        t_raw = result.t_hi_raw
        t_star = result.t_hi_star
        det = result.upper_pileup_detected
        expected = ds["expected"]["expected_upper_stickiness"]
        mass = _mass_at(result.upper_mass_curve, result.tol_grid, t_raw)

    expected_mass = None if t_raw is None else float(t_raw) * 1.5
    classification = _classify(det, expected)
    return {
        "param": name,
        "side": side,
        "t_raw": t_raw,
        "t_star": t_star,
        "det": det,
        "expected": expected,
        "class": classification,
        "mass_at_raw": mass,
        "expected_mass_at_raw": expected_mass,
    }


def _classify(det: bool, expected: bool) -> str:
    if expected and det:
        return "TP"
    if expected and not det:
        return "FN"
    if not expected and det:
        return "FP"
    return "TN"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    datasets = load_datasets()
    rows = []
    for name in PARAMS:
        for side in ("lower", "upper"):
            rows.append(diagnose(name, datasets[name], side=side))

    if args.csv:
        print("param,side,t_raw,t_star,det,expected,class,mass_at_raw,expected_mass_at_raw")
        for r in rows:
            print(
                f"{r['param']},{r['side']},{_fmt(r['t_raw'])},{_fmt(r['t_star'])},"
                f"{r['det']},{r['expected']},{r['class']},"
                f"{_fmt(r['mass_at_raw'])},{_fmt(r['expected_mass_at_raw'])}"
            )
    else:
        print(
            "| param | side | t_raw | t_star | det | exp | class | mass(t_raw) | exp_mass(t_raw) |"
        )
        print(
            "|-------|------|-------|--------|-----|-----|-------|-------------|-----------------|"
        )
        for r in rows:
            print(
                f"| {r['param']} | {r['side']} | {_fmt(r['t_raw'])} | {_fmt(r['t_star'])} | "
                f"{r['det']} | {r['expected']} | {r['class']} | "
                f"{_fmt(r['mass_at_raw'])} | {_fmt(r['expected_mass_at_raw'])} |"
            )

        n_fn = sum(1 for r in rows if r["class"] == "FN")
        n_tp = sum(1 for r in rows if r["class"] == "TP")
        n_fp = sum(1 for r in rows if r["class"] == "FP")
        n_tn = sum(1 for r in rows if r["class"] == "TN")
        print(f"\nTP={n_tp}  FN={n_fn}  FP={n_fp}  TN={n_tn}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
