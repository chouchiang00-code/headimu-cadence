"""Per-trial processing: branch signals, candidates, and all trial-level metrics."""
from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment

from . import dsp


# ----------------------------------------------------------------------------- windows
def windows(trial, fs: float, pad_s: float):
    hs = trial.hs
    if hs.size < 4 or trial.turn is None:
        return None
    t0, t1 = hs[0] - pad_s, hs[-1] + pad_s
    ts, te = trial.turn
    segs = {"S1": (hs[0], ts), "S2": (te, hs[-1])}
    return {"full": (t0, t1), "segs": segs, "turn": (ts, te)}


def static_slice(trial, fs, n, min_static_s):
    hs = trial.hs
    end = hs[0] - 0.5 if hs.size else 1.0
    if end < min_static_s:
        end = min(1.0, n / fs)
    return slice(0, max(1, int(end * fs)))


# ----------------------------------------------------------------------------- branch signals
def branch_signals(acc, gyr, fs, cfg, band_lo, polarity=None, static=slice(0, 100), which=("A0", "A0g", "A1")):
    d = cfg["detect"]
    out = {}
    ghat = dsp.gravity_dir(acc, fs, d["gravity_lp_hz"])
    if "A0" in which:
        ax = acc[:, d["a0_axis"]]
        pol = polarity if polarity is not None else np.sign(np.nanmean(ax[static])) or 1.0
        out["A0"] = dsp.bandpass(pol * ax, fs, band_lo, d["band_hi_hz"], d["filter_order"])
    if "A0g" in which:
        v = np.einsum("ij,ij->i", acc, ghat)
        out["A0g"] = dsp.bandpass(v, fs, band_lo, d["band_hi_hz"], d["filter_order"])
    if "A1" in which:
        out["A1"] = dsp.bandpass(np.linalg.norm(acc, axis=1), fs, band_lo, d["band_hi_hz"], d["filter_order"])
    q = dsp.turn_rate(gyr, ghat)
    return out, q


def candidates(sig, fs, cfg, i0, i1, valid):
    d = cfg["detect"]
    pk = dsp.detect_peaks(sig, fs, i0, i1, d["prominence_floor_mps2"], d["prominence_k_sigma"],
                          d["min_peak_distance_s"], valid)
    return pk / fs


# ----------------------------------------------------------------------------- metrics
def _intervals(times, valid, fs):
    if len(times) < 2:
        return np.array([])
    iv = np.diff(times)
    ok = np.ones(len(iv), bool)
    if valid is not None:
        for k in range(len(iv)):
            a, b = int(times[k] * fs), int(times[k + 1] * fs)
            if not valid[a:b + 1].all():
                ok[k] = False
    return iv[ok]


def segment_metrics(cand_s, lag, ref_hs, seg, valid, fs, cfg):
    """Primary metric on one straight segment. cand_s: candidate times (s), shifted by -lag."""
    m = cfg["metrics"]
    a, b = seg
    c = np.asarray(cand_s) - lag
    c = c[(c >= a - 0.1) & (c <= b + 0.1)]
    r = ref_hs[(ref_hs >= a) & (ref_hs <= b)]
    ri = np.diff(r)
    ci = _intervals(c + lag, valid, fs)
    res = {"n_ref": int(len(r)), "n_cand": int(len(c)),
           "detect_ratio": len(c) / len(r) if len(r) else np.nan}
    if len(ri) < m["min_ref_intervals"] or len(ci) < 2:
        res.update(T_ref=np.nan, T_imu=np.nan, e_T=np.nan, e_C=np.nan, ratio=np.nan, halving=np.nan, doubling=np.nan)
        return res
    Tr, Ti = float(np.median(ri)), float(np.median(ci))
    ratio = Ti / Tr
    res.update(T_ref=Tr, T_imu=Ti, e_T=Ti - Tr, e_C=60 / Ti - 60 / Tr, C_ref=60 / Tr, C_imu=60 / Ti, ratio=ratio,
               halving=float(m["halving_ratio"][0] <= ratio <= m["halving_ratio"][1]),
               doubling=float(m["doubling_ratio"][0] <= ratio <= m["doubling_ratio"][1]))
    return res


def step_time_from_ac(sig, fs, seg, cfg):
    a, b = int(seg[0] * fs), int(seg[1] * fs)
    if b - a < 2 * cfg["autocorr"]["max_lag_s"] * fs:
        return np.nan
    return dsp.autocorr_step_time(sig[a:b], fs, cfg["autocorr"]["min_lag_s"], cfg["autocorr"]["max_lag_s"])


def match_events(cand, ref, tol):
    """Minimum-cost one-to-one assignment within tolerance. Returns list of (i_cand, i_ref, dt)."""
    if len(cand) == 0 or len(ref) == 0:
        return []
    D = np.abs(cand[:, None] - ref[None, :])
    big = 1e6
    C = np.where(D <= tol, D, big)
    ri, ci = linear_sum_assignment(C)
    return [(i, j, cand[i] - ref[j]) for i, j in zip(ri, ci) if C[i, j] < big]


def matching_metrics(cand, ref, tol):
    pairs = match_events(np.asarray(cand), np.asarray(ref), tol)
    tp = len(pairs)
    dts = np.array([p[2] for p in pairs])
    out = {"tp": tp, "n_cand": len(cand), "n_ref": len(ref),
           "precision": tp / len(cand) if len(cand) else np.nan,
           "recall": tp / len(ref) if len(ref) else np.nan,
           "mae_s": float(np.mean(np.abs(dts))) if tp else np.nan,
           "bias_s": float(np.mean(dts)) if tp else np.nan}
    p, r = out["precision"], out["recall"]
    out["f1"] = 2 * p * r / (p + r) if tp and (p + r) > 0 else (0.0 if len(cand) and len(ref) else np.nan)
    # step-interval error for consecutive matched reference events
    jm = {j: i for i, j, _ in pairs}
    errs = [abs((cand[jm[j + 1]] - cand[jm[j]]) - (ref[j + 1] - ref[j]))
            for j in range(len(ref) - 1) if j in jm and (j + 1) in jm]
    out["step_interval_abs_err_s"] = float(np.median(errs)) if errs else np.nan
    return out


def turn_detection(gmask, fs, full, turn):
    i0, i1 = int(full[0] * fs), int(full[1] * fs)
    ts, te = int(turn[0] * fs), int(turn[1] * fs)
    t = np.zeros(len(gmask), bool)
    t[ts:te] = True
    win = np.zeros(len(gmask), bool)
    win[max(0, i0):i1] = True
    sens = float(gmask[t & win].mean()) if (t & win).any() else np.nan
    straight = win & ~t
    fmr = float(gmask[straight].mean()) if straight.any() else np.nan
    # boundary error of the gated run(s) overlapping the turn
    ov = [(a, b) for a, b in dsp.runs(gmask) if b > ts and a < te]
    if ov:
        start_err = (min(a for a, _ in ov) - ts) / fs
        end_err = (max(b for _, b in ov) - te) / fs
        detected = 1.0
    else:
        start_err = end_err = np.nan
        detected = 0.0
    return {"turn_sensitivity": sens, "straight_false_mark": fmr, "turn_detected": detected,
            "turn_start_err_s": start_err, "turn_end_err_s": end_err}


def gated_eval(cand, lag, ref, gmask, fs, full, tol):
    """Full-window evaluation of candidates restricted to non-gated time.
    To avoid an edge artefact at gate boundaries (a kept candidate whose heel strike falls just
    inside a gated block, or vice versa), precision matches the KEPT candidates against ALL
    reference events, and recall matches the reference events in accepted time against ALL candidates."""
    i0, i1 = int(full[0] * fs), int(full[1] * fs)
    acc_mask = ~gmask
    c = np.asarray(cand)
    keep_c = acc_mask[np.clip((c * fs).astype(int), 0, len(gmask) - 1)]
    cs_all = c - lag
    cs = cs_all[keep_c]
    refi = np.clip((ref * fs).astype(int), 0, len(gmask) - 1)
    r_acc = ref[acc_mask[refi]]
    win = acc_mask[max(0, i0):i1]
    mp = matching_metrics(cs, ref, tol)          # precision of kept candidates
    mr = matching_metrics(cs_all, r_acc, tol)    # recall of accepted reference events
    full_rec = matching_metrics(cs, ref, tol)["recall"]
    return {"time_coverage": float(win.mean()) if win.size else np.nan,
            "ref_event_coverage": len(r_acc) / len(ref) if len(ref) else np.nan,
            "accepted_precision": mp["precision"], "accepted_recall": mr["recall"],
            "accepted_mae_s": mp["mae_s"], "accepted_step_interval_abs_err_s": mp["step_interval_abs_err_s"],
            "full_window_recall": full_rec}


def random_gate(gmask, fs, full, rng):
    """Circularly shift the gate mask inside the evaluation window: same total time and block lengths."""
    i0, i1 = max(0, int(full[0] * fs)), min(len(gmask), int(full[1] * fs))
    seg = gmask[i0:i1]
    out = gmask.copy()
    if seg.size:
        out[i0:i1] = np.roll(seg, rng.integers(0, seg.size))
    return out
