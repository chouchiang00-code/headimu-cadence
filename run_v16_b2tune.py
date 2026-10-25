#!/usr/bin/env python3
"""V16 exploratory variant B2-t: causal peak-detector thresholds re-selected on the DEVELOPMENT set.

Motivation (recorded before running): in the first evaluation the prespecified causal detector (prominence factor 1.5,
confirmation 0.20 s, trailing-minimum window 0.9 s) produced 18% more peaks than reference heel strikes already on the
development set (precision 0.71), i.e., it had not been calibrated. Only the causal detector parameters are searched;
selection criterion: participant-median step F1 on development trials. The test set is evaluated once afterwards.
Usage: python run_v16_b2tune.py PACK.npz RESULTS_V11 E2E_DIR
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import butter, sosfilt, sosfilt_zi

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from headimu import dsp, endtoend as E  # noqa: E402
import run_v16_endtoend as R  # noqa: E402

FS = 100.0


def causal_peaks(a1, valid, P):
    dmin, dc, sw = int(round(P["min_dist_s"] * FS)), int(round(P["confirm_s"] * FS)), int(P["sigma_win_s"] * FS)
    tw = int(round(P.get("trail_min_s", 0.9) * FS))
    peaks, last = [], -10 ** 9
    for k in range(dmin, len(a1) - dc):
        x = a1[k]
        if x < a1[k - dmin:k].max() or x <= a1[k + 1:k + dc + 1].max() or k - last < dmin:
            continue
        thr = max(P["prom_floor"], P["prom_k"] * dsp.robust_sigma(a1[max(0, k - sw):k + 1]))
        if x - a1[max(0, k - tw):k].min() < thr or not valid[k]:
            continue
        peaks.append(k); last = k
    return np.array(peaks) / FS


def dev_job(args):
    t, acc, valid, hs, grid, P = args
    sos = butter(3, [P["band_lo"], P["band_hi"]], btype="band", fs=FS, output="sos")
    nrm = np.linalg.norm(acc, axis=1)
    a1, _ = sosfilt(sos, nrm, zi=sosfilt_zi(sos) * nrm[0])
    out = []
    for pk, cs, tm in grid:
        Q = dict(P, prom_k=pk, confirm_s=cs, trail_min_s=tm)
        p = causal_peaks(a1, valid, Q)
        w = (p >= hs[0] - 1) & (p <= hs[-1] + 1)
        out.append((t, pk, cs, tm, p[w]))
    return out


def main():
    pack, res11, e2e = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    z, meta = R.load_pack(pack)
    qc = pd.read_csv(res11 / "qc_trials.csv")
    setof = dict(zip(qc["trial"], qc["set"]))
    P = json.loads((e2e / "endtoend_params.json").read_text(encoding="utf-8"))["params"]
    grid = list(product([1.5, 2.0, 2.5, 3.0, 3.5], [0.20, 0.30], [0.9, 0.3]))
    dev = [t for t in meta if setof.get(t) == "dev"]
    jobs = [(t, z[f"{t}|acc"].astype(float), z[f"{t}|valid"], R.get(z, t)[3], grid, P) for t in dev]
    with ProcessPoolExecutor(2) as ex:
        res = sum(ex.map(dev_job, jobs, chunksize=8), [])
    # lag per grid point (median signed difference on dev) then F1
    rows = []
    hsd = {t: R.get(z, t)[3] for t in dev}
    for g in grid:
        sub = [(t, p) for t, pk, cs, tm, p in res if (pk, cs, tm) == g]
        d = []
        for t, p in sub:
            for h in hsd[t]:
                x = p - h
                x = x[np.abs(x) <= 0.4]
                if x.size:
                    d.append(x[np.argmin(np.abs(x))])
        lag = float(np.median(d))
        f1 = {}
        for t, p in sub:
            k, nd, nr, _ = E.match_events(p - lag, hsd[t], 0.15)
            f1.setdefault(meta[t]["participant"], []).append((k, nd, nr))
        pf = [2 * sum(a for a, _, _ in v) / (sum(b for _, b, _ in v) + sum(c for _, _, c in v)) for v in f1.values()]
        rows.append({"prom_k": g[0], "confirm_s": g[1], "trail_min_s": g[2], "lag": lag, "dev_step_f1": float(np.median(pf)),
                     "dev_det_ratio": sum(len(p) for _, p in sub) / sum(len(hsd[t]) for t, _ in sub)})
    tab = pd.DataFrame(rows).sort_values("dev_step_f1", ascending=False)
    tab.to_csv(e2e / "dev_tuning_b2t.csv", index=False)
    best = tab.iloc[0]
    print(tab.head(8).round(3).to_string())
    P2 = dict(P, prom_k=float(best.prom_k), confirm_s=float(best.confirm_s), trail_min_s=float(best.trail_min_s))
    (e2e / "b2t_params.json").write_text(json.dumps(P2, indent=1), encoding="utf-8")


# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python run_v16_b2tune.py PACK.npz RESULTS_V11 E2E_DIR')
        raise SystemExit(0)
    if len(sys.argv) < 4:
        print('Usage: python run_v16_b2tune.py PACK.npz RESULTS_V11 E2E_DIR', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
