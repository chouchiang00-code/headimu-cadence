#!/usr/bin/env bash
# V16 analyses, in order (Linux/macOS). Run from headimu_code/. Inputs (unchanged): ../results_v11, ../v16_data,
# ../external/duogait/processed.zip. Output: ../results_v16. Seeds are fixed inside the scripts (20261022 split,
# 20261023 bootstrap/simulation). JOBS = worker processes for the end-to-end run.
set -euo pipefail
PY=${PY:-python3}; JOBS=${JOBS:-2}
R11=../results_v11; PACK=../v16_data/voisard_head_pack.npz; OUT=../results_v16
E2E=$OUT/e2e; TR=$OUT/trust; EXT=$OUT/ext; SENS=$OUT/sens
mkdir -p "$OUT"
$PY prep4_merge_duogait.py ../v16_data "$EXT"
$PY run_v16_endtoend.py "$PACK" "$R11" "$E2E" --jobs "$JOBS"
$PY run_v16_b2tune.py "$PACK" "$R11" "$E2E"
$PY run_v16_b2t_eval.py "$PACK" "$R11" "$E2E"
$PY analysis/v16_endtoend_stats.py "$E2E"
$PY analysis/v16_gyro_offset.py "$PACK" "$R11" "$E2E"
$PY run_v16_trust.py "$PACK" "$R11" "$E2E" "$TR"
$PY analysis/v16_trust_extra.py "$TR"
$PY run_v16_external.py "$EXT/duogait_head.npz" ../external/duogait/processed.zip "$E2E" "$TR" "$EXT"
$PY analysis/v16_external_stats.py "$EXT"
$PY run_v16_sensitivity.py "$PACK" "$R11" "$E2E" "$SENS"
# post hoc (added after the V16 draft; labelled post hoc in the manuscript, Supplementary Table S6)
POST=$OUT/post; mkdir -p "$POST"
for SET in dev test; do for WIN in head ref; do
  $PY analysis/v16_post_gyrocal.py "$PACK" "$R11" "$E2E" "$POST" --jobs "$JOBS" --set $SET --window $WIN
done; done
$PY analysis/v16_post_gyrocal_rule.py "$E2E" "$POST"
$PY analysis/v16_post_gyrocal_rule.py "$E2E" "$POST" --window ref
$PY analysis/v16_post_stats.py "$R11" "$E2E" "$TR" "$EXT" "$POST"
$PY analysis/v16_post_eargait.py "$PACK" "$R11" "$E2E" "$POST" --jobs "$JOBS"
$PY analysis/v16_post_compute.py "$PACK" "$R11" "$E2E" "$POST" --n 930
$PY analysis/v16_post_clinical.py "$R11" "$E2E" "$POST"
$PY analysis/v16_post_drift_rate.py "$PACK" "$R11" "$E2E" "$POST/drift_rate"
$PY analysis/v16_post_b_checks.py "$PACK" "$R11" "$E2E" "$EXT/duogait_head.npz" ../external/duogait/processed.zip "$SENS/sensitivity_rows.csv" "$POST/b_checks" --jobs "$JOBS"
$PY analysis/v15_text_numbers.py "$R11"
$PY figures_results/make_figs_v16.py "$E2E" "$TR" "$OUT/figures" "$R11" "$EXT"
echo "V16 done: $OUT"
