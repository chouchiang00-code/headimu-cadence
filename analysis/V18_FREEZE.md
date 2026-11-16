# V18 estimator freeze (development set only)

Frozen 2026-11-12, before any V18 test-set evaluation. analysis/v18_methods.py sha256 prefix: 64f4b2d92925db99

Development set: 77 participants, 421 trials, 842 straight segments (head A1, B0 segmentation).
Reference: 60 / median reference step interval (published primary definition).

| Estimator | median of participant medians, |e_C| | |e_C| > 5 (%) |
|---|---|---|
| Published peak (median step interval) | 1.570 | 18.1 |
| Peak, median stride | 1.126 | 15.0 |
| Autocorrelation step time | 1.037 | 13.8 |
| AGS (frozen) | 1.027 | 12.9 |

Candidates considered on the development set (and only there): peak count / duration, trimmed mean interval,
gap-repair with the autocorrelation prior, median of three estimators, AC-guided minimum distance 0.55 / 0.65 / 0.75 T,
with and without averaging with the autocorrelation cadence. Selection rule: lowest share of |e_C| > 5; within-dev
participant 5-fold CV selected AGS(0.55) in 3/5 folds and Med3g in 2/5; out-of-fold large-error shares
6.9/11.9/15.7/7.1/25.3 % vs 6.9/18.3/21.7/11.0/27.9 % for the published estimator.

Test evaluation plan (one run): head and lower back, same estimator and same frozen settings; primary outcomes as in
V17 (median of participant medians with participant bootstrap CI; share > 5 steps/min), by cohort; head minus lower
back paired; secondary: stride reference definition; reference-suspect segments excluded as sensitivity; DUO-GAIT B1
with AGS as external check.
