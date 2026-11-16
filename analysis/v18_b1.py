#!/usr/bin/env python3
"""V18: frozen AGS applied to the head-only B1 segments on the Voisard test set (same B1 segments as published;
cadence recomputed with AGS over each B1 segment). Usage: python analysis/v18_b1.py PACK E2E_DIR OUT_DIR"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.signal import butter, sosfiltfilt
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from analysis import v18_methods as M  # noqa: E402
# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v18_b1.py PACK E2E_DIR OUT_DIR')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

pack, e2e, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
P = json.loads((e2e / "endtoend_params.json").read_text(encoding="utf-8"))["params"]
S = pd.read_csv(e2e / "endtoend_segments.csv"); S = S[S["set"] == "test"].copy()
z = np.load(pack); FS = 100.0; lag = P.get("lag_b1", 0.0)
cfg = {"detect": {"prominence_floor_mps2": 0.12, "prominence_k_sigma": 1.5, "min_peak_distance_s": 0.30}}
sos = butter(3, [P["band_lo"], P["band_hi"]], btype="band", fs=FS, output="sos")
cache = {}
ags = []
for r in S.itertuples():
    if r.trial not in cache:
        acc = z[f"{r.trial}|acc"].astype(float); valid = z[f"{r.trial}|valid"]
        cache = {r.trial: (sosfiltfilt(sos, np.linalg.norm(np.nan_to_num(acc), axis=1)), valid)}
    x, valid = cache[r.trial]
    if not np.isfinite(r.B1_t0):
        ags.append(np.nan); continue
    i0, i1 = max(0, int((r.B1_t0 - 1) * FS)), min(len(x), int((r.B1_t1 + 1) * FS))
    ags.append(M.ags_cadence(x, FS, cfg, i0, i1, valid, lag, r.B1_t0, r.B1_t1)[0])
S["B1_ags"] = ags
S.to_csv(out / "v18_b1_segments.csv", index=False)
res = {}
rng = np.random.default_rng(20261112)
for k in ("B1_C", "B1_ags"):
    e = (S[k] - S.C_ref).abs()
    pm = S.assign(a=e).groupby("participant")["a"].median().dropna()
    bs = [np.median(rng.choice(pm.to_numpy(), len(pm))) for _ in range(2000)]
    big_or_none = float(100 * ((e > 5) | S[k].isna()).mean())
    res[k] = {"median": float(pm.median()), "lo": float(np.percentile(bs, 2.5)), "hi": float(np.percentile(bs, 97.5)),
              "big_pct": float(100 * (e > 5).mean()), "big_or_no_output_pct": big_or_none, "nan_pct": float(100 * S[k].isna().mean())}
for c in ("CVA", "RIL", "PD", "HS"):
    g = S[S.cohort == c]
    res[f"{c}|big_or_none"] = {k: float(100 * (((g[k] - g.C_ref).abs() > 5) | g[k].isna()).mean()) for k in ("B1_C", "B1_ags")}
(out / "v18_b1.json").write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
