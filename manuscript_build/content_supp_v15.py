# -*- coding: utf-8 -*-
"""Supplementary Material (Tables S1–S14, Figs. S1–S5)."""
R = {}
TITLE = "Cadence From a Single Forehead IMU in Clinical Cohorts: Comparison With the Lower Back"
FIGPREFIX = "S"
B = []
def h1(t): B.append(("h1", t))
def p(t): B.append(("p", t))
def fig(path, caption, width=5.0): B.append(("fig", (path, caption, width)))
def table(caption, head, rows, widths, note=None): B.append(("table", (caption, head, rows, widths, note)))

p("All values refer to the participant-wise test set (183 participants, 930 trials) unless stated otherwise. Medians are "
  "participant-level medians; brackets give bootstrap 95% CIs (2000 participant resamples) or, where stated, interquartile ranges.")

h1("Analysis Parameters")
table("Analysis Parameters and How They Were Set",
      ["Parameter", "Value", "Set by"],
      [["Band-pass upper cutoff", "3.0 Hz", "Prespecified (step frequency ≤2.7 Hz)"],
       ["Band-pass lower cutoff", "0.6 Hz (from 0.6/0.8/1.0/1.2 Hz)", "Development-set rule"],
       ["Filter", "Third-order Butterworth, zero phase", "Prespecified"],
       ["Minimum peak prominence", "max(0.12 m/s², 1.5*σ̂*)", "Prespecified"],
       ["Minimum peak distance", "0.30 s", "Prespecified"],
       ["Gravity low-pass", "0.3 Hz", "Prespecified"],
       ["Gate threshold *q*^{*}", "30°/s (from 20/30/45/60/90°/s)", "Development-set rule"],
       ["Gate median filter / minimum duration / padding", "0.15 / 0.30 / 0.20 s", "Prespecified"],
       ["Peak–heel-strike lag", "Head 0.06–0.07 s; lower back 0.10 s", "Development-set median"],
       ["Event-matching tolerance", "0.15 s (sensitivity 0.10, 0.20 s)", "Prespecified"],
       ["Raw-gap invalidation limit", "0.05 s", "Prespecified"],
       ["Autocorrelation search range / peak criterion", "0.30–0.90 s / 60% of maximum", "Prespecified"],
       ["Random-gate repetitions", "200 per trial", "Prespecified"],
       ["Step-regularity threshold", "0.32 (10th percentile of development trials; 5th/20th as sensitivity)", "Development-set rule (post hoc)"],
       ["Rigid-rotation simulation", "5°–45°, 50 random axes per angle", "Prespecified"],
       ["Lever-arm simulation", "2–8 cm, 20 random directions; 10-Hz low-pass for angular acceleration", "Prespecified"],
       ["Bootstrap", "2000 participant-level resamples", "Prespecified"],
       ["Development/test split", "≈30/70%, stratified by cohort × sensor system, fixed seed", "Prespecified"]],
      [3300, 4000, 3140])

h1("Signal-Level Verification")
table("Signal-Level Verification by Sensor System (All Included Trials)",
      ["Metric", "Head, XSens", "Head, Technoconcept", "Lower back, XSens", "Lower back, Technoconcept"],
      [["Included trials / participants", "569 / 116", "782 / 154", "569 / 116", "782 / 154"],
       ["Missing samples (fraction)", "0.002 [0.001, 0.004]", "0 [0, 0]", "0.003 [0.001, 0.007]", "0 [0, 0]"],
       ["Longest gap (s)", "0.01 [0.01, 0.02]", "0 [0, 0]", "0.02 [0.01, 0.04]", "0 [0, 0]"],
       ["Saturated samples", "0", "0", "0", "0"],
       ["Standing acceleration SD (m/s²)", "0.33 [0.21, 0.58]", "0.31 [0.18, 0.52]", "0.15 [0.10, 0.21]", "0.14 [0.10, 0.20]"],
       ["Standing angular-rate SD (°/s)", "6.2 [3.4, 11.0]", "7.3 [3.5, 14.1]", "2.7 [1.9, 3.9]", "2.8 [1.9, 4.4]"],
       ["Standing gravity norm (m/s²)", "9.80 [9.75, 9.85]", "9.74 [9.66, 9.80]", "9.96 [9.93, 10.01]", "9.80 [9.76, 9.83]"],
       ["Gyroscope offset (°/s)", "2.3 [1.2, 4.6]", "7.0 [5.0, 9.8]", "1.0 [0.6, 1.6]", "4.9 [4.1, 5.9]"],
       ["Fraction of gravity on X", "0.955 [0.918, 0.981]", "0.977 [0.946, 0.992]", "0.982 [0.958, 0.994]", "0.973 [0.940, 0.991]"],
       ["Integrated turn angle (°)", "174 [167, 184]", "179 [170, 192]", "179 [173, 187]", "181 [174, 190]"],
       ["Dominant / step frequency", "1.011 [1.002, 1.021]", "1.013 [1.002, 1.027]", "1.009 [1.001, 1.021]", "1.011 [1.001, 1.024]"],
       ["Step regularity", "0.94 [0.86, 0.98]", "0.86 [0.66, 0.94]", "0.96 [0.89, 0.99]", "0.90 [0.73, 0.96]"]],
      [2840, 1900, 1900, 1900, 1900],
      "Median [interquartile range] across trials. Technoconcept packet counters are stored as floating-point values and were rounded "
      "to integer indices before gap detection; no Technoconcept trial had missing samples. Ten participants were recorded with both "
      "systems at different visits, so participant counts per system sum to more than 260. Standing variability includes postural sway "
      "and is not sensor noise. Trial-level maxima for XSens: missing fraction 0.081 (head) and 0.164 (lower back); longest gap 0.35 s "
      "(head) and 1.37 s (lower back).")

h1("Stratified Cadence Error")
table("Absolute Cadence Error by Cohort, Sensor System, and Age (Steps/Min)",
      ["Stratum", "*n*", "Head A0g", "Head A1", "Head AC", "Lower back A1", "Head A1 halving (%)"],
      [["HS", "51", "1.08 [0.92, 1.34]", "1.11 [1.00, 1.40]", "0.87 [0.72, 1.03]", "1.04 [0.91, 1.22]", "0.0"],
       ["HOA", "11", "1.75 [0.83, 2.41]", "1.78 [1.25, 2.68]", "1.05 [0.83, 1.45]", "1.72 [1.28, 1.91]", "0.0"],
       ["KOA", "13", "1.58 [1.27, 1.95]", "1.58 [1.13, 1.83]", "1.03 [0.71, 1.47]", "1.05 [0.73, 1.72]", "0.0"],
       ["ACL", "8", "1.67 [0.99, 2.53]", "1.45 [1.22, 2.26]", "1.04 [0.41, 1.89]", "1.47 [0.83, 1.84]", "0.0"],
       ["CVA", "34", "2.67 [1.75, 5.77]", "2.58 [2.17, 6.99]", "2.07 [1.30, 4.53]", "2.86 [1.64, 6.19]", "0.0"],
       ["PD", "16", "1.74 [1.12, 2.10]", "1.64 [1.06, 2.06]", "0.96 [0.79, 1.55]", "1.22 [0.92, 1.82]", "0.0"],
       ["CIPN", "14", "1.09 [0.74, 1.78]", "1.25 [0.83, 1.75]", "0.73 [0.55, 0.94]", "1.20 [0.98, 1.46]", "0.0"],
       ["RIL", "36", "1.52 [1.20, 1.72]", "1.27 [1.17, 1.74]", "0.86 [0.68, 1.15]", "1.37 [1.11, 1.96]", "1.2"],
       ["Technoconcept", "107", "1.64 [1.42, 1.78]", "1.64 [1.42, 1.85]", "1.05 [0.90, 1.21]", "1.51 [1.32, 1.82]", "0.6"],
       ["XSens", "80", "1.31 [1.07, 1.59]", "1.26 [1.13, 1.56]", "0.94 [0.80, 1.07]", "1.18 [1.03, 1.42]", "0.0"],
       ["Age <60 y", "93", "1.28 [1.12, 1.51]", "1.27 [1.12, 1.53]", "0.94 [0.80, 1.07]", "1.21 [1.07, 1.44]", "0.5"],
       ["Age ≥60 y", "90", "1.66 [1.54, 1.82]", "1.74 [1.52, 1.95]", "1.07 [0.89, 1.38]", "1.52 [1.30, 1.77]", "0.1"]],
      [1500, 620, 1650, 1650, 1650, 1650, 1720],
      "Participants recorded with both systems contribute to both sensor strata. Sensor system and age are confounded with cohort.")

h1("Mounting-Error Simulation")
table("Cadence Error Under Simulated Mounting Errors (Steps/Min)",
      ["Perturbation", "Level", "Method", "Median |*e*_{C}| [95% CI]", "Detection ratio", "Halving (%)"],
      [["Rigid rotation (X-axis tilt)", "≤5°", "A0", "1.54 [1.37, 1.75]", "0.92", "0.3"],
       ["", "5°–10°", "A0", "1.59 [1.38, 1.75]", "0.92", "0.5"],
       ["", "10°–20°", "A0", "1.75 [1.68, 1.88]", "0.92", "1.1"],
       ["", "20°–30°", "A0", "2.10 [1.93, 2.25]", "0.90", "2.8"],
       ["", "30°–45°", "A0", "3.45 [2.95, 4.10]", "0.87", "8.2"],
       ["Lever arm", "0 cm", "A0g / A1", "1.51 [1.34, 1.65] / 1.53 [1.31, 1.71]", "0.92 / 0.92", "0.1 / 0.3"],
       ["", "2 cm", "A0g / A1", "1.44 [1.31, 1.59] / 1.44 [1.24, 1.69]", "0.92 / 0.92", "0.2 / 0.3"],
       ["", "4 cm", "A0g / A1", "1.49 [1.24, 1.64] / 1.44 [1.23, 1.64]", "0.92 / 0.92", "0.1 / 0.3"],
       ["", "6 cm", "A0g / A1", "1.49 [1.28, 1.64] / 1.49 [1.21, 1.64]", "0.93 / 0.92", "0.2 / 0.3"],
       ["", "8 cm", "A0g / A1", "1.49 [1.24, 1.64] / 1.44 [1.24, 1.64]", "0.93 / 0.92", "0.2 / 0.3"]],
      [2300, 1000, 1100, 3000, 1500, 1540],
      "A0g, A1, and A2 are exactly invariant to rigid rotation. Under every lever arm, A2 retained-step precision (median 1.00) and "
      "time coverage (median 0.87) were unchanged.")

h1("Cross-Visit Agreement")
table("Cross-Visit Agreement for Same-System Visit Pairs (*n* = 36)",
      ["Metric", "Head A1", "Head A0g", "Lower back A1", "Foot reference"],
      [["ICC(A,1) [95% CI]", "0.68 [0.50, 0.83]", "0.64 [0.43, 0.79]", "0.72 [0.57, 0.84]", "0.67 [0.47, 0.82]"],
       ["SEM (steps/min)", "6.1", "6.4", "5.8", "5.9"],
       ["MDC_{95} (steps/min)", "17.0", "17.7", "16.0", "16.3"]],
      [2440, 2000, 2000, 2000, 2000],
      "Earliest two same-system visits per participant; per-visit median cadence over all straight segments; visit interval median "
      "60 days (IQR 28–141). Variance decomposition of the head–reference step-time error (trial-level medians; 37 test participants with ≥2 visits of any system): participant 23%, visit 44%, trial 33%. Visit intervals ranged from 0 to 219 days.")

h1("Turn Gating by Cohort")
table("Turn Detection and Gate-Versus-Random Differences by Cohort (*q*^{*} = 30°/s)",
      ["Cohort", "*n*", "Turn sensitivity", "False-mark rate", "Time coverage", "Δ precision (pp)", "Δ recall in kept time (pp)"],
      [["HS", "51", "0.92", "0.048", "0.817", "0.23 (0.09, 0.39)", "7.65 (6.85, 8.38)"],
       ["HOA", "11", "0.68", "0.047", "0.870", "0.69 (0.12, 1.48)", "6.49 (5.25, 7.63)"],
       ["KOA", "13", "0.72", "0.035", "0.867", "1.01 (0.47, 1.60)", "6.29 (5.12, 7.45)"],
       ["ACL", "8", "0.89", "0.014", "0.851", "0.22 (0.02, 0.46)", "7.03 (5.86, 8.24)"],
       ["CVA", "34", "0.70", "0.085", "0.844", "0.96 (0.40, 1.56)", "6.07 (4.60, 7.48)"],
       ["PD", "16", "0.81", "0.010", "0.869", "0.67 (0.24, 1.21)", "6.24 (5.48, 7.05)"],
       ["CIPN", "14", "0.91", "0.016", "0.864", "0.82 (0.32, 1.46)", "6.29 (5.18, 7.57)"],
       ["RIL", "36", "0.81", "0.043", "0.848", "0.67 (0.38, 0.99)", "5.25 (4.40, 6.14)"],
       ["All", "183", "0.82", "0.046", "0.845", "0.62 (0.46, 0.79)", "6.46 (6.04, 6.89)"]],
      [1100, 620, 1500, 1500, 1400, 2160, 2160],
      "Sensitivity and false-mark rate: participant medians; coverage: mean of participant means. Δ: participant-level mean of "
      "A2 − A2-R with bootstrap 95% CI; pp: percentage points. All turns were detected in every cohort.")

h1("Event Matching")
table("Event-Level Agreement of Head Detectors With Reference Heel Strikes",
      ["Method", "Tolerance (s)", "Precision", "Recall", "F1", "Timing error (ms)", "Step-interval error (ms)"],
      [["A0", "0.10", "0.960", "0.888", "0.923", "30.7", "20.0"],
       ["A0", "0.15", "0.971", "0.900", "0.935", "32.1", "20.0"],
       ["A0", "0.20", "0.976", "0.900", "0.935", "32.1", "20.0"],
       ["A0g", "0.10", "0.963", "0.889", "0.930", "31.6", "20.0"],
       ["A0g", "0.15", "0.976", "0.900", "0.937", "32.8", "20.0"],
       ["A0g", "0.20", "0.981", "0.900", "0.939", "33.9", "20.0"],
       ["A1", "0.10", "0.963", "0.888", "0.930", "30.0", "20.0"],
       ["A1", "0.15", "0.976", "0.897", "0.936", "31.4", "20.0"],
       ["A1", "0.20", "0.981", "0.897", "0.937", "31.5", "20.0"]],
      [1100, 1300, 1300, 1300, 1300, 2000, 2140],
      "Participant-level medians; timing error is the mean absolute difference between matched candidates and heel strikes after lag "
      "correction.")

h1("Step-Regularity Screen")
table("Step-Regularity Screen of Head A1 Segments at Three Development-Set Percentile Thresholds",
      ["Threshold (SR)", "Segments / participants kept (%)", "Participants lost", "Large errors (%)", "Change, pp (95% CI)", "LoA (steps/min)", "Sens. / spec.", "Segments excluded by cohort (%)"],
      [["None", "100 / 100", "0", "9.0", "—", "−11.5, 10.5", "—", "—"], ["5th (0.20)", "96.8 / 97.8", "4", "6.5", "−2.5\n(−5.3, −0.8)", "−8.5, 7.9", "0.31 / 0.99", "CVA 13.7, RIL 7.0, HOA 3.6"], ["10th (0.32)", "95.5 / 95.6", "8", "5.6", "−3.4\n(−6.1, −1.3)", "−7.7, 7.3", "0.40 / 0.99", "CVA 21.3, RIL 9.4, HOA 3.6"], ["20th (0.53)", "91.9 / 90.7", "17", "4.0", "−5.0\n(−8.4, −2.6)", "−5.1, 4.8", "0.59 / 0.97", "CVA 37.5, RIL 14.3, HOA 7.3, KOA 3.4, PD 3.5"]],
      [1250, 1350, 950, 950, 1500, 1200, 1000, 2240],
      "Exploratory post hoc analysis on 1858 test segments (two segments of one trial without an SR estimate excluded). SR: head step "
      "regularity of the trial (normalized unbiased autocorrelation of the band-passed norm at the step lag). Large error: |*e*_{C}| > 5 "
      "steps/min. Change: retained minus all, participant-bootstrap 95% CI; random removal of the same number of segments left the "
      "large-error share at 9.0% for every threshold. LoA: segment-level 95% limits of agreement. Sensitivity and specificity refer to "
      "the flagging of large-error segments. Cohorts not listed had no excluded segments. AUC of head SR for large head errors 0.90 "
      "[0.85, 0.94]; for large lower-back errors 0.87 (lower-back SR: 0.91).")

h1("Supplementary Figures")
fig("fig_results/fig3_inclusion_flow.png",
    "Trial inclusion and participant-wise split. Ribbon width is proportional to the number of trials; colors denote cohorts. Five "
    "trials from one visit of RIL_12 (empty head signal) were excluded; the participant’s later visits were retained. Test "
    "participants with two same-system visits entered the cross-visit analysis.", 4.6)
fig("fig_results/figS1_signal_qc.png",
    "Distributions of signal-level verification metrics of the head sensor by sensor system: (a) standing gravity norm, (b) fraction "
    "of gravity on X, (c) integrated turn angle, (d) dominant-to-step frequency ratio, (e) standing angular-rate SD, and (f) step "
    "regularity.", 5.2)

# ---------------------------------------------------------------- V14.1 reorder (compact main text)
_T = {b[1][0]: b for b in B if b[0] == "table"}
_F = {b[1][0]: b for b in B if b[0] == "fig"}
def _t(key): return next(v for k, v in _T.items() if key in k)
def _f(key): return next(v for k, v in _F.items() if key in k)
_intro = B[0]
_cohort = ("table", ("Cohort Characteristics Reported by the Dataset Providers",
      ["Cohort", "*n*", "Trials", "Age (y)", "Speed (m/s)", "Stride time (s)", "U-turn time (s)"],
      [["HS", "73", "360", "39.8 (20.2)", "1.17 (0.22)", "1.12 (0.09)", "2.09 (0.61)"],
       ["HOA", "15", "74", "69.7 (13.2)", "0.77 (0.24)", "1.21 (0.13)", "3.04 (1.57)"],
       ["KOA", "18", "78", "69.7 (13.7)", "0.76 (0.21)", "1.24 (0.12)", "3.36 (1.81)"],
       ["ACL", "11", "60", "36.7 (11.9)", "0.98 (0.24)", "1.21 (0.19)", "2.30 (0.61)"],
       ["CVA", "49", "128", "59.0 (9.5)", "0.68 (0.22)", "1.28 (0.22)", "4.32 (2.36)"],
       ["PD", "24", "160", "74.2 (11.4)", "0.86 (0.23)", "1.11 (0.10)", "3.05 (0.90)"],
       ["CIPN", "19", "98", "63.4 (10.5)", "0.88 (0.22)", "1.19 (0.15)", "2.57 (0.90)"],
       ["RIL", "51", "398", "59.8 (13.8)", "0.75 (0.24)", "1.18 (0.22)", "3.43 (1.94)"],
       ["Total", "260", "1356", "—", "—", "—", "—"]],
      [1100, 700, 1000, 1300, 1600, 1700, 1700],
      "Mean (SD). Speed, stride time, and U-turn time are from Table 10 of the data descriptor (derived by the providers from the "
      "foot sensors); age and counts were recomputed from the trial metadata (age missing for one RIL participant)."))
_flow = ("fig", ("fig_ieee/fig2_method_flowchart.png",
    "Processing and evaluation pipeline. Red: reference information and random-gate control; blue: development and test "
    "evaluation. Section numbers refer to the main text.", 3.6))
_example = ("fig", ("fig_results/fig4_example_trial.png",
    "Test trial PD_15_2. (a) Head and (b) lower-back band-passed acceleration norm (A1) with detected steps (dots) and lag-shifted "
    "reference heel strikes (ticks); (c) head turning rate *q*(*t*), threshold *q*^{*}, and turn gate (hatched). Gray: reference "
    "turn. Impact peaks weaken and steps are missed at both locations during the turn.", 4.2))
_rewear = ("fig", ("fig_results/fig8_rewear.png",
    "Cross-visit agreement (36 participants). (a) Head A1 cadence at two visits (band: ±MDC_{95}; dashed: identity). (b) ICC(A,1) "
    "with 95% CI; shading marks poor, moderate, good, and excellent reliability (0.5, 0.75, 0.9).", 4.2))
B = [_intro,
     ("h1", "Cohorts and Processing Pipeline"), _cohort, _flow,
     ("h1", "Analysis Parameters"), _t("Analysis Parameters"),
     ("h1", "Inclusion and Signal-Level Verification"), _f("inclusion"), _t("Signal-Level Verification"), _f("signal_qc"),
     ("h1", "Example Trial and Event Matching"), _example, _t("Event-Level Agreement"),
     ("h1", "Stratified Cadence Error"), _t("by Cohort, Sensor System"),
     ("h1", "Mounting-Error Simulation"), _t("Simulated Mounting Errors"),
     ("h1", "Cross-Visit Agreement"), _rewear, _t("Cross-Visit Agreement"),
     ("h1", "Turn Gating by Cohort"), _t("Turn Detection and Gate"),
     ("h1", "Step-Regularity Screen"), _t("Step-Regularity Screen")]

# ---------------------------------------------------------------- V15 tables
B += [("h1", "Head Features Beyond Cadence"),
      ("table", ["Validity and Within-Visit Reliability of Head Features (Test Set)", ["Feature", "ICC(A,1) vs. foot [95% CI]", "Spearman ρ vs. foot [95% CI]", "Within-visit ICC [95% CI]", "SEM (% of mean)", "Foot reference within-visit ICC"], [["Cadence (steps/min)", "0.93 [0.89, 0.96]", "0.96 [0.92, 0.99]", "0.93 [0.91, 0.95]", "3.0", "0.94 [0.91, 0.96]"], ["Step-time CV (%)", "0.75 [0.62, 0.84]", "0.67 [0.57, 0.75]", "0.85 [0.76, 0.90]", "25.8", "0.79 [0.70, 0.85]"], ["Step-time asymmetry (%)", "0.21 [0.02, 0.45]", "0.25 [0.09, 0.40]", "0.76 [0.59, 0.84]", "46.8", "0.85 [0.70, 0.92]"], ["Step regularity", "—", "—", "0.88 [0.81, 0.93]", "9.7", "—"], ["Stride regularity", "—", "—", "0.78 [0.66, 0.87]", "10.3", "—"], ["Vertical acc. RMS (m/s²)", "—", "—", "0.96 [0.95, 0.97]", "8.9", "—"], ["Horizontal acc. RMS (m/s²)", "—", "—", "0.96 [0.94, 0.97]", "6.7", "—"], ["Tilt-rate RMS (°/s)", "—", "—", "0.75 [0.47, 0.94]", "22.1", "—"], ["Yaw-rate RMS (°/s)", "—", "—", "0.74 [0.64, 0.82]", "22.1", "—"], ["X acc. RMS (control)", "—", "—", "0.96 [0.95, 0.97]", "8.7", "—"], ["X rate RMS (control)", "—", "—", "0.77 [0.70, 0.83]", "20.4", "—"]], [2000, 1700, 1700, 1700, 1000, 1700], "Validity: participant medians (183 participants; asymmetry 165). Within-visit: first two trials of each participant’s first visit (178–179 participants; asymmetry 136, reference asymmetry 170). Features were prespecified in headimu/features.py; participant-bootstrap CIs (2000 resamples)."]),
      ("table", ["Sensitivity of Head Features to Simulated Mounting Errors (Test Set, 930 Trials)", ["Feature", "Rotation 10°", "20°", "30°", "45°", "Lever arm 2 cm", "4 cm", "8 cm"], [["Cadence (steps/min)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.4 (0.03)", "0.5 (0.05)"], ["Step-time CV (%)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "1.9 (0.02)", "3.5 (0.04)", "6.3 (0.07)"], ["Step-time asymmetry (%)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "8.9 (0.06)", "15.6 (0.10)", "26.9 (0.17)"], ["Step regularity", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.3 (0.01)", "0.7 (0.02)", "1.3 (0.05)"], ["Stride regularity", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.2 (0.01)", "0.4 (0.02)", "0.8 (0.04)"], ["Vertical acc. RMS (m/s²)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.4 (0.01)", "0.8 (0.02)", "1.6 (0.03)"], ["Horizontal acc. RMS (m/s²)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.9 (0.03)", "1.8 (0.06)", "3.5 (0.11)"], ["Tilt-rate RMS (°/s)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)"], ["Yaw-rate RMS (°/s)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)"], ["X acc. RMS (control)", "2.0 (0.04)", "4.0 (0.09)", "6.3 (0.14)", "11.2 (0.23)", "0.4 (0.01)", "0.8 (0.02)", "1.6 (0.04)"], ["X rate RMS (control)", "2.0 (0.05)", "4.0 (0.09)", "6.2 (0.14)", "9.9 (0.23)", "0.0 (0.00)", "0.0 (0.00)", "0.0 (0.00)"]], [2000, 1050, 1050, 1050, 1050, 1100, 1050, 1040], "Median absolute relative change (%) of the trial feature across 10 random rotation axes or lever-arm directions per level; in parentheses, the same change in units of the between-participant SD. Gravity-frame features are exactly invariant to rigid rotation (change 0); angular-rate features are unaffected by lever arms on a rigid body."]),
      ("table", ["Association of Head Features With Clinician-Rated Gait (VGA) at the First Visit (Test Set)", ["Feature", "*n*", "Spearman ρ, all", "Spearman ρ, patients", "Rank partial ρ [95% CI]"], [["Cadence (steps/min)", "178", "−0.35", "−0.29 [−0.45, −0.11]", "−0.31 [−0.45, −0.16]"], ["Step-time CV (%)", "177", "0.59", "0.44 [0.28, 0.58]", "0.38 [0.25, 0.52]"], ["Step-time asymmetry (%)", "159", "0.31", "0.28", "0.18"], ["Step regularity", "178", "−0.67", "−0.48 [−0.61, −0.34]", "−0.47 [−0.57, −0.33]"], ["Stride regularity", "178", "−0.67", "−0.51", "−0.46 [−0.58, −0.32]"], ["Vertical acc. RMS (m/s²)", "178", "−0.64", "−0.55 [−0.68, −0.40]", "−0.43 [−0.55, −0.28]"], ["Horizontal acc. RMS (m/s²)", "178", "−0.04", "−0.03", "0.04"], ["Tilt-rate RMS (°/s)", "178", "−0.44", "−0.21", "−0.26 [−0.38, −0.12]"], ["Yaw-rate RMS (°/s)", "178", "−0.36", "−0.26", "−0.15"], ["Foot reference cadence", "178", "−0.37", "−0.31", "−0.34"], ["Foot reference step-time CV", "178", "0.53", "0.43 [0.27, 0.56]", "0.34 [0.18, 0.48]"], ["Foot reference asymmetry", "175", "0.27", "0.16", "0.11"]], [3000, 700, 1500, 2300, 2300], "VGA: visual gait assessment by the physician (0 none to 4 very severe); test participants by VGA 0/1/2/3: 63/42/51/22. Partial correlation adjusted for age, sensor system, and cadence (cadence itself: age and sensor). CIs where computed (participant bootstrap)."]),
      ("table", ["Discrimination of VGA ≥ 2 by Ridge-Logistic Models Fitted on Development and Evaluated on Test Participants", ["Model", "Status", "*n* dev", "*n* test", "Test AUC"], [["Age + sensor + cadence (M0)", "Prespecified", "70", "178", "0.77"], ["M0 + 8 head features (M1)", "Prespecified", "55", "159", "0.82 vs. M0 0.76; Δ 0.055 [−0.007, 0.119]"], ["Age + sensor + foot-reference cadence, CV, asymmetry", "Prespecified comparator", "69", "175", "0.84"], ["M0 + 7 head features (no asymmetry)", "Post hoc", "69", "177", "0.87 vs. M0 0.77; Δ 0.102 [0.038, 0.164]"]], [3200, 1500, 900, 900, 3940], "Standardization and coefficients from the development set only; fixed L2 penalty (λ = 1). Δ: AUC difference on participants with complete predictors for both models, participant-bootstrap 95% CI. Head features other than cadence: step-time CV, asymmetry, step and stride regularity, vertical and horizontal acceleration RMS, tilt- and yaw-rate RMS."]),
      ("table", ["Screening Coverage and Error by Clinician-Rated Gait Impairment (Test Set, Head A1)", ["VGA", "Segments", "Participants", "Excluded by SR screen (%)", "Large errors (%)", "Turn-gate time kept", "Turn sensitivity"], [["0 (none)", "666", "66", "0.0", "2.6", "0.82", "0.90"], ["1 (mild)", "440", "47", "0.0", "3.4", "0.84", "0.84"], ["2 (moderate)", "538", "56", "5.9", "13.6", "0.86", "0.80"], ["≥3 (severe)", "172", "23", "30.2", "32.0", "0.86", "0.62"]], [1700, 1200, 1300, 1700, 1500, 1500, 1540], "SR threshold 0.32 (development 10th percentile). Large error: |*e*_{C}| > 5 steps/min. Turn-gate values at 30°/s: trial means (time kept) and trial medians (sensitivity). VGA of each trial’s visit; segments without VGA omitted."]),
]
