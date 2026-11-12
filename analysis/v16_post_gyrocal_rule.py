#!/usr/bin/env python3
"""V16 post hoc: choose WHEN to apply the head-only zero-rate calibration on the DEVELOPMENT set, then test once.

Usage: python v16_post_gyrocal_rule.py E2E_DIR POST_DIR [--window head|ref]
Rule: correct a trial only if the reference-free resting offset estimate (|median angular rate| over the head-only
standing period, cal_offset_dps) exceeds a threshold. Threshold grid 0 (always) ... 30 deg/s and never; criterion =
development B1 share of segments with |e_C| > 5 steps/min or no output (lowest; ties -> higher threshold, i.e. fewer
corrections). The selected rule is then applied once to the test set. Writes POST_DIR/gyrocal_rule.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GRID = [0, 5, 10, 15, 20, 25, 30, np.inf]


def combined(base, cor, tri, thr):
    m = base.merge(cor[["trial", "segment", "B1_e", "B2_e"]].rename(columns={"B1_e": "B1c_e", "B2_e": "B2c_e"}),
                   on=["trial", "segment"]).merge(tri[["trial", "cal_offset_dps"]], on="trial")
    m = m[np.isfinite(m["C_ref"])].copy()
    use = m["cal_offset_dps"] > thr
    for k in ("B1", "B2"):
        m[f"{k}r_e"] = np.where(use, m[f"{k}c_e"], m[f"{k}_e"])
    return m, use


def summ(m, col):
    e = m[col]
    pm = m.assign(a=e.abs()).groupby("participant")["a"].median().dropna()
    return {"no_output_pct": round(100 * (~np.isfinite(e)).mean(), 2),
            "big_or_missing_pct": round(100 * ((~np.isfinite(e)) | (e.abs() > 5)).mean(), 2),
            "mae_participant_median": round(float(pm.median()), 3)}


def main():
    e2e, post = Path(sys.argv[1]), Path(sys.argv[2])
    suf = "" if "--window" not in sys.argv or sys.argv[sys.argv.index("--window") + 1] == "head" else "_" + sys.argv[sys.argv.index("--window") + 1]
    base = pd.read_csv(e2e / "endtoend_segments.csv")
    out = {"grid_dev": []}
    for SET in ("dev", "test"):
        b = base[base["set"] == SET]
        cor = pd.read_csv(post / f"gyrocal_segments_{SET}{suf}.csv"); tri = pd.read_csv(post / f"gyrocal_trials_{SET}{suf}.csv")
        if SET == "dev":
            for thr in GRID:
                m, use = combined(b, cor, tri, thr)
                out["grid_dev"].append({"threshold_dps": None if np.isinf(thr) else thr, "trials_corrected": int(m.loc[use, "trial"].nunique()),
                                        **{f"B1_{k}": v for k, v in summ(m, "B1r_e").items()}})
            g = pd.DataFrame(out["grid_dev"]).fillna(1e9)
            best = g.sort_values(["B1_big_or_missing_pct", "threshold_dps"], ascending=[True, False]).iloc[0]
            thr = np.inf if best["threshold_dps"] >= 1e9 else float(best["threshold_dps"])
            out["selected_threshold_dps"] = None if np.isinf(thr) else thr
        else:
            m0, _ = combined(b, cor, tri, 0)
            out["test_always_corrected"] = {"B1": summ(m0, "B1r_e"), "B2": summ(m0, "B2r_e")}
            m, use = combined(b, cor, tri, thr)
            g = pd.read_csv(e2e / "static_gyro_offsets.csv")[["trial", "q_static"]]
            m = m.merge(g, on="trial")
            out["test"] = {"trials_corrected": int(m.loc[use, "trial"].nunique()),
                           "all": {"B1_uncorrected": summ(m, "B1_e"), "B1_rule": summ(m, "B1r_e"),
                                   "B2_uncorrected": summ(m, "B2_e"), "B2_rule": summ(m, "B2r_e")},
                           "q_static_gt30": {"B1_uncorrected": summ(m[m.q_static > 30], "B1_e"), "B1_rule": summ(m[m.q_static > 30], "B1r_e"),
                                             "B2_uncorrected": summ(m[m.q_static > 30], "B2_e"), "B2_rule": summ(m[m.q_static > 30], "B2r_e")},
                           "HS": {"B1_uncorrected": summ(m[m.cohort == "HS"], "B1_e"), "B1_rule": summ(m[m.cohort == "HS"], "B1r_e")}}
    (post / f"gyrocal_rule{suf}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


# Command-line diagnostics only; analysis statements are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/v16_post_gyrocal_rule.py E2E_DIR POST_DIR [--window head|ref]')
        raise SystemExit(0)
    if len(sys.argv) < 3:
        print('Usage: python analysis/v16_post_gyrocal_rule.py E2E_DIR POST_DIR [--window head|ref]', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
