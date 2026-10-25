#!/usr/bin/env python3
"""Evaluate the exploratory causal variant B2-t (detector parameters from dev_tuning_b2t.csv) once on all trials.
Usage: python run_v16_b2t_eval.py PACK.npz RESULTS_V11 E2E_DIR"""
import json, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headimu import endtoend as E
import run_v16_endtoend as R

def job(a):
    t, acc, gyr, valid, hs, turn, P = a
    o = E.offline(acc, gyr, valid, 100.0, P)      # unchanged B1 (needed only for the evaluate() signature)
    c = E.causal(acc, gyr, valid, 100.0, P)
    rows, tr = R.evaluate(t, o, c, hs, turn, len(acc), P, P["lag_b1"], P["lag_b2t"])
    return rows, tr


def main():
    pack, res11, e2e = map(Path, sys.argv[1:4])
    z, meta = R.load_pack(pack)
    qc = pd.read_csv(res11 / "qc_trials.csv"); setof = dict(zip(qc["trial"], qc["set"]))
    P = json.loads((e2e / "b2t_params.json").read_text())
    tab = pd.read_csv(e2e / "dev_tuning_b2t.csv").iloc[0]
    P["lag_b2t"] = float(tab["lag"])
    trials = [t for t in meta if t in setof]
    with ProcessPoolExecutor(2) as ex:
        res = list(ex.map(job, [(t, *R.get(z, t), P) for t in trials], chunksize=8))
    seg = pd.DataFrame(sum((r[0] for r in res), []))[["trial", "segment", "B2_C", "B2_C_last", "B2_n_out", "B2_cont_mae"]]
    seg.columns = ["trial", "segment", "B2t_C", "B2t_C_last", "B2t_n_out", "B2t_cont_mae"]
    tri = pd.DataFrame([r[1] for r in res])
    tri = tri[["trial"] + [c for c in tri.columns if c.startswith("B2_")]].rename(columns=lambda c: c.replace("B2_", "B2t_"))
    s0 = pd.read_csv(e2e / "endtoend_segments.csv").merge(seg, on=["trial", "segment"], how="left")
    s0["B2t_e"] = s0["B2t_C"] - s0["C_ref"]
    s0.to_csv(e2e / "endtoend_segments.csv", index=False)
    t0 = pd.read_csv(e2e / "endtoend_trials.csv").merge(tri, on="trial", how="left")
    t0.to_csv(e2e / "endtoend_trials.csv", index=False)
    print("B2t added", s0["B2t_e"].notna().sum())


# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python run_v16_b2t_eval.py PACK.npz RESULTS_V11 E2E_DIR')
        raise SystemExit(0)
    if len(sys.argv) < 4:
        print('Usage: python run_v16_b2t_eval.py PACK.npz RESULTS_V11 E2E_DIR', file=sys.stderr)
        raise SystemExit(2)
    main()
