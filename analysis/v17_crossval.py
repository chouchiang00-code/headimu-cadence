#!/usr/bin/env python3
"""V17, POST HOC: participant-level cross-validation of the head-only B0 analysis on all 260 participants.

The primary analysis uses one fixed split (77 development / 183 test participants). Here every participant is tested
exactly once: 5 folds, stratified by cohort (participants shuffled with a fixed seed). In each fold the development
procedure of run_pipeline.py is repeated on the other four folds only (band low cut-off chosen from the configured
candidates by median participant |e_C| of HE-A1, then halving rate; lags = median of the training-trial lag lists), and
the held-out fold is evaluated with that choice. Only the head IMU is in the public-data pack used here, so the
lower-back comparison stays on the fixed test split (v17_cohort_table.py).

Outputs (OUT): cv_segments.csv (held-out segments, all methods), cv_folds.json (per-fold choices), cv_by_cohort.csv /
.json (HE-A1 per cohort: participants, segments, median of participant medians with participant-bootstrap 95% CI,
share of |e_C| > 5, and the same statistics from the fixed split's test participants for comparison).
Also checks that evaluating the fixed-split test trials with the published calibration reproduces test_segments.csv.

Usage: python analysis/v17_crossval.py PACK.npz RESULTS_V11 OUT [--jobs N] [--folds 5] [--seed 20261112]
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
from headimu.io_voisard import Trial, SensorData  # noqa: E402

BRANCHES = ("A0", "A0g", "A1")
G = {}


def _init(pack, cfg):
    G["z"] = np.load(pack)
    G["meta"] = {m["trial"]: m for m in json.loads(str(G["z"]["__meta__"]))}
    G["cfg"] = cfg


def _trial(t):
    z, m = G["z"], G["meta"][t]
    return Trial(t, m["participant"], m["cohort"], str(m["visit"]), m["sensor_type"], m["age"], None, 100.0,
                 {"HE": SensorData(z[f"{t}|acc"].astype(float), z[f"{t}|gyr"].astype(float), z[f"{t}|valid"], {})},
                 z[f"{t}|ref_hs_left"], z[f"{t}|ref_hs_right"], tuple(z[f"{t}|ref_turn"]), {}, [])


def _w_lag(args):
    t, lo = args
    tr = _trial(t)
    return t, lo, {f"HE_{b}": pl.lag_pairs(tr, G["cfg"], lo, "HE", b) for b in BRANCHES}


def _w_eval(args):
    t, lo, lags = args
    seg, _, _ = pl.evaluate_trial(_trial(t), G["cfg"], lo, lags, [], 0, 0, ("HE",))
    return seg


def pm_stats(s):
    s = s.assign(a=s["e_C"].abs())
    per = s.groupby("participant")["a"].median().to_numpy()
    med, lo, hi = stats.boot_ci(per, np.median, 2000, seed=1)[:3]
    return {"n_participants": int(len(per)), "n_segments": int(len(s)), "median": float(med), "lo": float(lo),
            "hi": float(hi), "big_pct": float(100 * (s["a"] > 5).mean())}


def main():
    a = sys.argv[1:]
    pack, r11, out = Path(a[0]), Path(a[1]), Path(a[2])
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 1
    K = int(a[a.index("--folds") + 1]) if "--folds" in a else 5
    seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 20261112
    out.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((r11 / "config_used.json").read_text(encoding="utf-8"))
    cal = json.loads((r11 / "dev_calibration.json").read_text(encoding="utf-8"))
    cands = [float(x) for x in cfg["detect"]["band_lo_candidates_hz"]]
    qc = pd.read_csv(r11 / "qc_trials.csv")
    ok = qc[qc["exclusion"].fillna("") == ""]
    _init(pack, cfg)
    trials = [t for t in ok["trial"] if t in G["meta"]]
    part = {t: G["meta"][t]["participant"] for t in trials}
    coh = {G["meta"][t]["participant"]: G["meta"][t]["cohort"] for t in trials}
    # folds stratified by cohort
    rng = np.random.default_rng(seed)
    fold_of = {}
    for c in sorted(set(coh.values())):
        ps = sorted(p for p in coh if coh[p] == c)
        rng.shuffle(ps)
        for i, p in enumerate(ps):
            fold_of[p] = i % K
    with Pool(jobs, initializer=_init, initargs=(str(pack), cfg)) as pool:
        # sanity: fixed split reproduces the published test segments
        test_ids = ok.loc[ok["set"] == "test", "trial"].tolist()
        chk = pd.DataFrame(sum(pool.map(_w_eval, [(t, float(cal["band_lo_hz"]), cal["lags_s"]) for t in test_ids],
                                        chunksize=16), []))
        ref = pd.read_csv(r11 / "test_segments.csv")
        ref = ref[(ref["loc"] == "HE") & (ref["method"].isin(BRANCHES))]
        mm = chk.merge(ref, on=["trial", "segment", "method"], suffixes=("", "_ref"))
        d = (mm["e_C"] - mm["e_C_ref"]).abs()
        repro = {"n": int(len(mm)), "n_ref": int(len(ref)), "max_abs_diff": float(d.max()),
                 "identical_frac": float((d < 1e-9).mean())}
        print("reproduction of test_segments.csv:", repro)
        # lag lists for every trial and candidate
        lag = {}
        for t, lo, dct in pool.map(_w_lag, [(t, lo) for t in trials for lo in cands], chunksize=16):
            lag[(t, lo)] = dct
        folds, held = [], []
        for k in range(K):
            tr_ids = [t for t in trials if fold_of[part[t]] != k]
            te_ids = [t for t in trials if fold_of[part[t]] == k]
            best, scores = None, {}
            for lo in cands:
                lags = {f"HE_{b}": float(np.median(sum((lag[(t, lo)][f"HE_{b}"] for t in tr_ids), []) or [0.0]))
                        for b in BRANCHES}
                seg = pd.DataFrame(sum(pool.map(_w_eval, [(t, lo, lags) for t in tr_ids], chunksize=16), []))
                s = seg[seg["method"] == "A1"]
                per = s.assign(x=s["e_C"].abs()).groupby("participant")[["x", "halving"]].median()
                sc = (float(per["x"].median()), float(s["halving"].mean()))
                scores[lo] = sc
                if best is None or sc < best[0]:
                    best = (sc, lo, lags)
            lo, lags = best[1], best[2]
            seg = pd.DataFrame(sum(pool.map(_w_eval, [(t, lo, lags) for t in te_ids], chunksize=16), []))
            seg["fold"] = k
            held.append(seg)
            folds.append({"fold": k, "n_train_trials": len(tr_ids), "n_test_trials": len(te_ids),
                          "n_test_participants": len({part[t] for t in te_ids}), "band_lo_hz": lo, "lags_s": lags,
                          "train_scores": {str(c): v for c, v in scores.items()}})
            print(f"fold {k}: band_lo={lo}  scores={scores}")
    H = pd.concat(held, ignore_index=True)
    H.to_csv(out / "cv_segments.csv", index=False)
    (out / "cv_folds.json").write_text(json.dumps({"seed": seed, "K": K, "reproduction_fixed_split": repro,
                                                   "folds": folds}, indent=1, default=float))
    A1 = H[H["method"] == "A1"]
    F = ref[ref["method"] == "A1"]
    rows = []
    for c in ["All", "HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]:
        s1 = A1 if c == "All" else A1[A1["cohort"] == c]
        s0 = F if c == "All" else F[F["cohort"] == c]
        r = {"cohort": c}
        r.update({f"cv_{k}": v for k, v in pm_stats(s1).items()})
        r.update({f"fixed_{k}": v for k, v in pm_stats(s0).items()})
        rows.append(r)
    T = pd.DataFrame(rows)
    T.to_csv(out / "cv_by_cohort.csv", index=False)
    (out / "cv_by_cohort.json").write_text(json.dumps(rows, indent=1))
    print(T.round(2).to_string())


# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v17_crossval.py PACK.npz RESULTS_V11 OUT [--jobs N] [--folds 5] [--seed 20261112]')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

if __name__ == "__main__":
    main()
