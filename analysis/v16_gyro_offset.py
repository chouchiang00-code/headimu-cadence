#!/usr/bin/env python3
"""V16 failure analysis: uncalibrated head-gyroscope offsets and missing head-only (B1) output.

Usage: python v16_gyro_offset.py PACK.npz RESULTS_V11 E2E_DIR
For every packed trial, over the standing period at the start of the trial (HE_static_s from results_v11/qc_trials.csv, i.e. up to
0.5 s before the first reference heel strike; 0.5 s when that period is shorter than 0.5 s):
  off       = |mean angular-rate vector| (deg/s)
  q_static  = median apparent turning rate q = |omega . g_hat| (deg/s), g_hat = 0.3-Hz low-pass gravity direction
              (the signal that the head-only turn gate thresholds at 30 deg/s)
  qc_bias   = HE_static_gyr_bias_dps of the V11 signal check (for comparison)
Writes E2E_DIR/static_gyro_offsets.csv and E2E_DIR/gyro_offset_summary.json (test set: trials with q_static > 30 deg/s,
their cohort/sensor mix, and missing-output rates of B1 at trial and segment level).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from headimu import dsp  # noqa: E402


def main():
    pack, res11, e2e = map(Path, sys.argv[1:4])
    z = np.load(pack)
    meta = {m["trial"]: m for m in json.loads(str(z["__meta__"]))}
    qc = pd.read_csv(res11 / "qc_trials.csv").set_index("trial")
    rows = []
    for t in meta:
        acc, gyr = z[f"{t}|acc"].astype(float), z[f"{t}|gyr"].astype(float)
        hs0 = min(np.r_[z[f"{t}|ref_hs_left"], z[f"{t}|ref_hs_right"]])
        # standing period = start of trial to 0.5 s before the first heel strike (as in the V11 signal check),
        # but at least 0.5 s (the V11 check falls back to 1.0 s, which may include the first step)
        n = int(round(qc.loc[t, "HE_static_s"] * 100)) if hs0 - 0.5 >= 0.5 else 50
        g = dsp.gravity_dir(acc, 100.0, 0.3)
        q = np.rad2deg(np.abs(np.einsum("ij,ij->i", gyr, g)))
        rows.append({"trial": t, "sensor": meta[t]["sensor_type"], "off": float(np.linalg.norm(np.rad2deg(gyr[:n]).mean(0))),
                     "q_static": float(np.median(q[:n])), "qc_bias": float(qc.loc[t, "HE_static_gyr_bias_dps"])})
    g = pd.DataFrame(rows)
    g.to_csv(e2e / "static_gyro_offsets.csv", index=False)

    s = pd.read_csv(e2e / "endtoend_segments.csv")
    s = s[(s["set"] == "test") & np.isfinite(s["C_ref"])].merge(g[["trial", "q_static"]], on="trial")
    s["hi"] = s["q_static"] > 30
    s["miss"] = ~np.isfinite(s["B1_e"])
    t = s.groupby("trial").agg(hi=("hi", "first"), miss=("miss", "any"), cohort=("cohort", "first"),
                               sensor=("sensor_type", "first"))
    hs = s[s["cohort"] == "HS"]
    out = {
        "n_test_trials": int(len(t)), "n_trials_q_static_gt30": int(t["hi"].sum()),
        "cohorts_of_these": t[t["hi"]]["cohort"].value_counts().to_dict(),
        "sensors_of_these": t[t["hi"]]["sensor"].value_counts().to_dict(),
        "trial_missing_rate_hi_pct": 100 * float(t[t["hi"]]["miss"].mean()),
        "trial_missing_rate_other_pct": 100 * float(t[~t["hi"]]["miss"].mean()),
        "n_trials_with_missing": int(t["miss"].sum()), "n_trials_with_missing_hi": int(t[t["hi"]]["miss"].sum()),
        "n_segments_missing": int(s["miss"].sum()), "n_segments_missing_hi": int(s[s["hi"]]["miss"].sum()),
        "HS_segment_missing_pct": 100 * float(hs["miss"].mean()),
        "HS_segment_missing_pct_without_hi": 100 * float(hs[~hs["hi"]]["miss"].mean()),
        "median_off_by_sensor_dps": g.groupby("sensor")["off"].median().round(2).to_dict(),
    }
    (e2e / "gyro_offset_summary.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/v16_gyro_offset.py PACK.npz RESULTS_V11 E2E_DIR')
        raise SystemExit(0)
    if len(sys.argv) < 4:
        print('Usage: python analysis/v16_gyro_offset.py PACK.npz RESULTS_V11 E2E_DIR', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
