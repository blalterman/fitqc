# JOSS Paper Materials

This directory contains supporting materials for the fitqc JOSS (Journal of Open Source Software) submission.

## Contents

### JOSS Paper Materials

| Document | Purpose |
|----------|---------|
| [statement-of-need.md](statement-of-need.md) | Foundation for JOSS "Statement of Need" section |
| [competitive-analysis.md](competitive-analysis.md) | Detailed comparison with existing Python packages |
| [related-work.md](related-work.md) | Citations and relationship to prior work |

## Document Summaries

### Statement of Need

Describes the core problem fitqc solves:
- Silent optimizer failures in bootstrap/MC fitting
- Two failure modes: x0 stickiness and boundary pileup
- Target audience (physics research, uncertainty quantification)
- The ecosystem gap and fitqc's solution

### Competitive Analysis

Comprehensive survey of related Python packages:
- MCMC diagnostics (ArviZ, emcee, mcmc-diagnostics)
- Fitting libraries (lmfit, iminuit, pyhf, scipy.optimize)
- Bootstrap tools (scipy.stats.bootstrap, arch)
- Outlier detection (scikit-learn)

Key finding: **No existing package detects optimizer stickiness in fitted parameter distributions.**

### Related Work

Citable references organized by category:
- Python packages with DOIs
- R packages (coda, boot)
- Statistical methods (R-hat, ESS, Kneedle)
- Physics context and practices

## Using These Documents

### For JOSS Paper

1. **Statement of Need section**: Adapt from `statement-of-need.md`
2. **Related Work section**: Use citations from `related-work.md`
3. **Differentiation claims**: Support with `competitive-analysis.md`

### For README/Documentation

The "ecosystem gap" table from `competitive-analysis.md` is suitable for the main README to quickly communicate fitqc's unique value.

## Research Date

This analysis was conducted in January 2025. Package versions and features should be verified before JOSS submission.
