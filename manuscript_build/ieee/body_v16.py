TITLE = ("Cadence From a Single Head-Worn IMU Across Clinical Cohorts: Head-Only Estimation, Trustworthiness, "
         "and External Validation")
AUTHORS = "Qiang Qiu, Shiqi Chen, and Zhenkun Jin"
FOOTNOTE = ("[[Manuscript received Month DD, 2026.]] This work was supported by the National Training Program of Innovation "
            "and Entrepreneurship for Undergraduates under Grant 202611654002. (Corresponding author: Zhenkun Jin.)\n\n"
            "Q. Qiu, S. Chen, and Z. Jin are with the School of Artificial Intelligence and Big Data, Wuhan "
            "University of Business, Wuhan 430056, China (e-mail: 2162385684@qq.com; 1705296766@qq.com; "
            "jinzhenkun@wbu.edu.cn).\n\n"
            "This work involved human subjects only through secondary analysis of two public, de-identified datasets, so "
            "separate ethics approval was not required. The Voisard study was approved by the Comité de Protection des "
            "Personnes Île-de-France II (CPP 2014-10-04 RNI); the ethics approval of the DUO-GAIT study is reported in its "
            "data descriptor.")

ABSTRACT = (
 "Head-worn inertial sensors, as in smart glasses, could bring gait monitoring into everyday devices. However, their "
 "accuracy in impaired gait, reliance on reference-assisted segmentation, and output trustworthiness and "
 "generalizability are unclear. Using a public dataset of 260 participants in eight clinical cohorts, we evaluated "
 "cadence from a single forehead inertial measurement unit. The reference was foot-sensor heel strikes in 183 held-out "
 "participants. With reference-assisted segmentation, median absolute error was 1.53 steps/min (1.5%), "
 "equivalent to a lower-back sensor. Large errors arose mainly in slow, irregular gait (35% of stroke "
 "segments). A head-only pipeline that detected walking, turns, and steps itself was equivalent offline (1.56 "
 "steps/min; mean paired difference 0.05) but had 1.6% missing outputs. A causal version showed a 2.2 steps/min bias, "
 "0.35-s step confirmation, and a 2.6-s start-up delay. Gravity-frame features were invariant to mounting rotation and "
 "robust to lever arms, noise, and moderate gyroscope bias, but errors grew below 50 Hz. A step-regularity screen discriminated "
 "large errors (area under the receiver operating characteristic curve 0.90). Adding estimator disagreement and "
 "interval variability raised this area to 0.92 and excluded fewer segments of severely impaired walkers (22% vs. "
 "30%). Yet it did not lower the residual error at matched coverage. We applied the pipeline unchanged to an "
 "independent dataset of 16 healthy adults with a different head sensor, protocol, and sampling rate. It reached 0.70 "
 "steps/min (limits of agreement −2.5 to 1.9) with no missing outputs. These results delimit when single-head-sensor "
 "cadence can be trusted and what screening costs.")
INDEX = ("Cadence, data quality, external validation, gait analysis, head-worn sensor, inertial measurement unit (IMU), "
         "smart glasses, wearable sensors.")

B = []
def h1(t): B.append(("h1", t))
def h2(t): B.append(("h2", t))
def p(t): B.append(("p", t))
def eq(name): B.append(("eq", name))
def fig(path, caption, width=3.45): B.append(("fig", (path, caption, width)))
def table(caption, head, rows, widths, note=None): B.append(("table", (caption, head, rows, widths, note)))

# =============================================================================== I
h1("Introduction")
p(
  "Wearable inertial measurement units (IMUs) bring instrumented gait analysis outside the laboratory, but their "
  "validity depends on sensor location, processing, and reference ⟦hulleck,yin,prisco⟧. The head is attractive because "
  "eyeglasses, ear-worn devices, and head-mounted displays can host an IMU without an extra wearable. Head-worn IMUs "
  "have supported real-time gait analysis ⟦hwang⟧, heel-strike detection ⟦tomc⟧, and symmetry assessment ⟦hwang2021⟧. "
  "In a four-site deep-learning comparison, a head IMU gave the highest heel-strike F1 in young and older adults ⟦kim⟧. "
  "Smart glasses, ear-worn, and temple-worn IMUs have been applied to healthy adults, older adults, and people with "
  "Parkinson’s disease ⟦hellec2022,hellec,vandoorn,fawden,seifer,jarchi,tasca⟧. As Table I shows, most studies used one "
  "device, one protocol, and small, mostly healthy samples.")
table("Head-Region IMU Gait Studies Compared With This Work",
      ["Study", "Site", "Population (*n*)", "Reference", "Turns / head motion", "Mounting / re-wear"],
      [["Hwang ⟦hwang2021⟧", "Occiput", "Healthy (12)", "Foot IMU, MVN", "—", "—"],
       ["Hellec ⟦hellec2022⟧", "Temple", "Healthy (20)", "Mocap", "—", "1-wk retest"],
       ["Tomc ⟦tomc⟧", "Forehead", "Healthy (7)", "Instr. treadmill", "—", "—"],
       ["Seifer ⟦seifer⟧", "Ear", "Healthy (48)", "Mocap", "—", "—"],
       ["Fawden ⟦fawden⟧", "Behind ear", "Mixed (68)^{a}", "Mocap", "Head turns, turns", "—"],
       ["Tasca ⟦tasca⟧", "Temple", "Healthy (15)", "Multi-sensor", "Head ROM only", "—"],
       ["This work", "Forehead + head^{b}", "8 cohorts (260) + healthy (16)", "Foot IMU", "180° turns", "Simulated; re-wear"]],
      [820, 740, 1000, 760, 840, 880],
      "Mocap: optical motion capture; MVN: full-body IMU system; ROM: range of motion. ^{a}Includes 18 participants with "
      "Parkinson’s disease, vestibular, or other disorders. ^{b}External dataset ⟦duogait⟧.")
p(
  "Four questions remain open. *Clinical heterogeneity:* how large is the cadence error of a single head IMU across "
  "diseases with abnormal gait? Does it fail by halving, by missed steps, or through irregular gait that defeats any "
  "single sensor, and how does it compare with the lower back on the same trials ⟦kuderle⟧? *Segmentation:* evaluations "
  "often take walking bouts and turns from a reference, which favors the device. A deployable system must find them "
  "itself, possibly in real time ⟦tomc⟧. *Robustness:* rule-based detectors depend on a fixed sensor location and "
  "orientation ⟦lin⟧. Orientation-invariant features remove rigid rotations in principle ⟦zijlstra,moe⟧. A displacement "
  "from the nominal site, however, adds tangential and centripetal accelerations, and sensor position alone changes "
  "simulated gait-event errors ⟦uhlenberg⟧. *Trustworthiness and generalization:* curved walking, turns, and irregular "
  "gait degrade step detection ⟦lin,hou,fawden⟧. Monitoring must therefore flag untrustworthy data, at a cost reported "
  "by population, and results from one dataset must be tested on another.")
p(
  "The public dataset of Voisard *et al.* makes these questions testable in eight cohorts with head, lower-back, and "
  "foot IMUs and clinician gait ratings ⟦voisard_sd,voisard_fig,voisard_jner,salarian⟧. The independent DUO-GAIT "
  "dataset adds a different head IMU, protocol, and sampling rate ⟦duogait,duogait_data⟧. Published uses of the Voisard "
  "head sensor are limited to multisensor classification and dataset auditing ⟦sadegh,wu2026,ye2026⟧. Our contributions "
  "are fourfold: 1) *cross-cohort accuracy with and without reference-assisted segmentation*, from offline and causal "
  "head-only pipelines, with failure modes and latency; 2) *robustness boundaries* for mounting errors and sensor "
  "non-idealities, stated as operating conditions; 3) a *trustworthiness assessment* of a turn gate, a step-regularity "
  "screen, and a multi-feature error-risk model, judged by gain over coverage-matched random removal, calibration, and "
  "exclusion cost by clinician-rated impairment; and 4) a *frozen external validation* on DUO-GAIT.")

# =============================================================================== II
h1("Datasets and Reference")
p(
  "*Voisard dataset.* This secondary analysis of public, de-identified data ⟦voisard_sd,voisard_fig⟧ comprises "
  "recordings from January 2014 to March 2016 in Paris public and military hospitals: healthy subjects (HS, *n* = 73); "
  "hip and knee osteoarthritis (HOA, 15; KOA, 18) and anterior cruciate ligament injury (ACL, 11); and stroke (CVA, "
  "49), Parkinson’s disease (PD, 24), chemotherapy-induced peripheral neuropathy (CIPN, 19), and radiation-induced "
  "leukoencephalopathy (RIL, 51) (⟪T:cohort⟫). At each visit, a physician rated gait deterioration visually (VGA: 0, "
  "none, to 4, very severe). IMUs were strapped to the forehead (HE), the lower back (LB), and each foot (Fig. 1(a)). "
  "Each visit used XSens MTw Awinda (569 trials) or Technoconcept I4 Motion (787 trials) at 100 Hz. Participants walked "
  "6–10 m, turned 180°, and walked back. Heel strikes came from the providers’ foot-IMU algorithm, validated against an "
  "instrumented walkway (F1 100% and 8-ms median error in healthy subjects; 96.3% and 26 ms in post-stroke equinovarus "
  "foot) ⟦voisard_jner⟧. Turn boundaries came from the lower-back IMU ⟦salarian⟧. Inputs were the providers’ processed "
  "accelerations including gravity and offset-corrected angular rates ⟦voisard_sd⟧. Axes were harmonized so that X is "
  "craniocaudal, signals were low-passed at 14 Hz (eighth order), and gaps <1.5 s were interpolated; raw packet "
  "counters marked gaps >0.05 s invalid.")
fig("fig_schematics/fig1_sensors_frames_leverarm_v17.png",
    "Sensors and mounting errors. (a) Sensor sites; X is the harmonized craniocaudal axis. (b) A rotation **R**(*θ*, **u**) "
    "tilts X to X′ by *φ* = arccos *R*_{11}; **r** offsets the sensor to a simulated temple site. (c) Lever-arm terms of (5).", 3.1)
p(
  "*DUO-GAIT (external).* Sixteen healthy adults (21–35 years) wore nine Physilog 5 IMUs (128 Hz, ±16 *g*, ±1000°/s), "
  "including one on the head ⟦duogait,duogait_data⟧. They walked for 6 min in a 35-m hallway under single- and "
  "dual-task conditions, before and after a fatiguing protocol (64 walks). The reference is the providers’ per-stride "
  "foot-IMU initial contacts (stride-time root-mean-square error 0.02 s against two reference systems ⟦duogait⟧), with "
  "turning and interruption flags. Reference straight passes are intervals in which both feet have strides that are "
  "neither turning nor interrupted. Head files were complete (no gaps or saturation; ⟪T:ext_audit⟫). Both references "
  "are independent of the head signal.")

# =============================================================================== III
h1("Methods")
h2("Orientation-Invariant Signals")
p("Let **a**_{s}(*t*) and **ω**_{s}(*t*) be the specific force and angular rate in the sensor frame. The norm is invariant to "
  "rotations of the sensor frame:")
eq("eq1")
p("A 0.3-Hz low-pass of **a**_{s} approximates the gravity direction, and the angular rate about it approximates the turning rate:")
eq("eq2")
p("The projection onto gravity gives the vertical acceleration of trunk accelerometry ⟦zijlstra,moe⟧:")
eq("eq3")
h2("Reference-Assisted Estimation (B0)")
p(
  "The primary analysis (B0) evaluates rhythm given reference segmentation. Each trial has two straight segments, from "
  "the first heel strike to turn onset and from turn end to the last heel strike. Steps are peaks of the step-band "
  "signal (0.6–3.0 Hz, third-order zero-phase Butterworth) with prominence ≥ max(0.12 m/s², 1.5*σ̂*) and spacing ≥0.30 "
  "s. They are taken from the fixed X axis (*A0*), the vertical acceleration (3) (*A0g*), or the norm (1) (*A1*). The "
  "autocorrelation estimator (*AC*) takes the first autocorrelation peak reaching 60% of the maximum within 0.30–0.90 s "
  "⟦moe⟧. The same detectors were applied to the lower-back IMU as a positional comparator (pipeline: ⟪F:pipeline⟫).")
h2("Head-Only End-to-End Estimation (B1, B2)")
p(
  "*B1 (offline)* uses only the head IMU. Walking is a centered 2-s root mean square (RMS) of the step-band "
  "acceleration norm above a threshold (gaps <1 s filled, bouts ≥3 s). Turns are runs of the turning gate (*q* > "
  "*q*^{*} = 30°/s, median 0.15 s, ≥0.30 s, padded 0.20 s, merged within 0.5 s) whose integrated rotation reaches 90°. "
  "Straight segments are bouts minus turns (≥2 s), and steps are A1 peaks within bouts. Cadence per segment is 60 over "
  "the median interval (≥3 intervals); otherwise there is no output. *B2 (causal)* replaces each filter with its causal "
  "counterpart, initialized on the first sample. It uses a trailing RMS with hysteresis (off at 0.7 × on; holds 0.5 and "
  "1.0 s) and a trailing gate median, and it confirms a peak 0.20 s after it occurs. At each confirmed step, it emits a "
  "running cadence: 60 over the median of the last six intervals within the current straight bout. Each reference "
  "segment was assigned the B1 segment with the largest overlap (≥1 s) and the median of the B2 outputs emitted within "
  "it; segments without output were failures.")
h2("Trustworthiness Criteria")
p(
  "*Turn gate (A2)* removes A1 candidates inside gated intervals; its control *A2-R* circularly shifts the mask at "
  "equal coverage (200 repetitions). *Step regularity (SR)* is the unbiased autocorrelation of the head norm at the "
  "step lag, taken as the median over a trial’s segments. It flagged trials below the development 10th percentile "
  "(0.32) ⟦moe⟧ (Q1). *Error-risk models (Q2)* used ten physically meaningful segment features: SR, stride regularity, "
  "step-interval coefficient of variation (CV), peak–autocorrelation cadence disagreement, spectral prominence and "
  "entropy, peak-amplitude CV, step-time coverage, angular-rate RMS, and duration. Ridge-logistic models (fixed "
  "penalty; standardization and fit on development segments) used SR only, SR plus disagreement and interval CV "
  "(*SR+2*), or all ten features. Each was thresholded at the development flag rate of Q1.")
h2("Mounting and Sensor Simulations")
p("Rigid rotations were applied to every test trial,")
eq("eq4")
p("with *θ* ∈ {5°, 10°, 20°, 30°, 45°} and 50 random axes **u**; A0g and A1 are exactly invariant, so this quantifies A0 "
  "⟦guimaraes⟧. Lever arms model a sensor displaced from the strap site, e.g., at a temple (Fig. 1(c)):")
eq("eq5")
p(
  "where **α**_{s} is the derivative of the 10-Hz low-passed **ω**_{s} and |**r**| ∈ {2, 4, 6, 8} cm. Sensor "
  "non-idealities were accelerometer white noise of 0.05–0.2 m/s² RMS per axis and constant gyroscope biases of "
  "1–10°/s; the median resting offset of the Technoconcept recordings was 7°/s (⟪T:qc⟫). We also simulated a slow "
  "0°–20° orientation drift over the trial and downsampling to 50 and 25 Hz.")
h2("Parameter Selection, External Application, and Analysis Status")
p(
  "Participants were split into development (≈30%) and test (≈70%) sets, stratified by cohort × sensor system with a "
  "fixed seed. The development set selected the band cutoff, lags, *q*^{*}, the SR threshold, the B1/B2 walking "
  "thresholds, and the Q2 coefficients; all else was fixed beforehand (⟪T:params⟫). The B1/B2 and Q2 analyses were "
  "designed after the primary test results were known and are labeled *exploratory*. One *post hoc* variant, *B2-t*, "
  "re-selected the causal detector parameters on development data after the first evaluation showed excess detections "
  "(⟪T:tuning⟫). Post hoc analyses (offset calibration, equivalence, error thresholds, a published detector, "
  "computational cost, clinical scale) are in ⟪T:post⟫. For DUO-GAIT, every parameter was frozen. Adaptation was "
  "limited to unit conversion and polyphase resampling from 128 to 100 Hz; axis conventions are irrelevant to the "
  "invariant features.")

# =============================================================================== IV
h1("Outcomes and Statistics")
p("For each straight segment, the medians of IMU and reference intervals give the cadence error:")
eq("eq6")
p(
  "Outcomes were the median absolute and relative error, the Bland–Altman bias with 95% limits of agreement (LoA) "
  "⟦bland1986,nassajpour⟧ corrected for repeated measurements ⟦bland2007⟧, the 90th percentile of |*e*_{C}|, large "
  "errors (|*e*_{C}| > 5 steps/min), no-output rates (counted, never dropped), and halving. Detection outcomes were "
  "event F1 (matching within 0.15 s), walking-detection sample F1, turn detection, and causal latencies. Trust criteria "
  "were assessed by gain over coverage-matched random removal, error–coverage curves, the areas under the receiver "
  "operating characteristic and precision–recall curves (AUROC, AUPRC), the Brier score, and reliability. Retention, "
  "false exclusion (flagged segments without a large error), and detection were compared by cohort and VGA. The "
  "participant was the unit of analysis: 95% confidence intervals (CIs) came from 2000 participant-level bootstrap "
  "resamples, and paired comparisons used Wilcoxon signed-rank tests with Holm correction ⟦holm⟧. Cross-visit agreement "
  "used the intraclass correlation coefficient ICC(A,1) ⟦mcgraw,koo⟧. A non-significant difference is not interpreted "
  "as equivalence. Equivalence was tested post hoc (two one-sided tests, margin ±1.8 steps/min, one sample of cadence "
  "resolution).")

# =============================================================================== V
h1("Results")
h2("Inclusion")
p("One visit of RIL_12 (five trials) lacked a head signal, leaving 1351 trials of 260 participants: 421 trials of 77 "
  "participants for development and 930 trials of 183 participants for testing (⟪F:inclusion⟫). No saturation was found; "
  "the median fraction of standing gravity on the head X axis was 0.968 (providers: 93 ± 8% ⟦voisard_sd⟧) and the head turn "
  "angle over the reference turn 177° (⟪T:qc⟫, ⟪F:qc⟫). Recomputing B0 from the packed head signals reproduced all 7440 test "
  "values of the primary analysis (maximum difference 5 × 10⁻⁶ steps/min).")
h2("Cross-Cohort Accuracy and Failure Modes (B0)")
p(
  "For head A1, the median absolute cadence error was 1.53 steps/min (95% CI 1.31–1.71), the relative error 1.50%, and "
  "the bias −0.45 steps/min with LoA −11.5 to 10.6 (Table II, Fig. 2). A0g and A0 performed alike (Holm-adjusted *p* = "
  "1.00); AC had the smallest median error (1.02) but wider LoA; the lower back reached 1.36 steps/min, equivalent to "
  "the head (mean paired difference −0.04; 90% CI −0.36 to 0.28). Run untuned on the same segments, the open-source "
  "EarGait detector ⟦seifer⟧ had a lower median error (1.13; −0.40, 95% CI −0.52 to −0.20) but doubled cadence in 4.9% "
  "of segments, mainly in impaired gait (LoA −34 to 44; ⟪T:post⟫). Head A1 events reached an F1 of 0.936 with a 31.4-ms "
  "timing error (⟪F:example⟫, ⟪T:events⟫). Error was lowest in HS (1.11) and highest in CVA (2.58), with the same "
  "ordering at the lower back (⟪T:strata⟫, ⟪F:cohorts⟫).")
table("Straight-Walking Cadence Agreement With Reference-Assisted Segmentation (Test Set, 183 Participants, 1860 Segments)",
      ["Method", "|*e*_{C}|, median [95% CI]", "Rel. error (%)", "Bias", "95% LoA", "Halv./doubl. (%)"],
      [["HE-A0", "1.54 [1.41, 1.67]", "1.55", "−0.27", "−11.8, 11.3", "0.2 / 0.1"],
       ["HE-A0g", "1.51 [1.34, 1.65]", "1.50", "−0.32", "−10.8, 10.1", "0.1 / 0.1"],
       ["HE-A1", "1.53 [1.31, 1.71]", "1.50", "−0.45", "−11.5, 10.6", "0.3 / 0.1"],
       ["HE-AC", "1.02 [0.88, 1.09]", "0.97", "0.72", "−12.9, 14.3", "0.1 / 0.3"],
       ["LB-A0g", "1.35 [1.24, 1.47]", "1.34", "0.21", "−10.8, 11.2", "0.1 / 0.2"],
       ["LB-A1", "1.36 [1.21, 1.54]", "1.36", "0.10", "−10.2, 10.4", "0.1 / 0.1"],
       ["LB-AC", "0.92 [0.85, 1.01]", "0.89", "0.97", "−13.8, 15.8", "0.0 / 0.4"]],
      [720, 1300, 700, 620, 1000, 700],
      "Steps/min except percentages; LoA for repeated measurements ⟦bland2007⟧. HE: head; LB: lower back.")
fig("fig_results/fig5_bland_altman.png",
    "Bland–Altman plots of cadence (B0) for (a) head A1, (b) head A0g, (c) head AC, and (d) lower-back A1. Dots: straight "
    "segments colored by cohort; solid line: bias; dashed lines and band: 95% LoA for repeated measurements.")
p(
  "Four failure modes were distinguished. *Quantization:* 25.8% of segments had zero error; one sample corresponds to "
  "about 1.8 steps/min at the median step time. *Halving or doubling* stayed ≤1.2% in every cohort. *Irregular gait:* "
  "errors >5 steps/min affected 9.1% of segments (CVA 35.2%, RIL 13.5%, PD 10.4%, HS 0.8%). They were mostly shared "
  "with the lower back (97 both, 72 head only, 70 lower back only) and were not halving (median ratio 1.06). They came "
  "from slow walking with low SR (0.43 vs. 0.92). Without them, the segment-level LoA narrowed to −3.6 to 3.6 "
  "steps/min. *Missed steps during turns* affected both locations (⟪F:example⟫). Beyond cadence, head step-time "
  "variability agreed moderately with the reference (ICC 0.75), but step asymmetry did not (0.22) (validity, mounting "
  "sensitivity, association with VGA, and VGA discrimination: ⟪T:feat_valid⟫, ⟪T:feat_mount⟫, ⟪T:feat_vga⟫, "
  "⟪T:feat_model⟫).")
h2("Head-Only End-to-End Estimation")
p(
  "B1 found walking with a median F1 of 0.95 (recall 1.00). It detected turns with recall 0.99 and precision 0.80 "
  "(boundary error 0.27 s). Its median error was close to that of B0: 1.56 steps/min (95% CI 1.44–1.72), with LoA −12.3 "
  "to 11.3. It was equivalent to B0 (mean paired difference 0.05; 90% CI −0.04 to 0.13). However, 1.6% of segments had "
  "no output, and large-or-missing segments rose from 9.1% to 10.9% (Table III, Fig. 3). Turn detection was weakest in "
  "CVA (F1 0.75). Half of the missing outputs (15 of 30 segments) came from recordings whose angular rate at rest "
  "exceeded the gate threshold. Such a resting rate >30°/s occurred in 17 of 930 test trials (11 HS); 8 of them (47%) "
  "lost an output, versus 1.2% of the others. Without them, the HS no-output rate fell from 4.0% to 2.0% "
  "(⟪T:e2e_cohort⟫, ⟪T:e2e_detect⟫). Post hoc, removing the offset measured over a known still period cut B1 no-output "
  "to 0.5% (−1.1 pp, 95% CI −2.3 to −0.1); an offset estimated from the head signal did not help (⟪T:post⟫).")
p(
  "The prespecified causal pipeline B2 was less accurate (1.62 steps/min; +0.14 vs. B1, 95% CI 0.04–0.32, Holm *p* = "
  "0.006) and was not equivalent to it. It had a positive bias (2.2 steps/min) and wide LoA (−15.0 to 19.4). Its "
  "detector produced 11% more peaks than heel strikes (precision 0.77), worst in KOA (21.6% large errors) and CVA "
  "(42.0%). Its turn onsets were declared 0.58 s after the reference with precision 0.39, as the causal gate lacks the "
  "90° criterion. Steps were confirmed 0.35 s after the heel strike, and the first cadence was output 2.6 s after "
  "walking onset (Fig. 3(b)). The post hoc variant B2-t (longer confirmation, 0.30 s) reduced the bias to 0.75 "
  "steps/min and the median error to 1.55 (+0.04 vs. B1, Holm *p* = 0.22), at 0.46-s confirmation latency. A "
  "sample-by-sample B2 reproduced all 27 428 test outputs with about 30 000 operations per second of data and 2.4 kB of "
  "state (⟪T:post⟫).")
table("Reference-Assisted (B0) Versus Head-Only Offline (B1) and Causal (B2, B2-t) Estimation, Test Set",
      ["Metric", "B0", "B1", "B2", "B2-t^{a}"],
      [["|*e*_{C}|, median [95% CI]", "1.53 [1.37, 1.64]", "1.56 [1.44, 1.72]", "1.62 [1.51, 1.70]", "1.55 [1.45, 1.64]"],
       ["Bias (95% LoA)", "−0.45 (−11.5, 10.6)", "−0.48 (−12.3, 11.3)", "2.20 (−15.0, 19.4)", "0.75 (−12.6, 14.1)"],
       ["90th pct. of |*e*_{C}|", "4.6", "4.8", "6.1", "4.8"],
       ["No output (%)", "0", "1.6", "1.5", "1.7"],
       ["|*e*_{C}| > 5 or no output (%)", "9.1", "10.9", "13.6", "11.0"],
       ["   CVA / HS (%)", "35.2 / 0.8", "33.3 / 4.9", "42.0 / 5.3", "32.1 / 5.9"],
       ["Walking F1; turn P / R", "reference", "0.95; 0.80 / 0.99", "0.96; 0.39 / 1.00", "as B2"],
       ["Step F1 (full walk)", "—", "0.91", "0.86", "0.87"],
       ["Step confirmation; first output (s)", "offline", "offline", "0.35; 2.6", "0.46; 2.7"]],
      [1600, 860, 860, 860, 860],
      "Steps/min unless stated; 183 participants, 1860 reference segments; failures counted. CIs from the V16 bootstrap. "
      "^{a}Post hoc: causal detector re-selected on development data after the first test evaluation.")
fig("fig_v16/fig10_endtoend.png",
    "Head-only end-to-end estimation (test set). (a) Segments with |*e*_{C}| > 5 steps/min (solid) or without output (hatched) "
    "by cohort for reference-assisted B0, head-only offline B1, and head-only causal B2. (b) Latencies of the causal pipeline "
    "relative to the reference heel strike, walking onset, and turn onset (box: IQR; whiskers: 1.5 IQR).", 3.45)
h2("Mounting and Sensor Robustness")
p(
  "A0 error was stable up to 10° of tilt (1.54–1.59 steps/min), rose by 14% at 10°–20°, and reached 3.45 (×2.2) at "
  "30°–45°. Halving rose from 0.3% to 8.2% (Fig. 4(a); ⟪T:sims⟫). A0g and A1 were exactly invariant, also under a "
  "0°–20° drift. Lever arms of 2–8 cm left A0g and A1 at 1.44–1.49 steps/min (Fig. 4(b)). Accelerometer noise up to 0.2 "
  "m/s² did not increase the A1 error (1.37–1.49 vs. 1.53 steps/min). Gyroscope bias up to 10°/s left cadence unchanged "
  "and turn detection at ≥0.98. Downsampling raised the A1 large-error share from 9.1% to 9.6% at 50 Hz and to 14.0% at "
  "25 Hz (⟪T:sens⟫). Cross-visit ICC(A,1) was 0.68 (95% CI 0.50–0.83) for head A1 and 0.67 (0.47–0.82) for the foot "
  "reference (⟪F:rewear⟫, ⟪T:rewear⟫). Table IV condenses these boundaries.")
fig("fig_results/fig7_simulations.png",
    "Mounting simulations. (a) A0 cadence error versus X-axis tilt (median and 95% CI; bars: halved segments, right axis); blue line: "
    "A0g and A1, invariant to rotation. (b) A0g and A1 versus lever-arm offset (median and 95% CI; 20 directions per offset).")
table("Operating Conditions of Head-IMU Cadence Estimation (Simulation and Observed Failures)",
      ["Factor", "Effect in this study", "Recommendation"],
      [["Tilt with a fixed axis (A0)", "Stable to ≈10°; +14% error at 10°–20°; ×2.2 and 8% halving at 30°–45°", "Use A0g or A1"],
       ["Rotation, slow drift (A0g, A1)", "Exactly invariant; 0°–20° drift without effect", "Default for eyewear"],
       ["Lever arm 2–8 cm", "No effect in straight walking; ≈3 m/s² centripetal term at 360°/s, 8 cm", "No step events within turns"],
       ["Accelerometer noise ≤0.2 m/s²", "No increase in error", "Consumer MEMS adequate"],
       ["Gyroscope bias", "≤10°/s: no effect; apparent resting rate >30°/s: 47% of trials without output",
        "Calibrate over a known still period"],
       ["Sampling rate", "50 Hz: +0.5 pp large errors; 25 Hz: +4.9 pp", "≥50 Hz"],
       ["AC estimator", "Lowest median error; widest LoA; ≥1.8 s per segment", "Segment summaries only"]],
      [1380, 2160, 1500],
      "Simulations exclude strap tension, slippage, frame coupling, and active head turns.")
h2("Trustworthiness")
p("*Turn gate.* At 30°/s, A2 kept 84.5% of walking time and recovered 6.5 percentage points (pp) more reference steps than "
  "coverage-matched random removal (95% CI 6.0–6.9; precision +0.6 pp) (Fig. 5(a); ⟪F:gating⟫, ⟪T:gating⟫); turn sensitivity "
  "was 0.82 overall but 0.62 at VGA ≥3.")
p(
  "*Step regularity and error-risk models.* SR discriminated large errors with an AUROC of 0.90 (95% CI 0.84–0.94; "
  "AUPRC 0.63). Keeping 95.5% of segments, it lowered their share from 9.0% to 5.6% (⟪T:sr⟫). Adding disagreement and "
  "interval CV (SR+2) raised the AUROC to 0.92 (0.88–0.94; +0.021, 95% CI 0.002–0.047). The full model did not (0.91; "
  "+0.014, −0.004 to 0.038). At matched coverage, the residual large-error share did not differ detectably between "
  "models (95.5%: 5.6%–5.9%; 90%: 3.5%–3.6%; differences ≤0.2 pp, 95% CIs within ±0.7 pp) (Fig. 5(b)). The development "
  "base rate (18%) was twice the test rate (9.1%), yet reliability was acceptable (Brier 0.050 vs. 0.091 for the base "
  "rate; calibration slope 1.12) (Fig. 5(c); ⟪T:q2⟫). The criteria differed in whom they excluded (Fig. 5(d); "
  "⟪T:q2_groups⟫). At VGA ≥3 (174 segments, 23 participants), SR excluded 29.9% of segments and falsely excluded 8.5% "
  "of those without a large error. SR+2 excluded 22.4% (retained +7.5 pp, 95% CI 1.4–14.9) and falsely excluded 5.1% "
  "(−3.4 pp, −11.3 to 0.0), but with lower sensitivity (0.58 vs. 0.74). These findings held with large errors defined "
  "at 3 or 10 steps/min (SR AUROC 0.79 and 0.96; ⟪T:post⟫). Table V summarizes the criteria.")
fig("fig_v16/fig11_trust.png",
    "Trustworthiness versus coverage-matched random removal (test set). (a) Turn gate: recall gain of A2 over A2-R versus "
    "fraction of time kept (shading: 95% CI). (b) Error–coverage curves of the step-regularity screen (Q1), SR+2, and the full "
    "model; oracle removes large errors first. (c) Reliability of development-fitted risks (deciles). (d) Excluded and falsely "
    "excluded segments by clinician-rated VGA for Q1 and SR+2 at the development-matched flag rate.", 3.45)
table("Trustworthiness Criteria: Gain, Discrimination, and Exclusion Cost",
      ["Criterion", "Kept", "Discrimination", "Gain over random", "Cost at VGA ≥ 3"],
      [["Turn gate (*q*^{*} = 30°/s)", "84.5% of time", "Turn sens. 0.82; false marks 0.046", "Recall +6.5 pp (6.0, 6.9)",
        "Turn sens. 0.62"],
       ["SR ≥ 0.32 (Q1)", "95.5% of segments", "AUROC 0.90 (0.84, 0.94); sens. 0.40", "Large errors −3.4 pp (−6.1, −1.3)",
        "29.9% excluded; 8.5% falsely"],
       ["SR+2 model (Q2)^{a}", "95.8% of segments", "AUROC 0.92 (0.88, 0.94); sens. 0.38", "None beyond Q1 at matched coverage",
        "22.4% excluded; 5.1% falsely; sens. 0.58"]],
      [900, 860, 1160, 1100, 1020],
      "pp: percentage points; sens.: sensitivity for |*e*_{C}| > 5 steps/min. ^{a}Exploratory; fitted on development segments.")
h2("External Validation (DUO-GAIT)")
p(
  "Applied unchanged to 797 straight passes (median 22 s, cadence 107 steps/min) of 64 walks, B1 detected walking with "
  "an F1 of 0.99. It detected turns with precision 0.93 and recall 0.95, and steps with F1 0.98. The median cadence "
  "error was 0.70 steps/min (95% CI 0.64–0.78), with LoA −2.5 to 1.9 and no missing output (Table VI; ⟪F:ext_ba⟫). B1 "
  "was again equivalent to B0. Errors did not differ between single/dual-task and control/fatigue conditions (Friedman "
  "*p* = 0.34; ⟪T:ext_cond⟫). With only one large error, discrimination of the trust criteria could not be tested; SR "
  "and SR+2 flagged 0% and 0.4% of passes (median SR 0.98).")
table("Frozen External Validation on DUO-GAIT (16 Participants, 64 Walks, 797 Passes)",
      ["Metric", "B0 (ref.-assisted)", "B1 (head-only)", "B2 (causal)"],
      [["|*e*_{C}|, median [95% CI]", "0.62 [0.48, 0.76]", "0.70 [0.64, 0.78]", "0.48 [0.46, 0.54]"],
       ["Relative error (%)", "0.59", "0.67", "0.45"],
       ["Bias (95% LoA)", "−0.01 (−2.2, 2.2)", "−0.27 (−2.5, 1.9)", "−0.06 (−1.8, 1.7)"],
       ["90th pct. of |*e*_{C}|; |*e*_{C}| > 5 (%)", "1.8; 0.1", "1.8; 0.4", "1.4; 0"],
       ["No output (%)", "0", "0", "0"],
       ["Step F1; turn F1", "—", "0.98; 0.94", "0.98; —"]],
      [1700, 1110, 1110, 1120],
      "Steps/min unless stated. No parameter was fitted on DUO-GAIT; adaptation: units and 128 → 100 Hz resampling.")

# =============================================================================== VI
h1("Discussion")
h2("Accuracy With and Without Reference Segmentation")
p(
  "Across eight cohorts, forehead-IMU cadence agreed with an independent foot-IMU reference to about 1.5%. The "
  "1.5-steps/min median error is a tenth of the smallest detectable cadence change in Parkinson's disease (15 "
  "steps/min) ⟦lang⟧ and of our cross-visit MDC95 (17); errors above 15 steps/min occurred in 2.6% of segments (CVA "
  "13%). It was equivalent to the lower back within one sample of cadence resolution. For context, Mobilise-D reported "
  "relative cadence errors of up to about 8.5% for lower-back algorithms in real-world data ⟦mico⟧. EarGait reached "
  "stride-time errors of about 12 ms ⟦seifer⟧, and a temple-worn IMU a heel-strike F1 of about 93% in daily life "
  "⟦tasca⟧; settings differ. EarGait's detector traded higher typical accuracy for cadence doubling in impaired gait. "
  "The head-only offline pipeline was equivalent to the reference-assisted one, so median accuracy does not hinge on "
  "reference segmentation. Its added failures came from uncalibrated gyroscope offsets and from turn detection in slow "
  "walkers. Calibration over a known still period removed most of these, but an offset estimated from walking data did "
  "not, so devices need an explicit still phase. Real-time operation is the larger cost. Without look-ahead, the "
  "detector over-counted peaks in irregular gait. Steps were confirmed 0.35–0.46 s late. Large errors with any pipeline "
  "arose in slow, irregular walking, which defeated the lower back equally. Step asymmetry cannot be estimated from one "
  "head IMU without step laterality ⟦seifer⟧.")
h2("Robustness Boundaries")
p(
  "Gravity-frame and norm features make the cadence estimate independent of how the head sensor is rotated. This "
  "allowed the pipeline to transfer to a different device without axis mapping. A fixed axis is acceptable only within "
  "about 10°–20° of tilt. Lever arms matter only within turns, where an 8-cm offset at 360°/s adds about 3 m/s². "
  "Sampling should stay at or above 50 Hz (Table IV). These are simulation results on a forehead strap; frame loosening "
  "and slippage need wearing tests.")
h2("Trustworthiness: Gain, Calibration, and Cost")
p(
  "All criteria beat random removal, but they differ in what they cost and whom they exclude (Table V). SR measures "
  "gait regularity. It therefore cannot separate an unreliable signal from impaired gait, and it excluded nearly a "
  "third of the most impaired walkers’ segments. Adding two signs of estimator failure (estimator disagreement, "
  "interval variability) improved discrimination slightly and excluded fewer impaired walkers, but caught fewer of "
  "their large errors and did not lower residual error at matched coverage. Multi-feature screening thus shifts the "
  "trade-off between retaining impaired walkers and removing errors; it does not escape it. Screened results should "
  "report coverage by population, and risk scores are better shown as confidence than used for silent exclusion. "
  "Probabilities fitted on one population need recalibration when the error base rate changes.")
h2("Generalization")
p(
  "On DUO-GAIT, the frozen head-only pipeline kept errors below 1 step/min across task and fatigue conditions. The "
  "device, sampling rate, and protocol differed, and straight passes were longer. This supports transfer across devices "
  "and protocols in healthy adults, but it is not a clinical validation. Trust-criterion transfer remains untested. The "
  "smaller errors than in Voisard likely reflect longer passes, regular gait, and young participants, which are "
  "confounded.")
h2("Limitations")
p(
  "Both references are validated foot-IMU algorithms, not motion capture. The Voisard sensor was strapped to the "
  "forehead. Walks were 6–10 m, turns were whole-body turns, and active head turns were absent ⟦fawden,tasca⟧. The "
  "end-to-end and risk-model analyses were designed after the primary results were known and are exploratory. B2-t and "
  "the analyses in ⟪T:post⟫ are post hoc. VGA is a single subjective rating. Cross-visit ICCs mix re-donning with "
  "clinical change. We will next record a temple-integrated IMU with foot IMUs and video, including re-donning, head "
  "turns, and free-living use.")

# =============================================================================== VII
h1("Conclusion")
p(
  "A single forehead IMU estimated cadence across eight clinical cohorts with a median error of about 1.5 steps/min. A "
  "head-only offline pipeline was equivalent without reference segmentation (1.56 steps/min, 1.6% missing outputs). "
  "Real-time operation added bias and a 0.35–0.46-s confirmation delay. Gravity-frame features were invariant to "
  "mounting rotation and robust to lever arms, noise, and moderate gyroscope bias. Sampling below 50 Hz and large "
  "uncalibrated gyroscope offsets degraded results. Step-regularity and multi-feature screens identified untrustworthy "
  "data better than random removal. They did so at the cost of excluding the most impaired walkers, which multi-feature "
  "screening reduced but did not remove. Frozen on one dataset, the head-only pipeline transferred to an independent "
  "device and protocol in healthy adults. Eyewear integration, clinical free-living use, and calibrated real-time trust "
  "estimates require prospective validation.")

TAIL = [
 ("h1u", "Data and Code Availability"),
 ("p", "The datasets are available on figshare ⟦voisard_fig⟧ and Zenodo ⟦duogait_data⟧. Code, configuration, the participant "
       "split, per-trial outputs, scripts regenerating all tables and figures, and an analysis-status register are available at "
       "https://github.com/chouchiang00-code/headimu-cadence."),
 ("h1u", "Acknowledgment"),
 ("p", "The authors thank C. Voisard, L. Zhou, and colleagues for making their datasets publicly available."),
]

# ---------------------------------------------------------------- number checks after writing (2026-10-23)
def _fix(a, b):
    hits = [i for i, x in enumerate(B) if x[0] == "p" and a in x[1]]
    assert len(hits) == 1, a[:60]
    B[hits[0]] = ("p", B[hits[0]][1].replace(a, b))
# (AUROC wording fixed directly in the paragraph during the readability pass)
