#!/usr/bin/env python3
"""V17, POST HOC: does the head move apart from the trunk in segments where only the head cadence fails?

Motivation. In the fixed test set, 72 segments had a large error (|e_C| > 5 steps/min, B0, A1) at the head only; 19 of
them in PD (16 participants). Head angular-rate magnitude alone did not explain them. Here the head and lower-back
(LB, L4/L5) signals of the same walk are analysed together. Measures per straight segment (definitions fixed here,
before looking at results):

  sr_he, sr_lb        step regularity (unbiased autocorrelation at the step lag) of band-passed |a|, each site
  xc_a1               max normalized cross-correlation of head and LB band-passed |a| within +/-0.15 s
                      (1 = head acceleration a copy of the trunk's, lower = head decoupled)
  lag_a1_s            lag of that maximum (head minus LB), also a synchronisation check
  coh_v               magnitude-squared coherence of head and LB vertical acceleration at the reference step
                      frequency (+/-0.25 Hz), Welch, 2.56-s windows
  tr_v                transmission ratio RMS(head vertical acc) / RMS(LB vertical acc), band-passed
  yaw_rel_bp          RMS of (head - LB) angular rate about vertical, band-passed in the step band  [deg/s]
                      (head oscillating on the trunk at step frequency)
  yaw_rel_lf          RMS of (head - LB) angular rate about vertical, low-passed at 1 Hz, mean removed [deg/s]
                      (slow head turns relative to the trunk while walking straight)
  tilt_ratio          RMS |horizontal angular rate| head / LB, band-passed (nodding / rolling of head vs trunk)
  n_cand_he, n_cand_lb, n_ref   detected peaks (lag-corrected, within the segment) and reference heel strikes

Each site's own vertical is its gravity direction, so yaw rates about vertical are comparable between sensors whose
axes differ. Large-error groups use the published B0 A1 errors (test_segments.csv): neither / head only / both / LB
only. Comparisons: head only vs neither and head only vs both, overall and in PD (participant bootstrap, 2000), and a
logistic model for a head large error among segments without a LB large error (standardized measures + cohort).
Usage:  python analysis/v17_head_trunk.py RESULTS_V11 OUT --root VOISARD_ROOT [--jobs N]
        (--pack PACK --fake-lb : smoke test only; LB replaced by the head signal)"""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import coherence

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from analysis import v17_reviewer_checks as rc  # noqa: E402
from headimu import dsp, pipeline as pl  # noqa: E402
from headimu.evaluate import candidates  # noqa: E402
from headimu.features import signals, _regularity  # noqa: E402

# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v17_head_trunk.py RESULTS_V11 OUT --root VOISARD_ROOT [--jobs N]')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

FAKE = "--fake-lb" in sys.argv
rms = lambda x: float(np.sqrt(np.mean(np.square(x)))) if len(x) else np.nan  # noqa: E731


def _xc(a, b, fs, maxlag_s=0.15):
    a = (a - a.mean()) / (a.std() + 1e-12); b = (b - b.mean()) / (b.std() + 1e-12)
    L = int(round(maxlag_s * fs)); n = len(a); best, lag = -np.inf, 0
    for k in range(-L, L + 1):
        x, y = (a[k:], b[:n - k]) if k >= 0 else (a[:n + k], b[-k:])
        if len(x) < fs:
            continue
        r = float(np.mean(x * y))
        if r > best:
            best, lag = r, k
    return best, lag / fs


def _w(args):
    t, band_lo, lags = args
    cfg = rc.G["cfg"]
    tr = rc._load(t)
    fs = tr.fs
    if FAKE:
        tr.sensors["LB"] = tr.sensors["HE"]
    if "LB" not in tr.sensors or "HE" not in tr.sensors:
        return []
    w = pl.windows(tr, fs, cfg["detect"]["window_pad_s"])
    S, raw, cand = {}, {}, {}
    n = min(tr.sensors["HE"].acc.shape[0], tr.sensors["LB"].acc.shape[0])
    for loc in ("HE", "LB"):
        s = tr.sensors[loc]
        acc, gyr, valid = s.acc[:n], s.gyr[:n], s.valid[:n]
        S[loc] = signals(acc, gyr, fs, cfg, band_lo)
        g = dsp.gravity_dir(acc, fs, cfg["detect"]["gravity_lp_hz"])
        raw[loc] = dsp.lowpass(np.einsum("ij,ij->i", gyr, g), fs, 1.0)
        i0, i1 = max(0, int(w["full"][0] * fs)), min(n, int(w["full"][1] * fs))
        cand[loc] = candidates(S[loc]["A1"], fs, cfg, i0, i1, valid) - lags.get(f"{loc}_A1", 0.0)
    rows = []
    for sname, (a, b) in w["segs"].items():
        i0, i1 = int(round(a * fs)), min(n, int(round(b * fs)))
        if i1 - i0 < 2 * fs:
            continue
        H, L = S["HE"], S["LB"]
        hs = tr.hs[(tr.hs >= a) & (tr.hs <= b)]
        r = {"trial": t, "participant": tr.participant, "cohort": tr.cohort, "segment": sname, "n_ref": int(len(hs)),
             "dur_s": (i1 - i0) / fs}
        long_enough = i1 - i0 >= int(2 * cfg["autocorr"]["max_lag_s"] * fs)
        r["sr_he"] = _regularity(H["A1"][i0:i1], fs, cfg)[0] if long_enough else np.nan
        r["sr_lb"] = _regularity(L["A1"][i0:i1], fs, cfg)[0] if long_enough else np.nan
        r["xc_a1"], r["lag_a1_s"] = _xc(H["A1"][i0:i1], L["A1"][i0:i1], fs)
        f0 = 60.0 / np.median(np.diff(hs)) / 60.0 if len(hs) >= 3 else np.nan
        if np.isfinite(f0) and i1 - i0 >= 256:
            fr, C = coherence(H["v"][i0:i1], L["v"][i0:i1], fs=fs, nperseg=256)
            m = np.abs(fr - f0) <= 0.25
            r["coh_v"] = float(np.mean(C[m])) if m.any() else np.nan
        else:
            r["coh_v"] = np.nan
        r["rms_v_he"], r["rms_v_lb"] = rms(H["v"][i0:i1]), rms(L["v"][i0:i1])
        r["tr_v"] = r["rms_v_he"] / r["rms_v_lb"] if r["rms_v_lb"] > 0 else np.nan
        r["yaw_rel_bp"] = float(np.rad2deg(rms(H["wv"][i0:i1] - L["wv"][i0:i1])))
        d = raw["HE"][i0:i1] - raw["LB"][i0:i1]
        r["yaw_rel_lf"] = float(np.rad2deg(rms(d - d.mean())))
        th, tl = rms(np.linalg.norm(H["wh"][i0:i1], axis=1)), rms(np.linalg.norm(L["wh"][i0:i1], axis=1))
        r["tilt_ratio"] = th / tl if tl > 0 else np.nan
        for loc in ("HE", "LB"):
            c = cand[loc]
            r[f"n_cand_{loc.lower()}"] = int(((c >= a - 0.1) & (c <= b + 0.1)).sum())
        rows.append(r)
    return rows


MEAS = ["sr_he", "sr_lb", "xc_a1", "coh_v", "tr_v", "yaw_rel_bp", "yaw_rel_lf", "tilt_ratio"]


def main():
    a = sys.argv[1:]
    r11, out = Path(a[0]), Path(a[1]); out.mkdir(parents=True, exist_ok=True)
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 1
    mode, src = ("pack", a[a.index("--pack") + 1]) if "--pack" in a else (
        ("root", a[a.index("--root") + 1]) if "--root" in a else ("csv", None))
    cfg = json.loads((r11 / "config_used.json").read_text(encoding="utf-8"))
    cal = json.loads((r11 / "dev_calibration.json").read_text(encoding="utf-8"))
    pub = pd.read_csv(r11 / "test_segments.csv"); pub = pub[pub["method"] == "A1"]
    trials = sorted(pub["trial"].unique())
    if "--limit" in a:
        trials = trials[:int(a[a.index("--limit") + 1])]
    if "--from-csv" in a:      # re-run the summaries from a saved segment table
        D = pd.read_csv(a[a.index("--from-csv") + 1]); mode = "root (from csv)"
    else:
        with Pool(jobs, initializer=rc._init, initargs=(mode, src, cfg)) as pool:
            rows = sum(pool.map(_w, [(t, float(cal["band_lo_hz"]), cal["lags_s"]) for t in trials], chunksize=8), [])
        D = pd.DataFrame(rows)
        e = pub.pivot_table(index=["trial", "segment"], columns="loc", values="e_C").reset_index()
        e = e.rename(columns={"HE": "e_he", "LB": "e_lb"})
        D = D.merge(e, on=["trial", "segment"], how="inner")
        D = D[np.isfinite(D["e_he"]) & np.isfinite(D["e_lb"])].copy()
        D["big_he"], D["big_lb"] = D["e_he"].abs() > 5, D["e_lb"].abs() > 5
        D["kind"] = np.select([D.big_he & ~D.big_lb, D.big_he & D.big_lb, ~D.big_he & D.big_lb],
                              ["head_only", "both", "lb_only"], "neither")
        D.to_csv(out / "head_trunk_segments.csv", index=False)
    R = {"mode": mode, "fake_lb": FAKE, "n_segments": int(len(D)), "n_participants": int(D["participant"].nunique()),
         "lag_a1_s_quantiles": D["lag_a1_s"].quantile([0.05, 0.5, 0.95]).tolist(),
         "kind_counts": {k: D.groupby(["cohort", "kind"]).size().unstack(fill_value=0).to_dict("index")}["kind_counts"]
         if False else D.groupby(["cohort", "kind"]).size().unstack(fill_value=0).to_dict("index")}
    rng = np.random.default_rng(20261112)

    def med(d):
        return {f"{k}|{m}": float(g[m].median()) for k, g in d.groupby("kind") for m in MEAS + ["n_cand_he", "n_cand_lb", "n_ref"]}

    def boot(d, fn, B=2000):
        est = fn(d); parts = d["participant"].unique(); idx = d.groupby("participant").indices; dr = []
        for _ in range(B):
            pk = rng.choice(parts, len(parts), replace=True)
            dr.append(fn(d.iloc[np.concatenate([idx[p] for p in pk])]))
        dr = pd.DataFrame(dr)
        return {k: [est.get(k, np.nan), float(np.nanpercentile(dr[k], 2.5)) if k in dr else np.nan,
                    float(np.nanpercentile(dr[k], 97.5)) if k in dr else np.nan] for k in est}

    def diffs(d):
        r = {}
        for m in MEAS:
            g = d.groupby("kind")[m].median()
            for ref in ("neither", "both"):
                if "head_only" in g and ref in g:
                    r[f"{m}|head_only-{ref}"] = float(g["head_only"] - g[ref])
        return r

    for tag, d in (("All", D), ("PD", D[D["cohort"] == "PD"]), ("nonPD", D[D["cohort"] != "PD"])):
        R[f"medians_{tag}"] = med(d)
        R[f"diff_{tag}"] = boot(d, diffs) if d["kind"].eq("head_only").sum() >= 3 else {}
    # PD vs other cohorts on segments without any large error (is the PD head generally more decoupled?)
    N = D[D["kind"] == "neither"].copy(); N["is_pd"] = N["cohort"] == "PD"
    R["neither_PD_vs_other"] = boot(N, lambda d: {f"{m}|PD-other": float(d.loc[d.is_pd, m].median() - d.loc[~d.is_pd, m].median())
                                                  for m in MEAS}, 1000)
    # logistic: head large error among segments without LB large error
    from sklearn.linear_model import LogisticRegression
    X = ["sr_lb", "xc_a1", "tr_v", "yaw_rel_bp", "yaw_rel_lf", "tilt_ratio"]
    M0 = D[~D["big_lb"]].dropna(subset=X).copy()
    mu, sd = M0[X].mean(), M0[X].std()
    X = [x for x in X if sd[x] > 1e-9]          # (only matters in the --fake-lb smoke test)
    coh = sorted(M0["cohort"].unique())

    def lg(d):
        Z = (d[X] - mu[X]) / sd[X]
        C = pd.get_dummies(d["cohort"]).reindex(columns=coh[1:], fill_value=0).astype(float)
        y = d["big_he"].astype(int).to_numpy()
        if y.sum() < 3:
            return {x: np.nan for x in X}
        m = LogisticRegression(C=1e6, max_iter=3000).fit(pd.concat([Z, C], axis=1).to_numpy(), y)
        return {x: float(np.exp(c)) for x, c in zip(X, m.coef_[0][:len(X)])}
    R["logit_head_big_given_lb_ok"] = {"n": int(len(M0)), "events": int(M0["big_he"].sum()), "sd": sd.to_dict(),
                                       "OR_per_SD": boot(M0, lg, 1000)}
    (out / "head_trunk.json").write_text(json.dumps(R, indent=1, default=float))
    print(json.dumps({k: R[k] for k in ("n_segments", "n_participants", "lag_a1_s_quantiles")}, default=float))
    for tag in ("All", "PD"):
        print(tag, {k: round(v, 3) for k, v in R[f"medians_{tag}"].items() if "head_only" in k or "neither" in k})
        for k, v in R[f"diff_{tag}"].items():
            print(" ", k, [round(x, 3) for x in v])
    for k, v in R["logit_head_big_given_lb_ok"]["OR_per_SD"].items():
        print(" OR", k, [round(x, 2) for x in v])


if __name__ == "__main__":
    main()
