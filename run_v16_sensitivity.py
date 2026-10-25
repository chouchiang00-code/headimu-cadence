#!/usr/bin/env python3
"""V16 (secondary, SIMULATION): sensitivity of head-IMU cadence to sensor non-idealities, test set.

Usage: python run_v16_sensitivity.py PACK.npz RESULTS_V11 E2E_OUT OUT [--n N]
Perturbations (magnitudes justified in the manuscript supplement):
  acc_noise   white Gaussian noise added to each accelerometer axis, sigma 0.05 / 0.1 / 0.2 m/s^2 (RMS per axis)
  gyro_bias   constant bias vector of 1 / 5 / 10 deg/s in a random direction (median offset measured at rest in the
              Technoconcept head recordings of this dataset: 7.0 deg/s, Supplementary signal-verification table)
  fs          downsampling to 50 Hz and 25 Hz (anti-aliased polyphase), all time parameters unchanged in seconds
  drift       slowly varying mounting rotation: angle 0 -> 20 deg linearly over the trial about a random axis
Outcomes: reference-assisted A1 and A0 / A0g cadence errors (as in the primary analysis) and head-only B1 turn detection.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import resample_poly

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from headimu import dsp, endtoend as E, pipeline as pl  # noqa: E402
from headimu.io_voisard import Trial, SensorData  # noqa: E402


def rot_series(n, axis, max_deg):
    out = np.empty((n, 3, 3))
    for k, th in enumerate(np.linspace(0, np.deg2rad(max_deg), n)):
        out[k] = dsp.rotation_matrix(axis, th)
    return out


def main():
    pack, res11, e2e, out = map(Path, sys.argv[1:5])
    nmax = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 10 ** 9
    out.mkdir(parents=True, exist_ok=True)
    z = np.load(pack)
    meta = {m["trial"]: m for m in json.loads(str(z["__meta__"]))}
    qc = pd.read_csv(res11 / "qc_trials.csv")
    setof = dict(zip(qc["trial"], qc["set"]))
    cfg = json.loads((res11 / "config_used.json").read_text(encoding="utf-8"))
    cal = json.loads((res11 / "dev_calibration.json").read_text(encoding="utf-8"))
    P = json.loads((e2e / "endtoend_params.json").read_text(encoding="utf-8"))["params"] if (e2e / "endtoend_params.json").exists() else dict(E.PARAMS)
    band_lo, lags = float(cal["band_lo_hz"]), cal["lags_s"]
    rng = np.random.default_rng(20261023)
    tests = [t for t in meta if setof.get(t) == "test"][:nmax]
    rows = []
    for t in tests:
        m = meta[t]
        acc0, gyr0, valid0 = z[f"{t}|acc"].astype(float), z[f"{t}|gyr"].astype(float), z[f"{t}|valid"]
        hsl, hsr, turn = z[f"{t}|ref_hs_left"], z[f"{t}|ref_hs_right"], z[f"{t}|ref_turn"]
        conds = [("none", 0.0, acc0, gyr0, valid0, 100.0)]
        for s in (0.05, 0.1, 0.2):
            conds.append(("acc_noise", s, acc0 + rng.normal(0, s, acc0.shape), gyr0, valid0, 100.0))
        for b in (1.0, 5.0, 10.0):
            u = dsp.random_unit(rng)[0]
            conds.append(("gyro_bias", b, acc0, gyr0 + np.deg2rad(b) * u, valid0, 100.0))
        for f in (50.0, 25.0):
            q = int(100 / f)
            a = resample_poly(acc0, 1, q, axis=0); g = resample_poly(gyr0, 1, q, axis=0)
            conds.append(("fs", f, a, g, valid0[::q][:len(a)], f))
        R = rot_series(len(acc0), dsp.random_unit(rng)[0], 20.0)
        conds.append(("drift", 20.0, np.einsum("nij,nj->ni", R, acc0), np.einsum("nij,nj->ni", R, gyr0), valid0, 100.0))
        for name, lev, a, g, v, fs in conds:
            c2 = json.loads(json.dumps(cfg)); c2["fs_hz"] = fs
            tr = Trial(t, m["participant"], m["cohort"], str(m["visit"]), m["sensor_type"], m["age"], None, fs,
                       {"HE": SensorData(a, g, v, {})}, hsl, hsr, tuple(turn), {}, [])
            seg, _, _ = pl.evaluate_trial(tr, c2, band_lo, lags, [], 0, 0, ("HE",))
            for s in seg:
                if s["method"] in ("A0", "A0g", "A1"):
                    rows.append({"trial": t, "participant": m["participant"], "cohort": m["cohort"], "pert": name,
                                 "level": lev, "method": s["method"], "segment": s["segment"], "e_C": s.get("e_C", np.nan)})
            o = E.offline(a, g, v, fs, P)
            hit = [x for x in o["turns"] if x[0] < turn[1] and x[1] > turn[0]]
            rows.append({"trial": t, "participant": m["participant"], "cohort": m["cohort"], "pert": name, "level": lev,
                         "method": "B1_turn", "segment": "full", "turn_tp": int(bool(hit)),
                         "turn_fp": len(o["turns"]) - int(bool(hit))})
    df = pd.DataFrame(rows)
    df.to_csv(out / "sensitivity_rows.csv", index=False)
    cad = df[df["method"].isin(["A0", "A0g", "A1"])].copy()
    cad["abs"] = cad["e_C"].abs()
    summ = (cad.groupby(["pert", "level", "method", "participant"])["abs"].median()
            .groupby(["pert", "level", "method"]).median().unstack("method"))
    big = cad.assign(b=cad["abs"] > 5).groupby(["pert", "level", "method"])["b"].mean().unstack("method") * 100
    tt = df[df["method"] == "B1_turn"].groupby(["pert", "level"])[["turn_tp", "turn_fp"]].mean()
    summ.join(big, rsuffix="_big_pct").join(tt).to_csv(out / "sensitivity_summary.csv")
    print(summ.join(tt).round(3))


# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python run_v16_sensitivity.py PACK.npz RESULTS_V11 E2E_OUT OUT [--n N]')
        raise SystemExit(0)
    if len(sys.argv) < 5:
        print('Usage: python run_v16_sensitivity.py PACK.npz RESULTS_V11 E2E_OUT OUT [--n N]', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
