"""V15 statistics on the outputs of run_features.py (+ the primary results folder).

Usage: python v15_stats.py RESULTS_V11 RESULTS_V15 [B]
Writes RESULTS_V15/v15_tables/*.csv and RESULTS_V15/v15_summary.json.

Prespecified analyses (test set unless stated; participant = unit of analysis):
 1 validity      head vs foot-reference cadence, step-time CV, step-time asymmetry (participant medians):
                 ICC(A,1), Spearman rho, median difference, participant-bootstrap CIs
 2 reliability   within-visit trial-to-trial ICC(A,1) of every feature (first visit with >= 2 trials, trials 1 vs 2,
                 trial value = mean of the two straight segments); same for reference counterparts
 3 mounting      sim_features.csv: change of each trial feature under rotation / lever arm, expressed as median |delta|
                 in units of the between-participant SD of the unperturbed feature ("standardized change")
 4 clinical      VGA (clinician visual gait assessment, 0-4) at the first visit:
                 a) Spearman rho of each feature with VGA (all; patients only), and rank partial correlation adjusted
                    for age, sensor system and cadence
                 b) incremental value for VGA >= 2: ridge-logistic models fitted on the DEVELOPMENT participants only
                    (standardization and coefficients from dev; fixed penalty), AUC on TEST participants:
                    M0 age + sensor + head cadence; M1 = M0 + 8 head features; MR = age + sensor + 3 reference features
                    delta AUC (M1 - M0) with participant-bootstrap CI
 5 screening     SR screen (dev 10th percentile) and turn gate (30 deg/s): exclusion / time kept by VGA level
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as ss
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from headimu.stats import icc_a1  # noqa: E402
from headimu.features import FEATS, CONTROLS  # noqa: E402

# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/v15_stats.py RESULTS_V11 RESULTS_V15 [B]')
        raise SystemExit(0)
    if len(sys.argv) < 3:
        print('Usage: python analysis/v15_stats.py RESULTS_V11 RESULTS_V15 [B]', file=sys.stderr)
        raise SystemExit(2)


R11, R15 = Path(sys.argv[1]), Path(sys.argv[2])
B = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
OUT = R15 / "v15_tables"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(20261022)
S = {}

seg = pd.read_csv(R15 / "features_segments.csv")
meta = pd.read_csv(R15 / "clinical_meta.csv")
sim = pd.read_csv(R15 / "sim_features.csv")
qc = pd.read_csv(R11 / "qc_trials.csv")
ALL = FEATS + CONTROLS
HEADX = [f for f in FEATS if f != "cadence"]

# trial level = mean of the two straight segments
trial = seg.groupby(["trial", "participant", "cohort", "visit", "sensor_type", "set"], as_index=False)[
    ALL + ["ref_cadence", "ref_step_cv", "ref_step_asym"]].mean()
trial = trial.merge(meta[["trial", "vga", "age", "tug_s"]], on="trial", how="left")
trial["tnum"] = trial["trial"].str.rsplit("_", n=1).str[-1].astype(int)
trial["visit"] = trial["visit"].astype(str)


def boot(fn, df, by="participant", B=B):
    ids = df[by].unique()
    g = {k: v for k, v in df.groupby(by)}
    vals = []
    for _ in range(B):
        bs = pd.concat([g[i] for i in rng.choice(ids, len(ids))], ignore_index=True)
        try:
            vals.append(fn(bs))
        except Exception:
            pass
    vals = np.array([v for v in vals if np.isfinite(v)])
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) if len(vals) > 20 else (np.nan, np.nan)


# ----------------------------------------------------------------------------- 1 validity
test = trial[trial["set"] == "test"]
pm = test.groupby("participant").median(numeric_only=True)
rows = []
for h, r in (("cadence", "ref_cadence"), ("step_cv", "ref_step_cv"), ("step_asym", "ref_step_asym")):
    d = pm[[h, r]].dropna()
    icc = icc_a1(d.to_numpy())["icc"]
    rho = ss.spearmanr(d[h], d[r]).correlation
    dd = d.reset_index()
    ci_icc = boot(lambda b: icc_a1(b[[h, r]].to_numpy())["icc"], dd)
    ci_rho = boot(lambda b: ss.spearmanr(b[h], b[r]).correlation, dd)
    rows.append({"feature": h, "n": len(d), "head_median": d[h].median(), "ref_median": d[r].median(),
                 "median_diff": (d[h] - d[r]).median(), "icc": icc, "icc_lo": ci_icc[0], "icc_hi": ci_icc[1],
                 "rho": rho, "rho_lo": ci_rho[0], "rho_hi": ci_rho[1]})
val = pd.DataFrame(rows)
val.to_csv(OUT / "validity.csv", index=False)
S["validity"] = val.round(4).to_dict("records")

# ----------------------------------------------------------------------------- 2 within-visit reliability
first_visit = test.groupby("participant")["visit"].min()
fv = test[test["visit"] == test["participant"].map(first_visit)]
fv = fv.sort_values("tnum").groupby("participant").head(2)
fv = fv[fv.groupby("participant")["trial"].transform("count") == 2]
fv["k"] = fv.groupby("participant").cumcount()
rows = []
for f in ALL + ["ref_cadence", "ref_step_cv", "ref_step_asym"]:
    X = fv.pivot(index="participant", columns="k", values=f)
    X = X.dropna()
    if len(X) < 5:
        continue
    res = icc_a1(X.to_numpy())
    ci = boot(lambda b: icc_a1(b[[0, 1]].to_numpy())["icc"], X.reset_index())
    rows.append({"feature": f, "n": res["n"], "icc": res["icc"], "lo": ci[0], "hi": ci[1], "sem": res["sem"],
                 "sem_pct": 100 * res["sem"] / np.nanmean(X.to_numpy())})
rel = pd.DataFrame(rows)
rel.to_csv(OUT / "reliability_within_visit.csv", index=False)
S["reliability"] = rel.round(4).to_dict("records")

# ----------------------------------------------------------------------------- 3 mounting sensitivity
base = sim[sim["pert"] == "none"].set_index("trial")
sd_between = base.groupby("participant")[ALL].median().std()
rows = []
for (pert, lev), g in sim[sim["pert"] != "none"].groupby(["pert", "level"]):
    for f in ALL:
        dlt = (g.set_index("trial")[f] - base[f].reindex(g["trial"]).to_numpy())
        rows.append({"pert": pert, "level": lev, "feature": f,
                     "std_change": float(np.nanmedian(np.abs(dlt)) / sd_between[f]) if sd_between[f] > 0 else np.nan,
                     "pct_change": float(100 * np.nanmedian(np.abs(dlt) / np.abs(base[f].reindex(g["trial"]).to_numpy()))),
                     "max_abs_change": float(np.nanmax(np.abs(dlt)))})
mnt = pd.DataFrame(rows)
mnt.to_csv(OUT / "mounting_sensitivity.csv", index=False)
S["mounting"] = {f"{k[0]}_{k[1]:g}": v for k, v in
                 mnt.pivot_table(index="feature", columns=["pert", "level"], values="std_change").round(4).to_dict().items()}

# ----------------------------------------------------------------------------- 4 clinical (VGA)
trial_all = trial.copy()
fvis = trial_all.groupby("participant")["visit"].min()
pv = trial_all[trial_all["visit"] == trial_all["participant"].map(fvis)]
P = pv.groupby(["participant", "cohort", "set", "sensor_type"], as_index=False).median(numeric_only=True)
P["xsens"] = (P["sensor_type"] == "XSens").astype(float)
P["vga2"] = (P["vga"] >= 2).astype(float)
P.loc[P["vga"].isna(), "vga2"] = np.nan
PT = P[(P["set"] == "test") & P["vga"].notna()]


def rank_partial(df, f, covs):
    d = df[[f, "vga"] + covs].dropna()
    r = d.rank()
    Z = np.column_stack([np.ones(len(r)), r[covs].to_numpy()])
    ex = r[f] - Z @ np.linalg.lstsq(Z, r[f], rcond=None)[0]
    ey = r["vga"] - Z @ np.linalg.lstsq(Z, r["vga"], rcond=None)[0]
    return float(np.corrcoef(ex, ey)[0, 1]), len(d)


rows = []
for f in FEATS + ["ref_cadence", "ref_step_cv", "ref_step_asym"]:
    d = PT[[f, "vga"]].dropna()
    pat = PT[PT["cohort"] != "HS"][[f, "vga"]].dropna()
    pr, n = rank_partial(PT, f, ["age", "xsens"] + ([] if f in ("cadence", "ref_cadence") else ["cadence"]))
    rows.append({"feature": f, "n": len(d), "rho_all": ss.spearmanr(d[f], d["vga"]).correlation,
                 "rho_patients": ss.spearmanr(pat[f], pat["vga"]).correlation if len(pat) > 5 else np.nan,
                 "partial_rho_adj": pr, "n_adj": n})
cl = pd.DataFrame(rows)
cl.to_csv(OUT / "vga_association.csv", index=False)
S["vga_association"] = cl.round(4).to_dict("records")
S["vga_counts_test"] = PT["vga"].value_counts().sort_index().to_dict()
S["vga_counts_dev"] = P[(P["set"] == "dev")]["vga"].value_counts().sort_index().to_dict()


def ridge_logit(X, y, lam=1.0):
    X1 = np.column_stack([np.ones(len(X)), X])

    def nll(b):
        z = X1 @ b
        return np.sum(np.logaddexp(0, z) - y * z) + 0.5 * lam * np.sum(b[1:] ** 2)

    def grad(b):
        p = 1 / (1 + np.exp(-(X1 @ b)))
        g = X1.T @ (p - y)
        g[1:] += lam * b[1:]
        return g
    return minimize(nll, np.zeros(X1.shape[1]), jac=grad, method="L-BFGS-B").x


def auc(y, s):
    y, s = np.asarray(y), np.asarray(s)
    pos, neg = s[y == 1], s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    return float(ss.mannwhitneyu(pos, neg).statistic / (len(pos) * len(neg)))


MODELS = {"M0_age_sensor_cadence": ["age", "xsens", "cadence"],
          "M1_plus_head_features": ["age", "xsens", "cadence"] + HEADX,
          "MR_reference_features": ["age", "xsens", "ref_cadence", "ref_step_cv", "ref_step_asym"]}
dev = P[(P["set"] == "dev") & P["vga2"].notna()]
tst = P[(P["set"] == "test") & P["vga2"].notna()]
scores, rows = {}, []
for name, cols in MODELS.items():
    d = dev.dropna(subset=cols)
    mu, sd = d[cols].mean(), d[cols].std().replace(0, 1)
    b = ridge_logit(((d[cols] - mu) / sd).to_numpy(), d["vga2"].to_numpy())
    t = tst.dropna(subset=cols)
    s = np.column_stack([np.ones(len(t)), ((t[cols] - mu) / sd).to_numpy()]) @ b
    scores[name] = pd.Series(s, index=t["participant"])
    rows.append({"model": name, "n_dev": len(d), "n_test": len(t), "auc_test": auc(t["vga2"], s),
                 "coef": dict(zip(["intercept"] + cols, np.round(b, 3)))})
common = tst.set_index("participant").loc[scores["M0_age_sensor_cadence"].index.intersection(
    scores["M1_plus_head_features"].index)]
comb = pd.DataFrame({"y": common["vga2"], "m0": scores["M0_age_sensor_cadence"].reindex(common.index),
                     "m1": scores["M1_plus_head_features"].reindex(common.index)}).reset_index()
d_auc = auc(comb["y"], comb["m1"]) - auc(comb["y"], comb["m0"])
ci = boot(lambda b: auc(b["y"], b["m1"]) - auc(b["y"], b["m0"]), comb)
inc = pd.DataFrame(rows)
inc.to_csv(OUT / "vga_incremental.csv", index=False)
S["vga_incremental"] = {"models": inc.to_dict("records"), "delta_auc_m1_m0": d_auc, "delta_ci": ci, "n_common": len(comb)}

# ----------------------------------------------------------------------------- 5 screening by VGA
sg = pd.read_csv(R11 / "test_segments.csv")
sg = sg[(sg["loc"] == "HE") & (sg["method"] == "A1") & np.isfinite(sg["e_C"])]
sg = sg.merge(qc[["trial", "HE_step_regularity"]], on="trial").merge(meta[["trial", "vga"]], on="trial", how="left")
dev_sr = qc[(qc["set"] == "dev") & (qc["exclusion"].fillna("") == "")]["HE_step_regularity"].dropna()
thr = float(np.percentile(dev_sr, 10))
sg = sg[np.isfinite(sg["HE_step_regularity"])]
sg["excluded"] = sg["HE_step_regularity"] < thr
sg["big"] = sg["e_C"].abs() > 5
sg["vga_lvl"] = sg["vga"].clip(upper=3)
gt = pd.read_csv(R11 / "test_gating.csv")
gt = gt[gt["threshold_dps"] == 30].merge(meta[["trial", "vga"]], on="trial", how="left")
gt["vga_lvl"] = gt["vga"].clip(upper=3)
scr = (sg.groupby("vga_lvl").agg(n_segments=("trial", "size"), n_participants=("participant", "nunique"),
                                  excluded_pct=("excluded", lambda x: 100 * x.mean()),
                                  big_pct=("big", lambda x: 100 * x.mean()))
       .join(gt.groupby("vga_lvl").agg(gate_time_kept=("A2_time_coverage", "mean"),
                                        turn_sensitivity=("turn_sensitivity", "median"))))
scr.to_csv(OUT / "screening_by_vga.csv")
S["screening_by_vga"] = {"sr_threshold": thr, "table": scr.round(3).reset_index().to_dict("records"),
                         "spearman_excluded_vs_vga": ss.spearmanr(sg["vga"], sg["excluded"], nan_policy="omit").correlation}

(R15 / "v15_summary.json").write_text(json.dumps(S, indent=1, default=str),
                                      encoding="utf-8")
print(json.dumps(S, indent=1, default=str)[:4000])
