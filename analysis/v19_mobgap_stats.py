#!/usr/bin/env python3
"""V19: statistics for the Mobilise-D (mobgap) baseline vs AGS and the published peak estimator on the same test
segments; participant bootstrap (2000); both reference definitions. Usage:
python analysis/v19_mobgap_stats.py MOBGAP_SEGMENTS_CSV EXT_TEST_CSV OUT_JSON"""
import json, sys
import numpy as np, pandas as pd
# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v19_mobgap_stats.py MOBGAP_SEGMENTS_CSV EXT_TEST_CSV OUT_JSON')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

mg, ext, outp = sys.argv[1:4]
M = pd.read_csv(mg); E = pd.read_csv(ext)
E = E[E.C_peak.notna()][["trial", "segment", "loc", "C_peak", "C_peak_stride", "C_ags", "C_ac"]]
D = M.merge(E, on=["trial", "segment", "loc"], how="inner")
EST = ["C_peak", "C_peak_stride", "C_ac", "C_ags", "MD_regular", "MD_impaired", "Ionescu_step", "Ionescu_stride"]
rng = np.random.default_rng(20261117)


def stats(d, ref):
    parts = d.participant.unique(); idx = d.groupby("participant").indices
    def f(x):
        o = {}
        for k in EST:
            e = (x[k] - x[ref]).abs()
            o[f"{k}|med"] = e.groupby(x.participant).median().median()
            o[f"{k}|big"] = 100 * ((e > 5) | x[k].isna()).mean()
        for k in ("MD_regular", "MD_impaired", "Ionescu_step", "C_peak", "Ionescu_stride"):
            o[f"ags-{k}|big"] = o["C_ags|big"] - o[f"{k}|big"]
            o[f"ags-{k}|med"] = ((x.C_ags - x[ref]).abs() - (x[k] - x[ref]).abs()).groupby(x.participant).median().median()
        o["Ionescu_stride-step|big"] = o["Ionescu_stride|big"] - o["Ionescu_step|big"]
        return o
    est = f(d); bs = []
    for _ in range(2000):
        pk = rng.choice(parts, len(parts)); bs.append(f(d.iloc[np.concatenate([idx[p] for p in pk])]))
    B = pd.DataFrame(bs)
    return {k: [float(v), float(B[k].quantile(0.025)), float(B[k].quantile(0.975))] for k, v in est.items()}


R = {"n": D.groupby("loc").size().to_dict()}
for loc, d in D.groupby("loc"):
    R[loc] = {"step": stats(d, "R_step"), "stride": stats(d, "R_stride")}
    R[loc]["by_cohort_big"] = {c: {k: float(100 * (((g[k] - g.R_step).abs() > 5) | g[k].isna()).mean()) for k in EST}
                               for c, g in d.groupby("cohort")}
json.dump(R, open(outp, "w"), indent=1)
f = lambda v, nd=2: f"{v[0]:.{nd}f} [{v[1]:.{nd}f}, {v[2]:.{nd}f}]"
for loc in [k for k in R if k in ("HE", "LB")]:
    for ref in ("step", "stride"):
        print(loc, ref, {k: f(v, 2 if "med" in k else 1) for k, v in R[loc][ref].items()})
