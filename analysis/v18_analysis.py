#!/usr/bin/env python3
"""V18: component ablation, failure mechanisms, theory checks and operating envelope from v18_ext_{dev,test}.csv.
Rules (envelope thresholds) are chosen on the development set only and then applied to the test set.
Usage: python analysis/v18_analysis.py EXT_DIR OUT.json [--locs HE,LB]"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v18_analysis.py EXT_DIR OUT.json [--locs HE,LB]')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

EXT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
locs = sys.argv[sys.argv.index("--locs") + 1].split(",") if "--locs" in sys.argv else ["HE"]
DEV = pd.read_csv(EXT / "v18_ext_dev.csv"); TEST = pd.read_csv(EXT / "v18_ext_test.csv")
VAR = [("published", "C_peak"), ("+stride", "C_peak_stride"), ("+guided", "C_g_step"), ("+guided+stride", "C_g_stride"),
       ("AGS", "C_ags"), ("AC only", "C_ac")]
rng = np.random.default_rng(20261112)


def pm(d, k, ref="R_step"):
    return float(d.assign(a=(d[k] - d[ref]).abs()).groupby("participant")["a"].median().median())


def big(d, k, ref="R_step"):
    return float(100 * ((d[k] - d[ref]).abs() > 5).mean())


def ftype(d):
    b = (d.C_peak - d.R_step).abs() > 5
    t = np.select([d.ref_suspect, (d.prec >= 0.9) & (d.rec >= 0.9), d.prec < 0.9, d.rec < 0.9],
                  ["reference suspect", "interval statistic", "extra peaks", "missed peaks"], "other")
    return pd.Series(np.where(b, t, "ok"), index=d.index)


def boot_ci(d, fn, B=1000):
    parts = d.participant.unique(); idx = d.groupby("participant").indices; v = []
    for _ in range(B):
        pk = rng.choice(parts, len(parts)); v.append(fn(d.iloc[np.concatenate([idx[p] for p in pk])]))
    return [float(fn(d)), float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]


R = {}
for loc in locs:
    out = {}
    for nm, D in (("dev", DEV[DEV["loc"] == loc]), ("test", TEST[TEST["loc"] == loc])):
        D = D[D.C_peak.notna()].copy(); D["type"] = ftype(D)
        o = {"n": int(len(D)), "ablation": {v: {"med": pm(D, k), "big": big(D, k), "med_strideref": pm(D, k, "R_stride"),
                                                 "big_strideref": big(D, k, "R_stride")} for v, k in VAR}}
        o["ablation_ci"] = {v: {"big": boot_ci(D, lambda x, k=k: big(x, k)), "med": boot_ci(D, lambda x, k=k: pm(x, k))}
                            for v, k in VAR if v in ("published", "+stride", "+guided+stride", "AGS")} if nm == "test" else {}
        o["types"] = D.type.value_counts().to_dict()
        o["fixed_by_type"] = {t: {v: float(((g[k] - g.R_step).abs() <= 5).mean()) for v, k in VAR}
                              for t, g in D[D.type != "ok"].groupby("type")}
        o["broken_ok"] = {v: float(((D[D.type == "ok"][k] - D[D.type == "ok"].R_step).abs() > 5).mean()) for v, k in VAR}
        # mechanisms
        g = D.groupby("type")
        o["mech"] = {t: {"R_step": float(x.R_step.median()), "amp": float(x.amp.median()), "sr": float(x.sr.median()),
                         "fp_intra": float(x.fp_intra.median()) if x.fp_intra.notna().any() else None,
                         "fp_per_ref": float((x.n_fp / x.n_ref).median()), "ref_ratio": float(x.ref_ratio.median()),
                         "n": int(len(x))} for t, x in g}
        # theory checks on the reference
        disc = (D.R_step - D.R_stride).abs()
        bins = pd.cut(D.ref_ratio, [0, 0.8, 0.9, 0.95, 1.01])
        o["asym_ref"] = {str(k): {"n": int(len(x)), "step_vs_stride_gt2": float(100 * (disc[x.index] > 2).mean()),
                                  "peak_big": float(100 * ((x.C_peak - x.R_step).abs() > 5).mean()),
                                  "stride_big": float(100 * ((x.C_peak_stride - x.R_step).abs() > 5).mean())}
                         for k, x in D.groupby(bins, observed=True)}
        o["ref_ratio_below_tol"] = float(100 * (D.ref_ratio < 0.55 / (2 - 0.55)).mean())
        o["zero_err"] = {v: float(100 * ((D[k] - D.R_step).abs() < 1e-6).mean()) for v, k in VAR}
        C = D.R_step.median()
        o["quantum"] = {"median_cadence": float(C), "step_quantum_spm": float(C ** 2 * 0.01 / 60),
                        "stride_quantum_spm": float(C ** 2 * 0.01 / 120)}
        out[nm] = o
    # operating envelope: thresholds on head-observable sr and AGS cadence, chosen on dev
    dv = DEV[(DEV["loc"] == loc) & DEV.C_peak.notna()].copy(); ts = TEST[(TEST["loc"] == loc) & TEST.C_peak.notna()].copy()
    for X in (dv, ts):
        X["bigA"] = (X.C_ags - X.R_step).abs() > 5
    grid = []
    for s_ in (0.0, 0.3, 0.4, 0.5, 0.6, 0.7):
        for c_ in (0, 80, 90, 95, 100):
            u = (dv.sr.fillna(0) >= s_) & (dv.C_ags >= c_)
            if u.sum() == 0:
                continue
            grid.append({"sr": s_, "cad": c_, "coverage": float(100 * u.mean()), "big_in": float(100 * dv.bigA[u].mean())})
    G = pd.DataFrame(grid)
    target = 3.0
    ok = G[G.big_in <= target]
    best = ok.sort_values(["coverage", "sr"], ascending=[False, True]).iloc[0].to_dict() if len(ok) else None
    env = {"grid_dev": grid, "target_big_pct": target, "chosen": best}
    if best:
        def ev(X):
            u = (X.sr.fillna(0) >= best["sr"]) & (X.C_ags >= best["cad"])
            r = {"coverage": float(100 * u.mean()), "big_in": float(100 * X.bigA[u].mean()),
                 "big_out": float(100 * X.bigA[~u].mean()) if (~u).any() else None,
                 "share_of_big_flagged": float(100 * (~u)[X.bigA].mean()) if X.bigA.any() else None}
            r["by_cohort"] = {c: {"coverage": float(100 * u[g.index].mean()), "big_in": float(100 * g.bigA[u[g.index]].mean())
                                  if u[g.index].any() else None} for c, g in X.groupby("cohort")}
            return r
        env["dev"] = ev(dv); env["test"] = ev(ts)
        env["test_ci"] = {"coverage": boot_ci(ts, lambda X: 100 * ((X.sr.fillna(0) >= best["sr"]) & (X.C_ags >= best["cad"])).mean()),
                          "big_in": boot_ci(ts, lambda X: 100 * X.bigA[(X.sr.fillna(0) >= best["sr"]) & (X.C_ags >= best["cad"])].mean())}
    # map for the figure: big% of AGS by sr x cadence bins (test)
    sb = pd.cut(ts.sr.fillna(0), [-1, 0.4, 0.6, 0.8, 1.01], labels=["<0.4", "0.4-0.6", "0.6-0.8", ">=0.8"])
    cb = pd.cut(ts.C_ags, [0, 90, 105, 300], labels=["<90", "90-105", ">=105"])
    env["map_test"] = {f"{a}|{b}": {"n": int(len(g)), "big": float(100 * g.bigA.mean())} for (a, b), g in ts.groupby([sb, cb], observed=True)}
    sb = pd.cut(dv.sr.fillna(0), [-1, 0.4, 0.6, 0.8, 1.01], labels=["<0.4", "0.4-0.6", "0.6-0.8", ">=0.8"])
    cb = pd.cut(dv.C_ags, [0, 90, 105, 300], labels=["<90", "90-105", ">=105"])
    env["map_dev"] = {f"{a}|{b}": {"n": int(len(g)), "big": float(100 * g.bigA.mean())} for (a, b), g in dv.groupby([sb, cb], observed=True)}
    out["envelope"] = env
    R[loc] = out
OUT.write_text(json.dumps(R, indent=1, default=float))
for loc in locs:
    for nm in ("dev", "test"):
        print(loc, nm, "types", R[loc][nm]["types"])
        for v, x in R[loc][nm]["ablation"].items():
            print(f"  {v:15s} med {x['med']:.3f} big {x['big']:.1f} | strideref med {x['med_strideref']:.3f} big {x['big_strideref']:.1f}")
        print("  fixed", {t: {k: round(v, 2) for k, v in d.items()} for t, d in R[loc][nm]["fixed_by_type"].items()})
        print("  broken_ok", {k: round(v * 100, 2) for k, v in R[loc][nm]["broken_ok"].items()})
        print("  mech", R[loc][nm]["mech"])
        print("  asym", R[loc][nm]["asym_ref"], "below tol", R[loc][nm]["ref_ratio_below_tol"])
        print("  zero", R[loc][nm]["zero_err"], R[loc][nm]["quantum"])
    e = R[loc]["envelope"]; print(loc, "chosen", e["chosen"], "\n dev", e.get("dev"), "\n test", {k: v for k, v in e.get("test", {}).items() if k != "by_cohort"}, e.get("test_ci"))
