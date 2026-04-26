# Filter Terminology Clarification

**Date**: 2026-01-23
**Issue**: Confusion about what different filters do and why visualizations look identical for A_He

---

## Your Questions Answered

### Q1: "In A_He_bounds_filter_comparison, is the filtering just removing out of bounds data?"

**YES - exactly right!** The "bounds filter" (also called "boundary filter") **ONLY** removes out-of-bounds samples:
- **Removes**: x < L or x > U (samples BEYOND the boundaries)
- **Keeps**: Everything within [L, U], including samples AT the boundaries

**For A_He**:
- L = 0.0, U = 25.0
- Original: n = 100,000, all within [0, 25]
- Out-of-bounds: 0 samples (0.00%)
- Filtered: n = 100,000 (nothing removed)
- **Result**: Both panels look identical ✅ This is correct!

---

### Q2: "I don't see how the boundary filter is working in panel 2 of A_He_combined_filter_comparison_hires. I still see data spikes at the top and bottom boundary."

**You're absolutely right to be confused!** This reveals a **terminology problem** in our naming:

#### The Confusion

**Panel 2: "Boundary Filter Only"**
- What it actually does: Removes **OUT-OF-BOUNDS** samples (x < L or x > U)
- For A_He: Removes 0 samples because all data is within [0, 25]
- **The spikes you see ARE NOT out-of-bounds** - they're AT the boundaries (x = 0 and x = 25)

**Panel 3: "Interior Filter Only"**
- What it actually does: Removes **BOUNDARY-STICKY** samples (samples too close to L or U)
- For A_He: Removes 1,689 samples (1.69%) that are too close to boundaries
- **THIS is what removes the spikes you see**

#### The Problem

The naming is backwards from intuition:
- ❌ "Boundary filter" sounds like it removes boundary spikes → **but it doesn't!**
- ❌ "Interior filter" sounds like it removes interior samples → **but it removes boundary samples!**

#### What's Actually Happening

```
Original Data (Panel 1):
├─ Spikes at x=0 and x=25 (boundary pileup)
└─ Smooth distribution in middle

Boundary Filter (Panel 2) - removes x < L or x > U:
├─ Still has spikes at x=0 and x=25 ← These are AT boundaries, not beyond
└─ Removed: 0 samples (nothing was out-of-bounds)

Interior Filter (Panel 3) - removes samples too close to L or U:
├─ Spikes GONE! ← This is what you expected from "boundary filter"
└─ Removed: 1,689 samples that were too close to boundaries

Combined (Panel 4) - both filters:
├─ Same as Panel 3 (since Panel 2 removed nothing)
└─ Removed: 1,689 samples total
```

#### Better Naming (Proposed)

Current names are misleading. Better names would be:

| Current Name | What It Does | Better Name |
|--------------|--------------|-------------|
| "Boundary Filter" | Removes x < L or x > U | **"Out-of-Bounds Filter"** or **"Bounds Validation"** |
| "Interior Filter" | Removes samples too close to L or U | **"Boundary Stickiness Filter"** or **"Proximity Filter"** |

**Recommendation**: Rename these in code and plots to avoid confusion.

---

### Q3: "I don't understand how A_He_filtering_audit actually shows the filters are having any effect. I don't see any data removal in the top right panel."

**You're seeing it correctly!** The top right panel shows **x-space filtering** (bounds filter), which removes out-of-bounds samples.

**Top Right Panel: "Overplotted: Original vs Filtered"**
- Purple = Original data (all 100,000 samples)
- Green = Filtered data (x-space bounds filter applied)
- **They look identical** because A_He has 0 out-of-bounds samples
- Middle panel confirms: **"Removed Samples (n=0)"**

**Where you DO see removal**:
- **Bottom panels**: Show u-space near boundaries
  - Bottom left: Near u=0 (lower boundary) - shows concentration
  - Bottom right: Near u=1 (upper boundary) - shows concentration
- These concentrations are what the **interior filter** removes (not shown in this audit plot)

**The audit plot only shows bounds filter (out-of-bounds removal), not interior filter (boundary stickiness removal).**

---

### Q4: "Why are there more plots for A_He than for the other parameters we are checking?"

**Plot counts**:
```
A_He:      12 plots
e_dv_pp:   6 plots
e_dv_ap:   6 plots
np1:       4 plots
np2:       4 plots
w_const:   4 plots
```

**Reasons**:

1. **A_He was the primary investigation target** (Jan 20-21, 2026)
   - Algorithm development focused on A_He bilateral boundary stickiness
   - Generated investigation plots: ultrahighres, improved_analysis, filtering_audit
   - These are **investigation artifacts**, not production outputs

2. **Duplicate versions**:
   - Each plot has regular (150 DPI) and _hires (300 DPI) versions
   - Double the file count unnecessarily

3. **Extra investigation plots**:
   - `A_He_ultrahighres_analysis.png` - 9-panel investigation plot
   - `A_He_improved_analysis.png` - 12-panel investigation plot
   - `A_He_filtering_audit.png` - 6-panel debug/audit plot
   - **These were one-off investigations, not standard outputs**

**Standard plots** (all datasets should have):
- `*_bounds_filter_comparison_hires.png`
- `*_interior_filter_comparison_hires.png`
- `*_combined_filter_comparison_hires.png`

**Investigation plots** (A_He only):
- `*_ultrahighres_analysis_hires.png` (optional, investigation)
- `*_improved_analysis_hires.png` (optional, investigation)
- `*_filtering_audit_hires.png` (optional, debug)

---

## Summary

### What Each Filter Actually Does

| Filter | Removes | Keeps | A_He Result |
|--------|---------|-------|-------------|
| **Bounds/Boundary Filter** | x < L or x > U | Everything within [L, U] | 0 removed (100% kept) |
| **Interior Filter** | Samples too close to L or U | Samples away from boundaries | 1,689 removed (98.31% kept) |
| **Combined** | Both of the above | Clean interior samples | 1,689 removed (98.31% kept) |

### Why A_He Plots Look Identical

**Bounds filter comparison** (2 panels):
- Panel 1 = Panel 2 because no out-of-bounds samples exist ✅ Correct

**Combined filter comparison** (4 panels):
- Panel 1 = Panel 2 because no out-of-bounds samples ✅ Correct
- Panel 2 ≠ Panel 3 because interior filter removes boundary stickiness ✅ Correct
- Panel 3 = Panel 4 because boundary filter removed nothing ✅ Correct

**Filtering audit** (6 panels):
- Top right: Original = Filtered because no out-of-bounds ✅ Correct
- Bottom panels: Show boundary concentrations that interior filter removes

---

## Action Items

1. ✅ **Terminology is confusing** - Consider renaming:
   - "Boundary filter" → "Out-of-bounds filter"
   - "Interior filter" → "Boundary stickiness filter"

2. ✅ **Remove duplicate low-res plots** - Keep only _hires (300 DPI) versions

3. ✅ **Standardize plot generation** - All datasets should have same plot types

4. ✅ **Clean up A_He investigation plots** - Archive or remove one-off analysis plots

---

## Technical Details

### Bounds Filter (src/fitqc/boundary.py)

```python
def apply_bounds_filter(x, L, U):
    """Remove out-of-bounds samples."""
    return x[(x >= L) & (x <= U)]
```

**Removes**: x < L or x > U
**For A_He**: All x in [0.0, 25.0], so nothing removed

### Interior Filter (src/fitqc/interior.py)

```python
def apply_interior_filter(x, L, U, result):
    """Remove boundary-sticky samples based on detected thresholds."""
    mask = np.ones(len(x), dtype=bool)

    # Remove lower boundary stickiness
    if result.lower_stickiness_detected:
        u = (x - L) / (U - L)
        mask &= (u > result.t_lo_star)

    # Remove upper boundary stickiness
    if result.upper_stickiness_detected:
        u = (x - L) / (U - L)
        mask &= (u < result.t_hi_star)

    return x[mask]
```

**Removes**: Samples with u < t_lo_star or u > t_hi_star (too close to boundaries)
**For A_He**: Removes 1,689 samples (1.69%) near boundaries
