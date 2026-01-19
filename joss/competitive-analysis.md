# Competitive Analysis: fitqc in the Python Ecosystem

This document analyzes existing Python packages related to fitqc's functionality and identifies the ecosystem gap that fitqc addresses. This analysis supports the "Statement of Need" section of the JOSS paper.

## Executive Summary

**fitqc fills a genuine gap in the Python ecosystem.** While numerous packages exist for MCMC diagnostics, curve fitting, and bootstrap resampling, none provide automated detection of optimizer stickiness—the silent failure mode where optimizers get "stuck" at initial guesses or parameter bounds during repeated fitting operations.

---

## Existing Package Categories

### 1. MCMC Diagnostics Packages

These packages diagnose whether Markov chains have converged to the target distribution.

#### ArviZ
- **Repository**: https://github.com/arviz-devs/arviz
- **PyPI**: https://pypi.org/project/arviz/
- **Focus**: Exploratory analysis of Bayesian models
- **Key Features**:
  - R-hat (Gelman-Rubin) convergence diagnostic
  - Effective Sample Size (ESS) estimation
  - Leave-One-Out Cross Validation (LOO-CV)
  - Backend-agnostic (PyMC, Stan, Pyro, emcee)
- **Gap vs fitqc**: Diagnoses chain convergence, not optimizer failure modes. Assumes samples are valid once chains converge.

#### mcmc-diagnostics
- **Repository**: https://github.com/aki-nishimura/mcmc-diagnostics
- **PyPI**: https://pypi.org/project/mcmc-diagnostics/
- **Focus**: Python analogue of R's coda package
- **Key Features**:
  - Integrated autocorrelation time estimation
  - ESS computation
- **Gap vs fitqc**: Focused on MCMC chain quality, not on detecting stuck optimizer iterations in bootstrap fitting.

#### emcee (autocorrelation module)
- **Repository**: https://github.com/dfm/emcee
- **Documentation**: https://emcee.readthedocs.io/en/stable/tutorials/autocorr/
- **Focus**: Affine-invariant ensemble MCMC sampler
- **Key Features**:
  - `integrated_time()` function for autocorrelation analysis
  - `AutocorrError` when chains are too short
  - Rule of thumb: chain length >> 50 × τ
- **Gap vs fitqc**: Detects insufficient chain length, not systematic optimizer stickiness patterns.

#### autoemcee
- **Documentation**: https://johannesbuchner.github.io/autoemcee/
- **Focus**: Automatic chain extension until convergence
- **Key Features**:
  - Wraps emcee and zeus samplers
  - Automatically extends chains until convergence criteria met
- **Gap vs fitqc**: Ensures adequate sampling, but doesn't filter samples where optimizer failed.

### 2. Curve Fitting Packages

These packages perform optimization to fit models to data.

#### lmfit
- **Repository**: https://github.com/lmfit/lmfit-py
- **PyPI**: https://pypi.org/project/lmfit/
- **Documentation**: https://lmfit.github.io/lmfit-py/
- **Focus**: Non-linear least-squares minimization and curve-fitting
- **Key Features**:
  - Parameter bounds and constraints
  - Covariance-based uncertainty estimation
  - Confidence interval calculation via `conf_interval()`
  - Optional emcee integration for Bayesian posteriors
- **Gap vs fitqc**: Provides uncertainty for single fits. Does not validate distributions from bootstrap resampling. Notes in documentation: "each variable Parameter must actually change the fit, and cannot be stuck at an initial value or at a boundary value"—acknowledges the problem but doesn't detect it.

#### iminuit
- **Repository**: https://github.com/scikit-hep/iminuit
- **PyPI**: https://pypi.org/project/iminuit/
- **Documentation**: https://scikit-hep.org/iminuit/
- **Focus**: Python interface to CERN's MINUIT2 optimizer
- **Key Features**:
  - MIGRAD minimizer
  - HESSE and MINOS error estimation
  - Parameter limits support
  - Interactive fitting in Jupyter
- **Gap vs fitqc**: Provides profile likelihood errors for single fits. When running bootstrap fits, does not detect or filter stuck samples.

#### pyhf
- **Repository**: https://github.com/scikit-hep/pyhf
- **Documentation**: https://pyhf.readthedocs.io/
- **Focus**: HistFactory-style binned statistical analysis
- **Key Features**:
  - Pure Python implementation
  - Multiple backends (NumPy, PyTorch, TensorFlow, JAX)
  - Asymptotic formulae for limit setting
- **Gap vs fitqc**: Focused on hypothesis testing and limit setting, not on validating bootstrap parameter distributions.

#### zfit
- **Repository**: https://github.com/zfit/zfit
- **Focus**: Scalable fitting library based on TensorFlow
- **Key Features**:
  - GPU acceleration
  - Automatic differentiation
  - Composable PDFs
- **Gap vs fitqc**: Performs fitting, doesn't validate fitted distributions.

### 3. Bootstrap/Resampling Packages

These packages provide resampling functionality.

#### scipy.stats.bootstrap
- **Documentation**: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html
- **Focus**: Bootstrap confidence intervals
- **Key Features**:
  - BCa, percentile, and basic bootstrap methods
  - Vectorized bootstrap computation
- **Gap vs fitqc**: General-purpose resampling. No fitting-specific diagnostics or quality control.

#### scikit-learn resample
- **Documentation**: https://scikit-learn.org/stable/modules/generated/sklearn.utils.resample.html
- **Focus**: Basic resampling utility
- **Gap vs fitqc**: Just performs resampling, no diagnostics.

#### arch (bootstrap module)
- **Repository**: https://github.com/bashtage/arch
- **Focus**: Bootstrap methods for dependent data (time series)
- **Key Features**:
  - Stationary bootstrap
  - Block bootstrap
  - Circular block bootstrap
- **Gap vs fitqc**: Handles temporal dependence in resampling, but no fitting QC.

### 4. General Outlier Detection

#### scikit-learn outlier detection
- **Documentation**: https://scikit-learn.org/stable/modules/outlier_detection.html
- **Focus**: Novelty and outlier detection
- **Key Features**:
  - Isolation Forest
  - Local Outlier Factor
  - One-Class SVM
  - Elliptic Envelope
- **Gap vs fitqc**: General-purpose outlier detection. Not designed for the specific failure modes of optimizer stickiness (x0 spikes, boundary pileup).

---

## Known Problems Without Packaged Solutions

### Parameter-at-Boundary Issues

The problem of optimizers getting stuck at boundaries is well-documented but has no packaged solution:

1. **Stan Issue #1928**: "Optimizing seems to get stuck at boundaries, dependent on seed"
   - https://github.com/stan-dev/stan/issues/1928
   - Optimization can terminate after 2 iterations with all parameters at boundaries
   - Convergence message says "gradient norm is below tolerance" (false convergence)

2. **SciPy Issue #11403**: "Optimize raises ValueError for parameters within bounds"
   - https://github.com/scipy/scipy/issues/11403
   - x0 can be modified during Jacobian calculation, causing bound violations

3. **SciPy Issue #3056**: "SLSQP leads to out of bounds solution"
   - https://github.com/scipy/scipy/issues/3056
   - SLSQP can go to infinity when local gradient is near zero

### Current Workarounds

Users currently write ad-hoc code to detect these issues:

```python
# Typical ad-hoc boundary check (insufficient)
def check_params_at_bounds(result, bounds, tol=1e-6):
    at_lower = np.abs(result.x - bounds[:, 0]) < tol
    at_upper = np.abs(result.x - bounds[:, 1]) < tol
    return at_lower | at_upper
```

**Problems with ad-hoc approaches**:
- No statistical criterion for choosing tolerance
- No detection of x0 stickiness
- No handling of natural distributions that concentrate near boundaries
- Not reproducible across projects

---

## Ecosystem Gap Summary

| Capability | MCMC Tools | Fitting Tools | Bootstrap Tools | fitqc |
|------------|-----------|---------------|-----------------|-------|
| Chain convergence (R-hat) | ✓ | — | — | — |
| Effective sample size | ✓ | — | — | — |
| Single-fit uncertainty | — | ✓ | — | — |
| Bootstrap resampling | — | — | ✓ | — |
| X0 spike detection | — | — | — | ✓ |
| Boundary pileup detection | — | — | — | ✓ |
| Per-sample filtering masks | — | — | — | ✓ |
| Elbow-based threshold selection | — | — | — | ✓ |
| Handles signed log-normal | — | — | — | ✓ |

---

## Why This Gap Exists

1. **Domain-Specific Problem**: Bootstrap fitting at scale is most common in physics (particle physics, astrophysics, materials science) where millions of fits are routine. The broader Python data science community favors MCMC approaches.

2. **Silent Failures**: Optimizers don't crash—they return "converged" status with invalid results. Without explicit checks, these failures go undetected.

3. **Downstream Corruption**: Invalid samples corrupt all downstream analyses:
   - Biased uncertainty estimates
   - Invalid confidence intervals
   - Compromised hypothesis tests
   - Wrong coverage in frequentist inference

4. **No Standardization**: Each research group writes custom detection code, leading to:
   - Inconsistent quality across projects
   - Non-reproducible preprocessing
   - Knowledge trapped in unpublished scripts

---

## References

- Kumar, R., Carroll, C., Hartikainen, A., & Martin, O. (2019). ArviZ a unified library for exploratory analysis of Bayesian models in Python. Journal of Open Source Software, 4(33), 1143.
- Foreman-Mackey, D., Hogg, D. W., Lang, D., & Goodman, J. (2013). emcee: The MCMC Hammer. Publications of the Astronomical Society of the Pacific, 125(925), 306.
- Newville, M., et al. (2014). LMFIT: Non-Linear Least-Square Minimization and Curve-Fitting for Python. Zenodo.
- Dembinski, H., et al. (2020). scikit-hep/iminuit. Zenodo.
