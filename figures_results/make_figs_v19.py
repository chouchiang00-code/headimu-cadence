#!/usr/bin/env python3
"""V19 figure: the forehead as a sensing site (test set, B0 straight segments).
(a) head/trunk transmission in segments without a large error: step-band vertical-acceleration RMS ratio and
    step-band horizontal angular-rate RMS ratio, by cohort (participant-level medians, bootstrap 95% CI);
(b) signal budget: distribution of the head step-band vertical RMS, against the step-band RMS of the simulated white
    noise and of a consumer MEMS accelerometer (BMI270 data sheet, 160 ug/sqrt(Hz), normal mode);
(c) large errors versus output data rate for the published step-median peak estimator and AGS (simulation), with the
    step-median resolution C^2 Delta / 60 at 105 steps/min on the top axis.
Usage: python figures_results/make_figs_v19.py SENSOR_REQ_JSON TRANSMISSION_JSON HEAD_TRUNK_CSV EXT_TEST_CSV OUT_DIR"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
SR = json.loads(Path(sys.argv[1]).read_text()); TR = json.loads(Path(sys.argv[2]).read_text())
HT = pd.read_csv(sys.argv[3]); E = pd.read_csv(sys.argv[4]); OUT = Path(sys.argv[5]); OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": ["TeX Gyre Heros", "DejaVu Sans"], "mathtext.fontset": "stixsans", "font.size": 7,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5,
                     "ytick.major.size": 2.5, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
                     "svg.fonttype": "none", "pdf.fonttype": 42})
HEAD, TEAL, GREY, INK, ORNG = "#2a6fb0", "#007367", "#8a9099", "#1a1a1a", "#c0661c"
_T = []
fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.3), gridspec_kw={"width_ratios": [1.15, 1, 1.05], "wspace": 0.42})
# (a)
ax = axs[0]
CO = ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]
y = np.arange(len(CO))[::-1]
for k, (m, col, mk, nm) in enumerate((("tr_v", HEAD, "o", "vertical acceleration"), ("tilt_ratio", ORNG, "s", "horizontal rotation"))):
    v = np.array([TR["clean"][c][m] for c in CO])
    ax.errorbar(v[:, 0], y + (0.15 if k == 0 else -0.15), xerr=[v[:, 0] - v[:, 1], v[:, 2] - v[:, 0]], fmt=mk, color=col, ms=3,
                elinewidth=0.6, capsize=1.2, label=nm)
ax.axvline(1, color=GREY, lw=0.6, ls=":")
ax.set_yticks(y, CO); ax.set_xlabel("Head / lower back, step band (RMS ratio)"); ax.set_xlim(0.2, 1.9)
ax.legend(fontsize=5.6, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, handletextpad=0.2, columnspacing=0.8); _T.append((ax, "(a) Transmission to the head"))
# (b)
ax = axs[1]
lab = E[E.C_peak.notna()].assign(b=lambda d: ((d.C_peak - d.R_step).abs() > 5) | ((d.C_ags - d.R_step).abs() > 5))
bad = lab.groupby(["trial", "segment"]).b.max()
H = HT.set_index(["trial", "segment"]).join(bad.rename("bad"))
clean = H[H.bad == False].rms_v_he.dropna()  # noqa: E712
ax.hist(clean, bins=np.logspace(np.log10(0.2), np.log10(6), 30), color=HEAD, alpha=0.75)
ax.set_xscale("log"); ax.set_xlabel("Step-band vertical RMS (m/s²)"); ax.set_ylabel("Segments")
for val, ls, txt in ((TR["noise_bandrms"]["1.0"], "--", "σ = 1.0"),
                     (TR["noise_bandrms"]["0.2"], ":", "σ = 0.2"),
                     (160e-6 * 9.80665 * np.sqrt(2.4), "-.", "consumer MEMS\n(160 µg/√Hz)")):
    ax.axvline(val, color=INK, lw=0.7, ls=ls)
    ax.text(val * (1.12 if "MEMS" in txt else 0.9), ax.get_ylim()[1] * (0.95 if "MEMS" in txt else 0.75 if "1.0" in txt else 0.55), txt,
            fontsize=5.2, va="top", ha="left" if "MEMS" in txt else "right")
ax.set_xlim(0.0015, 8)
_T.append((ax, "(b) Signal budget"))
# (c)
ax = axs[2]
F = [100, 50, 25, 20]
for est, col, mk, nm in (("peak", GREY, "s", "published (step median)"), ("AGS", TEAL, "o", "AGS (stride + AC)")):
    v = [SR["reference|0" if f == 100 else f"fs|{f}"][est]["big_or_none"] for f in F]
    yy = [x[0] for x in v]
    ax.errorbar(range(len(F)), yy, yerr=[[x[0] - x[1] for x in v], [x[2] - x[0] for x in v]], fmt=mk + "-", color=col, ms=3,
                lw=0.9, elinewidth=0.6, capsize=1.5, label=nm)
ax.set_xticks(range(len(F)), [f"{f}" for f in F]); ax.set_xlabel("Output data rate (Hz)")
ax.set_ylabel("Head segments > 5 steps/min (%)"); ax.set_ylim(0, 22); ax.legend(fontsize=5.6, loc="upper left")
top = ax.secondary_xaxis("top"); top.set_xticks(range(len(F)), [f"{105 ** 2 / f / 60:.1f}" for f in F]); top.tick_params(labelsize=5.6)
top.set_xlabel("step-median resolution C²Δ/60", fontsize=5.8)
_T.append((ax, "(c) Sampling-rate requirement"))
fig.canvas.draw()
for a_, t_ in _T:
    bb = a_.get_position()
    fig.text(bb.x0 - 0.035, 1.0, t_, fontsize=7, fontweight="bold", ha="left", va="bottom")
for ext in ("png", "pdf", "svg"):
    fig.savefig(OUT / f"fig7_sensing_v19.{ext}", dpi=600 if ext == "png" else None)
print("saved", OUT, "clean n", len(clean))
