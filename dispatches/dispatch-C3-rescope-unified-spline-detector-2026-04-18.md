# Dispatch: C3 re-scope — unified `|x − c|` spline detector

**Generated:** 2026-04-18
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** code + analysis
**CPM task:** `calibration-derivative-refine` (unfreezing C3 with new scope)
**Depends on:** `calibration-swefc-harness` (Task #2 must exist so this dispatch can validate against its output)
**Supersedes:** prior C3 framing (derivative-based refinement as narrow tweak on existing kneedle path)

## Scope

Three integrated changes, shipped together, validated in parallel
with the current detectors before any replacement:

1. **Coordinate unification.** Replace the boundary vs. interior
   dichotomy with a single primitive: `d = |x − c|` parameterized by
   a reference point `c` and a `center_type ∈ {lower, upper, interior}`.
   The fold is geometrically free — samples on the wrong side of a
   bound don't exist; interior stickiness is bilateral by definition.
2. **Dense ECDF grid.** Replace the 30-point log-spaced `quantile_grid`
   with ~1000 log-spaced eps points (or use the native ECDF — see
   Open Items). Compute is cheap; the detection runs once per
   parameter per dataset.
3. **Kneedle → monotonic spline + analytic second derivative.** Fit
   a monotonic C² cubic spline to the dense mass curve in `log ε`
   space. Pileup width `eps*` = argmax of `d²M/d(log ε)²`. No
   sensitivity parameter, fully analytic, residual-based uncertainty.

The null-reference model differs by `center_type` and is preserved:

- `lower` / `upper`: uniform-in-tolerance tail (current boundary null)
- `interior`: local-density null (KDE or off-center window — current
  interior.py's histogram baseline is the starting point)

## Motivation

- **Current interior.py is locus-blind.** It folds around `x0` only.
  `ab.a` has `x0=0` but the empirical interior spike is at `x=1`; the
  detector would mistake L=0 boundary stickiness for the interior
  feature and miss the x=1 spike entirely. `e.w.a` has two interior
  loci (0 and −25); interior.py handles one per call.
- **Current kneedle path is tunable but not analytic.** Sensitivity
  parameter `S`, perpendicular-to-chord heuristic, and discrete
  second-difference estimation all introduce implementation choices
  that don't map cleanly to the underlying "where does density drop
  from pileup to background?" question.
- **30-point grid was a kneedle-era compromise.** With splines,
  denser sampling stabilizes the second derivative at negligible
  compute cost.
- **Visual evidence.** The e.dv.ap interior mass curve (2026-04-18)
  shows a clean elbow structure that spline-argmax handles naturally.

## Read First

1. `dispatches/ground_truth_swefc.json` — 12 parameters, including
   `interior_locations` lists (e.w.a has two; ab.a has one at x=1 ≠ x0).
2. `analyze_swefc_calibration.py` (from harness dispatch) — the driver
   this dispatch's parallel detector runs alongside.
3. `src/fitqc/boundary.py:_compute_quantile_curves_boundary` (lines
   148–218) — current boundary mass curve + kneedle elbow detection.
4. `src/fitqc/interior.py` lines 1–100 — current interior pipeline;
   z-transform centered on `x0`, histogram spike + kneedle.
5. `src/fitqc/config.py` — `BoundaryConfig.quantile_grid` (current
   30 log-spaced points), `InteriorConfig` equivalents.
6. Prior methodology discussion captured in the plan file
   `/Users/balterma/.claude/plans/do-not-execute-the-zippy-cake.md`
   (Revisions section plus C3 references).

## Work plan

### Phase 1: prototype in parallel (no src edits)

Create `dispatches/prototype_unified_spline_detector.py`:

- Function `unified_detect(samples, c, center_type, *, n_eps=1000,
  null_model=None) -> {spike_detected, eps_star, eps_star_err,
  mass_curve, spline_fit}`.
- For each parameter in `ground_truth_swefc.json`, iterate over
  `{L, U} ∪ interior_locations` and call `unified_detect` per center.
- Emit `dispatches/unified_detector_comparison_report.md` with, per
  parameter per center: `eps*_current` (kneedle from existing
  detectors via `analyze_swefc_calibration.py`) vs. `eps*_spline`,
  delta in decades, spike verdict agreement, and where they diverge.
- Emit `figures/unified_detector_overlay.pdf`: per-parameter panels
  showing mass curve + both cut positions overlaid.

### Phase 2: validation

- Run prototype on swefc.h5 via the harness output (which must exist
  from Task #2).
- Also run on 10k parquet subset as a sanity check — the detector
  should not regress the existing subset TPs.
- Acceptance: spline-detector `eps*` within ±0.5 decade of kneedle
  on the 14 current boundary TPs where CSV has scale hints; interior
  multi-locus cases (`ab.a` at x=1, `e.w.a` second locus at −25)
  produce nonzero detections the current interior.py misses.
- If any significant divergence: investigate per ground-truth / visual
  inspection before deciding which is correct.

### Phase 3: integration (gated on Phase 2 passing)

Only after parallel validation passes:

- Create `src/fitqc/detector.py` with the unified primitive. Do NOT
  delete `boundary.py` or `interior.py` yet — keep both live behind a
  config flag (`BoundaryConfig.detector_mode ∈ {legacy, unified}`).
- Wire `analyze_swefc_calibration.py` to default to `unified`.
- Migrate tests to cover both modes; no test suite regressions.
- Legacy removal is a separate downstream dispatch after one full
  calibration pass confirms unified detector is at parity or better.

## Acceptance Criteria

### Phase 1–2 deliverables
- [ ] `dispatches/prototype_unified_spline_detector.py` committed.
- [ ] `dispatches/unified_detector_comparison_report.md` committed
      with per-parameter per-center kneedle-vs-spline `eps*` deltas.
- [ ] `figures/unified_detector_overlay.pdf` committed.
- [ ] Report explicitly covers: `ab.a` at x=1, `e.w.a` at {0, −25},
      and all boundary cases where `analyze_overrides.py` currently
      reports a TP.
- [ ] No `src/fitqc/` edits in Phase 1–2.

### Phase 3 (gated)
- [ ] `src/fitqc/detector.py` committed with unified primitive.
- [ ] `BoundaryConfig.detector_mode` added; default = `legacy` at
      first commit (safety), flipped to `unified` after one green
      harness run.
- [ ] `pytest tests/ -q` green in both modes.
- [ ] `analyze_overrides.py` output unchanged under `legacy` mode
      (byte-identical on subset).
- [ ] `analyze_swefc_calibration.py` runs under `unified` and
      reports pass/fail per `ground_truth_swefc.json`.

## Anti-Patterns

- Do NOT delete `boundary.py` or `interior.py` in this dispatch.
- Do NOT remove kneedle before parallel validation shows the spline
  detector is at parity or better on current TPs.
- Do NOT re-introduce a sensitivity knob analogous to kneedle's `S`.
  If the spline detector needs tuning, the tuning parameter is the
  spline smoothing level (or knot count), not an ad-hoc sensitivity.
- Do NOT change the ECDF coordinate fold beyond `|x − c|`. If a
  parameter appears to need signed treatment, surface as an open
  item rather than special-casing.
- Do NOT silently change the null-reference model. `lower/upper` stay
  uniform-tail; `interior` stays local-density. Changes to null
  models belong in a separate dispatch.
- Do NOT skip the interior multi-locus cases (`e.w.a`, `ab.a`);
  these are the primary motivation.

## Open Items

- **Dense grid vs. native ECDF.** Phase 1 prototype should try both
  and report which gives cleaner second-derivative behavior:
  - (a) 1000 log-spaced eps points + cubic spline
  - (b) Raw folded distances, isotonic regression + smoothing spline
  Pick the simpler of the two if both produce equivalent `eps*`.
- **Spline type.** `scipy.interpolate.CubicSpline` (natural BC) vs.
  `UnivariateSpline` with `s=0, k=3` vs. `csaps` (shape-constrained).
  Choose in Phase 1; default proposal is `CubicSpline` and verify
  monotonicity of the fit (should be true for any true mass curve).
- **Log-eps derivative vs linear-eps derivative.** The elbow is
  visually clearest in log-eps space. Fit and differentiate in
  `log ε`. State this explicitly in the prototype.
- **Interior null model.** Current interior.py uses histogram
  background for the spike-existence check. This is orthogonal to
  `eps*` width estimation. Phase 1 preserves it; any null-model
  changes are a separate dispatch.
- **Uncertainty reporting.** Spline residual gives an error bar on
  `eps*`. Decide in Phase 1 whether to report it in the harness
  output columns or only in diagnostic plots.

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc

# Phase 1-2 (no src edits)
python dispatches/prototype_unified_spline_detector.py \
  --h5 ./swefc.h5 \
  --truth dispatches/ground_truth_swefc.json \
  --report dispatches/unified_detector_comparison_report.md \
  --figure figures/unified_detector_overlay.pdf

# Phase 3 (after approval)
python -m pytest tests/ -q
python analyze_overrides.py   # byte-identical under detector_mode=legacy
python analyze_swefc_calibration.py --h5 ./swefc.h5 \
  --detector-mode unified \
  --truth dispatches/ground_truth_swefc.json
```

## Out of Scope

- C4 (broad-pileup algorithm) — independent track; its fix to
  `_compute_quantile_curves_boundary` may land before or after this;
  unified detector inherits whichever algorithm is current under
  `detector_mode=legacy`.
- Null-model changes for interior (local-density estimation
  improvements).
- Removal of legacy detectors — separate downstream dispatch.
- Signed-distance / asymmetric-pileup handling. Stickiness is
  defined as above-L, below-U, bilateral-around-interior; the fold
  is correct for all three.
