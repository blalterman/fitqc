# Dispatch: Document e_w_p2 interior 1e-8 machine-precision artifact

**Generated:** 2026-04-17
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** docs + verification
**CPM task:** `calibration-precision-note` (new; independent)

## Scope

Document the second inflection at ε ≈ 1e-8 in e_w_p2's interior mass
curve as a known machine-precision artifact of the upstream data
pipeline that generated the PPA12 parquet files. Add a brief comment
in `src/fitqc/config.py` (near `InteriorConfig.eps_log10_min`)
referencing the explanation. Write an analysis note at
`dispatches/e-w-p2-precision-note-2026-04-XX.md`. Verify current
detection does NOT latch on the 1e-8 knee under default config; if it
does, flag as a bug for a follow-up task (this task does not fix
detection).

## Motivation

User observed two inflections in e_w_p2's interior mass curve (one
at real-scale, one near 1e-8) and confirmed from knowledge of the
upstream data-generation code that the 1e-8 feature is a
machine-precision artifact (float32 serialization or equivalent).
Without documentation, future developers may chase it as a real
pileup. This is a cheap durability improvement.

## Read First

1. `src/fitqc/interior.py` — interior detection that produces the
   mass curve and selects the elbow.
2. `src/fitqc/config.py` — `InteriorConfig.eps_log10_min`,
   `eps_log10_max` defaults and their rationales.
3. `dispatches/ground_truth_validation.csv` — e_w_p2 row (the CSV
   value for interior is the target that the detector should match).
4. `dispatches/boundary_inspection.pdf` — raw e_w_p2 histogram; use
   to verify the 1e-8 artifact visually if desired.

## Implementation protocol

1. **Verification step first**: run `run_interior_qc` on e_w_p2 under
   current defaults (`InteriorConfig()`). Inspect `eps_star` and the
   mass curve.
   - If `eps_star` is the real-scale inflection → document as
     expected behavior; note remains informational.
   - If `eps_star` is the 1e-8 artifact → document AND raise as a
     bug; escalate to user and scope a follow-up fix (this task does
     not implement it).
2. **Write** `dispatches/e-w-p2-precision-note-2026-04-XX.md` with:
   - Observation (two inflections).
   - Confirmed cause (machine-precision in upstream data pipeline;
     attribute to user confirmation during 2026-04-17 review).
   - Empirical verification from step 1.
   - Implication for detection and for future visual-inspection
     work.
3. **Add a 1-2 line comment** near `InteriorConfig.eps_log10_min` in
   `src/fitqc/config.py` referencing the note by path.
4. **Single commit**: `docs(analysis): document e_w_p2 machine-precision artifact`.

## Acceptance Criteria

- [ ] Empirical verification of whether the current detector latches
      on 1e-8 for e_w_p2, with the answer recorded in the note.
- [ ] Analysis note committed at
      `dispatches/e-w-p2-precision-note-2026-04-XX.md`.
- [ ] Comment in `src/fitqc/config.py` points at the note.
- [ ] Single commit on the current branch.

## Anti-Patterns

- Do NOT modify interior detection algorithm or config defaults.
- Do NOT modify raw data or CSV.
- Do NOT silently change `eps_log10_min` to mask the artifact — if
  the detector DOES latch on 1e-8, escalate as a bug; do not fix in
  this task.

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc
python -c "
import pyarrow.parquet as pq, json
from pathlib import Path
from fitqc import run_interior_qc, InteriorConfig
parquet = Path('tests/data/e_w_p2_test_sample.parquet')
meta = json.loads(Path('tests/data/e_w_p2_test_metadata.json').read_text())
x = pq.read_table(parquet).column('values').to_numpy()
result = run_interior_qc(x, meta['x0'], meta['L'], meta['U'], InteriorConfig())
print(f'eps_star = {result.eps_star}')
print(f'spike_detected = {result.spike_detected}')
"

test -f dispatches/e-w-p2-precision-note-2026-04-*.md
grep -n "precision" src/fitqc/config.py
```

## Out of Scope

- Fixing the detector if it latches on 1e-8 (separate follow-up).
- Interior grid-density changes (C1 / D).
- Other parameters' precision-floor investigations.
