#!/usr/bin/env python
"""Example: Run QC on fitted parameter arrays.

This example demonstrates the complete fitqc workflow:
1. Generate synthetic fit results (simulating real fitted parameters)
2. Run QC to detect stickiness issues
3. Examine the report and filter bad samples

Usage:
    python examples/run_array_qc.py

In real use, you would replace the synthetic data with your actual
fitted parameter arrays from bootstrapping, MCMC, or Monte Carlo simulations.
"""

import numpy as np

from fitqc.config import BoundaryConfig, InteriorConfig, QCSpec
from fitqc.report import run_qc
from fitqc.synth import (
    generate_uniform,
    generate_with_boundary_pileup,
    generate_with_x0_spike,
)


def main():
    """Run QC on synthetic fitted parameters."""
    print("=" * 60)
    print("fitqc Example: Quality Control for Fitted Parameters")
    print("=" * 60)
    print()

    # Number of bootstrap/MC samples
    n_samples = 10000
    print(f"Generating {n_samples} synthetic fit results...")
    print()

    # Simulate fitted parameters from a physics model
    # In practice, these would come from your actual fits
    params = {
        # alpha: Clean uniform distribution (no issues)
        "alpha": generate_uniform(n=n_samples, low=0.0, high=10.0, seed=1),
        # beta: Has 5% x0 stickiness (optimizer stuck at initial guess)
        "beta": generate_with_x0_spike(n=n_samples, x0=5.0, L=0.0, U=10.0, spike_frac=0.05, seed=2),
        # gamma: Has 3% lower boundary pileup (constrained at bound)
        "gamma": generate_with_boundary_pileup(
            n=n_samples, L=0.0, U=10.0, lower_pileup_frac=0.03, seed=3
        ),
    }

    # Define the QC specification
    # This tells fitqc about the initial guesses and bounds for each parameter
    spec = QCSpec(
        param_names=["alpha", "beta", "gamma"],
        x0={
            "alpha": 5.0,
            "beta": 5.0,
            "gamma": 5.0,
        },
        bounds={
            "alpha": (0.0, 10.0),
            "beta": (0.0, 10.0),
            "gamma": (0.0, 10.0),
        },
    )

    # Run QC
    print("Running QC analysis...")
    report, masks = run_qc(
        params=params,
        spec=spec,
        interior_config=InteriorConfig(),
        boundary_config=BoundaryConfig(),
        precision_config=None,
    )
    print()

    # Report results
    print("QC Results:")
    print("-" * 40)
    for name in spec.param_names:
        interior = report.interior_results[name]
        boundary = report.boundary_results[name]

        print(f"\n{name}:")

        # Interior (x0 stickiness)
        if interior.spike_detected:
            print("  [!] x0 stickiness detected")
            print(f"      eps* = {interior.eps_star:.6f}")
            print(f"      spike location z = {interior.spike_z_loc:.6f}")
        else:
            print("  [ok] No x0 stickiness")

        # Boundary (pileup)
        if boundary.lower_pileup_detected:
            print("  [!] Lower boundary pileup detected")
            print(f"      t_lo* = {boundary.t_lo_star:.6f}")
        if boundary.upper_pileup_detected:
            print("  [!] Upper boundary pileup detected")
            print(f"      t_hi* = {boundary.t_hi_star:.6f}")
        if not boundary.lower_pileup_detected and not boundary.upper_pileup_detected:
            print("  [ok] No boundary pileup")

        # Mask statistics
        mask = masks[name]
        n_good = np.sum(mask)
        n_bad = len(mask) - n_good
        pct_bad = 100 * n_bad / len(mask)
        print(f"  Mask: {n_good}/{len(mask)} good samples ({pct_bad:.1f}% filtered)")

    # Combined mask for filtering all parameters together
    print()
    print("-" * 40)
    combined_mask = masks["alpha"] & masks["beta"] & masks["gamma"]
    n_good_combined = np.sum(combined_mask)
    print(f"Combined mask: {n_good_combined}/{n_samples} samples pass all QC")
    print()

    # Example: Use masks to get clean data
    clean_alpha = params["alpha"][combined_mask]
    clean_beta = params["beta"][combined_mask]
    clean_gamma = params["gamma"][combined_mask]
    print(f"Clean alpha: mean={np.mean(clean_alpha):.3f}, std={np.std(clean_alpha):.3f}")
    print(f"Clean beta:  mean={np.mean(clean_beta):.3f}, std={np.std(clean_beta):.3f}")
    print(f"Clean gamma: mean={np.mean(clean_gamma):.3f}, std={np.std(clean_gamma):.3f}")
    print()

    # Save report to JSON (for reproducibility)
    json_path = "qc_report.json"
    with open(json_path, "w") as f:
        f.write(report.to_json(indent=2))
    print(f"Report saved to: {json_path}")
    print()

    print("Done!")


if __name__ == "__main__":
    main()
