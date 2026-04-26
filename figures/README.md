# Figures Directory Organization

This directory contains visualization outputs organized by dataset.

## Structure

```
figures/
├── A_He/                    # Alpha particle abundance (helium)
├── e_dv_ap/                 # Electric field drift velocity (anti-parallel)
├── e_dv_pp/                 # Electric field drift velocity (parallel)
├── np1/                     # Beam density 1
├── np2/                     # Beam density 2
├── w_const/                 # Thermal speed (constant)
└── README.md                # This file
```

## File Naming Conventions

### Standard vs High-Resolution
- `<name>.png` - Standard resolution (150 DPI) for quick viewing
- `<name>_hires.png` - High resolution (300 DPI) for publication/detailed analysis

### Analysis Types

#### Filter Comparison Plots
- `<dataset>_bounds_filter_comparison*.png` - Before/after bounds filtering (removes out-of-bounds samples)
- `<dataset>_interior_filter_comparison*.png` - Before/after interior filtering (removes x0-stuck samples)
- `<dataset>_combined_filter_comparison*.png` - Combined view of both filters (2x2 grid)

#### Comprehensive Analysis
- `<dataset>_filtering_audit*.png` - 6-panel diagnostic showing filtering verification
- `<dataset>_improved_analysis*.png` - **Latest comprehensive analysis** (12-panel for A_He, varies by dataset)
- `<dataset>_ultrahighres_analysis*.png` - Earlier 9-panel ultra-high-res version (superseded by improved_analysis)
- `<dataset>_highres_histogram_analysis*.png` - Dataset-specific high-resolution histograms
- `<dataset>_detailed_analysis*.png` - Dataset-specific detailed analysis

## Datasets Overview

### A_He (12 files)
- **Parameter**: Alpha particle abundance (helium nuclei fraction)
- **Bounds**: L=0.0, U=25.0
- **Stickiness**: Lower boundary (1.84% within u<0.01)
- **Out-of-bounds**: None
- **Latest plot**: `improved_analysis_hires.png` (12-panel: histograms + CDFs)

### e_dv_ap (6 files)
- **Parameter**: Electric field drift velocity (anti-parallel component)
- **Bounds**: L=-150.0, U=150.0
- **Stickiness**: TBD
- **Out-of-bounds**: None

### e_dv_pp (6 files)
- **Parameter**: Electric field drift velocity (parallel component)
- **Bounds**: L=-75.0, U=75.0
- **Stickiness**: Lower boundary detected
- **Out-of-bounds**: None
- **Special**: Shows wider interior spike pattern (multi-bin width)

### np1 (4 files)
- **Parameter**: Beam density 1
- **Bounds**: L=0.01, U=100.0
- **Stickiness**: Lower boundary detected
- **Out-of-bounds**: 16,695 samples (1.67%) - failed fits at x=0.0

### np2 (2 files)
- **Parameter**: Beam density 2
- **Bounds**: L=0.01, U=100.0
- **Stickiness**: EXTREME lower boundary (57.81% within u<0.01)
- **Out-of-bounds**: 2,083 samples (2.08%) - failed fits at x=0.0
- **Critical**: Metadata error (should be `expected_lower_stickiness: true`)

### w_const (2 files)
- **Parameter**: Thermal speed (constant)
- **Bounds**: L=5.0, U=150.0
- **Stickiness**: Upper boundary detected
- **Out-of-bounds**: 1,528 samples (1.53%) - failed fits at x=0.0

## Key Visualizations

### For Understanding Boundary Stickiness
1. **Start with**: `<dataset>_improved_analysis_hires.png` (if available)
   - Comprehensive 12-panel view (histograms + CDFs)
   - Log-scale zooms on boundary regions
   - Shows both raw and normalized (u-space) coordinates

2. **For filtering verification**: `<dataset>_filtering_audit_hires.png`
   - 6-panel diagnostic showing filtering correctness
   - Includes algorithm-detected thresholds (t*)
   - Verifies x-space vs u-space filtering equivalence

3. **For detailed concentration analysis**: `<dataset>_highres_histogram_analysis_hires.png`
   - 1000-bin resolution histograms
   - Bin-to-bin ratio analysis
   - Exponential decay pattern visualization

### Panel Descriptions (improved_analysis 12-panel layout)

**Row 1: Raw X-Space**
1. Full range (2000 bins, linear scale)
2. Full range (2000 bins, LOG scale)
3. Near lower boundary zoom (LOG scale)

**Row 2: U-Space Normalized**
4. Full range (2000 bins, linear scale)
5. Full range (2000 bins, LOG scale)
6. Near lower boundary zoom (u<0.02, LOG scale)

**Row 3: Boundary Details + CDFs**
7. Near upper boundary zoom (u>0.98, LOG scale)
8. CDF - Lower boundary zoom (u ∈ [0, 0.2])
9. CDF - Upper boundary zoom (u ∈ [0.8, 1.0])

**Row 4: Complete View + Summary**
10. CDF - Full range [0, 1]
11. Summary statistics (left column)
12. Concentration analysis (right column)

## Z-Order Rendering

All plots use proper z-order to ensure visibility:
- **Grid**: z=0 (background, behind everything)
- **Reference lines** (axvline, axhline): z=1 (below data)
- **Histogram bars/CDF lines**: z=2 (on top, always visible)

This ensures reference lines don't obscure data spikes.

## File Sizes

Total: ~9.6 MB across 32 files
- Standard resolution (~100-400 KB each)
- High resolution (~200-1100 KB each)

## Related Documentation

- `../A_HE_PANEL_EXPLANATION.md` - Detailed explanation of A_He 12-panel layout
- `../FILTERING_AUDIT_REPORT.md` - Comprehensive filtering verification report
- `../TEST_QUALITY_ANALYSIS.md` - Test quality assessment

## Regenerating Plots

To regenerate plots:
```bash
# Individual dataset high-res analysis
python plot_A_He_improved.py

# High-res analysis for np2 and w_const
python plot_np2_highres.py
python plot_w_const_detailed.py

# Filtering audit for any dataset
python audit_filtering.py  # Edit dataset_name variable

# All filter comparison plots
python -c "from fitqc.plot import plot_bounds_filter_comparison; ..."
```

---

Last updated: 2026-01-21
