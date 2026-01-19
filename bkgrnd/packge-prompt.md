Create a brand-new standalone Python package repo from scratch implementing fit QC diagnostics for:

1) Boundary stickiness near global bounds (lower/upper separately).
2) Initial-guess/fallback stickiness (interior spike near provided x0), including a **required** spike detector using `scipy.signal.find_peaks`.

Constraints:
- Arrays-only package: algorithms operate on NumPy arrays (no pandas, no HDF5, no file adapters).
- Matplotlib is REQUIRED (plots are essential for validation).
- SciPy is REQUIRED (standard dependency; use `find_peaks` for spike detection).
- Must scale to 6M+ samples: sort once per parameter per stage; use searchsorted + index-based quantiles; avoid repeated sorting per tolerance/epsilon; avoid unnecessary copies.
- Parameters may include normal, log-normal (positive-only), and **signed log-normal** (positive+negative branches).

Defaults (do not ask unless necessary):
- Package/repo name: `fitqc`
- Python: >=3.11
- License: MIT
- Use `src/` layout; config in `pyproject.toml`.
- Tooling: ruff (lint+format), pytest, pre-commit.

Deliverables:
A) Repository scaffold:
- pyproject.toml (PEP 621), src layout
- ruff + pytest config
- pre-commit config (ruff check + ruff format)
- README with quickstart + API overview + method justification notes
- .gitignore

B) Implementation:
- Core modules (NumPy computations; SciPy required for peak detection).
- Matplotlib plotting module (required).
- Stable public API with dataclasses for configuration and results.
- Deterministic synthetic data generator (seeded RNG) used by tests and examples.
- All plotting functions return Figure objects and never call `plt.show()`.

C) Tests (pytest):
- Unit tests for identities/masks, tail-mass via searchsorted, quantile-by-index approximation, elbow selection, precision/ULP helpers.
- Smoke tests on synthetic data with injected artifacts (boundary pile-up and interior x0 spike) across normal, log-normal, and signed log-normal data.
- Spike detection tests:
  - verify `find_peaks` identifies a qualifying near-zero spike when injected,
  - verify it does NOT falsely classify a broad near-zero rise (especially for signed log-normal with x0≈0),
  - verify prominence collapses by a configured factor after applying eps* cut.
- Plot smoke tests (Agg backend) ensuring figures render, include colorbars, and contain expected line counts/axes (including log-magnitude panel).
- End-to-end integration test running full QC on multi-parameter synthetic data, serializing report to JSON, generating plots.

D) Examples:
- `examples/run_array_qc.py` demonstrating:
  - creating synthetic data
  - running interior QC and boundary QC
  - generating and saving plots + JSON report

Repository layout (create these files):
- README.md, pyproject.toml, .pre-commit-config.yaml, .gitignore
- src/fitqc/: __init__.py, config.py, precision.py, sortedops.py, selection.py, interior.py, boundary.py, report.py, synth.py, plot.py
- tests/: test_precision.py, test_sortedops.py, test_selection.py, test_interior.py, test_boundary.py, test_spike_detection.py, test_plot_smoke.py, test_smoke_pipeline.py, test_integration_end2end.py
- examples/: run_array_qc.py

Public API requirements (small and stable):
Dataclasses:
- PrecisionConfig:
  - precision_mode: "auto"|"float32"|"float64"
  - compare_mode: "quantize_to_storage"|"analysis_dtype"
- InteriorConfig:
  - eps_grid (logspace)
  - elbow_rule params
  - ulp_mults
  - quantile grid near 0 for spacing diagnostics
  - histogram settings for spike metric
  - spike detection thresholds (prominence/width/location) and spike-drop validation threshold
  - z_max selection mode (percentile or fixed)
- BoundaryConfig:
  - tols (linspace)
  - elbow_rule params
  - quantile grids near 0 and 1
  - histogram bin settings for overlays
- PlotConfig:
  - colormap name, dpi, figure sizing, alpha, etc.
  - include_log_abs_panel: bool
  - overlay_sign_on_log_abs: bool
- QCSpec (array-level):
  - parameter names list
  - x0 values per parameter (scalars)
  - global L,U per parameter (scalars) OR arrays (broadcasted)
  - optional mask_valid per parameter (boolean array)

Results dataclasses:
- InteriorResult, BoundaryResult, QCReport
- Provide `to_dict()` and JSON serialization.

Core functions:
- compute_u(x, L, U) -> u
- compute_z(x, x0, L, U) -> z
- run_interior_qc(x, x0, L, U, interior_cfg, precision_cfg, *, mask_valid=None) -> InteriorResult
- run_boundary_qc(x, L, U, boundary_cfg, *, mask_valid=None) -> BoundaryResult
- run_qc(params: dict[str, np.ndarray], bounds: dict[str, tuple[L,U] or tuple[np.ndarray,np.ndarray]], x0: dict[str, float], cfgs...) -> (QCReport, masks)

Algorithm requirements (must match):

Boundary QC:
- w = U - L
- u = (x - L)/w; lower proximity = u; upper proximity = 1-u
- tail mass curves:
  - p_lo(t) = P(u <= t)
  - p_hi(t) = P(u >= 1 - t)
- tail quantile spacing near 0 and near 1 using sorted u slices + index-quantiles
- choose minimal t_lo*, t_hi* via transparent elbow/plateau rule on (a) tail-mass curves and (b) spacing summaries; lower and upper may differ
- fixed-bin histogram overlays (linear + signed-log) colored by tolerance with colorbar and increasing zorder (stricter cuts on top)

Interior QC:
- z = abs((x - x0_eff)/w)
- p(eps) = P(z <= eps) over eps grid (logspace) via sorted z + searchsorted
- tail quantile spacing near z≈0
- REQUIRED spike metric using SciPy:
  - build a high-res histogram of z on [0, z_max] where z_max is selected by:
    - z_max_mode="percentile": z_max = percentile(z, z_max_value) (default 1.0 meaning 1st percentile)
    - z_max_mode="fixed": z_max = z_max_value
  - run `scipy.signal.find_peaks` on histogram counts
  - record: peak index, peak z location, prominence, width (bins) using `peak_widths`
  - define candidate “spike at x0” as the peak closest to z=0, if multiple peaks exist
- choose eps* via elbow/plateau on p(eps), then validate with:
  - spike prominence drop after cutting z <= eps*
  - tail spacing normalization improving after cut

### Signed log-normal (positive+negative branches) support (required)
Some parameters may have signed log-normal structure (|x| log-normal-like, x can be +/-). Add explicit diagnostics and robustness:

Interior QC robustness when x0≈0:
- Do NOT treat “many values near 0” alone as initial-guess failure.
- Define an initial-guess failure spike as a **narrow near-zero peak** in the histogram of z, not merely a steep ECDF rise.
- Use `find_peaks` with **prominence AND width** criteria:
  - Detect peaks on histogram counts of z over [0, z_max]
  - Pick the peak closest to z=0 as the candidate
  - Require:
    (a) candidate peak location <= peak_loc_max_z (config; default small, e.g. 5% of z_max or explicit value),
    (b) prominence >= peak_prom_factor * baseline
        where baseline = median(counts) excluding the first few bins (configurable exclude_n_bins),
    (c) peak width <= peak_width_max_bins AND also <= peak_width_max_z (convert bins to z-units via bin width)
- Record spike metrics: z_loc, prominence, width_bins, width_z, baseline.

Validation logic:
- After choosing eps* (via elbow on p(eps)), recompute spike metrics on the kept sample (z > eps*).
- Require and test that spike prominence drops by at least spike_drop_factor when a true injected spike exists.

Signed-log plotting enhancements (required):
- In addition to linear and signed-log histogram panels, add a “log-magnitude” panel:
  - histogram of log10(|x|) for |x|>0
  - optionally split/overlay by sign (x>0 vs x<0) controlled by PlotConfig
- Always report: counts of x==0, x>0, x<0 (and how these change after applying cuts).

Precision policy:
- PrecisionConfig with precision_mode {"auto","float32","float64"} and compare_mode {"quantize_to_storage","analysis_dtype"}
- Switching float32↔float64 assumptions is a one-line config change.
- Provide helper for ULP(x0)/w anchoring of eps grids when desired.

Plot requirements (Matplotlib required):
- All plots must return Figure; do not call show().
- Include colorbars mapping tol/eps to color; increasing zorder with stricter cuts.
- ECDF tail overlays implemented via sorted arrays (avoid heavy objects).
- Signed-log: positives use log bins; negatives use log bins on abs(values); zeros excluded from log panels and counted.
- Performance note: for overlay histograms across many tolerances/eps, compute hist counts with `np.histogram` on filtered arrays; keep N_tols/N_eps moderate in tests/examples, but core must support large grids.

Performance requirements:
- sort once per parameter per stage; reuse searchsorted and slices
- quantiles via integer indexing: idx = (q*(n-1)).astype(int)
- avoid `np.quantile` inside tolerance loops
- avoid unnecessary copies; do not coerce dtypes unless required by PrecisionConfig behavior

Tooling requirements:
pyproject.toml must include:
- dependencies: numpy, matplotlib, scipy
- dev extras: pytest, ruff, pre-commit
- ruff config for lint+format; pytest config (incl. setting MPL backend to Agg in tests)

pre-commit:
- ruff check
- ruff format

Synthetic data coverage (required):
- Implement generators in synth.py for:
  1) Normal-like x (can include negatives)
  2) Log-normal positive-only
  3) Signed log-normal: x = sign * lognormal(magnitude), with configurable sign probability and optionally different branch parameters
- Each generator must support injecting:
  - boundary pile-up near L and/or U (e.g., clipping or mixture with mass near bounds in u-space)
  - interior spike at x0 (fraction exact at x0 or within float quantization)
- Provide a fixed RNG seed interface for determinism.

Test requirements (additional details):
- test_spike_detection must include signed log-normal case with x0≈0 where:
  - WITHOUT injected spike: no qualifying “narrow spike near 0” should be reported (either no peak passes criteria or the candidate fails width/prominence/loc requirements).
  - WITH injected spike: qualifying near-zero peak is detected and prominence drops by >= spike_drop_factor after eps* cut.
- plot smoke test must include the log-magnitude panel and verify:
  - figure contains expected axes (linear, signed-log pos, signed-log neg-abs, log10(|x|) when enabled)
  - a colorbar exists for overlay plots

Definition of done:
- `pip install -e ".[dev]"` works
- `ruff check .` and `ruff format --check .` pass
- `pytest -q` passes
- example script runs and produces plots + JSON report

Implement with type hints and docstrings; keep code modular and testable.

