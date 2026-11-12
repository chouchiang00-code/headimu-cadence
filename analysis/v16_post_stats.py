#!/usr/bin/env python3
"""V16 post hoc statistics (requested after the V16 draft; labelled post hoc in the manuscript).

Usage: python v16_post_stats.py RESULTS_V11 E2E_DIR TRUST_DIR EXT_DIR POST_DIR
(1) Gyroscope zero-rate calibration (needs v16_post_gyrocal.py with --window head and --window ref, dev and test, and
    v16_post_gyrocal_rule.py): participant-bootstrap 95% CIs of the test-set change in no-output and
    large-or-missing shares under the development-selected rule.
(2) Equivalence (two one-sided tests, TOST) of paired participant-level median |e_C|:
    B1 vs B0, B2 vs B1, B2-t vs B1, head A1 vs lower-back A1 (B0), and B1 vs B0 on DUO-GAIT. Margin = 1.8 steps/min,
    the one-sample quantization of cadence at the median step time (0.57 s at 100 Hz) reported in the manuscript;
    a difference smaller than one sample is not resolvable. Equivalence if the 90% CI lies inside +/-margin.
    Reported with both a paired t-test TOST and a participant-bootstrap 90% CI, plus the smallest margin that would
    pass (max |90% CI bound|).
(3) Sensitivity of the large-error threshold (3, 5, 10 steps/min): large-or-missing shares (B0/B1/B2/B2-t, all and
    by cohort), AUROC of Q1 / SR+2 / full model (models and flags frozen as fitted at 5 steps/min), large-error share
    kept at matched coverage, and retention / sensitivity / false exclusion at VGA >= 3.
Seed 20261023, 2000 participant-level bootstrap resamples. Writes POST_DIR/post_stats.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats as ss

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from run_v16_trust import auc, keep_by_risk  # noqa: E402

B = 2000
rng = np.random.default_rng(20261023)
MARGIN = 1.8


def pboot(df, fn, B=B, alpha=(2.5, 97.5)):
    parts = df["participant"].unique()
    groups = {p: g for p, g in df.groupby("participant")}
    vals = []
    for _ in range(B):
        pick = rng.choice(parts, len(parts), replace=True)
        vals.append(fn(pd.concat([groups[p] for p in pick], ignore_index=True)))
    v = np.asarray(vals, float)
    v = v[np.isfinite(v)]
    return [round(float(x), 3) for x in np.percentile(v, alpha)]


# --------------------------------------------------------------------------------------------- (2) equivalence
def tost(a, b, label):
    """a, b: Series of participant medians indexed by participant (paired)."""
    d = (a - b).dropna()
    n = len(d); md, sd = d.mean(), d.std(ddof=1); se = sd / np.sqrt(n)
    t_lo = (md + MARGIN) / se; t_hi = (md - MARGIN) / se
    p_lo = 1 - ss.t.cdf(t_lo, n - 1); p_hi = ss.t.cdf(t_hi, n - 1)
    ci90_t = [md - ss.t.ppf(0.95, n - 1) * se, md + ss.t.ppf(0.95, n - 1) * se]
    arr = d.to_numpy()
    bs = np.array([arr[rng.integers(0, n, n)].mean() for _ in range(B)])
    ci90_b = np.percentile(bs, [5, 95])
    return {"comparison": label, "n_participants": int(n), "mean_diff": round(float(md), 3),
            "median_diff": round(float(np.median(arr)), 3),
            "ci90_t": [round(float(x), 3) for x in ci90_t], "ci90_boot": [round(float(x), 3) for x in ci90_b],
            "p_tost": round(float(max(p_lo, p_hi)), 5), "margin": MARGIN,
            "equivalent": bool(max(p_lo, p_hi) < 0.05 and abs(ci90_b).max() < MARGIN),
            "smallest_margin_passing": round(float(max(np.abs(ci90_t).max(), np.abs(ci90_b).max())), 3)}


def pmed(df, col):
    return df.assign(a=df[col].abs()).groupby("participant")["a"].median()


def main():
    r11, e2e, trust, ext, post = map(Path, sys.argv[1:6])
    out = {}

    # (1) calibration CIs
    base = pd.read_csv(e2e / "endtoend_segments.csv"); base = base[(base["set"] == "test") & np.isfinite(base["C_ref"])]
    for win, suf in (("head", ""), ("ref", "_ref")):
        rule = json.loads((post / f"gyrocal_rule{suf}.json").read_text())
        thr = rule["selected_threshold_dps"]
        cor = pd.read_csv(post / f"gyrocal_segments_test{suf}.csv"); tri = pd.read_csv(post / f"gyrocal_trials_test{suf}.csv")
        m = base.merge(cor[["trial", "segment", "B1_e", "B2_e"]].rename(columns={"B1_e": "B1c", "B2_e": "B2c"}), on=["trial", "segment"]) \
                .merge(tri[["trial", "cal_offset_dps"]], on="trial")
        use = (m["cal_offset_dps"] > thr) if thr is not None else np.zeros(len(m), bool)
        res = {"selected_threshold_dps": thr, "trials_corrected": int(m.loc[use, "trial"].nunique())}
        for k in ("B1", "B2"):
            m[f"{k}r"] = np.where(use, m[f"{k}c"], m[f"{k}_e"])
            miss = lambda d, c: 100 * (~np.isfinite(d[c])).mean()
            bom = lambda d, c: 100 * ((~np.isfinite(d[c])) | (d[c].abs() > 5)).mean()
            res[k] = {"no_output_pct": [round(miss(m, f"{k}_e"), 2), round(miss(m, f"{k}r"), 2)],
                      "no_output_diff_pp": [round(miss(m, f"{k}r") - miss(m, f"{k}_e"), 2), pboot(m, lambda d: miss(d, f"{k}r") - miss(d, f"{k}_e"))],
                      "big_or_missing_pct": [round(bom(m, f"{k}_e"), 2), round(bom(m, f"{k}r"), 2)],
                      "big_or_missing_diff_pp": [round(bom(m, f"{k}r") - bom(m, f"{k}_e"), 2), pboot(m, lambda d: bom(d, f"{k}r") - bom(d, f"{k}_e"))]}
            both = m[np.isfinite(m[f"{k}_e"]) & np.isfinite(m[f"{k}r"])]
            res[k]["median_abs_err_on_common_segments"] = [round(float(pmed(both, f"{k}_e").median()), 3), round(float(pmed(both, f"{k}r").median()), 3)]
        out[f"gyrocal_{win}"] = res

    # (2) equivalence
    seg = base
    eq = []
    both = seg[np.isfinite(seg["B1_e"]) & np.isfinite(seg["B0_e"])]
    eq.append(tost(pmed(both, "B1_e"), pmed(both, "B0_e"), "B1 - B0 (Voisard test)"))
    both = seg[np.isfinite(seg["B2_e"]) & np.isfinite(seg["B1_e"])]
    eq.append(tost(pmed(both, "B2_e"), pmed(both, "B1_e"), "B2 - B1 (Voisard test)"))
    both = seg[np.isfinite(seg["B2t_e"]) & np.isfinite(seg["B1_e"])]
    eq.append(tost(pmed(both, "B2t_e"), pmed(both, "B1_e"), "B2-t - B1 (Voisard test)"))
    ts = pd.read_csv(r11 / "test_segments.csv")
    a1 = ts[ts["method"] == "A1"].pivot_table(index=["participant", "trial", "segment"], columns="loc", values="e_C").reset_index().dropna()
    eq.append(tost(pmed(a1, "HE"), pmed(a1, "LB"), "head A1 - lower-back A1 (B0, Voisard test)"))
    ex = pd.read_csv(ext / "external_passes.csv").rename(columns={"sub": "participant"})
    ex = ex[np.isfinite(ex["B1_e"]) & np.isfinite(ex["B0_e"])]
    eq.append(tost(pmed(ex, "B1_e"), pmed(ex, "B0_e"), "B1 - B0 (DUO-GAIT)"))
    out["equivalence"] = eq

    # (3) threshold sensitivity
    sens = []
    t = pd.read_csv(trust / "trust_test_scored.csv")
    for thr in (3, 5, 10):
        row = {"threshold": thr}
        for k in ("B0", "B1", "B2", "B2t"):
            e = seg[f"{k}_e"]
            row[f"{k}_big_or_missing_pct"] = round(100 * ((~np.isfinite(e)) | (e.abs() > thr)).mean(), 2)
        for c in ("CVA", "HS"):
            e = seg.loc[seg["cohort"] == c, "B0_e"]
            row[f"B0_big_pct_{c}"] = round(100 * (e.abs() > thr).mean(), 2)
        y = (t["e_C"].abs() > thr).astype(int)
        row["test_base_rate_pct"] = round(100 * y.mean(), 2)
        q = t[np.isfinite(t["sr_trial"])]
        row["AUROC_Q1"] = round(auc((q["e_C"].abs() > thr).astype(int), -q["sr_trial"]), 3)
        row["AUROC_Q1_ci"] = pboot(q, lambda d: auc((d["e_C"].abs() > thr).astype(int), -d["sr_trial"]), B=500)
        for name, col in (("SR+2", "Q2c_SR_plus_2"), ("full", "Q2d_full")):
            row[f"AUROC_{name}"] = round(auc(y, t[col]), 3)
        dq = t.dropna(subset=["Q2c_SR_plus_2"])
        row["AUROC_SR+2_minus_Q1_ci"] = pboot(q, lambda d: auc((d["e_C"].abs() > thr).astype(int), d["Q2c_SR_plus_2"])
                                              - auc((d["e_C"].abs() > thr).astype(int), -d["sr_trial"]), B=500)
        risk_sr = (-t["sr_trial"]).fillna(np.inf).to_numpy()
        for cov in (0.955, 0.9):
            for name, r in (("Q1", risk_sr), ("SR+2", t["Q2c_SR_plus_2"].to_numpy()), ("full", t["Q2d_full"].to_numpy())):
                k = keep_by_risk(r, cov)
                row[f"kept_big_pct_{name}_cov{int(cov * 1000)}"] = round(100 * y.to_numpy()[k].mean(), 2)
        g = t[t["vga"] >= 3]
        yg = (g["e_C"].abs() > thr)
        for name, flag in (("Q1", "Q1_flag"), ("SR+2", "Q2c_SR_plus_2_flag")):
            f = g[flag].astype(bool)
            row[f"VGA3_{name}_retained_pct"] = round(100 * (1 - f.mean()), 1)
            row[f"VGA3_{name}_sensitivity"] = round(float(f[yg].mean()), 3) if yg.any() else None
            row[f"VGA3_{name}_false_excl_pct"] = round(100 * float(f[~yg].mean()), 1)
        sens.append(row)
    out["threshold_sensitivity"] = sens
    (post / "post_stats.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


# Command-line diagnostics only; analysis statements are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/v16_post_stats.py RESULTS_V11 E2E_DIR TRUST_DIR EXT_DIR POST_DIR')
        raise SystemExit(0)
    if len(sys.argv) < 6:
        print('Usage: python analysis/v16_post_stats.py RESULTS_V11 E2E_DIR TRUST_DIR EXT_DIR POST_DIR', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
