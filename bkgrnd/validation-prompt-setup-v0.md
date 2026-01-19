You are working in a **Jupyter notebook**. Use only: **numpy, pandas, matplotlib, scipy** (no statsmodels). The dataset has **6M+ rows**, so optimize for speed and memory: avoid repeated sorting; prefer `searchsorted` and quantiles via indexing on sorted arrays.

### 0) Start by asking me (required)
1) Ask me for the **HDF5 path** and list available keys:
   - Use `pd.HDFStore(H5_PATH).keys()` to print keys.
2) Ask: **“Which HDF5 key should I load with `pd.read_hdf`?”**
3) Ask me for guidance on the **data format**, specifically:
   - Which columns are the fitted parameter values to QC? (list of column names)
   - Which columns store the **lower/upper bounds** for each parameter? (even though bounds are global, they’re stored per-row)
   - Are there fit-quality/status fields (success flag, iterations, cost/chi2, covariance)? If yes, which columns?
   - I will provide **initial guesses** `x0` per parameter (likely constants). Ask me for a dict mapping `{param_name: x0}` and whether any are per-row.

Do not assume column naming conventions until I answer.

---

## 1) Configuration cell (ALL tunables here; float32↔float64 should be 1-line)
Create a first notebook cell defining:

### Data / IO
- `H5_PATH = "..."` (from me)
- `H5_KEY = None` (from me)
- `OUTPUT_DIR = "..."`

### Precision policy (1-line change)
- `PRECISION_MODE = "auto"`  # "auto" | "float32" | "float64"
- `COMPARE_MODE = "quantize_to_storage"`  # "quantize_to_storage" | "analysis_dtype"
Explanation:
- "auto": infer effective storage dtype from each value column after loading.
- "quantize_to_storage": compare `x` to `x0` after quantizing `x0` to effective dtype.

### Interior (initial guess) epsilon selection
- Use option C by default (sweep + elbow):
  - `EPS_SWEEP_LOG10_MIN = -12`
  - `EPS_SWEEP_LOG10_MAX = -3`
  - `N_EPS = 50`  # log-spaced
- Also compute a resolution-based anchor using ULP at x0:
  - `ULP_MULTS = [1, 2, 4, 8, 16, 32]`  # for sensitivity

### Boundary tolerances
- `TOL_MIN = 0.0`
- `TOL_MAX = 0.05`
- `N_TOLS = 41`  # must be >= 20
- `TOLS = np.linspace(TOL_MIN, TOL_MAX, N_TOLS)`

### Histograms (fixed bins per parameter; reuse across all tolerances)
- `N_BINS_LINEAR = 2000`  # > 500
- `N_BINS_LOG = 2000`
- `ROBUST_PCT = (0.5, 99.5)`  # for bin-range selection
- Signed-log handling:
  - positive values: log bins on x>0
  - negative values: log bins on abs(x) for x<0
  - zeros: exclude from log panels, report count

### Plot styling
- Use tolerance-colored overlays (colormap + colorbar).
- Increase `zorder` with tolerance so stricter cuts sit “on top”.

### Stage order (configurable)
- `RUN_ORDER = ["interior", "boundary"]`  # allow swapping

---

## 2) Load + inspect (pandas only)
- Load: `df = pd.read_hdf(H5_PATH, key=H5_KEY)`
- Print: shape, dtypes, memory usage estimate, missingness summary.
- Extract numpy views for speed: `x = df[col].to_numpy(copy=False)`

---

## 3) Helper functions (write these; keep them small and testable)
### dtype / precision helpers
- `effective_dtype(series, PRECISION_MODE) -> np.dtype`
- `quantize_scalar(val, dtype) -> scalar`
- `ulp_at_scalar(val, dtype) -> float` using `np.nextafter`
- `eps0_from_x0(x0, L, U, dtype, COMPARE_MODE) -> float` where eps0 ~ ULP(x0)/width

### sorting + ECDF/quantiles on sorted arrays (fast path)
Given sorted array `a_sorted` of length n:
- tail-mass at threshold t: `np.searchsorted(a_sorted, t, side="right") / n`
- quantile by indexing: `a_sorted[(q*(n-1)).astype(int)]` for q in [0,1]

### bins (per parameter; fixed across tolerances)
- `make_linear_edges(x_valid, N_BINS_LINEAR, ROBUST_PCT) -> edges`
- `make_log_edges_pos(x_pos, N_BINS_LOG, ROBUST_PCT) -> edges`
- `make_log_edges_neg_abs(abs_x_neg, N_BINS_LOG, ROBUST_PCT) -> edges`

### plotting utilities
- `plot_tolerance_overlays_hist(ax, x, edges, keep_masks_or_ranges, TOLS, title, norm, cmap)`
- `plot_ecdf_tail_overlays(ax, sorted_arr, TOLS, side, title, norm, cmap)`
- `plot_quantile_spacing_overlays(ax, sorted_arr, TOLS_or_EPS, q_grid, title, norm, cmap)`

Ensure plots are saved to OUTPUT_DIR.

---

## 4) Interior QC (initial-guess/fallback) — validate with ECDF + quantiles + one complementary spike test
For each parameter:
1) Determine L and U (global but stored per-row):
   - Verify they are constant: `df[Lcol].nunique()`, `df[Ucol].nunique()`. If not constant, proceed anyway but report.
2) Define width `w = U - L` and scaled coordinate:
   - `g = (x - x0_eff) / w` where `x0_eff` is either `x0` or quantized to effective dtype.
   - `z = abs(g)`  (distance-to-guess in units of fit-width)
3) Baseline validity mask (at minimum):
   - finite x, finite L/U, w>0
   - optionally require fit-success flags if provided (ask me which)
4) Sort once: `z_sorted = np.sort(z_valid)`

### 4A) ECDF tail-mass curve for z
- For EPS grid (logspace from 1e{min} to 1e{max}):
  - `p(eps) = P(z <= eps)` via `searchsorted(z_sorted, eps)/n`
- Plot p(eps) vs eps (log x).

### 4B) Quantile/spacing near zero for z
- Choose dense quantiles near 0: `q = np.linspace(0, 0.1, 300)`
- Quantiles by indexing from `z_sorted`
- Spacings `dz = diff(Q(q))`
- Plot dz vs q (or index), overlays across eps? (optional) but at least baseline.

### 4C) Complementary spike test (must implement at least one)
Use a high-res histogram of z near 0 (e.g., z in [0, z_hi] where z_hi is a small percentile like 1%):
- Compute counts with many bins.
- Use `scipy.signal.find_peaks` on counts (or on a spike-score) with `prominence` to detect a sharp spike at/near 0.
- Report a “spike prominence” metric.

### 4D) Choose eps* (default: sweep+elbow)
- Use Option C: choose the smallest eps after which p(eps) shows diminishing returns.
Implement a simple, transparent elbow rule:
- Work in log-eps space; compute slope of p vs log10(eps) (finite differences).
- Pick first eps where slope drops below a fraction (e.g., < 10% of max slope) and remains low for a few steps.
- Report eps* and fraction removed.

Also report resolution anchors based on ULP(x0)/w * {ULP_MULTS} for sensitivity.

### 4E) Multi-parameter coincidence check (strong evidence of optimizer fallback)
After choosing eps* per parameter, compute per-row:
- `k = number of params with z <= eps*`
Plot distribution of k and report fraction with k>=2, k>=3, etc.
This helps justify that the spike is algorithmic rather than physical.

Save:
- interior mask per parameter: `is_guess_stuck`
- combined interior mask across parameters (user-selectable: any vs all)

---

## 5) Boundary stickiness QC — validate with ECDF + quantiles; generate hist overlays too
For each parameter:
1) Using the same L, U, w:
   - `u = (x - L)/w`  (dimensionless in [0,1])
   - validity: finite u, and optionally within [0,1] (report out-of-range)
2) Sort once: `u_sorted = np.sort(u_valid)`

### 5A) Tail-mass curves vs tolerance (very fast)
For each tol t in TOLS:
- lower tail mass: `p_lo(t) = P(u <= t)` via searchsorted
- upper tail mass: `p_hi(t) = P(u >= 1-t)` = 1 - P(u < 1-t)
Plot p_lo(t), p_hi(t) vs t.

### 5B) ECDF tail overlays (lower and upper separately)
- Plot ECDF near 0 with overlays colored by tolerance:
  - For tol t, “kept” sample is u in (t, 1) for lower-only, or (0, 1-t) for upper-only, or (t,1-t) for both.
To keep this efficient:
- Use sorted u and slicing by indices computed with searchsorted:
  - i0(t) = searchsorted(u_sorted, t, right)
  - i1(t) = searchsorted(u_sorted, 1-t, left)
  - kept slice = u_sorted[i0:i1]
Compute ECDF on the slice via its sorted values (no re-sort).

### 5C) Quantile/spacing diagnostics near u≈0 and u≈1
For each tol t (using kept slice):
- Lower tail quantiles: q in [0, 0.1] of kept slice (index-based quantiles)
- Upper tail quantiles: q in [0.9, 1] (or compute on 1-u for symmetry)
Compute spacing metrics (du) and show overlays vs tolerance with colorbar.

### 5D) Select minimal tolerances t_lo*, t_hi*
Pick smallest t where both:
- tail-mass curve stabilizes (diminishing returns), AND
- tail quantile spacing no longer shows compression / pile-up.

Report separately for lower and upper (they can differ).

### 5E) Histogram overlays (as requested) using fixed bins
Build per-parameter bin edges once (from baseline valid data):
- linear edges (robust percentiles)
- signed-log edges: pos and neg-abs separately
Then for each tolerance, apply range filter in x-space:
- kept lower-only at tol t: x > L + t*w
- kept upper-only at tol t: x < U - t*w
- kept both: (x > L + t*w) & (x < U - t*w)
Using the SAME bin edges, plot step-hist overlays colored by tolerance, with a colorbar, increasing zorder with tolerance.
Do this for:
- Linear bins (1 figure with 2 subplots: lower vs upper cuts)
- Signed-log bins (separate panels for pos and neg-abs; lower vs upper)

Note: report zeros excluded from log panels.

Save all figures and a summary table with:
- eps* (interior) per parameter
- t_lo*, t_hi* (boundary) per parameter
- fractions removed by each stage

---

## 6) Re-check interaction (fast verification)
After removing interior guess-stuck points, re-run boundary selection quickly and report whether t_lo*, t_hi* changed.
If boundary tolerances can be reduced after interior removal, reduce them (this supports “remove as little as necessary”).

---

## 7) Outputs
Write to OUTPUT_DIR:
- Parquet/CSV summary table
- JSON config dump (precision mode, eps sweep, tol sweep, selected thresholds)
- PNG figures
- (Optional) boolean masks saved as NumPy `.npz` or Parquet columns

---

## Notes on interpretation with huge N (6M)
If you compute KS or Anderson-Darling statistics, DO NOT interpret p-values literally; with huge N they will be tiny for small effects. Use statistics as descriptive “change magnitude” curves if included.
(You may include `scipy.stats.ecdf` for ECDF objects, but the sorted-array approach is preferred for speed.)

