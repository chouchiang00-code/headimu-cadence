#!/usr/bin/env python3
"""V18: one-shot evaluation of the frozen AGS estimator against the published peak estimator (A1, median step
interval), the stride-median peak estimator and the autocorrelation estimator, on the B0 straight segments of one split,
for head and/or lower back. Reference = 60 / median reference step interval (the published primary definition), and,
as a secondary definition, 120 / median reference stride. Reference-suspect segments are flagged (same-foot repeat or
longest interval >= 1.6 x median) and reported separately.
Usage: python analysis/v18_eval.py RESULTS_V11 OUT --root VOISARD_ROOT [--set test] [--locs HE,LB] [--jobs N]
       python analysis/v18_eval.py RESULTS_V11 OUT --pack PACK [--set test] [--locs HE]"""
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
from headimu.features import signals  # noqa: E402
from headimu.evaluate import _intervals  # noqa: E402

ARGS = {}


def _init(mode, src, cfg, cal, locs):
    """Pool initializer: works with the Windows 'spawn' start method (globals are not inherited)."""
    rc._init(mode, src, cfg)
    ARGS.update(cfg=cfg, cal=cal, locs=locs)


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
            c = M.seg_peaks(c_all, lag, a, b)
            iv = _intervals(np.asarray(c) + lag, valid, fs)
            T = M.ac_step(x, fs, a, b)
            ags, info = M.ags_cadence(x, fs, cfg, i0, i1, valid, lag, a, b)
            rows.append({"trial": t, "participant": tr.participant, "cohort": tr.cohort, "loc": loc, "segment": sname,
                         "n_ref": int(len(r)), "R_step": 60 / np.median(ri), "R_stride": M.stride_cadence(ri),
                         "ref_suspect": bool((np.diff(ff) == 0).sum() >= 1 or ri.max() / np.median(ri) >= 1.6),
                         "C_peak": 60 / np.median(iv) if len(iv) >= 2 else np.nan,
                         "C_peak_stride": M.stride_cadence(iv), "C_ac": 60 / T if T == T else np.nan, "C_ags": ags})
    return rows


def main():
    a = sys.argv[1:]
    r11, out = Path(a[0]), Path(a[1]); out.mkdir(parents=True, exist_ok=True)
    split = a[a.index("--set") + 1] if "--set" in a else "test"
    locs = a[a.index("--locs") + 1].split(",") if "--locs" in a else ["HE", "LB"]
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 1
    mode, src = ("pack", a[a.index("--pack") + 1]) if "--pack" in a else ("root", a[a.index("--root") + 1])
    cfg = json.loads((r11 / "config_used.json").read_text(encoding="utf-8"))
    cal = json.loads((r11 / "dev_calibration.json").read_text(encoding="utf-8"))
    qc = pd.read_csv(r11 / "qc_trials.csv"); qc = qc[(qc["exclusion"].fillna("") == "") & (qc["set"] == split)]
    ARGS.update(cfg=cfg, cal=cal, locs=locs)
    with Pool(jobs, initializer=_init, initargs=(mode, src, cfg, cal, locs)) as pool:
        rows = sum(pool.map(_w, list(qc["trial"]), chunksize=8), [])
    D = pd.DataFrame(rows)
    D.to_csv(out / f"v18_{split}_segments.csv", index=False)
    print("segments", len(D), D.groupby("loc").size().to_dict())


# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v18_eval.py RESULTS_V11 OUT --root VOISARD_ROOT [--set test] [--locs HE,LB] [--jobs N]')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

if __name__ == "__main__":
    main()
