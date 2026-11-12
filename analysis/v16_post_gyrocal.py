#!/usr/bin/env python3
"""V16 post hoc analysis: does a resting zero-rate (gyroscope offset) calibration remove the head-only failures?

Usage: python v16_post_gyrocal.py PACK.npz RESULTS_V11 E2E_DIR OUT_DIR [--jobs N] [--set dev|test] [--window head|ref]
Head-only, reference-free calibration: the standing period is taken from the head signal itself, from the start of the
recording to 0.5 s before the first walking bout detected by B1 (at least 0.5 s); the per-axis MEDIAN angular rate over
that period is subtracted from the whole trial. B1 and B2 are then re-run with the frozen V16 parameters and lags and
evaluated exactly as in run_v16_endtoend.py. Test set only. Seed-free (deterministic).
Outputs: OUT_DIR/gyrocal_segments.csv, gyrocal_trials.csv, gyrocal_summary.json
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
from headimu import endtoend as E  # noqa: E402

FS = R.FS
P = None


def one(args):
    t, acc, gyr, valid, hs, turn, P, window = args
    if window == "ref":   # upper bound: a known still period (standing until 0.5 s before the first reference heel strike)
        n = int(round(max(0.5, hs[0] - 0.5) * FS))
    else:                 # head-only: standing until 0.5 s before the first B1 walking bout
        o0 = E.offline(acc, gyr, valid, FS, P)
        b0 = o0["bouts"][0][0] if o0["bouts"] else len(acc) / FS
        n = int(round(max(0.5, b0 - 0.5) * FS))
    off = np.median(gyr[:n], axis=0)
    g2 = gyr - off
    o = E.offline(acc, g2, valid, FS, P)
    c = E.causal(acc, g2, valid, FS, P)
    return t, o, c, hs, turn, len(acc), float(np.linalg.norm(np.rad2deg(off))), n / FS


def main():
    pack, res11, e2e, out = map(Path, sys.argv[1:5])
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 1
    out.mkdir(parents=True, exist_ok=True)
    z, meta = R.load_pack(pack)
    qc = pd.read_csv(res11 / "qc_trials.csv")
    SET = sys.argv[sys.argv.index("--set") + 1] if "--set" in sys.argv else "test"
    tests = [t for t in qc[qc["set"] == SET]["trial"] if t in meta]
    prm = json.loads((e2e / "endtoend_params.json").read_text())["params"]
    P = dict(E.PARAMS); P.update(prm)
    WIN = sys.argv[sys.argv.index("--window") + 1] if "--window" in sys.argv else "head"
    args = [(t, *R.get(z, t), P, WIN) for t in tests]
    run = (lambda f, it: list(ProcessPoolExecutor(jobs).map(f, it, chunksize=8))) if jobs > 1 else (lambda f, it: [f(x) for x in it])
    res = run(one, args)
    rows, trows = [], []
    for t, o, c, hs, turn, n, offdps, win in res:
        r, tr = R.evaluate(t, o, c, hs, turn, n, P, P["lag_b1"], P["lag_b2"])
        tr.update(cal_offset_dps=offdps, cal_window_s=win)
        rows += r; trows.append(tr)
    seg = pd.DataFrame(rows); tri = pd.DataFrame(trows)
    for k in ("B1", "B2"):
        seg[f"{k}_e"] = seg[f"{k}_C"] - seg["C_ref"]
    seg.to_csv(out / f"gyrocal_segments_{SET}{'' if WIN == 'head' else '_' + WIN}.csv", index=False); tri.to_csv(out / f"gyrocal_trials_{SET}{'' if WIN == 'head' else '_' + WIN}.csv", index=False)
    if SET != "test" or WIN != "head":
        return

    # compare with the uncorrected run on the same reference segments
    base = pd.read_csv(e2e / "endtoend_segments.csv")
    base = base[base["set"] == "test"]
    g = pd.read_csv(e2e / "static_gyro_offsets.csv")[["trial", "q_static"]]
    m = base.merge(seg[["trial", "segment", "B1_e", "B2_e"]].rename(columns={"B1_e": "B1c_e", "B2_e": "B2c_e"}),
                   on=["trial", "segment"]).merge(g, on="trial")
    m = m[np.isfinite(m["C_ref"])]
    m["hi"] = m["q_static"] > 30
    rng = np.random.default_rng(20261023)

    def stats(d, k):
        e = d[f"{k}_e"]
        miss = 100 * (~np.isfinite(e)).mean()
        big_or_miss = 100 * ((~np.isfinite(e)) | (e.abs() > 5)).mean()
        pm = d.assign(a=e.abs()).groupby("participant")["a"].median().dropna()
        return {"no_output_pct": round(miss, 2), "big_or_missing_pct": round(big_or_miss, 2),
                "mae_participant_median": round(float(pm.median()), 3), "n_segments": int(len(d))}

    out_s = {"n_test_segments": int(len(m)), "n_trials_q_static_gt30": int(m.loc[m["hi"], "trial"].nunique())}
    for lab, d in (("all", m), ("q_static_gt30", m[m["hi"]]), ("HS", m[m["cohort"] == "HS"]), ("other_trials", m[~m["hi"]])):
        out_s[lab] = {k: stats(d, k) for k in ("B1", "B1c", "B2", "B2c")}
    # paired participant-level difference in median |e| (corrected - uncorrected), outputs present in both
    for k in ("B1", "B2"):
        d = m[np.isfinite(m[f"{k}_e"]) & np.isfinite(m[f"{k}c_e"])]
        pm = d.assign(a=d[f"{k}_e"].abs(), b=d[f"{k}c_e"].abs()).groupby("participant")[["a", "b"]].median()
        diff = (pm["b"] - pm["a"]).to_numpy()
        bs = [np.median(diff[rng.integers(0, len(diff), len(diff))]) for _ in range(2000)]
        out_s[f"{k}_paired_median_diff"] = [round(float(np.median(diff)), 3), [round(float(x), 3) for x in np.percentile(bs, [2.5, 97.5])]]
    t2 = tri.merge(g, on="trial")
    out_s["B1_turn_detected_pct"] = {"uncorrected": None, "corrected": round(100 * t2["B1_turn_tp"].mean(), 2)}
    bt = pd.read_csv(e2e / "endtoend_trials.csv"); bt = bt[bt["set"] == "test"]
    out_s["B1_turn_detected_pct"]["uncorrected"] = round(100 * bt["B1_turn_tp"].mean(), 2)
    out_s["B1_extra_turns_per_trial"] = {"uncorrected": round(float(bt["B1_turn_fp"].mean()), 3),
                                         "corrected": round(float(tri["B1_turn_fp"].mean()), 3)}
    out_s["calibration_window_s_median"] = round(float(tri["cal_window_s"].median()), 2)
    out_s["offset_removed_dps_median_hi_trials"] = round(float(t2.loc[t2["q_static"] > 30, "cal_offset_dps"].median()), 2)
    (out / "gyrocal_summary.json").write_text(json.dumps(out_s, indent=1))
    print(json.dumps(out_s, indent=1))


# Command-line diagnostics only; analysis statements are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/v16_post_gyrocal.py PACK.npz RESULTS_V11 E2E_DIR OUT_DIR [--jobs N] [--set dev|test] [--window head|ref]')
        raise SystemExit(0)
    if len(sys.argv) < 5:
        print('Usage: python analysis/v16_post_gyrocal.py PACK.npz RESULTS_V11 E2E_DIR OUT_DIR [--jobs N] [--set dev|test] [--window head|ref]', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
