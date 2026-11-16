# Script index

Generated from each script's docstring (first line and `Usage:` line).


## analysis

- `analysis/__init__.py`: 
- `analysis/compare_results.py`: Compare two result folders (e.g. a fresh re-run against the delivered results_v16): every CSV and JSON file present  
  `Usage: python compare_results.py REFERENCE_DIR RERUN_DIR [--tol 1e-9]`
- `analysis/sr_screen.py`: Post hoc step-regularity (SR) screen (exploratory).  
  `Usage: python sr_screen.py RESULTS_DIR [OUT_JSON]`
- `analysis/v15_extra.py`: V15 supplementary computations (run after v15_stats.py). Labelled post hoc where applicable.  
  `Usage: python v15_extra.py RESULTS_V11 RESULTS_V15`
- `analysis/v15_stats.py`: V15 statistics on the outputs of run_features.py (+ the primary results folder).  
  `Usage: python v15_stats.py RESULTS_V11 RESULTS_V15 [B]`
- `analysis/v15_text_numbers.py`: Recompute, from results_v11 outputs, the descriptive numbers quoted in the V15 text that were first obtained  
  `interactively (audit for V16). Usage: python v15_text_numbers.py RESULTS_V11`
- `analysis/v16_endtoend_stats.py`: Statistics for the V16 end-to-end experiment (test set; participant = unit of analysis).  
  `Usage: python v16_endtoend_stats.py E2E_OUT`
- `analysis/v16_external_stats.py`: Statistics for the frozen DUO-GAIT external validation. Unit of analysis: participant (16); passes nested in walks  
  `nested in participants. Usage: python v16_external_stats.py EXT_DIR`
- `analysis/v16_gyro_offset.py`: V16 failure analysis: uncalibrated head-gyroscope offsets and missing head-only (B1) output.  
  `Usage: python v16_gyro_offset.py PACK.npz RESULTS_V11 E2E_DIR`
- `analysis/v16_post_b_checks.py`: POST HOC checks requested in the V16.3 review (added after the V16 draft; reported as post hoc).  
  `Usage: python analysis/v16_post_b_checks.py PACK.npz RESULTS_V11 E2E HEAD_NPZ PROCESSED_ZIP SENS_ROWS OUT [--jobs N]`
- `analysis/v16_post_clinical.py`: V16 post hoc: errors relative to the smallest detectable change of cadence.  
  `Usage: python v16_post_clinical.py RESULTS_V11 E2E_DIR POST_DIR`
- `analysis/v16_post_compute.py`: V16 post hoc: computational cost of the head-only pipelines.  
  `Usage: python v16_post_compute.py PACK.npz RESULTS_V11 E2E_DIR OUT_DIR [--n 60]`
- `analysis/v16_post_drift_rate.py`: POST HOC (added after V16.2 review, SIMULATION): mounting drift with its own angular rate.  
  `Usage: python analysis/v16_post_drift_rate.py PACK.npz RESULTS_V11 E2E_OUT OUT [--n N]`
- `analysis/v16_post_eargait.py`: V16 post hoc: a published open-source head/ear-worn step detector as an external baseline.  
  `Usage: python v16_post_eargait.py PACK.npz RESULTS_V11 E2E_DIR OUT_DIR [--jobs N]`
- `analysis/v16_post_gyrocal.py`: V16 post hoc analysis: does a resting zero-rate (gyroscope offset) calibration remove the head-only failures?  
  `Usage: python v16_post_gyrocal.py PACK.npz RESULTS_V11 E2E_DIR OUT_DIR [--jobs N] [--set dev|test] [--window head|ref]`
- `analysis/v16_post_gyrocal_rule.py`: V16 post hoc: choose WHEN to apply the head-only zero-rate calibration on the DEVELOPMENT set, then test once.  
  `Usage: python v16_post_gyrocal_rule.py E2E_DIR POST_DIR [--window head|ref]`
- `analysis/v16_post_stats.py`: V16 post hoc statistics (requested after the V16 draft; labelled post hoc in the manuscript).  
  `Usage: python v16_post_stats.py RESULTS_V11 E2E_DIR TRUST_DIR EXT_DIR POST_DIR`
- `analysis/v16_trust_extra.py`: Extra V16 trust statistics: Q1 AUROC on segments with SR, and participant-bootstrap CIs for the VGA>=3 / CVA  
  `false-exclusion and retention differences between Q2 variants and Q1. Usage: python v16_trust_extra.py TRUST_DIR`
- `analysis/v17_band_sensitivity.py`: V17, POST HOC: sensitivity of the head A1 result to the band low cut-off, all 260 participants.  
  `Usage: python analysis/v17_band_sensitivity.py PACK.npz RESULTS_V11 OUT [--jobs N]`
- `analysis/v17_cohort_table.py`: V17 restructuring (post hoc presentation of prespecified B0 outcomes): cohort-stratified head vs lower-back table  
  `Usage: python analysis/v17_cohort_table.py RESULTS_V11 OUT`
- `analysis/v17_crossval.py`: V17, POST HOC: participant-level cross-validation of the head-only B0 analysis on all 260 participants.  
  `Usage: python analysis/v17_crossval.py PACK.npz RESULTS_V11 OUT [--jobs N] [--folds 5] [--seed 20261112]`
- `analysis/v17_fig_cis.py`: Participant-bootstrap 95% CIs for the V17 figures (post hoc, descriptive).  
  `Usage: python analysis/v17_fig_cis.py RESULTS_V11 TRUST_DIR OUT_JSON`
- `analysis/v17_fig_examples.py`: Extract two example straight segments (head A1, B0 pipeline) for Fig. 4(c, d): band-passed signal, detected steps  
  `Usage: python analysis/v17_fig_examples.py RESULTS_V11 PACK.npz TRUST_DIR OUT.npz TRIAL:SEG [TRIAL:SEG ...]`
- `analysis/v17_flag_by_kind.py`: V17, POST HOC: share of segments flagged by the SR screen (Q1, sr_trial < 0.32) by large-error location  
  `Usage: python analysis/v17_flag_by_kind.py TRUST_DIR HEAD_TRUNK_DIR`
- `analysis/v17_head_trunk.py`: V17, POST HOC: does the head move apart from the trunk in segments where only the head cadence fails?  
  `Usage:  python analysis/v17_head_trunk.py RESULTS_V11 OUT --root VOISARD_ROOT [--jobs N]`
- `analysis/v17_peak_sensitivity.py`: V17, POST HOC: sensitivity of head A1 (B0, fixed test split) to the fixed peak-detection parameters.  
  `Usage: python analysis/v17_peak_sensitivity.py PACK.npz RESULTS_V11 OUT [--jobs N]`
- `analysis/v17_ref_check.py`: V17, POST HOC: could some 'large errors' be errors of the reference (foot-IMU heel strikes) rather than of the IMUs?  
  `Usage: python analysis/v17_ref_check.py RESULTS_V11 PACK.npz OUT_DIR`
- `analysis/v17_review2.py`: V17, POST HOC checks for a second critical review (B0, A1, fixed split, test set). Descriptive; not prespecified.  
  `Usage: python analysis/v17_review2.py RESULTS_V11 PACK.npz TRUST_DIR OUT_DIR`
- `analysis/v17_reviewer_checks.py`: V17, POST HOC reviewer checks (B0, A1, fixed split).  
  `back too. Usage:`
- `analysis/v18_analysis.py`: V18: component ablation, failure mechanisms, theory checks and operating envelope from v18_ext_{dev,test}.csv.  
  `Usage: python analysis/v18_analysis.py EXT_DIR OUT.json [--locs HE,LB]`
- `analysis/v18_b1.py`: V18: frozen AGS applied to the head-only B1 segments on the Voisard test set (same B1 segments as published;  
  `cadence recomputed with AGS over each B1 segment). Usage: python analysis/v18_b1.py PACK E2E_DIR OUT_DIR`
- `analysis/v18_duogait.py`: V18 external check on DUO-GAIT (16 healthy adults), frozen: AGS vs the published peak estimator on the reference  
  `Usage: python analysis/v18_duogait.py HEAD_NPZ PROCESSED_ZIP E2E_DIR OUT_DIR`
- `analysis/v18_eval.py`: V18: one-shot evaluation of the frozen AGS estimator against the published peak estimator (A1, median step  
  `Usage: python analysis/v18_eval.py RESULTS_V11 OUT --root VOISARD_ROOT [--set test] [--locs HE,LB] [--jobs N]`
- `analysis/v18_ext.py`: V18 extended per-segment table for the ablation, failure mechanisms and operating envelope (B0 straight segments).  
  `Usage: python analysis/v18_ext.py RESULTS_V11 OUT --root ROOT --set dev|test --locs HE,LB [--jobs N]`
- `analysis/v18_extract.py`: V18 method development: extract per-trial signals for one split only (default: development set).  
  `Usage: python analysis/v18_extract.py RESULTS_V11 PACK.npz OUT.pkl [--set dev|test] [--loc HE]`
- `analysis/v18_methods.py`: V18 candidate cadence estimators for straight segments (B0 segmentation). Pure functions of one sensor's signal;
- `analysis/v18_review.py`: V18.2 review checks (post hoc, test set only, nothing re-tuned):  
  `Usage: python analysis/v18_review.py EXT_TEST.csv TRUST_TEST_SCORED.csv OUT.json`
- `analysis/v18_stats.py`: V18 summaries from v18_<split>_segments.csv: per location and estimator, median of participant-median |e_C| and  
  `stride reference. Usage: python analysis/v18_stats.py SEGMENTS.csv OUT.json`
- `analysis/v19_mobgap.py`: V19 (post hoc, test set): open-source Mobilise-D cadence algorithms (mobgap) on the same straight segments,  
  `Usage: python analysis/v19_mobgap.py HEAD_PACK LB_PACK|none RESULTS_V11 OUT_DIR`
- `analysis/v19_mobgap_stats.py`: V19: statistics for the Mobilise-D (mobgap) baseline vs AGS and the published peak estimator on the same test  
  `segments; participant bootstrap (2000); both reference definitions. Usage:`
- `analysis/v19_sensor_req.py`: V19 (SIMULATION on recorded signals, test set, head): sensor requirements for the frozen AGS estimator.  
  `Usage: python analysis/v19_sensor_req.py HEAD_PACK RESULTS_V11 B1_SEGMENTS_CSV OUT_DIR`
- `analysis/v19_sensor_req_paired.py`: V19: paired differences (perturbation minus as-recorded) for the sensor-requirement simulations; participant  
  `bootstrap (2000). Large error counts no output as failure. Usage: python analysis/v19_sensor_req_paired.py OUT_DIR`
- `analysis/v19_transmission.py`: V19 (post hoc, descriptive): the forehead as a sensing site. Head-versus-trunk (L4/L5) transmission of the  
  `Usage: python analysis/v19_transmission.py HEAD_PACK LB_PACK RESULTS_V11 EXT_ALL_CSV OUT_DIR`
- `analysis/v19_transmission_v17.py`: V19 (post hoc, descriptive): the forehead as a sensing site, from the per-segment head-trunk measures already  
  `Usage: python analysis/v19_transmission_v17.py HEAD_TRUNK_SEGMENTS_CSV EXT_TEST_CSV OUT_JSON`

## (root)

- `extract_needed.py`: Extract only the files the analysis needs from the Voisard archive (meta, processed, raw HE/LB/LF).  
  `Usage: python extract_needed.py <dataset.zip> <output folder>`

## figures_results

- `figures_results/make_figs_v16.py`: V16 result figures (single column 3.5 in, same style as V15 figures).  
  `Usage: python make_figs_v16.py E2E_DIR TRUST_DIR OUT_DIR RESULTS_V11`
- `figures_results/make_figs_v17.py`: V17 main-text result figures (single column, 3.45 in), one colour code throughout:  
  `Usage: python figures_results/make_figs_v17.py RESULTS_V11 TRUST_DIR V17_DIR OUT_DIR`
- `figures_results/make_figs_v18.py`: V18 figure: the AGS estimator.  
  `Usage: python figures_results/make_figs_v18.py DEV_PKL V18_DIR OUT_DIR`
- `figures_results/make_figs_v18b.py`: V18 figure 6: (a) component ablation on the test set (head and lower back); (b) theory check of Proposition 1:  
  `Usage: python figures_results/make_figs_v18b.py EXT_ROOT_DIR ANALYSIS_JSON OUT_DIR`
- `figures_results/make_figs_v19.py`: V19 figure: the forehead as a sensing site (test set, B0 straight segments).  
  `Usage: python figures_results/make_figs_v19.py SENSOR_REQ_JSON TRANSMISSION_JSON HEAD_TRUNK_CSV EXT_TEST_CSV OUT_DIR`
- `figures_results/make_figs_v20.py`: V20 figure 5: share of head segments with |e_C| > 5 steps/min versus output data rate (simulation on recorded  
  `quantisation step C^2 Delta / 60 at 105 steps/min. Usage: python figures_results/make_figs_v20.py SENSOR_REQ_JSON OUT_DIR`
- `figures_results/make_result_figs.py`: Journal-style result figures (Figs. 4-9), single-column width (3.5 in).  
  `Usage:  python make_result_figs.py <results_dir> <dataset_data_dir> <out_dir> [4 5 6 7 8 9]`
- `figures_results/make_result_figs_vec.py`: Journal-style result figures (Figs. 4-9), single-column width (3.5 in).  
  `Usage:  python make_result_figs.py <results_dir> <dataset_data_dir> <out_dir> [4 5 6 7 8 9]`

## figures_schematic

- `figures_schematic/make_fig1.py`: Fig. 1 (journal line-art style): (a) sensor placement, sagittal view; (b) head close-up with
- `figures_schematic/make_fig2.py`: Schematic figures for V11: Fig.1 sensor placement / frames / lever arm; Fig.2 method flowchart.

## headimu

- `headimu/__init__.py`: Head-IMU step-rhythm analysis for the Voisard et al. (2025) dataset.
- `headimu/dsp.py`: Signal processing primitives used by all branches.
- `headimu/duogait.py`: DUO-GAIT (Zhou et al., Sci Data 2023; Zenodo 8244887) adapter for the frozen V16 external validation.
- `headimu/eargait_diao.py`: Re-implementation of the EarGait (Seifer et al., Sensors 2023; github.com/mad-lab-fau/eargait, v3.4.0) default
- `headimu/endtoend.py`: V16: head-only end-to-end cadence estimation.
- `headimu/evaluate.py`: Per-trial processing: branch signals, candidates, and all trial-level metrics.
- `headimu/features.py`: V15: prespecified head-IMU gait features beyond cadence (step / segment / visit levels).
- `headimu/io_voisard.py`: Loading the Voisard et al. (2025) clinical gait dataset (Sci Data 12:1674).
- `headimu/pipeline.py`: Trial-level workers (top-level functions so they can run in worker processes).
- `headimu/report.py`: Tables (CSV/XLSX) and figures (PNG/PDF) for the paper.
- `headimu/stats.py`: Participant-level statistics: bootstrap CIs, Bland-Altman with repeated measures,
- `headimu/stream_b2.py`: Sample-by-sample (streaming) implementation of the causal head-only pipeline B2 (headimu.endtoend.causal).

## (root)

- `pack_v16.py`: V16 data preparation (run once on the PC; nothing is modified in the existing folders).  
  `Usage`
- `pack_v19_lb.py`: V19 data preparation (run once on the PC; nothing in the existing folders is modified).  
  `Usage: python pack_v19_lb.py --data ..\dataset_extracted --results ..\results_v11 --out ..\v16_data`
- `prep2_v16.py`: V16 data preparation, step 2 (local only, no network).
- `prep3_v16.py`: V16 data preparation, step 3 (local only): extract the DUO-GAIT HEAD files of the four walking conditions.
- `prep4_merge_duogait.py`: V16 data preparation, step 4: merge the four per-condition DUO-GAIT head files written by prep3_v16.py into one  
  `Usage: python prep4_merge_duogait.py V16_DATA_DIR OUT_DIR`
- `run_features.py`: V15 feature extraction (run on the full dataset; statistics are computed afterwards by analysis/v15_stats.py).  
  `Usage`
- `run_pipeline.py`: Head-IMU step-rhythm analysis on the Voisard et al. (2025) dataset.  
  `Usage`
- `run_v16_b2t_eval.py`: Evaluate the exploratory causal variant B2-t (detector parameters from dev_tuning_b2t.csv) once on all trials.  
  `Usage: python run_v16_b2t_eval.py PACK.npz RESULTS_V11 E2E_DIR`
- `run_v16_b2tune.py`: V16 exploratory variant B2-t: causal peak-detector thresholds re-selected on the DEVELOPMENT set.  
  `Usage: python run_v16_b2tune.py PACK.npz RESULTS_V11 E2E_DIR`
- `run_v16_endtoend.py`: V16 task 1: end-to-end head-only cadence (B0 reference-assisted, B1 head-only offline, B2 head-only causal).  
  `Usage: python run_v16_endtoend.py PACK.npz RESULTS_V11 OUT [--jobs N]`
- `run_v16_external.py`: V16 task 3: frozen external validation on DUO-GAIT.  
  `Usage: python run_v16_external.py HEAD_NPZ PROCESSED_ZIP E2E_DIR TRUST_DIR OUT`
- `run_v16_sensitivity.py`: V16 (secondary, SIMULATION): sensitivity of head-IMU cadence to sensor non-idealities, test set.  
  `Usage: python run_v16_sensitivity.py PACK.npz RESULTS_V11 E2E_OUT OUT [--n N]`
- `run_v16_trust.py`: V16 task 2: trustworthiness of head-IMU cadence (Q0 none, Q1 V15 SR rule, Q2 multi-feature error-risk model).  
  `Usage: python run_v16_trust.py PACK.npz RESULTS_V11 E2E_OUT OUT`

## tests

- `tests/check_eargait_ssa_vs_pyts.py`: Check headimu.eargait_diao.ssa_components against the SSA kernel of pyts (used by EarGait).  
  `Usage: python tests/check_eargait_ssa_vs_pyts.py PATH_TO_PYTS_CLONE`
- `tests/make_synthetic_archive.py`: SYNTHETIC data for testing the code paths ONLY. Never use outputs as study results.
