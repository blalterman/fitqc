# Proposed CPM additions — swefc calibration switch

**Generated:** 2026-04-18
**Status:** proposed only; CPM sync deferred. Do NOT run `/critpath:*`
until user approves.

## New tasks

| ID | Title | Parent | Depends on | Est |
|----|-------|--------|------------|-----|
| `calibration-swefc-ground-truth` | Cal: swefc Ground Truth | `calibration` | (none) | 2h |
| `calibration-swefc-harness` | Cal: swefc Harness | `calibration` | `calibration-swefc-ground-truth` | 6h |
| `calibration-interior-det-swefc` | Cal: Interior Det (swefc delta) | `calibration` | `calibration-swefc-harness` | 3h |

## Notes

- C3 (`calibration-derivative-refine`) stays frozen pending harness results.
- Independent: C4 (`calibration-broad-pileup-algorithm`) — do not gate.
- Task E split proposed separately (see parent-plan amendment).
