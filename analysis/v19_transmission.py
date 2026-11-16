#!/usr/bin/env python3
"""V19 (post hoc, descriptive): the forehead as a sensing site. Head-versus-trunk (L4/L5) transmission of the
walking acceleration in the same straight segments (B0 reference segmentation), all included Voisard trials.

Per straight segment (definitions fixed before looking at results):
  f_s        reference step frequency (1 / median reference step interval)
  vertical acceleration of each sensor: projection of acc on its own gravity direction (0.3-Hz low-pass), mean removed
  G_k        gain |S_lh(f)| / S_ll(f) (H1 estimator, Welch, 2.56-s Hann windows, 50% overlap) at f = k f_s,
             k = 0.5 (stride), 1 (step), 2, 3 (harmonics); linear interpolation between frequency bins
  C_k        magnitude-squared coherence at the same frequencies
  delay_ms   time delay of the head relative to the trunk at f_s, from the cross-spectrum phase (-phase / 2 pi f_s)
  A_he, A_lb RMS of the vertical acceleration of each site in the step band 0.6-3 Hz (m/s2): the signal budget
Groups: all segments, and segments without a large error at either site with the published estimator and with AGS
(both |e_C| <= 5 steps/min), by cohort; participant-level medians, participant bootstrap (2000).
Usage: python analysis/v19_transmission.py HEAD_PACK LB_PACK RESULTS_V11 EXT_ALL_CSV OUT_DIR
       (EXT_ALL_CSV: v18_ext_dev.csv and v18_ext_test.csv concatenated, used only to label large errors)"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from scipy.signal import csd, welch, coherence, butter, sosfiltfilt
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from headimu import dsp  # noqa: E402
from headimu.evaluate import windows  # noqa: E402
from headimu.io_voisard import Trial  # noqa: E402

# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v19_transmission.py HEAD_PACK LB_PACK RESULTS_V11 EXT_ALL_CSV OUT_DIR')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

hp, lp, r11, extp, out = sys.argv[1], sys.argv[2], Path(sys.argv[3]), sys.argv[4], Path(sys.argv[5])
out.mkdir(parents=True, exist_ok=True)
FS = 100.0; NPS = 256; KS = (0.5, 1.0, 2.0, 3.0)
cfg = json.loads((r11 / "config_used.json").read_text(encoding="utf-8"))
qc = pd.read_csv(r11 / "qc_trials.csv"); setof = dict(zip(qc["trial"], qc["set"]))
zh = np.load(hp); zl = np.load(lp)
meta = {m["trial"]: m for m in json.loads(str(zh["__meta__"]))}
trials = [t for t in meta if setof.get(t) in ("dev", "test") and f"{t}|acc" in zl][:int(os.environ.get("NMAX", 10 ** 9))]
sos = butter(3, [0.6, 3.0], btype="band", fs=FS, output="sos")


def vert(acc):
    acc = acc.copy()
    bad = ~np.isfinite(acc).all(axis=1)
    if bad.any():
        idx = np.arange(len(acc))
        for k in range(3):
            acc[bad, k] = np.interp(idx[bad], idx[~bad], acc[~bad, k])
    g = dsp.gravity_dir(acc, FS, 0.3)
    return np.einsum("ij,ij->i", acc, g)


def at(f, y, f0):
    return float(np.interp(f0, f, y)) if f[0] <= f0 <= f[-1] else np.nan


rows, t0 = [], time.time()
for n, t in enumerate(trials):
    m = meta[t]
    hsl, hsr, turn = zh[f"{t}|ref_hs_left"], zh[f"{t}|ref_hs_right"], zh[f"{t}|ref_turn"]
    tr = Trial(t, m["participant"], m["cohort"], str(m["visit"]), m["sensor_type"], m["age"], None, FS, {}, hsl, hsr,
               tuple(turn), {}, [])
    w = windows(tr, FS, cfg["detect"]["window_pad_s"])
    if w is None:
        continue
    vh, vl = vert(zh[f"{t}|acc"].astype(float)), vert(zl[f"{t}|acc"].astype(float))
    n_ = min(len(vh), len(vl)); vh, vl = vh[:n_], vl[:n_]
    bh, bl = sosfiltfilt(sos, vh), sosfiltfilt(sos, vl)
    for sname, (a, b) in w["segs"].items():
        r = tr.hs[(tr.hs >= a) & (tr.hs <= b)]
        i, j = int(a * FS), min(n_, int(b * FS))
        if len(r) < 4 or j - i < NPS:
            continue
        fs_ = 1.0 / np.median(np.diff(r))
        x, y = vl[i:j] - vl[i:j].mean(), vh[i:j] - vh[i:j].mean()
        f, Sll = welch(x, FS, nperseg=NPS); _, Slh = csd(x, y, FS, nperseg=NPS); _, C = coherence(x, y, FS, nperseg=NPS)
        H = Slh / Sll
        row = {"trial": t, "participant": m["participant"], "cohort": m["cohort"], "set": setof[t], "segment": sname,
               "f_step": fs_, "cadence": 60 * fs_,
               "A_he": float(np.sqrt(np.mean(bh[i:j] ** 2))), "A_lb": float(np.sqrt(np.mean(bl[i:j] ** 2)))}
        for k in KS:
            row[f"G_{k}"] = at(f, np.abs(H), k * fs_); row[f"C_{k}"] = at(f, C, k * fs_)
        ph = float(np.angle(np.interp(fs_, f, H.real) + 1j * np.interp(fs_, f, H.imag)))
        row["delay_ms"] = -1000 * ph / (2 * np.pi * fs_)
        rows.append(row)
    if n % 200 == 0:
        print(f"{n}/{len(trials)} {time.time() - t0:.0f}s", flush=True)
D = pd.DataFrame(rows)
E = pd.read_csv(extp)
E = E[E["loc"].isin(["HE", "LB"])]
lab = E.assign(bp=(E.C_peak - E.R_step).abs() > 5, ba=(E.C_ags - E.R_step).abs() > 5).pivot_table(
    index=["trial", "segment"], columns="loc", values=["bp", "ba"], aggfunc="max")
lab.columns = [f"{a}_{b}" for a, b in lab.columns]
D = D.merge(lab.reset_index(), on=["trial", "segment"], how="left")
D["clean"] = ~(D[["bp_HE", "bp_LB", "ba_HE", "ba_LB"]].fillna(True).astype(bool).any(axis=1))
D.to_csv(out / "v19_transmission_segments.csv", index=False)

rng = np.random.default_rng(20261115)
MEAS = [f"G_{k}" for k in KS] + [f"C_{k}" for k in KS] + ["delay_ms", "A_he", "A_lb"]


def pboot(d, col, B=2000):
    pm = d.groupby("participant")[col].median().dropna()
    if len(pm) < 3:
        return [float(pm.median()) if len(pm) else np.nan, np.nan, np.nan]
    v = pm.to_numpy(); bs = [np.median(rng.choice(v, len(v))) for _ in range(B)]
    return [float(np.median(v)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


R = {"n_segments": int(len(D)), "n_clean": int(D.clean.sum()), "n_participants": int(D.participant.nunique())}
for grp, d in (("all", D), ("clean", D[D.clean])):
    R[grp] = {"All": {c: pboot(d, c) for c in MEAS}}
    for coh, g in d.groupby("cohort"):
        R[grp][coh] = {c: pboot(g, c) for c in MEAS}
        R[grp][coh]["n_part"] = int(g.participant.nunique()); R[grp][coh]["n_seg"] = int(len(g))
c = D[D.clean]
R["clean_spearman_vs_cadence"] = {k: float(c[[k, "cadence"]].corr("spearman").iloc[0, 1]) for k in ("G_1.0", "A_he", "C_1.0")}
# head versus trunk in large-error segments (published estimator), descriptive
for nm, msk in (("head_only", D.bp_HE.fillna(False).astype(bool) & ~D.bp_LB.fillna(False).astype(bool)),
                ("lb_only", ~D.bp_HE.fillna(False).astype(bool) & D.bp_LB.fillna(False).astype(bool)),
                ("both", D.bp_HE.fillna(False).astype(bool) & D.bp_LB.fillna(False).astype(bool))):
    R[nm] = {k: pboot(D[msk], k) for k in ("G_1.0", "C_1.0", "delay_ms", "A_he", "A_lb")}
    R[nm]["n_seg"] = int(msk.sum())
(out / "v19_transmission.json").write_text(json.dumps(R, indent=1))
f2 = lambda v: f"{v[0]:.2f} [{v[1]:.2f}, {v[2]:.2f}]"
for grp in ("clean",):
    for coh, d in R[grp].items():
        print(grp, coh, {k: f2(v) for k, v in d.items() if isinstance(v, list) and k in ("G_0.5", "G_1.0", "G_2.0", "G_3.0", "C_1.0", "delay_ms", "A_he", "A_lb")})
print({k: R[k] for k in ("n_segments", "n_clean", "n_participants", "clean_spearman_vs_cadence")})
for nm in ("head_only", "lb_only", "both"):
    print(nm, {k: (f2(v) if isinstance(v, list) else v) for k, v in R[nm].items()})
