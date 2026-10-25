#!/usr/bin/env python3
"""V16 data preparation (run once on the PC; nothing is modified in the existing folders).

Part A  Voisard: pack the HEAD signals (processed acc + gyr, validity mask) of every included trial together with the
        reference heel strikes and turn boundaries (kept in separate arrays, used only for evaluation) and the clinical
        metadata, into one compressed file  ->  <out>/voisard_head_pack.npz
Part B  DUO-GAIT (Zhou et al., Sci Data 2023; Zenodo 8244887): download processed.zip (2.6 MB) completely, list the
        content of interim.zip and raw.zip remotely (HTTP range requests, no full download), and extract only the
        head / foot sensor files and small metadata files of interim.zip  ->  <out>/duogait/

Usage
  python pack_v16.py --data ..\\dataset_extracted --results ..\\results_v11 --out ..\\v16_data [--skip-duogait]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from headimu import io_voisard as iov  # noqa: E402
from headimu.features import clinical_meta  # noqa: E402

ZENODO = "https://zenodo.org/records/8244887/files/{name}?download=1"
ZENODO_API = "https://zenodo.org/api/records/8244887/files/{name}/content"


# ----------------------------------------------------------------------------- Part A
def pack_voisard(data, results, out):
    cfgp = Path(results) / "config_used.json"
    cfg = json.loads((cfgp if cfgp.exists() else HERE / "config.json").read_text(encoding="utf-8"))
    if "io" not in cfg:
        cfg["io"] = json.loads((HERE / "config.json").read_text(encoding="utf-8"))["io"]
    qc = pd.read_csv(Path(results) / "qc_trials.csv")
    inc = set(qc.loc[qc["exclusion"].fillna("") == "", "trial"])
    trials = iov.discover(Path(data), cfg)
    arrays, meta, errs = {}, [], []
    t0 = time.time()
    for k, (tid, folder) in enumerate(trials):
        if tid not in inc:
            continue
        try:
            tr = iov.load_trial(tid, folder, cfg, locs=("HE",))
            s = tr.sensors["HE"]
            arrays[f"{tid}|acc"] = s.acc.astype(np.float32)
            arrays[f"{tid}|gyr"] = s.gyr.astype(np.float32)
            arrays[f"{tid}|valid"] = s.valid.astype(np.bool_)
            arrays[f"{tid}|ref_hs_left"] = np.asarray(tr.hs_left, np.float64)
            arrays[f"{tid}|ref_hs_right"] = np.asarray(tr.hs_right, np.float64)
            arrays[f"{tid}|ref_turn"] = np.asarray(tr.turn if tr.turn else [np.nan, np.nan], np.float64)
            meta.append(clinical_meta(tr))
        except Exception as e:  # report, never drop silently
            errs.append(f"{tid}: {type(e).__name__}: {e}")
        if k % 100 == 0:
            print(f"  Voisard {k}/{len(trials)}  ({time.time() - t0:.0f} s)", flush=True)
    arrays["__meta__"] = np.array(json.dumps(meta, default=str))
    arrays["__info__"] = np.array(json.dumps({"fs_hz": cfg["fs_hz"], "n_trials": len(meta), "errors": errs,
                                              "signals": "providers' processed HE_Acc (with gravity, m/s2) and HE_Gyr "
                                                         "(rad/s); validity from raw packet counter"}))
    np.savez_compressed(out / "voisard_head_pack.npz", **arrays)
    print(f"  Voisard packed: {len(meta)} trials, {len(errs)} errors -> {out / 'voisard_head_pack.npz'}")


# ----------------------------------------------------------------------------- Part B: remote zip via HTTP range
class HttpFile(io.RawIOBase):
    """Seekable read-only file over HTTP range requests with an 8-MB block cache."""
    BLOCK = 8 * 1024 * 1024

    def __init__(self, url):
        self.url, self.pos, self.cache = url, 0, {}
        req = urllib.request.Request(url, headers={"Range": "bytes=0-0", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            cr = r.headers.get("Content-Range")
            if r.status != 206 or not cr:
                raise OSError("server does not support range requests")
            self.size = int(cr.split("/")[-1])

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def _block(self, b):
        if b not in self.cache:
            a = b * self.BLOCK
            e = min(self.size, a + self.BLOCK) - 1
            for attempt in range(6):
                try:
                    req = urllib.request.Request(self.url, headers={"Range": f"bytes={a}-{e}", "User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=120) as r:
                        data = r.read()
                    if len(data) != e - a + 1:
                        raise OSError("short read")
                    break
                except Exception:
                    if attempt == 5:
                        raise
                    time.sleep(3 * (attempt + 1))
            if len(self.cache) > 16:
                self.cache.pop(next(iter(self.cache)))
            self.cache[b] = data
        return self.cache[b]

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = max(0, min(n, self.size - self.pos))
        out = bytearray()
        while n > 0:
            b, o = divmod(self.pos, self.BLOCK)
            chunk = self._block(b)[o:o + n]
            out += chunk
            self.pos += len(chunk)
            n -= len(chunk)
        return bytes(out)

    def readinto(self, buf):
        d = self.read(len(buf))
        buf[:len(d)] = d
        return len(d)


def open_remote(name):
    last = None
    for tmpl in (ZENODO, ZENODO_API):
        try:
            return HttpFile(tmpl.format(name=name))
        except Exception as e:
            last = e
    raise last


def download(name, dest):
    for tmpl in (ZENODO, ZENODO_API):
        try:
            req = urllib.request.Request(tmpl.format(name=name), headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            return
        except Exception as e:
            last = e
    raise last


SENSOR = re.compile(r"(?i)(^|[^a-z])(he|head|lf|rf|left[_ ]?foot|right[_ ]?foot)([^a-z]|$)")


def fetch_duogait(out, cap_gb=2.5):
    d = out / "duogait"
    d.mkdir(parents=True, exist_ok=True)
    print("  DUO-GAIT: processed.zip (full download)")
    download("processed.zip", d / "processed.zip")
    for name in ("raw.zip", "interim.zip"):
        z = zipfile.ZipFile(open_remote(name))
        rows = [{"name": i.filename, "size": i.file_size, "compressed": i.compress_size} for i in z.infolist()]
        pd.DataFrame(rows).to_csv(d / f"listing_{name}.csv", index=False)
        print(f"  DUO-GAIT: {name}: {len(rows)} members listed")
    z = zipfile.ZipFile(open_remote("interim.zip"))
    sel = [i for i in z.infolist() if not i.is_dir() and (
        (SENSOR.search(Path(i.filename).stem) and i.filename.lower().endswith((".csv", ".txt", ".json")))
        or (i.file_size < 300_000 and i.filename.lower().endswith((".csv", ".txt", ".json"))))]
    total = sum(i.compress_size for i in sel)
    print(f"  DUO-GAIT: extracting {len(sel)} interim members ({total / 1e9:.2f} GB compressed)")
    if total > cap_gb * 1e9:
        sel = sorted(sel, key=lambda i: i.compress_size)
        acc, keep = 0, []
        for i in sel:
            if acc + i.compress_size > cap_gb * 1e9:
                break
            keep.append(i)
            acc += i.compress_size
        print(f"  DUO-GAIT: capped to {len(keep)} members")
        sel = keep
    raw_sel = []
    zr = zipfile.ZipFile(open_remote("raw.zip"))
    for i in zr.infolist():
        if not i.is_dir() and i.file_size < 300_000 and i.filename.lower().endswith((".csv", ".txt", ".json")):
            raw_sel.append(i)
    with zipfile.ZipFile(d / "duogait_subset.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zo:
        for k, i in enumerate(sel):
            zo.writestr("interim/" + i.filename, z.read(i))
            if k % 20 == 0:
                print(f"    {k}/{len(sel)} {i.filename}", flush=True)
        for i in raw_sel:
            zo.writestr("raw/" + i.filename, zr.read(i))
    print(f"  DUO-GAIT subset -> {d / 'duogait_subset.zip'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", default="v16_data")
    ap.add_argument("--skip-voisard", action="store_true")
    ap.add_argument("--skip-duogait", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if not a.skip_voisard:
        print("[A] Voisard head data")
        pack_voisard(a.data, a.results, out)
    if not a.skip_duogait:
        print("[B] DUO-GAIT (Zenodo 8244887)")
        try:
            fetch_duogait(out)
        except Exception as e:
            print(f"  DUO-GAIT FAILED: {type(e).__name__}: {e}")
            (out / "duogait_error.txt").write_text(f"{type(e).__name__}: {e}", encoding="utf-8")
    print("DONE")


if __name__ == "__main__":
    main()
