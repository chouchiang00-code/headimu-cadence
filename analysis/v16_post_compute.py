#!/usr/bin/env python3
"""V16 post hoc: computational cost of the head-only pipelines.

Usage: python v16_post_compute.py PACK.npz RESULTS_V11 E2E_DIR OUT_DIR [--n 60]
(1) Streaming B2 (headimu/stream_b2.py) is run sample by sample on N test trials (first N in sorted order) and its
    outputs are compared with the batch implementation headimu.endtoend.causal (same parameters).
(2) Arithmetic operations per second of data (counted by stage) and the fixed state memory (32-bit values).
(3) Wall-clock time of the batch B1 and B2 implementations (Python/NumPy, this machine) on all test trials.
Writes OUT_DIR/compute_summary.json.
"""
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import run_v16_endtoend as R  # noqa: E402
from headimu import endtoend as E  # noqa: E402
from headimu.stream_b2 import StreamB2  # noqa: E402

FS = R.FS


def main():
    pack, r11, e2e, out = map(Path, sys.argv[1:5])
    N = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 60
    z, meta = R.load_pack(pack)
    qc = pd.read_csv(r11 / "qc_trials.csv")
    tests = sorted(t for t in qc[qc["set"] == "test"]["trial"] if t in meta)
    P = dict(E.PARAMS); P.update(json.loads((e2e / "endtoend_params.json").read_text())["params"])
    # (1)+(2) streaming equivalence and op counts
    nout_b = nout_s = nmatch = 0; maxdiff = 0.0; secs = 0.0
    tot = {}; nsig = 0; t_stream = 0.0
    for t in tests[:N]:
        acc, gyr, valid, hs, turn = R.get(z, t)
        b = E.causal(acc, gyr, valid, FS, P)["outputs"]
        s = StreamB2(FS, P)
        t0 = time.perf_counter()
        so = [r for r in (s.push(acc[i], gyr[i], valid[i]) for i in range(len(acc))) if r is not None]
        t_stream += time.perf_counter() - t0
        so = np.array(so).reshape(-1, 3)
        nout_b += len(b); nout_s += len(so)
        if len(b) == len(so) and len(b):
            same_t = np.allclose(b[:, 0], so[:, 0]) and np.allclose(b[:, 2], so[:, 2])
            if same_t:
                nmatch += len(b); maxdiff = max(maxdiff, float(np.abs(b[:, 1] - so[:, 1]).max()))
        secs += len(acc) / FS
        for k, v in s.ops.items():
            tot[k] = tot.get(k, 0) + v
        nsig += s.n_sigma
    ops_per_s = {k: round(v / secs) for k, v in tot.items()}
    res = {"n_trials_streaming": N, "data_seconds": round(secs, 1),
           "outputs_batch": int(nout_b), "outputs_stream": int(nout_s), "outputs_identical_timing": int(nmatch),
           "max_abs_cadence_diff": maxdiff,
           "ops_per_second_by_stage": ops_per_s, "ops_per_second_total": int(sum(ops_per_s.values())),
           "ops_per_sample_total": round(sum(tot.values()) / (secs * FS), 1),
           "sigma_evaluations_per_second": round(nsig / secs, 2),
           "state_bytes_float32": StreamB2(FS, P).state_bytes(4), "buffer_samples": StreamB2(FS, P).nbuf,
           "python_stream_seconds_per_hour_of_data": round(3600 * t_stream / secs, 1)}
    # (3) batch timing on all test trials
    tb1 = tb2 = 0.0; secs_all = 0.0
    for t in tests:
        acc, gyr, valid, hs, turn = R.get(z, t)
        t0 = time.perf_counter(); E.offline(acc, gyr, valid, FS, P); tb1 += time.perf_counter() - t0
        t0 = time.perf_counter(); E.causal(acc, gyr, valid, FS, P); tb2 += time.perf_counter() - t0
        secs_all += len(acc) / FS
    res.update(n_trials_batch=len(tests), batch_data_hours=round(secs_all / 3600, 2),
               B1_batch_seconds_per_hour=round(3600 * tb1 / secs_all, 2), B2_batch_seconds_per_hour=round(3600 * tb2 / secs_all, 2),
               machine=f"{platform.processor() or platform.machine()}, Python {platform.python_version()}, NumPy {np.__version__}")
    (out / "compute_summary.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


# Command-line diagnostics only; analysis statements are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/v16_post_compute.py PACK.npz RESULTS_V11 E2E_DIR OUT_DIR [--n N]')
        raise SystemExit(0)
    if len(sys.argv) < 5:
        print('Usage: python analysis/v16_post_compute.py PACK.npz RESULTS_V11 E2E_DIR OUT_DIR [--n N]', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
