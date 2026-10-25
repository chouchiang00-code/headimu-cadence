"""Statistics for the V16 end-to-end experiment (test set; participant = unit of analysis).
Usage: python v16_endtoend_stats.py E2E_OUT"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as ss

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from headimu.stats import bland_altman_repeated, holm  # noqa: E402

# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/v16_endtoend_stats.py E2E_DIR')
        raise SystemExit(0)
    if len(sys.argv) < 2:
        print('Usage: python analysis/v16_endtoend_stats.py E2E_DIR', file=sys.stderr)
        raise SystemExit(2)


D = Path(sys.argv[1])
B = 2000
rng = np.random.default_rng(20261023)
seg = pd.read_csv(D / "endtoend_segments.csv")
tri = pd.read_csv(D / "endtoend_trials.csv")
seg, tri = seg[seg["set"] == "test"].copy(), tri[tri["set"] == "test"].copy()
seg = seg[np.isfinite(seg["C_ref"])]
OUT = {}
M = [k for k in ("B0", "B1", "B2", "B2t") if f"{k}_e" in seg.columns]
MD = [k for k in ("B1", "B2", "B2t") if f"{k}_step_tp" in tri.columns]


def pboot(df, fn):
    ids = df["participant"].unique()
    g = {k: v for k, v in df.groupby("participant")}
    v = []
    for _ in range(B):
        bs = pd.concat([g[i] for i in rng.choice(ids, len(ids))], ignore_index=True)
        r = fn(bs)
        if np.isfinite(r):
            v.append(r)
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def med_abs(df, col):
    d = df[np.isfinite(df[col])]
    return float(d.assign(a=d[col].abs()).groupby("participant")["a"].median().median())


def summarize(df, label):
    r = {"group": label, "n_participants": int(df["participant"].nunique()), "n_segments": len(df)}
    for k in M:
        e = df[f"{k}_e"]
        ok = np.isfinite(e)
        r[f"{k}_no_output_pct"] = 100 * float((~ok).mean())
        r[f"{k}_mae_med"] = med_abs(df, f"{k}_e") if ok.any() else np.nan
        r[f"{k}_rel_pct"] = float((df.loc[ok, f"{k}_e"].abs() / df.loc[ok, "C_ref"] * 100)
                                  .groupby(df.loc[ok, "participant"]).median().median()) if ok.any() else np.nan
        r[f"{k}_big_or_missing_pct"] = 100 * float(((~ok) | (e.abs() > 5)).mean())
        r[f"{k}_p90_abs"] = float(e[ok].abs().quantile(0.9)) if ok.any() else np.nan
    return r


rows = [summarize(seg, "All")] + [summarize(g, c) for c, g in seg.groupby("cohort")]
tab = pd.DataFrame(rows)
for k in M:
    ci = pboot(seg, lambda b, k=k: med_abs(b, f"{k}_e"))
    tab.loc[0, f"{k}_mae_ci"] = f"[{ci[0]:.2f}, {ci[1]:.2f}]"
tab.to_csv(D / "table_endtoend_by_cohort.csv", index=False)
OUT["by_cohort"] = tab.round(3).to_dict("records")

# Bland-Altman (repeated measures) on segments with output
ba = {}
for k in M:
    d = seg[np.isfinite(seg[f"{k}_C"])].copy()
    d["imu"], d["ref"] = d[f"{k}_C"], d["C_ref"]
    ba[k] = bland_altman_repeated(d, "imu", "ref")
OUT["bland_altman"] = ba

# paired comparisons of participant-level |e| on segments where both methods produced output
pairs, pv = [], []
for a, b in [x for x in (("B1", "B0"), ("B2", "B1"), ("B2", "B0"), ("B2t", "B2"), ("B2t", "B1")) if x[0] in M]:
    d = seg[np.isfinite(seg[f"{a}_e"]) & np.isfinite(seg[f"{b}_e"])]
    pa = d.assign(x=d[f"{a}_e"].abs()).groupby("participant")["x"].median()
    pb = d.assign(x=d[f"{b}_e"].abs()).groupby("participant")["x"].median()
    diff = pa - pb
    p = ss.wilcoxon(pa, pb).pvalue if (diff != 0).any() else 1.0
    pv.append(p)
    pairs.append({"comparison": f"{a} - {b}", "n_participants": len(diff), "median_diff": float(diff.median()),
                  "ci": pboot(d, lambda bb, a=a, b=b: float((bb.assign(x=bb[f"{a}_e"].abs()).groupby("participant")["x"].median()
                                                           - bb.assign(x=bb[f"{b}_e"].abs()).groupby("participant")["x"].median()).median())),
                  "p": p})
for r, ph in zip(pairs, holm(pv)):
    r["p_holm"] = ph
OUT["paired"] = pairs

# detection performance
def prf(tp, nd, nr):
    p = tp / nd if nd else np.nan; r = tp / nr if nr else np.nan
    return p, r, 2 * p * r / (p + r) if p + r else np.nan

det = {}
for k in MD:
    pw = tri.groupby("participant")[[f"{k}_walk_p", f"{k}_walk_r", f"{k}_walk_f1"]].mean().median()
    det[f"{k}_walking_participant_median"] = pw.to_dict()
    det[f"{k}_turn_prf"] = prf(tri[f"{k}_turn_tp"].sum(), tri[f"{k}_turn_tp"].sum() + tri[f"{k}_turn_fp"].sum(),
                                tri[f"{k}_turn_tp"].sum() + tri[f"{k}_turn_fn"].sum())
    st = tri.groupby("participant")[[f"{k}_step_tp", f"{k}_step_nd", f"{k}_step_nr"]].sum()
    f1 = 2 * st[f"{k}_step_tp"] / (st[f"{k}_step_nd"] + st[f"{k}_step_nr"])
    det[f"{k}_step_f1_participant_median"] = float(f1.median())
det["B1_turn_start_err_median"] = float(tri["B1_turn_start_err"].median())
det["B1_turn_end_err_median"] = float(tri["B1_turn_end_err"].median())
det["B1_turn_abs_boundary_err_median"] = float(pd.concat([tri["B1_turn_start_err"], tri["B1_turn_end_err"]]).abs().median())
for c in [x for x in ("B2_walk_on_delay", "B2_first_output_delay", "B2_turn_on_delay", "B2_turn_off_delay", "B2_confirm_latency",
          "B2t_first_output_delay", "B2t_confirm_latency", "B2t_turn_on_delay") if x in tri.columns]:
    det[c + "_median_iqr"] = [float(tri[c].median()), float(tri[c].quantile(0.25)), float(tri[c].quantile(0.75))]
for k in [x for x in ("B2", "B2t") if f"{x}_cont_mae" in seg.columns]:
    det[f"{k}_cont_mae_participant_median"] = float(seg.groupby("participant")[f"{k}_cont_mae"].median().median())
OUT["detection"] = det
cohort_det = []
for c, g in tri.groupby("cohort"):
    r = {"cohort": c}
    for k in MD:
        r[f"{k}_walk_f1"] = float(g.groupby("participant")[f"{k}_walk_f1"].mean().median())
        r[f"{k}_turn_f1"] = prf(g[f"{k}_turn_tp"].sum(), g[f"{k}_turn_tp"].sum() + g[f"{k}_turn_fp"].sum(),
                                g[f"{k}_turn_tp"].sum() + g[f"{k}_turn_fn"].sum())[2]
        st = g.groupby("participant")[[f"{k}_step_tp", f"{k}_step_nd", f"{k}_step_nr"]].sum()
        r[f"{k}_step_f1"] = float((2 * st[f"{k}_step_tp"] / (st[f"{k}_step_nd"] + st[f"{k}_step_nr"])).median())
    cohort_det.append(r)
pd.DataFrame(cohort_det).to_csv(D / "table_endtoend_detection_by_cohort.csv", index=False)
OUT["detection_by_cohort"] = pd.DataFrame(cohort_det).round(3).to_dict("records")
(D / "endtoend_stats.json").write_text(json.dumps(OUT, indent=1, default=float), encoding="utf-8")
print(json.dumps(OUT, indent=1, default=float)[:6000])
