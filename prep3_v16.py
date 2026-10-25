#!/usr/bin/env python3
"""V16 data preparation, step 3 (local only): extract the DUO-GAIT HEAD files of the four walking conditions.

Reads ..\\external\\duogait\\interim.zip (unchanged), keeps interim/<cond>/<sub>/HE.csv for
OG_st_control, OG_dt_control, OG_st_fatigue, OG_dt_fatigue, stores every numeric column as float64 together with the
column names, and writes four files (one per condition) to ..\\v16_data\\duogait_head_<cond>.npz.
Also copies the first 15 text lines of one file and interim/interruptions.csv for inspection.
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python prep3_v16.py [DATA_ROOT]')
        raise SystemExit(0)


root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("..")
zpath = root / "external" / "duogait" / "interim.zip"
out = root / "v16_data"
out.mkdir(exist_ok=True)
CONDS = ["OG_st_control", "OG_dt_control", "OG_st_fatigue", "OG_dt_fatigue"]
z = zipfile.ZipFile(zpath)
names = [n for n in z.namelist() if not n.startswith("__MACOSX") and n.endswith("/HE.csv")]
first = True
for cond in CONDS:
    arr, info = {}, {}
    for n in sorted(x for x in names if f"/{cond}/" in x):
        sub = n.split("/")[-2]
        raw = z.read(n)
        if first:
            (out / "duogait_HE_head_lines.txt").write_bytes(b"\n".join(raw.splitlines()[:15]))
            first = False
        # locate the header line: first line whose fields are mostly non-numeric
        lines = raw.decode("utf-8", errors="replace").splitlines()
        hdr = 0
        for i, ln in enumerate(lines[:50]):
            toks = [t.strip() for t in ln.replace(";", ",").split(",")]
            try:
                [float(t) for t in toks if t]
                if i > 0:
                    hdr = i - 1
                    break
            except ValueError:
                continue
        sep = ";" if lines[hdr].count(";") > lines[hdr].count(",") else ","
        df = pd.read_csv(io.BytesIO(raw), sep=sep, skiprows=hdr)
        num = df.apply(pd.to_numeric, errors="coerce")
        cols = [c for c in num.columns if num[c].notna().mean() > 0.9]
        arr[f"{sub}|data"] = num[cols].to_numpy(np.float64)
        info[sub] = {"columns": [str(c) for c in cols], "header_line": hdr, "sep": sep, "n_rows": len(df)}
        print(f"{cond} {sub}: {len(df)} rows, columns {cols[:10]}", flush=True)
    arr["__info__"] = np.array(json.dumps(info))
    np.savez_compressed(out / f"duogait_head_{cond}.npz", **arr)
for extra in ("interim/interruptions.csv", "interim/stance_magnitude_thresholds_manual.csv"):
    if extra in z.namelist():
        (out / ("duogait_" + Path(extra).name)).write_bytes(z.read(extra))
print("DONE")
