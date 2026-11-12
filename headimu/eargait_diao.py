"""Re-implementation of the EarGait (Seifer et al., Sensors 2023; github.com/mad-lab-fau/eargait, v3.4.0) default
initial-contact detector `DiaoAdaptedEventDetection` (Diao et al., Physiol. Meas. 2020), without its heavy
dependencies (tensorflow/torch/pyts). Steps copied from eargait/event_detection/diao_*.py:
  1 FIR low-pass, Kaiser window (ripple 60 dB, transition width 2 Hz), cutoff 5 Hz, lfilter, group delay removed
  2 singular spectrum analysis (window = fs samples, groups [[0],[1],[2],[3..]]) of the superior-inferior acceleration
  3 IC = find_peaks(-component_1, height=0.2, distance=0.2 s)
Only the IC (step) events are needed for cadence; side assignment and terminal contacts are not used.
The SSA follows pyts.decomposition.SingularSpectrumAnalysis (eigh of the lag-covariance X X^T, eigenvalues descending,
rank-one reconstruction, diagonal averaging); `ssa_components` is checked against the pyts algorithm in tests.
Adapted from EarGait, MIT License, Copyright (c) 2018 MaD-Lab Erlangen.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks, firwin, kaiserord, lfilter


def fir_lowpass(x: np.ndarray, fs: float) -> np.ndarray:
    nyq = fs / 2.0
    n, beta = kaiserord(60.0, 2.0 / nyq)
    taps = firwin(n, 5.0 / nyq, window=("kaiser", beta))
    delay = int(0.5 * (n - 1))
    y = lfilter(taps, 1.0, x)
    out = np.full_like(x, np.nan, dtype=float)
    out[: len(x) - delay] = y[delay:]
    return out


def ssa_components(x: np.ndarray, L: int, comps=(0, 1, 2)) -> np.ndarray:
    x = np.asarray(x, float)
    N = len(x); K = N - L + 1
    idx = np.arange(L)[:, None] + np.arange(K)[None, :]
    X = x[idx]                                   # L x K trajectory matrix
    w, v = np.linalg.eigh(X @ X.T)
    v = v[:, ::-1]
    out = []
    cnt = np.bincount(idx.ravel(), minlength=N)
    for j in comps:
        u = v[:, j]
        Xj = np.outer(u, u @ X)                  # rank-one elementary matrix
        out.append(np.bincount(idx.ravel(), weights=Xj.ravel(), minlength=N) / cnt)
    return np.array(out)


def detect_ic(acc_si: np.ndarray, fs: float) -> np.ndarray:
    """IC sample indices from a superior-inferior acceleration (m/s^2) of one walking bout (> 3 s)."""
    L = int(round(fs))
    comp = ssa_components(acc_si, L, comps=(1,))[0]
    pk, _ = find_peaks(-comp, height=0.2, distance=fs * 0.2)
    return pk
