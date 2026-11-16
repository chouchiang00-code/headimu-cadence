#!/usr/bin/env python3
"""V18 figure 6: (a) component ablation on the test set (head and lower back); (b) theory check of Proposition 1:
reference step-median vs stride cadence against left-right step ratio, with the bound C(1-rho)/(2 rho); (c) operating
envelope: AGS large-error share by step regularity (SR) of each sensor's own signal, rule SR >= 0.7 chosen on dev.
Usage: python figures_results/make_figs_v18b.py EXT_ROOT_DIR ANALYSIS_JSON OUT_DIR"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
EXT, AJ, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": ["TeX Gyre Heros", "DejaVu Sans"], "mathtext.fontset": "stixsans", "font.size": 7,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5,
                     "ytick.major.size": 2.5, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
                     "svg.fonttype": "none", "pdf.fonttype": 42})
HEAD, LB, TEAL, GREY, LIGHT, INK = "#2a6fb0", "#c0661c", "#007367", "#8a9099", "#c9cdd3", "#1a1a1a"
R = json.loads(AJ.read_text()); T = pd.read_csv(EXT / "v18_ext_test.csv"); T = T[T.C_peak.notna()]
fig = plt.figure(figsize=(7.0, 2.3)); gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1.0, 1.0], wspace=0.45)
# (a)
ax = fig.add_subplot(gs[0])
V = [("published", "published peak"), ("+guided", "+ guided spacing"), ("+stride", "+ stride median"),
     ("+guided+stride", "+ both"), ("AGS", "AGS (+ AC average)"), ("AC only", "autocorrelation only")]
for j, (loc, col, mk) in enumerate((("HE", HEAD, "o"), ("LB", LB, "s"))):
    for i, (k, lab) in enumerate(V):
        y = i + (j - 0.5) * 0.3
        x = R[loc]["test"]["ablation"][k]["big"]
        ci = R[loc]["test"]["ablation_ci"].get(k, {}).get("big")
        if ci:
            ax.plot([ci[1], ci[2]], [y, y], color=col, lw=0.8)
        ax.plot(x, y, mk, color=col, ms=3.2, mfc=col if k == "AGS" else "white", mew=0.8,
                label=("head" if loc == "HE" else "lower back") if i == 0 else None)
ax.set_yticks(range(len(V)), [l for _, l in V], fontsize=5.9); ax.invert_yaxis(); ax.set_xlim(0, 14)
ax.set_xlabel("Segments with |$e_C$| > 5 steps/min (%)"); ax.legend(fontsize=5.6, loc="lower right")
ax.set_title("(a) Ablation (test set)", fontsize=7.0, loc="left", pad=3, fontweight="bold")
# (b)
ax = fig.add_subplot(gs[1])
H = T[T["loc"] == "HE"]
d = (H.R_step - H.R_stride).abs()
ax.scatter(H.ref_ratio, d.clip(upper=19.5), s=2.0, color=GREY, alpha=0.5, lw=0)
rho = np.linspace(0.62, 1.0, 100); C = float(H.R_step.median())
ax.plot(rho, C * (1 - rho) / (2 * rho), color=INK, lw=1.0, label=f"strict alternation: C(1−ρ)/(2ρ), C = {C:.0f}")
ax.axhline(5, color=GREY, lw=0.6, ls=":")
ax.set_xlim(0.62, 1.0); ax.set_ylim(0, 20)
ax.set_xlabel("Reference step ratio ρ (short / long)"); ax.set_ylabel("|step-median − stride cadence| (steps/min)")
ax.legend(fontsize=5.6, loc="upper right")
ax.set_title("(b) Asymmetry and the step median", fontsize=7.0, loc="left", pad=3, fontweight="bold")
# (c)
ax = fig.add_subplot(gs[2])
edges = [0, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]; mids = [(edges[i] + edges[i + 1]) / 2 for i in range(len(edges) - 1)]
for loc, col, mk in (("HE", HEAD, "o"), ("LB", LB, "s")):
    X = T[T["loc"] == loc]; b = pd.cut(X.sr.fillna(0), edges, right=False)
    y = X.groupby(b, observed=False).apply(lambda g: 100 * ((g.C_ags - g.R_step).abs() > 5).mean() if len(g) else np.nan)
    ax.plot(mids, y.values, mk + "-", color=col, ms=2.8, lw=0.9, label="head" if loc == "HE" else "lower back")
ax.axvline(0.7, color=TEAL, lw=0.9, ls="--")
e = R["HE"]["envelope"]["test"]; e2 = R["LB"]["envelope"]["test"]
ax.text(0.72, 60, f"rule SR ≥ 0.7\n(dev-chosen)\nkept: head {e['coverage']:.0f}%,\nlower back {e2['coverage']:.0f}%\n"
        f"> 5 within: {e['big_in']:.1f}% / {e2['big_in']:.1f}%", fontsize=5.3, color=TEAL, va="top")
ax.set_xlabel("Step regularity SR of the same sensor"); ax.set_ylabel("AGS segments > 5 steps/min (%)")
ax.set_ylim(0, 85); ax.legend(fontsize=5.6, loc="upper left", bbox_to_anchor=(0.0, 1.0))
ax.set_title("(c) Operating envelope (test set)", fontsize=7.0, loc="left", pad=3, fontweight="bold")
for ext in ("pdf", "svg"):
    fig.savefig(OUT / f"fig6_mech_v18.{ext}")
fig.savefig(OUT / "fig6_mech_v18.png", dpi=600); print("ok")
