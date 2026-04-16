# Override Review Results (M1/M2/M3)

Full 2^3 factorial experiment on 12 PPA12 datasets.
All configs use `refine_transition=True, use_quantile_analysis=True, grid_mode='progressive'`.

## Summary

### M1
- Helps: 0 / 24
- Hurts: 0 / 24
- No effect: 24 / 24
- Both wrong: 0 / 24
- Interaction: 0 / 24

### M3
- Helps: 1 / 24
- Hurts: 0 / 24
- No effect: 23 / 24
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
| M3 | w_const | lower | helps |
## Marginal Effect Details

Shows detection and threshold changes when toggling each override.

### M1

### M3

**w_const (lower)** — expected: True
  all-on -> M3-off: det True->False, raw 0.250000->0.050983, star 0.250000->None [helps]
  M1-off -> M1+M3-off: det True->False, raw 0.250000->0.050983, star 0.250000->None [helps]
  M2-off -> M2+M3-off: det True->False, raw 0.250000->0.050983, star 0.250000->None [helps]
  M1+M2-off -> all-off: det True->False, raw 0.250000->0.050983, star 0.250000->None [helps]

### M2

## Full Comparison Table

| Parameter | Config | t_lo_raw | t_lo_star | t_hi_raw | t_hi_star | lo_det | hi_det |
|-----------|--------|----------|-----------|----------|-----------|--------|--------|
| A_He | all-on | 0.000000 | 0.016420 | 0.000000 | 0.000100 | T | T |
| A_He | M1-off | 0.000000 | 0.016420 | 0.000000 | 0.000100 | T | T |
| A_He | M3-off | 0.000000 | 0.016420 | 0.000000 | 0.000100 | T | T |
| A_He | M2-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| A_He | M1+M3-off | 0.000000 | 0.016420 | 0.000000 | 0.000100 | T | T |
| A_He | M1+M2-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| A_He | M2+M3-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| A_He | all-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| e_dv_ap | all-on | 0.006071 | None | 0.000000 | 0.011580 | F | T |
| e_dv_ap | M1-off | 0.006071 | None | 0.000000 | 0.011580 | F | T |
| e_dv_ap | M3-off | 0.006071 | None | 0.000000 | 0.011580 | F | T |
| e_dv_ap | M2-off | 0.006071 | None | 0.000000 | 0.000100 | F | T |
| e_dv_ap | M1+M3-off | 0.006071 | None | 0.000000 | 0.011580 | F | T |
| e_dv_ap | M1+M2-off | 0.006071 | None | 0.000000 | 0.000100 | F | T |
| e_dv_ap | M2+M3-off | 0.006071 | None | 0.000000 | 0.000100 | F | T |
| e_dv_ap | all-off | 0.006071 | None | 0.000000 | 0.000100 | F | T |
| e_dv_pp | all-on | 0.000000 | 0.117810 | 0.000000 | 0.041320 | T | T |
| e_dv_pp | M1-off | 0.000000 | 0.117810 | 0.000000 | 0.041320 | T | T |
| e_dv_pp | M3-off | 0.000000 | 0.117810 | 0.000000 | 0.041320 | T | T |
| e_dv_pp | M2-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| e_dv_pp | M1+M3-off | 0.000000 | 0.117810 | 0.000000 | 0.041320 | T | T |
| e_dv_pp | M1+M2-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| e_dv_pp | M2+M3-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| e_dv_pp | all-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| np1 | all-on | 0.001551 | 0.000100 | None | None | T | F |
| np1 | M1-off | 0.001551 | 0.000100 | None | None | T | F |
| np1 | M3-off | 0.001551 | 0.000100 | None | None | T | F |
| np1 | M2-off | 0.001551 | 0.000100 | None | None | T | F |
| np1 | M1+M3-off | 0.001551 | 0.000100 | None | None | T | F |
| np1 | M1+M2-off | 0.001551 | 0.000100 | None | None | T | F |
| np1 | M2+M3-off | 0.001551 | 0.000100 | None | None | T | F |
| np1 | all-off | 0.001551 | 0.000100 | None | None | T | F |
| np2 | all-on | 0.006061 | 0.006061 | None | None | T | F |
| np2 | M1-off | 0.000366 | 0.000100 | None | None | T | F |
| np2 | M3-off | 0.006061 | 0.006061 | None | None | T | F |
| np2 | M2-off | 0.006061 | 0.006061 | None | None | T | F |
| np2 | M1+M3-off | 0.000366 | 0.000100 | None | None | T | F |
| np2 | M1+M2-off | 0.000366 | 0.000100 | None | None | T | F |
| np2 | M2+M3-off | 0.006061 | 0.006061 | None | None | T | F |
| np2 | all-off | 0.000366 | 0.000100 | None | None | T | F |
| vx | all-on | None | None | 0.001590 | 0.000100 | F | T |
| vx | M1-off | None | None | 0.001590 | 0.000100 | F | T |
| vx | M3-off | None | None | 0.001590 | 0.000100 | F | T |
| vx | M2-off | None | None | 0.001590 | 0.000100 | F | T |
| vx | M1+M3-off | None | None | 0.001590 | 0.000100 | F | T |
| vx | M1+M2-off | None | None | 0.001590 | 0.000100 | F | T |
| vx | M2+M3-off | None | None | 0.001590 | 0.000100 | F | T |
| vx | all-off | None | None | 0.001590 | 0.000100 | F | T |
| vy | all-on | 0.250000 | None | 0.147250 | None | F | F |
| vy | M1-off | 0.250000 | None | 0.147250 | None | F | F |
| vy | M3-off | 0.250000 | None | 0.147250 | None | F | F |
| vy | M2-off | 0.250000 | None | 0.147250 | None | F | F |
| vy | M1+M3-off | 0.250000 | None | 0.147250 | None | F | F |
| vy | M1+M2-off | 0.250000 | None | 0.147250 | None | F | F |
| vy | M2+M3-off | 0.250000 | None | 0.147250 | None | F | F |
| vy | all-off | 0.250000 | None | 0.147250 | None | F | F |
| vz | all-on | 0.159531 | None | 0.171768 | None | F | F |
| vz | M1-off | 0.159531 | None | 0.171768 | None | F | F |
| vz | M3-off | 0.159531 | None | 0.171768 | None | F | F |
| vz | M2-off | 0.159531 | None | 0.171768 | None | F | F |
| vz | M1+M3-off | 0.159531 | None | 0.171768 | None | F | F |
| vz | M1+M2-off | 0.159531 | None | 0.171768 | None | F | F |
| vz | M2+M3-off | 0.159531 | None | 0.171768 | None | F | F |
| vz | all-off | 0.159531 | None | 0.171768 | None | F | F |
| w_const | all-on | 0.250000 | 0.250000 | 0.000000 | 0.000100 | T | T |
| w_const | M1-off | 0.250000 | 0.250000 | 0.000000 | 0.000100 | T | T |
| w_const | M3-off | 0.050983 | None | 0.000000 | 0.000100 | F | T |
| w_const | M2-off | 0.250000 | 0.250000 | 0.000000 | 0.000100 | T | T |
| w_const | M1+M3-off | 0.050983 | None | 0.000000 | 0.000100 | F | T |
| w_const | M1+M2-off | 0.250000 | 0.250000 | 0.000000 | 0.000100 | T | T |
| w_const | M2+M3-off | 0.050983 | None | 0.000000 | 0.000100 | F | T |
| w_const | all-off | 0.050983 | None | 0.000000 | 0.000100 | F | T |
| e_w_p1 | all-on | 0.001450 | 0.000100 | 0.009063 | None | T | F |
| e_w_p1 | M1-off | 0.001450 | 0.000100 | 0.009063 | None | T | F |
| e_w_p1 | M3-off | 0.001450 | 0.000100 | 0.009063 | None | T | F |
| e_w_p1 | M2-off | 0.001450 | 0.000100 | 0.009063 | None | T | F |
| e_w_p1 | M1+M3-off | 0.001450 | 0.000100 | 0.009063 | None | T | F |
| e_w_p1 | M1+M2-off | 0.001450 | 0.000100 | 0.009063 | None | T | F |
| e_w_p1 | M2+M3-off | 0.001450 | 0.000100 | 0.009063 | None | T | F |
| e_w_p1 | all-off | 0.001450 | 0.000100 | 0.009063 | None | T | F |
| e_w_p2 | all-on | 0.001000 | 0.000100 | None | None | T | F |
| e_w_p2 | M1-off | 0.001000 | 0.000100 | None | None | T | F |
| e_w_p2 | M3-off | 0.001000 | 0.000100 | None | None | T | F |
| e_w_p2 | M2-off | 0.001000 | 0.000100 | None | None | T | F |
| e_w_p2 | M1+M3-off | 0.001000 | 0.000100 | None | None | T | F |
| e_w_p2 | M1+M2-off | 0.001000 | 0.000100 | None | None | T | F |
| e_w_p2 | M2+M3-off | 0.001000 | 0.000100 | None | None | T | F |
| e_w_p2 | all-off | 0.001000 | 0.000100 | None | None | T | F |
| e_w_a | all-on | 0.000000 | 0.000100 | 0.000000 | 0.096600 | T | T |
| e_w_a | M1-off | 0.000000 | 0.000100 | 0.000000 | 0.096600 | T | T |
| e_w_a | M3-off | 0.000000 | 0.000100 | 0.000000 | 0.096600 | T | T |
| e_w_a | M2-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| e_w_a | M1+M3-off | 0.000000 | 0.000100 | 0.000000 | 0.096600 | T | T |
| e_w_a | M1+M2-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| e_w_a | M2+M3-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |
| e_w_a | all-off | 0.000000 | 0.000100 | 0.000000 | 0.000100 | T | T |