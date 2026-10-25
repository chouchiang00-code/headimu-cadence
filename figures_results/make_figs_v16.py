"""V16 result figures (single column 3.5 in, same style as V15 figures).
fig10_endtoend : (a) cadence error or no output by cohort for B0/B1/B2; (b) B2 running-cadence latency components
fig11_trust    : (a) error-coverage curves Q1 vs Q2 variants vs random vs oracle; (b) reliability diagram; (c) false
                 exclusion and detection by VGA
Usage: python make_figs_v16.py E2E_DIR TRUST_DIR OUT_DIR RESULTS_V11
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

E2E, TR, OUT = map(Path, sys.argv[1:4])
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": ["TeX Gyre Heros", "DejaVu Sans"], "mathtext.fontset": "stixsans", "font.size": 7,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5,
                     "ytick.major.size": 2.5, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "savefig.bbox": "tight", "savefig.pad_inches": 0.02})
NAVY, RED, SKY, GREY, GOLD, INK = "#1f3b63", "#b03a2e", "#5b8cc0", "#8a9099", "#c98a1b", "#1a1a1a"
COH = ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]


def plabel(ax, s, x=-0.16, y=1.04):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=7.5, fontweight="bold", va="bottom")


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=400)
    plt.close(fig)


# ----------------------------------------------------------------------------- fig10
seg = pd.read_csv(E2E / "endtoend_segments.csv")
seg = seg[(seg["set"] == "test") & np.isfinite(seg["C_ref"])]
fig = plt.figure(figsize=(3.5, 2.7))
gs = fig.add_gridspec(2, 1, height_ratios=[1.25, 1], hspace=0.62)
ax = fig.add_subplot(gs[0])
x = np.arange(len(COH))
cols = {"B0": NAVY, "B1": SKY, "B2": GOLD}
lab = {"B0": "B0 reference-assisted", "B1": "B1 head-only offline", "B2": "B2 head-only causal"}
for j, k in enumerate(("B0", "B1", "B2")):
    big, miss = [], []
    for c in COH:
        g = seg[seg["cohort"] == c]
        e = g[f"{k}_e"]
        miss.append(100 * (~np.isfinite(e)).mean())
        big.append(100 * (np.isfinite(e) & (e.abs() > 5)).mean())
    xx = x + (j - 1) * 0.27
    ax.bar(xx, big, 0.25, color=cols[k], label=lab[k], lw=0)
    ax.bar(xx, miss, 0.25, bottom=big, color="white", edgecolor=cols[k], hatch="/////", lw=0.5)
ax.set_xticks(x, COH)
ax.set_ylabel("Segments (%)")
ax.set_title(r"|$e_C$| > 5 steps/min (solid) or no output (hatched)", fontsize=6.6, loc="left", pad=3)
ax.set_ylim(0, 56)
ax.legend(fontsize=5.4, ncol=3, loc="upper left", bbox_to_anchor=(0, 1.0), handlelength=1.2, columnspacing=0.8)
plabel(ax, "(a)")
ax2 = fig.add_subplot(gs[1])
tri = pd.read_csv(E2E / "endtoend_trials.csv")
tri = tri[tri["set"] == "test"]
items = [("B2_confirm_latency", "Step confirmation"), ("B2_turn_on_delay", "Turn onset"),
         ("B2_walk_on_delay", "Walking onset"), ("B2_first_output_delay", "First cadence output")]
data = [tri[c].dropna().to_numpy() for c, _ in items]
bp = ax2.boxplot(data, orientation="horizontal", widths=0.5, showfliers=False, patch_artist=True,
                 medianprops=dict(color=RED, lw=1.0), boxprops=dict(facecolor="#eef3fa", edgecolor=NAVY, lw=0.6),
                 whiskerprops=dict(color=NAVY, lw=0.6), capprops=dict(color=NAVY, lw=0.6))
ax2.set_yticks(range(1, len(items) + 1), [l for _, l in items])
ax2.axvline(0, color=GREY, lw=0.5, ls=":")
ax2.set_xlabel("Delay after the reference event (s)")
ax2.set_title("B2 causal latencies (trials)", fontsize=6.6, loc="left", pad=3)
plabel(ax2, "(b)", x=-0.36)
save(fig, "fig10_endtoend")

# ----------------------------------------------------------------------------- fig11
cur = pd.read_csv(TR / "error_coverage_curve.csv")
S = json.loads((TR / "trust_summary.json").read_text())
test = pd.read_csv(TR / "trust_test_scored.csv")
gat = pd.read_csv(Path(sys.argv[4]) / "test_gating.csv")
fig = plt.figure(figsize=(3.5, 3.3))
gs = fig.add_gridspec(2, 2, hspace=0.72, wspace=0.5)
# (a) turn gate: recall gain over random removal vs fraction of time kept
ax = fig.add_subplot(gs[0, 0])
rng = np.random.default_rng(9)
thrs = sorted(gat["threshold_dps"].unique()); cov, e = [], []
for th in thrs:
    g = gat[gat["threshold_dps"] == th]
    cov.append(g.groupby("participant")["A2_time_coverage"].mean().mean())
    x = (g["A2_accepted_recall"] - g["A2R_accepted_recall"]).groupby(g["participant"]).mean().dropna().to_numpy()
    bs = x[rng.integers(0, len(x), (2000, len(x)))].mean(1)
    e.append((100 * x.mean(), *(100 * np.percentile(bs, [2.5, 97.5]))))
e = np.array(e)
ax.axhline(0, color=GREY, lw=0.6, ls=":")
ax.fill_between(cov, e[:, 1], e[:, 2], color=NAVY, alpha=0.15, lw=0)
ax.plot(cov, e[:, 0], "-o", color=NAVY, ms=2.6, mec="white", mew=0.4)
for c, hi, t in zip(cov, e[:, 2], thrs):
    if t in (20, 30, 90):
        ax.annotate(f"{t:.0f}°/s", (c, hi), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=5.0, color=NAVY)
ax.set_xlim(0.74, 0.96); ax.set_ylim(0, 8.5); ax.set_xticks([0.75, 0.85, 0.95])
ax.set_xlabel("Fraction of time kept"); ax.set_ylabel("Recall gain (pp)")
ax.set_title("Turn gate vs random", fontsize=6.4, loc="left", pad=3)
plabel(ax, "(a)", x=-0.32)
# (b) error-coverage
ax = fig.add_subplot(gs[0, 1])
sty = {"Q1_score": (NAVY, "-", "SR (Q1)"), "Q2c_SR_plus_2": (GOLD, "-", "SR+2"), "Q2d_full": (RED, "--", "Full"),
       "oracle": (GREY, ":", "Oracle")}
for m, (c, ls, l) in sty.items():
    d = cur[cur["method"] == m]
    ax.plot(d["coverage"], d["big_pct"], ls, color=c, lw=0.9, label=l)
base = 100 * test["big"].mean()
ax.axhline(base, color=GREY, lw=0.6, ls=(0, (1, 2)))
ax.text(0.72, base + 0.3, "random removal", fontsize=5.0, color=GREY, ha="left")
ax.set_xlim(1.0, 0.6); ax.set_ylim(0, 10)
ax.set_xlabel("Fraction of segments kept"); ax.set_ylabel("Large errors kept (%)")
ax.legend(fontsize=5.0, loc="center right", handlelength=1.4, borderaxespad=0.1)
ax.set_title("Error-coverage", fontsize=6.4, loc="left", pad=3)
plabel(ax, "(b)", x=-0.32)
# (c) reliability
ax = fig.add_subplot(gs[1, 0])
for r in S["discrimination"]:
    if r["method"] in ("Q2a_SR_trial", "Q2c_SR_plus_2"):
        rel = pd.DataFrame(r["reliability"])
        c = NAVY if r["method"] == "Q2a_SR_trial" else GOLD
        ax.plot(rel["pred"], rel["obs"], "o-", color=c, ms=2.4, lw=0.8, label="SR (logistic)" if c == NAVY else "SR+2")
ax.plot([0, 0.8], [0, 0.8], ":", color=GREY, lw=0.6)
ax.set_xlim(0, 0.8); ax.set_ylim(0, 0.8); ax.set_xticks([0, 0.4, 0.8]); ax.set_yticks([0, 0.4, 0.8])
ax.set_xlabel("Predicted risk (dev-fitted)"); ax.set_ylabel("Observed share")
ax.legend(fontsize=5.0, loc="upper left", handlelength=1.4)
ax.set_title("Calibration (test)", fontsize=6.4, loc="left", pad=3)
plabel(ax, "(c)", x=-0.32)
# (d) by VGA: retained and false exclusion
ax = fig.add_subplot(gs[1, 1])
ops = pd.read_csv(TR / "trust_operating_points.csv")
v = ops[ops["by"] == "vga_lvl"]
for m, c, l in (("Q1", NAVY, "SR (Q1)"), ("Q2c_SR_plus_2", GOLD, "SR+2")):
    d = v[v["method"] == m].sort_values("group")
    ax.plot(d["group"], 100 - d["retained_pct"], "o-", color=c, ms=2.4, lw=0.8, label=f"{l}: excluded")
    ax.plot(d["group"], d["false_exclusion_pct"], "s--", color=c, ms=2.2, lw=0.7, label=f"{l}: falsely excl.")
ax.set_xticks([0, 1, 2, 3], ["0", "1", "2", "≥3"]); ax.set_ylim(0, 35)
ax.set_xlabel("Clinician-rated VGA"); ax.set_ylabel("Segments (%)")
ax.legend(fontsize=4.6, loc="upper left", handlelength=1.6, borderaxespad=0.1)
ax.set_title("Who is excluded", fontsize=6.4, loc="left", pad=3)
plabel(ax, "(d)", x=-0.32)
save(fig, "fig11_trust")
print("ok")

# ----------------------------------------------------------------------------- figS_ext (external Bland-Altman, B1)
EXT = Path(sys.argv[5]) if len(sys.argv) > 5 else None
if EXT is not None:
    S = pd.read_csv(EXT / "external_passes.csv")
    fig, axs = plt.subplots(1, 2, figsize=(5.2, 2.0), sharey=True)
    cols = {"OG_st_control": NAVY, "OG_dt_control": SKY, "OG_st_fatigue": RED, "OG_dt_fatigue": GOLD}
    names = {"OG_st_control": "single task, control", "OG_dt_control": "dual task, control",
             "OG_st_fatigue": "single task, fatigue", "OG_dt_fatigue": "dual task, fatigue"}
    st = json.loads((EXT / "external_stats.json").read_text())
    for ax, k, lab in ((axs[0], "B1", "(a) B1 head-only offline"), (axs[1], "B2", "(b) B2 head-only causal")):
        for c, g in S.groupby("cond"):
            m = (g[f"{k}_C"] + g["C_ref"]) / 2
            ax.scatter(m, g[f"{k}_e"], s=3, color=cols[c], alpha=0.6, lw=0, label=names[c])
        ba = st["all"][k]["ba"]
        ax.axhline(ba["bias"], color=INK, lw=0.8)
        for v in (ba["loa_lo"], ba["loa_hi"]):
            ax.axhline(v, color=INK, lw=0.6, ls="--")
        ax.set_ylim(-6, 6); ax.set_xlabel("Mean of head and reference cadence (steps/min)")
        ax.set_title(lab, fontsize=6.6, loc="left", pad=3)
    axs[0].set_ylabel("Head − reference (steps/min)")
    axs[1].legend(fontsize=5.2, markerscale=2.5, loc="lower right", handletextpad=0.2)
    save(fig, "figS_external_ba")
    print("ok ext")
