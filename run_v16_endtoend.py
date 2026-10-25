#!/usr/bin/env python3
"""V16 task 1: end-to-end head-only cadence (B0 reference-assisted, B1 head-only offline, B2 head-only causal).

Usage: python run_v16_endtoend.py PACK.npz RESULTS_V11 OUT [--jobs N]
- B0 is recomputed with the unchanged primary pipeline and checked against results_v11/test_segments.csv.
- The only parameters selected here (walking-detection thresholds of B1 and B2, and the B2 event lag used for matching)
  are selected on DEVELOPMENT participants; all other parameters are fixed in headimu/endtoend.py.
- Reference heel strikes and turn boundaries enter only the evaluation functions.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from headimu import endtoend as E  # noqa: E402
from headimu import pipeline as pl  # noqa: E402
from headimu.io_voisard import Trial, SensorData  # noqa: E402

FS = 100.0
TOL = 0.15


def load_pack(path):
    z = np.load(path, allow_pickle=False)
    meta = {m["trial"]: m for m in json.loads(str(z["__meta__"]))}
    return z, meta


def get(z, t):
    hs = np.sort(np.concatenate([z[f"{t}|ref_hs_left"], z[f"{t}|ref_hs_right"]]))
    return z[f"{t}|acc"].astype(float), z[f"{t}|gyr"].astype(float), z[f"{t}|valid"], hs, z[f"{t}|ref_turn"]


# ----------------------------------------------------------------------------- B0 (unchanged primary pipeline)
def b0_trial(args):
    t, acc, gyr, valid, hsl, hsr, turn, m, cfg, band_lo, lags = args
    tr = Trial(t, m["participant"], m["cohort"], str(m["visit"]), m["sensor_type"], m["age"], None, FS,
               {"HE": SensorData(acc, gyr, valid, {})}, hsl, hsr, tuple(turn), {}, [])
    seg, _, _ = pl.evaluate_trial(tr, cfg, band_lo, lags, [], 0, 0, ("HE",))
    return seg


# ----------------------------------------------------------------------------- B1/B2 per trial
def headonly_trial(args):
    t, acc, gyr, valid, hs, turn, P = args
    o = E.offline(acc, gyr, valid, FS, P)
    c = E.causal(acc, gyr, valid, FS, P)
    return t, o, c, hs, turn, len(acc)


def walking_f1_offline(o, thr, P, hs, n):
    """Re-threshold the stored centred RMS (dev tuning without recomputing the filters)."""
    walk = E._fill_gaps(o["rms"] > thr, int(P["gap_fill_s"] * FS))
    bouts = [(a / FS, b / FS) for a, b in E._runs(walk) if (b - a) / FS >= P["min_bout_s"]]
    return E.interval_prf(bouts, [(hs[0], hs[-1])], n, FS)[2]


def walking_state(rms, thr_on, P):
    n = len(rms)
    on_h, off_h = int(P["on_hold_s"] * FS), int(P["off_hold_s"] * FS)
    thr_off = thr_on * P["hyst"]
    st, cnt, w = False, 0, np.zeros(n, bool)
    for k in range(n):
        if not st:
            cnt = cnt + 1 if rms[k] > thr_on else 0
            if cnt >= on_h:
                st, cnt = True, 0
        else:
            cnt = cnt + 1 if rms[k] < thr_off else 0
            if cnt >= off_h:
                st, cnt = False, 0
        w[k] = st
    return w


def bouts_from_mask(w):
    return [(a / FS, b / FS) for a, b in E._runs(w)]


def evaluate(t, o, c, hs, turn, n, P, lag_b1, lag_b2):
    ref_segs = {"S1": (hs[0], turn[0]), "S2": (turn[1], hs[-1])}
    rows, trow = [], {"trial": t}
    # walking detection
    trow["B1_walk_p"], trow["B1_walk_r"], trow["B1_walk_f1"] = E.interval_prf(o["bouts"], [(hs[0], hs[-1])], n, FS)
    trow["B2_walk_p"], trow["B2_walk_r"], trow["B2_walk_f1"] = E.interval_prf(bouts_from_mask(c["walking"]),
                                                                              [(hs[0], hs[-1])], n, FS)
    # turn detection (B1): a detected turn matches the reference turn if they overlap
    tp = [x for x in o["turns"] if x[0] < turn[1] and x[1] > turn[0]]
    trow["B1_turn_tp"] = int(len(tp) > 0)
    trow["B1_turn_fp"] = len(o["turns"]) - min(1, len(tp))
    trow["B1_turn_fn"] = int(len(tp) == 0)
    if tp:
        best = max(tp, key=lambda x: min(x[1], turn[1]) - max(x[0], turn[0]))
        trow["B1_turn_start_err"], trow["B1_turn_end_err"] = best[0] - turn[0], best[1] - turn[1]
    # causal turn events (B2)
    on = [tt for e, tt in c["events"] if e == "turn_on"]
    off = [tt for e, tt in c["events"] if e == "turn_off"]
    m_on = [x for x in on if turn[0] - 1.0 <= x <= turn[1]]
    trow["B2_turn_tp"] = int(len(m_on) > 0)
    trow["B2_turn_fp"] = len([x for x in on if x < hs[0] or x > hs[-1] or not (turn[0] - 1.0 <= x <= turn[1])])
    trow["B2_turn_fn"] = int(len(m_on) == 0)
    if m_on:
        trow["B2_turn_on_delay"] = m_on[0] - turn[0]
        o2 = [x for x in off if x > m_on[0]]
        if o2:
            trow["B2_turn_off_delay"] = o2[0] - turn[1]
    # latency of causal walking onset and first cadence output
    won = [tt for e, tt in c["events"] if e == "walk_on"]
    trow["B2_walk_on_delay"] = (won[0] - hs[0]) if won else np.nan
    outs = c["outputs"]
    trow["B2_first_output_delay"] = (outs[0, 0] - hs[0]) if len(outs) else np.nan
    # step detection
    for name, ev, lag in (("B1", o["peaks"], lag_b1), ("B2", c["peaks"], lag_b2)):
        k, nd, nr, d = E.match_events(np.asarray(ev) - lag, hs, TOL)
        trow[f"{name}_step_tp"], trow[f"{name}_step_nd"], trow[f"{name}_step_nr"] = k, nd, nr
    k, nd, nr, d = E.match_events(c["confirm"] - lag_b2, hs, TOL)
    # confirmation latency = time from reference heel strike to confirmation of its matched step
    kk, _, _, dd = E.match_events(c["peaks"] - lag_b2, hs, TOL)
    trow["B2_confirm_latency"] = float(lag_b2 + P["confirm_s"] + np.median(dd)) if kk else np.nan
    # segment-level cadence
    for sname, (a, b) in ref_segs.items():
        cref = E.ref_cadence(hs, a, b)
        r = {"trial": t, "segment": sname, "C_ref": cref, "seg_dur": b - a}
        # B1: head-only segment with the largest overlap (>= 1 s)
        ov = [(min(s["t1"], b) - max(s["t0"], a), s) for s in o["segments"]]
        ov = [x for x in ov if x[0] >= 1.0]
        if ov:
            s = max(ov, key=lambda x: x[0])[1]
            r.update(B1_C=s["cadence"], B1_t0=s["t0"], B1_t1=s["t1"])
        else:
            r.update(B1_C=np.nan)
        sel = outs[(outs[:, 0] >= a) & (outs[:, 0] <= b + P["confirm_s"])] if len(outs) else np.zeros((0, 3))
        r["B2_C"] = float(np.median(sel[:, 1])) if len(sel) else np.nan
        r["B2_C_last"] = float(sel[-1, 1]) if len(sel) else np.nan
        r["B2_n_out"] = len(sel)
        # continuous causal error against the running reference cadence over the same number of intervals
        errs = []
        for tt, cc, _ in sel:
            rr = hs[(hs >= a) & (hs <= tt)]
            iv = np.diff(rr[-(P["k_iv"] + 1):])
            if len(iv) >= P["min_iv"]:
                errs.append(cc - 60.0 / np.median(iv))
        r["B2_cont_mae"] = float(np.mean(np.abs(errs))) if errs else np.nan
        rows.append(r)
    return rows, trow


def main():
    pack, res11, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 1
    out.mkdir(parents=True, exist_ok=True)
    z, meta = load_pack(pack)
    qc = pd.read_csv(res11 / "qc_trials.csv")
    setof = dict(zip(qc["trial"], qc["set"]))
    cfg = json.loads((res11 / "config_used.json").read_text(encoding="utf-8"))
    cal = json.loads((res11 / "dev_calibration.json").read_text(encoding="utf-8"))
    band_lo, lags = float(cal["band_lo_hz"]), cal["lags_s"]
    trials = [t for t in meta if t in setof]
    print(f"{len(trials)} trials in pack ({sum(setof[t] == 'test' for t in trials)} test)")
    pmap = (lambda f, it: list(ProcessPoolExecutor(jobs).map(f, it, chunksize=8))) if jobs > 1 else (lambda f, it: [f(x) for x in it])

    # ---- B0
    b0 = pmap(b0_trial, [(t, *[z[f"{t}|{k}"].astype(float) if k in ("acc", "gyr") else z[f"{t}|{k}"]
                                for k in ("acc", "gyr", "valid", "ref_hs_left", "ref_hs_right", "ref_turn")],
                          meta[t], cfg, band_lo, lags) for t in trials])
    b0 = pd.DataFrame(sum(b0, []))
    b0["set"] = b0["trial"].map(setof)
    b0.to_csv(out / "b0_segments_all.csv", index=False)
    v15 = pd.read_csv(res11 / "test_segments.csv")
    v15 = v15[v15["loc"] == "HE"]
    cmp = b0.merge(v15[["trial", "method", "segment", "e_C"]], on=["trial", "method", "segment"], suffixes=("", "_v15"))
    diff = (cmp["e_C"] - cmp["e_C_v15"]).abs()
    check = {"n_compared": int(len(cmp)), "max_abs_diff": float(np.nanmax(diff)) if len(cmp) else None,
             "n_nan_mismatch": int((cmp["e_C"].isna() != cmp["e_C_v15"].isna()).sum())}
    print("B0 reproduction check vs V15:", check)

    # ---- B1/B2 signals (default thresholds), then dev tuning of the walking thresholds
    P = dict(E.PARAMS)
    res = pmap(headonly_trial, [(t, *get(z, t)[:3], get(z, t)[3], get(z, t)[4], P) for t in trials])
    dev = [r for r in res if setof[r[0]] == "dev"]
    grid = np.round(np.concatenate([np.arange(0.02, 0.2, 0.02), np.arange(0.2, 1.81, 0.1)]), 2)  # extended downward after the first dev run selected the grid edge (0.2)
    part = {t: meta[t]["participant"] for t in trials}
    tune = []
    for thr in (grid if dev else []):
        f1 = [(part[t], walking_f1_offline(o, thr, P, hs, n)) for t, o, c, hs, turn, n in dev]
        f2 = [(part[t], E.interval_prf(bouts_from_mask(walking_state(c["rms"], thr, P)), [(hs[0], hs[-1])], n, FS)[2])
              for t, o, c, hs, turn, n in dev]
        tune.append({"thr": thr, "B1_dev_f1": pd.DataFrame(f1).groupby(0)[1].mean().mean(),
                     "B2_dev_f1": pd.DataFrame(f2).groupby(0)[1].mean().mean()})
    tune = pd.DataFrame(tune, columns=["thr", "B1_dev_f1", "B2_dev_f1"])
    tune.to_csv(out / "dev_tuning_walking.csv", index=False)
    if tune["B1_dev_f1"].notna().any():
        P["thr_walk"] = float(tune.loc[tune["B1_dev_f1"].idxmax(), "thr"])
        P["thr_on"] = float(tune.loc[tune["B2_dev_f1"].idxmax(), "thr"])
    print("dev-selected thresholds:", P["thr_walk"], P["thr_on"])
    res = pmap(headonly_trial, [(t, *get(z, t)[:3], get(z, t)[3], get(z, t)[4], P) for t in trials])
    # dev lags for event matching (median signed difference within 0.4 s)
    def lag_of(key):
        d = []
        for t, o, c, hs, turn, n in res:
            if setof[t] != "dev":
                continue
            ev = o["peaks"] if key == "B1" else c["peaks"]
            for h in hs:
                x = ev - h
                x = x[np.abs(x) <= 0.4]
                if x.size:
                    d.append(x[np.argmin(np.abs(x))])
        return float(np.median(d)) if d else 0.0
    lag_b1, lag_b2 = lag_of("B1"), lag_of("B2")
    print("dev lags:", lag_b1, lag_b2)
    segs, trs = [], []
    for t, o, c, hs, turn, n in res:
        r, tr = evaluate(t, o, c, hs, turn, n, P, lag_b1, lag_b2)
        segs += r
        trs.append(tr)
    segs = pd.DataFrame(segs)
    trs = pd.DataFrame(trs)
    m = pd.DataFrame(meta.values())[["trial", "participant", "cohort", "visit", "sensor_type", "age", "vga"]]
    b0a1 = b0[b0["method"] == "A1"][["trial", "segment", "C_imu", "C_ref"]].rename(columns={"C_imu": "B0_C", "C_ref": "B0_Cref"})
    segs = segs.merge(b0a1, on=["trial", "segment"], how="left").merge(m, on="trial", how="left")
    segs["set"] = segs["trial"].map(setof)
    trs = trs.merge(m, on="trial", how="left")
    trs["set"] = trs["trial"].map(setof)
    for k in ("B0", "B1", "B2"):
        segs[f"{k}_e"] = segs[f"{k}_C"] - segs["C_ref"]
    segs.to_csv(out / "endtoend_segments.csv", index=False)
    trs.to_csv(out / "endtoend_trials.csv", index=False)
    P.update(lag_b1=lag_b1, lag_b2=lag_b2)
    (out / "endtoend_params.json").write_text(json.dumps({"params": P, "b0_check": check}, indent=1), encoding="utf-8")
    print("done:", len(segs), "segments")


# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python run_v16_endtoend.py PACK.npz RESULTS_V11 OUT [--jobs N]')
        raise SystemExit(0)
    if len(sys.argv) < 4:
        print('Usage: python run_v16_endtoend.py PACK.npz RESULTS_V11 OUT [--jobs N]', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
