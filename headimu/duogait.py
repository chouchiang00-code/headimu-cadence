"""DUO-GAIT (Zhou et al., Sci Data 2023; Zenodo 8244887) adapter for the frozen V16 external validation.

Reference (evaluation only): per-stride foot-IMU gait events of the dataset providers (processed/<cond>/<sub>/
{left,right}_foot_core_params.csv: `timestamps` = initial contact (IC) opening the stride, `ic_times` = IC closing it,
seconds from the start of the segmented walking session; flags `turning_interval`, `interrupted`, `is_outlier`).
Reference straight passes: maximal time intervals in which both feet have strides that are neither in a turning
interval nor interrupted (intersection of the two feet). Reference cadence of a pass: 60 / median of the merged left/right IC intervals.

Pre-registered adaptation of the head signal (no tuning on this dataset): unit conversion (g -> m/s^2, deg/s -> rad/s),
anti-aliased polyphase resampling 128 -> 100 Hz (factor 25/32). Axis conventions are irrelevant because every
head-only stage uses orientation-invariant quantities (acceleration norm, rate about the estimated gravity direction).
"""
from __future__ import annotations

import io
import zipfile

import numpy as np
import pandas as pd
from scipy.signal import resample_poly

FS_SRC = 128.0
CONDS = ["OG_st_control", "OG_dt_control", "OG_st_fatigue", "OG_dt_fatigue"]


def load_reference(processed_zip, cond, sub):
    z = zipfile.ZipFile(processed_zip)
    out = {}
    for foot in ("left", "right"):
        name = f"processed/{cond}/{sub}/{foot}_foot_core_params.csv"
        out[foot] = pd.read_csv(io.BytesIO(z.read(name)))
    return out


def reference_passes(ref, min_iv=6):
    ics = np.unique(np.round(np.concatenate([np.r_[d["timestamps"].to_numpy(), d["ic_times"].to_numpy()]
                                             for d in ref.values()]), 5))
    ivs = {}
    for foot, d in ref.items():
        ok = (~d["turning_interval"].astype(bool)) & (~d["interrupted"].astype(bool))
        ivs[foot] = [(a, b) for a, b in zip(d.loc[ok, "timestamps"], d.loc[ok, "ic_times"])]
    # straight time = union over strides per foot, intersected across feet
    t = np.arange(0, max(ics.max(), 1) + 1, 0.01)
    masks = []
    for foot in ivs:
        m = np.zeros(len(t), bool)
        for a, b in ivs[foot]:
            m[int(a * 100):int(b * 100) + 1] = True
        masks.append(m)
    m = masks[0] & masks[1]
    runs = []
    on = np.flatnonzero(np.diff(np.r_[0, m.astype(int), 0]) == 1)
    off = np.flatnonzero(np.diff(np.r_[0, m.astype(int), 0]) == -1)
    for a, b in zip(on, off):
        runs.append([t[a], t[b - 1]])
    passes = []
    for a, b in runs:
        e = ics[(ics >= a - 1e-6) & (ics <= b + 1e-6)]
        if len(e) >= min_iv + 1:
            passes.append({"t0": float(e[0]), "t1": float(e[-1]), "n_ic": int(len(e)),
                           "C_ref": 60.0 / float(np.median(np.diff(e)))})
    turns = [(passes[i]["t1"], passes[i + 1]["t0"]) for i in range(len(passes) - 1)]
    return passes, turns, ics


def adapt_head(acc_g, gyr_dps, fs_src=FS_SRC):
    """g -> m/s^2, deg/s -> rad/s, resample to 100 Hz."""
    acc = np.asarray(acc_g, float) * 9.80665
    gyr = np.deg2rad(np.asarray(gyr_dps, float))
    up, down = 25, 32
    assert abs(fs_src * up / down - 100.0) < 1e-9
    return resample_poly(acc, up, down, axis=0), resample_poly(gyr, up, down, axis=0)
