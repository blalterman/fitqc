# Complete Filter Taxonomy: Understanding All Filter Types

**Date**: 2026-01-23
**Purpose**: Comprehensive explanation of all filter types, naming conventions, and their relationships

---

## Executive Summary

There are **THREE distinct types of problematic samples** in MCMC fitting:

1. **Out-of-bounds** (x < L or x > U) - Invalid values that violate parameter constraints
2. **Boundary stickiness** (x too close to L or U) - Optimizer got stuck at fit limits
3. **Initial guess stickiness** (x too close to x0) - Optimizer didn't explore from starting point

But the fitqc API only exposes **TWO filter types** with confusing names:
- "Boundary filter" → Actually removes **out-of-bounds** (not boundary stickiness)
- "Interior filter" → Actually removes **initial guess stickiness** (not interior samples)

**Meanwhile**, there are **TWO QC detection functions** with different purposes:
- `run_boundary_qc()` → **DETECTS** boundary stickiness (at L and U)
- `run_interior_qc()` → **DETECTS** initial guess stickiness (at x0)

This creates confusion because:
- QC detection names refer to **what they detect**
- Filter visualization names refer to **implementation details** (not what they filter)

---

## The Three Types of Problematic Samples

### 1. Out-of-Bounds Samples

**What are they?**
- Samples where x < L or x > U
- Violate the parameter bounds specified by user
- Invalid values that shouldn't exist mathematically

**Where do they come from?**
- Failed Markov chain fits (numerical errors, divergence)
- Numerical precision issues
- Algorithm bugs

**Example for A_He (L=0.0, U=25.0)**:
- x = -0.5 → Out-of-bounds (below L)
- x = 30.0 → Out-of-bounds (above U)
- x = 0.0 → **NOT out-of-bounds** (exactly at L, which is valid)
- x = 25.0 → **NOT out-of-bounds** (exactly at U, which is valid)

**Current terminology**:
- Called: "Boundary filter" or "Bounds filter"
- Removed by: `plot_bounds_filter_comparison()` visualization
- Detection: **NOT DETECTED** (trivial to check, no QC function needed)

**Why the name is confusing**:
- ❌ "Boundary" suggests it affects the boundaries (L and U)
- ✅ Actually affects data BEYOND the boundaries

**Better name would be**: "Out-of-bounds filter" or "Bounds validation filter"

---

### 2. Boundary Stickiness (Fit Limit Stickiness)

**What is it?**
- Samples that are too close to L or U (but still within [L, U])
- Indicates optimizer got stuck at parameter constraints
- Suggests poor parameterization or optimization failure

**Where does it come from?**
- Optimizer hitting constraints during optimization
- Likelihood surface has mode near boundary
- Poor choice of parameter bounds (too restrictive)
- Transformation issues (unbounded → bounded parameters)

**Example for A_He (L=0.0, U=25.0)**:
- x = 0.0 → Boundary-sticky (AT lower boundary L)
- x = 0.001 → Boundary-sticky (very close to L)
- x = 24.999 → Boundary-sticky (very close to U)
- x = 25.0 → Boundary-sticky (AT upper boundary U)
- x = 12.5 → **NOT boundary-sticky** (middle of range)

**How close is "too close"?**
- Determined by QC algorithm using u-space threshold
- For A_He: threshold t* ≈ 0.0013 (in u-space)
- In x-space: samples within 0.0013 × (U-L) = 0.0325 of boundaries
- So: x < 0.0325 or x > 24.9675 would be considered sticky

**Current terminology**:
- **DETECTION**: `run_boundary_qc()` function
  - Returns: `BoundaryResult` with `lower_pileup_detected`, `upper_pileup_detected`
  - Returns: Thresholds `t_lo_star`, `t_hi_star` defining sticky regions
- **FILTERING**: Used in "Combined filter" (panel 4 of combined comparison plot)
  - Removes samples with u < t_lo_star or u > t_hi_star
- **VISUALIZATION**: `plot_boundary_diagnostics()` shows mass curves at boundaries

**Why the terminology is confusing**:
- ✅ `run_boundary_qc()` correctly named (detects boundary problems)
- ❌ No dedicated "boundary stickiness filter" visualization function
- ❌ Only appears in "combined filter" with no clear name

**Better name would be**: "Boundary stickiness filter" or "Fit limit filter"

---

### 3. Initial Guess Stickiness (x0 Stickiness)

**What is it?**
- Samples that are too close to x0 (initial guess)
- Indicates optimizer didn't explore parameter space
- Suggests flat likelihood or optimization failure

**Where does it come from?**
- Flat or uninformative likelihood surface
- Poor choice of initial guess (far from mode)
- Optimizer convergence issues
- Too few MCMC iterations

**Example for A_He (x0=2.5, L=0.0, U=25.0)**:
- x = 2.5 → x0-sticky (AT initial guess)
- x = 2.49 → x0-sticky (very close to x0)
- x = 2.51 → x0-sticky (very close to x0)
- x = 10.0 → **NOT x0-sticky** (far from x0)

**How close is "too close"?**
- Determined by QC algorithm using z-space threshold
- For A_He: threshold ε* ≈ 0.05 (in z-space units)
- In x-space: within |x - x0| / (U - L) < ε* of x0
- So: |x - 2.5| < 0.05 × 25 = 1.25 would be sticky

**Current terminology**:
- **DETECTION**: `run_interior_qc()` function
  - Returns: `InteriorResult` with `spike_detected`
  - Returns: Threshold `eps_star` defining sticky region
- **FILTERING**: "Interior filter" in combined comparison plot
  - Removes samples within `eps_star` of x0
- **VISUALIZATION**: `plot_interior_filter_comparison()` shows before/after removal

**Why the terminology is confusing**:
- ❌ "Interior" suggests middle/interior of [L, U] range
- ✅ Actually refers to "interior point" (x0) that samples stick to
- ❌ Name doesn't convey it's about initial guess stickiness

**Better name would be**: "Initial guess filter" or "x0 stickiness filter"

---

## How The Pieces Fit Together

### The Two QC Detection Functions

**Purpose**: Detect problems in MCMC output

| Function | Detects | Returns | Filters |
|----------|---------|---------|---------|
| `run_boundary_qc(x, L, U)` | Boundary stickiness (at L and U) | `BoundaryResult` with thresholds | NO - just detects |
| `run_interior_qc(x, x0, L, U)` | Initial guess stickiness (at x0) | `InteriorResult` with thresholds | NO - just detects |

**Key insight**: These functions **DETECT** problems but **DO NOT** filter the data.

### The Three Filter Visualizations

**Purpose**: Show effect of filtering problematic samples

| Filter Visualization | Removes | Uses Detection From | QC Function |
|---------------------|---------|---------------------|-------------|
| "Boundary Filter" (or "Bounds Filter") | Out-of-bounds (x < L or x > U) | None (trivial check) | N/A |
| "Interior Filter" | Initial guess stickiness (near x0) | `run_interior_qc()` | Uses `eps_star` |
| "Combined Filter" | All three types | Both QC functions | Uses both thresholds |

**Combined Filter removes**:
1. Out-of-bounds (x < L or x > U) ← Trivial check
2. Boundary stickiness (u < t_lo_star or u > t_hi_star) ← From `run_boundary_qc()`
3. Initial guess stickiness (within eps_star of x0) ← From `run_interior_qc()`

### The Naming Disconnect

**The problem**:
- QC detection function names describe **what they detect** ✅
  - `run_boundary_qc()` → detects boundary problems
  - `run_interior_qc()` → detects interior point (x0) problems

- Filter visualization names describe **implementation modules** ❌
  - "Boundary filter" → implemented using bounds check (not boundary detection!)
  - "Interior filter" → uses interior detection results

**This creates confusion**:
```
User expectation: "Boundary filter" removes boundary-sticky samples
Reality: "Boundary filter" removes out-of-bounds samples

User expectation: "Interior filter" removes interior samples
Reality: "Interior filter" removes x0-sticky samples
```

---

## Complete Example: A_He Dataset

Let's trace all three types through A_He (L=0.0, U=25.0, x0=2.5):

### Original Data (100,000 samples)

**Distribution**:
- ~1,642 samples at x ≈ 0.0 (boundary-sticky at L)
- ~358 samples at x ≈ 25.0 (boundary-sticky at U)
- Remaining samples distributed throughout [0, 25]
- 0 samples with x < 0.0 or x > 25.0 (no out-of-bounds)

### Step 1: Bounds Filter (Panel 2 of Combined Plot)

**Removes**: Out-of-bounds samples (x < L or x > U)

**For A_He**:
- Checks: x < 0.0 or x > 25.0
- Found: 0 samples out-of-bounds
- **Result**: 100,000 samples remain (nothing removed)

**Why panel 1 and panel 2 look identical**: No out-of-bounds samples exist!

### Step 2: Boundary QC Detection (Behind the Scenes)

**Detects**: Boundary stickiness

```python
boundary_result = run_boundary_qc(x, L=0.0, U=25.0)
# Returns:
#   lower_pileup_detected = True (1,642 samples at x ≈ 0.0)
#   upper_pileup_detected = True (358 samples at x ≈ 25.0)
#   t_lo_star ≈ 0.0013 (threshold in u-space)
#   t_hi_star ≈ 0.9986 (threshold in u-space)
```

**This detection is used in panel 4 (combined filter), not panel 2!**

### Step 3: Interior Filter (Panel 3 of Combined Plot)

**Removes**: Initial guess stickiness (near x0)

```python
interior_result = run_interior_qc(x, x0=2.5, L=0.0, U=25.0)
# Returns:
#   spike_detected = False (no unusual concentration at x0)
#   eps_star = None
```

**For A_He**:
- No spike at x0 = 2.5
- **Result**: Nothing removed (or minimal removal if spike existed)

### Step 4: Combined Filter (Panel 4 of Combined Plot)

**Removes**: All three types

**For A_He**:
1. Out-of-bounds (x < 0 or x > 25): 0 samples removed
2. Boundary-sticky (u < 0.0013 or u > 0.9986): ~1,689 samples removed
3. x0-sticky: 0 samples removed (no spike detected)

**Total removed**: 1,689 samples (1.69%)
**Remaining**: 98,311 samples (98.31%)

**Why panel 2 and panel 4 look different**: Panel 2 only removes out-of-bounds (nothing), panel 4 removes boundary-sticky samples (1,689)!

---

## Summary Table: All Filter Types

| Filter Type | What It Removes | Example (A_He) | Detection Function | Visualization | Current Name |
|-------------|-----------------|----------------|-------------------|---------------|--------------|
| **Out-of-bounds** | x < L or x > U | x = -0.5 or x = 30 | None (trivial) | `plot_bounds_filter_comparison()` | "Boundary Filter" ❌ |
| **Boundary stickiness** | Too close to L or U | x < 0.03 or x > 24.97 | `run_boundary_qc()` | Combined filter only | No dedicated name |
| **Initial guess stickiness** | Too close to x0 | \|x - 2.5\| < 1.25 | `run_interior_qc()` | `plot_interior_filter_comparison()` | "Interior Filter" ❌ |

---

## Why This Matters for Understanding Your Data

### For A_He Specifically

When you see the combined filter comparison plot:

**Panel 1: Original Data**
- 100,000 samples
- Includes 1,642 boundary-sticky samples at x ≈ 0
- Includes 358 boundary-sticky samples at x ≈ 25
- No out-of-bounds samples
- No x0-sticky samples

**Panel 2: "Boundary Filter Only"**
- Still 100,000 samples (nothing removed)
- **Still has boundary spikes at x = 0 and x = 25** ← This confused you!
- Why? Because "boundary filter" removes out-of-bounds, not boundary stickiness
- Since A_He has no out-of-bounds, nothing is removed

**Panel 3: "Interior Filter Only"**
- Still ~100,000 samples (minimal removal)
- Why? Because there's no spike at x0 = 2.5
- The "interior filter" targets x0 stickiness, not boundary stickiness

**Panel 4: "Combined Filters"**
- 98,311 samples (1,689 removed)
- **Boundary spikes are GONE!** ← This is what you expected from panel 2
- Why? Because combined filter uses `run_boundary_qc()` detection results
- Removes samples with u < t_lo_star or u > t_hi_star

### The Key Insight

**The boundary spikes you see are removed by the COMBINED filter, not the BOUNDARY filter!**

This is because:
- "Boundary filter" = out-of-bounds removal (x < L or x > U)
- "Combined filter" = out-of-bounds + boundary stickiness + x0 stickiness

The boundary stickiness detection (`run_boundary_qc()`) is only applied in the combined filter.

---

## Proposed Documentation Improvements

### Clear Naming Map

I will document this as:

```markdown
## Understanding Filter Terminology

fitqc uses the following filter types:

### Filter Type 1: Out-of-Bounds Validation
- **Current name**: "Boundary Filter" or "Bounds Filter"
- **Removes**: Samples where x < L or x > U (invalid values)
- **Detection**: None needed (trivial check)
- **Visualization**: `plot_bounds_filter_comparison()`
- **Note**: Despite the name, this does NOT remove boundary-sticky samples!

### Filter Type 2: Boundary Stickiness Detection
- **Current name**: No dedicated filter (only in "Combined Filter")
- **Removes**: Samples too close to L or U boundaries
- **Detection**: `run_boundary_qc()` function
- **Visualization**: Only in combined filter comparison
- **Note**: This is what removes the spikes you see at boundaries!

### Filter Type 3: Initial Guess Stickiness Detection
- **Current name**: "Interior Filter"
- **Removes**: Samples too close to x0 (initial guess)
- **Detection**: `run_interior_qc()` function
- **Visualization**: `plot_interior_filter_comparison()`
- **Note**: "Interior" refers to the interior point (x0), not the interior of [L, U]!
```

### Visual Diagram

I will create a diagram showing:

```
Parameter Space: [L=0 ────────────────── x0=2.5 ──────────── U=25]

Out-of-Bounds:
  ←←← x<0 │                                              │ x>25 →→→
        REMOVED BY: "Boundary Filter" (panel 2)

Boundary-Sticky:
  ←x<0.03─→│                                          │←x>24.97→
        REMOVED BY: "Combined Filter" (panel 4) using run_boundary_qc()

x0-Sticky:
                          ← |x-2.5|<1.25 →
        REMOVED BY: "Interior Filter" (panel 3) using run_interior_qc()
```

### API Documentation

Each function will clearly state:

```python
def run_boundary_qc(x, L, U, config=None):
    """Detect boundary stickiness (pileup near L or U).

    This function DETECTS when samples cluster too close to the parameter
    bounds L or U. It does NOT remove samples itself.

    IMPORTANT:
    - This detects BOUNDARY STICKINESS (samples near L or U)
    - This does NOT detect out-of-bounds (x < L or x > U)
    - The detected thresholds are used by the combined filter

    Returns:
        BoundaryResult with:
        - lower_pileup_detected: True if samples pile up near L
        - upper_pileup_detected: True if samples pile up near U
        - t_lo_star: Threshold for lower boundary (in u-space)
        - t_hi_star: Threshold for upper boundary (in u-space)
    """

def run_interior_qc(x, x0, L, U, config=None):
    """Detect initial guess stickiness (spike at x0).

    This function DETECTS when samples fail to move away from the
    initial guess x0. It does NOT remove samples itself.

    IMPORTANT:
    - This detects X0 STICKINESS (samples stuck at initial guess)
    - This does NOT detect interior samples (away from boundaries)
    - "Interior" refers to x0 as an interior point, not the interior region

    Returns:
        InteriorResult with:
        - spike_detected: True if samples concentrate at x0
        - eps_star: Threshold for x0 proximity (in z-space)
    """
```

---

## Does This Answer Your Question?

**Your question**: "How does the initial guess vs fit limit stickiness play into all of this? What about the out of bounds?"

**Answer**:

1. **Out-of-bounds** (x < L or x > U):
   - Removed by: "Boundary Filter" visualization
   - Detection: None (trivial check)
   - For A_He: 0 samples (nothing to remove)

2. **Fit limit stickiness** (boundary stickiness at L or U):
   - Removed by: "Combined Filter" only
   - Detection: `run_boundary_qc()` function
   - For A_He: 1,689 samples removed
   - **This is why you see spikes in panel 2 but not panel 4!**

3. **Initial guess stickiness** (x0 stickiness):
   - Removed by: "Interior Filter" visualization
   - Detection: `run_interior_qc()` function
   - For A_He: ~0 samples (no spike at x0)

**The naming confusion**:
- "Boundary filter" sounds like it removes boundary spikes (fit limit stickiness)
  → **Actually removes out-of-bounds**
- "Interior filter" sounds like it removes interior samples
  → **Actually removes initial guess stickiness**

**My documentation will clarify**:
- Explicit definitions of all three types
- Visual diagram showing where each type appears
- Updated docstrings explaining what each function does
- Examples showing A_He behavior step-by-step

**Yes, this will be much clearer!** The documentation will include:
1. Complete taxonomy (this document)
2. Visual diagrams
3. Updated docstrings
4. Step-by-step examples
5. Clear naming map (current name → what it actually does)
