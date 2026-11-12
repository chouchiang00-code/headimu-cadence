"""Sample-by-sample (streaming) implementation of the causal head-only pipeline B2 (headimu.endtoend.causal).

Each call to `push(acc_xyz, gyr_xyz, valid)` consumes one sample and may emit a cadence output. All state is held in
fixed-size buffers (sizes depend only on fs and the frozen parameters), so the memory footprint is known in advance.
Arithmetic operations are counted per stage (`ops`): an add, multiply, divide, compare or square root counts as one
operation; a sort of n values is counted as n*ceil(log2 n) comparisons. The counts describe THIS implementation (naive
trailing max/min scans, sorting for medians), i.e. an upper bound for an optimised embedded version.
"""
from __future__ import annotations

import math
from collections import deque

import numpy as np
from scipy.signal import butter, sosfilt_zi


def _nlogn(n):
    return n * max(1, math.ceil(math.log2(max(n, 2))))


class StreamB2:
    def __init__(self, fs, P):
        self.fs, self.P = fs, P
        self.sos = butter(P["order"], [P["band_lo"], P["band_hi"]], btype="band", fs=fs, output="sos")
        self.sog = butter(2, P["grav_lp"], btype="low", fs=fs, output="sos")
        self.w = max(1, int(round(P["rms_win_s"] * fs)))
        self.on_h, self.off_h = int(P["on_hold_s"] * fs), int(P["off_hold_s"] * fs)
        self.thr_on, self.thr_off = P["thr_on"], P["thr_on"] * P["hyst"]
        self.m = max(1, int(round(P["gate_med_s"] * fs)))
        self.gmin, self.gend = int(P["gate_min_s"] * fs), int(P["gate_pad_s"] * fs)
        self.dmin, self.dc = int(round(P["min_dist_s"] * fs)), int(round(P["confirm_s"] * fs))
        self.sw = int(P["sigma_win_s"] * fs)
        self.tm = int(round(P.get("trail_min_s", 0.9) * fs))
        self.nbuf = max(self.sw + 1, self.tm, self.dmin) + self.dc + 1
        self.j = -1
        self.zb = None; self.zg = None
        self.a1 = deque(maxlen=self.nbuf); self.vb = deque(maxlen=self.nbuf)
        self.sq = deque(maxlen=self.w); self.ssum = 0.0
        self.qb = deque(maxlen=self.m)
        self.st = False; self.cnt = 0
        self.run = 0; self.gap = 0; self.st_t = False
        self.last = -10 ** 9
        self.buf = deque(maxlen=P["k_iv"] + 1)
        self.ops = {"filters": 0, "rms_walk": 0, "gate": 0, "peak_scan": 0, "sigma": 0, "cadence": 0}
        self.n_sigma = 0

    def state_bytes(self, bytes_per_value=4):
        n_vals = (self.sos.size + self.sog.size            # coefficients
                  + self.sos.shape[0] * 2 + 3 * 2           # filter states
                  + self.nbuf + self.w + self.m + (self.P["k_iv"] + 1) + 3 + 10)   # buffers, gravity, scalars
        return n_vals * bytes_per_value + self.nbuf // 8   # validity flags as bits

    @staticmethod
    def _sos_step(sos, z, x):
        for s in range(sos.shape[0]):
            b0, b1, b2, _, a1, a2 = sos[s]
            y = b0 * x + z[s, 0]
            z[s, 0] = b1 * x - a1 * y + z[s, 1]
            z[s, 1] = b2 * x - a2 * y
            x = y
        return x

    def push(self, acc, gyr, valid):
        P, fs, o = self.P, self.fs, self.ops
        self.j += 1; j = self.j
        nrm = math.sqrt(acc[0] * acc[0] + acc[1] * acc[1] + acc[2] * acc[2]); o["filters"] += 6
        if self.zb is None:
            self.zb = sosfilt_zi(self.sos) * nrm
            self.zg = [sosfilt_zi(self.sog) * acc[i] for i in range(3)]
        a1 = self._sos_step(self.sos, self.zb, nrm); o["filters"] += 9 * self.sos.shape[0]
        gl = [self._sos_step(self.sog, self.zg[i], acc[i]) for i in range(3)]; o["filters"] += 3 * 9
        gn = max(math.sqrt(gl[0] ** 2 + gl[1] ** 2 + gl[2] ** 2), 1e-9); o["filters"] += 7
        q = math.degrees(abs((gyr[0] * gl[0] + gyr[1] * gl[1] + gyr[2] * gl[2]) / gn)); o["filters"] += 8
        self.a1.append(a1); self.vb.append(bool(valid))
        # trailing RMS and walking state (hysteresis + hold)
        if len(self.sq) == self.w:
            self.ssum -= self.sq[0]
        self.sq.append(a1 * a1); self.ssum += a1 * a1
        rms = math.sqrt(max(self.ssum, 0.0) / len(self.sq)); o["rms_walk"] += 6
        if not self.st:
            self.cnt = self.cnt + 1 if rms > self.thr_on else 0
            if self.cnt >= self.on_h:
                self.st, self.cnt = True, 0
        else:
            self.cnt = self.cnt + 1 if rms < self.thr_off else 0
            if self.cnt >= self.off_h:
                self.st, self.cnt = False, 0
        o["rms_walk"] += 3
        walking = self.st
        # turn gate: trailing median, threshold, duration
        self.qb.append(q)
        qm = float(np.median(self.qb)); o["gate"] += _nlogn(len(self.qb)) + 1
        if qm > P["q_thr_dps"]:
            self.run += 1; self.gap = 0
            if not self.st_t and self.run >= self.gmin:
                self.st_t = True
        else:
            self.run = 0
            if self.st_t:
                self.gap += 1
                if self.gap >= self.gend:
                    self.st_t = False
        o["gate"] += 4
        turning = self.st_t
        # peak at k = j - dc is decided now (needs dc samples of look-ahead = confirmation delay)
        out = None
        k = j - self.dc
        if k >= self.dmin:
            buf = list(self.a1); vb = list(self.vb)
            ik = len(buf) - 1 - self.dc                     # index of sample k in the buffer
            x = buf[ik]
            o["peak_scan"] += self.dmin + self.dc + 1
            if not (x < max(buf[ik - self.dmin:ik]) or x <= max(buf[ik + 1:ik + self.dc + 1])) and k - self.last >= self.dmin:
                hist = np.array(buf[max(0, ik - min(self.sw, k)):ik + 1])
                med = np.median(hist); sig = 1.4826 * float(np.median(np.abs(hist - med)))
                self.n_sigma += 1; o["sigma"] += 2 * _nlogn(len(hist)) + 2 * len(hist) + 2
                thr = max(P["prom_floor"], P["prom_k"] * sig)
                lo = buf[max(0, ik - min(self.tm, k)):ik]
                o["peak_scan"] += len(lo) + 3
                if not (x - min(lo) < thr or not vb[ik]):
                    self.last = k
                    # cadence at confirmation time j
                    if not walking or turning:
                        self.buf.clear()
                    else:
                        self.buf.append(k)
                        b = list(self.buf)
                        iv = np.diff(b) / fs
                        iv = iv[iv < 2.0]
                        o["cadence"] += 3 * len(b) + _nlogn(max(len(iv), 1)) + 2
                        if len(iv) >= P["min_iv"]:
                            out = (j / fs, 60.0 / float(np.median(iv)), k / fs)
        return out
