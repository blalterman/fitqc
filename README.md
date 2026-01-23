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

## Understanding Filter Terminology

**Important**: fitqc's filter visualization terminology can be confusing. Here's what each filter actually does:

### Three Types of Problematic Samples

```
Parameter Space: [L=0 ────────────── x0=2.5 ──────────────── U=25]

1. Out-of-Bounds (Invalid):
   ←←← x<L │                                                 │ x>U →→→
   Removed by: "Boundary Filter" or "Bounds Filter"

2. Boundary-Sticky (Fit Limit Stickiness):
   ←─ near L ─→│                                         │←─ near U ─→
   Detected by: run_boundary_qc()
   Removed by: "Combined Filter" (uses detected thresholds)

3. x0-Sticky (Initial Guess Stickiness):
                            ←─ near x0 ─→
   Detected by: run_interior_qc()
   Removed by: "Interior Filter"
```

### Filter Comparison Visualizations

When you see filter comparison plots (e.g., `plot_combined_filter_comparison()`):

**Panel 1: Original Data**
- All samples, including all three types of problems above

**Panel 2: "Boundary Filter Only"**
- **Removes**: Out-of-bounds samples (x < L or x > U)
- **⚠️ Does NOT remove boundary spikes!** Despite the name, this only validates bounds
- **For datasets with all x ∈ [L, U]**: This panel looks identical to Panel 1

**Panel 3: "Interior Filter Only"**
- **Removes**: x0-sticky samples (too close to initial guess)
- **⚠️ Name is confusing!** "Interior" refers to the interior point (x0), not the interior region
- **Better mental model**: "Initial guess filter"

**Panel 4: "Combined Filters"**
- **Removes ALL THREE types**:
  1. Out-of-bounds (x < L or x > U)
  2. Boundary-sticky (detected by `run_boundary_qc()`)
  3. x0-sticky (detected by `run_interior_qc()`)
- **This is where boundary spikes disappear!**

### Common Confusion Explained

**Q: "Why do I still see boundary spikes in Panel 2 (Boundary Filter)?"**

A: Because the "Boundary Filter" only removes **out-of-bounds** samples (x < L or x > U), not **boundary-sticky** samples (too close to L or U). The boundary spikes you see are samples AT or NEAR the boundaries, which are valid values within [L, U].

Boundary stickiness is only filtered in Panel 4 (Combined Filter), which applies the thresholds detected by `run_boundary_qc()`.

**Q: "What's the difference between boundary stickiness and out-of-bounds?"**

- **Out-of-bounds**: x < L or x > U (invalid, shouldn't exist)
  - Example: x = -0.5 when L = 0.0
  - Indicates: Failed fits, numerical errors

- **Boundary-sticky**: x very close to L or U (valid but suspicious)
  - Example: x = 0.001 when L = 0.0, U = 25.0
  - Indicates: Optimizer got stuck at constraints

**Q: "What does `run_boundary_qc()` actually do?"**

A: It **detects** boundary stickiness (samples clustering near L or U), but it doesn't filter the data itself. The detected thresholds (`t_lo_star`, `t_hi_star`) are used by the combined filter visualization to remove boundary-sticky samples.

### Naming Rationale

The current names reflect the underlying detection modules:
- **"Boundary"** terminology → Code in `boundary.py` module (detects pileup at L/U)
- **"Interior"** terminology → Code in `interior.py` module (detects spike at x0)

However, this can be counter-intuitive when thinking about what gets filtered. We maintain these names to align with scientific computing conventions where "boundary" refers to the bounds of the valid parameter domain.

### Quick Reference

| What You Want to Do | Use This Function | What It Detects/Removes |
|---------------------|-------------------|-------------------------|
| Detect boundary pileup at L or U | `run_boundary_qc()` | Boundary stickiness |
| Detect spike at x0 | `run_interior_qc()` | Initial guess stickiness |
| Visualize out-of-bounds removal | `plot_bounds_filter_comparison()` | x < L or x > U |
| Visualize x0 stickiness removal | `plot_interior_filter_comparison()` | Samples near x0 |
| Visualize all filtering | `plot_combined_filter_comparison()` | All three types |

For more details, see the [complete filter taxonomy documentation](COMPLETE_FILTER_TAXONOMY.md).

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
