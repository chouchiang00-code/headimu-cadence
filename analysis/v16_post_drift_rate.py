#!/usr/bin/env python3
"""POST HOC (added after V16.2 review, SIMULATION): mounting drift with its own angular rate.

The V16 sensitivity run (run_v16_sensitivity.py) rotated acc and gyro by R(t) but did not add the angular velocity of
the drift itself to the gyroscope. Here the same trials, the same random axes (the random stream of the V16 run is
replayed draw for draw) and the same 0 -> 20 deg linear drift are evaluated twice:
  drift     R(t) applied to acc and gyro (as in V16)
  drift_w   as above, plus the drift angular rate theta_dot * u added to the gyro (rotation about a fixed axis u, so the
            rate vector is u in both frames); the tangential/centripetal acceleration of the drift is < 1e-4 m/s^2
            for a 2-3 cm offset and is ignored.
Also 'none'. Outputs per-segment rows and a summary (median over participants of median |e_C|, % |e_C| > 5,
B1 turn TP/FP) to OUT.
Usage: python analysis/v16_post_drift_rate.py PACK.npz RESULTS_V11 E2E_OUT OUT [--n N]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import resample_poly  # noqa: F401  (kept for parity with the V16 script)

HERE = Path(__file__).resolve().parent.parent
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
    P = json.loads((e2e / "endtoend_params.json").read_text(encoding="utf-8"))["params"]
    band_lo, lags = float(cal["band_lo_hz"]), cal["lags_s"]
    rng = np.random.default_rng(20261023)
    tests = [t for t in meta if setof.get(t) == "test"][:nmax]
    rows = []
    for t in tests:
        m = meta[t]
        acc0, gyr0, valid0 = z[f"{t}|acc"].astype(float), z[f"{t}|gyr"].astype(float), z[f"{t}|valid"]
        hsl, hsr, turn = z[f"{t}|ref_hs_left"], z[f"{t}|ref_hs_right"], z[f"{t}|ref_turn"]
        # replay the V16 random stream: 3 noise draws, 3 bias axes, then the drift axis
        for s in (0.05, 0.1, 0.2):
            rng.normal(0, s, acc0.shape)
        for _ in range(3):
            dsp.random_unit(rng)
        u = dsp.random_unit(rng)[0]
        n = len(acc0); fs = 100.0
        R = rot_series(n, u, 20.0)
        a_d = np.einsum("nij,nj->ni", R, acc0); g_d = np.einsum("nij,nj->ni", R, gyr0)
        rate = np.deg2rad(20.0) / ((n - 1) / fs)            # rad/s
        conds = [("none", acc0, gyr0), ("drift", a_d, g_d), ("drift_w", a_d, g_d + rate * u[None, :])]
        for name, a, g in conds:
            tr = Trial(t, m["participant"], m["cohort"], str(m["visit"]), m["sensor_type"], m["age"], None, fs,
                       {"HE": SensorData(a, g, valid0, {})}, hsl, hsr, tuple(turn), {}, [])
            seg, _, _ = pl.evaluate_trial(tr, cfg, band_lo, lags, [], 0, 0, ("HE",))
            for s in seg:
                if s["method"] in ("A0", "A0g", "A1"):
                    rows.append({"trial": t, "participant": m["participant"], "pert": name, "method": s["method"],
                                 "segment": s["segment"], "e_C": s.get("e_C", np.nan),
                                 "rate_dps": np.rad2deg(rate)})
            o = E.offline(a, g, valid0, fs, P)
            hit = [x for x in o["turns"] if x[0] < turn[1] and x[1] > turn[0]]
            rows.append({"trial": t, "participant": m["participant"], "pert": name, "method": "B1_turn",
                         "segment": "full", "turn_tp": int(bool(hit)), "turn_fp": len(o["turns"]) - int(bool(hit)),
                         "rate_dps": np.rad2deg(rate)})
    df = pd.DataFrame(rows)
    df.to_csv(out / "drift_rate_rows.csv", index=False)
    cad = df[df["method"].isin(["A0", "A0g", "A1"])].copy(); cad["abs"] = cad["e_C"].abs()
    summ = (cad.groupby(["pert", "method", "participant"])["abs"].median().groupby(["pert", "method"]).median()
            .unstack("method"))
    big = cad.assign(b=cad["abs"] > 5).groupby(["pert", "method"])["b"].mean().unstack("method") * 100
    tt = df[df["method"] == "B1_turn"].groupby("pert")[["turn_tp", "turn_fp"]].mean()
    S = summ.join(big, rsuffix="_big_pct").join(tt)
    S.to_csv(out / "drift_rate_summary.csv")
    # per-segment agreement with 'none'
    piv = cad.pivot_table(index=["trial", "segment", "method"], columns="pert", values="e_C").reset_index()
    agree = {}
    for meth in ("A0", "A0g", "A1"):
        p = piv[piv["method"] == meth]
        for c in ("drift", "drift_w"):
            d = (p[c] - p["none"]).abs()
            agree[f"{meth}|{c}"] = {"n": int(d.notna().sum()), "identical_frac": float((d < 1e-9).mean()),
                                   "gt0.5": int((d > 0.5).sum()), "max_abs_diff": float(d.max())}
    rr = df.drop_duplicates("trial")["rate_dps"]
    info = {"agreement_vs_none": agree, "drift_rate_dps_median": float(rr.median()),
            "drift_rate_dps_range": [float(rr.min()), float(rr.max())], "n_trials": int(len(tests))}
    (out / "drift_rate_summary.json").write_text(json.dumps(info, indent=1))
    print(S.round(3)); print(json.dumps(info, indent=1))


# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v16_post_drift_rate.py PACK.npz RESULTS_V11 E2E_OUT OUT [--n N]')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

if __name__ == "__main__":
    main()
