#!/usr/bin/env python
"""Analyze M1/M2/M3 override effects on PPA12 boundary QC.

Full 2^3 factorial experiment: run boundary QC on all 12 PPA12 datasets
under 8 configurations (all combinations of M1/M3/M2 on/off).

Analysis-only — does NOT modify boundary.py or any production code.
Override disabling uses source-string monkey-patching via exec().
"""

import csv
import inspect
import json
from pathlib import Path

import pyarrow.parquet as pq

import fitqc.boundary as bmod
from fitqc import BoundaryConfig

# ============================================================================
# Constants
# ============================================================================

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
CSV_PATH = Path(__file__).parent / "dispatches" / "ground_truth_validation.csv"

CONFIG = BoundaryConfig(
    use_quantile_analysis=True,
    refine_transition=True,
    grid_mode="progressive",
)

CONFIG_LABELS = [
    "all-on",
    "M1-off",
    "M3-off",
    "M2-off",
    "M1+M3-off",
    "M1+M2-off",
    "M2+M3-off",
    "all-off",
]

# Pairs that differ in exactly one override, for marginal-effect analysis.
# Each pair is (override-on config, override-off config).
MARGINAL_PAIRS = {
    "M1": [
        ("all-on", "M1-off"),
        ("M3-off", "M1+M3-off"),
        ("M2-off", "M1+M2-off"),
        ("M2+M3-off", "all-off"),
    ],
    "M3": [
        ("all-on", "M3-off"),
        ("M1-off", "M1+M3-off"),
        ("M2-off", "M2+M3-off"),
        ("M1+M2-off", "all-off"),
    ],
    "M2": [
        ("all-on", "M2-off"),
        ("M1-off", "M1+M2-off"),
        ("M3-off", "M2+M3-off"),
        ("M1+M3-off", "all-off"),
    ],
}


# ============================================================================
# Data loading
# ============================================================================


def _is_sticky(val):
    """Parse stickiness from CSV: 'None' or empty -> False, any number -> True."""
    s = val.strip()
    return s != "" and s != "None"


def load_ground_truth():
    """Load empirical ground truth from visual inspection CSV.

    Returns dict mapping parameter name to expected dict with keys
    matching the fitqc_test schema (expected_lower_stickiness, etc.).
    """
    ground_truth = {}
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["parameter"]
            x0_raw = row["x0"].strip()
            ground_truth[name] = {
                "expected_lower_stickiness": _is_sticky(row["lower"]),
                "expected_upper_stickiness": _is_sticky(row["upper"]),
                "expected_interior_stickiness": _is_sticky(row["interior"]),
                "x0": None if not x0_raw or x0_raw == "None" else float(x0_raw),
                "L": float(row["L"]),
                "U": float(row["U"]),
            }
    return ground_truth


def load_datasets():
    """Load all 12 PPA12 test datasets with CSV ground truth."""
    ground_truth = load_ground_truth()
    datasets = {}
    for name in PARAMS:
        values = pq.read_table(DATA_DIR / f"{name}_test_sample.parquet")["values"].to_numpy()
        with open(DATA_DIR / f"{name}_test_metadata.json") as f:
            meta = json.load(f)
        datasets[name] = {
            "values": values,
            "L": meta["L"],
            "U": meta["U"],
            "expected": ground_truth[name],
        }
    return datasets


# ============================================================================
# Monkey-patching: create function variants with overrides disabled
# ============================================================================


def _find_block_ranges(lines):
    """Find (start, end) line indices for each override block.

    Returns dict mapping block name to (start_idx, end_idx) where
    start_idx is inclusive and end_idx is exclusive.
    """
    m1_start = next(i for i, ln in enumerate(lines) if "\u2014 spread-pileup" in ln)
    m3_start = next(i for i, ln in enumerate(lines) if "\u2014 broad-pileup" in ln)
    m3_end = next(
        i
        for i, ln in enumerate(lines)
        if "kneedle_elbows_lower = elbows_lower" in ln and i > m3_start
    )
    m2_start = next(i for i, ln in enumerate(lines) if "\u2014 delta-function" in ln)
    m2_end = next(
        i for i, ln in enumerate(lines) if "return BoundaryResult(" in ln and i > m2_start
    )
    return {
        "M1": (m1_start, m3_start),
        "M3": (m3_start, m3_end),
        "M2": (m2_start, m2_end),
    }


def _make_variant(lines, ranges, disable):
    """Build source with specified override blocks removed."""
    skip_ranges = [ranges[name] for name in disable]
    kept = []
    for i, line in enumerate(lines):
        if any(start <= i < end for start, end in skip_ranges):
            continue
        kept.append(line)
    return "\n".join(kept)


def build_variants():
    """Create 8 function variants for the factorial design.

    Returns dict mapping config label to callable.
    """
    source = inspect.getsource(bmod.run_boundary_qc)
    lines = source.split("\n")
    ranges = _find_block_ranges(lines)

    configs = {
        "all-on": [],
        "M1-off": ["M1"],
        "M3-off": ["M3"],
        "M2-off": ["M2"],
        "M1+M3-off": ["M1", "M3"],
        "M1+M2-off": ["M1", "M2"],
        "M2+M3-off": ["M2", "M3"],
        "all-off": ["M1", "M3", "M2"],
    }

    variants = {}
    for label, disable in configs.items():
        if not disable:
            variants[label] = bmod.run_boundary_qc
            continue
        patched_source = _make_variant(lines, ranges, disable)
        code = compile(patched_source, f"<{label}>", "exec")
        ns = {}
        exec(code, bmod.__dict__, ns)
        variants[label] = ns["run_boundary_qc"]

    return variants


# ============================================================================
# Run experiments
# ============================================================================


def run_experiments():
    """Run all 96 experiments (12 datasets x 8 configs)."""
    datasets = load_datasets()
    variants = build_variants()

    results = {}
    for name in PARAMS:
        ds = datasets[name]
        x, L, U = ds["values"], ds["L"], ds["U"]
        for label in CONFIG_LABELS:
            func = variants[label]
            r = func(x, L, U, CONFIG)
            results[(name, label)] = {
                "t_lo_raw": r.t_lo_raw,
                "t_lo_star": r.t_lo_star,
                "t_hi_raw": r.t_hi_raw,
                "t_hi_star": r.t_hi_star,
                "lower_detected": r.lower_pileup_detected,
                "upper_detected": r.upper_pileup_detected,
            }
        print(f"  {name}: done", flush=True)

    return results, datasets


# ============================================================================
# Analysis: marginal effects and verdicts
# ============================================================================


def compute_verdicts(results, datasets):
    """Compute per-override verdicts from marginal effects."""
    marginal_effects = {}
    verdicts = {}
    interactions = []

    for override, pairs in MARGINAL_PAIRS.items():
        for name in PARAMS:
            expected = datasets[name]["expected"]
            for side in ["lower", "upper"]:
                det_key = f"{side}_detected"
                exp_key = f"expected_{side}_stickiness"
                exp = expected[exp_key]

                pair_verdicts = []
                for on_config, off_config in pairs:
                    on_det = results[(name, on_config)][det_key]
                    off_det = results[(name, off_config)][det_key]
                    on_correct = on_det == exp
                    off_correct = off_det == exp

                    if on_det == off_det:
                        pair_verdicts.append("no effect")
                    elif on_correct and not off_correct:
                        pair_verdicts.append("helps")
                    elif not on_correct and off_correct:
                        pair_verdicts.append("hurts")
                    else:
                        pair_verdicts.append("both wrong")

                marginal_effects[(override, name, side)] = pair_verdicts

                unique = set(pair_verdicts)
                if len(unique) == 1:
                    verdicts[(override, name, side)] = pair_verdicts[0]
                else:
                    verdicts[(override, name, side)] = "interaction"
                    interactions.append(
                        f"{override} on {name} ({side}): "
                        f"verdicts vary across pairs: {pair_verdicts}"
                    )

    return marginal_effects, verdicts, interactions


# ============================================================================
# Output formatting
# ============================================================================


def fmt(v):
    """Format a value for tables."""
    if v is None:
        return "None"
    if isinstance(v, bool):
        return "T" if v else "F"
    return f"{v:.6f}"


def format_summary(verdicts):
    """Summary counts per override."""
    lines = ["## Summary", ""]
    for override in ["M1", "M3", "M2"]:
        counts = {
            "helps": 0,
            "hurts": 0,
            "no effect": 0,
            "both wrong": 0,
            "interaction": 0,
        }
        for name in PARAMS:
            for side in ["lower", "upper"]:
                counts[verdicts[(override, name, side)]] += 1
        lines.append(f"### {override}")
        lines.append(f"- Helps: {counts['helps']} / 24")
        lines.append(f"- Hurts: {counts['hurts']} / 24")
        lines.append(f"- No effect: {counts['no effect']} / 24")
        lines.append(f"- Both wrong: {counts['both wrong']} / 24")
        lines.append(f"- Interaction: {counts['interaction']} / 24")
        lines.append("")
    return "\n".join(lines)


def format_interactions(interactions):
    """Interaction flags."""
    lines = ["## Interaction Flags", ""]
    if not interactions:
        lines.append(
            "No interactions detected — all override effects are consistent across contexts."
        )
    else:
        for desc in interactions:
            lines.append(f"- {desc}")
    lines.append("")
    return "\n".join(lines)


def format_verdict_table(verdicts):
    """Per-override verdict table (non-trivial cases only)."""
    lines = [
        "## Per-Override Verdict Table (non-trivial cases)",
        "",
        "| Override | Parameter | Side | Verdict |",
        "|----------|-----------|------|---------|",
    ]
    for override in ["M1", "M3", "M2"]:
        for name in PARAMS:
            for side in ["lower", "upper"]:
                v = verdicts[(override, name, side)]
                if v == "no effect":
                    continue
                lines.append(f"| {override} | {name} | {side} | {v} |")
    return "\n".join(lines)


def format_marginal_details(marginal_effects, results, datasets):
    """Detailed marginal effect analysis showing value changes."""
    lines = [
        "## Marginal Effect Details",
        "",
        "Shows detection and threshold changes when toggling each override.",
        "",
    ]
    for override in ["M1", "M3", "M2"]:
        lines.append(f"### {override}")
        lines.append("")
        for name in PARAMS:
            for side in ["lower", "upper"]:
                key = (override, name, side)
                pv = marginal_effects[key]
                if all(v == "no effect" for v in pv):
                    continue

                det_key = f"{side}_detected"
                raw_key = "t_lo_raw" if side == "lower" else "t_hi_raw"
                star_key = "t_lo_star" if side == "lower" else "t_hi_star"
                exp_key = f"expected_{side}_stickiness"
                exp = datasets[name]["expected"][exp_key]

                lines.append(f"**{name} ({side})** — expected: {exp}")
                for pair_idx, (on_cfg, off_cfg) in enumerate(MARGINAL_PAIRS[override]):
                    on_r = results[(name, on_cfg)]
                    off_r = results[(name, off_cfg)]
                    v = pv[pair_idx]
                    lines.append(
                        f"  {on_cfg} -> {off_cfg}: "
                        f"det {on_r[det_key]}->{off_r[det_key]}, "
                        f"raw {fmt(on_r[raw_key])}->{fmt(off_r[raw_key])}, "
                        f"star {fmt(on_r[star_key])}->{fmt(off_r[star_key])} "
                        f"[{v}]"
                    )
                lines.append("")
    return "\n".join(lines)


def format_comparison_table(results):
    """Full 96-row comparison table."""
    lines = [
        "## Full Comparison Table",
        "",
        "| Parameter | Config | t_lo_raw | t_lo_star | t_hi_raw | t_hi_star | lo_det | hi_det |",
        "|-----------|--------|----------|-----------|----------|-----------|--------|--------|",
    ]
    for name in PARAMS:
        for label in CONFIG_LABELS:
            r = results[(name, label)]
            lines.append(
                f"| {name} | {label} | "
                f"{fmt(r['t_lo_raw'])} | {fmt(r['t_lo_star'])} | "
                f"{fmt(r['t_hi_raw'])} | {fmt(r['t_hi_star'])} | "
                f"{fmt(r['lower_detected'])} | {fmt(r['upper_detected'])} |"
            )
    return "\n".join(lines)


# ============================================================================
# Main
# ============================================================================


def main():
    print("Running 96 experiments (12 datasets x 8 configs)...", flush=True)
    results, datasets = run_experiments()

    print("\nComputing verdicts...", flush=True)
    marginal_effects, verdicts, interactions = compute_verdicts(results, datasets)

    sections = [
        "# Override Review Results (M1/M2/M3)",
        "",
        "Full 2^3 factorial experiment on 12 PPA12 datasets.",
        "All configs use `refine_transition=True, use_quantile_analysis=True, "
        "grid_mode='progressive'`.",
        "",
        format_summary(verdicts),
        format_interactions(interactions),
        format_verdict_table(verdicts),
        format_marginal_details(marginal_effects, results, datasets),
        format_comparison_table(results),
    ]

    output = "\n".join(sections)

    out_path = Path(__file__).parent / "dispatches" / "override_review_results.md"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(output)

    print(output)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
