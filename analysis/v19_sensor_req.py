#!/usr/bin/env python3
"""V19 (SIMULATION on recorded signals, test set, head): sensor requirements for the frozen AGS estimator.
Each perturbation degrades the recorded head accelerometer signal; the reference is unchanged. Nothing is re-tuned:
all detector and AGS parameters are in seconds and stay frozen.
  fs        output data rate 100 (as recorded), 50, 25, 20 Hz  (anti-aliased polyphase decimation)
  noise     white Gaussian noise added per axis, sigma 0.05, 0.1, 0.2, 0.5, 1.0 m/s^2 (at 100 Hz)
  lsb       quantisation step of the accelerometer output 0.01, 0.05, 0.1, 0.2, 0.5 m/s^2
            (16-bit at +-8 g = 0.0024; 12-bit at +-8 g = 0.038; 8-bit at +-4 g = 0.31; 8-bit at +-8 g = 0.61 m/s^2)
  range     per-axis saturation at +-1.5 g and +-2 g
  lowpower  25 Hz and 8-bit at +-4 g together
  accel-only head-only pipeline: B1 without the gyroscope, i.e. no turn removal (the whole walking bout is one segment)
Outputs: per-segment rows and a summary with participant-bootstrap CIs; timing of AGS per segment.
Usage: python analysis/v19_sensor_req.py HEAD_PACK RESULTS_V11 B1_SEGMENTS_CSV OUT_DIR"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from scipy.signal import resample_poly
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from analysis import v18_methods as M  # noqa: E402
from headimu import endtoend as E  # noqa: E402
from headimu.features import signals  # noqa: E402
from headimu.evaluate import windows, _intervals  # noqa: E402
from headimu.io_voisard import Trial, SensorData  # noqa: E402

G0 = 9.80665
# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v19_sensor_req.py HEAD_PACK RESULTS_V11 B1_SEGMENTS_CSV OUT_DIR')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

pack, r11, b1csv, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)
cfg = json.loads((r11 / "config_used.json").read_text(encoding="utf-8"))
cal = json.loads((r11 / "dev_calibration.json").read_text(encoding="utf-8"))
band_lo, lag = float(cal["band_lo_hz"]), cal["lags_s"]["HE_A1"]
qc = pd.read_csv(r11 / "qc_trials.csv"); setof = dict(zip(qc["trial"], qc["set"]))
z = np.load(pack); meta = {m["trial"]: m for m in json.loads(str(z["__meta__"]))}
tests = [t for t in meta if setof.get(t) == "test"][:int(__import__("os").environ.get("NMAX", 10**9))]
rng = np.random.default_rng(20261113)


def quant(a, q):
    return np.round(a / q) * q


def conditions(acc, valid):
    c = [("reference", 0, acc, valid, 100.0)]
    for f in (50, 25, 20):
        k = 100 // f
        c.append(("fs", f, resample_poly(acc, 1, k, axis=0), valid[::k], float(f)))
    for s in (0.05, 0.1, 0.2, 0.5, 1.0):
        c.append(("noise", s, acc + rng.normal(0, s, acc.shape), valid, 100.0))
    for q in (0.01, 0.05, 0.1, 0.2, 0.5):
        c.append(("lsb", q, quant(acc, q), valid, 100.0))
    for g in (1.5, 2.0):
        c.append(("range", g, np.clip(acc, -g * G0, g * G0), valid, 100.0))
    a25 = resample_poly(acc, 1, 4, axis=0)
    c.append(("lowpower", "25Hz+8bit4g", quant(np.clip(a25, -4 * G0, 4 * G0), 8 * G0 / 256), valid[::4], 25.0))
    return c


rows, timing, peak_g = [], [], []
t_start = time.time()
for n_t, t in enumerate(tests):
    m = meta[t]
    acc0 = np.nan_to_num(z[f"{t}|acc"].astype(float)); gyr0 = z[f"{t}|gyr"].astype(float); valid0 = z[f"{t}|valid"]
    hsl, hsr, turn = z[f"{t}|ref_hs_left"], z[f"{t}|ref_hs_right"], z[f"{t}|ref_turn"]
    tr = Trial(t, m["participant"], m["cohort"], str(m["visit"]), m["sensor_type"], m["age"], None, 100.0,
               {"HE": SensorData(acc0, gyr0, valid0, {})}, hsl, hsr, tuple(turn), {}, [])
    w = windows(tr, 100.0, cfg["detect"]["window_pad_s"])
    if w is None:
        continue
    peak_g.append(float(np.nanmax(np.abs(acc0[valid0])) / G0) if valid0.any() else np.nan)
    for pert, lev, acc, valid, fs in conditions(acc0, valid0):
        x = signals(acc, np.zeros_like(acc), fs, cfg, band_lo)["A1"]
        i0, i1 = max(0, int(w["full"][0] * fs)), min(len(valid), int(w["full"][1] * fs))
        c_all = M.base_peaks(x, fs, cfg, i0, i1, valid)
        for sname, (a, b) in w["segs"].items():
            r = tr.hs[(tr.hs >= a) & (tr.hs <= b)]
            if len(r) < cfg["metrics"]["min_ref_intervals"] + 1:
                continue
            ri = np.diff(r)
            c = M.seg_peaks(c_all, lag, a, b); iv = _intervals(np.asarray(c) + lag, valid, fs)
            t0 = time.perf_counter()
            ags, info = M.ags_cadence(x, fs, cfg, i0, i1, valid, lag, a, b)
            if pert == "reference":
                timing.append({"dur_s": b - a, "ms": 1000 * (time.perf_counter() - t0)})
            rows.append({"trial": t, "participant": m["participant"], "cohort": m["cohort"], "segment": sname,
                         "pert": pert, "level": str(lev), "R_step": 60 / np.median(ri), "R_stride": M.stride_cadence(ri),
                         "C_peak": 60 / np.median(iv) if len(iv) >= 2 else np.nan, "C_ags": ags,
                         "C_stride": M.stride_cadence(iv) if len(iv) >= 3 else np.nan,
                         "C_ac": 60.0 / info["T"] if np.isfinite(info["T"]) else np.nan})
    # accelerometer-only head-only pipeline: no turn removal; the whole bout is the segment (100 Hz and 25 Hz)
    P = dict(E.PARAMS); P["q_thr_dps"] = 1e9
    for fsb in (100, 25):
      kk = 100 // fsb
      accb, validb = (acc0, valid0) if kk == 1 else (resample_poly(acc0, 1, kk, axis=0), valid0[::kk])
      o = E.offline(accb, np.zeros_like(accb), validb, float(fsb), P)
      xa = o["a1"]
      for sname, (a, b) in w["segs"].items():
            r = tr.hs[(tr.hs >= a) & (tr.hs <= b)]
            if len(r) < cfg["metrics"]["min_ref_intervals"] + 1:
                continue
            ov = [(min(b, y) - max(a, x_), x_, y) for x_, y in o["bouts"]]
            ov = [v for v in ov if v[0] >= 1.0]
            if not ov:
                cad = np.nan
            else:
                _, x_, y = max(ov)
                cad = M.ags_cadence(xa, float(fsb), {"detect": {"prominence_floor_mps2": 0.12, "prominence_k_sigma": 1.5,
                                                             "min_peak_distance_s": 0.30}},
                                    max(0, int((x_ - 1) * fsb)), min(len(xa), int((y + 1) * fsb)), validb, 0.0, x_, y)[0]
            rows.append({"trial": t, "participant": m["participant"], "cohort": m["cohort"], "segment": sname,
                         "pert": "accel_only_B1", "level": f"no turn removal {fsb} Hz", "R_step": 60 / np.median(np.diff(r)),
                         "R_stride": M.stride_cadence(np.diff(r)), "C_peak": np.nan, "C_ags": cad})
    if n_t % 100 == 0:
        print(f"{n_t}/{len(tests)} {time.time() - t_start:.0f}s", flush=True)

D = pd.DataFrame(rows)
# B1 with the gyroscope (published turn removal), AGS over each B1 segment, for the same reference segments
B1 = pd.read_csv(b1csv)[["trial", "segment", "participant", "cohort", "C_ref", "B1_ags"]]
D = pd.concat([D, B1.rename(columns={"C_ref": "R_step", "B1_ags": "C_ags"}).assign(pert="gyro_B1", level="turn removal")],
              ignore_index=True)
D.to_csv(out / "v19_sensor_req_rows.csv", index=False)

B = 2000
brng = np.random.default_rng(20261114)


def summ(d, k):
    e = (d[k] - d.R_step).abs()
    pmed = e.groupby(d.participant).median().dropna()
    big = ((e > 5) | d[k].isna()).groupby(d.participant)
    num, den = big.sum(), big.size()
    parts = pmed.index.to_numpy()
    bm, bb = [], []
    P = num.index.to_numpy()
    for _ in range(B):
        s = brng.choice(P, len(P))
        bb.append(100 * num[s].sum() / den[s].sum())
        s2 = brng.choice(parts, len(parts)); bm.append(np.median(pmed[s2]))
    return {"med": [float(pmed.median()), float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))],
            "big_or_none": [float(100 * num.sum() / den.sum()), float(np.percentile(bb, 2.5)), float(np.percentile(bb, 97.5))],
            "none_pct": float(100 * d[k].isna().mean()), "n": int(len(d))}


S = {}
for (pert, lev), d in D.groupby(["pert", "level"], sort=False):
    S[f"{pert}|{lev}"] = {"AGS": summ(d, "C_ags")}
    if d.C_peak.notna().any():
        S[f"{pert}|{lev}"]["peak"] = summ(d, "C_peak")
        S[f"{pert}|{lev}"]["stride"] = summ(d, "C_stride")
        S[f"{pert}|{lev}"]["ac"] = summ(d, "C_ac")
    S[f"{pert}|{lev}"]["CVA_big_or_none_AGS"] = float(100 * (((d.C_ags - d.R_step).abs() > 5) | d.C_ags.isna())[d.cohort == "CVA"].mean())
T = pd.DataFrame(timing)
S["timing"] = {"ms_per_segment_median": float(T.ms.median()), "ms_p95": float(T.ms.quantile(0.95)),
               "segment_s_median": float(T.dur_s.median()), "python": sys.version.split()[0]}
S["head_peak_abs_acc_g_quantiles"] = [float(np.nanpercentile(peak_g, q)) for q in (50, 90, 99, 100)]
(out / "v19_sensor_req.json").write_text(json.dumps(S, indent=1))
for k, v in S.items():
    if "|" in k:
        a = v["AGS"]
        print(f"{k:32s} AGS med {a['med'][0]:.2f} [{a['med'][1]:.2f},{a['med'][2]:.2f}]  big/none {a['big_or_none'][0]:.1f} "
              f"[{a['big_or_none'][1]:.1f},{a['big_or_none'][2]:.1f}] none {a['none_pct']:.1f}  CVA {v['CVA_big_or_none_AGS']:.1f}"
              + (f" | peak med {v['peak']['med'][0]:.2f} big {v['peak']['big_or_none'][0]:.1f}" if "peak" in v else ""))
print(S["timing"], S["head_peak_abs_acc_g_quantiles"])
