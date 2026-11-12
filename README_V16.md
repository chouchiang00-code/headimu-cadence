# V16 reproducibility notes

All V16 numbers in the manuscript and supplement come from the scripts below, run on the public data. No parameter
was set by hand after looking at test or external results, except where labelled post hoc (B2-t).

## 1. Data (public, unchanged)

| Data | Source | Used files |
|---|---|---|
| Voisard et al. 2025 | figshare doi:10.6084/m9.figshare.28806086 (data descriptor: Sci. Data 12, 1674, 2025, doi:10.1038/s41597-025-05959-w) | processed HE/LB/foot signals, heel strikes, turn boundaries, clinical metadata; extracted to `dataset_extracted/` |
| DUO-GAIT (Zhou et al. 2023) | Zenodo doi:10.5281/zenodo.8244887 (version 3) | `processed.zip` (2.6 MB, md5 59262239edaab480115ee5dd553587ee), `interim.zip` (3.0 GB, md5 de9ffa7ed1d9ea91e0b6b2e3af5ecda1); downloaded with a browser because scripted download returned HTTP 403 |
| V11/V15 outputs | `results_v11/` (primary analysis, split, development calibration), `results_v15/` | read only |

## 2. Software

Python 3.13; numpy 2.5, scipy 1.18, pandas 3.0, matplotlib 3.11 (PC lock file: `requirements.lock.txt`; the container
used for V16 had numpy 2.5.3, pandas 3.0.5, scipy 1.18.1, matplotlib 3.11.2). No scikit-learn. Manuscript build:
python-docx 1.2.0 (`ieee/build_jsen.py`, IEEE Sensors Journal colorized format). Multiprocessing is used only to speed up the end-to-end run and does not
change results.

## 3. Fixed settings

* **Split**: seed 20261022, 30 % of participants for development, stratified by cohort × sensor system
  (`run_pipeline.py`, stored in `results_v11/qc_trials.csv`): 77 development / 183 test participants,
  421 / 930 trials.
* **Bootstrap / simulation seed**: 20261023 (all V16 scripts); 2000 participant-level resamples.
* **Development-selected (V11)**: band 0.6–3.0 Hz, head lag 0.07 s (A1), turn gate q* = 30 °/s, SR threshold 0.3188.
* **Head-only pipeline** (`results_v16/e2e/endtoend_params.json`): band 0.6–3.0 Hz (3rd-order Butterworth),
  gravity low-pass 0.3 Hz, RMS window 2 s, walking threshold 0.18 m/s² (B1) / 0.20 m/s² (B2, development-selected),
  gap fill 1 s, bout ≥ 3 s, gate 30 °/s (median 0.15 s, ≥ 0.30 s, pad 0.20 s), merge 0.5 s, turn ≥ 90°, segment ≥ 2 s,
  ≥ 3 intervals, prominence max(0.12 m/s², 1.5 σ̂), spacing ≥ 0.30 s; causal: hysteresis 0.7, holds 0.5 / 1.0 s,
  confirmation 0.20 s, trailing-minimum window 0.9 s, running median of 6 intervals; lags 0.07 s (B1), 0.14 s (B2).
* **B2-t (post hoc)**: confirmation 0.30 s, selected on development data among 20 settings (`b2t_params.json`).
* **Error-risk models**: ridge logistic, λ = 1, standardized features, fitted on development segments; threshold at the
  Q1 development flag rate 0.0998 (`results_v16/trust/trust_models.json`).
* **DUO-GAIT adaptation**: g → m/s² (× 9.80665), °/s → rad/s, polyphase resampling 128 → 100 Hz (up 25, down 32);
  every other parameter frozen from Voisard. Reference straight passes: both feet have strides that are neither turning
  nor interrupted.

**Disclosed deviations.** (i) The first development grid for the walking threshold (0.2–1.8 m/s²) selected its edge
and was extended downward before test evaluation (Supplementary Table S5). (ii) B2-t was selected after the first test
evaluation (post hoc). (iii) Q1 AUROC uses the 1858 segments with a defined trial SR.

## 4. Commands (from `headimu_code/`)

Windows: double-click the `.cmd` files in this order. Linux/macOS: the `.sh` equivalent.

| Step | Command | Output |
|---|---|---|
| 1 | `run_v16_pack.cmd` → `pack_v16.py --data ..\dataset_extracted --results ..\results_v11 --out ..\v16_data` | `v16_data/voisard_head_pack.npz` (1351 trials) |
| 2 | (browser) download `processed.zip`, `interim.zip` to `..\external\duogait\` | — |
| 3 | `run_v16_prep3.cmd` → `prep3_v16.py` | `v16_data/duogait_head_<condition>.npz` |
| 4 | `run_v16_all.cmd` (or `bash run_v16_all.sh`) | `results_v16/{e2e,trust,ext,sens,post,figures}` |

`run_v16_all` runs, in order: `prep4_merge_duogait.py` → `run_v16_endtoend.py` (B0 re-run + B1/B2, development
tuning) → `run_v16_b2tune.py` → `run_v16_b2t_eval.py` → `analysis/v16_endtoend_stats.py` →
`analysis/v16_gyro_offset.py` → `run_v16_trust.py` → `analysis/v16_trust_extra.py` → `run_v16_external.py` →
`analysis/v16_external_stats.py` → `run_v16_sensitivity.py` → post hoc block (`analysis/v16_post_gyrocal.py` × 4: `--set dev|test --window head|ref`; `analysis/v16_post_gyrocal_rule.py` with and without `--window ref`; `analysis/v16_post_stats.py R11 E2E TRUST EXT POST`; `analysis/v16_post_eargait.py PACK R11 E2E POST`; `analysis/v16_post_compute.py PACK R11 E2E POST --n 930`; `analysis/v16_post_clinical.py R11 E2E POST`) → `analysis/v15_text_numbers.py` →
`figures_results/make_figs_v16.py`. Run time on a 2-core machine: see Section 6.

Manuscript: `cd ieee; python build_jsen.py main OUT.docx [--bios]; python build_jsen.py supp OUT.docx` (`content_en.py` =
`refs_part.py` + `body_v16.py`; `content_supp.py` builds the supplement from the result files and numbers its items
by first mention in the main text).

To compare a re-run with the delivered results: `python analysis/compare_results.py ..\results_v16_delivered ..\results_v16`.

## 5. Raw outputs

| Folder | Files |
|---|---|
| `e2e` | `b0_segments_all.csv` (B0 re-run, all trials), `endtoend_segments.csv` (per reference segment: B0/B1/B2/B2-t cadence and error), `endtoend_trials.csv` (per trial: walking/turn/step detection, latencies), `dev_tuning_walking.csv`, `dev_tuning_b2t.csv`, `endtoend_params.json`, `b2t_params.json`, `endtoend_stats.json`, `table_endtoend_by_cohort.csv`, `table_endtoend_detection_by_cohort.csv`, `static_gyro_offsets.csv`, `gyro_offset_summary.json` |
| `trust` | `trust_segments_features.csv` (10 features per segment, development + test), `trust_models.json`, `trust_test_scored.csv`, `trust_summary.json`, `trust_extra.json`, `error_coverage_curve.csv`, `trust_operating_points.csv` |
| `ext` | `duogait_head.npz`, `duogait_head_audit.csv`, `external_passes.csv` (per pass: reference and head cadence for B0/B1/B2, SR, risk flags), `external_walks.csv` (detection per walk), `external_stats.json` |
| `sens` | `sensitivity_rows.csv` (per trial × perturbation), `sensitivity_summary.csv` |
| `post` | `gyrocal_segments_{dev,test}[_ref].csv`, `gyrocal_trials_{dev,test}[_ref].csv` (per trial: estimated offset `cal_offset_dps`), `gyrocal_summary.json`, `gyrocal_rule.json` (head-only still window), `gyrocal_rule_ref.json` (known still period), `post_stats.json` (calibration CIs, TOST, threshold sensitivity), `eargait_segments.csv`, `eargait_events.csv`, `eargait_summary.json`, `compute_summary.json`, `clinical_summary.json` — Supplementary Table S6 |
| `figures` | `fig10_endtoend`, `fig11_trust`, `figS_external_ba` (.png/.pdf) |

## 6. Verification of this package (fresh re-run, 2026-10-23)

The complete chain `run_v16_all.sh` was run in an empty output folder from the packed public data, with the delivered
code, and compared with the delivered `results_v16` using `analysis/compare_results.py` (tolerance 1 × 10⁻⁹):

| Folder | Files compared | Result |
|---|---|---|
| `e2e` | 12 (incl. B0 re-run, development tuning, B1/B2/B2-t, statistics, gyroscope offsets) | all identical (max difference 0) |
| `trust` | 7 | all identical |
| `ext` | 4 (incl. DUO-GAIT signal audit) + `duogait_head.npz` | all identical |
| `sens` | 2 | all identical |
| figures | `fig10_endtoend`, `fig11_trust`, `figS_external_ba` (PNG) | pixel-identical |
| V15 text numbers | `analysis/v15_text_numbers.py` | 97/72/70, SR 0.43 vs 0.92, LoA −3.6/3.6, 25.8 %, 75.8 %, 9.1 %, ratio 1.06, 23 vs 16 steps — all reproduced |

Run time: about 30 min on 2 CPU cores (end-to-end ≈ 5 min, trust models with bootstrap ≈ 15 min, external ≈ 5 min,
sensitivity ≈ 3 min). Two steps that were first done interactively — merging the DUO-GAIT head files with their signal
audit, and the gyroscope-offset failure analysis — are now scripts (`prep4_merge_duogait.py`,
`analysis/v16_gyro_offset.py`) and reproduce the delivered files exactly.

## 7. Post hoc additions (2026-10-27)

The post hoc scripts were run in this environment with seeds 20261023 (bootstrap, 2000 resamples; 500 for AUROC CIs). Outputs are in `results_v16/post/`; every number quoted in the manuscript and Supplementary Table S6 is read from `post_stats.json`, `gyrocal_rule.json` and `gyrocal_rule_ref.json`.

Second batch (EarGait comparator, computational cost, clinical scale) run the same day; `tests/check_eargait_ssa_vs_pyts.py PYTS_CLONE` checks the SSA re-implementation. Run-time numbers in `compute_summary.json` are machine-dependent (they are the only outputs that will not reproduce exactly).
