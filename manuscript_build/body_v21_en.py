TITLE = ("Cadence Estimation From a Single Forehead IMU in Clinical Gait: Site Comparison, Failure Analysis, and "
         "Stride-Based Statistics")
AUTHORS = "Qiang Qiu, Shiqi Chen, and Zhenkun Jin"
RUNNING = "Q. Qiu *et al.*: Cadence Estimation From a Single Forehead IMU in Clinical Gait"
GA_PATH = "fig_v17/graphical_abstract_v17.png"
FOOTNOTE = ("[[Manuscript received Month DD, 2026.]] This work was supported by the National Training Program of Innovation "
            "and Entrepreneurship for Undergraduates under Grant 202611654002. (Corresponding author: Zhenkun Jin.)\n\n"
            "Q. Qiu, S. Chen, and Z. Jin are with the School of Artificial Intelligence and Big Data, Wuhan "
            "University of Business, Wuhan 430056, China (e-mail: 2162385684@qq.com; 1705296766@qq.com; "
            "jinzhenkun@wbu.edu.cn).\n\n"
            "This work involved human subjects only through secondary analysis of two public, de-identified datasets, so "
            "separate ethics approval was not required. The Voisard study was approved by the Comité de Protection des "
            "Personnes Île-de-France II (CPP 2014-10-04 RNI). The DUO-GAIT study was approved by the Ethics Committee of "
            "the University of Potsdam, Germany (No. 63/2020) and followed the Declaration of Helsinki; all participants "
            "gave written informed consent before data collection [32].")

ABSTRACT = (
 "Head-worn devices such as smart glasses can monitor cadence with a built-in inertial measurement unit (IMU), "
 "but same-trial evidence is lacking on whether the error differs between the forehead and the lower back in "
 "clinically abnormal gait and on which segments fail. We analyzed public data from 260 participants (healthy "
 "and seven patient groups), with heel strikes from foot-worn IMUs as the reference, and compared the two sites "
 "on the same straight-walking segments. An autocorrelation-guided stride estimator (AGS) was designed on a "
 "development set (77 participants), frozen, and evaluated on a test set (183 participants, 1860 segments). With "
 "the original peak method, the median absolute cadence error was 1.53 and 1.36 steps/min at the forehead and "
 "lower back, and the large-error proportions (> 5 steps/min) were 9.1% and 9.0% (difference 0.1 percentage "
 "points, 95% confidence interval −2.0 to 2.3). With alternating left and right step intervals, the median step "
 "interval could give a large error even with correctly matched step events. Taking the median per stride "
 "lowered the forehead large-error proportion to 6.8%. AGS, which also fuses an autocorrelation period estimate, "
 "gave 0.87 steps/min and 6.7%. Downsampling to 20 Hz raised the large errors of the original method by 7.2 "
 "percentage points but not detectably those of AGS. Screening by step regularity retained 82.2% of segments "
 "(1.6% with large errors) but excluded 58.0% of those from severely impaired participants. These results hold "
 "for strap fixation, short laboratory walks, and reference-assisted segmentation; real smart glasses and daily "
 "life remain to be validated.")
INDEX = ("Autocorrelation, cadence, gait analysis, gait asymmetry, head-worn sensors, inertial measurement unit (IMU), "
         "sampling rate, wearable sensors.")

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
  "Cadence is a temporal parameter that describes the rhythm of walking, and its changes can reflect disease status and "
  "treatment response in people with Parkinson’s disease ⟦lang⟧. Wearable inertial measurement units (IMUs) have made "
  "gait measurement in daily life possible, and their accuracy depends on the sensor location, the signal processing "
  "method, and the reference standard ⟦hulleck,yin,prisco⟧. Smart glasses and ear-worn devices usually already contain "
  "inertial sensors. If cadence could be estimated reliably from them, long-term monitoring would require one device "
  "fewer.")
p(
  "A foot-worn IMU records the motion of the foot directly, whereas the acceleration recorded by a head-worn IMU is "
  "shaped by the motion of the lower limbs, the trunk, and the neck together. Postural adjustment and independent head "
  "turns may weaken the periodic signature of heel strikes in the head signal. In abnormal gait, two kinds of error "
  "also need to be separated. Extra or missed peaks change the detected sequence of step events. Even when step events "
  "are detected accurately, an alternation of long and short step intervals between the left and right sides can "
  "affect the cadence computed from those intervals.")
p(
  "Head-worn sensors have been used to detect heel strikes and to estimate gait parameters ⟦hwang,tomc,hwang2021,kim⟧. "
  "IMUs in smart glasses, in ear-worn devices, and at the temple have also been evaluated in healthy adults, older "
  "adults, and people with Parkinson’s disease ⟦hellec2022,hellec,vandoorn,fawden,seifer,jarchi,tasca,seifer2025⟧. "
  "The representative studies listed in Table I each enrolled 7–68 participants, mostly healthy, and few compared the "
  "head with the lower back within the same walk.")
p(
  "Studies of trunk IMUs in clinical populations found larger estimation errors in people with hemiparesis or with more "
  "severe gait impairment ⟦trojaniello,mico⟧. Even in healthy people, a waist-worn IMU can miss gait events ⟦storm⟧. "
  "The head error alone therefore cannot tell whether an error is related to the wearing location. Only a comparison "
  "of the two sites on the same walking segment of the same participant can show whether measurement at the forehead "
  "adds error, and for which populations the comparison remains uncertain.")
p(
  "Cadence also depends on how the detected events are summarized. Foot-worn IMUs allow temporal parameters to be "
  "extracted per complete gait cycle (stride) ⟦bertoli,laidig⟧. A treadmill study of orthopedic and neurological "
  "patients reported a mean absolute cadence error of 0.7 steps/min ⟦laidig⟧. With a single trunk or head IMU, cadence "
  "can be estimated from the step intervals between adjacent peaks ⟦zijlstra⟧ or from the signal period obtained by "
  "autocorrelation ⟦moe⟧. When long and short step intervals alternate between the left and right sides, their median "
  "depends on the numbers of long and short intervals, whereas the sum of two adjacent steps may be more stable. For "
  "head or trunk signals, how many large errors a change of the statistical unit removes still has to be compared on "
  "the same sequence of step events.")
p(
  "The choice of the statistical unit also bears on the sampling rate of a head-worn device. In some six-axis IMUs, the "
  "accelerometer draws more than an order of magnitude less current in the 25-Hz low-power mode than in the normal "
  "mode ⟦bmi270⟧. A lower sampling rate also leaves fewer samples per step, so the peak instants are located more "
  "coarsely. How sensitive each cadence estimator is to this time quantization determines which low-rate "
  "configurations are worth validating on a device.")
p(
  "This paper addresses three questions. 1) Within the same walking trial, how much do the cadence estimation errors "
  "of the forehead and lower-back IMUs differ? 2) In clinically abnormal gait, which signal features, reference-event "
  "anomalies, or estimation stages are large errors related to? 3) Which errors are improved by switching to "
  "stride-based statistics and by further fusing an autocorrelation period estimate, and how do these methods behave "
  "at a lower sampling rate or with low step regularity?")
p(
  "The public dataset of Voisard *et al.* ⟦voisard_sd,voisard_fig,voisard_jner,salarian⟧ contains synchronized "
  "recordings from the forehead, the lower back, and both feet of 260 participants in eight cohorts, together with "
  "clinical scores of gait impairment. Earlier work used these recordings for multisensor classification and dataset "
  "auditing ⟦sadegh,wu2026,ye2026⟧. Here the synchronized recordings are used for a paired comparison of the two "
  "sites; step-detection errors and cadence-statistic errors are separated on common reference events, and the "
  "effects of stride-based statistics and of fusion with autocorrelation are then tested.")

table("Validation Conditions and Scope of Gait Studies With Head-Region IMUs",
      ["Study", "Location", "Population (*n*)", "Reference", "Turns/head motion", "Mounting/re-wear"],
      [["Hwang ⟦hwang2021⟧", "Occiput", "Healthy (12)", "Foot IMU, MVN", "—", "—"],
       ["Hellec ⟦hellec2022⟧", "Temple", "Healthy (20)", "Motion capture", "—", "1-week retest"],
       ["Tomc ⟦tomc⟧", "Forehead", "Healthy (7)", "Instrumented treadmill", "—", "—"],
       ["Seifer ⟦seifer⟧", "Ear", "Healthy (48)", "Motion capture", "—", "—"],
       ["Fawden ⟦fawden⟧", "Behind ear", "Mixed (68)^{a}", "Motion capture", "Head turns, turning", "—"],
       ["Tasca ⟦tasca⟧", "Temple", "Healthy (15)", "Multisensor", "Head range of motion only", "—"],
       ["This work", "Forehead + head^{b}", "8 cohorts (260) + healthy (16)", "Foot IMU", "180° turn", "Simulation^{c}"]],
      [820, 740, 1000, 760, 840, 880],
      "Motion capture: optical motion capture; MVN: full-body IMU system. ^{a}Including 18 patients with Parkinson’s "
      "disease, vestibular, or other disorders. ^{b}External dataset ⟦duogait⟧. ^{c}Mounting-error simulations are "
      "given in the supplementary material.")
# =============================================================================== II
h1("Dataset and Reference")
p(
  "This study is a secondary analysis of the public clinical gait dataset of Voisard *et al.* ⟦voisard_sd,voisard_fig⟧. "
  "The data were collected between January 2014 and March 2016 in public and military hospitals in Paris from 260 "
  "participants in eight cohorts: healthy subjects (HS, *n* = 73), hip osteoarthritis (HOA, *n* = 15), knee "
  "osteoarthritis (KOA, *n* = 18), anterior cruciate ligament injury (ACL, *n* = 11), stroke (CVA, *n* = 49), "
  "Parkinson’s disease (PD, *n* = 24), chemotherapy-induced peripheral neuropathy (CIPN, *n* = 19), and "
  "radiation-induced leukoencephalopathy (RIL, *n* = 51). At each visit, a physician rated gait by visual gait "
  "assessment (VGA) on a scale from 0 to 4, from no gait impairment to very severe impairment (⟪T:cohort⟫).")
p(
  "IMUs on the forehead (HE), the lower back (LB), and both feet were sampled synchronously at 100 Hz (Fig. 1(a)). "
  "Participants walked straight along a 6–10-m walkway, turned 180° at the end, and walked back.")
p(
  "The cadence reference is the heel-strike events that the data providers detected with an algorithm using the two "
  "foot-worn IMUs. This detection algorithm was previously validated against an instrumented walkway: the event "
  "detection F1 score was 100% with a median timing error of 8 ms in healthy subjects, and 96.3% with 26 ms in "
  "post-stroke patients with equinovarus foot ⟦voisard_jner⟧. The turn boundaries that delimit the straight-walking "
  "segments were identified from the lower-back IMU ⟦salarian⟧. The analysis uses the signals as processed by the "
  "data providers, namely acceleration including gravity and bias-corrected angular velocity; the preprocessing "
  "includes 14-Hz low-pass filtering and interpolation of short data gaps ⟦voisard_sd⟧.")
p(
  "After stratification by cohort and sensor system, the data were split at random by participant, so that all trials "
  "of one person fall in the same set. The development set contains 77 participants and was used to design the "
  "estimator and fix the parameters. The test set contains 183 participants, 930 walks, and 1860 straight segments, "
  "with 8–51 participants per cohort (⟪T:cohort_lb⟫).")
p(
  "The independent DUO-GAIT dataset ⟦duogait,duogait_data⟧ was used to examine whether the methods transfer to a "
  "different head sensor and walking task. Sixteen healthy adults completed 6-min walks in a 35-m corridor under "
  "single-task and dual-task conditions, before and after a fatigue intervention, giving 64 recordings "
  "(⟪T:ext_audit⟫). The Physilog 5 IMU was sampled at 128 Hz. This dataset tests transfer in healthy people; "
  "conclusions on severely pathological gait still rest on the main dataset.")
fig("fig_v17/fig1_v17.png",
    "Sensors and study design. (a) Sensor locations in the Voisard dataset: forehead (HE), lower back at L4/L5 (LB, the "
    "comparison site, also used to determine the turn boundaries), and both feet (LF/RF, which give the reference heel "
    "strikes). (b) Analysis flow: parameters are fixed on the development set and evaluated on the test set; Q1–Q3 "
    "correspond to questions 1)–3) in the Introduction. A schematic of the mounting errors is given in ⟪F:mount⟫.", 3.45)

# =============================================================================== III
h1("Methods")
h2("Signals and Segmentation")
p(
  "The mounting orientation of a forehead IMU may vary with how it is worn. To make the features insensitive to a "
  "rotation of the axes, let **a**_{s}(*t*) and **ω**_{s}(*t*) be the specific force and the angular velocity in the "
  "sensor frame. The primary signal is the norm of the specific force,")
eq("eq1")
p(
  "Low-pass filtering **a**_{s} at 0.3 Hz and normalizing gives an estimate of the direction of gravity. The projection "
  "of the angular velocity onto this direction approximates the turning rate.")
eq("eq2")
p(
  "Equation (3) projects the specific force onto the estimated direction of gravity, which gives the vertical "
  "acceleration. This feature is common in trunk IMU measurements ⟦zijlstra,moe⟧ and serves here as a comparison.")
eq("eq3")
p(
  "Reference-assisted segmentation (B0) provides the same comparison windows for the two sites. The outbound segment "
  "runs from the first heel strike to the start of the turn, and the return segment from the end of the turn to the "
  "last heel strike (⟪F:pipeline⟫).")
p(
  "Within each straight segment, a third-order zero-phase Butterworth filter extracts the cadence-band signal "
  "(0.6–3.0 Hz). Peaks with a prominence ≥ max(0.12 m/s², 1.5*σ̂*) and a spacing ≥ 0.30 s are taken as step events. "
  "The prespecified primary signal is the norm in (1) (*A1*), and the comparison signal is the vertical acceleration "
  "in (3) (*A0g*). A secondary analysis uses a head-only pipeline (B1), in which the head IMU alone identifies the "
  "walking bouts and the turns (parameters in ⟪T:params⟫).")
h2("Cadence Estimators")
p(
  "Four cadence estimators are compared within the same walking segment. The first two use the same set of peaks and "
  "differ only in how the intervals are summarized. The *step-median* method divides 60 by the median interval "
  "between adjacent peaks ⟦zijlstra⟧. The *stride-median* method first adds each pair of consecutive step intervals "
  "and then divides 120 by the median of these stride times, that is, *C*_{p} = 120 / median(Δ*t*_{k} + Δ*t*_{k+1}).")
p(
  "The *autocorrelation* method uses the periodicity of the band-passed norm signal directly. Within lags of "
  "0.30–0.90 s of the unbiased autocorrelation function, the first peak that reaches 60% of the maximum is taken; its "
  "lag is the estimated step period *T̂* ⟦moe⟧, and the cadence is 60/*T̂*.")
p(
  "*AGS* (the autocorrelation-guided stride estimator) uses the period estimate at two stages. Peaks are first "
  "re-detected with a minimum peak spacing of clip(0.55 *T̂*, 0.25 s, 0.70 s), and their stride median *C*_{p} is "
  "taken; this value is then averaged with the autocorrelation cadence, and the output is (*C*_{p} + 60/*T̂*)/2. If "
  "the segment is too short for *T̂* to be estimated, the output is *C*_{p}.")
p(
  "Estimators were screened on the development set (77 participants, 842 straight segments) by the criterion of the "
  "lowest large-error proportion. The candidates included the step count divided by the duration, a trimmed mean, "
  "interval repair based on an autocorrelation prior, and the median of three estimates. For autocorrelation-guided "
  "detection, three coefficients, 0.55, 0.65, and 0.75, were considered. Each coefficient multiplied by *T̂* gives the "
  "minimum peak spacing, and settings with and without averaging with the autocorrelation cadence were compared.")
p(
  "In fivefold cross-validation by participant, three folds selected AGS and the other two selected the median of "
  "the guided-peak stride estimate, the stride median, and the autocorrelation estimate (⟪T:ags_dev⟫). Both schemes "
  "use stride-based statistics and autocorrelation. After the scheme was selected, the code was frozen and the test "
  "plan was registered, including the secondary analysis with a stride-based reference. The forehead and the lower "
  "back used the same settings and were evaluated once on the test set.")
h2("Two Properties")
p(
  "1) *Step median in asymmetric gait.* To examine how sensitive the statistical unit is to temporal asymmetry, let "
  "the step intervals alternate strictly between *a* and *b* (*a* ≤ *b*). Denote the ratio of the short to the long "
  "step interval by *ρ* = *a*/*b* and the mean cadence by *C* = 120/(*a* + *b*). The median step interval depends on "
  "the numbers of long and short intervals and lies within [*a*, *b*]. The largest deviation of the resulting cadence "
  "from *C* is *C*(1 − *ρ*)/(2*ρ*). In the same model, the sum of two consecutive intervals is always *a* + *b*, and "
  "the cadence computed from the stride time equals *C*. For *C* = 105 steps/min, *ρ* = 0.95 corresponds to 2.8 "
  "steps/min and *ρ* = 0.9 to 5.8 steps/min. In the latter case, temporal asymmetry alone can produce a deviation of "
  "more than 5 steps/min.")
p(
  "2) *Quantization error.* To examine the effect of the sampling rate, let the event instants fall only on a grid "
  "with the sampling interval Δ. The cadence quantization step of the step median is about *C*^{2}Δ/60, and that of "
  "the stride median about *C*^{2}Δ/120. After parabolic interpolation of the autocorrelation peak, the time "
  "resolution of the period estimate can be finer than one sampling interval. For *C* = 105 steps/min at 100 Hz, the "
  "step value is 1.85 steps/min and the stride value 0.92 steps/min. At 20 Hz, they are 9.2 and 4.6 steps/min. This "
  "leads to a prediction to be tested by simulation: as the sampling rate decreases, the large errors of the step "
  "median increase the most, those of the stride median increase less, and estimates that include autocorrelation "
  "remain essentially unchanged.")
h2("Sampling Rate and Sensor Configuration (Simulation)")
p(
  "To test Property 2, the recorded head acceleration was degraded in simulation, with the reference events and the "
  "algorithm parameters held fixed. The output data rate was first reduced to 50, 25, and 20 Hz by anti-aliased "
  "decimation. The effects of noise, quantization, and measurement range were then examined separately. White noise "
  "with a standard deviation of 0.05–1.0 m/s² was added to each axis (1.0 m/s² corresponds to a noise density of about "
  "14 mg/√Hz at 100 Hz). The quantization step was set to 0.01–0.5 m/s², the range was clipped to ±1.5 g, and a "
  "combination of 25 Hz, ±4 g, and 8-bit quantization was also tested. For the head-only pipeline, the cost of "
  "omitting the gyroscope was examined as well; in this case, the turn is kept and the whole walk is treated as one "
  "segment.")
h2("Applicability Rule")
p(
  "*Step regularity (SR)* is used to decide when to report cadence. For each segment, it is the autocorrelation of "
  "the band-passed norm signal of that site at the lag of the step period ⟦moe⟧, and it requires only the signal of "
  "that sensor. On the development set, an SR threshold (0–0.7) and an AGS cadence threshold (0–100 steps/min) were "
  "searched jointly, and among the combinations with a large-error proportion of no more than 3%, the one retaining "
  "the most segments was selected. The selected rule was applied to the test set, and the retained proportion and "
  "the large-error proportion among the retained segments are reported. To assess the cost of screening, the "
  "excluded proportion is reported by the clinical VGA score, together with the segments that were excluded although "
  "their error did not exceed the threshold.")
h2("Outcomes and Statistics")
p(
  "On each straight segment, the median step interval is computed separately for the IMU-detected events and for the "
  "reference events. Equation (4) gives the interval error and the corresponding cadence error.")
eq("eq6")
p(
  "The primary outcome is the median of |*e*_{C}|. The secondary outcomes are the proportion of segments with a large "
  "error (|*e*_{C}| > 5 steps/min), the Bland–Altman bias, and the 95% limits of agreement (LoA) for repeated "
  "measurements ⟦bland1986,bland2007⟧. Segments without an output are also counted in the denominator of the "
  "large-error proportion. The 5-steps/min threshold is about three times the step quantization step at 100 Hz and "
  "one third of the minimal detectable change of cadence in Parkinson’s disease (15 steps/min) ⟦lang⟧. Results for "
  "thresholds of 3 and 10 steps/min are given in ⟪T:post⟫.")
p(
  "For the primary outcome, the median over the segments is first taken within each participant, and the median is "
  "then taken across participants. The 95% confidence intervals (CIs) come from 2000 participant-level bootstrap "
  "resamples. The forehead and the lower back are compared in pairs by participant and reported for each cohort, with "
  "Holm correction for multiple comparisons ⟦holm⟧. For each cohort, the larger absolute value of the two ends of the "
  "95% CI of the paired difference expresses the largest difference that the data cannot yet exclude.")
p(
  "The primary analysis uses the prespecified step-based reference, that is, 60 divided by the median reference step "
  "interval. A secondary analysis uses the same reference events with 120 divided by the median reference stride "
  "time. The two definitions can give different cadences in asymmetric gait (Property 1). In 2.6% of the test "
  "segments, the reference cadences computed by the two definitions differ by more than 5 steps/min; the estimator "
  "errors are therefore reported against both references.")
p(
  "The site comparison under reference-assisted segmentation was a prespecified analysis. AGS was designed on the "
  "development set, frozen, and evaluated once on the test set. The applicability rule, the simulations of the "
  "sampling rate and sensor configuration, the comparison with an external detector, and the failure analysis were "
  "all completed after the freeze, with the estimator parameters kept at their frozen values. The remaining post hoc "
  "analyses are listed in ⟪T:post⟫.")
p(
  "The supplementary material gives the signal checks (⟪F:inclusion⟫, ⟪T:qc⟫, ⟪F:qc⟫), the results stratified by "
  "sensor system and by cohort (⟪T:strata⟫, ⟪F:cohorts⟫), the mounting simulations (⟪T:sims⟫, ⟪F:sims⟫, ⟪T:sens⟫, "
  "⟪T:bounds⟫), the between-visit consistency (⟪F:rewear⟫, ⟪T:rewear⟫), and an earlier trial-level screening rule "
  "(⟪T:screen⟫, ⟪F:screen⟫, ⟪T:q2⟫).")

# =============================================================================== IV
h1("Results")
h2("Head Versus Lower Back")
p(
  "One visit of RIL_12 lacked the head signal, leaving 1351 trials from 260 participants. Under reference-assisted "
  "segmentation on the test set, the median absolute cadence error of the original peak method was 1.53 steps/min at "
  "the forehead (95% CI 1.31–1.71) and 1.36 steps/min at the lower back (1.21–1.54). The bias of the forehead "
  "estimate was −0.45 steps/min, with LoA from −11.5 to 10.6 steps/min (Table II, ⟪F:ba4⟫). Paired by participant, "
  "the median difference in error, forehead minus lower back, was 0.00 steps/min (95% CI −0.01 to 0.06). The "
  "large-error proportions at the forehead and the lower back were 9.1% and 9.0%, a difference of 0.1 percentage "
  "points (95% CI −2.0 to 2.3).")
p(
  "With the step median, 25.8% of the segments had zero error, and the typical error was close to the cadence "
  "resolution of one sampling interval (about 1.8 steps/min). With the mean step interval, which has a finer "
  "resolution, the typical errors at the forehead and the lower back were 1.06 and 1.08 steps/min (⟪T:altmetric⟫). "
  "The F1 score of step-event detection at the forehead was 0.936 (⟪T:events⟫, ⟪F:example⟫). When the cadence of each "
  "segment was estimated only by the median cadence of its cohort, the error was 7.42 steps/min (⟪T:baseline⟫). "
  "Changing the peak-detection parameters (⟪T:peak⟫), or using cross-validation so that each of the 260 participants "
  "was tested once (1.44 steps/min, 1.31–1.61; ⟪T:cv⟫, ⟪T:band⟫), gave forehead typical errors close to that of the "
  "main analysis.")
table("Agreement of Straight-Walking Cadence Under Reference-Assisted Segmentation (Test Set, 183 Participants, 1860 Segments)",
      ["Method", "|*e*_{C}|, median [95% CI]", "Relative error (%)", "Bias", "95% LoA", "Halving/doubling (%)"],
      [["HE-A0g", "1.51 [1.34, 1.65]", "1.50", "−0.32", "−10.8, 10.1", "0.1 / 0.1"],
       ["HE-A1", "1.53 [1.31, 1.71]", "1.50", "−0.45", "−11.5, 10.6", "0.3 / 0.1"],
       ["HE-AC", "1.02 [0.88, 1.09]", "0.97", "0.72", "−12.9, 14.3", "0.1 / 0.3"],
       ["LB-A1", "1.36 [1.21, 1.54]", "1.36", "0.10", "−10.2, 10.4", "0.1 / 0.1"],
       ["LB-AC", "0.92 [0.85, 1.01]", "0.89", "0.97", "−13.8, 15.8", "0.0 / 0.4"]],
      [720, 1300, 700, 620, 1000, 700],
      "Values are in steps/min except for percentages; LoA are computed for repeated measurements ⟦bland2007⟧. HE: head; "
      "LB: lower back. A1: norm; A0g: vertical acceleration (both with the step median); AC: autocorrelation.")
p(
  "The forehead typical error was lowest in the healthy cohort (1.11 steps/min) and highest in the stroke cohort "
  "(2.58 steps/min), and the lower back showed the same ordering (Fig. 2). The 95% CIs of the paired site difference "
  "included 0 in all eight cohorts. The largest difference that the data cannot yet exclude was 0.31 steps/min in the "
  "CIPN cohort and 1.13 steps/min in the stroke cohort (⟪T:cohort_lb⟫). In the stroke cohort, the large-error "
  "proportions at the forehead and the lower back were 35.2% and 35.8%. In the Parkinson’s disease cohort, they were "
  "10.4% and 4.8%, a difference of 5.7 percentage points (−2.0 to 15.7). This cohort has only 16 participants, and "
  "the direction of the site difference remains uncertain (⟪T:tail⟫).")
fig("fig_v17/fig3_cohort_v17.png",
    "Cadence error of A1 at the head and the lower back in each cohort (B0, test set). Cohorts are grouped as healthy, "
    "orthopedic, and neurological; the number of test participants is given in parentheses. (a) Median of the "
    "participant medians with 95% CI; the upper limit for the stroke cohort exceeds the axis and is marked by an arrow "
    "and its value; the trivial baseline that ignores the signal (7.4 steps/min) is shown at the lower right. "
    "(b) Paired participant difference, head minus lower back, with 95% CI; the numbers on the right are the largest "
    "differences that the data cannot yet exclude. (c) Proportion of segments with |*e*_{C}| > 5 steps/min, divided "
    "into head only, both sites, and lower back only; the numbers on the right are the totals with a large error at "
    "either site. CIs are from 2000 participant-level bootstrap resamples; values are given in ⟪T:cohort_lb⟫.", 7.0)
h2("Sources of Large Errors")
p(
  "At both sites, large errors were concentrated in segments with low step regularity. Among the 109 segments with "
  "SR < 0.4, the large-error proportions at the forehead and the lower back were 72.5% and 61.5%. For SR ≥ 0.9, both "
  "were below 1.5% (⟪F:failure⟫). After adjustment for cadence, head signal amplitude, and cohort, the odds ratio of a "
  "forehead large error per one-standard-deviation increase in SR was 0.24 (0.16–0.30), and the association between "
  "amplitude and large errors was no longer evident. The head SR also predicted large errors at the lower back "
  "(⟪T:confound⟫, ⟪T:seglen⟫). Ninety-seven segments had a large error at both sites, and 72 and 70 segments had a "
  "large error only at the forehead or only at the lower back (⟪T:headonly⟫, ⟪T:headtrunk⟫).")
p(
  "The two sites share the foot reference, so a suspected missed reference event can also appear as an error at both "
  "sites. The reference was flagged as suspect if the same foot had two consecutive heel strikes or if the longest "
  "step interval exceeded 1.6 times the median (⟪T:refcheck⟫). Of the 1860 test segments, 101 (5.4%) met this "
  "condition; in the stroke cohort, the proportion was 16.7%. The reference was suspect in 29 of the 97 segments with "
  "a large error at both sites. After the suspect-reference segments were removed, the large-error proportions at the "
  "forehead and the lower back were 7.7% and 7.2%, a difference of 0.5 percentage points (95% CI −1.5 to 2.6).")
p(
  "To separate reference anomalies, event-detection errors, and interval-summary bias, the 152 segments with a large "
  "error of the step-median method among the 842 development segments were classified in sequence (Fig. 3(b)). The "
  "reference was suspect in 44 of them. With reference events matched within a tolerance of 0.15 s, 56 were "
  "classified as extra peaks (precision < 0.9) and 37 as missed peaks (recall < 0.9); in the remaining 15, the step "
  "events were essentially matched but the cadence error was still large. The extra-peak segments had a lower "
  "cadence and a smaller signal amplitude. The extra peaks occurred 0.15–0.6 step periods after the reference heel "
  "strike, which is consistent with a secondary peak within a step, and the same phenomenon was present at the lower "
  "back (⟪T:mech⟫).")
p(
  "In the 15 large-error segments with essentially matched step events, the median asymmetry of the reference "
  "intervals was 0.13, compared with 0.04 in the small-error segments. The asymmetry is the difference between the "
  "medians of the odd and even step intervals divided by the median interval. In the segment shown in Fig. 3(a), the "
  "reference intervals alternate between about 0.57 s and 0.85 s. Computed per step, the reference and forehead "
  "cadences were 87.6 and 82.2 steps/min. Computed per stride, both were 84.5 steps/min. This example agrees with "
  "the prediction of Property 1.")
h2("Stride-Based Computation")
p(
  "Replacing the step median by the stride median on the same set of peaks lowered the large-error proportion from "
  "9.1% to 6.8% at the forehead and from 9.0% to 6.3% at the lower back (Table III, Fig. 4(a)). The frozen AGS had "
  "large-error proportions of 6.7% and 5.9% at the two sites, which were 2.4 percentage points (95% CI 1.1–3.9) and "
  "3.1 percentage points (2.0–4.5) lower than those of the step median. With AGS, the difference between the "
  "forehead and the lower back was 0.8 percentage points (−0.5 to 2.2). With the autocorrelation-guided peak spacing "
  "alone, the forehead large-error proportion was 8.8%.")
p(
  "The large-error proportions of the stride median, autocorrelation, and AGS were close, and the three differed more "
  "in the typical error. The forehead median absolute errors were 1.05, 1.02, and 0.87 steps/min, respectively; with "
  "autocorrelation alone, 0.5% of the segments were too short to give an output. The improvement of AGS agrees with "
  "the difference in resolution described by Property 2.")
p(
  "Stratified by the original failure type, 88% of the forehead test segments with “step events essentially matched "
  "but error still large” fell within the large-error threshold after the change to stride-based statistics. For the "
  "extra-peak and missed-peak segments, the corresponding proportions were 51% and 31%. Conversely, 2.0% of the "
  "segments whose error had been small became large errors. When the same reference events gave cadences differing "
  "by more than 5 steps/min between the step and stride computations, the reference ratio *ρ* in Fig. 4(b) was below "
  "0.9 in 96% of the segments.")
p(
  "With the reference also defined per stride, the stride median still lowered the forehead large-error proportion "
  "from 7.8% to 4.9%, and AGS was 2.8 percentage points (1.5–4.4) lower than the step median. The improvement "
  "remained after the reference definition was unified, and it was also seen in some segments with occasional extra "
  "or missed peaks.")
p(
  "To test whether the effect of stride-based statistics depends on the peak detector, the Ionescu initial-contact "
  "detector was run with its default parameters on the same segments. This detector is wavelet based, was designed "
  "for the lower back, and was taken from mobgap 1.2.0, the open-source implementation of the Mobilise-D pipeline "
  "⟦mico,mobgap⟧. The forehead large-error proportions of the step and stride medians were 7.6% and 5.8%, a "
  "difference of −1.8 percentage points (95% CI −3.0 to −0.7). At the lower back, they were 6.0% and 5.4%, a "
  "difference of −0.6 percentage points (−1.4 to 0.2). The results of the two mobgap cadence presets intended for "
  "long daily-life walking on these short straight segments are given in ⟪T:mdpreset⟫.")
p(
  "Compared with the original peak method, the forehead large-error proportion of AGS decreased in seven cohorts and "
  "was unchanged in the CIPN cohort. It fell from 35.2% to 28.4% in the stroke cohort (95% CI 15.8–42.9) and from "
  "13.5% to 10.5% in the radiation-induced leukoencephalopathy cohort (Fig. 3(c), ⟪T:ags_cohort⟫). The net reduction "
  "was 45 forehead large-error segments, 26 of which came from these two cohorts.")
p(
  "In the head-only pipeline (B1), the comparison metric is the proportion of segments with a large error or no "
  "output, which fell from 10.9% with the original peak method to 8.3% with AGS (⟪T:e2e_main⟫, ⟪T:e2e_cohort⟫, "
  "⟪T:e2e_detect⟫, ⟪T:gating⟫, ⟪F:gating⟫, ⟪F:e2e⟫, ⟪T:tuning⟫). On the independent DUO-GAIT dataset of healthy "
  "adults, with the same parameters, the median error fell from 0.62 to 0.42 steps/min (0.37–0.50). Only one of the "
  "797 segments of this dataset had a large error (⟪F:ext_ba⟫, ⟪T:ext_cond⟫).")
table("Cadence Estimators Computed per Step and per Stride on the Test Set (183 Participants, 1860 Segments per Site)",
      ["Estimator", "Head |*e*_{C}|", "Head > 5 (%)", "Lower back |*e*_{C}|", "Lower back > 5 (%)",
       "Stride reference: head > 5 (%)", "Stride reference: lower back > 5 (%)"],
      [["Peaks, step median (original method)", "1.53 [1.31, 1.71]", "9.1 [5.9, 12.8]", "1.36 [1.20, 1.54]",
        "9.0 [6.1, 12.8]", "7.8 [4.9, 12.0]", "8.1 [5.3, 12.2]"],
       ["Peaks, stride median", "1.05 [1.00, 1.11]", "6.8 [4.6, 9.2]", "1.05 [0.96, 1.13]", "6.3 [4.3, 8.7]",
        "4.9 [2.8, 7.7]", "3.4 [1.8, 5.4]"],
       ["Autocorrelation", "1.02 [0.88, 1.09]", "6.4 [3.7, 9.9]", "0.92 [0.85, 1.00]", "5.7 [3.1, 9.3]",
        "4.6 [2.2, 8.3]", "4.0 [1.7, 7.9]"],
       ["AGS", "0.87 [0.81, 0.98]", "6.7 [4.1, 9.8]", "0.84 [0.80, 0.91]", "5.9 [3.3, 9.6]", "5.0 [2.6, 8.5]",
        "4.0 [1.7, 7.7]"],
       ["Ionescu detector, step median^{a}", "1.39 [1.30, 1.54]", "7.6 [5.0, 11.1]", "1.30 [1.11, 1.44]",
        "6.0 [3.4, 9.7]", "5.2 [2.8, 8.4]", "4.4 [2.0, 8.0]"],
       ["Ionescu detector, stride median^{a}", "1.10 [1.07, 1.14]", "5.8 [3.7, 8.6]", "1.04 [1.01, 1.08]",
        "5.4 [2.9, 9.1]", "3.9 [1.9, 6.7]", "3.3 [1.2, 6.8]"]],
      [2350, 1350, 1250, 1350, 1250, 1350, 1350],
      "Values are in steps/min; brackets give 95% CIs (2000 participant-level bootstrap resamples). For the first five "
      "columns, the reference is 60 divided by the median reference step interval (primary definition); for the last "
      "two, it is 120 divided by the median reference stride time. |*e*_{C}| is the median of the participant medians. "
      "The autocorrelation method gave no output for 0.5% (head) and 0.4% (lower back) of the segments because they "
      "were too short; these are counted in the denominator and not as large errors. ^{a}Initial-contact detector of "
      "mobgap 1.2.0 ⟦mobgap⟧, default parameters.")
fig("fig_v18/fig6_ags_v18.png",
    "Asymmetric gait and stride-based computation. (a) A development-set segment with left–right step asymmetry "
    "(KOA_6_1): the reference step intervals (crosses) and the head peak intervals (circles) alternate between a long "
    "and a short cluster; dashed lines are the step medians and dotted lines are half the stride medians (the dotted "
    "lines of the reference and the head coincide), with the corresponding cadences given as numbers; the triangle "
    "marks one missed-peak interval beyond the axis. (b) Large errors of the original estimator on the development set "
    "grouped by failure type; teal marks the segments whose error AGS brought within 5 steps/min. (c) Proportion of "
    "segments with |*e*_{C}| > 5 steps/min in each cohort on the test set, from the original estimator (open marker) "
    "to AGS (arrowhead), shown separately for the head and the lower back.", 7.0)
fig("fig_v18/fig6_mech_v18.png",
    "Ablation, test of Property 1, and applicability (test set). (a) Proportion of segments with |*e*_{C}| > 5 "
    "steps/min as components are added one at a time; horizontal bars are participant-level bootstrap 95% CIs. "
    "(b) Difference between the reference cadences computed by the step median and per stride, plotted against the "
    "reference left–right step ratio *ρ*; the curve is the largest deviation under strict alternation, "
    "*C*(1 − *ρ*)/(2*ρ*), and the dotted line is 5 steps/min. (c) Large-error proportion of AGS by the segment step "
    "regularity SR of the same sensor signal; the dashed line is the rule SR ≥ 0.7 selected on the development set.", 7.0)
h2("Sampling Rate and Sensor Configuration")
p(
  "The effect of downsampling on the forehead large-error proportion differed between estimators (Table IV, Fig. 5). "
  "Relative to the original recording, at 20 Hz the step median increased by 7.2 percentage points (95% CI 5.6 to "
  "8.7), the stride median by 1.1 percentage points (0.2 to 2.1), and AGS changed by 0.0 percentage points (−0.3 to "
  "0.3). The typical error of AGS increased by 0.08 steps/min. This ordering agrees with the prediction of "
  "Property 2.")
p(
  "When noise of 1.0 m/s² was added to each axis, the quantization step was raised to 0.5 m/s², or the range was "
  "clipped to ±1.5 g, the large-error proportion of AGS changed by no more than 0.4 percentage points. In the "
  "segments without a large error, the median root-mean-square (RMS) value of the forehead cadence-band vertical "
  "acceleration was 1.16 m/s², 0.97 times that of the lower back. As an order-of-magnitude comparison, a noise "
  "density of 160 µg/√Hz, as specified for a consumer-grade microelectromechanical systems (MEMS) accelerometer "
  "⟦bmi270⟧, gives an in-band noise of about 0.0024 m/s² (⟪F:sensing⟫, ⟪T:transmission⟫, ⟪T:harm⟫).")
p(
  "The head-only pipeline uses the gyroscope to identify turns. When the gyroscope was omitted and the whole walk, "
  "including the turn, was treated as one segment, the proportion of AGS large errors or no output increased by 1.6 "
  "percentage points at 100 Hz (95% CI −0.3 to 3.7) and by 2.0 percentage points at 25 Hz (0.1 to 4.3).")
table("Change in the Head Large-Error Proportion Under Degraded Sensor Configurations (Simulation; Test Set, Relative to "
      "the 100-Hz Original Recording, Percentage Points)",
      ["Degradation", "Step median", "Stride median", "AGS"],
      [["50 Hz", "0.5 [−0.5, 1.5]", "0.2 [−0.3, 0.8]", "0.0 [−0.4, 0.4]"],
       ["25 Hz", "4.9 [3.7, 6.3]", "1.1 [0.4, 1.9]", "0.2 [−0.2, 0.5]"],
       ["20 Hz", "7.2 [5.6, 8.7]", "1.1 [0.2, 2.1]", "0.0 [−0.3, 0.3]"],
       ["Noise 1.0 m/s²", "0.6 [−0.3, 1.6]", "1.6 [0.6, 2.7]", "0.4 [−0.1, 1.0]"],
       ["Quantization 0.5 m/s²", "−0.2 [−0.8, 0.4]", "0.2 [−0.3, 0.8]", "−0.1 [−0.4, 0.3]"],
       ["Range ±1.5 g", "0.0 [0.0, 0.0]", "0.0 [0.0, 0.0]", "0.0 [0.0, 0.0]"],
       ["25 Hz, ±4 g, 8 bit", "4.6 [3.3, 6.0]", "1.6 [0.7, 2.7]", "0.1 [−0.4, 0.5]"]],
      [1300, 1240, 1240, 1240],
      "Paired change, relative to the original recording, in the proportion of segments with |*e*_{C}| > 5 steps/min; "
      "brackets give participant-level bootstrap 95% CIs. Noise is the standard deviation per axis. The recorded "
      "signals were degraded artificially and the parameters were not retuned; all conditions are given in ⟪T:sensreq⟫.")
fig("fig_v20/fig5_rate_v20.png",
    "Proportion of head segments with |*e*_{C}| > 5 steps/min as the output data rate is reduced (test set; "
    "anti-aliased decimation of the 100-Hz recorded signals, parameters not retuned). Vertical bars are "
    "participant-level bootstrap 95% CIs; the upper axis gives the quantization step of the step median from "
    "Property 2, *C*^{2}Δ/60 (*C* = 105 steps/min); the stride value is half of it.", 3.45)
h2("Applicability")
p(
  "On the development set, the rule selected for both sites was a segment SR ≥ 0.7 from the same sensor. Applied to "
  "the test set, the rule retained 82.2% of the forehead segments (95% CI 77.5–86.7), among which the large-error "
  "proportion of AGS was 1.6% (95% CI 0.8–2.5). The large-error proportion among the excluded segments was 30.1%, "
  "and these segments contained 81% of all forehead large errors. At the lower back, 87.4% of the segments were "
  "retained, and the large-error proportions among the retained and excluded segments were 1.3% and 37.4% "
  "(Fig. 4(c)).")
p(
  "The cost of screening was highest in severely impaired participants. For VGA scores of 0, 1, 2, and ≥ 3, the "
  "excluded proportions of forehead segments were 2.4%, 9.5%, 30.3%, and 58.0% (95% CI for the severe group "
  "37.5–76.6). The VGA ≥ 3 group has 23 participants, and 44% of its segments without a forehead large error were "
  "also excluded. The lower-back rule excluded 53.4% of all segments of this group (⟪T:env_vga⟫). By cohort, the "
  "head rule retained 99%, 85%, and 37% of the segments in the healthy, Parkinson’s disease, and stroke cohorts.")

# =============================================================================== V
h1("Discussion")
h2("Head and Lower Back")
p(
  "A paired comparison within the same segment of the same participant controls for between-participant differences "
  "in gait. In the 183 test participants, the 95% CI of the difference in the large-error proportion between the "
  "forehead and the lower back was −2.0 to 2.3 percentage points. The overall result shows no clear site "
  "difference, but the precision in subgroups is lower. In the stroke cohort, a difference in typical error of 1.1 "
  "steps/min cannot yet be excluded. In the Parkinson’s disease cohort, the forehead large-error proportion was "
  "about twice that of the lower back, and with only 16 participants it is difficult to judge whether this "
  "difference would replicate.")
p(
  "The two sites often had a large error in the same segment, and low regularity of the head signal was also "
  "associated with errors at the lower back. In the segments without a large error, the amplitudes of the "
  "cadence-band vertical acceleration at the two sites were close. These observations suggest that shared gait "
  "characteristics may explain part of the failures, and they help to explain why no consistent disadvantage of "
  "either site was observed under reference-assisted segmentation.")
h2("Why Compute per Stride")
p(
  "The step median is sensitive to how many long and how many short intervals occur. In the strict-alternation model "
  "of Property 1, the sum of two adjacent steps is more stable than the step interval. In the experiments, almost "
  "all segments in which the reference cadences of the two definitions differed by more than 5 steps/min had *ρ* "
  "below 0.9 in Fig. 4(b). Of the segments in which the step events were essentially matched but the cadence error "
  "was still large, nearly 90% fell within the threshold after the change to stride-based statistics. The "
  "large-error proportions at the forehead and the lower back both decreased by more than one quarter, and the "
  "improvement at the forehead was still observed with a different event detector.")
p(
  "The large-error proportions of the stride median, autocorrelation, and AGS showed no detectable difference. Both "
  "schemes selected by cross-validation on the development set contain stride-based statistics. These results "
  "support summarizing the events detected by a single head or trunk sensor per stride, in preference to per step, "
  "in gait that may be temporally asymmetric.")
p(
  "After fusion with the autocorrelation estimate, the forehead typical error of AGS fell from 1.53 steps/min with "
  "the original peak method to 0.87 steps/min, and part of this improvement may come from time resolution. This "
  "difference is smaller than the minimal detectable change of cadence reported for Parkinson’s disease (15 "
  "steps/min) ⟦lang⟧. For large errors, the study threshold equals one third of that change. Compared with the "
  "original method, AGS gave about two fewer large-error outputs per 100 forehead segments, and more than half of "
  "the net reduction came from the radiation-induced leukoencephalopathy and stroke cohorts.")
h2("Implications for Head-Worn Devices")
p(
  "The sampling resolution of the event times places a constraint on hardware design. With the example used for "
  "Property 2, the cadence quantization step of the step median already exceeds 5 steps/min at sampling rates below "
  "about 37 Hz (7.4 steps/min at 25 Hz). Stride-based statistics halve this step, and the autocorrelation peak can "
  "in addition be interpolated to below one sampling interval. In the 20-Hz simulation, the large-error proportions "
  "of the step and stride medians increased by about 7 and 1 percentage points, and the change of AGS was close to "
  "zero.")
p(
  "According to the device documentation, the accelerometer current in the 25-Hz low-power mode is more than an order "
  "of magnitude lower than in the normal mode, and the gyroscope operating current is about three times that of the "
  "accelerometer ⟦bmi270⟧. The simulations suggest that a configuration estimating cadence from an accelerometer "
  "alone at 20–25 Hz could be tested on a real head-worn device. With the turn retained, the proportion of large "
  "errors or no output increased by about 2 percentage points. Under the comparison conditions of this study, the "
  "head gait signal was more than two orders of magnitude above the device noise, and AGS was also stable under the "
  "tested noise and quantization degradations. Without reference-assisted segmentation, the original analysis "
  "attributed about half of the no-output cases to uncalibrated gyroscope bias, which suggests that a static "
  "calibration should be considered when a gyroscope is used to identify turns.")
p(
  "Under temporal asymmetry, two adjacent steps can still form a stable stride period. When the gait itself is highly "
  "irregular, stride-based estimation also tends to fail. Among the forehead segments with SR ≥ 0.7, the large-error "
  "proportion of AGS was below 2%. This range covers almost all segments of the healthy cohort and 85% of those of "
  "the Parkinson’s disease cohort, but only 37% of those of the stroke cohort and about 40% of those of the severely "
  "impaired group. Below the threshold, large errors were common at both sites. A device can report the SR computed "
  "from its own signal together with the cadence, and users interpreting the retained results also need to take "
  "into account the loss of coverage caused by screening.")
h2("Comparison With Previous Studies")
p(
  "Previous studies of the head region mostly addressed healthy people. The ear-worn EarGait reported a stride-time "
  "error of about 12 ms ⟦seifer⟧, and a temple IMU detected heel strikes in daily life with an F1 score of about 93% "
  "⟦tasca⟧. When the EarGait detector was run without tuning on the same segments as in this paper, the cadence was "
  "doubled in 4.9% of the segments (⟪T:post⟫). In studies of trunk IMUs, people with hemiparesis ⟦trojaniello⟧ and "
  "those with the most severe gait impairment ⟦mico⟧ were also more difficult to measure. A similar difficulty was "
  "observed here in the stroke cohort, and it involved both the forehead and the lower back. Foot-worn IMUs extract "
  "parameters per stride, and a mean absolute cadence error of 0.7 steps/min was reported for pathological gait on a "
  "treadmill ⟦laidig⟧. This value is of the same order as the median absolute error of head AGS (0.87 steps/min), "
  "although the statistic and the walking conditions both differ.")
h2("Limitations")
p(
  "The reference events come from a validated foot-IMU algorithm, and a synchronized motion-capture reference is "
  "lacking. The reference was suspect in about one sixth of the segments of the stroke cohort, and the turn "
  "boundaries of the primary analysis were also taken from the lower-back IMU. The sensor was fixed to the forehead "
  "with a strap, the walkway was 6–10 m long, and the participants did not turn their heads actively. Slipping and "
  "re-wearing of glasses were only simulated (⟪T:sims⟫), so the transfer of the results to real glasses and daily "
  "activities remains to be validated. The simulations of the sampling rate and configuration are based on signals "
  "recorded at 100 Hz and do not model the filtering and clock jitter of real low-power modes.")
p(
  "The estimator was designed on the development set, but the authors had already seen the distribution of large "
  "errors on the test set during the site comparison, so the evaluation of AGS was not fully blinded. Each cohort has "
  "only 8–51 test participants, and the intervals of the subgroup differences are wide. The independent DUO-GAIT "
  "dataset has only 16 healthy adults and almost no large errors, so it can hardly test the improvement in severely "
  "abnormal gait.")

# =============================================================================== VI
h1("Conclusion")
p(
  "Through a same-trial comparison, this study evaluated cadence estimation from a single forehead IMU in clinical "
  "populations and analyzed the main sources of error and ways to reduce them. With short laboratory walks, strap "
  "fixation at the forehead, and reference-assisted segmentation, the overall cadence estimation errors of the "
  "forehead and lower-back IMUs showed no clear difference, but the comparisons in clinical subgroups remain "
  "uncertain. Further analysis showed that large estimation errors were mainly related to reduced step regularity, "
  "extra or missed gait events, and temporal asymmetry between alternating steps.")
p(
  "For the bias that step-interval statistics can produce in asymmetric gait, the median stride time removed part of "
  "the large errors. On this basis, AGS further fuses an autocorrelation period estimate; it improved the typical "
  "estimation error and remained relatively stable in the 20-Hz downsampling simulation. The screening rule based on "
  "step regularity identified part of the segments at high risk of error, but it also excluded many valid recordings "
  "from participants with severe gait impairment.")
p(
  "These results indicate that cadence estimation from a single forehead IMU is feasible under controlled "
  "experimental conditions, and that stride-based statistics and fusion with autocorrelation offer a practicable way "
  "to improve the estimates. Severely irregular gait nevertheless remains an important factor limiting the "
  "reliability of the estimates. Validation with smart glasses, during long-term wear, and in daily walking "
  "environments is still needed to determine the practical range of application of these methods.")

TAIL = [
 ("h1u", "Data and Code Availability"),
 ("p", "The datasets are available from figshare ⟦voisard_fig⟧ and Zenodo ⟦duogait_data⟧. The code, configurations, "
       "participant split, per-trial outputs, scripts that regenerate all figures and tables, and the register of "
       "analysis status are available at https://github.com/chouchiang00-code/headimu-cadence."),
 ("h1u", "Acknowledgment"),
 ("p", "The authors thank C. Voisard, L. Zhou, and their colleagues for making their datasets publicly available."),
]
