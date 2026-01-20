# PPA12 Test Data Analysis Report

## Executive Summary

Analyzed 4 real-world PPA12 test datasets from Wind/SWE pipeline:
- **e_dv_pp**: ✓ PASS (both boundaries detected correctly)
- **e_dv_ap**: ✓ PASS (both boundaries detected correctly)
- **A_He**: ✓ PASS (both boundaries detected correctly, metadata corrected)
- **np1**: ⚠️ DATA ISSUE (samples outside parameter bounds)

## Dataset Details

### 1. e_dv_pp (Proton-Proton Drift Velocity Perturbation)

**Status**: ✓ **PASS** - Algorithm working correctly

**Bounds**: L=-75%, U=75%, x0=0%

**Observed Stickiness**:
- Lower boundary: **11.78%** exactly at L=-75.0 (117,990x excess at u<1e-6)
- Upper boundary: **4.13%** exactly at U=75.0 (41,400x excess)
- Interior (x0=0): **1.64%** exactly at x0

**Detection Results**:
- Lower: ✓ Detected (t_lo_star=0.00125)
- Upper: ✓ Detected (t_hi_star=0.00125)

**Notes**: Strong bilateral boundary stickiness with clear delta functions.

---

### 2. e_dv_ap (Alpha-Proton Drift Velocity Perturbation)

**Status**: ✓ **PASS** - Algorithm working correctly

**Bounds**: L=-150%, U=150%, x0=0%

**Observed Stickiness**:
- Lower boundary: **0.62%** exactly at L=-150.0 (6,240x excess at u<1e-6)
- Upper boundary: **1.16%** exactly at U=150.0 (11,580x excess)
- Interior (x0=0): **1.59%** exactly at x0

**Detection Results**:
- Lower: ✓ Detected (t_lo_star=0.00125)
- Upper: ✓ Detected (t_hi_star=0.00125)

**Notes**: Moderate boundary stickiness at both bounds. Successfully detects sub-1% pileups.

---

### 3. A_He (Helium Abundance)

**Status**: ✓ **PASS** - Algorithm working correctly (metadata updated)

**Bounds**: L=0%, U=25%, x0=0%

**Observed Stickiness**:
- Lower boundary: **1.64%** exactly at L=0.0 (16,880x excess at u<1e-6)
- Upper boundary: **0.45%** exactly at U=25.0 (4,530x excess at u<1e-6)
- Interior (x0=0): **1.64%** exactly at x0 (same as lower - both at 0.0)

**Detection Results**:
- Lower: ✓ Detected (t_lo_star=0.00125) - **CORRECT**
- Upper: ✓ Detected (t_hi_star=0.00125) - **CORRECT**

**Analysis**:
The algorithm correctly detects upper boundary stickiness:
1. 453 samples (0.45%) exactly at U=25.0
2. Clear delta function (4,530x excess at u<1e-6)
3. Similar magnitude to e_dv_ap's 0.62% lower boundary

**Note**: Metadata was initially marked as `expected_upper_stickiness: false` but has been corrected to `true` after domain expert confirmation of the boundary spike.

---

### 4. np1 (Proton Core Density)

**Status**: ⚠️ **DATA ISSUE** - Samples outside parameter bounds

**Bounds**: L=0.01 /cc, U=100.0 /cc, x0=None (moment-based)

**Observed Data**:
- **1,708 samples (1.71%) are BELOW L=0.01**:
  - 1,530 samples exactly at 0.0
  - 178 samples in (0.001, 0.01)
- Upper boundary: 6 samples (0.006%) at U=100.0
- **This creates negative u-values**: u_min = -0.0001

**Detection Results**:
- Lower: ✓ Detected (t_lo_star=0.00125) - **FALSE POSITIVE**
- Upper: ✓ Not detected - **CORRECT**

**Root Cause**:
The 1,708 samples below L=0.01 create negative u-values:
```
u = (x - L) / (U - L)
u = (0.0 - 0.01) / (100 - 0.01) = -0.0001
```

When `u_sorted` is computed, these negative values sort to the beginning.
The algorithm detects this as a "pileup at lower boundary" (1.7% at u<0).

**This is NOT boundary stickiness - these samples are outside the parameter bounds!**

**Possible Causes**:
1. **Data Quality**: Optimizer returned 0.0 instead of clipping to L=0.01
2. **Bound Definition**: L=0.01 is a soft lower bound (physical limit may be 0.0)
3. **Post-processing**: Samples were clipped/transformed after fitting

**Recommendation**:
- Check if np1 should have L=0.0 instead of L=0.01
- Or add validation to algorithm: filter samples where u<0 or u>1

---

## Summary Table

| Dataset | Lower Expected | Lower Detected | Upper Expected | Upper Detected | Status |
|---------|----------------|----------------|----------------|----------------|--------|
| e_dv_pp | True (11.8%)   | ✓ True         | True (4.1%)    | ✓ True         | ✓ PASS |
| e_dv_ap | True (0.62%)   | ✓ True         | True (1.16%)   | ✓ True         | ✓ PASS |
| A_He    | True (1.64%)   | ✓ True         | True (0.45%)   | ✓ True         | ✓ PASS |
| np1     | **False** (1.71% at u<0) | ✗ True   | False (0.006%) | ✓ False    | ⚠️ Data issue |

## Key Findings

### Algorithm Performance
✓ **Successfully detects**:
- Strong pileups (11.8% e_dv_pp)
- Moderate pileups (0.6-4% range)
- Sub-percent pileups (0.45% A_He upper)
- Delta functions at exact boundaries

✓ **Correctly rejects**:
- Negligible pileups (0.006% np1 upper)

⚠️ **Edge Cases**:
- **Out-of-bounds samples** (np1): Detects as false positive when samples fall outside [L, U]

### Recommendations

1. **np1 Lower Bound**:
   - Investigate why 1,708 samples (1.7%) are below L=0.01
   - Consider changing L from 0.01 to 0.0 if physical minimum is 0
   - Or add algorithm validation to reject u<0 samples

2. **Interior Stickiness**:
   - All three parameters with x0=0 show ~1.6% at x0
   - This should be detectable by `run_interior_qc()` (not tested in this analysis)

## Test Data Quality

All datasets are:
- ✓ 100,000 samples (uniform random from 7.5M total)
- ✓ Representative of production pipeline data
- ✓ Include metadata with expected results
- ⚠️ np1 contains out-of-bounds samples (needs investigation)

## Algorithm Validation Status

**Core Algorithm**: ✅ **VALIDATED**
- Correctly detects delta function pileups
- Handles bilateral stickiness
- Sub-percent sensitivity confirmed (0.45-0.62% range)

**Edge Cases Identified**:
1. Out-of-bounds samples (u<0 or u>1) → False positive detection

**Production Readiness**: ✅ **READY** with caveats
- Works correctly on valid data (e_dv_pp, e_dv_ap, A_He)
- Needs input validation for out-of-bounds samples
