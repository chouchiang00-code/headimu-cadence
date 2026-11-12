#!/usr/bin/env python3
"""V16 post hoc: a published open-source head/ear-worn step detector as an external baseline.

Usage: python v16_post_eargait.py PACK.npz RESULTS_V11 E2E_DIR OUT_DIR [--jobs N]
Detector: EarGait DiaoAdaptedEventDetection (re-implemented in headimu/eargait_diao.py with its published defaults; no
parameter is tuned). Input: superior-inferior acceleration = head specific force projected on the mean gravity direction
of the analysis window (EarGait aligns the sensor frame to gravity with a constant rotation). Same reference-assisted
windows, straight segments, interval rules and cadence metric as B0 (primary pipeline, evaluate.segment_metrics);
the only selected quantity is the event-time offset (lag) for event matching, taken as the median signed offset to the
nearest reference heel strike (|offset| <= 0.4 s) over DEVELOPMENT trials, as for B0.
Outputs: OUT_DIR/eargait_segments.csv (dev + test), eargait_events.csv, eargait_summary.json (test-set statistics with
participant-level bootstrap, paired against B0 head A1, seed 20261023).
"""
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import run_v16_endtoend as R  # noqa: E402
from headimu.eargait_diao import detect_ic, fir_lowpass  # noqa: E402
from headimu.evaluate import segment_metrics, match_events  # noqa: E402

FS = R.FS
CFG = json.loads((HERE / "config.json").read_text())


def one(args):
    t, acc, gyr, valid, hs, turn = args
    if hs.size < 4 or turn is None or len(turn) < 2:
        return t, None
    t0, t1 = hs[0] - CFG["detect"]["window_pad_s"], hs[-1] + CFG["detect"]["window_pad_s"]
    i0, i1 = max(0, int(t0 * FS)), min(len(acc), int(t1 * FS))
    lp = np.column_stack([fir_lowpass(acc[:, j], FS) for j in range(3)])
    w = lp[i0:i1]
    ok = np.isfinite(w).all(axis=1)
    w = w[ok]
    g = np.nanmean(w, axis=0); g /= np.linalg.norm(g)
    si = w @ g
    if len(si) <= 3 * FS:
        return t, None
    ic = detect_ic(si, FS) + i0
    ic = ic[valid[ic]]
    return t, ic / FS


def main():
    pack, r11, e2e, out = map(Path, sys.argv[1:5])
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 1
    out.mkdir(parents=True, exist_ok=True)
    z, meta = R.load_pack(pack)
    qc = pd.read_csv(r11 / "qc_trials.csv")
    sets = dict(zip(qc["trial"], qc["set"]))
    trials = [t for t in qc[qc["set"].isin(["dev", "test"])]["trial"] if t in meta]
    data = {t: R.get(z, t) for t in trials}
    args = [(t, *data[t]) for t in trials]
    run = (lambda f, it: list(ProcessPoolExecutor(jobs).map(f, it, chunksize=8))) if jobs > 1 else (lambda f, it: [f(x) for x in it])
    res = dict(run(one, args))
    # lag on development trials
    offs = []
    for t, ic in res.items():
        if ic is None or sets[t] != "dev":
            continue
        hs = data[t][3]
        d = ic[:, None] - hs[None, :]
        k = np.abs(d).argmin(axis=1)
        o = d[np.arange(len(ic)), k]
        offs += list(o[np.abs(o) <= 0.4])
    lag = float(np.median(offs))
    rows, ev = [], []
    tol = CFG["metrics"]["match_tol_s"]
    for t, ic in res.items():
        acc, gyr, valid, hs, turn = data[t]
        m = meta[t]
        base = {"trial": t, "participant": m["participant"], "cohort": m["cohort"], "sensor_type": m["sensor_type"],
                "vga": m.get("vga"), "set": sets[t]}
        if ic is None or hs.size < 4:
            continue
        segs = {"S1": (hs[0], turn[0]), "S2": (turn[1], hs[-1])}
        segc = []
        for s, seg in segs.items():
            r = segment_metrics(ic, lag, hs, seg, valid, FS, CFG)
            rows.append({**base, "segment": s, **r})
            c = ic - lag
            segc.append(c[(c >= seg[0] - 0.2) & (c <= seg[1] + 0.2)])
        refs = np.concatenate([hs[(hs >= a) & (hs <= b)] for a, b in segs.values()])
        mm = match_events(np.concatenate(segc), refs, tol)
        ev.append({**base, "tp": len(mm), "n_det": int(sum(len(x) for x in segc)), "n_ref": int(len(refs)),
                   "timing_mae_ms": 1000 * float(np.mean([abs(x[2]) for x in mm])) if mm else np.nan})
    seg = pd.DataFrame(rows); seg.to_csv(out / "eargait_segments.csv", index=False)
    evd = pd.DataFrame(ev); evd.to_csv(out / "eargait_events.csv", index=False)

    # ---- test-set statistics, paired with B0 (head A1) on the same segments
    rng = np.random.default_rng(20261023); B = 2000
    e = pd.read_csv(e2e / "endtoend_segments.csv")
    e = e[(e["set"] == "test") & np.isfinite(e["C_ref"])][["trial", "segment", "participant", "cohort", "C_ref", "B0_e", "B1_e"]]
    s = seg[seg["set"] == "test"][["trial", "segment", "e_C"]].rename(columns={"e_C": "EG_e"})
    m = e.merge(s, on=["trial", "segment"], how="left")
    parts = m["participant"].unique(); groups = {p: g for p, g in m.groupby("participant")}

    def pmed(d, c):
        x = d.assign(a=d[c].abs()).groupby("participant")["a"].median().dropna()
        return float(x.median())

    def boot(fn):
        v = [fn(pd.concat([groups[p] for p in rng.choice(parts, len(parts))], ignore_index=True)) for _ in range(B)]
        return [round(float(x), 3) for x in np.nanpercentile(v, [2.5, 97.5])]

    both = m[np.isfinite(m["EG_e"]) & np.isfinite(m["B0_e"])]
    pb = both.assign(a=both["EG_e"].abs(), b=both["B0_e"].abs()).groupby("participant")[["a", "b"]].median()
    dd = (pb["a"] - pb["b"]).to_numpy()
    summ = {
        "lag_s_dev": round(lag, 3), "n_test_segments": int(len(m)),
        "no_output_pct": round(100 * (~np.isfinite(m["EG_e"])).mean(), 2),
        "median_abs_err": round(pmed(m, "EG_e"), 3), "median_abs_err_ci": boot(lambda d: pmed(d, "EG_e")),
        "B0_median_abs_err": round(pmed(m, "B0_e"), 3),
        "rel_err_pct_median": round(float((100 * m["EG_e"].abs() / m["C_ref"]).median()), 2),
        "bias": round(float(m["EG_e"].mean()), 2),
        "loa": [round(float(m["EG_e"].mean() - 1.96 * m["EG_e"].std()), 1), round(float(m["EG_e"].mean() + 1.96 * m["EG_e"].std()), 1)],
        "large_or_missing_pct": round(100 * ((~np.isfinite(m["EG_e"])) | (m["EG_e"].abs() > 5)).mean(), 2),
        "B0_large_or_missing_pct": round(100 * ((~np.isfinite(m["B0_e"])) | (m["B0_e"].abs() > 5)).mean(), 2),
        "halving_pct": round(100 * float(seg[seg["set"] == "test"]["halving"].mean()), 2),
        "doubling_pct": round(100 * float(seg[seg["set"] == "test"]["doubling"].mean()), 2),
        "paired_diff_EG_minus_B0_participant_median": round(float(np.median(dd)), 3),
        "paired_diff_mean": round(float(dd.mean()), 3),
        "paired_diff_mean_ci95": [round(float(x), 3) for x in np.percentile([dd[rng.integers(0, len(dd), len(dd))].mean() for _ in range(B)], [2.5, 97.5])],
    }
    def dpair(d):
        a = d.assign(x=d["EG_e"].abs(), y=d["B0_e"].abs()).groupby("participant")[["x", "y"]].median()
        lm = lambda c: 100 * ((~np.isfinite(d[c])) | (d[c].abs() > 5)).mean()
        return a["x"].median() - a["y"].median(), lm("EG_e") - lm("B0_e")
    bs = np.array([dpair(pd.concat([groups[p] for p in rng.choice(parts, len(parts))], ignore_index=True)) for _ in range(B)])
    pt = dpair(m)
    summ["diff_median_abs_err"] = round(float(pt[0]), 3)
    summ["diff_median_abs_err_ci"] = [round(float(x), 3) for x in np.percentile(bs[:, 0], [2.5, 97.5])]
    summ["diff_large_or_missing_pp"] = round(float(pt[1]), 2)
    summ["diff_large_or_missing_ci"] = [round(float(x), 2) for x in np.percentile(bs[:, 1], [2.5, 97.5])]
    st = seg[seg["set"] == "test"]
    summ["doubling_by_cohort"] = {c: round(float(g["doubling"].mean()), 3) for c, g in st.groupby("cohort")}
    from scipy.stats import wilcoxon
    summ["wilcoxon_p"] = float(wilcoxon(pb["a"], pb["b"]).pvalue)
    te = evd[evd["set"] == "test"]
    P = te["tp"].sum() / te["n_det"].sum(); Rc = te["tp"].sum() / te["n_ref"].sum()
    summ.update(event_precision=round(float(P), 3), event_recall=round(float(Rc), 3), event_f1=round(float(2 * P * Rc / (P + Rc)), 3),
                event_timing_mae_ms=round(float(np.nanmedian(te["timing_mae_ms"])), 1))
    bc = {}
    for c, g in m.groupby("cohort"):
        bc[c] = {"EG": round(float(g["EG_e"].abs().median()), 2), "B0": round(float(g["B0_e"].abs().median()), 2),
                 "EG_large_or_missing_pct": round(100 * ((~np.isfinite(g["EG_e"])) | (g["EG_e"].abs() > 5)).mean(), 1),
                 "B0_large_or_missing_pct": round(100 * ((~np.isfinite(g["B0_e"])) | (g["B0_e"].abs() > 5)).mean(), 1)}
    summ["by_cohort"] = bc
    (out / "eargait_summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))


# Command-line diagnostics only; analysis statements are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/v16_post_eargait.py PACK.npz RESULTS_V11 E2E_DIR OUT_DIR [--jobs N]')
        raise SystemExit(0)
    if len(sys.argv) < 5:
        print('Usage: python analysis/v16_post_eargait.py PACK.npz RESULTS_V11 E2E_DIR OUT_DIR [--jobs N]', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
