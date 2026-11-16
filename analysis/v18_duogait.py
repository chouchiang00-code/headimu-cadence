#!/usr/bin/env python3
"""V18 external check on DUO-GAIT (16 healthy adults), frozen: AGS vs the published peak estimator on the reference
straight passes (B0) and on the head-only B1 segments matched to each pass. Nothing is fitted on DUO-GAIT.
Usage: python analysis/v18_duogait.py HEAD_NPZ PROCESSED_ZIP E2E_DIR OUT_DIR"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.signal import butter, sosfiltfilt
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from headimu import endtoend as E, duogait as dg  # noqa: E402
from analysis import v18_methods as M  # noqa: E402
from headimu.evaluate import _intervals  # noqa: E402
FS = 100.0
# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v18_duogait.py HEAD_NPZ PROCESSED_ZIP E2E_DIR OUT_DIR')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

head_npz, proc_zip, e2e, out = map(Path, sys.argv[1:5]); out.mkdir(parents=True, exist_ok=True)
P = json.loads((e2e / "endtoend_params.json").read_text(encoding="utf-8"))["params"]
cfg = {"detect": {"prominence_floor_mps2": 0.12, "prominence_k_sigma": 1.5, "min_peak_distance_s": 0.30},
       "autocorr": {"min_lag_s": 0.30, "max_lag_s": 0.90}}
z = np.load(head_npz); lag = P.get("lag_b1", 0.0)
walks = sorted({tuple(k.split("|")[:2]) for k in z.files if k.count("|") == 2})
sos = butter(3, [P["band_lo"], P["band_hi"]], btype="band", fs=FS, output="sos")
rows = []
for cond, sub in walks:
    acc, gyr = dg.adapt_head(z[f"{cond}|{sub}|acc_g"], z[f"{cond}|{sub}|gyr_dps"], float(z[f"{cond}|{sub}|fs"]))
    valid = np.isfinite(acc).all(1) & np.isfinite(gyr).all(1); acc = np.nan_to_num(acc); gyr = np.nan_to_num(gyr)
    passes, turns, ics = dg.reference_passes(dg.load_reference(proc_zip, cond, sub))
    o = E.offline(acc, gyr, valid, FS, P)
    x = sosfiltfilt(sos, np.linalg.norm(acc, axis=1))
    i0, i1 = max(0, int((ics[0] - 1) * FS)), min(len(acc), int((ics[-1] + 1) * FS))
    c_all = M.base_peaks(x, FS, cfg, i0, i1, valid)
    for k, p in enumerate(passes):
        a, b = p["t0"], p["t1"]
        c = M.seg_peaks(c_all, lag, a, b); iv = np.diff(c)
        r = {"cond": cond, "sub": sub, "pass": k, "C_ref": p["C_ref"],
             "B0_peak": 60.0 / np.median(iv) if len(iv) >= 3 else np.nan,
             "B0_ags": M.ags_cadence(x, FS, cfg, i0, i1, valid, lag, a, b)[0]}
        ov = [(min(s["t1"], b) - max(s["t0"], a), s) for s in o["segments"]]
        ov = [q for q in ov if q[0] >= 1.0]
        if ov:
            s = max(ov, key=lambda q: q[0])[1]
            r["B1_peak"] = s["cadence"]
            r["B1_ags"] = M.ags_cadence(x, FS, cfg, i0, i1, valid, lag, s["t0"], s["t1"])[0]
        else:
            r["B1_peak"] = r["B1_ags"] = np.nan
        rows.append(r)
S = pd.DataFrame(rows); S.to_csv(out / "v18_duogait_passes.csv", index=False)
S["pid"] = S["sub"]
res = {"n_passes": int(len(S))}
rng = np.random.default_rng(20261112)
for k in ("B0_peak", "B0_ags", "B1_peak", "B1_ags"):
    e = (S[k] - S.C_ref).abs(); pm = S.assign(a=e).groupby("pid")["a"].median()
    bs = [np.median(rng.choice(pm.to_numpy(), len(pm))) for _ in range(2000)]
    res[k] = {"median": float(pm.median()), "lo": float(np.percentile(bs, 2.5)), "hi": float(np.percentile(bs, 97.5)),
              "big_pct": float(100 * (e > 5).mean()), "nan_pct": float(100 * S[k].isna().mean())}
(out / "v18_duogait.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
