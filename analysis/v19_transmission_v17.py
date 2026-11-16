#!/usr/bin/env python3
"""V19 (post hoc, descriptive): the forehead as a sensing site, from the per-segment head-trunk measures already
computed on the PC by v17_head_trunk.py (test set, same B0 straight segments; definitions in that script):
  tr_v       step-band (0.6-3 Hz) RMS of head vertical acceleration / RMS of lower-back vertical acceleration
  coh_v      magnitude-squared coherence of head and lower-back vertical acceleration at the reference step frequency
  lag_a1_s   lag of the head relative to the lower back (max cross-correlation of band-passed |a|)
  rms_v_he, rms_v_lb   step-band RMS of vertical acceleration (m/s2): the signal budget at each site
  tilt_ratio head / lower-back RMS of horizontal angular rate in the step band (nodding / rolling)
  yaw_rel_bp RMS of head-minus-trunk angular rate about vertical in the step band (deg/s)
Main group: segments without a large error at either site, with the published estimator and with AGS ("clean").
Participant-level medians, participant bootstrap (2000). Also the noise margin: step-band RMS of the simulated white
noise of the sensor-requirement analysis (sigma per axis at 100 Hz; projected on vertical, filtered to 0.6-3 Hz).
Usage: python analysis/v19_transmission_v17.py HEAD_TRUNK_SEGMENTS_CSV EXT_TEST_CSV OUT_JSON"""
import json, sys
import numpy as np, pandas as pd
# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v19_transmission_v17.py HEAD_TRUNK_SEGMENTS_CSV EXT_TEST_CSV OUT_JSON')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

ht, ext, outp = sys.argv[1:4]
D = pd.read_csv(ht)
E = pd.read_csv(ext); E = E[E.C_peak.notna()]
lab = E.assign(bp=(E.C_peak - E.R_step).abs() > 5, ba=(E.C_ags - E.R_step).abs() > 5).pivot_table(
    index=["trial", "segment"], columns="loc", values=["bp", "ba", "R_step"], aggfunc="max")
lab.columns = [f"{a}_{b}" for a, b in lab.columns]
D = D.merge(lab.reset_index(), on=["trial", "segment"], how="left")
D["clean"] = ~D[["bp_HE", "bp_LB", "ba_HE", "ba_LB"]].fillna(True).astype(bool).any(axis=1)
D["lag_ms"] = 1000 * D.lag_a1_s
rng = np.random.default_rng(20261118)
MEAS = ["tr_v", "coh_v", "lag_ms", "rms_v_he", "rms_v_lb", "tilt_ratio", "yaw_rel_bp"]


def pb(d, c, B=2000):
    pm = d.groupby("participant")[c].median().dropna().to_numpy()
    if len(pm) < 3:
        return [float(np.median(pm)) if len(pm) else np.nan, np.nan, np.nan]
    bs = [np.median(rng.choice(pm, len(pm))) for _ in range(B)]
    return [float(np.median(pm)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


R = {"n_segments": int(len(D)), "n_clean": int(D.clean.sum()), "n_participants_clean": int(D[D.clean].participant.nunique())}
C = D[D.clean]
R["clean"] = {"All": {m: pb(C, m) for m in MEAS}}
for coh, g in C.groupby("cohort"):
    R["clean"][coh] = {m: pb(g, m) for m in MEAS}
    R["clean"][coh]["n_part"] = int(g.participant.nunique()); R["clean"][coh]["n_seg"] = int(len(g))
R["clean"]["All"]["n_part"] = R["n_participants_clean"]; R["clean"]["All"]["n_seg"] = R["n_clean"]
R["spearman_clean"] = {m: float(C[[m, "R_step_HE"]].corr("spearman").iloc[0, 1]) for m in ("tr_v", "rms_v_he", "coh_v")}
# lowest decile of head signal budget among clean segments
R["rms_v_he_p05_p10_clean"] = [float(C.rms_v_he.quantile(0.05)), float(C.rms_v_he.quantile(0.10))]
# white noise sigma per axis at fs=100 Hz -> vertical projection keeps sigma; band 0.6-3 Hz keeps sqrt(2.4/50)
R["noise_bandrms"] = {str(s): float(s * np.sqrt(2.4 / 50.0)) for s in (0.05, 0.1, 0.2, 0.5, 1.0)}
json.dump(R, open(outp, "w"), indent=1)
f = lambda v: f"{v[0]:.2f} [{v[1]:.2f}, {v[2]:.2f}]"
for k, v in R["clean"].items():
    print(k, v.get("n_part"), v.get("n_seg"), {m: f(v[m]) for m in MEAS})
print({k: R[k] for k in ("n_segments", "n_clean", "n_participants_clean", "spearman_clean", "rms_v_he_p05_p10_clean", "noise_bandrms")})
