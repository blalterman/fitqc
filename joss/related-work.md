# Related Work

This document catalogs packages and publications related to fitqc's functionality, supporting the JOSS paper's related work discussion.

## Python Packages

### MCMC Diagnostics

#### ArviZ
- **Citation**: Kumar, R., Carroll, C., Hartikainen, A., & Martin, O. (2019). ArviZ a unified library for exploratory analysis of Bayesian models in Python. *Journal of Open Source Software*, 4(33), 1143. https://doi.org/10.21105/joss.01143
- **Repository**: https://github.com/arviz-devs/arviz
- **Relationship**: Complementary. ArviZ diagnoses MCMC chain convergence; fitqc diagnoses optimizer stickiness in bootstrap/MC fitting. Could be used together when MCMC is used for uncertainty estimation.

#### emcee
- **Citation**: Foreman-Mackey, D., Hogg, D. W., Lang, D., & Goodman, J. (2013). emcee: The MCMC Hammer. *Publications of the Astronomical Society of the Pacific*, 125(925), 306-312. https://doi.org/10.1086/670067
- **Repository**: https://github.com/dfm/emcee
- **Relationship**: Complementary. emcee's autocorrelation analysis ensures adequate chain length; fitqc would detect if the underlying optimizer (used in likelihood evaluation) exhibits stickiness.

#### mcmc-diagnostics
- **Repository**: https://github.com/aki-nishimura/mcmc-diagnostics
- **Relationship**: Similar goals (sample quality), different domain (MCMC vs bootstrap).

### Fitting Libraries

#### lmfit
- **Citation**: Newville, M., Stensitzki, T., Allen, D. B., & Ingargiola, A. (2014). LMFIT: Non-Linear Least-Square Minimization and Curve-Fitting for Python. *Zenodo*. https://doi.org/10.5281/zenodo.11813
- **Repository**: https://github.com/lmfit/lmfit-py
- **Relationship**: Upstream. lmfit performs fitting; fitqc validates distributions from repeated lmfit fits.

#### iminuit
- **Citation**: Dembinski, H., et al. (2020). scikit-hep/iminuit. *Zenodo*. https://doi.org/10.5281/zenodo.3949207
- **Repository**: https://github.com/scikit-hep/iminuit
- **Relationship**: Upstream. iminuit (MINUIT2) is widely used in physics fitting; fitqc validates bootstrap distributions from iminuit fits.

#### scipy.optimize
- **Documentation**: https://docs.scipy.org/doc/scipy/reference/optimize.html
- **Relationship**: Upstream. scipy.optimize provides the minimizers; fitqc detects when they fail silently.

### Bootstrap/Resampling

#### scipy.stats.bootstrap
- **Documentation**: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html
- **Relationship**: Complementary. scipy.stats.bootstrap generates resampled datasets; fitqc validates the fitted parameters from those resamples.

#### arch
- **Repository**: https://github.com/bashtage/arch
- **Relationship**: Parallel. arch provides bootstrap methods for time series; fitqc could validate fitted parameters from arch bootstrap procedures.

### Threshold Detection

#### kneed
- **Citation**: Satopaa, V., Albrecht, J., Irwin, D., & Raghavan, B. (2011). Finding a "Kneedle" in a Haystack: Detecting Knee Points in System Behavior. *31st International Conference on Distributed Computing Systems Workshops*.
- **Repository**: https://github.com/arvkevi/kneed
- **Relationship**: Dependency. fitqc uses kneed for elbow detection in mass curves.

## R Packages

### coda
- **Citation**: Plummer, M., Best, N., Cowles, K., & Vines, K. (2006). CODA: Convergence Diagnosis and Output Analysis for MCMC. *R News*, 6(1), 7-11.
- **Relationship**: Inspiration. coda provides comprehensive MCMC diagnostics for R; mcmc-diagnostics is a partial Python port. fitqc addresses a different problem (optimizer stickiness vs chain convergence).

### boot
- **Citation**: Canty, A., & Ripley, B. D. (2021). boot: Bootstrap Functions. R package.
- **Relationship**: Ecosystem gap. R's boot package is comprehensive for bootstrap analysis; Python lacks an equivalent, and fitqc partially addresses this gap for the specific case of fitting QC.

## Statistical Methods

### Convergence Diagnostics

#### Gelman-Rubin Statistic (R-hat)
- **Citation**: Gelman, A., & Rubin, D. B. (1992). Inference from Iterative Simulation Using Multiple Sequences. *Statistical Science*, 7(4), 457-472.
- **Relationship**: Different problem. R-hat diagnoses whether multiple chains have converged to the same distribution; fitqc detects whether individual optimization runs succeeded.

#### Effective Sample Size
- **Citation**: Geyer, C. J. (1992). Practical Markov Chain Monte Carlo. *Statistical Science*, 7(4), 473-483.
- **Relationship**: Related concept. ESS quantifies independent information in correlated samples; fitqc identifies samples that should be excluded entirely.

### Elbow/Knee Detection

#### Kneedle Algorithm
- **Citation**: Satopaa, V., Albrecht, J., Irwin, D., & Raghavan, B. (2011). Finding a "Kneedle" in a Haystack: Detecting Knee Points in System Behavior.
- **Relationship**: Core method. fitqc uses the Kneedle algorithm (via kneed package) to find optimal thresholds in cumulative mass curves.

### Peak Detection

#### scipy.signal.find_peaks
- **Documentation**: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
- **Relationship**: Core method. fitqc uses find_peaks with width and prominence criteria to detect x0 stickiness spikes while rejecting natural distribution variation.

## Physics Context

### Bootstrap in Particle Physics
- Common practice: Generate O(10³-10⁶) bootstrap samples, fit each, use distribution for uncertainty
- Known issue: Optimizer failures at bounds or initial guess
- Current solution: Ad-hoc filtering, often undocumented

### Profile Likelihood
- **Citation**: Wilks, S. S. (1938). The Large-Sample Distribution of the Likelihood Ratio for Testing Composite Hypotheses. *The Annals of Mathematical Statistics*, 9(1), 60-62.
- **Relationship**: Alternative approach. Profile likelihood (implemented in iminuit's MINOS) provides single-fit confidence intervals without bootstrap. fitqc is relevant when bootstrap is preferred or required.

## Key Differentiators from All Related Work

| Aspect | Related Work | fitqc |
|--------|-------------|-------|
| Target | MCMC chains OR single fits | Bootstrap/MC parameter distributions |
| Failure mode | Chain non-convergence | Optimizer stickiness |
| Detection | R-hat, ESS, autocorrelation | Spike detection, pileup detection |
| Output | Convergence diagnostics | Per-sample boolean masks |
| Threshold | Often arbitrary or rule-of-thumb | Data-driven (elbow detection) |
| Edge cases | Not specifically handled | Width criterion for natural variation |
