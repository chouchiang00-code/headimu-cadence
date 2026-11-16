#!/usr/bin/env python3
"""V18 figure: the AGS estimator.
(a) development-set example with left-right step asymmetry (KOA_6_1, S1): reference and head step intervals; the
    median single step interval falls between the short and the long step, the median stride does not;
(b) development-set large errors of the published estimator by failure type and the share AGS brings within 5 steps/min;
(c) test set: share of segments with |e_C| > 5 by cohort, published estimator vs AGS, head and lower back (95% CI).
Usage: python figures_results/make_figs_v18.py DEV_PKL V18_DIR OUT_DIR"""
import json, pickle, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis import v18_methods as M  # noqa: E402
from headimu.evaluate import _intervals  # noqa: E402
DEV, V18, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": ["TeX Gyre Heros", "DejaVu Sans"], "mathtext.fontset": "stixsans", "font.size": 7,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5,
                     "ytick.major.size": 2.5, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
                     "svg.fonttype": "none", "pdf.fonttype": 42})
HEAD, LB, TEAL, GREY, LIGHT, INK, GOLD = "#2a6fb0", "#c0661c", "#007367", "#8a9099", "#c9cdd3", "#1a1a1a", "#a87900"
ORDER = ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]


def plabel(ax, s, x=-0.2, y=1.03):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=7.5, fontweight="bold", va="bottom")


fig = plt.figure(figsize=(7.0, 2.3))
gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 0.9, 1.35], wspace=0.42)
# (a)
P = pickle.load(open(DEV, "rb")); cfg, cal = P["cfg"], P["cal"]; lag = cal["lags_s"]["HE_A1"]
d = [t for t in P["trials"] if t["trial"] == "KOA_6_1"][0]; fs = d["fs"]; x = d["A1"].astype(float); valid = d["valid"]
i0, i1 = max(0, int(d["full"][0] * fs)), min(len(valid), int(d["full"][1] * fs)); a, b = d["segs"]["S1"]
r = d["hs"][(d["hs"] >= a) & (d["hs"] <= b)]; ri = np.diff(r)
c = M.seg_peaks(M.base_peaks(x, fs, cfg, i0, i1, valid), lag, a, b); iv = _intervals(c + lag, valid, fs)
ax = fig.add_subplot(gs[0])
ax.plot(np.arange(len(ri)), ri, "x", color=INK, ms=3.2, mew=0.8, label="reference step")
ivp = np.minimum(iv, 1.09); off = iv > 1.09
ax.plot(np.arange(len(iv))[~off], ivp[~off], "o", color=HEAD, ms=2.8, mfc="none", mew=0.8, label="head step")
ax.plot(np.arange(len(iv))[off], ivp[off], "^", color=HEAD, ms=3.2, mfc="none", mew=0.8)
lines = [(np.median(ri), INK, "--", f"reference, median step: {60 / np.median(ri):.1f}"),
         (np.median(ri[:-1] + ri[1:]) / 2, INK, ":", f"reference, median stride: {M.stride_cadence(ri):.1f}"),
         (np.median(iv), HEAD, "--", f"head, median step: {60 / np.median(iv):.1f}"),
         (np.median(iv[:-1] + iv[1:]) / 2, HEAD, ":", f"head, median stride: {M.stride_cadence(iv):.1f}")]
for yv, col, ls, lab in lines:
    ax.axhline(yv, color=col, ls=ls, lw=0.8)
ax.set_ylim(0.4, 1.12); ax.set_xlabel("Step number"); ax.set_ylabel("Step interval (s)")
txt = "\n".join(l[3] for l in lines) + "  (steps/min)"
ax.text(0.02, 0.98, txt, transform=ax.transAxes, fontsize=5.0, va="top", color=INK, linespacing=1.25)
ax.legend(fontsize=5.4, loc="lower right", handletextpad=0.2, borderaxespad=0.1)
ax.set_title("(a) Step asymmetry (development set)", fontsize=7.0, loc="left", pad=3, fontweight="bold")
# (b)
DM = json.loads((V18 / "dev_mech.json").read_text())
types = [("extra peaks", "extra peaks"), ("missed peaks", "missed peaks"), ("events correct, interval statistic", "events correct,\nstep median jumps"),
         ("reference suspect", "reference\nsuspect")]
ax = fig.add_subplot(gs[1])
for k, (key, lab) in enumerate(types):
    n = DM["types"][key]; fx = DM["fixed_by_ags"][key] * n
    ax.barh(k, n, 0.62, color=LIGHT); ax.barh(k, fx, 0.62, color=TEAL)
    ax.text(n + 1.5, k, f"{fx:.0f}/{n}", va="center", fontsize=5.6, color=GREY)
ax.set_yticks(range(len(types)), [l for _, l in types], fontsize=5.8); ax.invert_yaxis()
ax.set_xlim(0, 70); ax.set_xlabel("Large errors, published estimator")
ax.text(0.98, 1.0, "teal: within 5 steps/min with AGS", transform=ax.transAxes, fontsize=5.2, ha="right", va="top", color=TEAL)
ax.set_title("(b) Failure types (development set)", fontsize=7.0, loc="left", pad=3, fontweight="bold")
# (c)
S = json.loads((V18 / "test_root" / "v18_stats.json").read_text())
ax = fig.add_subplot(gs[2])
rows = ORDER + ["All"]
for j, loc, col, mk in ((0, "HE", HEAD, "o"), (1, "LB", LB, "s")):
    for i, cco in enumerate(rows):
        src = S["primary"] if cco == "All" else S["by_cohort"][cco]
        y0 = i * 1.0 + (j - 0.5) * 0.34
        p0, p1 = src[f"{loc}|C_peak|big"][0], src[f"{loc}|C_ags|big"]
        ax.annotate("", xy=(p1[0], y0), xytext=(p0, y0), arrowprops=dict(arrowstyle="-|>", color=col, lw=0.8, mutation_scale=5))
        ax.plot(p0, y0, mk, color=col, mfc="white", ms=2.8, mew=0.7, label=(f"{'head' if loc == 'HE' else 'lower back'}: published → AGS") if i == 0 else None)
ax.set_yticks(range(len(rows)), rows, fontsize=5.8); ax.invert_yaxis()
ax.set_xlabel("Segments with |$e_C$| > 5 steps/min (%)"); ax.set_xlim(0, 40)
ax.legend(fontsize=5.4, loc="upper right", handletextpad=0.3)
ax.set_title("(c) Test set: published → AGS", fontsize=7.0, loc="left", pad=3, fontweight="bold")
for ext in ("pdf", "svg"):
    fig.savefig(OUT / f"fig6_ags_v18.{ext}")
fig.savefig(OUT / "fig6_ags_v18.png", dpi=600)
print("ok")
