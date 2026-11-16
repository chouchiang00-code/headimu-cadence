#!/usr/bin/env python3
"""V18 extended per-segment table for the ablation, failure mechanisms and operating envelope (B0 straight segments).
Per segment and location:
  reference : R_step (60/median step), R_stride (120/median stride), ref_suspect, ref_ratio (median of the shorter
              / longer of the odd and even reference step intervals; 1 = symmetric)
  estimators: C_peak (published), C_peak_stride, C_g_step (guided peaks, median step), C_g_stride (guided peaks,
              median stride), C_ac, C_ags  -> component ablation
  head-observable quantities (no reference): T (autocorrelation step time), sr (step regularity), amp (RMS of the
              band-passed |a| in the segment), imu_ratio (shorter/longer of odd and even guided-peak intervals)
  matching of the published peaks to the reference (0.15 s): prec, rec; fp_intra = share of unmatched peaks lying
              0.15-0.6 T after the previous reference heel strike (a second peak inside the same step)
Usage: python analysis/v18_ext.py RESULTS_V11 OUT --root ROOT --set dev|test --locs HE,LB [--jobs N]
       python analysis/v18_ext.py RESULTS_V11 OUT --pack PACK --set dev|test --locs HE"""
from __future__ import annotations
import json, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from analysis import v17_reviewer_checks as rc  # noqa: E402
from analysis import v18_methods as M  # noqa: E402
from headimu import pipeline as pl  # noqa: E402
from headimu.features import signals, _regularity  # noqa: E402
from headimu.evaluate import _intervals, matching_metrics, match_events  # noqa: E402

ARGS = {}


def _init(mode, src, cfg, cal, locs):
    rc._init(mode, src, cfg); ARGS.update(cfg=cfg, cal=cal, locs=locs)


def _ratio(iv):
    if len(iv) < 4:
        return np.nan
    a, b = np.median(iv[0::2]), np.median(iv[1::2])
    return float(min(a, b) / max(a, b))


def _w(t):
    cfg, cal, locs = ARGS["cfg"], ARGS["cal"], ARGS["locs"]
    tr = rc._load(t); fs = tr.fs
    w = pl.windows(tr, fs, cfg["detect"]["window_pad_s"])
    if w is None:
        return []
    rows = []
    for loc in locs:
        s = tr.sensors.get(loc)
        if s is None:
            continue
        x = signals(s.acc, s.gyr, fs, cfg, float(cal["band_lo_hz"]))["A1"]
        valid = s.valid; lag = cal["lags_s"].get(f"{loc}_A1", 0.0)
        i0, i1 = max(0, int(w["full"][0] * fs)), min(len(valid), int(w["full"][1] * fs))
        c_all = M.base_peaks(x, fs, cfg, i0, i1, valid)
        for sname, (a, b) in w["segs"].items():
            r = tr.hs[(tr.hs >= a) & (tr.hs <= b)]
            if len(r) < cfg["metrics"]["min_ref_intervals"] + 1:
                continue
            ri = np.diff(r)
            ev = sorted([(u, 0) for u in tr.hs_left if a <= u <= b] + [(u, 1) for u in tr.hs_right if a <= u <= b])
            ff = np.array([e[1] for e in ev])
            c = M.seg_peaks(c_all, lag, a, b); iv = _intervals(np.asarray(c) + lag, valid, fs)
            T = M.ac_step(x, fs, a, b)
            if T == T:
                md = float(np.clip(M.AGS_MINDIST_FRAC * T, *M.AGS_MINDIST_CLIP))
                cg = M.seg_peaks(M.base_peaks(x, fs, cfg, i0, i1, valid, min_dist=md), lag, a, b)
            else:
                cg = c
            ivg = _intervals(np.asarray(cg) + lag, valid, fs)
            ags, _ = M.ags_cadence(x, fs, cfg, i0, i1, valid, lag, a, b)
            j0, j1 = int(a * fs), int(b * fs)
            sr = _regularity(x[j0:j1], fs, cfg)[0] if j1 - j0 >= int(2 * cfg["autocorr"]["max_lag_s"] * fs) else np.nan
            mm = matching_metrics(c, r, 0.15)
            pairs = match_events(np.asarray(c), np.asarray(r), 0.15); used = {i for i, _, _ in pairs}
            fp = [c[i] for i in range(len(c)) if i not in used]
            Tr = np.median(ri)
            intra = [((u - r[r <= u].max()) / Tr) for u in fp if (r <= u).any()]
            rows.append({"trial": t, "participant": tr.participant, "cohort": tr.cohort, "loc": loc, "segment": sname,
                         "n_ref": int(len(r)), "n_c": int(len(c)), "n_g": int(len(cg)),
                         "R_step": 60 / Tr, "R_stride": M.stride_cadence(ri), "ref_ratio": _ratio(ri),
                         "ref_suspect": bool((np.diff(ff) == 0).sum() >= 1 or ri.max() / Tr >= 1.6),
                         "C_peak": 60 / np.median(iv) if len(iv) >= 2 else np.nan, "C_peak_stride": M.stride_cadence(iv),
                         "C_g_step": 60 / np.median(ivg) if len(ivg) >= 2 else np.nan, "C_g_stride": M.stride_cadence(ivg),
                         "C_ac": 60 / T if T == T else np.nan, "C_ags": ags, "T": T, "sr": sr,
                         "amp": float(np.sqrt(np.mean(x[j0:j1] ** 2))), "imu_ratio": _ratio(ivg),
                         "prec": mm["precision"], "rec": mm["recall"], "n_fp": len(fp),
                         "fp_intra": float(np.mean([0.15 <= q <= 0.6 for q in intra])) if intra else np.nan})
    return rows


def main():
    a = sys.argv[1:]
    r11, out = Path(a[0]), Path(a[1]); out.mkdir(parents=True, exist_ok=True)
    split = a[a.index("--set") + 1]; locs = a[a.index("--locs") + 1].split(",")
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 1
    mode, src = ("pack", a[a.index("--pack") + 1]) if "--pack" in a else ("root", a[a.index("--root") + 1])
    cfg = json.loads((r11 / "config_used.json").read_text(encoding="utf-8"))
    cal = json.loads((r11 / "dev_calibration.json").read_text(encoding="utf-8"))
    qc = pd.read_csv(r11 / "qc_trials.csv"); qc = qc[(qc["exclusion"].fillna("") == "") & (qc["set"] == split)]
    with Pool(jobs, initializer=_init, initargs=(mode, src, cfg, cal, locs)) as pool:
        rows = sum(pool.map(_w, list(qc["trial"]), chunksize=8), [])
    D = pd.DataFrame(rows); D.to_csv(out / f"v18_ext_{split}.csv", index=False)
    print(split, "segments", len(D), D.groupby("loc").size().to_dict())


# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v18_ext.py RESULTS_V11 OUT --root ROOT --set dev|test --locs HE,LB [--jobs N]')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

if __name__ == "__main__":
    main()
