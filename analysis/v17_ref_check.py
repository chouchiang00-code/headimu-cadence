#!/usr/bin/env python3
"""V17, POST HOC: could some 'large errors' be errors of the reference (foot-IMU heel strikes) rather than of the IMUs?

Two independent signs, defined before looking at the large-error groups:
 (1) Reference plausibility, from the reference events alone (left/right heel strikes of the segment):
       alt_viol   number of consecutive heel strikes from the same foot (a missed contralateral heel strike)
       gap_ratio  longest reference interval / median interval (>= 1.6 suggests a missed heel strike)
       ref_suspect = alt_viol >= 1 or gap_ratio >= 1.6
 (2) Agreement of four IMU estimates that share no events with the reference (head A1, head AC, lower-back A1,
     lower-back AC; B0, published test_segments.csv):
       spread     max - min of the four cadences
       consensus_off = spread <= 3 steps/min and |median of the four - reference| > 5 steps/min
Large-error groups (|e_C| > 5, A1): both / head only / LB only / neither. Then the head and lower-back large-error
shares are recomputed without ref_suspect segments (participant bootstrap, 2000).
Usage: python analysis/v17_ref_check.py RESULTS_V11 PACK.npz OUT_DIR"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis import v17_reviewer_checks as rc  # noqa: E402
from headimu import pipeline as pl  # noqa: E402

# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v17_ref_check.py RESULTS_V11 PACK.npz OUT_DIR')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

r11, pack, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
cfg = json.loads((r11 / "config_used.json").read_text(encoding="utf-8"))
rc._init("pack", pack, cfg)
pub = pd.read_csv(r11 / "test_segments.csv")
rows = []
for t in sorted(pub["trial"].unique()):
    tr = rc._load(t); w = pl.windows(tr, tr.fs, cfg["detect"]["window_pad_s"])
    for sname, (a, b) in w["segs"].items():
        L = tr.hs_left[(tr.hs_left >= a) & (tr.hs_left <= b)]; R = tr.hs_right[(tr.hs_right >= a) & (tr.hs_right <= b)]
        ev = sorted([(x, 0) for x in L] + [(x, 1) for x in R])
        foot = np.array([f for _, f in ev]); tt = np.array([x for x, _ in ev])
        iv = np.diff(tt)
        rows.append({"trial": t, "segment": sname, "n_left": len(L), "n_right": len(R),
                     "alt_viol": int((np.diff(foot) == 0).sum()) if len(foot) > 1 else 0,
                     "gap_ratio": float(iv.max() / np.median(iv)) if len(iv) >= 2 else np.nan,
                     "ref_iv_cv": float(np.std(iv, ddof=1) / np.mean(iv)) if len(iv) >= 3 else np.nan})
R = pd.DataFrame(rows)
C = pub[pub["method"].isin(["A1", "AC"])].pivot_table(index=["trial", "segment", "participant", "cohort"],
                                                     columns=["loc", "method"], values="C_imu")
C.columns = [f"C_{l}_{m}" for l, m in C.columns]
E = pub[pub["method"] == "A1"].pivot_table(index=["trial", "segment"], columns="loc", values=["e_C", "C_ref"])
E.columns = [f"{v}_{l}" for v, l in E.columns]
D = C.reset_index().merge(E.reset_index(), on=["trial", "segment"]).merge(R, on=["trial", "segment"])
D = D[np.isfinite(D["e_C_HE"]) & np.isfinite(D["e_C_LB"])].copy()
D["C_ref"] = D["C_ref_HE"]
four = D[["C_HE_A1", "C_HE_AC", "C_LB_A1", "C_LB_AC"]]
D["spread"] = four.max(axis=1) - four.min(axis=1)
D["consensus"] = four.median(axis=1)
D["consensus_off"] = (D["spread"] <= 3) & ((D["consensus"] - D["C_ref"]).abs() > 5)
D["ref_suspect"] = (D["alt_viol"] >= 1) | (D["gap_ratio"] >= 1.6)
D["bh"], D["bl"] = D["e_C_HE"].abs() > 5, D["e_C_LB"].abs() > 5
D["kind"] = np.select([D.bh & ~D.bl, D.bh & D.bl, ~D.bh & D.bl], ["head_only", "both", "lb_only"], "neither")
D.to_csv(out / "ref_check_segments.csv", index=False)
res = {"n_segments": int(len(D))}
res["by_kind"] = D.groupby("kind").agg(n=("bh", "size"), ref_suspect=("ref_suspect", "mean"),
                                      consensus_off=("consensus_off", "mean"),
                                      either=("ref_suspect", lambda s: float((s | D.loc[s.index, "consensus_off"]).mean())),
                                      alt_viol_any=("alt_viol", lambda s: float((s >= 1).mean())),
                                      gap_ge_16=("gap_ratio", lambda s: float((s >= 1.6).mean()))).round(3).to_dict("index")
res["both_by_cohort"] = D[D.kind == "both"].groupby("cohort").agg(n=("bh", "size"), ref_suspect=("ref_suspect", "sum"),
                                                                 consensus_off=("consensus_off", "sum")).to_dict("index")
res["ref_suspect_by_cohort_all_segments"] = (100 * D.groupby("cohort")["ref_suspect"].mean()).round(1).to_dict()
rng = np.random.default_rng(20261112)


def rates(d):
    r = {"head": 100 * d.bh.mean(), "lb": 100 * d.bl.mean()}; r["diff"] = r["head"] - r["lb"]
    for c in ("CVA", "RIL", "PD"):
        g = d[d.cohort == c]
        r[f"{c}|head"], r[f"{c}|lb"] = 100 * g.bh.mean(), 100 * g.bl.mean()
    k = d.groupby("kind").size()
    for kk in ("both", "head_only", "lb_only"):
        r[f"n_{kk}"] = float(k.get(kk, 0))
    return r


def boot(d):
    est = rates(d); parts = d.participant.unique(); idx = d.groupby("participant").indices; dr = []
    for _ in range(2000):
        pk = rng.choice(parts, len(parts), replace=True); dr.append(rates(d.iloc[np.concatenate([idx[p] for p in pk])]))
    dr = pd.DataFrame(dr)
    return {k: [float(est[k]), float(np.nanpercentile(dr[k], 2.5)), float(np.nanpercentile(dr[k], 97.5))] for k in est}


res["all"] = boot(D)
K = D[~D.ref_suspect]
res["excl_ref_suspect"] = boot(K); res["excl_ref_suspect_n"] = [int(len(K)), int(K.participant.nunique())]
K2 = D[~(D.ref_suspect | D.consensus_off)]
res["excl_suspect_or_consensus"] = boot(K2); res["excl_suspect_or_consensus_n"] = [int(len(K2)), int(K2.participant.nunique())]
(out / "ref_check.json").write_text(json.dumps(res, indent=1, default=float))
print(json.dumps({k: res[k] for k in ("n_segments", "by_kind", "both_by_cohort", "ref_suspect_by_cohort_all_segments",
                                      "excl_ref_suspect_n", "excl_suspect_or_consensus_n")}, indent=0, default=float))
for tag in ("all", "excl_ref_suspect", "excl_suspect_or_consensus"):
    print(tag, {k: [round(x, 1) for x in v] for k, v in res[tag].items()})
