# -*- coding: utf-8 -*-
"""Supplementary Material V16. Items are keyed; their order (and S-numbers) follows the first mention of the
⟪T:key⟫ / ⟪F:key⟫ markers in body_v16.py, so main-text references and supplement numbering cannot drift.
V15 items are taken verbatim from content_supp_v15 (matched by caption/path); new V16 tables are generated
directly from the result files in ../v16res."""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

import content_supp_v15 as V15

HERE = Path(__file__).resolve().parent
import os  # noqa: E402
RES = Path(os.environ["V16_RESULTS"]) if "V16_RESULTS" in os.environ else next(
    (d for d in (HERE.parent / "v16res", HERE.parent / "results_v16") if d.exists()), HERE.parent / "results_v16")
R = {}
TITLE = "Cadence From a Single Forehead IMU in Clinical Cohorts: Comparison With the Lower Back"
FULL = 10440


def _old(kind, key):
    for b in V15.B:
        if b[0] == kind and key in b[1][0]:
            return b
    raise KeyError(key)


def m(x, nd=2):
    s = f"{abs(x):.{nd}f}"
    return ("−" if x < 0 and float(s) != 0 else "") + s


def ci(v, nd=2):
    return f"[{m(v[0], nd)}, {m(v[1], nd)}]"


def T(cap, head, rows, widths, note=None):
    assert sum(widths) <= FULL, (cap, sum(widths))
    assert all(len(r) == len(head) for r in rows), cap
    return ("table", (cap, head, rows, widths, note))


ITEMS = {}  # key -> (section heading, block)
S_PIPE, S_INC, S_B0, S_FEAT = ("Datasets, Pipeline, and Parameters", "Inclusion and Signal Verification",
                               "Reference-Assisted Accuracy (B0)", "Head Features Beyond Cadence")
S_E2E, S_ROB, S_TR, S_EXT = ("Head-Only End-to-End Estimation", "Mounting and Sensor Robustness", "Trustworthiness",
                             "External Validation (DUO-GAIT)")
# ------------------------------------------------------------------------------------------------ V15 items
ITEMS["T:cohort"] = (S_PIPE, _old("table", "Cohort Characteristics"))
ITEMS["F:pipeline"] = (S_PIPE, ("fig", ("fig_ieee/fig2_method_flowchart.png",
    "Processing and evaluation pipeline of the reference-assisted analysis (B0). Red: reference information and random-gate "
    "control; blue: development and test evaluation. The head-only pipelines B1 and B2 replace the reference walking "
    "interval and turn boundaries by head-only detection (main text, Section III-C).", 3.6)))
cap, head, rows, widths, note = _old("table", "Analysis Parameters")[1]
E2EP = json.loads((RES / "e2e" / "endtoend_params.json").read_text())["params"]
rows = [list(r) for r in rows] + [
    ["B1 walking threshold (centred 2-s RMS of band-passed norm)", f"{E2EP['thr_walk']:.2f} m/s²; gaps < 1 s filled; bouts ≥ 3 s",
     "Development-set rule (walking F1)"],
    ["B2 walking threshold (trailing 2-s RMS)", f"on {E2EP['thr_on']:.2f} m/s², off 0.7 × on; holds 0.5 s / 1.0 s",
     "Development-set rule (walking F1)"],
    ["B1/B2 turns", "gate runs merged within 0.5 s; integrated rotation ≥ 90°; segments ≥ 2 s", "Prespecified (V16)"],
    ["B2 peak confirmation; trailing-minimum window", "0.20 s; 0.9 s (B2-t: 0.30 s; 0.9 s)",
     "Prespecified; B2-t re-selected on development data"],
    ["B2 running cadence", "median of the last 6 step intervals within a straight bout", "Prespecified (V16)"],
    ["Head–heel-strike lag B1 / B2 / B2-t", f"{E2EP['lag_b1']:.2f} / {E2EP['lag_b2']:.2f} / 0.14 s", "Development-set median"],
    ["Q2 ridge-logistic models", "λ = 1 on standardized features; threshold at the Q1 development flag rate (10.0%)",
     "Prespecified; development-set rule"],
    ["DUO-GAIT adaptation", "g → m/s², °/s → rad/s, polyphase resampling 128 → 100 Hz; all other values frozen",
     "Prespecified, no fitting"]]
ITEMS["T:params"] = (S_PIPE, T(cap, head, rows, widths, note))
ITEMS["F:inclusion"] = (S_INC, _old("fig", "fig3_inclusion_flow"))
ITEMS["T:qc"] = (S_INC, _old("table", "Signal-Level Verification"))
ITEMS["F:qc"] = (S_INC, _old("fig", "figS1_signal_qc"))
ITEMS["F:example"] = (S_B0, _old("fig", "fig4_example_trial"))
ITEMS["T:events"] = (S_B0, _old("table", "Event-Level Agreement"))
ITEMS["T:strata"] = (S_B0, _old("table", "by Cohort, Sensor System"))
ITEMS["F:cohorts"] = (S_B0, ("fig", ("fig_results/fig6_cohorts.png",
    "Reference-assisted (B0) cadence error by cohort. Participant-level absolute error and share of straight segments with an "
    "absolute error above 5 steps/min for the head and lower-back signals (test set).", 4.0)))
ITEMS["T:feat_valid"] = (S_FEAT, _old("table", "Validity and Within-Visit Reliability"))
ITEMS["T:feat_mount"] = (S_FEAT, _old("table", "Sensitivity of Head Features"))
ITEMS["T:feat_vga"] = (S_FEAT, _old("table", "Association of Head Features"))
ITEMS["T:feat_model"] = (S_FEAT, _old("table", "Discrimination of VGA"))
ITEMS["T:sims"] = (S_ROB, _old("table", "Simulated Mounting Errors"))
ITEMS["F:rewear"] = (S_ROB, _old("fig", "fig8_rewear"))
ITEMS["T:rewear"] = (S_ROB, _old("table", "Cross-Visit Agreement"))
ITEMS["T:gating"] = (S_TR, _old("table", "Turn Detection and Gate"))
ITEMS["F:gating"] = (S_TR, ("fig", ("fig_results/fig9_gating.png",
    "Turn gate versus coverage-matched random removal and the step-regularity screen (reference-assisted segmentation, test "
    "set): gate-minus-random differences in retained-step precision and recall, turn sensitivity and false marks versus "
    "threshold, and large-error share versus the fraction of segments kept.", 4.2)))
ITEMS["T:sr"] = (S_TR, _old("table", "Step-Regularity Screen"))

# ------------------------------------------------------------------------------------------------ V16: end-to-end
ST = json.loads((RES / "e2e" / "endtoend_stats.json").read_text())
tc = pd.read_csv(RES / "e2e" / "table_endtoend_by_cohort.csv")
tc = tc.iloc[tc["group"].map({c: i for i, c in enumerate(["All", "HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"])}).argsort()]
rows = []
for _, r in tc.iterrows():
    rows.append([r["group"], str(int(r["n_participants"])), str(int(r["n_segments"])),
                 " / ".join(f"{r[f'{k}_mae_med']:.2f}" for k in ("B0", "B1", "B2", "B2t")),
                 " / ".join(f"{r[f'{k}_big_or_missing_pct']:.1f}" for k in ("B0", "B1", "B2", "B2t")),
                 " / ".join(f"{r[f'{k}_no_output_pct']:.1f}" for k in ("B1", "B2", "B2t")),
                 " / ".join(f"{r[f'{k}_p90_abs']:.1f}" for k in ("B0", "B1", "B2"))])
BA = ST["bland_altman"]
ba_txt = "; ".join(f"{k.replace('B2t', 'B2-t')} {m(BA[k]['bias'])} ({m(BA[k]['loa_lo'], 1)}, {m(BA[k]['loa_hi'], 1)})"
                   for k in ("B0", "B1", "B2", "B2t"))
pr = "; ".join(f"{d['comparison'].replace('B2t', 'B2-t').replace(' - ', ' − ')}: {m(d['median_diff'])} {ci(d['ci'])}, Holm p = {d['p_holm']:.3f}"
               for d in ST["paired"])
ITEMS["T:e2e_cohort"] = (S_E2E, T(
    "Reference-Assisted (B0) and Head-Only (B1, B2, B2-t) Cadence Error by Cohort (Test Set)",
    ["Cohort", "*n*", "Segments", "Median |*e*_{C}|: B0 / B1 / B2 / B2-t", "|*e*_{C}| > 5 or no output (%): B0 / B1 / B2 / B2-t",
     "No output (%): B1 / B2 / B2-t", "90th pct. |*e*_{C}|: B0 / B1 / B2"],
    rows, [760, 420, 820, 2100, 2340, 1900, 2100],
    "Steps/min; medians of participant-level median |*e*_{C}| over the reference straight segments. A head-only segment without "
    "output counts as a failure in the fifth column and is excluded from the error columns. Bias (95% LoA for repeated "
    f"measurements): {ba_txt}. Paired participant-level differences in median |*e*_{{C}}| [bootstrap 95% CI]: {pr}. "
    "B1/B2 are exploratory; B2-t (causal detector re-selected on development data after the first test evaluation) is post hoc."))
D = ST["detection"]
dc = pd.DataFrame(ST["detection_by_cohort"])
rows = [["All", f"{D['B1_walking_participant_median']['B1_walk_f1']:.3f}", f"{D['B1_turn_prf'][2]:.3f}",
         f"{D['B1_step_f1_participant_median']:.3f}", f"{D['B2_walking_participant_median']['B2_walk_f1']:.3f}",
         f"{D['B2_turn_prf'][2]:.3f}", f"{D['B2_step_f1_participant_median']:.3f}", f"{D['B2t_step_f1_participant_median']:.3f}"]]
order = ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]
dc["o"] = dc["cohort"].map({c: i for i, c in enumerate(order)})
for _, r in dc.sort_values("o").iterrows():
    rows.append([r["cohort"]] + [f"{r[c]:.3f}" for c in ("B1_walk_f1", "B1_turn_f1", "B1_step_f1", "B2_walk_f1", "B2_turn_f1",
                                                         "B2_step_f1", "B2t_step_f1")])


def iqr(k, nd=2):
    v = D[k]
    return f"{m(v[0], nd)} [{m(v[1], nd)}, {m(v[2], nd)}]"


lat = (f"B1 turns: precision {D['B1_turn_prf'][0]:.2f}, recall {D['B1_turn_prf'][1]:.2f}; median boundary error start "
       f"{m(D['B1_turn_start_err_median'])} s, end {m(D['B1_turn_end_err_median'])} s. B2 turns: precision "
       f"{D['B2_turn_prf'][0]:.2f}, recall {D['B2_turn_prf'][1]:.2f}. B2 delays after the reference event, median [IQR] (s): "
       f"step confirmation {iqr('B2_confirm_latency_median_iqr')}; walking onset {iqr('B2_walk_on_delay_median_iqr')}; first "
       f"cadence output {iqr('B2_first_output_delay_median_iqr')}; turn onset {iqr('B2_turn_on_delay_median_iqr')}; turn end "
       f"{iqr('B2_turn_off_delay_median_iqr')}. B2-t: confirmation {iqr('B2t_confirm_latency_median_iqr')}; first output "
       f"{iqr('B2t_first_output_delay_median_iqr')}. Running-cadence error of B2 over all confirmed outputs: "
       f"{D['B2_cont_mae_participant_median']:.2f} steps/min (B2-t {D['B2t_cont_mae_participant_median']:.2f}).")
ITEMS["T:e2e_detect"] = (S_E2E, T(
    "Head-Only Detection Performance by Cohort (Test Set)",
    ["Cohort", "B1 walking F1", "B1 turn F1", "B1 step F1", "B2 walking F1", "B2 turn F1", "B2 step F1", "B2-t step F1"],
    rows, [1000, 1300, 1300, 1300, 1300, 1300, 1300, 1340],
    "Walking F1: sample-level F1 against the reference walking interval (first to last heel strike), median across "
    "participants; turn F1: overlap-based detection of reference turns, pooled; step F1: heel-strike matching with 0.15-s "
    "tolerance after lag correction, median across participants. B2 and B2-t share the walking and turn detectors. " + lat))
tw = pd.read_csv(RES / "e2e" / "dev_tuning_walking.csv")
tw = tw[tw["thr"].round(2).isin([0.04, 0.08, 0.12, 0.16, 0.18, 0.2, 0.3, 0.5, 1.0, 1.5])]
tb = pd.read_csv(RES / "e2e" / "dev_tuning_b2t.csv").sort_values("dev_step_f1", ascending=False)
rows = [[f"{r.thr:.2f}", f"{r.B1_dev_f1:.3f}", f"{r.B2_dev_f1:.3f}"] for r in tw.itertuples()]
pre = tb[(tb.prom_k == 1.5) & (tb.confirm_s == 0.2) & (tb.trail_min_s == 0.9)].iloc[0]
best = ", ".join(f"({r.prom_k:.1f}, {r.confirm_s:.1f} s, {r.trail_min_s:.1f} s): {r.dev_step_f1:.3f} / {r.dev_det_ratio:.2f}"
                 for r in tb.head(4).itertuples())
ITEMS["T:tuning"] = (S_E2E, T(
    "Development-Set Selection of the Head-Only Walking Thresholds (Participant-Mean Walking F1, 77 Development Participants)",
    ["Walking threshold (m/s²)", "B1 development F1", "B2 development F1"], rows, [3480, 3480, 3480],
    "The first grid (0.2–1.8 m/s²) selected its lower edge; it was extended downward (0.02–0.18 m/s²) on development data "
    "before any test evaluation of B1 or B2, giving 0.18 m/s² (B1) and 0.20 m/s² (B2). B2-t (post hoc): after the first test "
    "evaluation showed excess B2 step detections, prominence factor × confirmation delay × trailing-minimum window "
    f"({len(tb)} settings) were re-searched on development data only. Best settings (development step F1 / detections per "
    f"heel strike): {best}. Prespecified B2 setting (1.5, 0.2 s, 0.9 s): {pre.dev_step_f1:.3f} / {pre.dev_det_ratio:.2f}."))
sens = pd.read_csv(RES / "sens" / "sensitivity_summary.csv")
po = {"none": 0, "acc_noise": 1, "gyro_bias": 2, "drift": 3, "fs": 4}
sens["o1"] = sens["pert"].map(po)
sens["o2"] = np.where(sens["pert"] == "fs", -sens["level"], sens["level"])
lab = {"none": "None (100 Hz)", "acc_noise": "Accelerometer white noise (m/s² RMS)", "gyro_bias": "Gyroscope bias (°/s)",
       "drift": "Orientation drift, 0 → level (°)", "fs": "Sampling rate (Hz)"}
rows = [[lab[r.pert], "—" if r.pert == "none" else f"{r.level:g}", f"{r.A0:.2f}", f"{r.A0g:.2f}", f"{r.A1:.2f}",
         f"{r.A0_big_pct:.1f} / {r.A0g_big_pct:.1f} / {r.A1_big_pct:.1f}", f"{r.turn_tp:.3f}", f"{r.turn_fp:.2f}"]
        for r in sens.sort_values(["o1", "o2"]).itertuples()]
ITEMS["T:sens"] = (S_ROB, T(
    "Sensitivity of Cadence and Head-Only Turn Detection to Simulated Sensor Non-Idealities (Test Set, 930 Trials)",
    ["Perturbation", "Level", "A0 |*e*_{C}|", "A0g |*e*_{C}|", "A1 |*e*_{C}|", "|*e*_{C}| > 5 (%): A0 / A0g / A1",
     "B1 turns detected", "B1 extra turns per trial"], rows, [2500, 700, 1000, 1000, 1000, 1700, 1200, 1340],
    "Simulation on recorded test trials: median of participant-level median |*e*_{C}| (steps/min) with reference-assisted "
    "segmentation; turn columns from the B1 turn detector. Gyroscope biases span up to the median resting offset of the "
    "Technoconcept head recordings (7.0°/s; Signal-Level Verification table). Drift rotates the sensor frame linearly over "
    "each trial. Sampling-rate cases are decimated with anti-alias filtering and evaluated at the reduced rate. These "
    "simulations do not model strap tension, slippage, frame coupling, or sensor temperature."))
# ------------------------------------------------------------------------------------------------ V16: risk models
TS = json.loads((RES / "trust" / "trust_summary.json").read_text())
TX = json.loads((RES / "trust" / "trust_extra.json").read_text())
MOD = json.loads((RES / "trust" / "trust_models.json").read_text())
NAME = {"Q1_score": "Q1: SR rule (trial SR)", "Q2a_SR_trial": "Q2a: trial SR, logistic", "Q2b_SR_segment": "Q2b: segment SR",
        "Q2c_SR_plus_2": "Q2c: SR+2", "Q2d_full": "Q2d: full (10 features)"}
rows = []
for r in TS["discrimination"]:
    q1 = r["method"] == "Q1_score"
    au = TX["Q1_auroc"] if q1 else (r["auroc"], r["auroc_ci"])
    ap = TX["Q1_auprc"] if q1 else (r["auprc"], r["auprc_ci"])
    rows.append([NAME[r["method"]], f"{au[0]:.3f} {ci(au[1], 3)}", f"{ap[0]:.3f} {ci(ap[1], 3)}",
                 "—" if q1 else f"{r['brier']:.4f}",
                 "—" if q1 else f"{m(r['cal_intercept_slope'][0])} / {r['cal_intercept_slope'][1]:.2f}",
                 "reference" if r["method"] == "Q2a_SR_trial" else
                 ("—" if q1 else f"{m(r['delta_auroc_vs_Q2a'], 3)} {ci(r['delta_auroc_vs_Q2a_ci'], 3)}")])
FN = {"sr_seg": "SR", "stride_reg_seg": "stride regularity", "cv_iv": "interval CV", "disagree": "disagreement",
      "spec_prom": "spectral prominence", "spec_entropy": "spectral entropy", "peak_amp_cv": "peak-amplitude CV",
      "time_cover": "step-time coverage", "w_rms": "RMS", "log_dur": "log duration", "sr_trial": "trial SR"}
coef = "; ".join(f"{NAME[k].split(':')[0]}: " + ", ".join(f"{FN[c]} {m(v)}" for c, v in d_.items()
                                                         if not c.startswith("_") and c != "intercept")
                 for k, d_ in MOD.items() if k in ("Q2c_SR_plus_2", "Q2d_full"))
MC = TS["matched_coverage"]
ITEMS["T:q2"] = (S_TR, T(
    "Discrimination and Calibration of Error-Risk Criteria for Large Cadence Errors (Test Set, 1860 Segments, 183 Participants)",
    ["Criterion", "AUROC [95% CI]", "AUPRC [95% CI]", "Brier", "Calibration intercept / slope", "ΔAUROC vs. Q2a [95% CI]"],
    rows, [2140, 1900, 1900, 800, 1600, 2100],
    f"Large error: |*e*_{{C}}| > 5 steps/min with B0 segmentation (base rate: development {100 * TS['base_rate_dev']:.1f}%, test "
    f"{100 * TS['base_rate_test']:.1f}%). Brier score of the development base rate on test: "
    f"{TS['discrimination'][1]['brier_null_test']:.4f}. Q1 is a threshold rule without probabilities (AUROC from its score; "
    f"{TX['n_Q1']} segments with a defined trial SR). Standardized coefficients — {coef}. Large-error share among kept segments "
    f"at matched coverage: 95.5%, Q2a {MC['0.955']['Q2a_big_pct']:.1f}%, Q2c {MC['0.955']['Q2c_big_pct']:.1f}%, Q2d "
    f"{MC['0.955']['Q2d_big_pct']:.1f}% (Q2d − Q2a {m(MC['0.955']['diff_Q2d_minus_Q2a_pp'])} pp {ci(MC['0.955']['diff_ci'])}); "
    f"90%, {MC['0.9']['Q2a_big_pct']:.1f}%, {MC['0.9']['Q2c_big_pct']:.1f}%, {MC['0.9']['Q2d_big_pct']:.1f}% "
    f"({m(MC['0.9']['diff_Q2d_minus_Q2a_pp'])} pp {ci(MC['0.9']['diff_ci'])}). Exploratory analysis; models fitted on development "
    "segments only."))
ops = pd.read_csv(RES / "trust" / "trust_operating_points.csv", dtype={"group": str})
MM = ("Q1", "Q2c_SR_plus_2", "Q2d_full")
rows = []
grp = [("all", "all", "All")] + [("vga_lvl", g, "VGA " + l) for g, l in (("0.0", "0"), ("1.0", "1"), ("2.0", "2"), ("3.0", "≥3"))] \
    + [("cohort", c, c) for c in order]
for by, g_, lab_ in grp:
    g = ops[(ops["by"] == by) & (ops["group"] == g_)]
    if g.empty:
        continue

    def cell(col, f="{:.1f}"):
        return " / ".join(f.format(g[g["method"] == x][col].iloc[0]) for x in MM)
    rows.append([lab_, str(int(g["n"].iloc[0])), f"{g['big_pct_all'].iloc[0]:.1f}", cell("retained_pct"),
                 cell("sensitivity", "{:.2f}"), cell("false_exclusion_pct"), cell("big_pct_retained")])


def dd(k):
    v = TX[k]
    return f"{m(v[0], 1)} pp {ci(v[1], 1)}"


ITEMS["T:q2_groups"] = (S_TR, T(
    "Retention, Detection, and False Exclusion by Clinician-Rated VGA and Cohort for Q1 / Q2c / Q2d (Test Set)",
    ["Group", "Segments", "Large errors (%)", "Retained (%)", "Sensitivity", "False exclusion (%)", "Large errors kept (%)"],
    rows, [1100, 900, 1100, 1900, 1700, 1900, 1840],
    "Each cell: Q1 / Q2c / Q2d at the development-matched flag rate. Sensitivity: share of large errors flagged; false "
    "exclusion: share of segments without a large error that were flagged. Differences from Q1 with participant-bootstrap "
    f"95% CI — VGA ≥3 ({TX['vga3_n_segments_participants'][0]} segments, {TX['vga3_n_segments_participants'][1]} participants): "
    f"Q2c retained {dd('vga3_Q2c_SR_plus_2_flag_retained_diff_vs_Q1')}, false exclusion "
    f"{dd('vga3_Q2c_SR_plus_2_flag_false_excl_diff_vs_Q1')}; Q2d retained {dd('vga3_Q2d_full_flag_retained_diff_vs_Q1')}, false "
    f"exclusion {dd('vga3_Q2d_full_flag_false_excl_diff_vs_Q1')}. CVA ({TX['CVA_n_segments_participants'][0]} segments, "
    f"{TX['CVA_n_segments_participants'][1]} participants): Q2c retained {dd('CVA_Q2c_SR_plus_2_flag_retained_diff_vs_Q1')}, false "
    f"exclusion {dd('CVA_Q2c_SR_plus_2_flag_false_excl_diff_vs_Q1')}. VGA was not used to fit or select any criterion."))
# ------------------------------------------------------------------------------------------------ V16: external
EX = json.loads((RES / "ext" / "external_stats.json").read_text())
CN = {"OG_st_control": "Single task, control", "OG_dt_control": "Dual task, control", "OG_st_fatigue": "Single task, fatigue",
      "OG_dt_fatigue": "Dual task, fatigue"}
rows = []
for c in CN:
    b = EX["by_condition"][c]
    rows.append([CN[c], str(b["n_passes"])] + [f"{b[k]['mae_participant_median']:.2f} {ci(b[k]['mae_ci'])}" for k in ("B0", "B1", "B2")]
                + [f"{m(b['B1']['ba']['bias'])} ({m(b['B1']['ba']['loa_lo'], 1)}, {m(b['B1']['ba']['loa_hi'], 1)})",
                   f"{b['B1']['p90_abs']:.2f}"])
a = EX["all"]
rows.append(["All", str(EX["n_passes"])] + [f"{a[k]['mae_participant_median']:.2f} {ci(a[k]['mae_ci'])}" for k in ("B0", "B1", "B2")]
            + [f"{m(a['B1']['ba']['bias'])} ({m(a['B1']['ba']['loa_lo'], 1)}, {m(a['B1']['ba']['loa_hi'], 1)})", f"{a['B1']['p90_abs']:.2f}"])
TT = EX["trust_transfer"]
ITEMS["T:ext_cond"] = (S_EXT, T(
    "Frozen External Validation by Task Condition (DUO-GAIT, 16 Healthy Adults, 64 Walks)",
    ["Condition", "Passes", "B0 |*e*_{C}| [95% CI]", "B1 |*e*_{C}| [95% CI]", "B2 |*e*_{C}| [95% CI]", "B1 bias (95% LoA)",
     "B1 90th pct. |*e*_{C}|"], rows, [1900, 700, 1700, 1700, 1700, 1500, 1240],
    f"Steps/min; participant-level medians of pass-level |*e*_{{C}}| over reference straight passes. Friedman test of B1 participant "
    f"medians across the four conditions: p = {EX['B1_friedman_conditions']['p']:.2f}. Observed median head–initial-contact "
    f"lag {m(EX['observed_lag_median'])} s (frozen Voisard lag 0.07 s; matching tolerance 0.15 s). Large errors: B0 "
    f"{EX['n_large_errors_B0']} pass, B1 {a['B1']['big_pct']:.2f}%, B2 {a['B2']['big_pct']:.2f}%; no pass without output. "
    f"Frozen error-risk criteria flagged {TT['Q1_flag_flagged_pct']:.1f}% (Q1), {TT['Q2c_SR_plus_2_flag_flagged_pct']:.1f}% "
    f"(Q2c), and {TT['Q2d_full_flag_flagged_pct']:.1f}% (Q2d) of passes (median segment SR "
    f"{EX['sr_seg_quantiles']['0.5']:.3f}); with a single large error, transfer of discrimination could not be tested."))
# ------------------------------------------------------------------------------------------------ V16: post hoc
PS = json.loads((RES / "post" / "post_stats.json").read_text())
GR = json.loads((RES / "post" / "gyrocal_rule_ref.json").read_text())
gh, gr = PS["gyrocal_head"], PS["gyrocal_ref"]
rows = [["Calibration", "Rule chosen on development data",
         f"head-only offset estimate: never apply; known still period: apply if offset > {gr['selected_threshold_dps']:g}°/s "
         f"({gr['trials_corrected']} of 930 test trials)"]]
for k in ("B1", "B2"):
    a = gr[k]
    rows.append(["Calibration", f"{k} no output (%)",
                 f"{a['no_output_pct'][0]:.2f} → {a['no_output_pct'][1]:.2f} ({m(a['no_output_diff_pp'][0])} pp {ci(a['no_output_diff_pp'][1])})"])
    rows.append(["Calibration", f"{k} |*e*_{{C}}| > 5 or no output (%)",
                 f"{a['big_or_missing_pct'][0]:.2f} → {a['big_or_missing_pct'][1]:.2f} ({m(a['big_or_missing_diff_pp'][0])} pp {ci(a['big_or_missing_diff_pp'][1])})"])
q = GR["test"]["q_static_gt30"]
rows.append(["Calibration", "B1 / B2 no output, 17 trials with resting rate > 30°/s (%)",
             f"{q['B1_uncorrected']['no_output_pct']:.1f} → {q['B1_rule']['no_output_pct']:.1f} / "
             f"{q['B2_uncorrected']['no_output_pct']:.1f} → {q['B2_rule']['no_output_pct']:.1f}"])
rows.append(["Calibration", "B1 median |*e*_{C}| on segments with output in both runs",
             f"{gr['B1']['median_abs_err_on_common_segments'][0]:.2f} → {gr['B1']['median_abs_err_on_common_segments'][1]:.2f} steps/min"])
for e in PS["equivalence"]:
    rows.append(["Equivalence (±1.8)", e["comparison"].replace("B2-t", "B2-t"),
                 f"mean {m(e['mean_diff'])}; 90% CI {ci(e['ci90_t'])}; TOST p {'< 0.001' if e['p_tost'] < 0.001 else f'= {e['p_tost']:.2f}'}; "
                 f"{'equivalent' if e['equivalent'] else 'not equivalent'} (passes from ±{e['smallest_margin_passing']:.2f})"])
for r in PS["threshold_sensitivity"]:
    th = r["threshold"]
    rows.append(["Threshold", f"{th} steps/min: large or missing (%), B0 / B1 / B2 / B2-t",
                 f"{r['B0_big_or_missing_pct']:.1f} / {r['B1_big_or_missing_pct']:.1f} / {r['B2_big_or_missing_pct']:.1f} / "
                 f"{r['B2t_big_or_missing_pct']:.1f} (CVA {r['B0_big_pct_CVA']:.1f}, HS {r['B0_big_pct_HS']:.1f} for B0)"])
    rows.append(["Threshold", f"{th} steps/min: AUROC Q1 / SR+2 / full",
                 f"{r['AUROC_Q1']:.3f} {ci(r['AUROC_Q1_ci'], 3)} / {r['AUROC_SR+2']:.3f} / {r['AUROC_full']:.3f}; "
                 f"SR+2 − Q1 {ci(r['AUROC_SR+2_minus_Q1_ci'], 3)}"])
    rows.append(["Threshold", f"{th} steps/min: large errors kept at 95.5% / 90% coverage, Q1 / SR+2 / full (%)",
                 f"{r['kept_big_pct_Q1_cov955']:.1f} / {r['kept_big_pct_SR+2_cov955']:.1f} / {r['kept_big_pct_full_cov955']:.1f}; "
                 f"{r['kept_big_pct_Q1_cov900']:.1f} / {r['kept_big_pct_SR+2_cov900']:.1f} / {r['kept_big_pct_full_cov900']:.1f}"])
    rows.append(["Threshold", f"{th} steps/min: VGA ≥3, retained (%) / sensitivity / false exclusion (%), Q1 vs SR+2",
                 f"{r['VGA3_Q1_retained_pct']:.1f} / {r['VGA3_Q1_sensitivity']:.2f} / {r['VGA3_Q1_false_excl_pct']:.1f} vs "
                 f"{r['VGA3_SR+2_retained_pct']:.1f} / {r['VGA3_SR+2_sensitivity']:.2f} / {r['VGA3_SR+2_false_excl_pct']:.1f}"])
EG = json.loads((RES / "post" / "eargait_summary.json").read_text())
CP = json.loads((RES / "post" / "compute_summary.json").read_text())
CL = json.loads((RES / "post" / "clinical_summary.json").read_text())
rows.append(["Published detector", "EarGait (untuned) vs head A1 (B0): median |*e*_{C}| (steps/min)",
             f"{EG['median_abs_err']:.2f} {ci(EG['median_abs_err_ci'])} vs {EG['B0_median_abs_err']:.2f}; difference "
             f"{m(EG['diff_median_abs_err'])} {ci(EG['diff_median_abs_err_ci'])}"])
rows.append(["Published detector", "EarGait: bias, LoA; doubling / halving (% of segments)",
             f"{m(EG['bias'])}, {m(EG['loa'][0])} to {m(EG['loa'][1])}; {EG['doubling_pct']:.1f} / {EG['halving_pct']:.1f} "
             f"(doubling CIPN {100 * EG['doubling_by_cohort']['CIPN']:.0f}%, KOA {100 * EG['doubling_by_cohort']['KOA']:.0f}%, "
             f"CVA {100 * EG['doubling_by_cohort']['CVA']:.0f}%)"])
rows.append(["Published detector", "EarGait vs B0: |*e*_{C}| > 5 or no output (%); event F1 (timing error)",
             f"{EG['large_or_missing_pct']:.1f} vs {EG['B0_large_or_missing_pct']:.1f} (difference {ci(EG['diff_large_or_missing_ci'])} pp); "
             f"F1 {EG['event_f1']:.3f} ({EG['event_timing_mae_ms']:.0f} ms)"])
rows.append(["Computation", "Streaming B2 vs batch B2 (outputs reproduced)",
             f"{CP['outputs_identical_timing']} of {CP['outputs_batch']} outputs identical ({CP['n_trials_streaming']} test trials, "
             f"{CP['data_seconds'] / 3600:.2f} h)"])
rows.append(["Computation", "Streaming B2: operations per second of data; state memory",
             f"{CP['ops_per_second_total']:,} (filters {CP['ops_per_second_by_stage']['filters']:,}, turn gate "
             f"{CP['ops_per_second_by_stage']['gate']:,}, peak search {CP['ops_per_second_by_stage']['peak_scan']:,}, "
             f"robust σ {CP['ops_per_second_by_stage']['sigma']:,}); {CP['state_bytes_float32'] / 1024:.1f} kB (32-bit values)"])
rows.append(["Computation", "Batch run time per hour of data (Python, one core)",
             f"B1 {CP['B1_batch_seconds_per_hour']:.1f} s, B2 {CP['B2_batch_seconds_per_hour']:.1f} s"])
b0, b1 = CL["pipelines"]["B0"], CL["pipelines"]["B1"]
rows.append(["Clinical scale", "Median |*e*_{C}| / MDC; segments with |*e*_{C}| > MDC (%), all / CVA",
             f"MDC 15.1 (Parkinson's disease; main-text ref.): B0 {b0['median_over_lang2016_PD']:.2f}, {b0['pct_exceeding_lang2016_PD']:.1f} / "
             f"{b0['pct_exceeding_lang2016_PD_CVA']:.0f}; B1 {b1['median_over_lang2016_PD']:.2f}, {b1['pct_exceeding_lang2016_PD']:.1f} / "
             f"{b1['pct_exceeding_lang2016_PD_CVA']:.0f}. Cross-visit MDC95 {CL['anchors_spm']['crossvisit_head_A1']:.1f} (head) and "
             f"{CL['anchors_spm']['crossvisit_reference']:.1f} (reference)"])
ITEMS["T:post"] = ("Post Hoc Analyses", T(
    "Post Hoc Analyses: Gyroscope Offset Calibration, Equivalence, Large-Error Threshold, a Published Detector, Computation, and Clinical Scale (Test Set)",
    ["Analysis", "Quantity", "Result"], rows, [1500, 3600, 5340],
    "Calibration: the per-axis median angular rate over a still period was subtracted before re-running B1/B2 with frozen "
    "parameters; the still period was either estimated from the head signal (start of recording to 0.5 s before the first "
    "B1 walking bout) or known (to 0.5 s before the first reference heel strike, standing in for a device-initiated still "
    "phase). Whether to apply it was chosen on development data. Equivalence: two one-sided tests on paired "
    "participant-level median |e_C| (mean difference with 90% CI); margin ±1.8 steps/min, the one-sample cadence resolution "
    "at the median step time. Threshold: models and flags frozen as fitted at 5 steps/min; participant-bootstrap 95% CIs. "
    "Published detector: initial-contact detector of the open-source EarGait package (DiaoAdaptedEventDetection, v3.4.0; "
    "Kaiser FIR low-pass 5 Hz, singular spectrum analysis with a 1-s window, minima of the dominant component) re-implemented "
    "with its published defaults (code checked against the pyts SSA algorithm) and applied, untuned, to the superior–inferior "
    "acceleration within the same reference-assisted segments as B0; only the event-time offset for matching was set on "
    "development data. Computation: sample-by-sample implementation of B2; one operation = one add, multiply, compare, "
    "divide or square root, sorting counted as n·log2(n) comparisons (naive implementation, i.e. an upper bound). "
    "All analyses were added after the V16 draft and are post hoc."))
ITEMS["T:ext_audit"] = (S_PIPE, T(
    "Suitability Audit of the DUO-GAIT Files Used for External Validation",
    ["Requirement", "Finding on the files", "Verdict"],
    [["Head 6-axis signals", "interim/<condition>/<subject>/HE.csv (GyrX–Z, AccX–Z) for 64 walks (16 participants × 4 conditions)", "Met"],
     ["Independent reference", "Per-stride initial contacts from the two foot IMUs with turning, interrupted, and outlier flags "
      "(processed/<condition>/<subject>/{left,right}_foot_core_params.csv); a foot-IMU algorithm, not motion capture", "Met"],
     ["Common time base", "ic_samples / 128 = ic_times, counted from the first row of the segmented files; head time stamps "
      "regular (Δt = 1/128 s); sensors started simultaneously per the data descriptor", "Met"],
     ["Condition labels", "OG_st_control, OG_dt_control, OG_st_fatigue, OG_dt_fatigue", "Met"],
     ["Sampling rate, placement", "128 Hz Physilog 5; head sensor location not specified in text", "Met; placement unverified"],
     ["Units", "Acceleration in g (median norm 0.98 g), angular rate in °/s; converted", "Met"],
     ["Data levels", "raw (continuous), interim (segmented walks per sensor), processed (stride parameters)", "Documented"],
     ["Missing data, saturation", "No gaps or missing values; maxima 2.7 g of ±16 g and 537°/s of ±1000°/s; 8 provider-flagged "
      "interruptions excluded", "No blocking issue"],
     ["Reference sufficiency", f"{EX['n_passes']} straight passes in which both feet had valid, non-turning strides (median "
      f"{EX['pass_duration_median']:.0f} s; reference cadence {EX['cadence_ref_median']:.0f} steps/min)", "Met"],
     ["Licence, citation", "Licence terms not displayed on the retrieved record; cite data descriptor and Zenodo DOI", "To verify"]],
    [2300, 6200, 1940],
    "Source: Zenodo record 10.5281/zenodo.8244887 (processed.zip, interim.zip) and the data descriptor. The cohort is healthy "
    "and young (21–35 years); results do not constitute clinical validation."))
ITEMS["F:ext_ba"] = (S_EXT, ("fig", ("fig_v16/figS_external_ba.png",
    "Bland–Altman plots of frozen head-only cadence on DUO-GAIT, colored by task condition: (a) B1 offline and (b) B2 causal. "
    "Solid line: bias; dashed lines: 95% LoA for repeated measurements (797 passes, 16 participants).", 6.0)))

# ------------------------------------------------------------------------------------------------ order by first mention
BODY = (HERE / "body_v16.py").read_text(encoding="utf-8")
RANGES = {("T:feat_valid", "T:feat_model"): ["T:feat_mount", "T:feat_vga"]}
seen = []
for k in re.findall(r"⟪([TF]:[a-z0-9_]+)⟫", BODY):
    if k in ITEMS and k not in seen:
        seen.append(k)
        for (a_, b_), mids in RANGES.items():
            if k == a_:
                seen.extend(x for x in mids if x not in seen)
missing = [k for k in ITEMS if k not in seen]
if missing:
    print("supplement items not cited in the main text:", missing)
ORDER_KEYS = seen + missing
NUM, nt, nf = {}, 0, 0
for k in ORDER_KEYS:
    if k.startswith("T:"):
        nt += 1
        NUM[k] = ("Table", nt)
    else:
        nf += 1
        NUM[k] = ("Fig.", nf)
COUNTS = {"T:count": str(nt), "F:count": str(nf)}
# Cross-references inside supplement notes (by caption name) -> S-numbers
B = [("p", "All Voisard values refer to the participant-wise test set (183 participants, 930 trials) unless stated otherwise; "
           "medians are participant-level medians and brackets give participant-bootstrap 95% CIs. Analysis status: "
           "the reference-assisted analysis (B0) and the mounting simulations are prespecified; head features beyond cadence "
           "are secondary; the step-regularity screen is post hoc; the head-only pipelines (B1, B2), the sensor-sensitivity "
           "simulations, and the error-risk models (Q2) are exploratory, B2-t is post hoc; DUO-GAIT results are a frozen external "
           "validation. Simulation results describe recorded signals with synthetic perturbations, not real re-wearing.")]
last = None
for k in ORDER_KEYS:
    sec, blk = ITEMS[k]
    if sec != last:
        B.append(("h1", sec))
        last = sec
    B.append(blk)
qc_ref = f"Table S{NUM['T:qc'][1]}"
B = [(kind, (pl[0], pl[1], pl[2], pl[3], pl[4].replace("Signal-Level Verification table", qc_ref)) if kind == "table" and pl[4] else pl)
     for kind, pl in B]


def resolve(text):
    """⟪T:a⟫, ⟪F:b⟫ -> 'Supplementary Table S3', 'Supplementary Fig. S2'; adjacent '⟪F:x⟫, ⟪T:y⟫' -> 'Supplementary Fig. S4,
    Table S5'; '⟪T:a⟫–⟪T:b⟫' -> 'Supplementary Tables S8–S11'; counts."""
    for k, v in COUNTS.items():
        text = text.replace(f"⟪{k}⟫", v)

    def rng(mo):
        a_, b_ = NUM[mo.group(1)], NUM[mo.group(2)]
        return f"Supplementary {a_[0].replace('Table', 'Tables').replace('Fig.', 'Figs.')} S{a_[1]}–S{b_[1]}"
    text = re.sub(r"⟪([TF]:[a-z0-9_]+)⟫–⟪([TF]:[a-z0-9_]+)⟫", rng, text)

    def seq(mo):
        keys = re.findall(r"⟪([TF]:[a-z0-9_]+)⟫", mo.group(0))
        kinds = {NUM[k][0] for k in keys}
        if len(keys) > 1 and len(kinds) == 1:
            kind = kinds.pop()
            return f"Supplementary {'Tables' if kind == 'Table' else 'Figs.'} " + ", ".join(f"S{NUM[k][1]}" for k in keys)
        parts = [f"{NUM[k][0]} S{NUM[k][1]}" for k in keys]
        return "Supplementary " + ", ".join(parts)
    text = re.sub(r"⟪[TF]:[a-z0-9_]+⟫(?:, ⟪[TF]:[a-z0-9_]+⟫)*", seq, text)
    assert "⟪" not in text, text[:200]
    return text
