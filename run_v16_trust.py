#!/usr/bin/env python3
"""V16 task 2: trustworthiness of head-IMU cadence (Q0 none, Q1 V15 SR rule, Q2 multi-feature error-risk model).

Usage: python run_v16_trust.py PACK.npz RESULTS_V11 E2E_OUT OUT
Inputs : head signals (pack), B0 segments with reference errors (E2E_OUT/b0_segments_all.csv, dev + test).
Outcome: large cadence error |e_C| > 5 steps/min of head A1 on reference-assisted straight segments (as in V15).
Q1     : trial step regularity < 0.32 (V15 rule, development 10th percentile; unchanged).
Q2     : ridge-logistic risk models (fixed L2 penalty, standardisation and coefficients from DEVELOPMENT segments only);
         operating threshold set on development so that the development flag rate equals that of Q1.
All features use the head signal only, given the segment boundaries.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as ss
from scipy.optimize import minimize
from scipy.signal import butter, sosfiltfilt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from headimu import dsp  # noqa: E402
from headimu.features import _regularity  # noqa: E402

FS = 100.0
BIG = 5.0
RNG = np.random.default_rng(20261023)
FEATS = ["sr_seg", "stride_reg_seg", "cv_iv", "disagree", "spec_prom", "spec_entropy", "peak_amp_cv", "time_cover",
         "w_rms", "log_dur"]
MODELS = {"Q2a_SR_trial": ["sr_trial"],
          "Q2b_SR_segment": ["sr_seg"],
          "Q2c_SR_plus_2": ["sr_seg", "disagree", "cv_iv"],
          "Q2d_full": FEATS}


def seg_features(a1, wn, peaks_s, a, b, cfg_ac):
    i0, i1 = int(round(a * FS)), int(round(b * FS))
    x = a1[i0:i1]
    f = {"log_dur": np.log(max(b - a, 0.1))}
    p = peaks_s[(peaks_s >= a - 0.1) & (peaks_s <= b + 0.1)]
    iv = np.diff(p)
    f["cv_iv"] = float(np.std(iv, ddof=1) / np.mean(iv)) if len(iv) >= 3 else np.nan
    f["time_cover"] = float(len(iv) * np.median(iv) / (b - a)) if len(iv) >= 1 else np.nan
    idx = np.clip(np.round(p * FS).astype(int), 0, len(a1) - 1)
    amp = a1[idx]
    f["peak_amp_cv"] = float(np.std(amp, ddof=1) / np.mean(amp)) if len(amp) >= 3 and np.mean(amp) > 0 else np.nan
    if len(x) >= int(2 * cfg_ac["max_lag_s"] * FS):
        f["sr_seg"], f["stride_reg_seg"] = _regularity(x, FS, {"autocorr": cfg_ac})
        Tac = dsp.autocorr_step_time(x, FS, cfg_ac["min_lag_s"], cfg_ac["max_lag_s"])
    else:
        f["sr_seg"] = f["stride_reg_seg"] = Tac = np.nan
    f["disagree"] = abs(60 / Tac - 60 / np.median(iv)) if (np.isfinite(Tac) and len(iv) >= 2) else np.nan
    xx = (x - x.mean()) * np.hanning(len(x))
    P = np.abs(np.fft.rfft(xx, 2048)) ** 2
    fr = np.fft.rfftfreq(2048, 1 / FS)
    band = (fr >= 0.6) & (fr <= 3.0)
    Pb = P[band] / max(P[band].sum(), 1e-12)
    k = np.argmax(Pb)
    f["spec_prom"] = float(Pb[np.abs(fr[band] - fr[band][k]) <= 0.15].sum())
    f["spec_entropy"] = float(-(Pb * np.log(Pb + 1e-12)).sum() / np.log(len(Pb)))
    f["w_rms"] = float(np.rad2deg(np.sqrt(np.mean(wn[i0:i1] ** 2))))
    return f


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
    y, s = np.asarray(y), np.asarray(s, float)
    pos, neg = s[y == 1], s[y == 0]
    return float(ss.mannwhitneyu(pos, neg).statistic / (len(pos) * len(neg))) if len(pos) and len(neg) else np.nan


def auprc(y, s):
    y, s = np.asarray(y), np.asarray(s, float)
    o = np.argsort(-s)
    y = y[o]
    tp = np.cumsum(y)
    prec = tp / np.arange(1, len(y) + 1)
    return float(np.sum(prec * y) / max(y.sum(), 1))


def boot(fn, df, B=2000):
    ids = df["participant"].unique()
    g = {k: v for k, v in df.groupby("participant")}
    v = []
    for _ in range(B):
        bs = pd.concat([g[i] for i in RNG.choice(ids, len(ids))], ignore_index=True)
        try:
            r = fn(bs)
            if np.isfinite(r):
                v.append(r)
        except Exception:
            pass
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) > 50 else [np.nan, np.nan]


def keep_by_risk(risk, cov):
    """Retain the fraction `cov` of segments with the lowest risk (ties broken by order)."""
    n = len(risk)
    k = int(round(cov * n))
    o = np.argsort(risk, kind="stable")
    m = np.zeros(n, bool)
    m[o[:k]] = True
    return m


def main():
    pack, res11, e2e, out = map(Path, sys.argv[1:5])
    out.mkdir(parents=True, exist_ok=True)
    z = np.load(pack)
    meta = {m["trial"]: m for m in json.loads(str(z["__meta__"]))}
    cfg = json.loads((res11 / "config_used.json").read_text(encoding="utf-8"))
    cal = json.loads((res11 / "dev_calibration.json").read_text(encoding="utf-8"))
    band_lo, lag = float(cal["band_lo_hz"]), float(cal["lags_s"]["HE_A1"])
    qc = pd.read_csv(res11 / "qc_trials.csv")
    b0 = pd.read_csv(e2e / "b0_segments_all.csv")
    b0 = b0[(b0["method"] == "A1") & np.isfinite(b0["e_C"])].copy()
    sos = butter(3, [band_lo, cfg["detect"]["band_hi_hz"]], btype="band", fs=FS, output="sos")
    rows = []
    from headimu.evaluate import candidates, windows
    from headimu.io_voisard import Trial, SensorData
    for t, g in b0.groupby("trial"):
        acc, gyr, valid = z[f"{t}|acc"].astype(float), z[f"{t}|gyr"].astype(float), z[f"{t}|valid"]
        hs = np.sort(np.concatenate([z[f"{t}|ref_hs_left"], z[f"{t}|ref_hs_right"]]))
        turn = z[f"{t}|ref_turn"]
        a1 = sosfiltfilt(sos, np.linalg.norm(acc, axis=1))
        wn = sosfiltfilt(sos, np.linalg.norm(gyr, axis=1))
        tr = Trial(t, "", "", "", "", None, None, FS, {}, z[f"{t}|ref_hs_left"], z[f"{t}|ref_hs_right"], tuple(turn), {}, [])
        w = windows(tr, FS, cfg["detect"]["window_pad_s"])
        i0, i1 = max(0, int(w["full"][0] * FS)), min(len(valid), int(w["full"][1] * FS))
        cand = candidates(a1, FS, cfg, i0, i1, valid) - lag
        for _, r in g.iterrows():
            a, b = w["segs"][r["segment"]]
            rows.append({"trial": t, "segment": r["segment"], **seg_features(a1, wn, cand, a, b, cfg["autocorr"])})
    F = pd.DataFrame(rows)
    D = b0.merge(F, on=["trial", "segment"]).merge(qc[["trial", "HE_step_regularity"]], on="trial", how="left")
    D = D.rename(columns={"HE_step_regularity": "sr_trial"})
    D["participant"] = D["trial"].map(lambda t: meta[t]["participant"])
    D["vga"] = D["trial"].map(lambda t: meta[t]["vga"])
    D["big"] = (D["e_C"].abs() > BIG).astype(int)
    D.to_csv(out / "trust_segments_features.csv", index=False)
    dev, test = D[D["set"] == "dev"].copy(), D[D["set"] == "test"].copy()
    S = {"n_dev": len(dev), "n_test": len(test), "base_rate_dev": dev["big"].mean(), "base_rate_test": test["big"].mean()}
    # ---- Q1 (unchanged V15 rule)
    thr_q1 = 0.318819057281164
    for d in (dev, test):
        d["Q1_flag"] = (d["sr_trial"] < thr_q1).astype(int)
    q1_rate_dev = float(dev["Q1_flag"].mean())
    # ---- Q2 models fitted on dev only
    coefs = {}
    for name, cols in MODELS.items():
        med = dev[cols].median()
        Xd = dev[cols].fillna(med)
        mu, sd = Xd.mean(), Xd.std().replace(0, 1)
        b = ridge_logit(((Xd - mu) / sd).to_numpy(), dev["big"].to_numpy())
        coefs[name] = {"intercept": b[0], **dict(zip(cols, b[1:])), "_impute": med.to_dict(), "_mu": mu.to_dict(), "_sd": sd.to_dict()}
        for d in (dev, test):
            X = ((d[cols].fillna(med) - mu) / sd).to_numpy()
            d[name] = 1 / (1 + np.exp(-(np.column_stack([np.ones(len(X)), X]) @ b)))
        thr = float(np.quantile(dev[name], 1 - q1_rate_dev))
        coefs[name]["_threshold_dev_matched"] = thr
        for d in (dev, test):
            d[name + "_flag"] = (d[name] > thr).astype(int)
    (out / "trust_models.json").write_text(json.dumps(coefs, indent=1, default=float), encoding="utf-8")
    # ---- discrimination and calibration on test
    res = []
    test["Q1_score"] = -test["sr_trial"]
    for name in ["Q1_score"] + list(MODELS):
        s = test[name]
        r = {"method": name, "auroc": auc(test["big"], s), "auroc_ci": boot(lambda b: auc(b["big"], b[name]), test),
             "auprc": auprc(test["big"], s), "auprc_ci": boot(lambda b: auprc(b["big"], b[name]), test)}
        if name != "Q1_score":
            p = test[name].to_numpy(); y = test["big"].to_numpy()
            r["brier"] = float(np.mean((p - y) ** 2))
            r["brier_ci"] = boot(lambda b: float(np.mean((b[name] - b["big"]) ** 2)), test)
            r["brier_null_test"] = float(np.mean((S["base_rate_dev"] - y) ** 2))
            lp = np.log(np.clip(p, 1e-6, 1 - 1e-6) / np.clip(1 - p, 1e-6, 1))
            b = ridge_logit(lp[:, None], y, lam=0.0)
            r["cal_intercept_slope"] = [float(b[0]), float(b[1])]
            q = pd.qcut(test[name], 10, duplicates="drop")
            r["reliability"] = test.groupby(q, observed=True).agg(pred=(name, "mean"), obs=("big", "mean"), n=("big", "size")).round(4).to_dict("records")
        if name != "Q1_score":
            r["delta_auroc_vs_Q2a"] = auc(test["big"], s) - auc(test["big"], test["Q2a_SR_trial"])
            r["delta_auroc_vs_Q2a_ci"] = boot(lambda b: auc(b["big"], b[name]) - auc(b["big"], b["Q2a_SR_trial"]), test)
        res.append(r)
    S["discrimination"] = res
    # ---- error-coverage curves (test)
    covs = np.round(np.arange(1.0, 0.595, -0.01), 2)
    curve = []
    for name in ["Q1_score"] + list(MODELS) + ["oracle"]:
        risk = test["e_C"].abs().to_numpy() if name == "oracle" else test[name].to_numpy()
        for c in covs:
            k = keep_by_risk(risk, c)
            curve.append({"method": name, "coverage": c, "big_pct": 100 * test["big"].to_numpy()[k].mean(),
                          "mae": float(test["e_C"].abs().to_numpy()[k].mean())})
    curve = pd.DataFrame(curve)
    curve.to_csv(out / "error_coverage_curve.csv", index=False)
    # matched-coverage comparison at 95.5% and 90%: Q2d vs SR (trial, continuous)
    mc = {}
    for c in (0.955, 0.90):
        def diff(b, c=c):
            k1 = keep_by_risk(b["Q2a_SR_trial"].to_numpy(), c); k2 = keep_by_risk(b["Q2d_full"].to_numpy(), c)
            return 100 * (b["big"].to_numpy()[k2].mean() - b["big"].to_numpy()[k1].mean())
        mc[str(c)] = {"Q2a_big_pct": 100 * test["big"].to_numpy()[keep_by_risk(test["Q2a_SR_trial"].to_numpy(), c)].mean(),
                      "Q2d_big_pct": 100 * test["big"].to_numpy()[keep_by_risk(test["Q2d_full"].to_numpy(), c)].mean(),
                      "Q2c_big_pct": 100 * test["big"].to_numpy()[keep_by_risk(test["Q2c_SR_plus_2"].to_numpy(), c)].mean(),
                      "diff_Q2d_minus_Q2a_pp": diff(test), "diff_ci": boot(diff, test)}
    S["matched_coverage"] = mc
    # ---- operating points and clinical bias (test)
    test["vga_lvl"] = test["vga"].clip(upper=3)
    ops = []
    for flag in ["Q1_flag"] + [m + "_flag" for m in MODELS]:
        for by in ("all", "cohort", "vga_lvl"):
            groups = [("all", test)] if by == "all" else list(test.groupby(by))
            for gname, g in groups:
                f, y = g[flag].astype(bool), g["big"].astype(bool)
                ops.append({"method": flag.replace("_flag", ""), "by": by, "group": gname, "n": len(g),
                            "retained_pct": 100 * (~f).mean(), "big_pct_all": 100 * y.mean(),
                            "big_pct_retained": 100 * y[~f].mean() if (~f).any() else np.nan,
                            "sensitivity": f[y].mean() if y.any() else np.nan,
                            "false_exclusion_pct": 100 * f[~y].mean() if (~y).any() else np.nan})
    ops = pd.DataFrame(ops)
    ops.to_csv(out / "trust_operating_points.csv", index=False)
    S["operating_points_all"] = ops[ops["by"] == "all"].round(4).to_dict("records")
    S["q1_dev_flag_rate"] = q1_rate_dev
    test.to_csv(out / "trust_test_scored.csv", index=False)
    (out / "trust_summary.json").write_text(json.dumps(S, indent=1, default=float), encoding="utf-8")
    print(json.dumps({k: S[k] for k in ("n_dev", "n_test", "base_rate_dev", "base_rate_test")}, default=float))


# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python run_v16_trust.py PACK.npz RESULTS_V11 E2E_OUT OUT')
        raise SystemExit(0)
    if len(sys.argv) < 5:
        print('Usage: python run_v16_trust.py PACK.npz RESULTS_V11 E2E_OUT OUT', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
