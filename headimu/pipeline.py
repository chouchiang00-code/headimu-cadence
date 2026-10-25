"""Trial-level workers (top-level functions so they can run in worker processes)."""
from __future__ import annotations

import numpy as np

from . import dsp
from .evaluate import (branch_signals, candidates, gated_eval, matching_metrics, random_gate,
                       segment_metrics, static_slice, step_time_from_ac, turn_detection, windows)

HE_BRANCHES = ("A0", "A0g", "A1")
LB_BRANCHES = ("A0g", "A1")


# ----------------------------------------------------------------------------- QC
def qc_trial(tr, cfg):
    fs = tr.fs
    row = {"trial": tr.trial_id, "participant": tr.participant, "cohort": tr.cohort, "visit": tr.visit,
           "sensor_type": tr.sensor_type, "age": tr.age, "notes": ";".join(tr.notes)}
    w = windows(tr, fs, cfg["detect"]["window_pad_s"])
    reason = None
    if "HE" not in tr.sensors:
        reason = "head_signal_missing_or_empty"
    elif tr.hs.size < 4:
        reason = "reference_events_missing"
    elif tr.turn is None:
        reason = "turn_boundaries_missing"
    elif "events_beyond_signal_length" in tr.notes:
        reason = "events_beyond_signal_length"
    elif w and not (w["segs"]["S1"][1] > w["segs"]["S1"][0] and w["segs"]["S2"][1] > w["segs"]["S2"][0]):
        reason = "turn_outside_walking_bout"
    row["exclusion"] = reason or ""
    for loc in ("HE", "LB"):
        s = tr.sensors.get(loc)
        if s is None:
            continue
        info = s.info
        n = s.acc.shape[0]
        st = static_slice(tr, fs, n, cfg["qc"]["min_static_s"])
        sr = getattr(tr, "raw", {}).get(loc, s)   # raw signal for saturation / static statistics
        a, g = sr.acc, sr.gyr
        rng_cfg = cfg["qc"]["sensor_ranges"].get(tr.sensor_type, cfg["qc"]["sensor_ranges"]["unknown"])
        frac = cfg["qc"]["saturation_fraction_of_range"]
        row.update({
            f"{loc}_n": n,
            f"{loc}_grid": info.get("grid"),
            f"{loc}_acc_unit_in": info.get("acc_unit_in"),
            f"{loc}_gyr_unit_in": info.get("gyr_unit_in"),
            f"{loc}_missing_frac": info.get("missing_fraction"),
            f"{loc}_longest_gap_s": info.get("longest_gap_s"),
            f"{loc}_duplicate_counter": info.get("duplicate_counter", 0),
            f"{loc}_invalid_frac": float(1 - s.valid.mean()),
            f"{loc}_acc_sat_frac": float(np.mean(np.abs(a) >= frac * rng_cfg["acc_mps2"])) if rng_cfg["acc_mps2"] else np.nan,
            f"{loc}_gyr_sat_frac": float(np.mean(np.abs(np.rad2deg(g)) >= frac * rng_cfg["gyr_dps"])) if rng_cfg["gyr_dps"] else np.nan,
            f"{loc}_static_s": (st.stop - st.start) / fs,
            f"{loc}_static_acc_sd_mps2": float(np.mean(np.std(a[st], axis=0))),
            f"{loc}_static_gyr_sd_dps": float(np.mean(np.std(np.rad2deg(g[st]), axis=0))),
            f"{loc}_static_gnorm_mps2": float(np.linalg.norm(np.mean(a[st], axis=0))),
            f"{loc}_static_gyr_bias_dps": float(np.linalg.norm(np.rad2deg(np.mean(g[st], axis=0)))),
            f"{loc}_static_xfrac": float(abs(np.mean(s.acc[st, 0])) / max(1e-9, np.linalg.norm(np.mean(s.acc[st], axis=0)))),
            f"{loc}_signal_source": info.get("source", "raw"),
        })
        a, g = s.acc, s.gyr   # analysed signal for turn angle and periodicity
        if w and not reason:
            ghat = dsp.gravity_dir(a, fs, cfg["detect"]["gravity_lp_hz"])
            q = dsp.turn_rate(g, ghat)
            ts, te = int(w["turn"][0] * fs), int(w["turn"][1] * fs)
            row[f"{loc}_turn_angle_deg"] = float(np.rad2deg(np.sum(q[ts:te]) / fs))
            # periodicity: dominant frequency of |a| on straight segments vs reference step frequency
            sig = dsp.bandpass(np.linalg.norm(a, axis=1), fs, 0.6, 3.0, 3)
            ratios, regs = [], []
            for seg in w["segs"].values():
                i0, i1 = int(seg[0] * fs), int(seg[1] * fs)
                if i1 - i0 < 2 * fs:
                    continue
                x = sig[i0:i1] - sig[i0:i1].mean()
                nfft = max(1024, 1 << int(np.ceil(np.log2(len(x)))))
                P = np.abs(np.fft.rfft(x * np.hanning(len(x)), nfft)) ** 2
                f = np.fft.rfftfreq(nfft, 1 / fs)
                band = (f >= 0.6) & (f <= 3.0)
                fdom = f[band][np.argmax(P[band])]
                r = tr.hs[(tr.hs >= seg[0]) & (tr.hs <= seg[1])]
                if len(r) >= 4:
                    ratios.append(fdom * np.median(np.diff(r)))
                Tac = dsp.autocorr_step_time(x, fs, 0.3, 0.9)
                if np.isfinite(Tac):
                    n0 = len(x)
                    ac = np.correlate(x, x, "full")[n0 - 1:] / (n0 - np.arange(n0))
                    regs.append(ac[int(round(Tac * fs))] / ac[0])
            row[f"{loc}_fdom_over_fstep"] = float(np.median(ratios)) if ratios else np.nan
            row[f"{loc}_step_regularity"] = float(np.median(regs)) if regs else np.nan
    return row


# ----------------------------------------------------------------------------- lag estimation
def lag_pairs(tr, cfg, band_lo, loc, branch):
    fs = tr.fs
    s = tr.sensors[loc]
    w = windows(tr, fs, cfg["detect"]["window_pad_s"])
    st = static_slice(tr, fs, s.acc.shape[0], cfg["qc"]["min_static_s"])
    sig, _ = branch_signals(s.acc, s.gyr, fs, cfg, band_lo, static=st, which=(branch,))
    out = []
    for seg in w["segs"].values():
        i0, i1 = int((seg[0] - 0.2) * fs), int((seg[1] + 0.5) * fs)
        c = candidates(sig[branch], fs, cfg, max(0, i0), min(len(s.valid), i1), s.valid)
        r = tr.hs[(tr.hs >= seg[0]) & (tr.hs <= seg[1])]
        for h in r:
            d = c - h
            d = d[np.abs(d) <= cfg["detect"]["lag_search_s"]]
            if d.size:
                out.append(float(d[np.argmin(np.abs(d))]))
    return out


# ----------------------------------------------------------------------------- main trial evaluation
def evaluate_trial(tr, cfg, band_lo, lags, thr_list, rng_seed, n_random=None, locs=("HE", "LB")):
    fs = tr.fs
    w = windows(tr, fs, cfg["detect"]["window_pad_s"])
    tol = cfg["metrics"]["match_tol_s"]
    base = {"trial": tr.trial_id, "participant": tr.participant, "cohort": tr.cohort, "visit": tr.visit,
            "sensor_type": tr.sensor_type, "age": tr.age}
    seg_rows, match_rows, gate_rows = [], [], []
    rng = np.random.default_rng(rng_seed)
    n_random = cfg["gate"]["random_reps"] if n_random is None else n_random
    for loc in locs:
        s = tr.sensors.get(loc)
        if s is None:
            continue
        st = static_slice(tr, fs, s.acc.shape[0], cfg["qc"]["min_static_s"])
        branches = HE_BRANCHES if loc == "HE" else LB_BRANCHES
        sig, q = branch_signals(s.acc, s.gyr, fs, cfg, band_lo, static=st, which=branches)
        i0, i1 = max(0, int(w["full"][0] * fs)), min(len(s.valid), int(w["full"][1] * fs))
        cands = {b: candidates(sig[b], fs, cfg, i0, i1, s.valid) for b in branches}
        for b in branches:
            lag = lags.get(f"{loc}_{b}", 0.0)
            seg_c = []
            for sname, seg in w["segs"].items():
                m = segment_metrics(cands[b], lag, tr.hs, seg, s.valid, fs, cfg)
                seg_rows.append({**base, "loc": loc, "method": b, "segment": sname, **m})
                c = cands[b] - lag
                seg_c.append(c[(c >= seg[0] - 0.2) & (c <= seg[1] + 0.2)])
            if loc == "HE":
                ref_s = np.concatenate([tr.hs[(tr.hs >= a) & (tr.hs <= e)] for a, e in w["segs"].values()])
                cs = np.concatenate(seg_c)
                for t_ in cfg["metrics"]["match_tol_sensitivity_s"]:
                    mm = matching_metrics(cs, ref_s, t_)
                    match_rows.append({**base, "loc": loc, "method": b, "tol_s": t_, **mm})
        # autocorrelation on the A1 signal
        for sname, seg in w["segs"].items():
            T = step_time_from_ac(sig["A1"], fs, seg, cfg)
            r = tr.hs[(tr.hs >= seg[0]) & (tr.hs <= seg[1])]
            ri = np.diff(r)
            row = {**base, "loc": loc, "method": "AC", "segment": sname, "n_ref": len(r), "n_cand": np.nan,
                   "detect_ratio": np.nan}
            if len(ri) >= cfg["metrics"]["min_ref_intervals"] and np.isfinite(T):
                Tr = float(np.median(ri))
                ratio = T / Tr
                mcfg = cfg["metrics"]
                row.update(T_ref=Tr, T_imu=T, e_T=T - Tr, e_C=60 / T - 60 / Tr, C_ref=60 / Tr, C_imu=60 / T, ratio=ratio,
                           halving=float(mcfg["halving_ratio"][0] <= ratio <= mcfg["halving_ratio"][1]),
                           doubling=float(mcfg["doubling_ratio"][0] <= ratio <= mcfg["doubling_ratio"][1]))
            seg_rows.append(row)
        # gating (head only)
        if loc == "HE":
            lag = lags.get("HE_A1", 0.0)
            ref_full = tr.hs
            allc = cands["A1"]
            nog = gated_eval(allc, lag, ref_full, np.zeros(len(q), bool), fs, w["full"], tol)
            for thr in thr_list:
                gm = dsp.gate_mask(q, fs, thr, cfg["gate"]["median_win_s"], cfg["gate"]["min_dur_s"], cfg["gate"]["pad_s"])
                td = turn_detection(gm, fs, w["full"], w["turn"])
                a2 = gated_eval(allc, lag, ref_full, gm, fs, w["full"], tol)
                rr = [gated_eval(allc, lag, ref_full, random_gate(gm, fs, w["full"], rng), fs, w["full"], tol)
                      for _ in range(n_random)] if n_random else []
                a2r = {k: float(np.nanmean([x[k] for x in rr])) if rr else np.nan for k in a2}
                gate_rows.append({**base, "threshold_dps": thr, **td,
                                  **{f"A1_{k}": v for k, v in nog.items()},
                                  **{f"A2_{k}": v for k, v in a2.items()},
                                  **{f"A2R_{k}": v for k, v in a2r.items()}})
    return seg_rows, match_rows, gate_rows


# ----------------------------------------------------------------------------- simulations
def simulate_trial(tr, cfg, band_lo, lags, thr, rng_seed):
    fs = tr.fs
    s = tr.sensors["HE"]
    w = windows(tr, fs, cfg["detect"]["window_pad_s"])
    st = static_slice(tr, fs, s.acc.shape[0], cfg["qc"]["min_static_s"])
    base = {"trial": tr.trial_id, "participant": tr.participant, "cohort": tr.cohort, "sensor_type": tr.sensor_type}
    rng = np.random.default_rng(rng_seed)
    rot_rows, lev_rows = [], []
    i0, i1 = max(0, int(w["full"][0] * fs)), min(len(s.valid), int(w["full"][1] * fs))

    def seg_eval(sig, b, extra, rows):
        c = candidates(sig, fs, cfg, i0, i1, s.valid)
        for sname, seg in w["segs"].items():
            m = segment_metrics(c, lags.get(f"HE_{b}", 0.0), tr.hs, seg, s.valid, fs, cfg)
            rows.append({**base, **extra, "method": b, "segment": sname, **m})

    # rigid rotation: only A0 changes (norm and gravity projection are invariant)
    sig0, _ = branch_signals(s.acc, s.gyr, fs, cfg, band_lo, static=st, which=("A0", "A1"))
    seg_eval(sig0["A0"], "A0", {"theta_deg": 0, "tilt_deg": 0.0, "rep": 0}, rot_rows)
    for th in cfg["sim"]["rotation_deg"]:
        for rep in range(cfg["sim"]["rotation_reps"]):
            R = dsp.rotation_matrix(dsp.random_unit(rng)[0], np.deg2rad(th))
            A = s.acc @ R.T
            Wg = s.gyr @ R.T
            sig, _ = branch_signals(A, Wg, fs, cfg, band_lo, static=st, which=("A0",) if rep else ("A0", "A1"))
            if rep == 0:  # numerical check of the analytical invariance
                assert np.allclose(sig["A1"], sig0["A1"], atol=1e-6), "norm not rotation invariant?"
            tilt = float(np.rad2deg(np.arccos(np.clip(R[0, 0], -1, 1))))
            seg_eval(sig["A0"], "A0", {"theta_deg": th, "tilt_deg": tilt, "rep": rep}, rot_rows)

    # lever arm: affects every acceleration feature
    mode = cfg["sim"]["lever_direction_mode"]
    dirs = dsp.random_unit(rng, cfg["sim"]["lever_directions"]) if mode == "sphere" else \
        np.array([cfg["sim"]["lever_fixed_direction"]], float)
    tol = cfg["metrics"]["match_tol_s"]
    for off in [0.0] + list(cfg["sim"]["lever_offsets_m"]):
        for k, u in enumerate(dirs if off > 0 else dirs[:1]):
            A = dsp.lever_arm(s.acc, s.gyr, fs, off * u, cfg["sim"]["angacc_lp_hz"]) if off > 0 else s.acc
            sig, q = branch_signals(A, s.gyr, fs, cfg, band_lo, static=st, which=("A0g", "A1"))
            extra = {"offset_m": off, "dir": k}
            seg_eval(sig["A0g"], "A0g", extra, lev_rows)
            seg_eval(sig["A1"], "A1", extra, lev_rows)
            gm = dsp.gate_mask(q, fs, thr, cfg["gate"]["median_win_s"], cfg["gate"]["min_dur_s"], cfg["gate"]["pad_s"])
            c = candidates(sig["A1"], fs, cfg, i0, i1, s.valid)
            ge = gated_eval(c, lags.get("HE_A1", 0.0), tr.hs, gm, fs, w["full"], tol)
            lev_rows.append({**base, **extra, "method": "A2", "segment": "full", **ge})
    return rot_rows, lev_rows
