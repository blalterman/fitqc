# Analysis note: e_w_p2 machine-precision artifact at eps ~ 1e-8

**Date:** 2026-04-17
**Parameter:** `e_w_p2` (beam thermal-speed perturbation coefficient, PPA12)
**Scope:** Documentation + detector-behavior bug flag. No code or config
fixes in this note.

## Summary

The interior mass curve for `e_w_p2` has two inflections: a physical
inflection at real scale (`|x| < ~0.2` in x-space, `z ~ 2.7e-3`) and a
second inflection at `eps ~ 1e-8` in z-space. The `1e-8` inflection is an
upstream machine-precision serialization artifact (float32 round-trip or
equivalent) from the data pipeline that generates the PPA12 parquet files,
not a physical x0 pileup. Under default `InteriorConfig()`, the detector
latches on the `1e-8` artifact instead of the real-scale inflection. This
is a detection bug; per the governing dispatch it is **flagged here and
addressed in a follow-up**, not patched in this change.

## Observation

Two inflections are visible in `P(z < eps)` for `e_w_p2`:

- Real-scale: `|x| < ~0.2` → `z ~ 2.7e-3`. Physical interior pileup at
  `x0 = 0`.
- Precision-scale: `eps ~ 1e-8` in z-space. Corresponds to `|x| ~ 7.5e-7`
  in original units (z = `|x| / max(x0 - L, U - x0) = |x| / 75`).

## Confirmed cause

The user confirmed on 2026-04-17, based on direct knowledge of the
upstream data-generation code that produced the PPA12 parquet files,
that the `1e-8` feature is a machine-precision serialization artifact
(float32 round-trip or equivalent quantization), not a physical pileup.
This attribution rests on upstream-code knowledge provided by the user,
not on any fitqc self-measurement.

## Empirical verification

Command (dispatch verbatim):

```python
import pyarrow.parquet as pq, json
from pathlib import Path
from fitqc import run_interior_qc, InteriorConfig

parquet = Path('tests/data/e_w_p2_test_sample.parquet')
meta = json.loads(Path('tests/data/e_w_p2_test_metadata.json').read_text())
x = pq.read_table(parquet).column('values').to_numpy()
result = run_interior_qc(x, meta['x0'], meta['L'], meta['U'], InteriorConfig())
```

Outputs under default `InteriorConfig()`:

| Field | Value |
|---|---|
| `eps_star` | `1.0985411419875594e-08` |
| `spike_detected` | `True` |
| `n_samples` | `100000` (seeded uniform subsample of ~7.5M) |

Supporting mass-fraction measurements on the same sample:

| Cut | Fraction of samples |
|---|---|
| `z < 1e-8` | 0.01643 |
| `z < 1e-6` | 0.01646 |
| `z < 1e-3` | 0.01705 |
| `|x| < 0.2` | 0.01761 |

The mass fraction is essentially flat across five orders of magnitude in
`z` (1.643% at `z<1e-8` → 1.705% at `z<1e-3`). This is the signature of a
sharp step at the precision floor: the pileup that the detector sees at
`z ~ 1e-8` is the same physical pileup that exists at `|x| < 0.2`, but
the upstream precision cliff presents the detector with a cleaner,
sharper knee at `z ~ 1e-8` than the knee at real scale, so the elbow
detector prefers the artifact.

The detector's `eps_star = 1.10e-8` matches the value recorded in
`dispatches/ground_truth_validation.csv:12` for `e_w_p2`.

## Implication for detection

The current default detector **latches on the machine-precision artifact**,
returning `eps_star ~ 1e-8` instead of the real-scale inflection at
`z ~ 2.7e-3`. This is a detection bug: it under-reports the
physically-meaningful interior stickiness threshold by roughly five
orders of magnitude.

This note does not fix the bug. A separate follow-up dispatch is the
appropriate vehicle, since a fix involves detector-algorithm changes and
must be reviewed against other parameters that may have legitimately tight
stickiness.

## Follow-up

- Propose a follow-up dispatch: add a precision-aware guard in
  `run_interior_qc` (e.g. an upper-side elbow preference, or a
  data-driven precision floor inferred from the empirical CDF) so the
  detector prefers the real-scale inflection when a precision cliff is
  present.
- Defer any per-parameter tuning (e.g. raising `eps_log10_min` for
  `e_w_p2` only) until the general fix is evaluated, to avoid band-aid
  overrides.

## Assumptions and caveats

- The `e_w_p2` test parquet (`tests/data/e_w_p2_test_sample.parquet`) is
  a seeded uniform-random 100 k subsample of the ~7.5 M full-sample
  source (`ppa12_apeq`). The precision artifact is expected to survive
  uniform subsampling unchanged; this is not verified against the full
  sample.
- The "upstream machine-precision artifact" attribution rests on
  user-provided upstream-code knowledge, not on independent analysis.
  If the upstream code changes to preserve full float64 representation,
  this note becomes stale.
- `eps_star = 1.0985411419875594e-08` is reproducible because
  `InteriorConfig.n_eps = 50` produces a fixed logspace grid; the value
  is the grid point nearest the true artifact knee. Small grid-density
  changes would shift `eps_star` by one grid-point.
- `spike_z_location` is not populated on the current `InteriorResult`
  object (returned `None` via `getattr`); the CSV note's value
  `spike_z_loc=0.005` comes from a separate analysis path and is not
  directly re-verified here.

## References

- `src/fitqc/config.py:113` — `InteriorConfig.eps_log10_min` (default
  `-12`) and the reference comment pointing at this note.
- `src/fitqc/interior.py` — interior detection algorithm.
- `dispatches/ground_truth_validation.csv:12` — e_w_p2 CSV row recording
  `eps_star=1.10e-8` from prior interior.py run.
- `dispatches/dispatch-e-w-p2-precision-note-2026-04-17.md` — governing
  dispatch.
