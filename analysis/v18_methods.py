"""V18 candidate cadence estimators for straight segments (B0 segmentation). Pure functions of one sensor's signal;
the reference is used only for scoring."""
import numpy as np
from scipy.signal import find_peaks
from headimu import dsp
from headimu.evaluate import _intervals

AC_MIN, AC_MAX = 0.30, 0.90


def base_peaks(x, fs, cfg, i0, i1, valid, k_sigma=None, min_dist=None):
    d = cfg["detect"]
    return dsp.detect_peaks(x, fs, i0, i1, d["prominence_floor_mps2"], k_sigma or d["prominence_k_sigma"],
                            min_dist or d["min_peak_distance_s"], valid) / fs


def seg_peaks(c, lag, a, b):
    c = np.asarray(c) - lag
    return c[(c >= a - 0.1) & (c <= b + 0.1)]


def cad_median(c, lag, valid, fs):
    iv = _intervals(np.asarray(c) + lag, valid, fs)
    return 60.0 / np.median(iv) if len(iv) >= 2 else np.nan, iv


def ac_step(x, fs, a, b):
    i, j = int(a * fs), int(b * fs)
    if j - i < 2 * AC_MAX * fs:
        return np.nan
    return dsp.autocorr_step_time(x[i:j], fs, AC_MIN, AC_MAX)


def ac_profile(x, fs, a, b):
    i, j = int(a * fs), int(b * fs); y = x[i:j] - np.mean(x[i:j]); n = len(y)
    if n < 2 * AC_MAX * fs:
        return None
    ac = np.correlate(y, y, "full")[n - 1:] / (n - np.arange(n)); return ac / ac[0]


def repaired_intervals(iv, T):
    """Split intervals that look like k missed steps (k = round(iv/T) >= 2) and merge runs of short intervals
    (extra peaks) so that each merged interval is the closest to T. Returns step intervals (s)."""
    out = []; acc = 0.0
    for d in iv:
        acc += d
        if acc < 0.6 * T:            # too short: an extra peak; keep accumulating
            continue
        k = max(1, int(round(acc / T)))
        out.extend([acc / k] * k)
        acc = 0.0
    return np.array(out)


# ----------------------------------------------------------------------------- frozen V18 estimator
# Chosen on the development set only (77 participants; participant 5-fold CV inside the development set selected it
# in 3 of 5 folds), frozen on 2026-11-12 before any test-set evaluation of V18 methods.
AGS_MINDIST_FRAC = 0.55          # peak minimum distance as a fraction of the autocorrelation step time
AGS_MINDIST_CLIP = (0.25, 0.70)  # s


def stride_cadence(iv):
    s = np.asarray(iv)[:-1] + np.asarray(iv)[1:]
    return 120.0 / np.median(s) if len(s) >= 2 else np.nan


def ags_cadence(x, fs, cfg, i0, i1, valid, lag, a, b):
    """Autocorrelation-guided stride cadence (AGS) for one straight segment [a, b] (s).
    1) step time T from the unbiased autocorrelation of the band-passed signal in the segment (0.30-0.90 s);
    2) peaks re-detected with minimum distance clip(0.55 T, 0.25, 0.70) s (other detector settings unchanged);
    3) peak cadence from the median stride (sum of two consecutive valid step intervals): robust to left-right
       asymmetry, where the median single step interval jumps between the short and the long step;
    4) output = mean of the peak stride cadence and 60 / T; if T is undefined, the peak stride cadence with the
       default detector."""
    T = ac_step(x, fs, a, b)
    if T == T:
        md = float(np.clip(AGS_MINDIST_FRAC * T, *AGS_MINDIST_CLIP))
        c = seg_peaks(base_peaks(x, fs, cfg, i0, i1, valid, min_dist=md), lag, a, b)
    else:
        c = seg_peaks(base_peaks(x, fs, cfg, i0, i1, valid), lag, a, b)
    from headimu.evaluate import _intervals
    iv = _intervals(np.asarray(c) + lag, valid, fs)
    cp = stride_cadence(iv)
    if T == T and cp == cp:
        return 0.5 * (cp + 60.0 / T), {"T": T, "C_peak_stride": cp, "n_peaks": len(c)}
    return cp, {"T": T, "C_peak_stride": cp, "n_peaks": len(c)}
