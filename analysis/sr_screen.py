"""Post hoc step-regularity (SR) screen (exploratory).
Usage: python sr_screen.py RESULTS_DIR [OUT_JSON]
SR = head step regularity per trial (qc_trials.csv: HE_step_regularity).
Threshold = percentile of development-set trial SR (p5/p10/p20); evaluated on test HE-A1 segments."""
import sys, json
import numpy as np, pandas as pd
from scipy.stats import mannwhitneyu


def roc_auc_score(y, s):
    """AUC = P(score_pos > score_neg) (Mann-Whitney U), no scikit-learn dependency."""
    y, s = np.asarray(y), np.asarray(s, float)
    pos, neg = s[y == 1], s[y == 0]
    return float(mannwhitneyu(pos, neg).statistic / (len(pos) * len(neg)))

# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/sr_screen.py RESULTS_DIR [OUT_JSON]')
        raise SystemExit(0)
    if len(sys.argv) < 2:
        print('Usage: python analysis/sr_screen.py RESULTS_DIR [OUT_JSON]', file=sys.stderr)
        raise SystemExit(2)


res = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
qc = pd.read_csv(f"{res}/qc_trials.csv")
seg = pd.read_csv(f"{res}/test_segments.csv")
BIG = 5.0

def prep(loc, method):
    s = seg[(seg.loc_ == loc) & (seg.method == method)] if "loc_" in seg else seg[(seg["loc"] == loc) & (seg.method == method)]
    s = s.merge(qc[["trial", "HE_step_regularity", "LB_step_regularity"]], on="trial", how="left")
    s = s[np.isfinite(s.e_C)].copy()
    s["big"] = (s.e_C.abs() > BIG).astype(int)
    return s

def loa(e):  # simple segment-level LoA (repeated-measures LoA reported elsewhere)
    return e.mean() - 1.96 * e.std(ddof=1), e.mean() + 1.96 * e.std(ddof=1)

def part_bigshare(s):  # participant-level mean of large-error indicator, then mean
    return s.groupby("participant").big.mean().mean() * 100

he = prep("HE", "A1"); lb = prep("LB", "A1")
he = he[np.isfinite(he.HE_step_regularity)]
dev_sr = qc[(qc.set == "dev") & qc.exclusion.isna()].HE_step_regularity.dropna()
R = {"n_segments": int(len(he)), "auc_head": roc_auc_score(he.big, -he.HE_step_regularity),
     "auc_head_sr_lb_err": roc_auc_score(lb.dropna(subset=["HE_step_regularity"]).big,
                                         -lb.dropna(subset=["HE_step_regularity"]).HE_step_regularity),
     "auc_lb_sr_lb_err": roc_auc_score(lb.dropna(subset=["LB_step_regularity"]).big,
                                       -lb.dropna(subset=["LB_step_regularity"]).LB_step_regularity),
     "all": {"big_seg_pct": he.big.mean() * 100, "loa": loa(he.e_C)}, "ops": {}}
rng = np.random.default_rng(20261022)
_g = {q: x for q, x in he.groupby("participant")}; _p = he.participant.unique(); _a = []
for _ in range(1000):
    bs = pd.concat([_g[q] for q in rng.choice(_p, len(_p))])
    if bs.big.nunique() == 2: _a.append(roc_auc_score(bs.big, -bs.HE_step_regularity))
R["auc_head_ci"] = list(np.percentile(_a, [2.5, 97.5]))
for pc in (5, 10, 20):
    thr = float(np.percentile(dev_sr, pc))
    keep = he.HE_step_regularity >= thr
    k = he[keep]
    coh = (1 - he.groupby("cohort").apply(lambda d: (d.HE_step_regularity >= thr).mean())) * 100
    tp = ((~keep) & (he.big == 1)).sum(); fn = (keep & (he.big == 1)).sum()
    tn = (keep & (he.big == 0)).sum(); fp = ((~keep) & (he.big == 0)).sum()
    # random removal of the same number of segments
    rb = []
    for _ in range(200):
        idx = rng.choice(len(he), keep.sum(), replace=False); rb.append(he.big.iloc[idx].mean() * 100)
    # participant bootstrap of difference in large-error share (kept - all)
    parts = he.participant.unique(); d = []
    g = {p: x for p, x in he.groupby("participant")}
    for _ in range(2000):
        bs = pd.concat([g[p] for p in rng.choice(parts, len(parts))])
        d.append(bs[bs.HE_step_regularity >= thr].big.mean() * 100 - bs.big.mean() * 100)
    R["ops"][f"p{pc}"] = {"thr": thr, "seg_cov": keep.mean(), "trial_cov": k.trial.nunique() / he.trial.nunique(),
        "n_trials_kept": int(k.trial.nunique()), "n_trials": int(he.trial.nunique()),
        "part_cov": k.participant.nunique() / he.participant.nunique(),
        "n_part_lost": int(he.participant.nunique() - k.participant.nunique()),
        "big_seg_pct": k.big.mean() * 100, "diff_pp": k.big.mean() * 100 - he.big.mean() * 100,
        "diff_ci": list(np.percentile(d, [2.5, 97.5])), "random_big_pct": float(np.mean(rb)),
        "loa": loa(k.e_C), "sens": tp / (tp + fn), "spec": tn / (tn + fp),
        "excl_by_cohort_pct": coh.round(1).to_dict()}
# screening curve for Fig. 8(d): drop the lowest-SR segments in 1% steps
curve = []
for q in np.arange(0, 0.41, 0.01):
    t = float(np.quantile(he.HE_step_regularity, q)) if q > 0 else float(he.HE_step_regularity.min()) - 1
    k = he[he.HE_step_regularity >= t] if q > 0 else he
    lo, hi = loa(k.e_C)
    curve.append({"t": t, "cov": len(k) / len(he), "big": k.big.mean() * 100, "loa": (hi - lo) / 2})
o = R["ops"]["p10"]; lo, hi = o["loa"]
R_curve = {"thr": o["thr"], "curve": curve, "all_big": R["all"]["big_seg_pct"],
           "all_halfw": (R["all"]["loa"][1] - R["all"]["loa"][0]) / 2,
           "op": {"cov": o["seg_cov"], "big": o["big_seg_pct"], "halfw": (hi - lo) / 2}}
from pathlib import Path
json.dump(R_curve, open((Path(out).parent if out else Path(res)) / "sr_curve.json", "w"), default=float)
txt = json.dumps(R, indent=1, default=float)
print(txt)
if out: open(out, "w").write(txt)
