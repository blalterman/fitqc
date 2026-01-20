# fitqc

[![CI](https://github.com/blalterman/fitqc/actions/workflows/ci.yml/badge.svg)](https://github.com/blalterman/fitqc/actions/workflows/ci.yml)
[![Documentation](https://readthedocs.org/projects/fitqc/badge/?version=latest)](https://fitqc.readthedocs.io/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20|%203.12%20|%203.13-blue.svg)](https://www.python.org/downloads/)
[![License: BSD-3-Clause](https://img.shields.io/badge/license-BSD--3--Clause-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)

Fit QC diagnostics for detecting optimizer stickiness in fitted parameters.

## Overview

When fitting models to data using bootstrap, MCMC, or Monte Carlo methods, optimizers can get "stuck" in two ways:

1. **Boundary stickiness** — Fitted values pile up at parameter bounds (L or U)
2. **Initial-guess stickiness** — Fitted values cluster at the initial guess (x0)

`fitqc` provides automated detection of these issues across multiple parameters, with diagnostic plots and JSON-serializable reports.

## Installation

```bash
pip install fitqc
```

For development:
```bash
pip install -e ".[dev]"
pre-commit install
```

## Quick Start

```python
from fitqc import run_qc, QCSpec

# Your fitted parameter samples (e.g., from 10,000 bootstrap fits)
params = {
    "alpha": alpha_samples,  # shape (10000,)
    "beta": beta_samples,    # shape (10000,)
}

# Define the parameter specification
spec = QCSpec(
    param_names=["alpha", "beta"],
    x0={"alpha": 1.0, "beta": 2.0},           # Initial guesses
    bounds={"alpha": (0.0, 10.0), "beta": (-5.0, 5.0)},  # Bounds
)

# Run QC
report, masks = run_qc(params, spec)

# Check results
for name in spec.param_names:
    if report.interior_results[name].spike_detected:
        print(f"{name}: x0 stickiness detected!")
    if report.boundary_results[name].lower_pileup_detected:
        print(f"{name}: lower bound pileup detected!")

# Filter to good samples only
combined_mask = masks["alpha"] & masks["beta"]
clean_alpha = params["alpha"][combined_mask]
clean_beta = params["beta"][combined_mask]

# Save report to JSON
with open("qc_report.json", "w") as f:
    f.write(report.to_json(indent=2))
```

## How It Works

### Interior QC (x0 Stickiness)

Detects samples clustered at the initial guess using:
1. Normalize distances from x0: `z = |x - x0| / (U - L)`
2. Build histogram of z-values
3. Detect narrow spike at z ≈ 0 using `scipy.signal.find_peaks`
4. Select detection threshold (eps*) via elbow detection

### Boundary QC (Pileup)

Detects samples clustered at bounds using:
1. Normalize positions: `u = (x - L) / (U - L)`
2. Compute cumulative mass near boundaries
3. Detect excess mass via elbow detection
4. Independent thresholds for lower (t_lo*) and upper (t_hi*)

## API Reference

### Configuration

```python
from fitqc import QCSpec, InteriorConfig, BoundaryConfig

# Required: Parameter specification
spec = QCSpec(
    param_names=["alpha", "beta"],
    x0={"alpha": 1.0, "beta": 2.0},
    bounds={"alpha": (0.0, 10.0), "beta": (-5.0, 5.0)},
)

# Optional: Customize detection parameters
interior_config = InteriorConfig(
    n_bins=100,      # Histogram bins
    n_eps=50,        # Epsilon grid points
)

boundary_config = BoundaryConfig(
    n_tols=41,       # Tolerance grid points
    tol_max=0.05,    # Maximum tolerance to check
)
```

### Core Functions

```python
from fitqc import run_qc, run_interior_qc, run_boundary_qc

# High-level API (recommended)
report, masks = run_qc(params, spec, interior_config, boundary_config)

# Low-level API
interior_result = run_interior_qc(x, x0, L, U, config)
boundary_result = run_boundary_qc(x, L, U, config)
```

### Results

```python
# Interior result
result.spike_detected    # bool: Was a spike detected?
result.eps_star          # float: Detection threshold (None if not detected)
result.spike_z_loc       # float: Location of spike in z-space

# Boundary result
result.lower_pileup_detected  # bool
result.upper_pileup_detected  # bool
result.t_lo_star              # float: Lower threshold
result.t_hi_star              # float: Upper threshold

# Masks
masks["alpha"]  # bool array: True = good sample, False = stuck sample
```

### Plotting

```python
from fitqc import (
    plot_interior_diagnostics,
    plot_boundary_diagnostics,
    plot_histogram_tolerance_overlays,
    plot_ecdf_tolerance_overlays,
    plot_quantile_spacing_overlays,
    PlotConfig,
)

# Basic diagnostic plots
fig = plot_interior_diagnostics(interior_result, PlotConfig())
fig = plot_boundary_diagnostics(boundary_result, PlotConfig())

# Tolerance-overlay visualizations (for understanding boundary detection)
fig = plot_histogram_tolerance_overlays(x, L=0, U=10)
fig = plot_ecdf_tolerance_overlays(u, side='both')
fig = plot_quantile_spacing_overlays(np.sort(x), L=0, U=10)
```

## Examples

### Complete Workflows

- **`examples/run_array_qc.py`** — Full QC pipeline: generate data, run QC, filter samples
- **`examples/plot_tolerance_overlays.py`** — Tolerance-overlay visualizations for boundary diagnostics

### Tolerance-Overlay Visualizations

The tolerance-overlay functions help you understand how different tolerance thresholds affect boundary pile-up detection:

```python
from fitqc.plot import (
    plot_histogram_tolerance_overlays,
    plot_ecdf_tolerance_overlays,
    plot_quantile_spacing_overlays,
)

# Show histograms with varying boundary cuts
fig = plot_histogram_tolerance_overlays(x, L=0, U=10, tols=np.linspace(0, 0.05, 7))

# Show ECDF changes near boundaries
u = (x - L) / (U - L)
fig = plot_ecdf_tolerance_overlays(u, side='both')

# Show quantile spacing compression (indicates pile-up)
fig = plot_quantile_spacing_overlays(np.sort(x), L=0, U=10)
```

Run `python examples/plot_tolerance_overlays.py` to see these in action.

## Requirements

- Python ≥ 3.11
- NumPy ≥ 1.24
- SciPy ≥ 1.10
- Matplotlib ≥ 3.6
- kneed ≥ 0.8

## License

BSD-3-Clause
