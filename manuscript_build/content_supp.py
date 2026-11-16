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
TITLE = ("Cadence Estimation From a Single Forehead IMU in Clinical Gait: Site Comparison, Failure Analysis, and "
         "Stride-Based Statistics")
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
S_E2E, S_ROB, S_TR, S_EXT = ("Head-Only End-to-End Estimation", "Mounting and Sensor Robustness", "Early Screening Rules (Superseded by the Segment-Level Rule)",
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
    ["B1/B2 turns", "gate runs merged within 0.5 s; integrated rotation ≥ 90°; segments ≥ 2 s", "Prespecified"],
    ["B2 peak confirmation; trailing-minimum window", "0.20 s; 0.9 s (B2-t: 0.30 s; 0.9 s)",
     "Prespecified; B2-t re-selected on development data"],
    ["B2 running cadence", "median of the last 6 step intervals within a straight bout", "Prespecified"],
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
ITEMS["T:sims"] = (S_ROB, _old("table", "Simulated Mounting Errors"))
ITEMS["F:rewear"] = (S_ROB, _old("fig", "fig8_rewear"))
ITEMS["T:rewear"] = (S_ROB, _old("table", "Cross-Visit Agreement"))
ITEMS["T:gating"] = (S_E2E, _old("table", "Turn Detection and Gate"))
ITEMS["F:gating"] = (S_E2E, ("fig", ("fig_results/fig9_gating.png",
    "Turn gate versus coverage-matched random removal and the step-regularity screen (reference-assisted segmentation, test "
    "set): gate-minus-random differences in retained-step precision and recall, turn sensitivity and false marks versus "
    "threshold, and large-error share versus the fraction of segments kept.", 4.2)))

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
    "each trial (acc and gyro rotated; the drift angular rate itself was not added here, see Post Hoc Analyses table). Sampling-rate cases are decimated with anti-alias filtering and evaluated at the reduced rate. These "
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
DR = json.loads((RES / "post" / "drift_rate" / "drift_rate_summary.json").read_text())
import pandas as _pd
_ds = _pd.read_csv(RES / "post" / "drift_rate" / "drift_rate_summary.csv").set_index("pert")
_ag = DR["agreement_vs_none"]
rows.append(["Mounting drift", "0°–20° linear drift: segments changed vs. no drift (> 0.5 steps/min; max), A0 / A0g / A1",
             f"{_ag['A0|drift']['gt0.5']} ({_ag['A0|drift']['max_abs_diff']:.1f}) / {_ag['A0g|drift']['gt0.5']} "
             f"({_ag['A0g|drift']['max_abs_diff']:.2f}) / {_ag['A1|drift']['gt0.5']} of {_ag['A1|drift']['n']} segments"])
rows.append(["Mounting drift", "Drift angular rate added to the gyroscope (median, range °/s): A0 / A0g / A1 median |*e*_{C}|; B1 turn FP per trial",
             f"{DR['drift_rate_dps_median']:.2f} ({DR['drift_rate_dps_range'][0]:.2f}–{DR['drift_rate_dps_range'][1]:.2f}): "
             f"{_ds.loc['drift_w','A0']:.2f} / {_ds.loc['drift_w','A0g']:.2f} / {_ds.loc['drift_w','A1']:.2f}, unchanged vs. rotation only; "
             f"turn FP {_ds.loc['drift','turn_fp']:.3f} → {_ds.loc['drift_w','turn_fp']:.3f}"])
BC = json.loads((RES / "post" / "b_checks" / "b_checks_summary.json").read_text())
_d, _t, _n = BC["duogait"], BC["voisard_b2_turns"], BC["acc_noise_A1"]
rows.append(["Error sources", "DUO-GAIT median |*e*_{C}|: B0 / B1 / B1 peaks within reference passes / B2; mean bias",
             f"{_d['median_abs_err_participant']['B0']:.2f} / {_d['median_abs_err_participant']['B1']:.2f} / "
             f"{_d['median_abs_err_participant']['B1peaks_in_pass']:.2f} / {_d['median_abs_err_participant']['B2']:.2f}; "
             f"{m(_d['bias_mean']['B0'])} / {m(_d['bias_mean']['B1'])} / {m(_d['bias_mean']['B1peaks_in_pass'])} / {m(_d['bias_mean']['B2'])}"])
rows.append(["Error sources", "DUO-GAIT: B1 segment beyond the pass, start / end (median s); B2 outputs per pass",
             f"{_d['B1_segment_extension_s_median']['before']:.1f} / {_d['B1_segment_extension_s_median']['after']:.1f} "
             f"({_d['pct_passes_B1_ext_gt_1s']:.0f}% of passes > 1 s); {_d['B2_outputs_per_pass_median']:.0f}"])
rows.append(["Error sources", "Steps detected per reference step (precision / recall): B1, B2; DUO-GAIT vs Voisard",
             f"B1 {_d['steps_B1']['detected_per_reference']:.2f} ({_d['steps_B1']['precision']:.2f}/{_d['steps_B1']['recall']:.2f}) vs "
             f"{_d['voisard_steps_B1']['detected_per_reference']:.2f} ({_d['voisard_steps_B1']['precision']:.2f}/{_d['voisard_steps_B1']['recall']:.2f}); "
             f"B2 {_d['steps_B2']['detected_per_reference']:.2f} ({_d['steps_B2']['precision']:.2f}/{_d['steps_B2']['recall']:.2f}) vs "
             f"{_d['voisard_steps_B2']['detected_per_reference']:.2f} ({_d['voisard_steps_B2']['precision']:.2f}/{_d['voisard_steps_B2']['recall']:.2f})"])
_loc = _t["false_by_location_pct"]
rows.append(["B2 turn onsets", "False onsets (per trial); location: straight walking / within 3 s of the turn / before first / after last heel strike (%)",
             f"{_t['n_false_onsets']} of {_t['n_onsets']} ({_t['n_false_onsets'] / _t['n_trials']:.2f}); "
             f"{_loc.get('straight_walking', 0):.1f} / {_loc.get('straight_within_3s_of_turn', 0):.1f} / "
             f"{_loc.get('before_first_hs', 0):.1f} / {_loc.get('after_last_hs', 0):.1f}"])
rows.append(["B2 turn onsets", "Integrated rotation, false (median [IQR]) vs true onsets; false < 90° (%); onset precision with a 90° rule (diagnostic)",
             f"{_t['false_angle_deg_median_iqr'][1]:.0f}° [{_t['false_angle_deg_median_iqr'][0]:.0f}, {_t['false_angle_deg_median_iqr'][2]:.0f}] vs "
             f"{_t['true_angle_deg_median']:.0f}°; {_t['false_pct_below_90deg']:.0f}%; {_t['precision_onsets']:.2f} → {_t['precision_if_90deg_rule']:.2f} "
             f"(trials with a true onset {100 * _t['recall_if_90deg_rule_trials']:.0f}%)"])
for lev in ("0.05", "0.1", "0.2"):
    q = _n[lev]
    rows.append(["Accelerometer noise", f"{lev} m/s²: change in median |*e*_{{C}}| [95% CI]; mean |*e*_{{C}}|; unchanged / better / worse segments (%)",
                 f"{m(q['median_participant_abs_change'])} {ci(q['ci95'])}; {q['mean_abs_err'][0]:.2f} → {q['mean_abs_err'][1]:.2f}; "
                 f"{q['pct_segments_unchanged']:.0f} / {q['pct_better_worse'][0]:.0f} / {q['pct_better_worse'][1]:.0f}"])
ITEMS["T:post"] = ("Post Hoc Analyses", T(
    "Post Hoc Analyses: Gyroscope Offset Calibration, Equivalence, Large-Error Threshold, a Published Detector, Computation, Clinical Scale, Mounting Drift, and Error Sources (Test Set)",
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
    "Mounting drift: the prespecified drift simulation rotated acc and gyro by R(t) only; the post hoc rerun replays the same axes and "
    "adds the drift angular rate (20° over the trial, about a fixed axis) to the gyroscope. "
    "Error sources: B1 peaks within reference passes use the B1 detector with the reference segmentation; the 90° rule "
    "is a diagnostic applied after the fact, not a causal pipeline. Noise: paired per-segment comparison; CI from 2000 "
    "participant bootstrap resamples. "
    "All analyses were added after the primary results were known and are post hoc."))
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


# ------------------------------------------------------------------------------------------------ V17: moved from the main text
V17 = json.loads((RES / "v17" / "cohort_head_vs_lb.json").read_text())
_COH0 = V17[0]
def _cl(r, k):
    return f"{m(r[k + '_median'])} [{m(r[k + '_lo'])}, {m(r[k + '_hi'])}]"
ITEMS["T:cohort_lb"] = (S_B0, T(
    "Head Versus Lower-Back A1 Cadence Error by Cohort (B0, Test Set)",
    ["Cohort", "Participants / segments", "Reference cadence", "Head |*e*_{C}|", "Lower back |*e*_{C}|",
     "Head − lower back", "Largest difference not excluded", "|*e*_{C}| > 5: head / LB / both (%)"],
    [[("All" if r["cohort"] == "All" else r["cohort"]), f"{r['n_participants']} / {r['n_segments']}", f"{r['cadence_ref_median']:.0f}",
      _cl(r, "head"), _cl(r, "lb"), _cl(r, "diff"), f"{max(abs(r['diff_lo']), abs(r['diff_hi'])):.2f}",
      f"{r['big_head_pct']:.1f} / {r['big_lb_pct']:.1f} / {r['big_both_pct']:.1f}"] for r in V17[1:] + V17[:1]],
    [800, 1150, 850, 1450, 1450, 1450, 1150, 1450],
    "Steps/min. |*e*_{C}|: median of participant medians [participant-bootstrap 95% CI, 2000 resamples]; head − lower back: "
    "median of participant paired differences [95% CI]; largest difference not excluded: the larger absolute CI bound, "
    "i.e., differences beyond it are incompatible with the data at the 95% level. A CI that includes 0 means no difference "
    "was detected, not equivalence. Large errors: share of segments; both: large error at both sites in the same segment."))
CV = json.loads((RES / "v17" / "cv" / "cv_by_cohort.json").read_text())
CVF = json.loads((RES / "v17" / "cv" / "cv_folds.json").read_text())
import pandas as _pd2
BAND = _pd2.read_csv(RES / "v17" / "cv" / "band_sensitivity.csv")
ITEMS["T:cv"] = (S_B0, T(
    "Head A1 Cadence Error With All 260 Participants Tested Once (Post Hoc 5-Fold Cross-Validation) Versus the Fixed Split",
    ["Cohort", "CV: participants / segments", "CV: |*e*_{C}| [95% CI]", "CV: |*e*_{C}| > 5 (%)",
     "Fixed split: participants", "Fixed split: |*e*_{C}| [95% CI]", "Fixed split: |*e*_{C}| > 5 (%)"],
    [[r["cohort"], f"{r['cv_n_participants']} / {r['cv_n_segments']}", f"{m(r['cv_median'])} [{m(r['cv_lo'])}, {m(r['cv_hi'])}]",
      f"{r['cv_big_pct']:.1f}", f"{r['fixed_n_participants']}", f"{m(r['fixed_median'])} [{m(r['fixed_lo'])}, {m(r['fixed_hi'])}]",
      f"{r['fixed_big_pct']:.1f}"] for r in CV[1:] + CV[:1]],
    [900, 1400, 1650, 1250, 1250, 1650, 1250],
    f"Steps/min. Folds stratified by cohort (seed {CVF['seed']}); in each fold the development procedure (band low cut-off "
    "from the configured candidates by training-fold median |*e*_{C}|, then halving rate; lags from training trials) was "
    "repeated on the other folds only. Selected band low cut-off: "
    + ", ".join(f"{f['band_lo_hz']:.1f}" for f in CVF["folds"]) + " Hz (fixed split: 0.6 Hz). Evaluation code check: "
    f"the fixed-split test segments were reproduced exactly ({CVF['reproduction_fixed_split']['n']} segments). The public "
    "data pack used here holds the head IMU only, so the lower-back comparison stays on the fixed split."))
_b = BAND[BAND["cohort"] == "All"]
ITEMS["T:band"] = (S_B0, T(
    "Sensitivity of Head A1 to the Band Low Cut-Off, All 260 Participants (Post Hoc)",
    ["Band low cut-off (Hz)", "|*e*_{C}|, median [95% CI]", "|*e*_{C}| > 5 (%)", "|*e*_{C}| > 5 when reference cadence < 90 (%)"],
    [[f"{r.band_lo:.1f}", f"{m(r.median)} [{m(r.lo)}, {m(r.hi)}]", f"{r.big_pct:.1f}",
      f"{r.big_pct_slow:.1f} (*n* = {int(r.slow_n)})"] for r in _b.itertuples()],
    [1700, 2300, 1600, 2700],
    "All 2702 segments of the 260 participants (development and test), each evaluated with the lags that the published "
    "development calibration stored for that cut-off. Per-cohort values are in band_sensitivity.csv."))
REV = json.loads((RES / "v17" / "rev" / "reviewer_checks.json").read_text())
_r2 = REV["R2"]
ITEMS["T:baseline"] = (S_B0, T(
    "Head A1 Versus a Trivial Baseline That Ignores the IMU (B0, Test Set, Post Hoc)",
    ["Cohort", "Head A1 |*e*_{C}| [95% CI]", "Baseline |*e*_{C}| [95% CI]", "|*e*_{C}| > 5: head / baseline (%)",
     "*r* (head vs. reference)", "SD of reference cadence"],
    [[c, f"{m(v['head_A1']['median'])} [{m(v['head_A1']['lo'])}, {m(v['head_A1']['hi'])}]",
      f"{m(v['baseline_cohort_median']['median'])} [{m(v['baseline_cohort_median']['lo'])}, {m(v['baseline_cohort_median']['hi'])}]",
      f"{v['head_A1']['big_pct']:.1f} / {v['baseline_cohort_median']['big_pct']:.1f}", f"{v['pearson_r_head_vs_ref']:.2f}",
      f"{v['ref_cadence_sd']:.1f}"] for c, v in list(_r2.items())[1:] + list(_r2.items())[:1]],
    [900, 2000, 2000, 1900, 1500, 1500],
    "Steps/min. Baseline: every test segment is assigned the development-set median reference cadence of its cohort "
    f"({', '.join(f'{k} {v:.0f}' for k, v in sorted(REV['baseline_dev_cohort_median_cadence'].items()))}); using the median "
    f"of all development segments ({REV['baseline_dev_all_median_cadence']:.0f}) gives "
    f"{m(_r2['All']['baseline_all_median']['median'])} steps/min overall. *r*: Pearson correlation of segment cadences. "
    "CIs: 2000 participant-level bootstrap resamples."))
PEAK = _pd2.read_csv(RES / "v17" / "peak" / "peak_sensitivity.csv")
_pn = {"prominence_floor_mps2": "Prominence floor (m/s²)", "prominence_k_sigma": "Prominence factor (× σ̂)",
       "min_peak_distance_s": "Minimum peak distance (s)"}
ITEMS["T:peak"] = (S_B0, T(
    "Sensitivity of Head A1 to the Fixed Peak-Detection Parameters (B0, Test Set, Post Hoc)",
    ["Parameter", "Value", "|*e*_{C}| [95% CI]", "|*e*_{C}| > 5 (%)", "Halving / doubling (%)", "No output (segments)"],
    [[_pn[r.parameter], f"{r.value:g}" + (" (prespecified)" if r.prespecified else ""), f"{m(r.median)} [{m(r.lo)}, {m(r.hi)}]",
      f"{r.big_pct:.1f}", f"{r.halving_pct:.2f} / {r.doubling_pct:.2f}", f"{int(r.no_output)}"] for r in PEAK.itertuples()],
    [2400, 1700, 2000, 1300, 1700, 1300],
    "One parameter changed at a time; band low cut-off and lags as calibrated on the development set. Changing the "
    "prominence floor between 0.08 and 0.20 m/s² left the summary results unchanged, because the noise-scaled threshold "
    "was the larger term."))
RR = json.loads((RES / "v17" / "rev_root" / "reviewer_checks.json").read_text())
_mn = {"median": "60 / median interval (primary)", "mean": "60 / trimmed mean interval", "count": "Steps / duration"}
ITEMS["T:altmetric"] = (S_B0, T(
    "Head and Lower-Back A1 Error Under Three Cadence Definitions (B0, Test Set, Post Hoc)",
    ["Cadence definition", "Head |*e*_{C}| [95% CI]", "Lower back |*e*_{C}| [95% CI]", "|*e*_{C}| > 5: head / LB (%)",
     "Zero error: head / LB (%)", "Head − lower back [95% CI]"],
    [[_mn[h], f"{m(RR['R3']['HE'][h]['median'])} [{m(RR['R3']['HE'][h]['lo'])}, {m(RR['R3']['HE'][h]['hi'])}]",
      f"{m(RR['R3']['LB'][h]['median'])} [{m(RR['R3']['LB'][h]['lo'])}, {m(RR['R3']['LB'][h]['hi'])}]",
      f"{RR['R3']['HE'][h]['big_pct']:.1f} / {RR['R3']['LB'][h]['big_pct']:.1f}",
      f"{RR['R3']['HE'][h]['zero_pct']:.1f} / {RR['R3']['LB'][h]['zero_pct']:.1f}",
      (f"{m(_COH0['diff_median'])} [{m(_COH0['diff_lo'])}, {m(_COH0['diff_hi'])}]" if h == "median" else
       f"{m(RR['R3']['head_minus_lb'][h]['median_diff'])} [{m(RR['R3']['head_minus_lb'][h]['lo'])}, {m(RR['R3']['head_minus_lb'][h]['hi'])}]")]
     for h in ("median", "mean", "count")],
    [2300, 1700, 1700, 1500, 1500, 1700],
    "Steps/min; 183 participants, 1860 segments per site; the same detected events and reference heel strikes, cadence "
    "computed three ways for IMU and reference alike. Trimmed mean: intervals within 0.67–1.5 × the segment median interval "
    "(drops intervals from a missed or extra step). Steps / duration: (events − 1) / time from first to last event, no "
    "trimming. With 100-Hz events the median-interval cadence moves in steps of about 1.8 steps/min. Head − lower back: "
    "median of participant paired differences of participant-median |*e*_{C}|. Run on the full Voisard data; the primary "
    f"metric reproduced all {RR['reproduction']['n']} published head and lower-back segments."))
RV2 = json.loads((RES / "v17" / "review2" / "review2.json").read_text())
_c2 = RV2["C2"]
_ord2 = ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]
_f1 = lambda v: f"{v[0]:.1f} [{v[1]:.1f}, {v[2]:.1f}]"
ITEMS["T:tail"] = (S_B0, T(
    "Share of Segments With |*e*_{C}| > 5 Steps/Min, Head Versus Lower Back by Cohort (B0, A1, Test Set, Post Hoc)",
    ["Cohort", "Participants / segments", "Head (%) [95% CI]", "Lower back (%) [95% CI]", "Head − lower back (pp) [95% CI]"],
    [[c, f"{RV2['C2_n'][c][1]} / {RV2['C2_n'][c][0]}", _f1(_c2[f"{c}|head"]), _f1(_c2[f"{c}|lb"]), _f1(_c2[f"{c}|diff"])]
     for c in _ord2] + [["All", f"{RV2['n_participants']} / {RV2['n_segments']}", _f1(_c2["All|head"]), _f1(_c2["All|lb"]),
                        _f1(_c2["All|diff"])]],
    [1500, 2000, 2200, 2200, 2400],
    "Segments with an estimate at both locations. pp: percentage points. 95% CIs from 2000 participant bootstrap resamples; the "
    "difference is computed within each resample, so it is paired. The median error does not reflect occasional large errors; "
    "this table compares the tail directly."))
_or = RV2["C1_OR_per_SD"]
_fo = lambda k: f"{_or[k][0]:.2f} [{_or[k][1]:.2f}, {_or[k][2]:.2f}]"
_vn = {"sr_seg": "Head segment SR", "C_ref": "Reference cadence", "log_amp": "log head A1 amplitude"}
_rows = []
for y, yn in (("bh", "Head large error"), ("bl", "Lower-back large error")):
    for v in ("sr_seg", "C_ref", "log_amp"):
        alone = f"{y}|sr_only|sr_seg" if v == "sr_seg" else f"{y}|cad_amp|{v}"
        _rows.append([yn if v == "sr_seg" else "", _vn[v], f"{RV2['C1_SD'][v]:.2f}", _fo(alone), _fo(f"{y}|full|{v}")])
ITEMS["T:confound"] = (S_B0, T(
    "Is the Link Between Low Step Regularity and Large Errors Explained by Slow Walking or a Weak Head Signal? "
    "(Logistic Regression, B0, A1, Test Set, Post Hoc)",
    ["Outcome", "Predictor", "1 SD", "OR per SD, partial model [95% CI]", "OR per SD, full model [95% CI]"],
    _rows, [2000, 2300, 900, 2700, 2400],
    f"{RV2['C1_n_model']} segments with all predictors (of {RV2['n_segments']}). All models include cohort indicators. "
    "Partial model: SR alone, or cadence and amplitude together without SR. Full model: SR, cadence and amplitude. "
    "Gait speed is not available; reference cadence is used as a proxy for walking slowly. Amplitude: RMS of the "
    "band-passed head A1 signal within the segment. 95% CIs from 1000 participant bootstrap resamples. Within reference-"
    "cadence tertiles (cut points {:.0f} and {:.0f} steps/min) the head large-error share was ".format(*RV2["C1_cad_tertile_edges"])
    + ", ".join(f"{RV2['C1_strata'][f'{t}|SR<0.6']['head_pct']:.0f}% vs {RV2['C1_strata'][f'{t}|SR>=0.6']['head_pct']:.0f}%"
                for t in ("slow", "mid", "fast"))
    + " for SR < 0.6 vs SR ≥ 0.6 (slow, middle, fast tertile)."))
_k3 = [("neither", "Neither"), ("head_only", "Head only"), ("both", "Both"), ("lb_only", "Lower back only")]
ITEMS["T:headonly"] = (S_B0, T(
    "Segments by Location of the Large Error: Step Regularity, Cadence, Head Signal Amplitude and Head Rotation "
    "(B0, A1, Test Set, Post Hoc)",
    ["Large error at", "Group", "Segments", "Head SR", "Ref. cadence (steps/min)", "Head A1 amplitude (m/s²)",
     "Head angular rate RMS (°/s)"],
    [[lab, grp, f"{int(R['n'])}", f"{R['sr']:.2f}", f"{R['cad']:.0f}", f"{R['amp']:.2f}", f"{R['w_rms']:.1f}"]
     for grp, src in (("All", "C3_all"), ("PD", "C3_PD")) for k, lab in _k3 for R in [RV2[src][k]]],
    [1600, 800, 1100, 1000, 1900, 1900, 1900],
    "Medians. Head angular rate RMS: norm of the head gyroscope signal over the segment, a proxy for head rotation. Head-only "
    "large errors did not occur with larger head rotation; motion of the head relative to the trunk would need synchronized "
    "head and trunk analysis, which was not done."))
HT = json.loads((RES / "v17" / "head_trunk" / "head_trunk.json").read_text())
_HTD = pd.read_csv(RES / "v17" / "head_trunk" / "head_trunk_segments.csv")
_htm = [("sr_lb", "Trunk (LB) step regularity", 2), ("sr_he", "Head step regularity", 2),
        ("xc_a1", "Head–trunk |a| cross-correlation", 2), ("coh_v", "Head–trunk vertical coherence at step frequency", 2),
        ("tr_v", "Vertical transmission, head / trunk", 2), ("yaw_rel_bp", "Head-on-trunk yaw rate, step band (°/s)", 1),
        ("yaw_rel_lf", "Head-on-trunk yaw rate, < 1 Hz (°/s)", 1), ("tilt_ratio", "Horizontal angular rate, head / trunk", 2)]
_kmed = _HTD.groupby("kind")[[k for k, _, _ in _htm]].median()
_pd = _HTD[_HTD["cohort"] == "PD"].groupby("kind")[[k for k, _, _ in _htm]].median()
def _dci(tag, k, nd):
    v = HT[f"diff_{tag}"].get(f"{k}|head_only-neither")
    return f"{v[0]:+.{nd}f} [{v[1]:+.{nd}f}, {v[2]:+.{nd}f}]" if v else "—"
ITEMS["T:headtrunk"] = (S_B0, T(
    "Head Versus Trunk in Segments by Location of the Large Error (B0, A1, Test Set, Post Hoc, Full Voisard Data)",
    ["Measure", "Neither", "Head only", "Both", "LB only", "Head only − neither [95% CI]", "PD: head only / neither",
     "PD: difference [95% CI]"],
    [[lab, *[f"{_kmed.loc[g, k]:.{nd}f}" for g in ("neither", "head_only", "both", "lb_only")], _dci("All", k, nd),
      f"{_pd.loc['head_only', k]:.{nd}f} / {_pd.loc['neither', k]:.{nd}f}", _dci("PD", k, nd)] for k, lab, nd in _htm],
    [2300, 850, 850, 850, 850, 1750, 1300, 1490],
    "Medians per segment group; segments: neither {n0}, head only {n1} ({p1} participants), both {n2}, LB only {n3}; PD head "
    "only 19 segments from 5 participants (two of them 12 segments). Each site's vertical is its own gravity direction, so "
    "yaw rates about vertical are comparable. Cross-correlation: maximum within ±0.15 s of band-passed |a| (head lag "
    "median {lag:.2f} s, a synchronisation check). Differences: medians, participant bootstrap (2000). Logistic regression "
    "for a head large error among {nl} segments without a lower-back large error ({ev} events), cohort-adjusted, OR per SD: "
    "{ors}. Among segments without any large error, PD did not differ from the other cohorts in vertical transmission "
    "({pdtr}).".format(
        n0=int((_HTD.kind == "neither").sum()), n1=int((_HTD.kind == "head_only").sum()),
        p1=int(_HTD[_HTD.kind == "head_only"].participant.nunique()), n2=int((_HTD.kind == "both").sum()),
        n3=int((_HTD.kind == "lb_only").sum()), lag=HT["lag_a1_s_quantiles"][1],
        nl=HT["logit_head_big_given_lb_ok"]["n"], ev=HT["logit_head_big_given_lb_ok"]["events"],
        ors="; ".join(f"{dict((k, l) for k, l, _ in _htm)[k].split(' (')[0]} {v[0]:.2f} [{v[1]:.2f}, {v[2]:.2f}]"
                      for k, v in HT["logit_head_big_given_lb_ok"]["OR_per_SD"].items()),
        pdtr="difference {:+.2f} [{:+.2f}, {:+.2f}]".format(*HT["neither_PD_vs_other"]["tr_v|PD-other"]))))
RCK = json.loads((RES / "v17" / "ref_check" / "ref_check.json").read_text())
_kn = {"neither": "Neither", "head_only": "Head only", "both": "Both", "lb_only": "Lower back only"}
_rk = [[_kn[k], f"{int(v['n'])}", f"{100 * v['alt_viol_any']:.1f}", f"{100 * v['gap_ge_16']:.1f}", f"{100 * v['ref_suspect']:.1f}",
        f"{100 * v['consensus_off']:.1f}", f"{100 * v['either']:.1f}"] for k, v in
       sorted(RCK["by_kind"].items(), key=lambda kv: ["neither", "head_only", "both", "lb_only"].index(kv[0]))]
_f1r = lambda v: f"{v[0]:.1f} [{v[1]:.1f}, {v[2]:.1f}]"
ITEMS["T:refcheck"] = (S_B0, T(
    "Plausibility of the Reference in Segments by Location of the Large Error, and Large-Error Shares Without "
    "Reference-Suspect Segments (B0, A1, Test Set, Post Hoc)",
    ["Large error at", "Segments", "Same-foot repeat (%)", "Gap ≥ 1.6 × median (%)", "Reference suspect (%)",
     "Four IMU estimates agree, off reference (%)", "Either (%)"],
    _rk, [1500, 1000, 1400, 1500, 1400, 1800, 1000],
    "Reference suspect: two consecutive heel strikes from the same foot, or the longest reference interval ≥ 1.6 × the "
    "median interval (a long interval can also be a real pause). Four IMU estimates: head A1, head AC, lower-back A1, "
    "lower-back AC; 'agree' = range ≤ 3 steps/min with their median > 5 steps/min from the reference. "
    f"Reference-suspect segments: {RCK['n_segments'] - RCK['excl_ref_suspect_n'][0]} of {RCK['n_segments']} "
    f"(stroke {RCK['ref_suspect_by_cohort_all_segments']['CVA']}%, healthy {RCK['ref_suspect_by_cohort_all_segments']['HS']}%). "
    f"Without them ({RCK['excl_ref_suspect_n'][0]} segments, {RCK['excl_ref_suspect_n'][1]} participants), share of "
    f"|e_C| > 5: head {_f1r(RCK['excl_ref_suspect']['head'])}%, lower back {_f1r(RCK['excl_ref_suspect']['lb'])}%, "
    f"difference {_f1r(RCK['excl_ref_suspect']['diff'])} pp; stroke {RCK['excl_ref_suspect']['CVA|head'][0]:.1f}% vs "
    f"{RCK['excl_ref_suspect']['CVA|lb'][0]:.1f}%; segments with a large error at both / head only / lower back only: "
    f"{int(RCK['excl_ref_suspect']['n_both'][0])} / {int(RCK['excl_ref_suspect']['n_head_only'][0])} / "
    f"{int(RCK['excl_ref_suspect']['n_lb_only'][0])}. 95% CIs: participant bootstrap (2000)."))
_seg = RR["R12"]
ITEMS["T:seglen"] = (S_B0, T(
    "A1 Error by Segment Length (Number of Reference Heel Strikes; B0, Test Set, Post Hoc)",
    ["Heel strikes in segment", "Segments", "Head |*e*_{C}| [95% CI]", "Head |*e*_{C}| > 5 (%)",
     "Lower back |*e*_{C}| [95% CI]", "Lower back |*e*_{C}| > 5 (%)", "Reference cadence (median)"],
    [[g, f"{_seg['HE'][g]['n_segments']}",
      f"{m(_seg['HE'][g]['median'])} [{m(_seg['HE'][g]['lo'])}, {m(_seg['HE'][g]['hi'])}]", f"{_seg['HE'][g]['big_pct']:.1f}",
      f"{m(_seg['LB'][g]['median'])} [{m(_seg['LB'][g]['lo'])}, {m(_seg['LB'][g]['hi'])}]", f"{_seg['LB'][g]['big_pct']:.1f}",
      f"{_seg['HE'][g]['ref_cadence_median']:.0f}"] for g in ("5-10", "11-15", "16-20", ">20")],
    [1600, 1100, 1800, 1300, 1800, 1300, 1400],
    "Steps/min. Slow walkers take more steps over the same 6–10 m, so long segments are mostly CVA, PD, and RIL. Within "
    "cohorts, short segments (≤10 heel strikes) versus longer ones changed the large-error rate by "
    f"{_seg['HE']['mh_risk_difference_pp']:+.1f} percentage points at the head and {_seg['LB']['mh_risk_difference_pp']:+.1f} at the "
    "lower back (cohort-weighted risk difference; only HS, HOA, KOA, ACL, and RIL had short segments, 72 in total)."))
ITEMS["T:e2e_main"] = (S_E2E, T(
    "Reference-Assisted (B0) Versus Head-Only Offline (B1) and Causal (B2, B2-t) Estimation, Test Set",
    ["Metric", "B0", "B1", "B2", "B2-t^{a}"],
    [["|*e*_{C}|, median [95% CI]", "1.53 [1.31, 1.71]", "1.56 [1.40, 1.75]", "1.62 [1.50, 1.75]", "1.55 [1.43, 1.68]"],
     ["Bias (95% LoA)", "−0.45 (−11.5, 10.6)", "−0.48 (−12.3, 11.3)", "2.20 (−15.0, 19.4)", "0.75 (−12.6, 14.1)"],
     ["90th pct. of |*e*_{C}|", "4.6", "4.8", "6.1", "4.8"],
     ["No output (%)", "0", "1.6", "1.5", "1.7"],
     ["|*e*_{C}| > 5 or no output (%)", "9.1", "10.9", "13.6", "11.0"],
     ["   CVA / HS (%)", "35.2 / 0.8", "33.3 / 4.9", "42.0 / 5.3", "32.1 / 5.9"],
     ["Walking F1; turn P / R", "reference", "0.95; 0.80 / 0.99", "0.96; 0.39 / 1.00", "as B2"],
     ["Step F1 (full walk)", "—", "0.91", "0.86", "0.87"],
     ["Step confirmation; first output (s)", "offline", "offline", "0.35; 2.6", "0.46; 2.7"],
     ["Equivalence to B0 (post hoc, ±1.8)", "—", "Yes (mean diff. 0.05; 90% CI −0.04, 0.13)", "No", "—"]],
    [2600, 1700, 2140, 2000, 2000],
    "Steps/min unless stated; 183 participants, 1860 reference segments; failures counted. CIs: 2000 participant-level "
    "bootstrap resamples. B2 is causal only after the providers’ offline preprocessing (14-Hz low-pass, interpolation, offset "
    "correction). B2 vs. B1: +0.14 steps/min (95% CI 0.03–0.34, Holm *p* = 0.006); B2-t vs. B1: +0.04 (Holm *p* = 0.22). "
    "B2 false turn onsets: 1.5 per trial, 89% below 90° of rotation. ^{a}Post hoc: causal detector re-selected on development "
    "data after the first test evaluation."))
ITEMS["F:e2e"] = (S_E2E, ("fig", ("fig_v16/fig10_endtoend.png",
    "Head-only end-to-end estimation (test set). (a) Segments with |*e*_{C}| > 5 steps/min (solid) or without output (hatched) "
    "by cohort for reference-assisted B0, head-only offline B1, and head-only causal B2. (b) Latencies of the causal pipeline "
    "relative to the reference heel strike, walking onset, and turn onset (box: IQR; whiskers: 1.5 IQR).", 4.2)))
ITEMS["F:sims"] = (S_ROB, ("fig", ("fig_results/fig7_simulations.png",
    "Mounting simulations. (a) A0 cadence error versus X-axis tilt (median and 95% CI; bars: halved segments, right axis); blue line: "
    "A0g and A1, invariant to fixed rotation. (b) A0g and A1 versus lever-arm offset (median and 95% CI; 20 directions per offset).", 5.0)))
ITEMS["F:mount"] = (S_ROB, ("fig", ("fig_schematics/fig1_sensors_frames_leverarm_v17.png",
    "Sensors and mounting error (former main-text Fig. 1). (a) Sensor positions; X is the harmonised cranio-caudal axis. "
    "(b) Rotation R(theta, u) tilts X by phi = arccos R11 to X'; r offsets the sensor to a simulated temple position. "
    "(c) Tangential and centripetal accelerations introduced by the lever arm. Simulation results: see the mounting-simulation figure in the section on mounting and sensor robustness.", 3.4)))
ITEMS["F:ba4"] = (S_B0, ("fig", ("fig_v17/figS_ba4_v17.png",
    "Bland–Altman plots of cadence (B0, test set) for four signals: (a) head A1, (b) head A0g, (c) head AC, (d) lower-back A1. "
    "Red: stroke (CVA); purple: radiation-induced leukoencephalopathy (RIL); grey: other cohorts. Solid line: bias; dashed lines "
    "and band: repeated-measures 95% limits of agreement; segments beyond ±25 steps/min are drawn at the axis edge (triangles).", 5.0)))
ITEMS["T:bounds"] = (S_ROB, T(
    "Operating Conditions of Head-IMU Cadence Estimation (Simulation and Observed Failures)",
    ["Factor", "Effect in this study", "Recommendation"],
    [["Tilt with a fixed axis (A0)", "Stable to ≈10°; +14% error at 10°–20°; ×2.2 and 8% halving at 30°–45°", "Use A0g or A1"],
     ["Fixed rotation (A0g, A1)", "Exactly invariant", "Prefer A0g or A1"],
     ["Drift 0°–20° per trial", "A1 invariant; A0g ≤2.3 steps/min in 4 of 1860 segments; A0 +1.1 pp large errors", "Prefer A1"],
     ["Lever arm 2–8 cm", "No effect in straight walking (A0g, A1 1.44–1.49 steps/min); ≈3 m/s² centripetal term at 360°/s, 8 cm",
      "No step events within turns"],
     ["Accelerometer noise ≤0.2 m/s²", "No change in error (paired 95% CIs including 0)", "Not limiting here"],
     ["Gyroscope bias", "≤10°/s: no effect; apparent resting rate >30°/s: 47% of trials without B1 output",
      "Calibrate over a known still period"],
     ["Sampling rate", "50 Hz: +0.5 pp large errors; 25 Hz: +4.9 pp", "≥50 Hz"],
     ["AC estimator", "Lowest median error; widest LoA; ≥1.8 s per segment", "Segment summaries only"]],
    [2600, 5000, 2800],
    "Simulations of the strapped forehead sensor with recorded signals; eyeglass frames, slippage, and active head turns were "
    "not tested. Drift: post hoc rerun with the drift angular rate (Post Hoc Analyses table)."))
# ------------------------------------------------------------------------------------------------ V18 items (AGS)
S_AGS = "Failure Analysis and Stride-Based Estimators"
_V18 = HERE.parent / "v18"
_dc = pd.read_csv(_V18 / "dev_cands.csv")
_pm = lambda e: _dc.assign(a=e.abs()).groupby("participant")["a"].median().median()
_cand = [("Published peak, median step", "C0"), ("Peak, median stride", "Cs"), ("Autocorrelation", "Cac"),
         ("Median of peak, stride and autocorrelation", "Med3"), ("Median of guided-peak stride, stride, autocorrelation", "Med3g"),
         ("Guided peak (0.55 T) stride + AC (AGS, frozen)", "Med_g0.55_ac"), ("Guided peak (0.65 T) stride + AC", "Med_g0.65_ac"),
         ("Guided peak (0.75 T) stride + AC", "Med_g0.75_ac")]
ITEMS["T:ags_dev"] = (S_AGS, T(
    "Candidate Estimators on the Development Set (Head A1, B0, 77 Participants, 842 Segments)",
    ["Estimator", "|*e*_{C}|, median", "|*e*_{C}| > 5 (%)", "RIL > 5 (%)", "CVA > 5 (%)", "No output (segments)"],
    [[nm, f"{_pm(_dc[k] - _dc.R):.2f}", f"{100 * ((_dc[k] - _dc.R).abs() > 5).mean():.1f}",
      f"{100 * ((_dc[k] - _dc.R)[_dc.cohort == 'RIL'].abs() > 5).mean():.1f}",
      f"{100 * ((_dc[k] - _dc.R)[_dc.cohort == 'CVA'].abs() > 5).mean():.1f}", f"{int(_dc[k].isna().sum())}"] for nm, k in _cand],
    [3300, 1300, 1300, 1100, 1100, 1300],
    "Reference: 60 / median reference step interval. T: autocorrelation step time of the segment. Selection rule: lowest "
    "share of |e_C| > 5; participant 5-fold CV inside the development set selected AGS in 3 of 5 folds (the median-of-three "
    "variant in 2). The estimator was frozen (code hash recorded in V18_FREEZE.md) before any test-set evaluation."))
_S18 = json.loads((_V18 / "test_root" / "v18_stats.json").read_text())
_f = lambda v, nd=1: f"{v[0]:.{nd}f} [{v[1]:.{nd}f}, {v[2]:.{nd}f}]"
_ord = ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]
ITEMS["T:ags_cohort"] = (S_AGS, T(
    "Published Peak Estimator Versus AGS by Cohort (Test Set, B0, A1): Share of Segments With |*e*_{C}| > 5 Steps/Min",
    ["Cohort", "Head, published", "Head, AGS", "Lower back, published", "Lower back, AGS", "Head |*e*_{C}|: published / AGS"],
    [[c, _f(_S18["by_cohort"][c]["HE|C_peak|big"]), _f(_S18["by_cohort"][c]["HE|C_ags|big"]),
      _f(_S18["by_cohort"][c]["LB|C_peak|big"]), _f(_S18["by_cohort"][c]["LB|C_ags|big"]),
      f"{_S18['by_cohort'][c]['HE|C_peak|med'][0]:.2f} / {_S18['by_cohort'][c]['HE|C_ags|med'][0]:.2f}"] for c in _ord]
    + [["All", _f(_S18["primary"]["HE|C_peak|big"]), _f(_S18["primary"]["HE|C_ags|big"]), _f(_S18["primary"]["LB|C_peak|big"]),
        _f(_S18["primary"]["LB|C_ags|big"]),
        f"{_S18['primary']['HE|C_peak|med'][0]:.2f} / {_S18['primary']['HE|C_ags|med'][0]:.2f}"]],
    [900, 1700, 1700, 1800, 1800, 2000],
    "Percent with participant-bootstrap 95% CIs (1000 resamples per cohort, 2000 overall). Sensitivity: without reference-"
    f"suspect segments, head AGS minus published {_f(_S18['no_ref_suspect']['HE|ags-peak|big'])} pp; with the stride "
    f"reference, {_f(_S18['stride_ref']['HE|ags-peak|big'])} pp."))
_AN = json.loads((_V18 / "ext_root" / "v18_analysis.json").read_text())
_tn = {"extra peaks": "Extra peaks", "missed peaks": "Missed peaks", "interval statistic": "Events correct, step median jumps",
       "reference suspect": "Reference suspect", "ok": "No large error"}
_rows = []
for loc, ln in (("HE", "Head"), ("LB", "Lower back")):
    for t in ("extra peaks", "missed peaks", "interval statistic", "reference suspect", "ok"):
        m = _AN[loc]["test"]["mech"][t]; fx = _AN[loc]["test"]["fixed_by_type"].get(t)
        _rows.append([ln if t == "extra peaks" else "", _tn[t], f"{m['n']}", f"{m['R_step']:.0f}", f"{m['amp']:.2f}", f"{m['sr']:.2f}",
                      "—" if m["fp_intra"] is None or t != "extra peaks" else f"{100 * m['fp_intra']:.0f}",
                      "—" if fx is None else f"{100 * fx['+stride']:.0f} / {100 * fx['AGS']:.0f}"])
ITEMS["T:mech"] = (S_AGS, T(
    "Failure Types of the Published Peak Estimator and Their Signal Characteristics (Test Set, B0, A1)",
    ["Site", "Type", "Segments", "Ref. cadence", "Amplitude (m/s²)", "SR", "Extra peaks inside a step (%)",
     "Fixed: +stride / AGS (%)"],
    _rows, [1100, 2400, 900, 1000, 1200, 700, 1400, 1700],
    "Medians per type. Types (in this order): reference suspect; events correct (precision and recall >= 0.9 at 0.15 s) "
    "but |e_C| > 5; extra peaks (precision < 0.9); missed peaks (recall < 0.9). Amplitude: RMS of the band-passed |a| in the "
    "segment. Extra peaks inside a step: median share of unmatched peaks lying 0.15-0.6 reference step times after the "
    "previous reference heel strike. Fixed: share brought within 5 steps/min by the stride median alone and by AGS. "
    f"Segments without a large error that became large: +stride {100 * _AN['HE']['test']['broken_ok']['+stride']:.1f}% / "
    f"AGS {100 * _AN['HE']['test']['broken_ok']['AGS']:.1f}% (head)."))

ITEMS["T:screen"] = (S_TR, T(
    "Early Screening Rules: Gain, Discrimination, and Exclusion Cost (Published Peak Estimator, Test Set; Former Main-Text Table)",
    ["Criterion", "Retained", "Discrimination", "Gain over random deletion", "Cost at VGA ≥ 3"],
    [["Turn gate (30°/s)", "84.5% of walking time", "Turn sensitivity 0.82; false flags 0.046", "Recall +6.5 pp [6.0, 6.9]",
      "Turn sensitivity 0.62"],
     ["Trial SR ≥ 0.32", "95.5% of segments", "AUROC 0.90 [0.84, 0.94]; sensitivity 0.40", "Large errors −3.4 pp [−6.1, −1.3]",
      "Excluded 29.9% [7.3, 53.8]; falsely excluded 8.5% [0, 21.8]"],
     ["SR+2 model^{a}", "95.8% of segments", "AUROC 0.92 [0.88, 0.94]; sensitivity 0.38", "No gain beyond SR at equal coverage",
      "Excluded 22.4%; falsely excluded 5.1%; sensitivity 0.58"]],
    [1500, 1600, 2500, 2300, 2500],
    "Trial SR: median over the trial's segments of the head step regularity; threshold = development 10th percentile. "
    "Sensitivity: share of segments with |e_C| > 5 steps/min that are flagged; falsely excluded: share of segments without a "
    "large error that are excluded (VGA ≥ 3: 23 participants, 174 segments, 117 without a large error). By location of the "
    "large error, the trial-level rule flagged 55% [29, 71] of segments with a large error at both sites but only 19% [3, 35] "
    "of head-only large errors (difference 35 pp [6, 59]). ^{a}Exploratory; adds the peak–autocorrelation cadence "
    "disagreement and the interval CV in a ridge logistic model fitted on development segments. These rules were replaced by "
    "the segment-level rule of the main text, which is defined on the same unit as the error and for the AGS estimator."))
ITEMS["F:screen"] = (S_TR, ("fig", ("fig_v17/fig4_screen_v17.png",
    "Trial-level step-regularity screening (test set; former main-text figure). (a) Share of large errors among retained "
    "segments as segments are removed from lowest to highest SR (band: 95% CI); random deletion leaves the share unchanged, "
    "an ideal screen removes all large errors first. (b) Share excluded by the SR threshold (0.32) by clinician-rated VGA; "
    "filled: all segments of the group; open: segments without a large error (false exclusion). Error bars: participant "
    "bootstrap 95% CIs.", 3.4)))
_RV = json.loads((_V18 / "ext_root" / "v18_review.json").read_text())
_mm = lambda x: (f"{x:.1f}" if round(x, 1) >= 0 else f"−{abs(x):.1f}")
_c = lambda v: f"{_mm(v[0])} [{_mm(v[1])}, {_mm(v[2])}]"
_vr = []
for lv, lab in (("0", "0"), ("1", "1"), ("2", "2"), ("3", "≥ 3")):
    h, l_ = _RV["vga"]["HE"][lv], _RV["vga"]["LB"][lv]
    _vr.append([lab, f"{h['n_part']} / {h['n_seg']}", _c(h["excluded"]), _c(h["false_excl"]), _c(h["big_in"]), _c(h["sens"]),
                _c(l_["excluded"]), _c(l_["false_excl"])])
_o = _RV["overall"]
_vr.append(["All^{a}", f"{_RV['n_participants']} / {_RV['n_segments']}", _c(_o["HE"]["excluded"]), _c(_o["HE"]["false_excl"]),
            _c(_o["HE"]["big_in"]), _c(_o["HE"]["sens"]), _c(_o["LB"]["excluded"]), _c(_o["LB"]["false_excl"])])
_fs = _RV["flag_by_source"]
ITEMS["T:env_vga"] = (S_AGS, T(
    "Segment-Level Rule (SR of the Same Sensor ≥ 0.7, Chosen on the Development Set): Exclusion Cost by Clinician-Rated VGA "
    "(Test Set, B0, A1, AGS, Post Hoc)",
    ["VGA", "Participants / segments", "Head: excluded (%)", "Head: falsely excluded (%)", "Head: AGS |*e*_{C}| > 5 among retained (%)",
     "Head: large errors flagged (%)", "Lower back: excluded (%)", "Lower back: falsely excluded (%)"],
    _vr, [700, 1200, 1450, 1450, 1500, 1450, 1350, 1340],
    "Percent with participant-bootstrap 95% CIs (2000 resamples, participants resampled within the whole test set). "
    "Falsely excluded: excluded among segments without an AGS large error; flagged: excluded among AGS large errors. VGA "
    "(0 none to 4 very severe; 3 and 4 pooled) is missing for 42 segments. ^{a}Including segments without VGA. By location of "
    f"the large error (head rule): AGS large errors at both sites flagged {_c(_fs['ags']['both'])}% (n = {_fs['ags']['n_both']}), "
    f"head-only {_c(_fs['ags']['head_only'])}% (n = {_fs['ags']['n_head_only']}); published estimator {_c(_fs['peak']['both'])}% and "
    f"{_c(_fs['peak']['head_only'])}%. With the stride-defined reference, head minus lower back, share of |e_C| > 5: published "
    f"{_c(_RV['stride_ref']['peak']['HE-LB_big'])} pp, AGS {_c(_RV['stride_ref']['ags']['HE-LB_big'])} pp."))

_SRJ = json.loads((HERE.parent / "v19" / "sensor_req" / "v19_sensor_req.json").read_text())
_lab = {"reference|0": "As recorded (100 Hz)", "fs|50": "50 Hz", "fs|25": "25 Hz", "fs|20": "20 Hz",
        "noise|0.05": "Noise 0.05 m/s²", "noise|0.1": "Noise 0.1 m/s²", "noise|0.2": "Noise 0.2 m/s²", "noise|0.5": "Noise 0.5 m/s²",
        "noise|1.0": "Noise 1.0 m/s²", "lsb|0.01": "LSB 0.01 m/s²", "lsb|0.05": "LSB 0.05 m/s²", "lsb|0.1": "LSB 0.1 m/s²",
        "lsb|0.2": "LSB 0.2 m/s²", "lsb|0.5": "LSB 0.5 m/s²", "range|1.5": "Range ±1.5 g", "range|2.0": "Range ±2 g",
        "lowpower|25Hz+8bit4g": "25 Hz, ±4 g, 8 bit", "gyro_B1|turn removal": "Head-only B1, gyroscope turns",
        "accel_only_B1|no turn removal 100 Hz": "Head-only, no gyroscope, 100 Hz",
        "accel_only_B1|no turn removal 25 Hz": "Head-only, no gyroscope, 25 Hz"}
_q = lambda v, nd: f"{v[0]:.{nd}f} [{v[1]:.{nd}f}, {v[2]:.{nd}f}]"
ITEMS["T:sensreq"] = (S_ROB, T(
    "Sensor Requirements of Head Cadence Estimation: All Simulated Degradations (Test Set, Head, Post Hoc)",
    ["Condition", "AGS |*e*_{C}|", "AGS > 5 or none (%)", "Step median |*e*_{C}|", "Step median > 5 (%)", "Stride median > 5 (%)",
     "Autocorrelation > 5 or none (%)"],
    [[_lab[k], _q(v["AGS"]["med"], 2), _q(v["AGS"]["big_or_none"], 1), _q(v["peak"]["med"], 2) if "peak" in v else "—",
      _q(v["peak"]["big_or_none"], 1) if "peak" in v else "—", _q(v["stride"]["big_or_none"], 1) if "stride" in v else "—",
      _q(v["ac"]["big_or_none"], 1) if "ac" in v else "—"]
     for k, v in _SRJ.items() if k in _lab],
    [2400, 1400, 1400, 1400, 1300, 1300, 1240],
    "Steps/min; brackets: participant-bootstrap 95% CIs (2000). Degradations of the recorded 100-Hz head accelerometer: "
    "anti-aliased decimation; white Gaussian noise per axis (1.0 m/s² at 100 Hz ≈ 14 mg/√Hz); rounding to the LSB; per-axis "
    "saturation. Nothing re-tuned. Head-only rows are paired with the reference segments by largest overlap (≥ 1 s); without "
    "the gyroscope the whole walking bout, including the turn, is one segment. Per-trial maximum |acc| per axis (whole trial, "
    "head): median {:.2f} g, 99th percentile {:.2f} g. AGS run time per segment: median {:.2f} ms (Python, one core).".format(
        _SRJ["head_peak_abs_acc_g_quantiles"][0], _SRJ["head_peak_abs_acc_g_quantiles"][2], _SRJ["timing"]["ms_per_segment_median"])))
_TRJ = json.loads((HERE.parent / "v19" / "transmission" / "v19_transmission.json").read_text())
_c = _TRJ["clean"]
ITEMS["T:transmission"] = (S_ROB, T(
    "The Forehead as a Sensing Site: Head-Versus-Lower-Back Step-Band Measures in Segments Without a Large Error (Test Set, Post Hoc)",
    ["Cohort (participants / segments)", "Vertical RMS ratio", "Coherence at step frequency", "Head vertical RMS (m/s²)",
     "Lower-back vertical RMS (m/s²)", "Horizontal angular-rate ratio", "Head-on-trunk yaw rate (°/s)"],
    [[f"{k} ({_c[k]['n_part']} / {_c[k]['n_seg']})"] + [_q(_c[k][m], 2) for m in ("tr_v", "coh_v", "rms_v_he", "rms_v_lb", "tilt_ratio")]
     + [_q(_c[k]["yaw_rel_bp"], 1)] for k in ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL", "All"] if k in _c],
    [1700, 1400, 1450, 1450, 1450, 1500, 1490],
    "Same B0 straight segments; per-segment measures computed with both sensors of the same walk (v17_head_trunk.py). Each "
    "sensor's vertical is its own gravity direction; band 0.6–3 Hz. Ratios: head / lower back. Coherence: magnitude-squared, "
    "Welch 2.56-s windows, mean within ±0.25 Hz of the reference step frequency. Yaw rate: RMS of head minus trunk angular "
    "rate about vertical in the step band. Segments without |e_C| > 5 at either site with the published estimator and with "
    "AGS. Medians of participant medians; participant bootstrap 95% CIs (2000). Descriptive only: these measures are not "
    "independent of detection failure and are not used to infer its cause."))
ITEMS["F:failure"] = (S_B0, ("fig", ("fig_v17/fig5_failure_v17.png",
    "Large errors and step regularity (B0, test set; former main-text figure). (a) Share of segments with |e_C| > 5 "
    "steps/min at the head and the lower back by head segment step regularity (SR), participant-bootstrap 95% CIs; segment "
    "counts below the axis. (b) Head versus lower-back |e_C| in the same segments (≥ 30 drawn at the edge); dashed: 5 "
    "steps/min. (c), (d) First 8 s of two straight segments, head A1 signal: a healthy participant (HS_31_4) and a stroke "
    "patient (CVA_17_2); dots: detected steps; vertical lines: reference heel strikes. SR is computed from the head signal only; "
    "errors are judged against the reference.", 3.4)))
_THJ = json.loads((HERE.parent / "v19" / "transmission_harm" / "v19_transmission.json").read_text())
_ch = _THJ["clean"]
ITEMS["T:harm"] = (S_ROB, T(
    "Head-Versus-Lower-Back Transmission by Frequency in Segments Without a Large Error (Development and Test, Post Hoc)",
    ["Cohort (participants / segments)", "Gain, stride (0.5×)", "Gain, step (1×)", "Gain, 2×", "Gain, 3×", "Coherence, step"],
    [[f"{k} ({_ch[k]['n_part']} / {_ch[k]['n_seg']})"] + [_q(_ch[k][m], 2) for m in ("G_0.5", "G_1.0", "G_2.0", "G_3.0", "C_1.0")]
     for k in ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]] +
    [[f"All ({_THJ['n_participants']} / {_THJ['n_clean']})"] + [_q(_ch["All"][m], 2) for m in ("G_0.5", "G_1.0", "G_2.0", "G_3.0", "C_1.0")]],
    [2400, 1600, 1600, 1600, 1600, 1600],
    "Input: lower-back vertical acceleration; output: head vertical acceleration (each sensor's own gravity direction). H1 gain "
    "and magnitude-squared coherence (Welch, 2.56-s Hann windows, 50% overlap) at multiples of the reference step frequency. "
    "Segments without |e_C| > 5 at either site with the published estimator and with AGS. Medians of participant medians; "
    "participant bootstrap 95% CIs (2000). The inter-sensor phase was not interpreted because sensor synchronisation at the "
    "10-ms level is not documented."))
_MGJ = json.loads((HERE.parent / "v19" / "mobgap" / "v19_mobgap_stats.json").read_text())
ITEMS["T:mdpreset"] = (S_AGS, T(
    "Open-Source Mobilise-D Cadence Presets (mobgap 1.2.0, Default Parameters) on the Same Short Straight Segments (Test Set, Post Hoc)",
    ["Algorithm", "Head |*e*_{C}|", "Head > 5 (%)", "Lower back |*e*_{C}|", "Lower back > 5 (%)"],
    [[nm] + [_q(_MGJ[loc]["step"][f"{k}|{m_}"], nd) for loc in ("HE", "LB") for m_, nd in (("med", 2), ("big", 1))]
     for nm, k in (("Regular-walking preset (IcdShinImproved)", "MD_regular"), ("Impaired-walking preset (IcdHKLeeImproved)", "MD_impaired"),
                   ("Ionescu contacts, step median", "Ionescu_step"), ("Ionescu contacts, stride median", "Ionescu_stride"),
                   ("AGS", "C_ags"))],
    [3400, 1750, 1750, 1750, 1750],
    "Steps/min; participant-bootstrap 95% CIs (2000). CadFromIcDetector with Hampel smoothing; segment cadence = mean of the "
    "per-second cadence. The presets were developed for walking bouts of daily living detected on the lower back; here the "
    "gait-sequence detection is replaced by the reference segmentation and the segments are 6–10 m straight walks. AGS minus "
    f"impaired-walking preset, share > 5: head {_q(_MGJ['HE']['step']['ags-MD_impaired|big'], 1)} pp, lower back "
    f"{_q(_MGJ['LB']['step']['ags-MD_impaired|big'], 1)} pp."))
ITEMS["F:sensing"] = (S_ROB, ("fig", ("fig_v19/fig7_sensing_v19.png",
    "The forehead as a sensing site (test set, B0 straight segments). (a) Head / lower-back ratio of the step-band (0.6–3 Hz) "
    "vertical-acceleration RMS (circles) and horizontal angular-rate RMS (squares) in segments without a large error, by "
    "cohort; participant-level medians with bootstrap 95% CIs. (b) Distribution of the head step-band vertical RMS in the same "
    "segments; vertical lines: in-band noise of a consumer MEMS accelerometer (data-sheet value) and of the simulated white "
    "noise (0.2 and 1.0 m/s² per axis). (c) Share of head segments with |e_C| > 5 steps/min versus output data rate, published "
    "step-median estimator and AGS.", 7.0)))
# ------------------------------------------------------------------------------------------------ order by first mention
BODY = (HERE / os.environ.get("SUPP_BODY", "body_v16.py")).read_text(encoding="utf-8")
RANGES = {}
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
           "the reference-assisted head versus lower-back comparison (B0) and the mounting simulations are prespecified; the "
           "AGS estimator was designed and frozen on the development set and evaluated once on the test set (its stride-reference "
           "analysis was listed in the freeze record); the head-only pipelines (B1, B2), the sensor-sensitivity simulations, and "
           "the early screening rules are exploratory, B2-t is post hoc; the ablation, failure mechanisms, and the segment-level "
           "rule are post hoc (rule threshold chosen on development data); the open-source Mobilise-D baseline, the head-trunk "
           "transmission measures, and the sensor-requirement simulations were run after the freeze with nothing re-tuned "
           "(post hoc); DUO-GAIT results are a frozen external check. "
           "Simulation results describe recorded signals with synthetic perturbations, not real re-wearing.")]
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
