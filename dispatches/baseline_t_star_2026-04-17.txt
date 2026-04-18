# Override Review Results (M2/M3)

Full 2^2 factorial experiment on 12 PPA12 datasets.
All configs use `refine_transition=True, use_quantile_analysis=True, grid_mode='progressive'`.

## Summary

### M3
- Helps: 0 / 24
- Hurts: 0 / 24
- No effect: 24 / 24
- Both wrong: 0 / 24
- Interaction: 0 / 24

### M2
- Helps: 0 / 24
- Hurts: 0 / 24
- No effect: 24 / 24
- Both wrong: 0 / 24
- Interaction: 0 / 24

## Interaction Flags

No interactions detected — all override effects are consistent across contexts.

## Per-Override Verdict Table (non-trivial cases)

| Override | Parameter | Side | Verdict |
|----------|-----------|------|---------|
## Marginal Effect Details

Shows detection and threshold changes when toggling each override.

### M3

### M2

## Full Comparison Table

| Parameter | Config | t_lo_raw | t_lo_star | t_hi_raw | t_hi_star | lo_det | hi_det |
|-----------|--------|----------|-----------|----------|-----------|--------|--------|
| A_He | all-on | 0.000000 | 0.016420 | 0.000000 | 0.000100 | T | T |
| A_He | M3-off | 0.000000 | 0.016420 | 0.000000 | 0.000100 | T | T |
| A_He | M2-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| A_He | all-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| e_dv_ap | all-on | 0.006071 | 0.000000 | 0.000000 | 0.011580 | T | T |
| e_dv_ap | M3-off | 0.006071 | 0.000000 | 0.000000 | 0.011580 | T | T |
| e_dv_ap | M2-off | 0.006071 | 0.000000 | 0.000000 | 0.000100 | T | T |
| e_dv_ap | all-off | 0.006071 | 0.000000 | 0.000000 | 0.000100 | T | T |
| e_dv_pp | all-on | 0.000000 | 0.117810 | 0.000000 | 0.041320 | T | T |
| e_dv_pp | M3-off | 0.000000 | 0.117810 | 0.000000 | 0.041320 | T | T |
| e_dv_pp | M2-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| e_dv_pp | all-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| np1 | all-on | 0.001551 | 0.001551 | None | 0.000000 | T | T |
| np1 | M3-off | 0.001551 | 0.001551 | None | 0.000000 | T | T |
| np1 | M2-off | 0.001551 | 0.001551 | None | 0.000000 | T | T |
| np1 | all-off | 0.001551 | 0.001551 | None | 0.000000 | T | T |
| np2 | all-on | 0.000366 | 0.000366 | None | 0.000000 | T | T |
| np2 | M3-off | 0.000366 | 0.000366 | None | 0.000000 | T | T |
| np2 | M2-off | 0.000366 | 0.000366 | None | 0.000000 | T | T |
| np2 | all-off | 0.000366 | 0.000366 | None | 0.000000 | T | T |
| vx | all-on | None | 0.000000 | 0.001590 | 0.001590 | T | T |
| vx | M3-off | None | 0.000000 | 0.001590 | 0.001590 | T | T |
| vx | M2-off | None | 0.000000 | 0.001590 | 0.001590 | T | T |
| vx | all-off | None | 0.000000 | 0.001590 | 0.001590 | T | T |
| vy | all-on | 0.250000 | 0.000000 | 0.147250 | 0.000000 | T | T |
| vy | M3-off | 0.250000 | 0.000000 | 0.147250 | 0.000000 | T | T |
| vy | M2-off | 0.250000 | 0.000000 | 0.147250 | 0.000000 | T | T |
| vy | all-off | 0.250000 | 0.000000 | 0.147250 | 0.000000 | T | T |
| vz | all-on | 0.159531 | 0.000000 | 0.171768 | 0.000000 | T | T |
| vz | M3-off | 0.159531 | 0.000000 | 0.171768 | 0.000000 | T | T |
| vz | M2-off | 0.159531 | 0.000000 | 0.171768 | 0.000000 | T | T |
| vz | all-off | 0.159531 | 0.000000 | 0.171768 | 0.000000 | T | T |
| w_const | all-on | 0.250000 | 0.250000 | 0.000000 | 0.000100 | T | T |
| w_const | M3-off | 0.050983 | 0.000000 | 0.000000 | 0.000100 | T | T |
| w_const | M2-off | 0.250000 | 0.250000 | 0.000000 | 0.000100 | T | T |
| w_const | all-off | 0.050983 | 0.000000 | 0.000000 | 0.000100 | T | T |
| e_w_p1 | all-on | 0.001450 | 0.001450 | 0.009063 | 0.000000 | T | T |
| e_w_p1 | M3-off | 0.001450 | 0.001450 | 0.009063 | 0.000000 | T | T |
| e_w_p1 | M2-off | 0.001450 | 0.001450 | 0.009063 | 0.000000 | T | T |
| e_w_p1 | all-off | 0.001450 | 0.001450 | 0.009063 | 0.000000 | T | T |
| e_w_p2 | all-on | 0.001000 | 0.001000 | None | 0.000000 | T | T |
| e_w_p2 | M3-off | 0.001000 | 0.001000 | None | 0.000000 | T | T |
| e_w_p2 | M2-off | 0.001000 | 0.001000 | None | 0.000000 | T | T |
| e_w_p2 | all-off | 0.001000 | 0.001000 | None | 0.000000 | T | T |
| e_w_a | all-on | 0.000000 | 0.000100 | 0.000000 | 0.096600 | T | T |
| e_w_a | M3-off | 0.000000 | 0.000100 | 0.000000 | 0.096600 | T | T |
| e_w_a | M2-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| e_w_a | all-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |