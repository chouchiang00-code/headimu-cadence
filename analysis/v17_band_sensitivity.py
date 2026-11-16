#!/usr/bin/env python3
"""V17, POST HOC: sensitivity of the head A1 result to the band low cut-off, all 260 participants.

Evaluates every included trial (development and test participants) with each configured band low cut-off, using the
lags that the published development calibration stored for that cut-off. Reports per cohort the median of participant
medians |e_C| (participant-bootstrap 95% CI) and the share of segments with |e_C| > 5 steps/min, and the share among
segments whose reference cadence is below 90 steps/min.
Usage: python analysis/v17_band_sensitivity.py PACK.npz RESULTS_V11 OUT [--jobs N]
"""
import json, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis.v17_crossval import _init, _w_eval  # noqa: E402
from headimu import stats  # noqa: E402

def main():
    a = sys.argv[1:]; pack, r11, out = Path(a[0]), Path(a[1]), Path(a[2])
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 1
    out.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((r11 / "config_used.json").read_text()); cal = json.loads((r11 / "dev_calibration.json").read_text())
    qc = pd.read_csv(r11 / "qc_trials.csv"); ok = qc[qc["exclusion"].fillna("") == ""]
    _init(str(pack), cfg); trials = [t for t in ok["trial"] if t in __import__("analysis.v17_crossval", fromlist=["G"]).G["meta"]]
    setof = dict(zip(ok["trial"], ok["set"]))
    rows, segs = [], []
    with Pool(jobs, initializer=_init, initargs=(str(pack), cfg)) as pool:
        for lo in [float(x) for x in cfg["detect"]["band_lo_candidates_hz"]]:
            lags = cal["band_lo_candidates"][str(lo)]["lags_s"]
            s = pd.DataFrame(sum(pool.map(_w_eval, [(t, lo, lags) for t in trials], chunksize=16), []))
            s = s[s["method"] == "A1"].assign(band_lo=lo, set=lambda d: d["trial"].map(setof))
            segs.append(s)
            for c in ["All", "HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]:
                d = s if c == "All" else s[s["cohort"] == c]
                d = d.assign(x=d["e_C"].abs())
                per = d.groupby("participant")["x"].median().to_numpy()
                m, l, h = stats.boot_ci(per, np.median, 2000, seed=1)[:3]
                slow = d[d["C_ref"] < 90]
                rows.append({"band_lo": lo, "cohort": c, "n_participants": len(per), "n_segments": len(d),
                             "median": m, "lo": l, "hi": h, "big_pct": 100 * (d["x"] > 5).mean(),
                             "slow_n": len(slow), "big_pct_slow": 100 * (slow["x"] > 5).mean() if len(slow) else np.nan})
    T = pd.DataFrame(rows); T.to_csv(out / "band_sensitivity.csv", index=False)
    pd.concat(segs).to_csv(out / "band_sensitivity_segments.csv", index=False)
    print(T.round(2).to_string())

# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v17_band_sensitivity.py PACK.npz RESULTS_V11 OUT [--jobs N]')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

if __name__ == "__main__":
    main()
