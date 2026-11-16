#!/usr/bin/env python3
"""V19: paired differences (perturbation minus as-recorded) for the sensor-requirement simulations; participant
bootstrap (2000). Large error counts no output as failure. Usage: python analysis/v19_sensor_req_paired.py OUT_DIR"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v19_sensor_req_paired.py OUT_DIR')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

out = Path(sys.argv[1]); D = pd.read_csv(out / "v19_sensor_req_rows.csv", dtype={"level": str})
rng = np.random.default_rng(20261116)
key = ["trial", "segment"]


def paired(a, b, k):
    m = a.merge(b, on=key + ["participant"], suffixes=("_p", "_r"))
    ep, er = (m[f"{k}_p"] - m.R_step_r).abs(), (m[f"{k}_r"] - m.R_step_r).abs()
    m["bd"] = ((ep > 5) | m[f"{k}_p"].isna()).astype(float) - ((er > 5) | m[f"{k}_r"].isna()).astype(float)
    m["md"] = ep - er
    g = m.groupby("participant"); s, c = g.bd.sum(), g.size(); pmd = g.md.median()
    P = s.index.to_numpy(); bb, bm = [], []
    for _ in range(2000):
        pk = rng.choice(P, len(P)); bb.append(100 * s[pk].sum() / c[pk].sum()); bm.append(np.nanmedian(pmd[pk]))
    return {"big_pp": [100 * s.sum() / c.sum(), np.percentile(bb, 2.5), np.percentile(bb, 97.5)],
            "med_diff": [float(pmd.median()), np.percentile(bm, 2.5), np.percentile(bm, 97.5)], "n": int(len(m))}


ref = D[D.pert == "reference"]
R = {}
for pert, lev in [("fs", "50"), ("fs", "25"), ("fs", "20"), ("noise", "1.0"), ("lsb", "0.5"), ("range", "1.5"),
                  ("lowpower", "25Hz+8bit4g")]:
    d = D[(D.pert == pert) & (D.level == lev)]
    R[f"{pert}|{lev}"] = {k: paired(d, ref, k) for k in ("C_ags", "C_peak", "C_stride", "C_ac")}
for _fb in (100, 25):
    R[f"accel_only_{_fb}Hz_vs_gyro_B1"] = {"C_ags": paired(D[(D.pert == "accel_only_B1") & (D.level == f"no turn removal {_fb} Hz")], D[D.pert == "gyro_B1"], "C_ags")}
(out / "v19_sensor_req_paired.json").write_text(json.dumps(R, indent=1, default=float))
for k, v in R.items():
    print(k, {e: {m: "%.2f [%.2f, %.2f]" % tuple(x[m]) for m in ("big_pp", "med_diff")} for e, x in v.items()})
