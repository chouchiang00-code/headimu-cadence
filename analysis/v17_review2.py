"""V17, POST HOC checks for a second critical review (B0, A1, fixed split, test set). Descriptive; not prespecified.
 (C1) Confounding of the SR–large-error association by walking slowness and signal amplitude. Head large error
      (|e_C|>5) and lower-back large error are modelled with logistic regression on standardized head segment SR,
      reference cadence (proxy for walking speed; gait speed is not used) and log head A1 amplitude (RMS of the
      band-passed A1 signal in the segment), with cohort indicators. 95% CIs: participant bootstrap (1000).
      Also: large-error share by SR (<0.6 / >=0.6) within reference-cadence tertiles.
 (C2) Tail risk: share of segments with |e_C|>5 for head and lower back by cohort, and the paired difference
      (head - lower back) with participant-bootstrap 95% CIs (2000).
 (C3) Head-only large errors: SR, cadence, head amplitude and head angular-rate RMS (w_rms) in segments with a large
      error at the head only, at both locations, at the lower back only, and at neither; overall and in PD.
Usage: python analysis/v17_review2.py RESULTS_V11 PACK.npz TRUST_DIR OUT_DIR"""
import sys
# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v17_review2.py RESULTS_V11 PACK.npz TRUST_DIR OUT_DIR')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis import v17_reviewer_checks as rc  # noqa: E402
from headimu import pipeline as pl  # noqa: E402

r11, pack, trd, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]); out.mkdir(parents=True, exist_ok=True)
cfg = json.loads((r11 / "config_used.json").read_text(encoding="utf-8"))
cal = json.loads((r11 / "dev_calibration.json").read_text(encoding="utf-8"))
rc._init("pack", pack, cfg)
T = pd.read_csv(trd / "trust_test_scored.csv")
seg = pd.read_csv(r11 / "test_segments.csv"); seg = seg[seg["method"] == "A1"]
lb = seg[seg["loc"] == "LB"][["trial", "segment", "e_C"]].rename(columns={"e_C": "e_lb"})
# head A1 amplitude per segment
amp = []
for t in T["trial"].unique():
    tr = rc._load(t); fs = tr.fs; s = tr.sensors["HE"]
    w = pl.windows(tr, fs, cfg["detect"]["window_pad_s"])
    st = pl.static_slice(tr, fs, s.acc.shape[0], cfg["qc"]["min_static_s"])
    sig, _ = pl.branch_signals(s.acc, s.gyr, fs, cfg, float(cal["band_lo_hz"]), static=st, which=("A1",))
    for sname, (a, b) in w["segs"].items():
        x = sig["A1"][int(a * fs):int(b * fs) + 1]; v = s.valid[int(a * fs):int(b * fs) + 1].astype(bool)
        amp.append({"trial": t, "segment": sname, "amp": float(np.sqrt(np.nanmean(x[v] ** 2))) if v.any() else np.nan})
D = T.merge(pd.DataFrame(amp), on=["trial", "segment"]).merge(lb, on=["trial", "segment"])
D = D[np.isfinite(D["e_C"]) & np.isfinite(D["e_lb"])].copy()
D["bh"], D["bl"] = (D["e_C"].abs() > 5).astype(int), (D["e_lb"].abs() > 5).astype(int)
D["log_amp"] = np.log(D["amp"])
D.to_csv(out / "review2_segments.csv", index=False)
res = {"n_segments": int(len(D)), "n_participants": int(D["participant"].nunique())}
rng = np.random.default_rng(20261112)
parts = D["participant"].unique(); idx = D.groupby("participant").indices


def boot(fn, B):
    est = fn(D); dr = []
    for _ in range(B):
        pick = rng.choice(parts, len(parts), replace=True)
        dr.append(fn(D.iloc[np.concatenate([idx[p] for p in pick])]))
    dr = pd.DataFrame(dr)
    return {k: [float(est[k]), float(np.nanpercentile(dr[k], 2.5)), float(np.nanpercentile(dr[k], 97.5))] for k in est}


# ---- C1
X0 = ["sr_seg", "C_ref", "log_amp"]
M = D[X0].agg(["mean", "std"])
COH = sorted(D["cohort"].unique())


def logit(d, y, xs):
    d = d.dropna(subset=X0)
    Z = (d[xs] - M.loc["mean", xs]) / M.loc["std", xs]
    C = pd.get_dummies(d["cohort"]).reindex(columns=COH[1:], fill_value=0).astype(float)
    m = LogisticRegression(C=1e6, max_iter=2000).fit(pd.concat([Z, C], axis=1).to_numpy(), d[y].to_numpy())
    return dict(zip(xs, np.exp(m.coef_[0][:len(xs)])))


def c1(d):
    r = {}
    for y in ("bh", "bl"):
        for tag, xs in (("sr_only", ["sr_seg"]), ("cad_amp", ["C_ref", "log_amp"]), ("full", X0)):
            for k, v in logit(d, y, xs).items():
                r[f"{y}|{tag}|{k}"] = v
    return r


res["C1_OR_per_SD"] = boot(c1, 1000)
res["C1_n_model"] = int(D.dropna(subset=X0).shape[0])
res["C1_SD"] = {k: float(M.loc["std", k]) for k in X0}
D["cad_t"] = pd.qcut(D["C_ref"], 3, labels=["slow", "mid", "fast"])
D["sr_lo"] = D["sr_seg"] < 0.6
res["C1_strata"] = {f"{c}|{'SR<0.6' if s_ else 'SR>=0.6'}": {"n": int(len(g)), "head_pct": 100 * g["bh"].mean(),
                    "lb_pct": 100 * g["bl"].mean()} for (c, s_), g in D.groupby(["cad_t", "sr_lo"], observed=True)}
res["C1_cad_tertile_edges"] = [float(x) for x in D["C_ref"].quantile([1 / 3, 2 / 3])]
res["corr_spearman"] = D[X0 + ["w_rms"]].corr("spearman").round(3).to_dict()
# ---- C2
ORDER = ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]


def c2(d):
    r = {}
    for c in ORDER + ["All"]:
        g = d if c == "All" else d[d["cohort"] == c]
        r[f"{c}|head"] = 100 * g["bh"].mean(); r[f"{c}|lb"] = 100 * g["bl"].mean()
        r[f"{c}|diff"] = r[f"{c}|head"] - r[f"{c}|lb"]
    return r


res["C2"] = boot(c2, 2000)
res["C2_n"] = {c: [int((D["cohort"] == c).sum()), int(D.loc[D["cohort"] == c, "participant"].nunique())] for c in ORDER}
# ---- C3
D["kind"] = np.select([(D.bh == 1) & (D.bl == 0), (D.bh == 1) & (D.bl == 1), (D.bh == 0) & (D.bl == 1)],
                      ["head_only", "both", "lb_only"], "neither")
def c3(d):
    return d.groupby("kind").agg(n=("bh", "size"), sr=("sr_seg", "median"), cad=("C_ref", "median"),
                                 amp=("amp", "median"), w_rms=("w_rms", "median"), n_ref=("n_ref", "median")).round(3).to_dict("index")
res["C3_all"] = c3(D); res["C3_PD"] = c3(D[D["cohort"] == "PD"])
(out / "review2.json").write_text(json.dumps(res, indent=1, default=float))
print(json.dumps({k: res[k] for k in ("n_segments", "C1_n_model", "C1_SD", "C1_cad_tertile_edges", "C1_strata", "C2_n", "C3_all", "C3_PD")}, indent=0, default=float))
for k, v in res["C1_OR_per_SD"].items(): print(k, [round(x, 2) for x in v])
for k, v in res["C2"].items(): print(k, [round(x, 1) for x in v])
print(res["corr_spearman"])
