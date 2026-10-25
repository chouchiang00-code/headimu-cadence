#!/usr/bin/env python3
"""Head-IMU step-rhythm analysis on the Voisard et al. (2025) dataset.

Usage
  python run_pipeline.py inspect --data <extracted archive folder> [--out inspect_out]
  python run_pipeline.py run     --data <extracted archive folder> [--out results] [--jobs 4] [--quick]

`inspect` must be run first: it reports the detected file format, units and
event conventions and draws one trial so the alignment of reference events
can be checked by eye. Fix config.json if anything is wrong, then `run`.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from headimu import io_voisard as iov  # noqa: E402
from headimu import pipeline as pl  # noqa: E402
from headimu import report  # noqa: E402


def load_cfg(path=None):
    return json.loads(Path(path or HERE / "config.json").read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------- workers
def _w_qc(args):
    tid, folder, cfg = args
    try:
        tr = iov.load_trial(tid, Path(folder), cfg)
        return pl.qc_trial(tr, cfg)
    except Exception as e:  # report, never silently drop
        return {"trial": tid, "exclusion": f"load_error: {type(e).__name__}: {e}"}


def _w_lag(args):
    tid, folder, cfg, band_lo = args
    tr = iov.load_trial(tid, Path(folder), cfg)
    out = {}
    for loc, branches in (("HE", pl.HE_BRANCHES), ("LB", pl.LB_BRANCHES)):
        if loc in tr.sensors:
            for b in branches:
                out[f"{loc}_{b}"] = pl.lag_pairs(tr, cfg, band_lo, loc, b)
    return out


def _w_eval(args):
    tid, folder, cfg, band_lo, lags, thr_list, seed, n_random, locs = args
    tr = iov.load_trial(tid, Path(folder), cfg)
    return pl.evaluate_trial(tr, cfg, band_lo, lags, thr_list, seed, n_random, locs)


def _w_sim(args):
    tid, folder, cfg, band_lo, lags, thr, seed = args
    tr = iov.load_trial(tid, Path(folder), cfg)
    return pl.simulate_trial(tr, cfg, band_lo, lags, thr, seed)


def pmap(fn, items, jobs):
    if jobs <= 1:
        return [fn(x) for x in items]
    with ProcessPoolExecutor(max_workers=min(jobs, 61)) as ex:
        return list(ex.map(fn, items, chunksize=4))


# ----------------------------------------------------------------------------- inspect
def cmd_inspect(a):
    cfg = load_cfg(a.config)
    root = Path(a.data)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    trials = iov.discover(root, cfg)
    print(f"found {len(trials)} trials (*_meta.json)")
    if not trials:
        print("No *_meta.json found. Check --data points to the extracted archive.")
        return
    rep = {"n_trials": len(trials), "examples": []}
    tid, folder = trials[0]
    meta = json.loads((folder / cfg["io"]["meta_pattern"].format(trial=tid)).read_text(encoding="utf-8"))
    rep["meta_keys_first_trial"] = {k: (type(v).__name__, str(v)[:120]) for k, v in meta.items()}
    for tid, folder in trials[: a.n]:
        tr = iov.load_trial(tid, folder, cfg, locs=tuple(cfg["io"]["sensors"]))
        ex = {"trial": tid, "participant": tr.participant, "cohort": tr.cohort, "visit": tr.visit,
              "sensor_type": tr.sensor_type, "n_hs_left": len(tr.hs_left), "n_hs_right": len(tr.hs_right),
              "turn_s": tr.turn, "notes": tr.notes,
              "sensors": {k: v.info for k, v in tr.sensors.items()}}
        rep["examples"].append(ex)
        report.fig_inspect(tr, cfg, out / f"inspect_{tid}.png")
    # dataset-wide quick checks
    qc = pd.DataFrame(pmap(_w_qc, [(t, str(f), cfg) for t, f in trials], a.jobs))
    qc.to_csv(out / "inspect_qc_all_trials.csv", index=False)
    rep["exclusion_counts"] = qc["exclusion"].fillna("").value_counts().to_dict()
    for col in ("HE_turn_angle_deg", "HE_static_gnorm_mps2", "HE_static_xfrac", "HE_fdom_over_fstep"):
        if col in qc:
            rep[col + "_quantiles"] = qc[col].quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(3).to_dict()
    rep["sensor_type_counts"] = qc.get("sensor_type", pd.Series(dtype=str)).value_counts().to_dict()
    (out / "inspect_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=2, default=str)[:6000])
    print("\nChecklist: (1) HE_turn_angle_deg median ~170-180 => gyro units OK; (2) HE_static_gnorm ~9.8 => acc units OK;"
          " (3) in inspect_*.png the reference heel strikes line up with foot-gyro events => event index convention OK;"
          " (4) sensor_type_counts ~ XSens 569 / Technoconcept 787.")


# ----------------------------------------------------------------------------- run
def split_participants(qc, cfg):
    rng = np.random.default_rng(cfg["seed"])
    p = qc.groupby("participant").agg(cohort=("cohort", "first"), sensor_type=("sensor_type", "first")).reset_index()
    dev = []
    for _, g in p.groupby(cfg["split"]["stratify"]):
        ids = g["participant"].to_numpy()
        rng.shuffle(ids)
        k = int(round(cfg["split"]["dev_fraction"] * len(ids)))
        if len(ids) >= 2:
            k = max(1, k)
        dev += list(ids[:k])
    p["set"] = np.where(p["participant"].isin(dev), "dev", "test")
    return p[["participant", "set"]]


def cmd_run(a):
    t_start = time.time()
    cfg = load_cfg(a.config)
    if a.quick:
        cfg["gate"]["random_reps"] = 10
        cfg["sim"]["rotation_reps"] = 5
        cfg["sim"]["lever_directions"] = 4
        cfg["stats"]["bootstrap"] = 300
    root, out = Path(a.data), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    trials = iov.discover(root, cfg)
    excl = set(cfg["io"]["exclude_trials"])
    print(f"[1/7] QC on {len(trials)} trials")
    qc = pd.DataFrame(pmap(_w_qc, [(t, str(f), cfg) for t, f in trials], a.jobs))
    qc.loc[qc["trial"].isin(excl) & (qc["exclusion"].fillna("") == ""), "exclusion"] = "listed_in_dataset_paper_as_empty"
    folder_of = {t: str(f) for t, f in trials}
    split = split_participants(qc[qc["participant"].notna()], cfg)
    qc = qc.merge(split, on="participant", how="left")
    qc.to_csv(out / "qc_trials.csv", index=False)
    ok = qc[qc["exclusion"].fillna("") == ""]
    dev_ids = ok.loc[ok["set"] == "dev", "trial"].tolist()
    test_ids = ok.loc[ok["set"] == "test", "trial"].tolist()
    print(f"      included {len(ok)} trials: dev {len(dev_ids)}, test {len(test_ids)}")
    if not dev_ids or not test_ids:
        print("Not enough included trials for a dev/test split. See qc_trials.csv (column 'exclusion').")
        return

    # ---------------- development set: band low cut-off, lags, gate threshold
    print("[2/7] development-set calibration")
    calib = {"band_lo_candidates": {}}
    best = None
    for lo in cfg["detect"]["band_lo_candidates_hz"]:
        lagl = pmap(_w_lag, [(t, folder_of[t], cfg, lo) for t in dev_ids], a.jobs)
        lags = {k: float(np.median(sum((d.get(k, []) for d in lagl), []) or [0.0]))
                for k in set().union(*[d.keys() for d in lagl])}
        res = pmap(_w_eval, [(t, folder_of[t], cfg, lo, lags, [], 0, 0, ("HE",)) for t in dev_ids], a.jobs)
        seg = pd.DataFrame(sum((r[0] for r in res), []))
        s = seg[(seg["method"] == "A1") & (seg["loc"] == "HE")]
        per = s.assign(abs_eC=s["e_C"].abs()).groupby("participant")[["abs_eC", "halving"]].median()
        score = (float(per["abs_eC"].median()), float(s["halving"].mean()))
        calib["band_lo_candidates"][lo] = {"median_abs_eC_spm": score[0], "halving_rate": score[1], "lags_s": lags}
        if best is None or score < best[0]:
            best = (score, lo, lags)
    band_lo, lags = best[1], best[2]
    # gate threshold on dev: maximise mean participant-level (sensitivity - false-mark rate)
    res = pmap(_w_eval, [(t, folder_of[t], cfg, band_lo, lags, cfg["gate"]["threshold_candidates_dps"], 0, 0, ("HE",))
                         for t in dev_ids], a.jobs)
    gdev = pd.DataFrame(sum((r[2] for r in res), []))
    gsc = (gdev.assign(j=gdev["turn_sensitivity"] - gdev["straight_false_mark"])
           .groupby(["threshold_dps", "participant"])["j"].mean().groupby("threshold_dps").mean())
    thr = float(gsc.idxmax())
    calib.update(band_lo_hz=band_lo, lags_s=lags, gate_threshold_dps=thr, gate_dev_youden=gsc.to_dict())
    (out / "dev_calibration.json").write_text(json.dumps(calib, indent=2, default=float), encoding="utf-8")
    print(f"      band_lo={band_lo} Hz, gate threshold={thr} deg/s")

    # ---------------- test set
    print("[3/7] test-set evaluation")
    seeds = {t: cfg["seed"] + i for i, t in enumerate(test_ids)}
    res = pmap(_w_eval, [(t, folder_of[t], cfg, band_lo, lags, cfg["gate"]["threshold_candidates_dps"], seeds[t], None,
                          ("HE", "LB")) for t in test_ids], a.jobs)
    seg = pd.DataFrame(sum((r[0] for r in res), []))
    mat = pd.DataFrame(sum((r[1] for r in res), []))
    gat = pd.DataFrame(sum((r[2] for r in res), []))
    seg.to_csv(out / "test_segments.csv", index=False)
    mat.to_csv(out / "test_matching.csv", index=False)
    gat.to_csv(out / "test_gating.csv", index=False)

    print("[4/7] simulations (rotation, lever arm)")
    sims = pmap(_w_sim, [(t, folder_of[t], cfg, band_lo, lags, thr, seeds[t] + 7919) for t in test_ids], a.jobs)
    rot = pd.DataFrame(sum((r[0] for r in sims), []))
    lev = pd.DataFrame(sum((r[1] for r in sims), []))
    rot.to_csv(out / "sim_rotation.csv", index=False)
    lev.to_csv(out / "sim_leverarm.csv", index=False)

    print("[5/7] tables and statistics")
    tables, numbers = report.make_tables(qc, seg, mat, gat, rot, lev, cfg, thr, band_lo)
    for name, df in tables.items():
        df.to_csv(out / f"table_{name}.csv", index=False, encoding="utf-8-sig")
    try:
        with pd.ExcelWriter(out / "tables.xlsx") as xw:
            for name, df in tables.items():
                df.to_excel(xw, sheet_name=name[:31], index=False)
    except ImportError:
        print("      (openpyxl not installed: tables.xlsx skipped, CSV tables written)")
    print("[6/7] figures")
    report.make_figures(qc, seg, mat, gat, rot, lev, cfg, thr, out, folder_of, test_ids, band_lo, lags)
    numbers.update({"band_lo_hz": band_lo, "gate_threshold_dps": thr, "lags_s": lags,
                    "runtime_min": round((time.time() - t_start) / 60, 1), "quick_mode": bool(a.quick)})
    (out / "numbers_for_paper.json").write_text(json.dumps(numbers, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    (out / "config_used.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"[7/7] done in {numbers['runtime_min']} min -> {out.resolve()}")


def cmd_report(a):
    """Rebuild tables and figures from the CSVs saved by `run` (no re-analysis)."""
    out = Path(a.out)
    cfg = json.loads((out / "config_used.json").read_text(encoding="utf-8"))
    cal = json.loads((out / "dev_calibration.json").read_text(encoding="utf-8"))
    rd = lambda n: pd.read_csv(out / n) if (out / n).exists() else pd.DataFrame()
    qc = rd("qc_trials.csv")
    qc["exclusion"] = qc["exclusion"].astype(object).fillna("")
    for c in ("visit", "participant"):
        qc[c] = qc[c].astype(str)
    seg, mat, gat, rot, lev = (rd(n) for n in ("test_segments.csv", "test_matching.csv", "test_gating.csv",
                                                "sim_rotation.csv", "sim_leverarm.csv"))
    seg["visit"] = seg["visit"].astype(str)
    thr, band_lo, lags = float(cal["gate_threshold_dps"]), float(cal["band_lo_hz"]), cal["lags_s"]
    tables, numbers = report.make_tables(qc, seg, mat, gat, rot, lev, cfg, thr, band_lo)
    for name, df in tables.items():
        df.to_csv(out / f"table_{name}.csv", index=False, encoding="utf-8-sig")
    folder_of = {t: str(f) for t, f in iov.discover(Path(a.data), cfg)} if a.data else {}
    test_ids = qc.loc[(qc["exclusion"] == "") & (qc["set"] == "test"), "trial"].tolist()
    test_ids = [t for t in test_ids if t in folder_of]
    report.make_figures(qc, seg, mat, gat, rot, lev, cfg, thr, out, folder_of, test_ids, band_lo, lags)
    old = json.loads((out / "numbers_for_paper.json").read_text(encoding="utf-8")) if (out / "numbers_for_paper.json").exists() else {}
    old.update(numbers)
    (out / "numbers_for_paper.json").write_text(json.dumps(old, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    print(f"tables and figures rebuilt in {out.resolve()}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("inspect", "run", "report"):
        p = sub.add_parser(name)
        p.add_argument("--data", required=(name != "report"), default=None)
        p.add_argument("--out", default="inspect_out" if name == "inspect" else "results")
        p.add_argument("--config", default=None)
        p.add_argument("--jobs", type=int, default=1)
        if name == "report":
            pass
        elif name == "inspect":
            p.add_argument("--n", type=int, default=3, help="number of example trials to draw")
        else:
            p.add_argument("--quick", action="store_true", help="few repetitions, for a smoke test only")
    a = ap.parse_args()
    {"inspect": cmd_inspect, "run": cmd_run, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
