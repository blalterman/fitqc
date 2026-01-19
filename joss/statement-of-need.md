# Statement of Need: fitqc

This document provides the foundation for the JOSS paper's "Statement of Need" section.

## The Problem

When fitting models to data using bootstrap resampling, Monte Carlo methods, or repeated optimization, optimizers can fail silently by getting "stuck" in predictable ways:

1. **Initial-Guess Stickiness**: The optimizer returns the starting point (x0) without meaningful iteration, often because:
   - The cost function is locally flat
   - Numerical precision issues prevent gradient computation
   - The optimizer hits iteration limits before moving

2. **Boundary Stickiness**: Fitted values accumulate abnormally at parameter bounds, indicating:
   - Overly restrictive constraints
   - Model-data mismatch
   - Pathological likelihood surfaces

These failures are **silent**—the optimizer returns "converged" status with plausible-looking values. Without explicit detection, invalid samples contaminate the fitted parameter distribution, corrupting all downstream statistical inferences.

## Who Needs This

### Primary Audience: Physics Research

Bootstrap fitting at scale is routine in physics:

- **Particle Physics**: Fitting detector response functions, extracting cross-sections, systematic uncertainty estimation
- **Astrophysics**: Spectral fitting, photometric redshift estimation, light curve analysis
- **Materials Science**: Fitting diffraction patterns, spectroscopic analysis

These workflows commonly involve:
- 10³–10⁶ bootstrap or Monte Carlo fits
- Bounded parameters (physical constraints like positivity)
- Complex likelihood surfaces with local minima
- High-stakes statistical claims requiring valid uncertainty quantification

### Secondary Audience: General Uncertainty Quantification

Anyone performing bootstrap uncertainty estimation with bounded optimization:
- Econometrics with constrained parameters
- Biostatistics with physical bounds
- Engineering reliability analysis

## The Gap in Current Tools

### What Exists

| Tool Category | Examples | What They Do |
|--------------|----------|--------------|
| MCMC Diagnostics | ArviZ, emcee | Diagnose chain convergence |
| Fitting Libraries | lmfit, iminuit, scipy.optimize | Perform optimization |
| Bootstrap Tools | scipy.stats.bootstrap | Generate resampled datasets |

### What's Missing

**No existing package answers**: "Did my optimizer fail silently on some bootstrap samples, and which samples should I exclude?"

Current practice:
- Researchers write ad-hoc detection code
- Tolerance thresholds are chosen arbitrarily
- Detection logic is not reproducible across projects
- Edge cases (e.g., distributions naturally near x0) cause false positives

## What fitqc Provides

### Core Capabilities

1. **X0 Spike Detection**: Identifies samples where the optimizer returned near the initial guess
   - Uses histogram + `scipy.signal.find_peaks` with width/prominence criteria
   - Distinguishes genuine stickiness from natural distribution variation
   - Critical for signed log-normal distributions that naturally concentrate near zero

2. **Boundary Pileup Detection**: Identifies abnormal accumulation at parameter bounds
   - Independent analysis of lower and upper bounds
   - Elbow-based threshold selection (no arbitrary tolerances)
   - Returns interpretable thresholds (e.g., "5% of mass within 1% of lower bound")

3. **Per-Sample Filtering**: Boolean masks for excluding invalid samples
   - Combine masks across parameters: `good = mask_alpha & mask_beta`
   - Clean distributions for downstream analysis

4. **Reproducible Diagnostics**: Full diagnostic output in JSON-serializable format
   - All thresholds and intermediate quantities preserved
   - Version-controllable QC decisions

### Design Principles

- **Arrays-only**: Pure NumPy/SciPy, no heavy dependencies
- **Scale**: Optimized for 10⁶+ samples (sort-once, searchsorted efficiency)
- **Transparency**: All intermediate diagnostics exposed for inspection
- **Reproducibility**: Seeded generators, explicit configuration, JSON export

## Differentiating Features

### Spike Detection Innovation

Existing approaches (if implemented at all) use simple distance thresholds:
```python
# Naive approach (problematic)
stuck = np.abs(x - x0) < tolerance
```

**Problem**: Distributions like signed log-normal naturally concentrate near x0 when x0 ≈ 0. This causes massive false positive rates.

**fitqc's solution**:
1. Transform to z-space: `z = |x - x0| / max(x0 - L, U - x0)`
2. Build histogram of z values
3. Use `find_peaks` with **width criterion** to detect narrow spikes
4. Reject broad concentrations (natural variation) vs narrow spikes (stickiness)

### Elbow-Based Threshold Selection

Rather than arbitrary tolerances, fitqc uses the kneed library to find natural breakpoints in cumulative mass curves:
- Test multiple quantile grids (1%, 5%, 10%, 25%, 50%)
- Find elbow point where mass accumulation changes character
- Return data-driven threshold with statistical meaning

## Impact

### Without fitqc
- Silent optimizer failures go undetected
- Invalid samples corrupt uncertainty estimates
- Confidence intervals have wrong coverage
- Statistical claims are unreliable

### With fitqc
- Systematic detection of optimizer failure modes
- Reproducible sample filtering
- Valid parameter distributions for inference
- Auditable QC decisions

## Summary

fitqc addresses a genuine gap in the Python scientific computing ecosystem. While tools exist for MCMC diagnostics, curve fitting, and bootstrap resampling, none provide automated detection and filtering of optimizer stickiness in fitted parameter distributions. This silent failure mode is well-known in physics research communities but has no standardized solution, leading to ad-hoc, non-reproducible workarounds. fitqc provides a principled, efficient, and reproducible approach to this problem.
