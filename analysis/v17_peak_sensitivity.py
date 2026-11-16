#!/usr/bin/env python3
"""V17, POST HOC: sensitivity of head A1 (B0, fixed test split) to the fixed peak-detection parameters.

One parameter at a time is changed from its prespecified value (prominence floor 0.12 m/s^2, prominence factor 1.5
sigma, minimum peak distance 0.30 s); band low cut-off and lags stay as calibrated on the development set.
Reports median of participant medians |e_C| (participant-bootstrap 95% CI), share |e_C| > 5, halving/doubling rates.
Usage: python analysis/v17_peak_sensitivity.py PACK.npz RESULTS_V11 OUT [--jobs N]
"""
import copy, json, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis.v17_crossval import _init, _trial, G  # noqa: E402
from headimu import pipeline as pl, stats  # noqa: E402

GRID = [("prominence_floor_mps2", [0.08, 0.12, 0.16, 0.20]), ("prominence_k_sigma", [1.0, 1.5, 2.0, 2.5]),
        ("min_peak_distance_s", [0.25, 0.30, 0.35, 0.40])]


def _w(args):
    t, cfg, lo, lags = args
    seg, _, _ = pl.evaluate_trial(_trial(t), cfg, lo, lags, [], 0, 0, ("HE",))
    return [s for s in seg if s["method"] == "A1"]


def main():
    a = sys.argv[1:]; pack, r11, out = Path(a[0]), Path(a[1]), Path(a[2])
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 1
    out.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((r11 / "config_used.json").read_text()); cal = json.loads((r11 / "dev_calibration.json").read_text())
    qc = pd.read_csv(r11 / "qc_trials.csv"); test = qc[(qc["exclusion"].fillna("") == "") & (qc["set"] == "test")]["trial"].tolist()
    rows = []
    with Pool(jobs, initializer=_init, initargs=(str(pack), cfg)) as pool:
        for key, vals in GRID:
            for v in vals:
                c = copy.deepcopy(cfg); c["detect"][key] = v
                s = pd.DataFrame(sum(pool.map(_w, [(t, c, float(cal["band_lo_hz"]), cal["lags_s"]) for t in test], chunksize=16), []))
                n_all = len(s); s = s[np.isfinite(s["e_C"])]
                per = s.assign(x=s["e_C"].abs()).groupby("participant")["x"].median().to_numpy()
                m, lo, hi = stats.boot_ci(per, np.median, 2000, seed=1)[:3]
                rows.append({"parameter": key, "value": v, "prespecified": v == cfg["detect"][key], "median": m, "lo": lo, "hi": hi,
                             "big_pct": 100 * (s["e_C"].abs() > 5).mean(), "halving_pct": 100 * s["halving"].mean(),
                             "doubling_pct": 100 * s["doubling"].mean(), "n_segments": len(s), "no_output": n_all - len(s)})
                print(rows[-1])
    pd.DataFrame(rows).to_csv(out / "peak_sensitivity.csv", index=False)

# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v17_peak_sensitivity.py PACK.npz RESULTS_V11 OUT [--jobs N]')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

if __name__ == "__main__":
    main()
