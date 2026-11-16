"""V18 summaries from v18_<split>_segments.csv: per location and estimator, median of participant-median |e_C| and
share > 5 steps/min with participant bootstrap 95% CIs (2000, each draw relabelled), overall and by cohort; paired
AGS minus published peak; head minus lower back for AGS; sensitivity without reference-suspect segments and with the
stride reference. Usage: python analysis/v18_stats.py SEGMENTS.csv OUT.json"""
import json, sys
import numpy as np, pandas as pd
# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v18_stats.py SEGMENTS.csv OUT.json')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

D = pd.read_csv(sys.argv[1]); out = sys.argv[2]
EST = ["C_peak", "C_peak_stride", "C_ac", "C_ags"]
ORDER = ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]
rng = np.random.default_rng(20261112)
D = D[np.isfinite(D["C_peak"])].copy()           # same segments as the published primary analysis


def stat(d, ref):
    r = {}
    for loc, g in d.groupby("loc"):
        for k in EST:
            e = (g[k] - g[ref]).abs()
            pmed = g.assign(a=e).groupby("participant")["a"].median()
            r[f"{loc}|{k}|med"] = float(pmed.median()); r[f"{loc}|{k}|big"] = float(100 * (e > 5).mean())
            r[f"{loc}|{k}|nan"] = float(100 * g[k].isna().mean())
        pa = g.assign(a=(g.C_ags - g[ref]).abs(), b=(g.C_peak - g[ref]).abs()).groupby("participant")[["a", "b"]].median()
        r[f"{loc}|ags-peak|med"] = float((pa.a - pa.b).median())
        r[f"{loc}|ags-peak|big"] = r[f"{loc}|C_ags|big"] - r[f"{loc}|C_peak|big"]
    if {"HE", "LB"} <= set(d["loc"]):
        r["ags|HE-LB|big"] = r["HE|C_ags|big"] - r["LB|C_ags|big"]
        P = d.pivot_table(index=["trial", "segment", "participant"], columns="loc", values="C_ags").dropna()
        R = d[d["loc"] == "HE"].set_index(["trial", "segment", "participant"])[ref]
        P = P.join(R).dropna()
        ad = (P["HE"] - P[ref]).abs().groupby(level="participant").median() - (P["LB"] - P[ref]).abs().groupby(level="participant").median()
        r["ags|HE-LB|med"] = float(ad.median())
    return r


def boot(d, ref, B=2000):
    est = stat(d, ref); parts = d["participant"].unique(); idx = d.groupby("participant").indices; dr = []
    for _ in range(B):
        pk = rng.choice(parts, len(parts), replace=True)
        dd = pd.concat([d.iloc[idx[p]].assign(participant=f"{p}#{j}") for j, p in enumerate(pk)])
        dr.append(stat(dd, ref))
    dr = pd.DataFrame(dr)
    return {k: [v, float(np.nanpercentile(dr[k], 2.5)), float(np.nanpercentile(dr[k], 97.5))] for k, v in est.items()}


R = {"n": D.groupby("loc").size().to_dict(), "n_participants": int(D.participant.nunique())}
R["primary"] = boot(D, "R_step")
R["by_cohort"] = {c: boot(D[D.cohort == c], "R_step", 1000) for c in ORDER}
R["no_ref_suspect"] = boot(D[~D.ref_suspect], "R_step", 1000)
R["stride_ref"] = boot(D, "R_stride", 1000)
json.dump(R, open(out, "w"), indent=1)
for k, v in R["primary"].items():
    print(k, [round(x, 2) for x in v])
