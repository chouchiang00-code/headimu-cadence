"""V16: head-only end-to-end cadence estimation.

B1 (offline) and B2 (causal) use ONLY the head IMU (acc incl. gravity [m/s^2], gyr [rad/s], validity mask, fs).
No reference information enters any function in this module; references are used only in evaluate_*().
The pipeline is protocol-agnostic (any number of walking bouts and turns), so it can be applied unchanged to
datasets with other walking protocols.

Stages (offline B1)
  1 walking detection   centred moving RMS of the step-band acceleration norm > thr_walk; gaps < gap_fill_s filled;
                        bouts shorter than min_bout_s dropped
  2 turn detection      turning-rate gate of the primary analysis (q = |omega . g_hat| > q_thr, median 0.15 s,
                        >= 0.30 s, padding 0.20 s); gated runs closer than merge_s merged; a run is a turn if its
                        integrated rotation >= min_turn_deg
  3 straight segments   bout minus turns; segments shorter than min_seg_s dropped
  4 steps               A1 peaks inside the bouts (same detector as the primary analysis)
  5 cadence             60 / median peak interval per straight segment; "no output" if < min_iv intervals
B2 (causal) replaces every filter by its causal counterpart and every decision by a trailing-window rule:
  causal Butterworth band-pass and gravity low-pass, trailing RMS with hysteresis, trailing median for the gate,
  peaks confirmed confirm_s after they occur, and a running cadence = 60 / median of the last k_iv intervals within
  the current straight bout, emitted at each confirmed step.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import median_filter, uniform_filter1d
from scipy.signal import butter, find_peaks, sosfilt, sosfilt_zi, sosfiltfilt

from . import dsp

PARAMS = {  # fixed before any test-set evaluation; thr_walk / thr_on are selected on the development set
    "band_lo": 0.6, "band_hi": 3.0, "order": 3, "grav_lp": 0.3,
    "rms_win_s": 2.0, "thr_walk": 0.6, "gap_fill_s": 1.0, "min_bout_s": 3.0,
    "q_thr_dps": 30.0, "gate_med_s": 0.15, "gate_min_s": 0.30, "gate_pad_s": 0.20, "merge_s": 0.5, "min_turn_deg": 90.0,
    "min_seg_s": 2.0, "min_iv": 3,
    "prom_floor": 0.12, "prom_k": 1.5, "min_dist_s": 0.30,
    # causal
    "thr_on": 0.6, "hyst": 0.7, "on_hold_s": 0.5, "off_hold_s": 1.0, "confirm_s": 0.20, "sigma_win_s": 3.0, "k_iv": 6,
}


def _runs(m):
    return dsp.runs(np.asarray(m, bool))


def _fill_gaps(mask, n_gap):
    m = mask.copy()
    rr = _runs(m)
    for (a0, b0), (a1, b1) in zip(rr[:-1], rr[1:]):
        if a1 - b0 <= n_gap:
            m[b0:a1] = True
    return m


# ----------------------------------------------------------------------------- B1 offline
def offline(acc, gyr, valid, fs, P=PARAMS):
    acc = np.asarray(acc, float); gyr = np.asarray(gyr, float)
    n = len(acc)
    sos = butter(P["order"], [P["band_lo"], P["band_hi"]], btype="band", fs=fs, output="sos")
    a1 = sosfiltfilt(sos, np.linalg.norm(acc, axis=1))
    g = dsp.gravity_dir(acc, fs, P["grav_lp"])
    q = np.rad2deg(np.abs(np.einsum("ij,ij->i", gyr, g)))
    w = max(1, int(round(P["rms_win_s"] * fs)))
    rms = np.sqrt(uniform_filter1d(a1 ** 2, w, mode="nearest"))
    walk = _fill_gaps(rms > P["thr_walk"], int(P["gap_fill_s"] * fs))
    bouts = [(a, b) for a, b in _runs(walk) if (b - a) / fs >= P["min_bout_s"]]
    gate = dsp.gate_mask(np.deg2rad(q), fs, P["q_thr_dps"], P["gate_med_s"], P["gate_min_s"], P["gate_pad_s"])
    gate = _fill_gaps(gate, int(P["merge_s"] * fs))
    turns = []
    for a, b in _runs(gate):
        ang = float(np.sum(q[a:b]) / fs)
        if ang >= P["min_turn_deg"] and any(a < y and b > x for x, y in bouts):
            turns.append((a, b, ang))
    tmask = np.zeros(n, bool)
    for a, b, _ in turns:
        tmask[a:b] = True
    segs = []
    for x, y in bouts:
        m = np.zeros(n, bool); m[x:y] = True; m &= ~tmask
        segs += [(a, b) for a, b in _runs(m) if (b - a) / fs >= P["min_seg_s"]]
    peaks = []
    for x, y in bouts:
        seg = a1[x:y]
        prom = max(P["prom_floor"], P["prom_k"] * dsp.robust_sigma(seg))
        pk, _ = find_peaks(seg, prominence=prom, distance=max(1, int(round(P["min_dist_s"] * fs))))
        pk = pk + x
        peaks += list(pk[valid[pk]])
    peaks = np.array(sorted(peaks), int)
    out_segs = []
    for a, b in segs:
        p = peaks[(peaks >= a) & (peaks < b)] / fs
        iv = np.diff(p)
        cad = 60.0 / np.median(iv) if len(iv) >= P["min_iv"] else np.nan
        out_segs.append({"t0": a / fs, "t1": b / fs, "n_steps": int(len(p)), "cadence": cad})
    return {"a1": a1, "q": q, "rms": rms, "bouts": [(a / fs, b / fs) for a, b in bouts],
            "turns": [(a / fs, b / fs, ang) for a, b, ang in turns], "segments": out_segs, "peaks": peaks / fs}


# ----------------------------------------------------------------------------- B2 causal
def causal(acc, gyr, valid, fs, P=PARAMS):
    acc = np.asarray(acc, float); gyr = np.asarray(gyr, float)
    n = len(acc)
    sos = butter(P["order"], [P["band_lo"], P["band_hi"]], btype="band", fs=fs, output="sos")
    nrm = np.linalg.norm(acc, axis=1)
    # causal filters initialised in steady state on the FIRST sample only (no look-ahead)
    a1, _ = sosfilt(sos, nrm, zi=sosfilt_zi(sos) * nrm[0])
    sog = butter(2, P["grav_lp"], btype="low", fs=fs, output="sos")
    zg = sosfilt_zi(sog)
    gl = np.column_stack([sosfilt(sog, acc[:, j], zi=zg * acc[0, j])[0] for j in range(3)])
    g = gl / np.maximum(np.linalg.norm(gl, axis=1, keepdims=True), 1e-9)
    q = np.rad2deg(np.abs(np.einsum("ij,ij->i", gyr, g)))
    w = max(1, int(round(P["rms_win_s"] * fs)))
    c2 = np.concatenate([[0.0], np.cumsum(a1 ** 2)])
    idx = np.arange(n)
    lo = np.maximum(0, idx - w + 1)
    rms = np.sqrt((c2[idx + 1] - c2[lo]) / (idx + 1 - lo))           # trailing window
    # walking state with hysteresis and hold times
    on_h, off_h = int(P["on_hold_s"] * fs), int(P["off_hold_s"] * fs)
    thr_on, thr_off = P["thr_on"], P["thr_on"] * P["hyst"]
    walking = np.zeros(n, bool)
    st, cnt, events = False, 0, []
    for k in range(n):
        if not st:
            cnt = cnt + 1 if rms[k] > thr_on else 0
            if cnt >= on_h:
                st, cnt = True, 0
                events.append(("walk_on", k))
        else:
            cnt = cnt + 1 if rms[k] < thr_off else 0
            if cnt >= off_h:
                st, cnt = False, 0
                events.append(("walk_off", k))
        walking[k] = st
    # causal turn gate: trailing median, threshold, minimum duration (declared when the duration is reached)
    m = max(1, int(round(P["gate_med_s"] * fs)))
    qm = np.array([np.median(q[max(0, k - m + 1):k + 1]) for k in range(n)])
    above = qm > P["q_thr_dps"]
    turning = np.zeros(n, bool)
    run, gap, st_t = 0, 0, False
    gmin, gend = int(P["gate_min_s"] * fs), int(P["gate_pad_s"] * fs)
    for k in range(n):
        if above[k]:
            run += 1; gap = 0
            if not st_t and run >= gmin:
                st_t = True
                events.append(("turn_on", k))
        else:
            run = 0
            if st_t:
                gap += 1
                if gap >= gend:
                    st_t = False
                    events.append(("turn_off", k))
        turning[k] = st_t
    # causal peaks: local maximum over [k - min_dist, k + confirm], prominence over the trailing minimum,
    # threshold from a trailing robust sigma; confirmed at k + confirm
    dmin, dc, sw = int(round(P["min_dist_s"] * fs)), int(round(P["confirm_s"] * fs)), int(P["sigma_win_s"] * fs)
    peaks, conf = [], []
    last = -10 ** 9
    for k in range(dmin, n - dc):
        x = a1[k]
        if x < a1[k - dmin:k].max() or x <= a1[k + 1:k + dc + 1].max():
            continue
        if k - last < dmin:
            continue
        hist = a1[max(0, k - sw):k + 1]
        thr = max(P["prom_floor"], P["prom_k"] * dsp.robust_sigma(hist))
        if x - a1[max(0, k - int(round(P.get("trail_min_s", 0.9) * fs))):k].min() < thr or not valid[k]:
            continue
        peaks.append(k); conf.append(k + dc); last = k
    peaks, conf = np.array(peaks, int), np.array(conf, int)
    # running cadence at each confirmed step during straight walking (not turning), within the current bout
    outs = []
    buf = []
    for p, c in zip(peaks, conf):
        if not walking[c] or turning[c]:
            buf = []           # a turn or a stop resets the straight-bout buffer
            continue
        buf.append(p)
        iv = np.diff(buf[-(P["k_iv"] + 1):]) / fs
        iv = iv[iv < 2.0]
        if len(iv) >= P["min_iv"]:
            outs.append((c / fs, 60.0 / float(np.median(iv)), p / fs))
    return {"a1": a1, "q": q, "rms": rms, "walking": walking, "turning": turning, "events": [(e, k / fs) for e, k in events],
            "peaks": peaks / fs, "confirm": conf / fs, "outputs": np.array(outs).reshape(-1, 3)}


# ----------------------------------------------------------------------------- evaluation helpers (reference used here only)
def interval_prf(det, ref, n, fs):
    """Sample-level precision/recall/F1 between lists of (t0, t1) intervals (seconds)."""
    d = np.zeros(n, bool); r = np.zeros(n, bool)
    for a, b in det:
        d[int(a * fs):int(b * fs)] = True
    for a, b in ref:
        r[int(a * fs):int(b * fs)] = True
    tp = (d & r).sum()
    p = tp / d.sum() if d.sum() else np.nan
    rc = tp / r.sum() if r.sum() else np.nan
    f = 2 * p * rc / (p + rc) if p and rc and np.isfinite(p) and np.isfinite(rc) else (0.0 if r.sum() else np.nan)
    return p, rc, f


def match_events(det, ref, tol):
    from scipy.optimize import linear_sum_assignment
    det, ref = np.asarray(det, float), np.asarray(ref, float)
    if len(det) == 0 or len(ref) == 0:
        return 0, len(det), len(ref), np.array([])
    C = np.abs(det[:, None] - ref[None, :])
    big = 1e6
    Cm = np.where(C <= tol, C, big)
    i, j = linear_sum_assignment(Cm)
    ok = Cm[i, j] < big
    return int(ok.sum()), len(det), len(ref), (det[i[ok]] - ref[j[ok]])


def ref_cadence(hs, t0, t1, min_iv=3):
    r = hs[(hs >= t0) & (hs <= t1)]
    iv = np.diff(r)
    return 60.0 / np.median(iv) if len(iv) >= min_iv else np.nan
