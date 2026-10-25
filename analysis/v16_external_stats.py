"""Statistics for the frozen DUO-GAIT external validation. Unit of analysis: participant (16); passes nested in walks
nested in participants. Usage: python v16_external_stats.py EXT_DIR"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as ss

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from headimu.stats import bland_altman_repeated  # noqa: E402
from run_v16_trust import auc, auprc, keep_by_risk  # noqa: E402

# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/v16_external_stats.py EXT_DIR')
        raise SystemExit(0)
    if len(sys.argv) < 2:
        print('Usage: python analysis/v16_external_stats.py EXT_DIR', file=sys.stderr)
        raise SystemExit(2)


D = Path(sys.argv[1])
S = pd.read_csv(D / "external_passes.csv")
W = pd.read_csv(D / "external_walks.csv")
S["participant"] = S["sub"]
rng = np.random.default_rng(20261023)
B = 2000
M = [k for k in ("B0", "B1", "B2") if f"{k}_e" in S]
OUT = {"n_participants": int(S["sub"].nunique()), "n_walks": int(len(W)), "n_passes": int(len(S))}


def pboot(df, fn):
    ids = df["participant"].unique(); g = {k: v for k, v in df.groupby("participant")}
    v = []
    for _ in range(B):
        bs = pd.concat([g[i] for i in rng.choice(ids, len(ids))], ignore_index=True)
        r = fn(bs)
        if np.isfinite(r):
            v.append(r)
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) > 50 else [np.nan, np.nan]


def mae(df, k):
    d = df[np.isfinite(df[f"{k}_e"])]
    return float(d.assign(a=d[f"{k}_e"].abs()).groupby("participant")["a"].median().median())


def block(df):
    r = {"n_passes": len(df)}
    for k in M:
        e = df[f"{k}_e"]; ok = np.isfinite(e)
        r[k] = {"mae_participant_median": mae(df, k), "mae_ci": pboot(df, lambda b, k=k: mae(b, k)),
                "rel_pct": float((e[ok].abs() / df.loc[ok, "C_ref"] * 100).groupby(df.loc[ok, "participant"]).median().median()),
                "p90_abs": float(e[ok].abs().quantile(0.9)), "no_output_pct": 100 * float((~ok).mean()),
                "big_pct": 100 * float((e[ok].abs() > 5).mean()),
                "ba": bland_altman_repeated(df.assign(imu=df[f"{k}_C"], ref=df["C_ref"])[ok], "imu", "ref")}
    return r


OUT["all"] = block(S)
OUT["by_condition"] = {c: block(g) for c, g in S.groupby("cond")}
# condition effect on head-only error (participant medians; Friedman across the four conditions)
for k in ("B1",):
    pm = S.assign(a=S[f"{k}_e"].abs()).groupby(["participant", "cond"])["a"].median().unstack()
    pm = pm.dropna()
    OUT[f"{k}_friedman_conditions"] = {"n": len(pm), "p": float(ss.friedmanchisquare(*[pm[c] for c in pm]).pvalue),
                                       "medians": pm.median().round(3).to_dict()}
# detection
OUT["B1_turn_prf"] = (lambda tp, fp, fn: [tp / (tp + fp), tp / (tp + fn), 2 * tp / (2 * tp + fp + fn)])(
    W["B1_turn_tp"].sum(), W["B1_turn_fp"].sum(), W["B1_turn_fn"].sum())
for k in ("B1", "B2"):
    st = W.groupby("sub")[[f"{k}_step_tp", f"{k}_step_nd", f"{k}_step_nr"]].sum()
    OUT[f"{k}_step_f1_participant_median"] = float((2 * st[f"{k}_step_tp"] / (st[f"{k}_step_nd"] + st[f"{k}_step_nr"])).median())
    OUT[f"{k}_step_precision_recall"] = [float(W[f"{k}_step_tp"].sum() / W[f"{k}_step_nd"].sum()),
                                         float(W[f"{k}_step_tp"].sum() / W[f"{k}_step_nr"].sum())]
OUT["B1_walk_f1_median"] = float(W["B1_walk_f1"].median())
OUT["observed_lag_median"] = float(W["B1_median_lag_obs"].median())
# trust transfer
S["Q1_score"] = -S["sr_trial"]
y = S["big"]
OUT["n_large_errors_B0"] = int(y.sum())
tr = {}
if y.sum() >= 5 and (1 - y).sum() >= 5:
    for name in ["Q1_score", "Q2a_SR_trial", "Q2b_SR_segment", "Q2c_SR_plus_2", "Q2d_full"]:
        d = S[np.isfinite(S[name])]
        tr[name] = {"auroc": auc(d["big"], d[name]), "auroc_ci": pboot(d, lambda b, name=name: auc(b["big"], b[name])),
                    "auprc": auprc(d["big"], d[name])}
        if name != "Q1_score":
            tr[name]["brier"] = float(np.mean((d[name] - d["big"]) ** 2))
    curve = []
    for name in ["Q2a_SR_trial", "Q2c_SR_plus_2", "Q2d_full"]:
        for c in (1.0, 0.95, 0.9, 0.8):
            k = keep_by_risk(S[name].fillna(1).to_numpy(), c)
            curve.append({"method": name, "coverage": c, "big_pct": 100 * y.to_numpy()[k].mean()})
    tr["error_coverage"] = curve
for f in ("Q1_flag", "Q2a_SR_trial_flag", "Q2c_SR_plus_2_flag", "Q2d_full_flag"):
    tr[f + "_flagged_pct"] = 100 * float(S[f].mean())
OUT["trust_transfer"] = tr
OUT["sr_seg_quantiles"] = S["sr_seg"].quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(3).to_dict()
OUT["pass_duration_median"] = float(S["dur"].median())
OUT["cadence_ref_median"] = float(S["C_ref"].median())
(D / "external_stats.json").write_text(json.dumps(OUT, indent=1, default=float), encoding="utf-8")
print(json.dumps(OUT, indent=1, default=float)[:7000])
