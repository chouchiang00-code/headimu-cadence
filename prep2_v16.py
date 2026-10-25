#!/usr/bin/env python3
"""V16 data preparation, step 2 (local only, no network).

(a) split ..\\v16_data\\voisard_head_pack.npz into parts of about 12 MB (transfer limit of the remote link)
(b) DUO-GAIT: if ..\\external\\duogait\\interim.zip (and processed.zip) were downloaded with a browser from
    https://zenodo.org/records/8244887 , list their content and copy all files of one participant (sub_01 or the
    first one found) into a small sample zip, so that the file format can be inspected before full conversion.
Nothing in the existing folders is modified.
"""
from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

SENSOR = re.compile(r"(?i)(^|[^a-z])(he|head|lf|rf|left[_ ]?foot|right[_ ]?foot)([^a-z]|$)")
# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python prep2_v16.py [DATA_ROOT]')
        raise SystemExit(0)


root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("..")
v16 = root / "v16_data"
pack = v16 / "voisard_head_pack.npz"
if pack.exists():
    z = np.load(pack)
    trials = sorted({k.split("|")[0] for k in z.files if "|" in k})
    parts, cur, size = [], [], 0
    for t in trials:
        s = sum(z[f"{t}|{k}"].nbytes for k in ("acc", "gyr"))
        if cur and size + s > 30_000_000:   # ~30 MB raw float32 -> ~12 MB compressed
            parts.append(cur); cur, size = [], 0
        cur.append(t); size += s
    parts.append(cur)
    for i, p in enumerate(parts):
        arr = {k: z[k] for t in p for k in z.files if k.startswith(t + "|")}
        if i == 0:
            arr["__meta__"], arr["__info__"] = z["__meta__"], z["__info__"]
        np.savez_compressed(v16 / f"voisard_head_pack_part{i:02d}.npz", **arr)
        print(f"part {i:02d}: {len(p)} trials")
else:
    print("voisard_head_pack.npz not found - run run_v16_pack.cmd first")

d = root / "external" / "duogait"
for name in ("processed.zip", "interim.zip", "raw.zip"):
    f = d / name
    if not f.exists():
        print(f"DUO-GAIT {name}: not found in {d}")
        continue
    with zipfile.ZipFile(f) as zz:
        info = [i for i in zz.infolist() if not i.is_dir()]
        pd.DataFrame([{"name": i.filename, "size": i.file_size, "compressed": i.compress_size} for i in info]) \
            .to_csv(v16 / f"duogait_listing_{name}.csv", index=False)
        print(f"DUO-GAIT {name}: {len(info)} files listed")
        if name == "interim.zip":
            sid = re.compile(r"(?i)^(sub|subject|participant|s|p)[_-]?(\d+)$")
            comps = {c for i in info for c in Path(i.filename).parts if sid.match(c)}
            pick = min(comps, key=lambda c: int(sid.match(c).group(2))) if comps else ""
            with zipfile.ZipFile(v16 / "duogait_sample_one_subject.zip", "w", zipfile.ZIP_DEFLATED) as zo:
                n = 0
                for i in info:
                    small = i.file_size < 1_000_000
                    sensor = SENSOR.search(Path(i.filename).stem) is not None
                    if ((not pick or pick in Path(i.filename).parts) and (sensor or small) and n < 60
                            and not i.filename.lower().endswith((".png", ".pdf", ".jpg"))):
                        with zz.open(i) as fh:          # keep the sample small: first 3 MB of each file
                            data = fh.read(3_000_000)
                        zo.writestr(i.filename, data)
                        n += 1
            print(f"DUO-GAIT sample of '{pick}': {n} files -> duogait_sample_one_subject.zip")
print("DONE")
