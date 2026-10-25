"""V15: prespecified head-IMU gait features beyond cadence (step / segment / visit levels).

All definitions are fixed here before any test-set result is seen (no data-driven feature selection).
Per straight segment (reference-assisted segmentation, as in the primary analysis):

  cadence      60 / median A1 peak interval                                  [steps/min]
  step_cv      CV of A1 peak intervals within 0.5-1.5 x median               [%]
  step_asym    |mean(odd) - mean(even)| / mean of consecutive intervals      [%]   (needs all intervals in range)
  step_reg     unbiased autocorrelation of band-passed |a| at the step lag   [-]   (Moe-Nilssen & Helbostad)
  stride_reg   same at the stride lag (peak within 0.75-1.25 x 2 x step lag) [-]
  rms_v        RMS of band-passed vertical acceleration  a.g_hat             [m/s^2]
  rms_h        RMS of the norm of band-passed horizontal acceleration        [m/s^2]
  w_tilt_rms   RMS of the norm of band-passed horizontal angular rate        [deg/s]  (pitch+roll, frame-free)
  w_yaw_rms    RMS of band-passed angular rate about g_hat                   [deg/s]
Fixed-axis controls (sensitive to mounting rotation by construction):
  rms_x        RMS of band-passed X-axis acceleration                         [m/s^2]
  w_x_rms      RMS of band-passed X-axis angular rate (nominally yaw)         [deg/s]
Reference counterparts from foot heel strikes (same interval rules): ref_cadence, ref_step_cv, ref_step_asym.

The gait band is the selected step band (band_lo .. band_hi of config.detect).
Variability and asymmetry need >= MIN_IV intervals; segments of 6-10 m walks give 6-15 intervals, so
their reliability is an outcome, not an assumption.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks

from . import dsp
from .evaluate import windows, candidates

MIN_IV = 6
FEATS = ["cadence", "step_cv", "step_asym", "step_reg", "stride_reg", "rms_v", "rms_h", "w_tilt_rms", "w_yaw_rms"]
CONTROLS = ["rms_x", "w_x_rms"]
REF = ["ref_cadence", "ref_step_cv", "ref_step_asym"]


def _interval_feats(t):
    """cadence, CV, asymmetry from a sorted event-time vector (s)."""
    out = {"cadence": np.nan, "step_cv": np.nan, "step_asym": np.nan, "n_iv": 0}
    if len(t) < 3:
        return out
    iv = np.diff(t)
    med = np.median(iv)
    out["cadence"] = 60.0 / med
    ok = (iv >= 0.5 * med) & (iv <= 1.5 * med)
    out["n_iv"] = int(ok.sum())
    if ok.sum() >= MIN_IV:
        x = iv[ok]
        out["step_cv"] = 100 * np.std(x, ddof=1) / np.mean(x)
    if ok.all() and len(iv) >= MIN_IV:
        a, b = iv[0::2].mean(), iv[1::2].mean()
        out["step_asym"] = 100 * abs(a - b) / (0.5 * (a + b))
    return out


def _ac(x):
    x = x - x.mean()
    n = len(x)
    ac = np.correlate(x, x, "full")[n - 1:] / (n - np.arange(n))
    return ac / ac[0] if ac[0] > 0 else ac * np.nan


def _regularity(x, fs, cfg):
    """step and stride regularity of a band-passed segment."""
    a = cfg["autocorr"]
    T = dsp.autocorr_step_time(x, fs, a["min_lag_s"], a["max_lag_s"])
    if not np.isfinite(T):
        return np.nan, np.nan
    ac = _ac(x)
    k1 = int(round(T * fs))
    lo, hi = int(round(0.75 * 2 * T * fs)), min(len(ac) - 1, int(round(1.25 * 2 * T * fs)))
    sr = float(ac[k1]) if k1 < len(ac) else np.nan
    if hi <= lo:
        return sr, np.nan
    pk, _ = find_peaks(ac[lo:hi + 1])
    if pk.size == 0:
        return sr, np.nan
    return sr, float(ac[lo + pk[np.argmax(ac[lo + pk])]])


def signals(acc, gyr, fs, cfg, band_lo):
    d = cfg["detect"]
    bp = lambda x: dsp.bandpass(x, fs, band_lo, d["band_hi_hz"], d["filter_order"])  # noqa: E731
    g = dsp.gravity_dir(acc, fs, d["gravity_lp_hz"])
    v = np.einsum("ij,ij->i", acc, g)
    h = acc - v[:, None] * g
    wv = np.einsum("ij,ij->i", gyr, g)
    wh = gyr - wv[:, None] * g
    return {"A1": bp(np.linalg.norm(acc, axis=1)), "v": bp(v), "h": bp(h), "wv": bp(wv), "wh": bp(wh),
            "ax": bp(acc[:, d["a0_axis"]]), "wx": bp(gyr[:, d["a0_axis"]])}


def segment_features(sig, cand_s, seg, fs, cfg, ref_hs=None):
    a, b = seg
    i0, i1 = int(round(a * fs)), int(round(b * fs))
    out = {}
    c = cand_s[(cand_s >= a - 0.1) & (cand_s <= b + 0.1)]
    out.update(_interval_feats(np.sort(c)))
    rms = lambda x: float(np.sqrt(np.mean(np.square(x)))) if len(x) else np.nan  # noqa: E731
    if i1 - i0 >= int(2 * cfg["autocorr"]["max_lag_s"] * fs):
        out["step_reg"], out["stride_reg"] = _regularity(sig["A1"][i0:i1], fs, cfg)
    else:
        out["step_reg"] = out["stride_reg"] = np.nan
    out["rms_v"] = rms(sig["v"][i0:i1])
    out["rms_h"] = rms(np.linalg.norm(sig["h"][i0:i1], axis=1))
    out["w_tilt_rms"] = np.rad2deg(rms(np.linalg.norm(sig["wh"][i0:i1], axis=1)))
    out["w_yaw_rms"] = np.rad2deg(rms(sig["wv"][i0:i1]))
    out["rms_x"] = rms(sig["ax"][i0:i1])
    out["w_x_rms"] = np.rad2deg(rms(sig["wx"][i0:i1]))
    if ref_hs is not None:
        r = _interval_feats(ref_hs[(ref_hs >= a) & (ref_hs <= b)])
        out.update({"ref_cadence": r["cadence"], "ref_step_cv": r["step_cv"], "ref_step_asym": r["step_asym"],
                    "ref_n_iv": r["n_iv"]})
    out["seg_dur_s"] = b - a
    return out


def trial_features(acc, gyr, valid, tr, cfg, band_lo, lag, with_ref=True):
    fs = tr.fs
    w = windows(tr, fs, cfg["detect"]["window_pad_s"])
    sig = signals(acc, gyr, fs, cfg, band_lo)
    i0, i1 = max(0, int(w["full"][0] * fs)), min(len(valid), int(w["full"][1] * fs))
    cand = candidates(sig["A1"], fs, cfg, i0, i1, valid) - lag
    rows = []
    for sname, seg in w["segs"].items():
        rows.append({"segment": sname, **segment_features(sig, cand, seg, fs, cfg, tr.hs if with_ref else None)})
    return rows


def simulate_features(tr, cfg, band_lo, lag, rng, rot_deg=(10, 20, 30, 45), n_axes=10,
                      lever_m=(0.02, 0.04, 0.08), n_dirs=10, lp_hz=10.0):
    """Feature values under rigid rotations and lever arms (trial-level mean of the two segments)."""
    s = tr.sensors["HE"]
    base = {"trial": tr.trial_id, "participant": tr.participant, "cohort": tr.cohort}

    def agg(rows):
        keys = FEATS + CONTROLS
        return {k: float(np.nanmean([r[k] for r in rows])) if any(np.isfinite(r[k]) for r in rows) else np.nan
                for k in keys}

    out = [{**base, "pert": "none", "level": 0.0, "rep": 0, "tilt_deg": 0.0,
            **agg(trial_features(s.acc, s.gyr, s.valid, tr, cfg, band_lo, lag, False))}]
    for th in rot_deg:
        for k in range(n_axes):
            R = dsp.rotation_matrix(dsp.random_unit(rng)[0], np.deg2rad(th))
            f = agg(trial_features(s.acc @ R.T, s.gyr @ R.T, s.valid, tr, cfg, band_lo, lag, False))
            out.append({**base, "pert": "rotation", "level": float(th), "rep": k,
                        "tilt_deg": float(np.rad2deg(np.arccos(np.clip(R[0, 0], -1, 1)))), **f})
    for off in lever_m:
        for k, u in enumerate(dsp.random_unit(rng, n_dirs)):
            A = dsp.lever_arm(s.acc, s.gyr, tr.fs, off * u, lp_hz)
            f = agg(trial_features(A, s.gyr, s.valid, tr, cfg, band_lo, lag, False))
            out.append({**base, "pert": "lever", "level": float(off), "rep": k, "tilt_deg": 0.0, **f})
    return out


def clinical_meta(tr):
    m = tr.meta_raw

    def num(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return np.nan
    vga = m.get("visualGaitAssessment", m.get("visualGaitEvaluation"))
    return {"trial": tr.trial_id, "participant": tr.participant, "cohort": tr.cohort, "visit": tr.visit,
            "sensor_type": tr.sensor_type, "age": tr.age, "sex": m.get("gender"), "height_m": num(m.get("height")),
            "weight_kg": num(m.get("weight")), "vga": num(vga), "tug_s": num(m.get("TUG")),
            "score_name": m.get("evaluationScoreName"), "score_value": num(m.get("evaluationScoreValue")),
            "deficit_side": m.get("clinicalDeficitSide"), "days_since_first": num(m.get("daysSinceFirstSession")),
            "protocol": m.get("protocol")}
