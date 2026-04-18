Do *NOT* execute the instructions below. Follow this protocol:

1. Read this prompt in full. Do not read linked files yet.
2. Produce a /plan-draft based only on what you read here. Treat it as your
   hypothesis for HOW to execute the work.
3. Read the dispatch, plan, and other files referenced in the "Read" section
   against your plan-draft — verify it, identify gaps.
4. Revise your plan-draft. Verify it addresses every Acceptance Criterion in
   the dispatch, honors every Anti-Pattern, and resolves every Open Item
   (either by answering or by flagging as a user question). Do not rewrite
   scope or intent — they were reviewed in the prior session.
5. Present the revised plan for user approval. Prefix it with a "Revisions
   from initial draft" section noting what changed between steps 2 and 4.
6. Execute only after user approval.

---

# Launch: Plan the calibration data-source switch (10k subset → swefc.h5)

**Worktree:** new (do not reuse the orchestrator worktree). Create with
`git worktree add ../fitqc-plan-swefc-switch <new-branch>` off the
integration target. Confirm branch name with user before creating.

## Scope

Produce a `/plan-draft` that defines how the project switches its calibration
target from the 10k-sample parquet subset (`tests/data/*.parquet`) to the full
`swefc.h5` dataset, while keeping the test suite running on the subset.
Deliverable is the plan itself plus enumerated follow-on dispatches + launch
prompts, NOT source code changes.

## Context

The PPA12 calibration work (parent plan
`/Users/balterma/.claude/plans/delegated-stargazing-iverson.md`) calibrated
detection against the 10k subset + `dispatches/ground_truth_validation.csv`.
The user has since produced a full-dataset visual-inspection pass using
`dispatches/plot_swefc_fit_param_hists.py` → `figures/swefc_fit_param_histograms.pdf`.
That pass yielded a new bullet-list ground truth over the full data and
motivated switching the calibration target.

## DECIDED (do not renegotiate)

1. Test suite stays on the 10k subset — `analyze_overrides.py` and
   `tests/` fixtures unchanged.
2. Calibration harness is **new** and **swefc-specific** — not a flag / env-var
   on `analyze_overrides.py`. Naming must be unambiguously full-data; final
   name is this plan's call.
3. C3 (`calibration-derivative-refine`) remains frozen and is re-scoped
   AFTER this plan lands.
4. The broad-pileup algorithm dispatch
   (`dispatches/dispatch-broad-pileup-algorithm-2026-04-17.md`) is independent
   of this switch and proceeds on its own track.
5. CPM sync is deferred during this planning session; the plan may propose
   CPM additions but no `/critpath:*` calls happen during planning.

## PROPOSED (plan should validate / refine)

1. User-provided bullet list becomes the authoritative ground truth for the
   full dataset. CSV may be retained for cross-reference on the subset.
2. Harness name along the lines of `analyze_swefc_calibration.py` — plan picks.
3. C1's Q_EXTENDED grid default (commit 6bac9e9) carries over unchanged until
   full-data widths prove otherwise.
4. D (interior-det) re-validates on full data post-harness.
5. Parent plan Task E (`calibration-end-to-end`) shifts to use the new harness.

## Open items the plan must resolve

1. Ground-truth arbitration: when the subset CSV and the full-data bullets
   disagree (e.g., CSV "my guess" markers on vy/vz/e_w_p1/e_w_p2 interiors
   that the user has now firmly asserted), which wins for detection?
2. Harness architecture: HDF5 loader, per-parameter partitioning, entry
   point. Identify what can reuse existing functions vs. what must be new.
3. Validation protocol: how do we know the harness is correct? (Smoke test
   on a subset-equivalent slice of swefc.h5? Parity with `analyze_overrides.py`
   on overlapping params?)
4. Dataset provenance: who produces `swefc.h5`, how is it versioned, where
   does it live canonically (not in the repo — currently untracked).
5. Failure mode if Q_EXTENDED doesn't hold on full data — do we re-open C1,
   or branch a follow-up?
6. D re-validation scope: full pass or delta pass (only parameters where
   bullet list diverges from CSV)?
7. Parent plan amendment: does this shift require edits to
   `/Users/balterma/.claude/plans/delegated-stargazing-iverson.md`? (If yes,
   flag as user-approval-required.)

## Read-first (in order)

1. `/Users/balterma/.claude/plans/delegated-stargazing-iverson.md` — parent
   calibration plan; source of truth for A-E scope.
2. `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-calibration-orchestrator-2026-04-17.md`
   — orchestrator charter; describes reviewer/executor split.
3. `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-grid-resolution-2026-04-17.md`
   — C1 dispatch; cites the current calibration AC template.
4. `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-broad-pileup-algorithm-2026-04-17.md`
   — independent open bug; included so the plan does not duplicate or
   conflict with it.
5. `/Users/balterma/observatories/code/fitqc/dispatches/ground_truth_validation.csv`
   — current subset-derived ground truth.
6. `/Users/balterma/observatories/code/fitqc/dispatches/plot_swefc_fit_param_hists.py`
   + `figures/swefc_fit_param_histograms.pdf` — full-dataset visual
   inspection the bullet list came from.
7. `/Users/balterma/observatories/code/fitqc/analyze_overrides.py` (lines 1-80)
   — current harness pattern; the new harness should be independent.
8. `/Users/balterma/observatories/code/fitqc/src/fitqc/config.py` and
   `src/fitqc/boundary.py:_compute_quantile_curves_boundary` (lines 148-218)
   — production detection path; the switch does not modify these.

## User-provided full-data bullet list (ground truth under proposal)

From `figures/swefc_fit_param_histograms.pdf` (user visual inspection, 2026-04-17):

- `v_param.x.py` (vx): lower + upper boundary
- `v_param.y.p1` (vy): lower + upper boundary + interior
- `v_param.z.py` (vz): lower + upper boundary + interior
- `w.const` (w_const): lower + upper boundary
- `n_param_p1` (np1): lower + upper boundary
- `n_param_p2` (np2): lower + upper boundary + samples below lower that must be cut
- `e.w.p1`: lower + upper boundary + interior (log-x: |x| < 1e-3 will remove some interior)
- `e.w.p2`: lower + upper boundary + interior (log-x: |x| < 1e-3 will remove some interior)
- `e.w.a` (e_w_a): lower + upper + interior at 0 + interior at -25
- `e.dv.pp`: lower + upper + interior
- `e.dv.ap`: lower + upper + interior
- `ab.a` (= A_He): lower + upper + interior

Everything else is out-of-scope for calibration.

## Deliverable

1. Approved `/plan-draft` (via ExitPlanMode) covering the open items above.
2. One or more follow-on dispatches (e.g., `dispatch-swefc-harness-…`,
   `dispatch-swefc-ground-truth-arbitration-…`) — authored in the plan
   chat or routed to a dedicated `/dispatch` session.
3. Matching launch prompts for executor sessions.
4. Proposed CPM task additions, staged but not applied (CPM sync deferred).
5. Any proposed amendments to the parent calibration plan flagged for
   user approval (do NOT edit that plan file).

## Anti-patterns

- Do NOT silently replace the CSV ground truth with the bullet list —
  explicit arbitration is a required deliverable.
- Do NOT extend `analyze_overrides.py` to handle swefc.h5. The harness
  is new and swefc-specific by user directive.
- Do NOT run empirical checks (pytest, analyze_overrides.py, any harness)
  from the plan session. Planning only.
- Do NOT modify `src/fitqc/` in the plan session. That happens in
  dispatch-defined executor sessions.
- Do NOT modify the parent calibration plan
  (`/Users/balterma/.claude/plans/delegated-stargazing-iverson.md`) —
  propose amendments, await user approval.
- Do NOT touch CPM (`/critpath:*`) — sync deferred.

## Prerequisites already satisfied

- C1 `calibration-grid-resolution` complete (commits 6bac9e9..cdee81f).
- C2 `calibration-plot-axis-scale` complete (per user assertion).
- C4 `calibration-precision-note` complete (per user assertion).
- D `calibration-interior-det` complete (commits 1fab4ac..3e16ae7 +
  reviewer sufficiency confirmed).
- C3 frozen pending this plan.
- Broad-pileup bug documented at
  `dispatches/dispatch-broad-pileup-algorithm-2026-04-17.md`.

## Success criterion

User approves the plan via ExitPlanMode; dispatches and launches are
written; the orchestrator chat can resume routing with a clear map of
the downstream work.
