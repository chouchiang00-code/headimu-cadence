#!/usr/bin/env python3
"""V19 data preparation (run once on the PC; nothing in the existing folders is modified).
Packs the LOWER-BACK signals (providers' processed LB_Acc with gravity, m/s2; LB_Gyr, rad/s; validity from the raw
packet counter) of every included Voisard trial into one compressed file, keyed exactly like voisard_head_pack.npz:
  <out>/voisard_lb_pack.npz   with arrays  '<trial>|acc', '<trial>|gyr', '<trial>|valid'
Used for the V19 lower-back comparisons (open-source Mobilise-D algorithms, head-trunk transmission spectra).
Usage: python pack_v19_lb.py --data ..\\dataset_extracted --results ..\\results_v11 --out ..\\v16_data"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from headimu import io_voisard as iov  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--results", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    cfgp = Path(a.results) / "config_used.json"
    cfg = json.loads((cfgp if cfgp.exists() else HERE / "config.json").read_text(encoding="utf-8"))
    if "io" not in cfg:
        cfg["io"] = json.loads((HERE / "config.json").read_text(encoding="utf-8"))["io"]
    qc = pd.read_csv(Path(a.results) / "qc_trials.csv")
    inc = set(qc.loc[qc["exclusion"].fillna("") == "", "trial"])
    trials = iov.discover(Path(a.data), cfg)
    arrays, errs, n, t0 = {}, [], 0, time.time()
    for k, (tid, folder) in enumerate(trials):
        if tid not in inc:
            continue
        try:
            tr = iov.load_trial(tid, folder, cfg, locs=("LB",))
            s = tr.sensors["LB"]
            arrays[f"{tid}|acc"] = s.acc.astype(np.float32)
            arrays[f"{tid}|gyr"] = s.gyr.astype(np.float32)
            arrays[f"{tid}|valid"] = s.valid.astype(np.bool_)
            n += 1
        except Exception as e:  # report, never drop silently
            errs.append(f"{tid}: {type(e).__name__}: {e}")
        if k % 100 == 0:
            print(f"  LB {k}/{len(trials)}  ({time.time() - t0:.0f} s)", flush=True)
    arrays["__info__"] = np.array(json.dumps({"fs_hz": cfg["fs_hz"], "n_trials": n, "errors": errs,
                                              "signals": "providers' processed LB_Acc (with gravity, m/s2) and LB_Gyr "
                                                         "(rad/s); validity from raw packet counter"}))
    np.savez_compressed(out / "voisard_lb_pack.npz", **arrays)
    print(f"  LB packed: {n} trials, {len(errs)} errors -> {out / 'voisard_lb_pack.npz'}")
    for e in errs[:20]:
        print("   ", e)


if __name__ == "__main__":
    main()
