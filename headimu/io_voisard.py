"""Loading the Voisard et al. (2025) clinical gait dataset (Sci Data 12:1674).

Every format assumption is configurable in config.json and reported by
`run_pipeline.py inspect`, because column names, units and event-index
conventions must be confirmed on the real archive before analysis.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

G0 = 9.80665


@dataclass
class SensorData:
    acc: np.ndarray            # (N,3) m/s^2, specific force incl. gravity, NaN in uninterpolated gaps
    gyr: np.ndarray            # (N,3) rad/s
    valid: np.ndarray          # (N,) bool, False inside gaps that were not interpolated
    info: dict = field(default_factory=dict)


@dataclass
class Trial:
    trial_id: str
    participant: str
    cohort: str
    visit: str
    sensor_type: str
    age: float | None
    tug: float | None
    fs: float
    sensors: dict               # loc -> SensorData
    hs_left: np.ndarray         # seconds
    hs_right: np.ndarray
    turn: tuple | None          # (start_s, end_s)
    meta_raw: dict
    notes: list = field(default_factory=list)

    @property
    def hs(self) -> np.ndarray:
        return np.sort(np.concatenate([self.hs_left, self.hs_right]))


def _first_key(d: dict, keys: list):
    for k in keys:
        if k in d:
            return d[k]
    return None


def discover(root: Path, cfg: dict) -> list[tuple[str, Path]]:
    """Return (trial_id, folder) for every *_meta.json under root."""
    suffix = cfg["io"]["meta_pattern"].replace("{trial}", "")
    out = []
    for p in sorted(root.rglob("*" + suffix)):
        out.append((p.name[: -len(suffix)], p.parent))
    return out


def _read_table(path: Path, cfg: dict) -> tuple[np.ndarray | None, np.ndarray, np.ndarray, dict]:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        head = [f.readline() for _ in range(3)]
    has_header = bool(re.search(r"[A-Za-z]", head[0]))
    try:
        df = pd.read_csv(path, sep="\t", header=0 if has_header else None)
        if df.shape[1] < 7:
            raise ValueError
    except Exception:
        df = pd.read_csv(path, sep=None, engine="python", header=0 if has_header else None)
    info = {"columns": [str(c) for c in df.columns], "has_header": has_header}
    cc = cfg["io"]["column_candidates"]
    cols = [str(c).strip() for c in df.columns]
    df.columns = cols
    counter = acc = gyr = None
    if has_header:
        for c in cc["counter"]:
            if c in cols:
                counter = df[c].to_numpy(float)
                info["counter_col"] = c
                break
        for trip in cc["acc"]:
            if all(c in cols for c in trip):
                acc = df[trip].to_numpy(float)
                info["acc_cols"] = trip
                break
        for trip in cc["gyr"]:
            if all(c in cols for c in trip):
                gyr = df[trip].to_numpy(float)
                info["gyr_cols"] = trip
                break
    if acc is None or gyr is None:
        pf = cfg["io"]["positional_fallback"]
        arr = df.apply(pd.to_numeric, errors="coerce").to_numpy(float)
        counter = arr[:, pf["counter"]] if pf.get("counter") is not None else None
        acc = arr[:, pf["acc"]]
        gyr = arr[:, pf["gyr"]]
        info["positional_fallback_used"] = True
    return counter, acc, gyr, info


def _unwrap_counter(counter: np.ndarray, wrap: int) -> np.ndarray:
    """Unwrap the packet counter and return integer sample indices.
    Technoconcept files store the counter as floating point (steps such as 0.9999999999998);
    rounding each step before summing avoids spurious duplicates/gaps from truncation."""
    d = np.diff(counter)
    d = np.where(d < -wrap / 2, d + wrap, d)
    return np.concatenate([[0], np.cumsum(np.rint(d))])


def _to_grid(counter, acc, gyr, fs, cfg, info):
    """Place samples on a uniform grid using the packet counter; fill short gaps."""
    n = len(acc)
    if counter is None or not np.all(np.isfinite(counter)):
        idx = np.arange(n)
        info["grid"] = "row_index"
    else:
        idx = _unwrap_counter(counter, cfg["io"]["counter_wrap"]).astype(np.int64)
        dup = np.sum(np.diff(idx) == 0)
        info["duplicate_counter"] = int(dup)
        if np.any(np.diff(idx) < 0) or idx[-1] > 20 * n:
            idx = np.arange(n)
            info["grid"] = "row_index(counter_unusable)"
        else:
            info["grid"] = "packet_counter"
    keep = np.concatenate([[True], np.diff(idx) > 0])
    idx, acc, gyr = idx[keep], acc[keep], gyr[keep]
    m = int(idx[-1]) + 1
    A = np.full((m, 3), np.nan)
    W = np.full((m, 3), np.nan)
    A[idx] = acc
    W[idx] = gyr
    miss = ~np.isfinite(A).all(1) | ~np.isfinite(W).all(1)
    info["n_grid"] = m
    info["missing_fraction"] = float(miss.mean())
    # run lengths of missing samples
    runs = _runs(miss)
    info["longest_gap_s"] = float(max([b - a for a, b in runs], default=0) / fs)
    maxfill = int(round(cfg["qc"]["max_interp_gap_s"] * fs))
    valid = ~miss
    t = np.arange(m)
    for a, b in runs:
        if b - a <= maxfill and a > 0 and b < m:
            valid[a:b] = True
    good = ~miss
    for k in range(3):
        A[:, k] = np.where(miss, np.interp(t, t[good], A[good, k]), A[:, k])
        W[:, k] = np.where(miss, np.interp(t, t[good], W[good, k]), W[:, k])
    # samples in long gaps keep interpolated values for filtering only; flagged invalid
    return A, W, valid


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    m = np.concatenate([[False], mask, [False]]).astype(int)
    d = np.diff(m)
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


def _units(acc, gyr, cfg, info):
    au = cfg["io"]["acc_unit"]
    if au == "auto":
        nrm = np.nanmedian(np.linalg.norm(acc, axis=1))
        au = "g" if 0.5 < nrm < 2.0 else "mps2"
    if au == "g":
        acc = acc * G0
    gu = cfg["io"]["gyr_unit"]
    if gu == "auto":
        p99 = np.nanpercentile(np.abs(gyr), 99)
        gu = "dps" if p99 > 15 else "rads"
    if gu == "dps":
        gyr = np.deg2rad(gyr)
    info["acc_unit_in"] = au
    info["gyr_unit_in"] = gu
    return acc, gyr




def _to_s(x, fs, n, unit):
    x = np.asarray(x, float)
    if unit == "auto":
        unit = "samples" if (np.nanmax(x) > n / fs * 1.05 or np.allclose(x, np.round(x))) else "seconds"
    return (x / fs if unit == "samples" else x), unit


def _num(x):
    try:
        v = float(x)
        return v if np.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _load_processed(trial_id, folder, cfg, locs, sensors_raw_valid, notes):
    """Signals from the preprocessed file: axes homogenised by the dataset providers
    (X = craniocaudal for HE/LB), 14 Hz low-pass, short gaps interpolated by the providers.
    Validity is taken from the raw packet counter (sensors_raw_valid)."""
    io = cfg["io"]
    cands = [folder / io["processed_pattern"].format(trial=trial_id),
             folder / io["processed_pattern"].replace("_processed_data", "_processed").format(trial=trial_id)]
    p = next((c for c in cands if c.exists()), None)
    if p is None:
        notes.append("processed_missing")
        return {}
    df = pd.read_csv(p, sep="\t")
    out = {}
    for loc in locs:
        ac = [f"{loc}_Acc_{a}" for a in "XYZ"]
        gc = [f"{loc}_Gyr_{a}" for a in "XYZ"]
        if not all(c in df.columns for c in ac + gc):
            notes.append(f"processed_cols_missing_{loc}")
            continue
        A = df[ac].to_numpy(float)
        Wg = df[gc].to_numpy(float)
        nan = ~(np.isfinite(A).all(1) & np.isfinite(Wg).all(1))
        valid = ~nan
        rv = sensors_raw_valid.get(loc)
        if rv is not None:
            m = min(len(rv), len(valid))
            valid[:m] &= rv[:m]
            valid[m:] = False if len(rv) < len(valid) else valid[m:]
        t = np.arange(len(A))
        good = ~nan
        if good.sum() < 10:
            notes.append(f"empty_{loc}")
            continue
        for k in range(3):
            A[:, k] = np.where(nan, np.interp(t, t[good], A[good, k]), A[:, k])
            Wg[:, k] = np.where(nan, np.interp(t, t[good], Wg[good, k]), Wg[:, k])
        info = {"source": "processed", "n_grid": len(A), "nan_rows": int(nan.sum())}
        out[loc] = SensorData(A, Wg, valid, info)
    return out


def load_trial(trial_id: str, folder: Path, cfg: dict, locs=("HE", "LB")) -> Trial:
    fs = float(cfg["fs_hz"])
    io = cfg["io"]
    meta = json.loads((folder / io["meta_pattern"].format(trial=trial_id)).read_text(encoding="utf-8"))
    mk = io["meta_keys"]
    notes = []
    m = re.match(io["trial_id_regex"], trial_id)
    cohort = str(_first_key(meta, mk["cohort"]) or (m.group("cohort") if m else "NA"))
    pid = _first_key(meta, mk["participant"])
    if pid is None and m:
        pid = m.group("pid")
    pid = str(pid)
    participant = pid if pid.startswith(cohort + "_") else f"{cohort}_{pid}"
    visit = _first_key(meta, mk["visit"])
    if visit is None:
        visit = "1"
        notes.append("visit_missing_assumed_1")
    sensor_type = str(_first_key(meta, mk["sensor_type"]) or "unknown")
    st = sensor_type.lower()
    sensor_type = "XSens" if "xsens" in st else ("Technoconcept" if ("techno" in st or "i4" in st or "tc" == st) else sensor_type)
    age = _num(_first_key(meta, mk["age"]))
    tug = _num(_first_key(meta, mk["tug"]))
    days = _num(_first_key(meta, mk.get("days", [])))

    # raw files: always read, for QC and for the validity mask from the packet counter
    raw = {}
    for loc in locs:
        p = folder / io["raw_pattern"].format(trial=trial_id, loc=loc)
        if not p.exists():
            notes.append(f"missing_{loc}")
            continue
        counter, acc, gyr, info = _read_table(p, cfg)
        if acc.size == 0 or not np.isfinite(acc).any() or np.nanstd(np.linalg.norm(acc, axis=1)) < 1e-3:
            notes.append(f"empty_{loc}")
            continue
        acc, gyr = _units(acc, gyr, cfg, info)
        A, W, valid = _to_grid(counter, acc, gyr, fs, cfg, info)
        raw[loc] = SensorData(A, W, valid, info)
    if io.get("signal_source", "processed") == "processed":
        sensors = _load_processed(trial_id, folder, cfg, [l for l in locs if l in raw],
                                  {k: v.valid for k, v in raw.items()}, notes)
        for loc, s in sensors.items():
            s.info.update({k: v for k, v in raw[loc].info.items() if k not in ("columns", "n_grid")})
            if np.nanstd(np.linalg.norm(s.acc, axis=1)) < 1e-3:
                notes.append(f"empty_{loc}")
        sensors = {k: v for k, v in sensors.items() if f"empty_{k}" not in notes}
    else:
        sensors = raw

    n = max([s.acc.shape[0] for s in sensors.values()], default=0)
    unit = io["event_index_unit"]
    order = io["event_pair_order"]
    hs_idx = order.index("HS")

    def parse(ev):
        if ev is None or len(ev) == 0:
            return np.array([])
        arr = np.asarray(ev, float)
        if arr.ndim == 2:
            arr = arr[:, hs_idx]
        s, _ = _to_s(arr, fs, n, unit)
        return np.sort(s[np.isfinite(s)])

    hs_l = parse(_first_key(meta, mk["left_events"]))
    hs_r = parse(_first_key(meta, mk["right_events"]))
    tb = _first_key(meta, mk["turn"])
    turn = None
    if tb is not None and len(tb) >= 2:
        tb = np.asarray(tb, float).ravel()[:2]
        tbs, _ = _to_s(tb, fs, n, unit)
        turn = (float(min(tbs)), float(max(tbs)))
    if n and len(hs_l) + len(hs_r):
        mx = max(np.max(hs_l, initial=0), np.max(hs_r, initial=0))
        if mx > n / fs + 0.5:
            notes.append("events_beyond_signal_length")
    tr = Trial(trial_id, participant, cohort, str(visit), sensor_type, age, tug,
               fs, sensors, hs_l, hs_r, turn, meta, notes)
    tr.days = days
    tr.raw = raw
    return tr
