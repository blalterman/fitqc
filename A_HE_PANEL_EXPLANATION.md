# A_He Ultra-High-Resolution Analysis - Panel Explanation

## Overview
This 9-panel figure uses 2000 bins (extremely high resolution) to visualize the A_He dataset's boundary stickiness patterns. Each bin is only 0.0125 units wide (25/2000), making individual bars very thin.

## Panel-by-Panel Explanation

### Row 1: Raw Data (X-Space)

#### Panel 1 (Top-Left): Full Range - Linear Scale
**What it shows:**
- Histogram of all 100,000 A_He values in raw units
- Full range from L=0.0 to U=25.0
- 2000 bins (each bin width = 0.0125)
- Linear y-axis

**How it was created:**
```python
bins_raw_full = np.linspace(L, U, 2001)  # 2001 edges = 2000 bins
ax1.hist(x, bins=bins_raw_full, color='steelblue', edgecolor='none', alpha=0.7)
ax1.axvline(L, color='red', linestyle='--', linewidth=1.5, label=f'L={L}')
ax1.axvline(U, color='red', linestyle='--', linewidth=1.5, label=f'U={U}')
ax1.axvline(x0, color='orange', linestyle='--', linewidth=1.5, label=f'x0={x0}')
```

**What you should see:**
- Bulk distribution peaking around x=2-4
- Red dashed lines at L=0.0 and U=25.0
- Orange dashed line at x0=0.0 (coincides with L)
- 1,642 samples creating a spike exactly at x=0.0

**Visibility issue:** With 2000 very thin bars, you might see a "filled" area rather than individual bars. The spike at x=0.0 might be obscured by the red/orange axvlines drawn on top.

#### Panel 2 (Top-Center): Full Range - LOG Scale
**What it shows:**
- Same as Panel 1 but with logarithmic y-axis
- Better reveals low-count bins and boundary spikes

**How it was created:**
```python
ax2.hist(x, bins=bins_raw_full, color='steelblue', edgecolor='none', alpha=0.7)
ax2.set_yscale('log')
```

**What you should see:**
- Much clearer spike at x=0.0 (1,642 samples)
- Spike at x=25.0 (453 samples)
- Better visibility of distribution tails

**Visibility issue:** Same as Panel 1 - axvlines might obscure the spikes.

#### Panel 3 (Top-Right): Lower Boundary Zoom
**What it shows:**
- Only samples with x < 0.1 (near lower boundary)
- 201 bins over narrow range [0, 0.1]
- Shows detail of lower boundary concentration

**How it was created:**
```python
zoom_threshold_lower = L + 0.1  # 0.1
mask_zoom_lower = x < zoom_threshold_lower
x_zoom_lower = x[mask_zoom_lower]  # ~1,842 samples
bins_zoom_lower = np.linspace(L, zoom_threshold_lower, 201)
ax3.hist(x_zoom_lower, bins=bins_zoom_lower, color='darkgreen', ...)
```

**What you should see:**
- Large spike at x=0.0 (1,642 samples in first bin)
- Rapid decay moving away from x=0.0
- 1,842 total samples in this region (1.84%)

### Row 2: U-Space Transformation

#### Panel 4 (Middle-Left): U-Space Full - Linear Scale
**What it shows:**
- Normalized coordinates u = (x - L) / (U - L)
- Transforms data to [0, 1] range
- 2000 bins over [0, 1]

**How it was created:**
```python
u = (x - L) / (U - L)
bins_u_full = np.linspace(0, 1, 2001)
ax4.hist(u, bins=bins_u_full, color='purple', edgecolor='none', alpha=0.7)
ax4.axvline(0, color='red', linestyle='--', linewidth=1.5, label='u=0 (L)')
ax4.axvline(1, color='red', linestyle='--', linewidth=1.5, label='u=1 (U)')
```

**What you should see:**
- Same distribution shape as Panel 1, but compressed to [0, 1]
- Spike at u=0 (lower boundary)
- Small spike at u=1 (upper boundary)

**Why this matters:**
- U-space normalization makes boundaries directly comparable
- Algorithm operates in u-space to detect stickiness
- u < 0 or u > 1 indicates out-of-bounds samples (A_He has none)

#### Panel 5 (Middle-Center): U-Space Full - LOG Scale
**What it shows:**
- Same as Panel 4 with log y-axis
- Best view of boundary spikes in normalized coordinates

**How it was created:**
```python
ax5.hist(u, bins=bins_u_full, color='purple', edgecolor='none', alpha=0.7)
ax5.set_yscale('log')
```

**What you should see:**
- Clear spike at u=0 (1,642 samples at lower boundary)
- Clear spike at u=1 (453 samples at upper boundary)
- Smooth distribution in between

#### Panel 6 (Middle-Right): U-Space Lower Zoom (u < 0.02)
**What it shows:**
- Extreme zoom on lower boundary region
- Only samples with u < 0.02 (within 2% of lower bound)
- 201 bins over narrow range [0, 0.02]

**How it was created:**
```python
u_zoom_extreme_lower = u[u < 0.02]
bins_u_extreme_lower = np.linspace(0, 0.02, 201)
ax6.hist(u_zoom_extreme_lower, bins=bins_u_extreme_lower, color='darkred', ...)
ax6.axvline(0, color='red', linestyle='--', linewidth=2)
ax6.axvline(0.001, color='orange', linestyle=':', linewidth=1.5, label='u=0.001')
ax6.axvline(0.01, color='yellow', linestyle=':', linewidth=1.5, label='u=0.01')
```

**What you should see:**
- Massive spike at u=0 (first bin)
- Reference lines at u=0.001 and u=0.01
- Exponential decay pattern moving away from u=0

**Critical for detection:**
- Shows the detailed pattern the algorithm uses to detect stickiness
- 1,694 samples within u<0.001 (1.69%)
- 1,842 samples within u<0.01 (1.84%)

### Row 3: Upper Boundary and Summary

#### Panel 7 (Bottom-Left): U-Space Upper Zoom (u > 0.98)
**What it shows:**
- Extreme zoom on upper boundary region
- Only samples with u > 0.98 (within 2% of upper bound)
- 201 bins over narrow range [0.98, 1.0]

**How it was created:**
```python
u_zoom_upper = u[u > 0.98]
bins_u_zoom_upper = np.linspace(0.98, 1.0, 201)
ax7.hist(u_zoom_upper, bins=bins_u_zoom_upper, color='darkblue', ...)
ax7.axvline(1, color='red', linestyle='--', linewidth=2)
ax7.axvline(0.999, color='orange', linestyle=':', linewidth=1.5)
ax7.axvline(0.99, color='yellow', linestyle=':', linewidth=1.5)
```

**What you should see:**
- Smaller spike at u=1 (453 samples)
- 458 samples within u>0.999 (0.46%)
- 465 samples within u>0.99 (0.47%)

**Why smaller than lower:**
- Upper boundary stickiness is less pronounced
- Metadata correctly says `expected_upper_stickiness: false`
- Algorithm may or may not detect this as significant

#### Panel 8 (Bottom-Center): Cumulative Distribution Function (CDF)
**What it shows:**
- Cumulative fraction of samples vs. u
- Zoomed to u ∈ [0, 0.05] to show lower boundary detail
- Shows what fraction of data lies below each threshold

**How it was created:**
```python
u_sorted = np.sort(u)
cumulative = np.arange(1, len(u_sorted) + 1) / len(u_sorted)
ax8.plot(u_sorted, cumulative, color='green', linewidth=1.5)
ax8.axvline(0.001, color='orange', linestyle=':', linewidth=1)
ax8.axvline(0.01, color='red', linestyle=':', linewidth=1)
ax8.axhline(near_L_001/len(u), color='orange', linestyle=':', linewidth=1)
ax8.axhline(near_L_01/len(u), color='red', linestyle=':', linewidth=1)
ax8.set_xlim(0, 0.05)
```

**What you should see:**
- Green curve showing cumulative fraction
- Steep rise at u=0 (sudden jump from boundary spike)
- Horizontal line at ~0.0169 (1.69% below u=0.001)
- Horizontal line at ~0.0184 (1.84% below u=0.01)

**Why this matters:**
- CDF clearly shows concentration magnitude
- Steep initial rise = boundary stickiness
- Complements histogram view with different perspective

#### Panel 9 (Bottom-Right): Summary Statistics
**What it shows:**
- Text summary of all key metrics
- Sample counts, boundary concentrations, metadata

**Content:**
```
A_He (ALPHA PARTICLE ABUNDANCE) - DETAILED STATISTICS

Total samples: 100,000
Bounds: L=0.0, U=25.0
x0 (initial guess): 0.0

RAW DATA RANGE:
  Min: 0.000000
  Max: 25.000000
  Mean: 3.5550
  Median: 3.1254
  Std: 2.8838

BOUNDARY CONCENTRATION:
  At L=0.0 exactly: 1,642 samples
  At U=25.0 exactly: 453 samples

  Lower (u < 0.001): 1,694 (1.694%)
  Lower (u < 0.010): 1,842 (1.842%)
  Upper (u > 0.999): 458 (0.458%)
  Upper (u > 0.990): 465 (0.465%)

OUT-OF-BOUNDS:
  Below L (u<0): 0
  Above U (u>1): 0
  Total: 0

METADATA EXPECTATIONS:
  expected_lower_stickiness: true
  expected_upper_stickiness: false
```

## Visibility Issues with 2000 Bins

### Problem 1: Thin Bars
With 2000 bins over 25 units:
- Each bin width = 25 / 2000 = 0.0125 units
- At typical screen resolutions, bars appear as a continuous fill
- Individual bar boundaries are invisible

### Problem 2: axvlines Drawn on Top
The code draws axvlines AFTER histograms:
```python
ax.hist(...)  # Drawn first (z-order default = 0)
ax.axvline(...)  # Drawn second (z-order default = 1)
```

Result: Lines obscure the data they're marking!

### Problem 3: Color Overlap
- Red lines at L=0.0 and x0=0.0 (they coincide for A_He)
- Orange line at x0=0.0 overlaps with red line
- Both cover the exact location of the 1,642-sample spike

## Solution: Use Z-Order

To fix visibility, we need:
1. Draw axvlines BELOW histogram data using `zorder`
2. Use higher-contrast colors
3. Make histogram more opaque

```python
# Draw reference lines FIRST but tell matplotlib to render them BELOW
ax.axvline(L, color='red', linestyle='--', linewidth=2,
           label=f'L={L}', zorder=0)  # BELOW histogram

# Draw histogram ABOVE reference lines
ax.hist(x, bins=bins, color='steelblue', edgecolor='none',
        alpha=0.9, zorder=2)  # ABOVE reference lines
```

**Z-order values:**
- Lower numbers are drawn first and appear BEHIND
- Higher numbers are drawn last and appear IN FRONT
- Default z-order = 2 for most plot elements

Would you like me to create an improved version with proper z-ordering and better visibility?
