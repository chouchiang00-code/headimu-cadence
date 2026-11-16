#!/usr/bin/env python3
"""V17, POST HOC reviewer checks (B0, A1, fixed split).

 (R2) Trivial baseline: predict every test segment's cadence without looking at the IMU, as the development-set median
      reference cadence of the segment's cohort (and, second, of all development segments). If the head estimate were
      not much better than this, a 1.5 steps/min error would carry little information.
 (R3) Resolution of the primary metric. The primary cadence is 60 / median step interval; with 100 Hz event times the
      median interval moves in 10-ms steps (about 1.8 steps/min at 105 steps/min). Two alternatives with finer
      resolution are computed for the IMU and the reference in the same way:
        mean   : 60 / mean of the step intervals within 0.67-1.5 x the segment's median interval (outlier intervals,
                 e.g. a missed or extra step, are left out)
        count  : 60 * (number of events - 1) / (time from first to last event)  (no trimming)
 (R12) Segment length: errors grouped by the number of reference heel strikes in the segment, overall and within
      cohort (Mantel-Haenszel-style pooling of within-cohort large-error rates is reported as a check of confounding).

The public pack holds the head IMU only. With --root (the full Voisard data folder) the same is computed for the lower
back too. Usage:
  python analysis/v17_reviewer_checks.py RESULTS_V11 OUT --pack PACK.npz [--jobs N]
  python analysis/v17_reviewer_checks.py RESULTS_V11 OUT --root VOISARD_ROOT [--jobs N]
"""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from headimu import pipeline as pl, stats  # noqa: E402
from headimu.evaluate import candidates, _intervals  # noqa: E402

G = {}
ORDER = ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]


def _init(mode, src, cfg):
    G.update(mode=mode, src=src, cfg=cfg)
    if mode == "pack":
        G["z"] = np.load(src)
        G["meta"] = {m["trial"]: m for m in json.loads(str(G["z"]["__meta__"]))}
    else:
        from headimu import io_voisard as iov
        G["folders"] = {t: f for t, f in iov.discover(Path(src), cfg)}


def _load(t):
    if G["mode"] == "pack":
        from headimu.io_voisard import Trial, SensorData
        z, m = G["z"], G["meta"][t]
        return Trial(t, m["participant"], m["cohort"], str(m["visit"]), m["sensor_type"], m["age"], None, 100.0,
                     {"HE": SensorData(z[f"{t}|acc"].astype(float), z[f"{t}|gyr"].astype(float), z[f"{t}|valid"], {})},
                     z[f"{t}|ref_hs_left"], z[f"{t}|ref_hs_right"], tuple(z[f"{t}|ref_turn"]), {}, [])
    from headimu import io_voisard as iov
    return iov.load_trial(t, Path(G["folders"][t]), G["cfg"])


def cad(times, valid, fs, how):
    """Cadence (steps/min) from event times in one segment; valid=None for the reference."""
    iv = _intervals(np.asarray(times), valid, fs) if valid is not None else np.diff(times)
    if how == "median":
        return 60.0 / np.median(iv) if len(iv) >= 2 else np.nan
    if how == "mean":
        if len(iv) < 2:
            return np.nan
        md = np.median(iv)
        k = iv[(iv >= 0.67 * md) & (iv <= 1.5 * md)]
        return 60.0 / np.mean(k) if len(k) >= 2 else np.nan
    if how == "count":
        return 60.0 * (len(times) - 1) / (times[-1] - times[0]) if len(times) >= 3 else np.nan


def _w(args):
    t, band_lo, lags, is_test = args
    cfg = G["cfg"]
    tr = _load(t)
    fs = tr.fs
    w = pl.windows(tr, fs, cfg["detect"]["window_pad_s"])
    rows = []
    for sname, (a, b) in w["segs"].items():
        r = tr.hs[(tr.hs >= a) & (tr.hs <= b)]
        base = {"trial": t, "participant": tr.participant, "cohort": tr.cohort, "segment": sname, "n_ref": len(r)}
        refc = {h: cad(r, None, fs, h) for h in ("median", "mean", "count")}
        if not is_test:
            rows.append({**base, "loc": "REF", **{f"ref_{h}": v for h, v in refc.items()}})
            continue
        for loc in ("HE", "LB"):
            s = tr.sensors.get(loc)
            if s is None:
                continue
            st = pl.static_slice(tr, fs, s.acc.shape[0], cfg["qc"]["min_static_s"])
            sig, _ = pl.branch_signals(s.acc, s.gyr, fs, cfg, band_lo, static=st, which=("A1",))
            i0, i1 = max(0, int(w["full"][0] * fs)), min(len(s.valid), int(w["full"][1] * fs))
            c = candidates(sig["A1"], fs, cfg, i0, i1, s.valid)
            lag = lags.get(f"{loc}_A1", 0.0)
            cc = c - lag
            cc = cc[(cc >= a - 0.1) & (cc <= b + 0.1)]
            row = {**base, "loc": loc, **{f"ref_{h}": v for h, v in refc.items()}}
            for h in ("median", "mean", "count"):
                row[f"imu_{h}"] = cad(cc + lag, s.valid if h != "count" else None, fs, h) if len(cc) else np.nan
            rows.append(row)
    return rows


def summ(df, err):
    d = df[np.isfinite(df[err])].assign(a=lambda x: x[err].abs())
    per = d.groupby("participant")["a"].median().to_numpy()
    m, lo, hi = stats.boot_ci(per, np.median, 2000, seed=1)[:3]
    return {"n_participants": int(len(per)), "n_segments": int(len(d)), "median": float(m), "lo": float(lo),
            "hi": float(hi), "big_pct": float(100 * (d["a"] > 5).mean()), "zero_pct": float(100 * (d["a"] < 1e-6).mean()),
            "mean_abs": float(d["a"].mean())}


def main():
    a = sys.argv[1:]
    r11, out = Path(a[0]), Path(a[1])
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 1
    mode, src = ("pack", a[a.index("--pack") + 1]) if "--pack" in a else ("root", a[a.index("--root") + 1])
    out.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((r11 / "config_used.json").read_text(encoding="utf-8"))
    cal = json.loads((r11 / "dev_calibration.json").read_text(encoding="utf-8"))
    qc = pd.read_csv(r11 / "qc_trials.csv")
    ok = qc[qc["exclusion"].fillna("") == ""]
    jobsl = [(t, float(cal["band_lo_hz"]), cal["lags_s"], s == "test") for t, s in zip(ok["trial"], ok["set"])]
    with Pool(jobs, initializer=_init, initargs=(mode, src, cfg)) as pool:
        rows = sum(pool.map(_w, jobsl, chunksize=16), [])
    D = pd.DataFrame(rows)
    D.to_csv(out / "reviewer_checks_segments.csv", index=False)
    dev = D[D["loc"] == "REF"]
    T = D[D["loc"] != "REF"].copy()
    for h in ("median", "mean", "count"):
        T[f"e_{h}"] = T[f"imu_{h}"] - T[f"ref_{h}"]
    # reproduction of the published primary metric
    pub = pd.read_csv(r11 / "test_segments.csv")
    pub = pub[(pub["method"] == "A1") & pub["loc"].isin(T["loc"].unique())]
    mm = T.merge(pub[["trial", "segment", "loc", "e_C"]], on=["trial", "segment", "loc"])
    dd = (mm["e_median"] - mm["e_C"]).abs()
    R = {"mode": mode, "reproduction": {"n": int(dd.notna().sum()), "max_abs_diff": float(dd.max()),
                                        "n_published_finite": int(np.isfinite(pub["e_C"]).sum())}}
    print(R["reproduction"])
    T = T[np.isfinite(T["e_median"])]           # same segments as the published primary analysis
    # (R2) trivial baselines from development reference cadence
    cmed = dev.groupby("cohort")["ref_median"].median().to_dict()
    gmed = float(dev["ref_median"].median())
    he = T[T["loc"] == "HE"].copy()
    he["e_base_cohort"] = he["cohort"].map(cmed) - he["ref_median"]
    he["e_base_all"] = gmed - he["ref_median"]
    R["baseline_dev_cohort_median_cadence"] = {k: float(v) for k, v in cmed.items()}
    R["baseline_dev_all_median_cadence"] = gmed
    R["R2"] = {}
    for c in ["All"] + ORDER:
        d = he if c == "All" else he[he["cohort"] == c]
        R["R2"][c] = {"head_A1": summ(d, "e_median"), "baseline_cohort_median": summ(d, "e_base_cohort"),
                      "baseline_all_median": summ(d, "e_base_all"),
                      "pearson_r_head_vs_ref": float(np.corrcoef(d["imu_median"], d["ref_median"])[0, 1]),
                      "ref_cadence_sd": float(d["ref_median"].std())}
    if "LB" in T["loc"].unique():
        lb = T[T["loc"] == "LB"]
        R["R2"]["All"]["lb_A1"] = summ(lb, "e_median")
    # (R3) alternative metrics
    R["R3"] = {}
    for loc in T["loc"].unique():
        d = T[T["loc"] == loc]
        R["R3"][loc] = {h: summ(d[np.isfinite(d[f"e_{h}"])], f"e_{h}") for h in ("median", "mean", "count")}
        R["R3"][loc]["ref_resolution_spm_at_median_cadence"] = float(
            60 / (60 / d["ref_median"].median() - 0.01) - d["ref_median"].median())
    if "LB" in T["loc"].unique():
        P = T.pivot_table(index=["trial", "segment", "participant"], columns="loc", values=["e_mean", "e_count"])
        R["R3"]["head_minus_lb"] = {}
        for h in ("mean", "count"):
            x = P[f"e_{h}"].dropna()
            pm = x.abs().groupby(level="participant").median()
            dlt = (pm["HE"] - pm["LB"]).to_numpy()
            m, lo, hi = stats.boot_ci(dlt, np.median, 2000, seed=2)[:3]
            R["R3"]["head_minus_lb"][h] = {"median_diff": float(m), "lo": float(lo), "hi": float(hi)}
    # (R12) segment length
    bins = [0, 10, 15, 20, 999]
    labs = ["5-10", "11-15", "16-20", ">20"]
    R["R12"] = {}
    for loc in T["loc"].unique():
        d = T[T["loc"] == loc].assign(g=lambda x: pd.cut(x["n_ref"], bins, labels=labs), a=lambda x: x["e_median"].abs())
        R["R12"][loc] = {}
        for g in labs:
            s = d[d["g"] == g]
            if len(s):
                R["R12"][loc][g] = {**summ(s, "e_median"), "cohort_mix_pct": (100 * s["cohort"].value_counts(normalize=True)).round(1).to_dict(),
                                    "ref_cadence_median": float(s["ref_median"].median())}
        # within-cohort: large-error rate short (<=10) vs longer (>10), pooled with cohort weights (MH risk difference)
        num, den, per = 0.0, 0.0, {}
        for c, s in d.groupby("cohort"):
            sh, lo_ = s[s["n_ref"] <= 10], s[s["n_ref"] > 10]
            if len(sh) and len(lo_):
                rd = (sh["a"] > 5).mean() - (lo_["a"] > 5).mean()
                wgt = len(sh) * len(lo_) / len(s)
                num += wgt * rd; den += wgt
                per[c] = {"short_n": int(len(sh)), "long_n": int(len(lo_)), "big_short_pct": float(100 * (sh["a"] > 5).mean()),
                          "big_long_pct": float(100 * (lo_["a"] > 5).mean())}
        R["R12"][loc]["within_cohort_short_vs_long"] = per
        R["R12"][loc]["mh_risk_difference_pp"] = float(100 * num / den) if den else None
        R["R12"][loc]["spearman_nref_vs_refcadence"] = float(d[["n_ref", "ref_median"]].corr("spearman").iloc[0, 1])
    (out / "reviewer_checks.json").write_text(json.dumps(R, indent=1, default=float))
    print(json.dumps(R, indent=1, default=float)[:6000])


# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v17_reviewer_checks.py RESULTS_V11 OUT --pack PACK.npz [--jobs N]')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

if __name__ == "__main__":
    main()
