#!/usr/bin/env python3
"""V16 task 3: frozen external validation on DUO-GAIT.

Usage: python run_v16_external.py HEAD_NPZ PROCESSED_ZIP E2E_DIR TRUST_DIR OUT
HEAD_NPZ : head signals per walk, keys "<cond>|<sub>|acc_g", "<cond>|<sub>|gyr_dps", "<cond>|<sub>|fs" (from
           prep3_v16.py on the PC; raw dataset values, no processing)
Frozen   : every parameter comes from the Voisard development set (E2E_DIR/endtoend_params.json,
           TRUST_DIR/trust_models.json, V15 SR threshold 0.32, V15 A1 detector). Nothing is fitted on DUO-GAIT.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as ss
from scipy.signal import butter, sosfiltfilt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from headimu import dsp, endtoend as E, duogait as dg  # noqa: E402
from run_v16_trust import seg_features, auc, auprc, keep_by_risk, MODELS  # noqa: E402

FS = 100.0
SR_Q1 = 0.318819057281164


def a1_peaks(a1, valid, i0, i1, cfg_det):
    pk = dsp.detect_peaks(a1, FS, i0, i1, cfg_det["prominence_floor_mps2"], cfg_det["prominence_k_sigma"],
                          cfg_det["min_peak_distance_s"], valid)
    return pk / FS


def main():
    head_npz, proc_zip, e2e, trust, out = map(Path, sys.argv[1:6])
    out.mkdir(parents=True, exist_ok=True)
    P = json.loads((e2e / "endtoend_params.json").read_text(encoding="utf-8"))["params"]
    models = json.loads((trust / "trust_models.json").read_text(encoding="utf-8"))
    cfg = {"detect": {"prominence_floor_mps2": 0.12, "prominence_k_sigma": 1.5, "min_peak_distance_s": 0.30},
           "autocorr": {"min_lag_s": 0.30, "max_lag_s": 0.90}}
    z = np.load(head_npz)
    walks = sorted({tuple(k.split("|")[:2]) for k in z.files if k.count("|") == 2})
    sos = butter(3, [P["band_lo"], P["band_hi"]], btype="band", fs=FS, output="sos")
    seg_rows, walk_rows = [], []
    for cond, sub in walks:
        acc, gyr = dg.adapt_head(z[f"{cond}|{sub}|acc_g"], z[f"{cond}|{sub}|gyr_dps"], float(z[f"{cond}|{sub}|fs"]))
        valid = np.isfinite(acc).all(1) & np.isfinite(gyr).all(1)
        acc = np.nan_to_num(acc); gyr = np.nan_to_num(gyr)
        ref = dg.load_reference(proc_zip, cond, sub)
        passes, turns, ics = dg.reference_passes(ref)
        o = E.offline(acc, gyr, valid, FS, P)
        c = E.causal(acc, gyr, valid, FS, P)
        a1 = sosfiltfilt(sos, np.linalg.norm(acc, axis=1))
        wn = sosfiltfilt(sos, np.linalg.norm(gyr, axis=1))
        i0, i1 = max(0, int((ics[0] - 1) * FS)), min(len(acc), int((ics[-1] + 1) * FS))
        pk0 = a1_peaks(a1, valid, i0, i1, cfg["detect"]) - P.get("lag_b1", 0.0)
        outs = c["outputs"]
        sr_list = []
        for k, p in enumerate(passes):
            a, b = p["t0"], p["t1"]
            r = {"cond": cond, "sub": sub, "pass": k, "C_ref": p["C_ref"], "dur": b - a}
            iv = np.diff(pk0[(pk0 >= a - 0.1) & (pk0 <= b + 0.1)])
            r["B0_C"] = 60.0 / np.median(iv) if len(iv) >= 3 else np.nan
            ov = [(min(s["t1"], b) - max(s["t0"], a), s) for s in o["segments"]]
            ov = [x for x in ov if x[0] >= 1.0]
            r["B1_C"] = max(ov, key=lambda x: x[0])[1]["cadence"] if ov else np.nan
            sel = outs[(outs[:, 0] >= a) & (outs[:, 0] <= b + P["confirm_s"])] if len(outs) else np.zeros((0, 3))
            r["B2_C"] = float(np.median(sel[:, 1])) if len(sel) else np.nan
            f = seg_features(a1, wn, pk0, a, b, cfg["autocorr"])
            r.update(f)
            sr_list.append(f["sr_seg"])
            seg_rows.append(r)
        # turn detection against reference turns (gaps between reference passes)
        tp = sum(any(x[0] < tb and x[1] > ta for x in o["turns"]) for ta, tb in turns)
        fp = sum(not any(x[0] < tb and x[1] > ta for ta, tb in turns) for x in o["turns"]
                 if ics[0] <= x[0] <= ics[-1])
        k_, nd, nr, d = E.match_events(o["peaks"] - P.get("lag_b1", 0.0), ics, 0.15)
        kc, ndc, nrc, dc = E.match_events(c["peaks"] - P.get("lag_b2", 0.0), ics, 0.15)
        walk_rows.append({"cond": cond, "sub": sub, "n_pass": len(passes), "n_ref_turns": len(turns), "B1_turn_tp": tp,
                          "B1_turn_fp": fp, "B1_turn_fn": len(turns) - tp, "B1_step_tp": k_, "B1_step_nd": nd,
                          "B1_step_nr": nr, "B2_step_tp": kc, "B2_step_nd": ndc, "B2_step_nr": nrc,
                          "B1_walk_f1": E.interval_prf(o["bouts"], [(ics[0], ics[-1])], len(acc), FS)[2],
                          "B1_median_lag_obs": float(np.median(d)) if len(d) else np.nan,
                          "sr_session": float(np.nanmedian(sr_list)) if sr_list else np.nan, "dur_s": len(acc) / FS})
    S = pd.DataFrame(seg_rows)
    W = pd.DataFrame(walk_rows)
    for k in ("B0", "B1", "B2"):
        S[f"{k}_e"] = S[f"{k}_C"] - S["C_ref"]
    S = S.merge(W[["cond", "sub", "sr_session"]], on=["cond", "sub"])
    S["sr_trial"] = S["sr_session"]
    S["big"] = (S["B0_e"].abs() > 5).astype(int)
    # frozen risk models
    for name, cols in MODELS.items():
        m = models[name]
        X = np.column_stack([(S[cname].fillna(m["_impute"][cname]) - m["_mu"][cname]) / m["_sd"][cname] for cname in cols])
        lp = m["intercept"] + X @ np.array([m[cname] for cname in cols])
        S[name] = 1 / (1 + np.exp(-lp))
        S[name + "_flag"] = (S[name] > m["_threshold_dev_matched"]).astype(int)
    S["Q1_flag"] = (S["sr_trial"] < SR_Q1).astype(int)
    S.to_csv(out / "external_passes.csv", index=False)
    W.to_csv(out / "external_walks.csv", index=False)
    print(len(S), "passes;", len(W), "walks")


# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python run_v16_external.py HEAD_NPZ PROCESSED_ZIP E2E_DIR TRUST_DIR OUT')
        raise SystemExit(0)
    if len(sys.argv) < 6:
        print('Usage: python run_v16_external.py HEAD_NPZ PROCESSED_ZIP E2E_DIR TRUST_DIR OUT', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
