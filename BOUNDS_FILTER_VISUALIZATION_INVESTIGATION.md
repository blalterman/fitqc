# Bounds Filter Comparison Visualization Investigation

## User's Observation
"When I look at the bounds filter comparison histograms, they make it look like nothing is filtered."

## Executive Summary

**Finding:** The visualization is **technically correct but visually misleading**. This is a **DESIGN FLAW, not a code bug**.

The filtering algorithm works correctly (verified by audit), but the visual representation fails to clearly show the impact of filtering when:
1. Out-of-bounds samples are concentrated at x=0 (far from main distribution)
2. The number of filtered samples is small relative to total samples (<5%)
3. The y-axis is scaled to accommodate the main distribution

---

## Evidence

### Visual Comparison

**A_He Dataset:**
- Original: 100,000 samples, 0 out-of-bounds (0.00%)
- Filtered: 100,000 samples (100.00%)
- **Visual appearance:** IDENTICAL
- **Assessment:** ✅ CORRECT - nothing to filter, so plots SHOULD look identical

**np1 Dataset:**
- Original: 1,000,000 samples, 16,695 out-of-bounds (1.67%, all below L=0.01)
- Filtered: 983,305 samples (98.33%)
- **Visual appearance:** IDENTICAL despite filtering 16,695 samples
- **Assessment:** ❌ MISLEADING - filtering occurred but is invisible

### Code Analysis (src/fitqc/plot.py:764-913)

#### Filtering Logic (Line 814)
```python
x_filtered = x[(x >= L) & (x <= U)]
```
**Status:** ✅ Mathematically correct

#### Bin Range Calculation (Lines 828-836)
```python
x_min = min(x.min(), L)  # For np1: min(0.0, 0.01) = 0.0
x_max = max(x.max(), U)  # For np1: ~100.0

if isinstance(bins, str):
    _, bin_edges = np.histogram(x, bins=bins, range=(x_min, x_max))
else:
    bin_edges = np.linspace(x_min, x_max, bins + 1)
```
**Status:** ✅ Correct - extends range to capture out-of-bounds samples

**Effect:**
- For np1 with 100 bins: bin width = (100-0)/100 = 1.0
- All 16,695 out-of-bounds samples (at x=0) go into first bin [0.0, 1.0]
- First bin represents 1% of x-axis range but contains anomalous data (failed fits)

#### Y-Axis Matching (Lines 893-896)
```python
y_max_overall = max(counts_unfiltered.max(), counts_filtered.max()) * 1.1
ax_unfiltered.set_ylim(0, y_max_overall)
ax_filtered.set_ylim(0, y_max_overall)
```
**Status:** ✅ Correct for comparison, but exacerbates visibility problem

**Effect:**
- Main distribution bins contain ~70,000 samples (for np1)
- First bin contains 16,695 samples (24% of max)
- Y-axis scaled to 70,000 * 1.1 = 77,000
- Difference of 16,695 in first bin appears as subtle change from ~24% bar to ~0% bar
- When first bin is 1% of x-axis width, this difference is **visually imperceptible**

#### Shading (Lines 856-859)
```python
if n_below > 0:
    ax_unfiltered.axvspan(x_min, L, alpha=0.2, color="red",
                         label=f"Out-of-bounds (below L): {n_below}")
```
**Status:** ✅ Shows WHERE out-of-bounds region is, but doesn't make the DATA visible

---

## Root Cause Analysis

### Why the Plots Look Identical

For np1 (and similar datasets with failed fits at x=0):

1. **Spatial compression:**
   - Out-of-bounds region [0.0, 0.01] is 0.01 units wide
   - Valid range [0.01, 100] is 99.99 units wide
   - Out-of-bounds region occupies 0.01% of the parameter space but holds 1.67% of samples

2. **Visual compression:**
   - If plotting range is [0, 100], out-of-bounds region is 0.01% of x-axis
   - At 1200 pixels wide, out-of-bounds region is ~0.12 pixels (sub-pixel)
   - Even at 300 DPI, this is barely visible

3. **Count scaling:**
   - Main distribution peaks at ~70,000 samples/bin
   - First bin has 16,695 samples (appeared in top plot)
   - First bin has 0 samples (disappeared in bottom plot)
   - Difference is significant (16,695 samples) but small relative to peak (24%)
   - When bin is sub-pixel width, difference is invisible

4. **Y-axis matching:**
   - Required for valid comparison (can't compare different scales)
   - But means 16,695-sample difference is shown as 24% bar height vs 0% bar height
   - In a sub-pixel-width bin, this is imperceptible

### Why This is a Design Problem, Not a Bug

The code is doing exactly what it was designed to do:
- ✅ Apply correct filtering
- ✅ Use consistent bins for comparison
- ✅ Show full data range including out-of-bounds
- ✅ Match y-axes for fair comparison
- ✅ Label counts correctly in titles

But the design **fails to communicate the filtering impact** when:
- Out-of-bounds samples are spatially concentrated far from main distribution
- Out-of-bounds region is much narrower than main distribution range
- Number of out-of-bounds samples is small relative to peak bin counts

---

## Design Decision Analysis

### Current Design: Equal-Width Bins Across Full Range

**Pros:**
- ✅ Mathematically simple and standard
- ✅ Easy to implement
- ✅ Bins are directly comparable (same edges)
- ✅ No data is excluded from visualization
- ✅ Shading shows where out-of-bounds region is

**Cons:**
- ❌ Out-of-bounds data becomes invisible when spatially compressed
- ❌ Visually misleading ("looks like nothing is filtered")
- ❌ Fails to communicate the purpose of the plot (showing filtering impact)
- ❌ Scientists cannot visually assess filtering quality
- ❌ Small out-of-bounds regions are dwarfed by main distribution

**Scientific impact:**
When reviewing PPA12 data quality, scientists need to SEE the filtering impact to trust that:
1. The filtering algorithm is working correctly
2. The out-of-bounds samples are truly anomalous (failed fits)
3. The proportion of filtered data is acceptable

Current design fails this requirement for datasets like np1, np2, w_const.

---

## Proposed Solutions

### Option 1: Log Scale Y-Axis (Minimal Change)

**Change:** Add log scale option to y-axis
```python
if log_scale:
    ax_unfiltered.set_yscale('log')
    ax_filtered.set_yscale('log')
```

**Pros:**
- ✅ Minimal code change (2 lines)
- ✅ Makes small bins more visible
- ✅ Preserves existing bin structure
- ✅ Scientists familiar with log plots

**Cons:**
- ❌ Still doesn't solve spatial compression issue
- ❌ Log scale can be misleading for histograms (area interpretation)
- ❌ Sub-pixel bins remain sub-pixel regardless of y-scale
- ❌ Requires user to know to use log scale

**Effectiveness:** 🟡 Marginal - helps with count visibility but not spatial compression

---

### Option 2: Inset/Zoom Panel for Out-of-Bounds Region

**Change:** Add third subplot showing zoomed view of out-of-bounds region
```
Layout:
┌────────────────────────────────┐
│ Original Data (full range)     │
├────────────────────────────────┤
│ Filtered Data (full range)     │
├────────────────────────────────┤
│ Out-of-Bounds Region Detail    │
│ [zoomed to x_min to L+margin]  │
└────────────────────────────────┘
```

**Pros:**
- ✅ Shows out-of-bounds data clearly at appropriate scale
- ✅ Maintains full-range view for context
- ✅ Makes filtering impact immediately obvious
- ✅ Educational - shows WHERE the anomalous data is

**Cons:**
- ❌ Adds complexity (3 panels instead of 2)
- ❌ Requires more vertical space
- ❌ May be confusing if out-of-bounds region is empty (no zoom needed)
- ❌ Need to handle both below-L and above-U cases

**Effectiveness:** 🟢 High - directly addresses visibility problem

---

### Option 3: Separate Binning for Out-of-Bounds Region (Adaptive)

**Change:** Use finer bins in out-of-bounds regions, coarser bins in main distribution
```python
# Example: 1000 bins for [x_min, L], 1000 bins for [L, U], 1000 bins for [U, x_max]
bins_below = np.linspace(x_min, L, 1001) if x_min < L else []
bins_inside = np.linspace(L, U, 1001)
bins_above = np.linspace(U, x_max, 1001) if x_max > U else []
bin_edges = np.concatenate([bins_below, bins_inside[1:], bins_above[1:]])
```

**Pros:**
- ✅ Gives equal visual weight to out-of-bounds regions
- ✅ Single plot maintains simplicity
- ✅ Out-of-bounds data becomes visible

**Cons:**
- ❌ Bins no longer equal width (misleading for density interpretation)
- ❌ Violates standard histogram convention
- ❌ Could be confusing without explicit labeling
- ❌ Bin count varies with out-of-bounds extent (inconsistent)
- ❌ Scientists may misinterpret as equal-width bins

**Effectiveness:** 🟡 Moderate - solves visibility but introduces new problems

---

### Option 4: Side-by-Side Instead of Stacked (Layout Change)

**Change:** Show original and filtered data side-by-side with shared y-axis
```
Layout:
┌─────────────────┬─────────────────┐
│ Original Data   │ Filtered Data   │
│ (n=1,000,000)   │ (n=983,305)     │
└─────────────────┴─────────────────┘
```

**Pros:**
- ✅ Easier to compare visually (side-by-side is better for comparison)
- ✅ Same y-axis enforced by layout
- ✅ Takes less vertical space

**Cons:**
- ❌ Doesn't solve the visibility problem at all
- ❌ Takes more horizontal space
- ❌ Still have spatial compression issue

**Effectiveness:** 🔴 Low - doesn't address root cause

---

### Option 5: Difference Plot (Third Panel)

**Change:** Add third panel showing (Original - Filtered) counts per bin
```
Layout:
┌────────────────────────────────┐
│ Original Data                  │
├────────────────────────────────┤
│ Filtered Data                  │
├────────────────────────────────┤
│ Difference (Original - Filtered)│
│ [highlights bins with changes] │
└────────────────────────────────┘
```

**Pros:**
- ✅ Makes filtering impact explicit and quantitative
- ✅ Shows exactly WHICH bins changed
- ✅ Easy to see magnitude of change
- ✅ Maintains existing structure + adds clarity

**Cons:**
- ❌ Still affected by spatial compression (difference in sub-pixel bin)
- ❌ Adds complexity (3 panels)
- ❌ Difference may still be invisible if bin is too narrow
- ❌ Requires more explanation

**Effectiveness:** 🟡 Moderate - helps but doesn't fully solve spatial issue

---

### Option 6: Breakaxis for Out-of-Bounds Region

**Change:** Use broken x-axis to give more space to out-of-bounds regions
```
Plot range: [0 ... 0.01] // [0.01 ... 100]
            ←narrow→  break  ←────wide────→
```

**Pros:**
- ✅ Directly addresses spatial compression
- ✅ Shows out-of-bounds data at readable scale
- ✅ Maintains single-panel simplicity

**Cons:**
- ❌ Broken axes are controversial (can be misleading)
- ❌ Requires matplotlib-brokenaxes library (dependency)
- ❌ Complicated to implement correctly
- ❌ May confuse readers unfamiliar with broken axes
- ❌ Hard to choose break points automatically

**Effectiveness:** 🟢 High - directly solves spatial compression, but controversial

---

### Option 7: Overlaid Histograms with Alpha Transparency

**Change:** Show both histograms in same panel with transparency
```python
ax.hist(x, bins=bins, alpha=0.5, color='blue', label='Original')
ax.hist(x_filtered, bins=bins, alpha=0.5, color='green', label='Filtered')
```

**Pros:**
- ✅ Direct visual comparison (easier than stacked)
- ✅ Differences immediately apparent where colors don't overlap
- ✅ Single panel - simplest layout
- ✅ Familiar pattern to scientists

**Cons:**
- ❌ Still has spatial compression problem
- ❌ Color mixing can be confusing
- ❌ Overlapping regions hard to read
- ❌ Doesn't actually make sub-pixel bins visible

**Effectiveness:** 🔴 Low - doesn't address root cause

---

### Option 8: Summary Statistics Table + Histogram

**Change:** Add table showing key statistics in separate panel
```
┌────────────────────────────────┐
│ Statistics                     │
│ Total: 1,000,000               │
│ Out-of-bounds: 16,695 (1.67%)  │
│   Below L: 16,695 (1.67%)      │
│   Above U: 0 (0.00%)           │
│ Retained: 983,305 (98.33%)     │
├────────────────────────────────┤
│ Original Data                  │
├────────────────────────────────┤
│ Filtered Data                  │
└────────────────────────────────┘
```

**Pros:**
- ✅ Makes numbers explicit and impossible to miss
- ✅ Complements visual representation
- ✅ Easy to implement

**Cons:**
- ❌ Doesn't solve visual representation problem
- ❌ Numbers already in titles
- ❌ Doesn't help scientists SEE the data

**Effectiveness:** 🟡 Moderate - helps communication but not visualization

---

## Recommended Solution: Option 2 (Inset Zoom) + Option 8 (Statistics)

### Proposed Implementation

Create **three-panel** layout:
1. **Top panel:** Original data (full range) with shading
2. **Middle panel:** Filtered data (full range)
3. **Bottom panel:** Out-of-bounds detail (auto-zoomed) - ONLY if out-of-bounds samples exist

**Auto-zoom logic:**
```python
if n_below > 0:
    # Zoom to [x_min, L + margin]
    margin = (U - L) * 0.01  # 1% of valid range
    zoom_range = (x_min, min(L + margin, U))

elif n_above > 0:
    # Zoom to [U - margin, x_max]
    margin = (U - L) * 0.01
    zoom_range = (max(U - margin, L), x_max)

else:
    # No out-of-bounds, skip third panel
    zoom_panel = None
```

**Statistics enhancement:**
Add comprehensive statistics to panel titles:
```
Original Data (n=1,000,000, out-of-bounds=16,695 [1.67%])
Filtered Data (n=983,305, retained=98.33%, removed=16,695)
Out-of-Bounds Detail (zoomed: [0.0, 0.01]) - 16,695 samples removed
```

### Why This Solution

**Addresses root cause:**
- ✅ Spatial compression solved by zoom panel
- ✅ Makes filtering impact visually obvious
- ✅ Maintains context with full-range view
- ✅ Auto-adapts based on data (no zoom if no out-of-bounds)

**Maintains scientific rigor:**
- ✅ No misleading visual tricks (broken axes, non-uniform bins)
- ✅ Straightforward interpretation
- ✅ Shows data at appropriate scales

**Practical:**
- ✅ Moderate implementation complexity
- ✅ No new dependencies
- ✅ Backward compatible (can keep old version as option)

**User experience:**
- ✅ Immediately clear what was filtered
- ✅ Educational (shows where anomalies are)
- ✅ Builds trust in filtering algorithm

---

## Alternative Recommendation: Option 6 (Broken Axis)

If we want to maintain two-panel layout, broken axis is the most direct solution.

**Pros:**
- ✅ Solves spatial compression directly
- ✅ Maintains two-panel simplicity
- ✅ Shows all data at readable scales

**Cons:**
- ❌ Requires additional dependency (mpl-broken-axis)
- ❌ More controversial (some consider broken axes misleading)
- ❌ More complex to implement correctly

---

## Questions for Decision

1. **Layout preference:**
   - Accept 3-panel layout for better clarity?
   - Or maintain 2-panel and use broken axis?

2. **Scope:**
   - Fix only bounds filter comparison plots?
   - Or also update interior filter comparison plots?
   - Or update combined filter comparison plots?

3. **Backward compatibility:**
   - Keep old version as `plot_bounds_filter_comparison_legacy()`?
   - Or replace entirely?

4. **Default behavior:**
   - Always show zoom panel when out-of-bounds exist?
   - Or make it optional parameter `show_detail=True`?

---

## Implementation Checklist (Option 2)

- [ ] Update `plot_bounds_filter_comparison()` signature to include `show_detail=True`
- [ ] Add logic to detect out-of-bounds existence and location
- [ ] Create 3-subplot layout when `show_detail=True` and out-of-bounds exist
- [ ] Implement zoom range calculation (auto-determine based on out-of-bounds extent)
- [ ] Add zoom panel with clear title/labels
- [ ] Update titles to include comprehensive statistics
- [ ] Test with all 12 PPA12 datasets
- [ ] Update test_plot_filter_comparison.py to verify new functionality
- [ ] Update figures/README.md to explain new visualization
- [ ] Regenerate all filter comparison plots
- [ ] Update documentation

---

## Success Criteria

After implementing the fix, the visualization should:
1. ✅ Make filtering impact immediately visually apparent for all datasets
2. ✅ Show out-of-bounds data at appropriate scale
3. ✅ Maintain scientific rigor (no misleading tricks)
4. ✅ Work automatically for all datasets (no manual adjustment)
5. ✅ User can see at a glance: "Yes, filtering worked correctly"

---

## Next Steps

Awaiting user approval to proceed with implementation of:
- **Primary recommendation:** Option 2 (Inset zoom panel) + Option 8 (Enhanced statistics)
- **Alternative:** Option 6 (Broken axis) if 2-panel layout is required

Please review propositions and provide guidance on:
1. Which solution to implement
2. Whether to maintain backward compatibility
3. Whether to apply to all filter comparison functions (bounds + interior + combined)
