"""V15 supplementary computations (run after v15_stats.py). Labelled post hoc where applicable.
Usage: python v15_extra.py RESULTS_V11 RESULTS_V15"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats as ss
# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/v15_extra.py RESULTS_V11 RESULTS_V15')
        raise SystemExit(0)
    if len(sys.argv) < 3:
        print('Usage: python analysis/v15_extra.py RESULTS_V11 RESULTS_V15', file=sys.stderr)
        raise SystemExit(2)


sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2], "2000"]
src = Path(__file__).with_name("v15_stats.py").read_text(encoding="utf-8")
src = src[: src.index("# ----------------------------------------------------------------------------- 1 validity")]
exec(src)  # loads data and helper definitions (boot, trial, etc.)
exec(Path(__file__).with_name("v15_stats.py").read_text(encoding="utf-8").split("# ----------------------------------------------------------------------------- 4 clinical (VGA)")[1]
     .split("# ----------------------------------------------------------------------------- 5 screening by VGA")[0])
X = {}
# (a) post hoc: M1 without step asymmetry (poor validity, missing in short segments)
cols0 = MODELS["M0_age_sensor_cadence"]; cols1 = cols0 + [f for f in HEADX if f != "step_asym"]
def fit_score(cols):
    d = dev.dropna(subset=cols); mu, sd = d[cols].mean(), d[cols].std().replace(0, 1)
    b = ridge_logit(((d[cols] - mu) / sd).to_numpy(), d["vga2"].to_numpy())
    t = tst.dropna(subset=cols)
    return pd.Series(np.column_stack([np.ones(len(t)), ((t[cols] - mu) / sd).to_numpy()]) @ b, index=t["participant"]), len(d)
s0, n0 = fit_score(cols0); s1, n1 = fit_score(cols1)
idx = s0.index.intersection(s1.index)
cm = pd.DataFrame({"y": tst.set_index("participant").loc[idx, "vga2"], "m0": s0[idx], "m1": s1[idx]}).reset_index()
X["m1_no_asym"] = {"n_dev": n1, "n_test": len(cm), "auc_m0": auc(cm.y, cm.m0), "auc_m1": auc(cm.y, cm.m1),
                   "delta": auc(cm.y, cm.m1) - auc(cm.y, cm.m0), "ci": boot(lambda b: auc(b.y, b.m1) - auc(b.y, b.m0), cm)}
# prespecified models: AUCs on the common test set
c0 = scores["M0_age_sensor_cadence"]; c1 = scores["M1_plus_head_features"]; i2 = c0.index.intersection(c1.index)
yy = tst.set_index("participant").loc[i2, "vga2"]
X["prespecified_common"] = {"n": len(i2), "auc_m0": auc(yy, c0[i2]), "auc_m1": auc(yy, c1[i2])}
# (b) bootstrap CIs of rank partial correlations with VGA
PTr = PT.reset_index(drop=True)
X["partial_ci"] = {}
for f in ["cadence", "step_cv", "step_reg", "stride_reg", "rms_v", "w_tilt_rms", "ref_step_cv"]:
    covs = ["age", "xsens"] + ([] if f in ("cadence",) else ["cadence"])
    X["partial_ci"][f] = (rank_partial(PTr, f, covs)[0], boot(lambda b: rank_partial(b, f, covs)[0], PTr))
# (c) Spearman with VGA, patients only, CIs
pat = PTr[PTr.cohort != "HS"]
X["rho_patients_ci"] = {f: (ss.spearmanr(pat[f], pat.vga, nan_policy="omit").correlation,
                            boot(lambda b: ss.spearmanr(b[f], b.vga, nan_policy="omit").correlation, pat))
                        for f in ["step_reg", "rms_v", "step_cv", "cadence", "ref_step_cv"]}
(R15 / "v15_extra.json").write_text(json.dumps(X, indent=1, default=float), encoding="utf-8")
print(json.dumps(X, indent=1, default=float))
