"""Signal processing primitives used by all branches."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import median_filter
from scipy.signal import butter, find_peaks, sosfiltfilt


def bandpass(x: np.ndarray, fs: float, lo: float, hi: float, order: int = 3) -> np.ndarray:
    sos = butter(order, [lo, hi], btype="band", fs=fs, output="sos")
    return sosfiltfilt(sos, x, axis=0)


def lowpass(x: np.ndarray, fs: float, fc: float, order: int = 2) -> np.ndarray:
    sos = butter(order, fc, btype="low", fs=fs, output="sos")
    return sosfiltfilt(sos, x, axis=0)


def robust_sigma(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    return float(1.4826 * np.median(np.abs(x - np.median(x)))) if x.size else 0.0


def gravity_dir(acc: np.ndarray, fs: float, fc: float) -> np.ndarray:
    """Unit vector of low-passed specific force ('up' in specific-force sense)."""
    g = lowpass(acc, fs, fc)
    return g / np.linalg.norm(g, axis=1, keepdims=True)


def detect_peaks(sig: np.ndarray, fs: float, i0: int, i1: int, prom_floor: float,
                 k_sigma: float, min_dist_s: float, valid: np.ndarray | None = None) -> np.ndarray:
    """Peak sample indices of a band-passed signal inside [i0, i1)."""
    seg = sig[i0:i1]
    prom = max(prom_floor, k_sigma * robust_sigma(seg))
    pk, _ = find_peaks(seg, prominence=prom, distance=max(1, int(round(min_dist_s * fs))))
    pk = pk + i0
    if valid is not None:
        pk = pk[valid[pk]]
    return pk


def turn_rate(gyr: np.ndarray, ghat: np.ndarray) -> np.ndarray:
    """q(t) = |omega . g_hat| in rad/s (proxy of rotation rate about vertical)."""
    return np.abs(np.einsum("ij,ij->i", gyr, ghat))


def runs(mask: np.ndarray) -> list[tuple[int, int]]:
    m = np.concatenate([[False], mask, [False]]).astype(int)
    d = np.diff(m)
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


def gate_mask(q_rads: np.ndarray, fs: float, thr_dps: float, med_win_s: float,
              min_dur_s: float, pad_s: float) -> np.ndarray:
    w = max(1, int(round(med_win_s * fs)) | 1)
    qs = median_filter(np.rad2deg(q_rads), size=w, mode="nearest")
    above = qs > thr_dps
    out = np.zeros_like(above)
    pad = int(round(pad_s * fs))
    for a, b in runs(above):
        if (b - a) / fs >= min_dur_s:
            out[max(0, a - pad): min(len(out), b + pad)] = True
    return out


def autocorr_step_time(x: np.ndarray, fs: float, min_lag_s: float, max_lag_s: float) -> float:
    """Step time from the first dominant unbiased-autocorrelation peak (Moe-Nilssen & Helbostad 2004)."""
    x = x - np.mean(x)
    n = len(x)
    if n < int(2 * max_lag_s * fs):
        return np.nan
    full = np.correlate(x, x, mode="full")[n - 1:]
    ac = full / (n - np.arange(n))
    ac = ac / ac[0]
    lo, hi = int(min_lag_s * fs), min(n - 1, int(max_lag_s * fs))
    seg = ac[lo:hi + 1]
    pk, prop = find_peaks(seg, prominence=0.05)
    if pk.size == 0:
        return np.nan
    # first peak reaching 60 % of the largest peak in range: the step (not stride) lag
    strong = pk[seg[pk] >= 0.6 * seg[pk].max()] if seg[pk].max() > 0 else pk
    k = strong[0]
    # parabolic refinement
    j = k + lo
    if 0 < j < len(ac) - 1:
        y0, y1, y2 = ac[j - 1], ac[j], ac[j + 1]
        den = y0 - 2 * y1 + y2
        off = 0.5 * (y0 - y2) / den if den != 0 else 0.0
    else:
        off = 0.0
    return (j + off) / fs


def rotation_matrix(axis: np.ndarray, theta_rad: float) -> np.ndarray:
    u = np.asarray(axis, float)
    u = u / np.linalg.norm(u)
    K = np.array([[0, -u[2], u[1]], [u[2], 0, -u[0]], [-u[1], u[0], 0]])
    return np.eye(3) + np.sin(theta_rad) * K + (1 - np.cos(theta_rad)) * K @ K


def random_unit(rng: np.random.Generator, n: int = 1) -> np.ndarray:
    v = rng.normal(size=(n, 3))
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def lever_arm(acc: np.ndarray, gyr: np.ndarray, fs: float, r: np.ndarray, lp_hz: float) -> np.ndarray:
    """Specific force at a point displaced by r (sensor frame) on the same rigid body:
    a'' = a + alpha x r + omega x (omega x r)."""
    w = lowpass(gyr, fs, lp_hz)
    alpha = np.gradient(w, 1.0 / fs, axis=0)
    r = np.broadcast_to(np.asarray(r, float), acc.shape)
    return acc + np.cross(alpha, r) + np.cross(gyr, np.cross(gyr, r))
