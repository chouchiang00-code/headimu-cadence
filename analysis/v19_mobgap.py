#!/usr/bin/env python3
"""V19 (post hoc, test set): open-source Mobilise-D cadence algorithms (mobgap) on the same straight segments,
head and lower back, against the frozen AGS and the published peak estimator.

Algorithms, exactly as packaged in mobgap (no re-tuning):
  MD-regular   CadFromIcDetector with IcdShinImproved   (mobgap preset 'regular_walking')
  MD-impaired  CadFromIcDetector with IcdHKLeeImproved  (mobgap preset 'impaired_walking')
  both with the Hampel step-time smoothing and per-second interpolation of mobgap; segment cadence = mean of the
  per-second cadence values (the Mobilise-D walking-bout aggregation).
  Ionescu      IcdIonescu initial contacts (the IC detector of both Mobilise-D pipelines); cadence from the median
               step and from the median stride of those contacts (for comparison with the step/stride question).
Segments: the B0 straight segments (first reference heel strike -> turn onset, turn end -> last heel strike), i.e.
the gait-sequence detection step of Mobilise-D is replaced by the reference segmentation, as for B0 and AGS.
Input frame: mobgap expects body-frame acceleration with gravity (acc_is ~ +9.81 m/s2 upright). acc_is is the
projection on the gravity direction (0.3-Hz low-pass of acc), acc_ml / acc_pa are two orthogonal horizontal axes
(their orientation does not matter for the norm-based Shin and HKLee detectors).
Usage: python analysis/v19_mobgap.py HEAD_PACK LB_PACK|none RESULTS_V11 OUT_DIR"""
from __future__ import annotations
import sys
# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v19_mobgap.py HEAD_PACK LB_PACK|none RESULTS_V11 OUT_DIR')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

import json, os, sys, time, warnings
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from headimu import dsp  # noqa: E402
from headimu.evaluate import windows  # noqa: E402
from headimu.io_voisard import Trial, SensorData  # noqa: E402
import mobgap  # noqa: E402
from mobgap.cadence import CadFromIcDetector  # noqa: E402
from mobgap.initial_contacts import IcdIonescu  # noqa: E402

warnings.filterwarnings("ignore")
hp, lp, r11, out = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)
cfg = json.loads((r11 / "config_used.json").read_text(encoding="utf-8"))
qc = pd.read_csv(r11 / "qc_trials.csv"); setof = dict(zip(qc["trial"], qc["set"]))
zh = np.load(hp); zl = np.load(lp) if lp != "none" else None
meta = {m["trial"]: m for m in json.loads(str(zh["__meta__"]))}
tests = [t for t in meta if setof.get(t) == "test"][:int(os.environ.get("NMAX", 10 ** 9))]
FS = 100.0
ALGS = {"MD_regular": CadFromIcDetector(**CadFromIcDetector.PredefinedParameters.regular_walking),
        "MD_impaired": CadFromIcDetector(**CadFromIcDetector.PredefinedParameters.impaired_walking)}


def body_frame(acc):
    g = dsp.gravity_dir(acc, FS, 0.3)
    v = np.einsum("ij,ij->i", acc, g)
    ref = np.where(np.abs(g[:, [0]]) < 0.9, np.array([[1.0, 0, 0]]), np.array([[0, 1.0, 0]]))
    e1 = np.cross(g, ref); e1 /= np.linalg.norm(e1, axis=1, keepdims=True)
    e2 = np.cross(g, e1)
    return pd.DataFrame({"acc_is": v, "acc_ml": np.einsum("ij,ij->i", acc, e1), "acc_pa": np.einsum("ij,ij->i", acc, e2),
                         "gyr_is": 0.0, "gyr_ml": 0.0, "gyr_pa": 0.0})


def stride_cad(iv):
    s = iv[:-1] + iv[1:]
    return 120.0 / np.median(s) if len(s) >= 2 else np.nan


rows, t0 = [], time.time()
for n, t in enumerate(tests):
    m = meta[t]
    hsl, hsr, turn = zh[f"{t}|ref_hs_left"], zh[f"{t}|ref_hs_right"], zh[f"{t}|ref_turn"]
    tr = Trial(t, m["participant"], m["cohort"], str(m["visit"]), m["sensor_type"], m["age"], None, FS, {}, hsl, hsr,
               tuple(turn), {}, [])
    w = windows(tr, FS, cfg["detect"]["window_pad_s"])
    if w is None:
        continue
    for loc, z in (("HE", zh), ("LB", zl)):
        if z is None or f"{t}|acc" not in z:
            continue
        acc = z[f"{t}|acc"].astype(float)
        bad = ~np.isfinite(acc).all(axis=1)
        if bad.any():  # short gaps: linear interpolation (mobgap filters cannot take NaN)
            idx = np.arange(len(acc))
            for k in range(3):
                acc[bad, k] = np.interp(idx[bad], idx[~bad], acc[~bad, k])
        bf = body_frame(acc)
        for sname, (a, b) in w["segs"].items():
            r = tr.hs[(tr.hs >= a) & (tr.hs <= b)]
            if len(r) < cfg["metrics"]["min_ref_intervals"] + 1:
                continue
            ri = np.diff(r)
            d = bf.iloc[int(round(a * FS)):int(round(b * FS)) + 1].reset_index(drop=True)
            row = {"trial": t, "participant": m["participant"], "cohort": m["cohort"], "loc": loc, "segment": sname,
                   "R_step": 60 / np.median(ri), "R_stride": stride_cad(ri)}
            for nm, alg in ALGS.items():
                try:
                    c = alg.clone().calculate(d, initial_contacts=pd.DataFrame({"ic": []}), sampling_rate_hz=FS)
                    v = c.cadence_per_sec_["cadence_spm"].to_numpy()
                    row[nm] = float(np.nanmean(v)) if np.isfinite(v).any() else np.nan
                except Exception as e:  # report, count as no output
                    row[nm] = np.nan; row[f"{nm}_err"] = type(e).__name__
            try:
                ic = IcdIonescu().detect(d, sampling_rate_hz=FS).ic_list_["ic"].to_numpy() / FS
                iv = np.diff(np.sort(ic))
                row["Ionescu_step"] = 60 / np.median(iv) if len(iv) >= 2 else np.nan
                row["Ionescu_stride"] = stride_cad(iv)
                row["Ionescu_n_ic"] = int(len(ic))
            except Exception as e:
                row["Ionescu_step"] = row["Ionescu_stride"] = np.nan; row["Ionescu_err"] = type(e).__name__
            rows.append(row)
    if n % 100 == 0:
        print(f"{n}/{len(tests)} {time.time() - t0:.0f}s", flush=True)
D = pd.DataFrame(rows)
D.to_csv(out / "v19_mobgap_segments.csv", index=False)
print("mobgap", mobgap.__version__ if hasattr(mobgap, "__version__") else "?", "segments", D.groupby("loc").size().to_dict())
for loc, g in D.groupby("loc"):
    for k in ("MD_regular", "MD_impaired", "Ionescu_step", "Ionescu_stride"):
        e = (g[k] - g.R_step).abs()
        pm = e.groupby(g.participant).median().median()
        print(loc, k, f"med {pm:.2f}  big {100 * (e > 5).mean():.1f}  none {100 * g[k].isna().mean():.1f}")
