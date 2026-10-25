#!/usr/bin/env python3
"""V15 feature extraction (run on the full dataset; statistics are computed afterwards by analysis/v15_stats.py).

Usage
  python run_features.py --data ..\\dataset_extracted --results ..\\results_v11 --out ..\\results_v15 [--jobs 6] [--quick]

Reuses, unchanged, the participant split (qc_trials.csv: column 'set'), the development-set band cut-off and lags
(dev_calibration.json), and the configuration (config_used.json) of the primary analysis. Nothing is re-selected.
Outputs
  clinical_meta.csv        one row per trial: VGA, TUG, cohort-specific score, deficit side, sex, height, weight
  features_segments.csv    one row per included trial x straight segment: head features + foot-reference counterparts
  sim_features.csv         test trials only: trial-level features under rigid rotations and lever arms
  run_info.json
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
from headimu import features as ft  # noqa: E402


def _w_trial(args):
    tid, folder, cfg, band_lo, lag, include, do_sim, seed, quick = args
    try:
        tr = iov.load_trial(tid, Path(folder), cfg, locs=("HE",))
        meta = ft.clinical_meta(tr)
        if not include or "HE" not in tr.sensors:
            return meta, [], [], None
        s = tr.sensors["HE"]
        base = {"trial": tid, "participant": tr.participant, "cohort": tr.cohort, "visit": tr.visit,
                "sensor_type": tr.sensor_type}
        segs = [{**base, **r} for r in ft.trial_features(s.acc, s.gyr, s.valid, tr, cfg, band_lo, lag)]
        sims = []
        if do_sim:
            rng = np.random.default_rng(seed)
            kw = dict(n_axes=2, n_dirs=2) if quick else {}
            sims = ft.simulate_features(tr, cfg, band_lo, lag, rng, **kw)
        return meta, segs, sims, None
    except Exception as e:  # report, never silently drop
        return {"trial": tid}, [], [], f"{tid}: {type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--results", required=True, help="output folder of run_pipeline.py run (results_v11)")
    ap.add_argument("--out", default="results_v15")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--quick", action="store_true", help="smoke test: 40 trials, 2 perturbation repeats")
    a = ap.parse_args()
    t0 = time.time()
    res, out = Path(a.results), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cfgp = res / "config_used.json"
    cfg = json.loads((cfgp if cfgp.exists() else HERE / "config.json").read_text(encoding="utf-8"))
    if "io" not in cfg:  # config_used.json may omit io: take it from config.json
        cfg["io"] = json.loads((HERE / "config.json").read_text(encoding="utf-8"))["io"]
    cal = json.loads((res / "dev_calibration.json").read_text(encoding="utf-8"))
    band_lo, lag = float(cal["band_lo_hz"]), float(cal["lags_s"].get("HE_A1", 0.0))
    qc = pd.read_csv(res / "qc_trials.csv")
    inc = qc[qc["exclusion"].fillna("") == ""]
    setof = dict(zip(inc["trial"], inc["set"]))
    trials = iov.discover(Path(a.data), cfg)
    if a.quick:
        trials = trials[:40]
    print(f"{len(trials)} trials found; {len(setof)} included in the primary analysis; band_lo={band_lo} Hz, lag={lag:.3f} s")
    jobs = [(t, str(f), cfg, band_lo, lag, t in setof, setof.get(t) == "test", cfg["seed"] + 104729 + i, a.quick)
            for i, (t, f) in enumerate(trials)]
    if a.jobs > 1:
        with ProcessPoolExecutor(max_workers=min(a.jobs, 61)) as ex:
            rs = list(ex.map(_w_trial, jobs, chunksize=4))
    else:
        rs = [_w_trial(j) for j in jobs]
    meta = pd.DataFrame([r[0] for r in rs])
    seg = pd.DataFrame(sum((r[1] for r in rs), []))
    sim = pd.DataFrame(sum((r[2] for r in rs), []))
    errs = [r[3] for r in rs if r[3]]
    if not seg.empty:
        seg = seg.merge(inc[["trial", "set"]], on="trial", how="left")
    meta.to_csv(out / "clinical_meta.csv", index=False, encoding="utf-8")
    seg.to_csv(out / "features_segments.csv", index=False)
    sim.to_csv(out / "sim_features.csv", index=False)
    info = {"n_trials_found": len(trials), "n_segments": len(seg), "n_sim_rows": len(sim), "errors": errs,
            "band_lo_hz": band_lo, "lag_s": lag, "quick": a.quick, "runtime_min": round((time.time() - t0) / 60, 1),
            "feature_definitions": ft.__doc__}
    (out / "run_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"done in {info['runtime_min']} min: {len(seg)} segments, {len(sim)} simulation rows, {len(errs)} errors -> {out.resolve()}")
    if errs:
        print("first errors:", *errs[:5], sep="\n  ")


if __name__ == "__main__":
    main()
