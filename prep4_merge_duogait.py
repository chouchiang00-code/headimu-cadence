#!/usr/bin/env python3
"""V16 data preparation, step 4: merge the four per-condition DUO-GAIT head files written by prep3_v16.py into one
file for run_v16_external.py, and write the signal audit used in the DUO-GAIT suitability table.

Usage: python prep4_merge_duogait.py V16_DATA_DIR OUT_DIR
Input : V16_DATA_DIR/duogait_head_<cond>.npz  (keys "<sub>|data" = raw HE.csv columns, "__info__" = column names)
Output: OUT_DIR/duogait_head.npz        keys "<cond>|<sub>|acc_g" (g), "<cond>|<sub>|gyr_dps" (deg/s), "<cond>|<sub>|fs"
        OUT_DIR/duogait_head_audit.csv  one row per walk: samples, duration, sampling interval, gaps, missing values,
                                        median acceleration norm (g), maximum |acc| (g), maximum |angular rate| (deg/s)
No filtering, resampling or unit conversion is done here (the unit conversion happens in headimu/duogait.py).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CONDS = ("OG_st_control", "OG_dt_control", "OG_st_fatigue", "OG_dt_fatigue")


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    arrays, rows = {}, []
    for cond in sorted(CONDS):
        z = np.load(src / f"duogait_head_{cond}.npz")
        info = json.loads(str(z["__info__"]))
        for sub in sorted(info):
            cols = info[sub]["columns"]
            d = z[f"{sub}|data"]
            ts = d[:, cols.index("timestamp")]
            acc = d[:, [cols.index(c) for c in ("AccX", "AccY", "AccZ")]]
            gyr = d[:, [cols.index(c) for c in ("GyrX", "GyrY", "GyrZ")]]
            arrays[f"{cond}|{sub}|acc_g"] = acc
            arrays[f"{cond}|{sub}|gyr_dps"] = gyr
            arrays[f"{cond}|{sub}|fs"] = np.float64(128.0)
            dt = np.diff(ts)
            rows.append({"cond": cond, "sub": sub, "n": len(ts), "dur_s": len(ts) / 128,
                         "dt_median": float(np.median(dt)), "dt_max": float(dt.max()),
                         "n_gaps": int((dt > 1.5 / 128).sum()), "nan_frac": float(np.isnan(np.c_[acc, gyr]).mean()),
                         "acc_norm_med": float(np.nanmedian(np.linalg.norm(acc, axis=1))),
                         "acc_max_abs": float(np.nanmax(np.abs(acc))), "gyr_max_abs": float(np.nanmax(np.abs(gyr)))})
    np.savez_compressed(out / "duogait_head.npz", **arrays)
    a = pd.DataFrame(rows).sort_values(["cond", "sub"]).reset_index(drop=True)
    a.to_csv(out / "duogait_head_audit.csv", index=False)
    print(f"{len(a)} walks, {a['sub'].nunique()} participants; gaps {a['n_gaps'].sum()}, missing fraction max "
          f"{a['nan_frac'].max():.3g}; max |acc| {a['acc_max_abs'].max():.2f} g, max |gyr| {a['gyr_max_abs'].max():.0f} deg/s; "
          f"median acc norm {a['acc_norm_med'].median():.3f} g")


# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python prep4_merge_duogait.py V16_DATA_DIR OUT_DIR')
        raise SystemExit(0)
    if len(sys.argv) < 3:
        print('Usage: python prep4_merge_duogait.py V16_DATA_DIR OUT_DIR', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
