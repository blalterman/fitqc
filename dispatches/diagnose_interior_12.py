#!/usr/bin/env python
"""Throwaway diagnostic: run interior QC on all 12 PPA12 parameters.

Evaluates ``run_interior_qc`` against the ``interior`` column of
``dispatches/ground_truth_validation.csv``. Prints a 12-row verdict table
(TP/FN/FP/TN/SKIP per parameter) to stdout.

SKIP classification is used when the CSV ``x0`` column is None (moment-based
parameters). ``run_interior_qc`` requires a scalar ``x0``, so these rows
cannot be evaluated without an assumption about per-sample x0.

Mirrors ``diagnose_boundary_24.py`` structure. Imports ``PARAMS`` and
``load_datasets`` from ``analyze_overrides``; imports ``run_interior_qc``
from ``fitqc.interior``.

Usage:
    python dispatches/diagnose_interior_12.py [--csv]

Without --csv, prints a markdown table for human review. With --csv, prints
machine-readable rows for diffing across runs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyze_overrides import PARAMS, load_datasets

from fitqc.config import InteriorConfig
from fitqc.interior import run_interior_qc


def _fmt(x: float | None) -> str:
    return "None" if x is None else f"{x:.6g}"


def _classify(det: bool, expected: bool, x0_present: bool) -> str:
    if not x0_present:
        return "SKIP"
    if expected and det:
        return "TP"
    if expected and not det:
        return "FN"
    if not expected and det:
        return "FP"
    return "TN"


def diagnose(name: str, ds: dict, config: InteriorConfig) -> dict:
    expected_bool = ds["expected"]["expected_interior_stickiness"]
    x0 = ds["expected"]["x0"]
    L = ds["expected"]["L"]
    U = ds["expected"]["U"]

    if x0 is None:
        return {
            "param": name,
            "x0": None,
            "interior_expected": expected_bool,
            "spike_detected": None,
            "spike_z_loc": None,
            "eps_star": None,
            "class": _classify(False, expected_bool, x0_present=False),
        }

    result = run_interior_qc(ds["values"], x0=x0, L=L, U=U, config=config)
    return {
        "param": name,
        "x0": x0,
        "interior_expected": expected_bool,
        "spike_detected": result.spike_detected,
        "spike_z_loc": result.spike_z_loc,
        "eps_star": result.eps_star,
        "class": _classify(result.spike_detected, expected_bool, x0_present=True),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    datasets = load_datasets()
    config = InteriorConfig()

    rows = [diagnose(name, datasets[name], config) for name in PARAMS]

    if args.csv:
        print("param,x0,interior_expected,spike_detected,spike_z_loc,eps_star,class")
        for r in rows:
            print(
                f"{r['param']},{_fmt(r['x0'])},{r['interior_expected']},"
                f"{r['spike_detected']},{_fmt(r['spike_z_loc'])},"
                f"{_fmt(r['eps_star'])},{r['class']}"
            )
    else:
        print(
            "| param | x0 | interior_expected | spike_detected | spike_z_loc | eps_star | class |"
        )
        print(
            "|-------|-----|-------------------|----------------|-------------|----------|-------|"
        )
        for r in rows:
            print(
                f"| {r['param']} | {_fmt(r['x0'])} | {r['interior_expected']} | "
                f"{r['spike_detected']} | {_fmt(r['spike_z_loc'])} | "
                f"{_fmt(r['eps_star'])} | {r['class']} |"
            )

        counts = {"TP": 0, "FN": 0, "FP": 0, "TN": 0, "SKIP": 0}
        for r in rows:
            counts[r["class"]] += 1
        print(
            f"\nTP={counts['TP']}  FN={counts['FN']}  FP={counts['FP']}  "
            f"TN={counts['TN']}  SKIP={counts['SKIP']}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
