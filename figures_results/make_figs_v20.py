#!/usr/bin/env python3
"""V20 figure 5: share of head segments with |e_C| > 5 steps/min versus output data rate (simulation on recorded
signals, test set) for the step-median peak estimator, the stride-median peak estimator and AGS; top axis: step-median
quantisation step C^2 Delta / 60 at 105 steps/min. Usage: python figures_results/make_figs_v20.py SENSOR_REQ_JSON OUT_DIR"""
import json, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
SR = json.loads(Path(sys.argv[1]).read_text()); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": ["TeX Gyre Heros", "DejaVu Sans"], "mathtext.fontset": "stixsans", "font.size": 7,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5,
                     "ytick.major.size": 2.5, "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "svg.fonttype": "none", "pdf.fonttype": 42})
fig, ax = plt.subplots(figsize=(3.4, 2.2))
F = [100, 50, 25, 20]
for k, (est, col, mk, nm) in enumerate((("peak", "#8a9099", "s", "step median"), ("stride", "#c0661c", "^", "stride median"),
                                         ("AGS", "#007367", "o", "AGS (stride + autocorrelation)"))):
    v = [SR["reference|0" if f == 100 else f"fs|{f}"][est]["big_or_none"] for f in F]
    x = [i + (k - 1) * 0.07 for i in range(len(F))]
    ax.errorbar(x, [a[0] for a in v], yerr=[[a[0] - a[1] for a in v], [a[2] - a[0] for a in v]], fmt=mk + "-", color=col, ms=3,
                lw=0.9, elinewidth=0.6, capsize=1.5, label=nm)
ax.set_xticks(range(len(F)), [str(f) for f in F]); ax.set_xlabel("Output data rate (Hz)")
ax.set_ylabel("Head segments > 5 steps/min (%)"); ax.set_ylim(0, 22); ax.legend(fontsize=5.8, loc="upper left")
top = ax.secondary_xaxis("top"); top.set_xticks(range(len(F)), [f"{105 ** 2 / f / 60:.1f}" for f in F]); top.tick_params(labelsize=5.8)
top.set_xlabel("step-median quantisation step C²Δ/60 (steps/min)", fontsize=5.8)
for ext in ("png", "pdf", "svg"):
    fig.savefig(OUT / f"fig5_rate_v20.{ext}", dpi=600 if ext == "png" else None)
