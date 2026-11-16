"""V17 main-text result figures (single column, 3.45 in), one colour code throughout:
head = blue, lower back = orange; screening = teal; random removal / references = grey; the two cohorts with most large
errors (CVA, RIL) are the only cohorts given their own colours.

fig2_ba_v17       Bland-Altman, head A1 vs lower-back A1 (B0, test), same axes; points beyond the axis drawn as
                  triangles at the edge.
fig3_cohort_v17   (a) median |e_C| per cohort, head and lower back, with the trivial-baseline level; (b) paired
                  head - lower-back difference with 95% CI; (c) segments with |e_C| > 5: head only / both / LB only.
fig4_screen_v17   (a) large errors kept vs fraction of segments kept: SR, random removal, oracle; (b) share of all
                  segments excluded and share of segments without a large error excluded, by VGA. 95% CIs from
                  analysis/v17_fig_cis.py (participant bootstrap).
fig5_failure_v17  (a) share of large errors by head step regularity (SR) bins, head and lower back, with 95% CIs;
                  (b) head vs lower-back |e_C| per segment; (c, d) head A1 signal of a regular and an irregular
                  segment (analysis/v17_fig_examples.py).
Usage: python figures_results/make_figs_v17.py RESULTS_V11 TRUST_DIR V17_DIR OUT_DIR
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from headimu import stats  # noqa: E402

R11, TR, V17, OUT = map(Path, sys.argv[1:5])
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": ["TeX Gyre Heros", "DejaVu Sans"], "mathtext.fontset": "stixsans", "font.size": 7,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5,
                     "ytick.major.size": 2.5, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
                     "svg.fonttype": "none", "pdf.fonttype": 42})
HEAD, LB, TEAL, GREY, LIGHT, INK = "#2a6fb0", "#c0661c", "#007367", "#8a9099", "#c9cdd3", "#1a1a1a"
CVA, RIL = "#b4232a", "#6f4a9e"
ORDER = ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]


def plabel(ax, s, x=-0.2, y=1.03):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=7.5, fontweight="bold", va="bottom")


def save(fig, name):
    for ext in ("pdf", "svg"):
        fig.savefig(OUT / f"{name}.{ext}")
    fig.savefig(OUT / f"{name}.png", dpi=600)
    plt.close(fig)


seg = pd.read_csv(R11 / "test_segments.csv")
a1 = seg[(seg["method"] == "A1") & np.isfinite(seg["e_C"])]
he, lb = a1[a1["loc"] == "HE"], a1[a1["loc"] == "LB"]

# ----------------------------------------------------------------------------- fig2: Bland-Altman
fig, axs = plt.subplots(1, 2, figsize=(3.45, 1.95), sharey=True, gridspec_kw={"wspace": 0.12})
YL = 25
for ax, d, name, col, lab in ((axs[0], he, "Head A1", HEAD, "(a)"), (axs[1], lb, "Lower back A1", LB, "(b)")):
    ba = stats.bland_altman_repeated(d, "C_imu", "C_ref")
    x = (d["C_imu"] + d["C_ref"]) / 2
    y = d["C_imu"] - d["C_ref"]
    ax.axhspan(ba["loa_lo"], ba["loa_hi"], color=col, alpha=0.08, lw=0)
    for c_, z, mk in ((None, 1, "o"),):
        pass
    oth = ~d["cohort"].isin(["CVA", "RIL"])
    inr = y.abs() <= YL
    ax.scatter(x[oth & inr], y[oth & inr], s=2.2, color=LIGHT, lw=0, zorder=1, label="other cohorts")
    for coh, cc in (("RIL", RIL), ("CVA", CVA)):
        m = (d["cohort"] == coh) & inr
        ax.scatter(x[m], y[m], s=2.6, color=cc, lw=0, zorder=2, label=coh)
    for sign in (1, -1):
        m = (sign * y) > YL
        cols = np.where(d["cohort"][m] == "CVA", CVA, np.where(d["cohort"][m] == "RIL", RIL, "#9aa1aa"))
        ax.scatter(x[m], np.full(m.sum(), sign * (YL - 0.6)), s=7, marker="^" if sign > 0 else "v", c=cols, lw=0, zorder=3)
    ax.axhline(ba["bias"], color=INK, lw=0.8)
    for v in (ba["loa_lo"], ba["loa_hi"]):
        ax.axhline(v, color=col, lw=0.7, ls="--")
    n_off = int((y.abs() > YL).sum())
    ax.text(0.98, 0.80, f"bias {ba['bias']:+.2f}\nLoA {ba['loa_lo']:.1f} to {ba['loa_hi']:+.1f}", transform=ax.transAxes,
            fontsize=5.4, va="top", ha="right", bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
    ax.text(0.98, 0.14, f"{n_off} beyond ±{YL}\n(triangles)", transform=ax.transAxes, fontsize=5.0, ha="right", color=GREY)
    ax.set_ylim(-YL - 1, YL + 1); ax.set_xlim(55, 160)
    ax.set_title(f"{lab} {name}", fontsize=6.8, loc="left", pad=2, color=col, fontweight="bold")
    ax.set_xlabel("Mean cadence (steps/min)")
axs[0].set_ylabel("IMU − reference (steps/min)")
h, l = axs[0].get_legend_handles_labels()
fig.legend(h[::-1], l[::-1], loc="lower center", ncol=3, fontsize=5.6, bbox_to_anchor=(0.55, 0.93), markerscale=2.5,
           handletextpad=0.2, columnspacing=1.0)
save(fig, "fig2_ba_v17")

# ----------------------------------------------------------------------------- supplement: BA for four signals
fig, axs = plt.subplots(2, 2, figsize=(5.0, 3.5), sharex=True, sharey=True, gridspec_kw={"wspace": 0.08, "hspace": 0.32})
for ax, (loc, meth, col, lab) in zip(axs.flat, (("HE", "A1", HEAD, "(a) Head A1"), ("HE", "A0g", HEAD, "(b) Head A0g"),
                                               ("HE", "AC", HEAD, "(c) Head AC"), ("LB", "A1", LB, "(d) Lower back A1"))):
    d = seg[(seg["method"] == meth) & (seg["loc"] == loc) & np.isfinite(seg["e_C"])]
    ba = stats.bland_altman_repeated(d, "C_imu", "C_ref")
    x = (d["C_imu"] + d["C_ref"]) / 2; y = d["C_imu"] - d["C_ref"]
    ax.axhspan(ba["loa_lo"], ba["loa_hi"], color=col, alpha=0.08, lw=0)
    inr = y.abs() <= YL; oth = ~d["cohort"].isin(["CVA", "RIL"])
    ax.scatter(x[oth & inr], y[oth & inr], s=2.2, color=LIGHT, lw=0, label="other cohorts")
    for coh, cc in (("RIL", RIL), ("CVA", CVA)):
        m = (d["cohort"] == coh) & inr
        ax.scatter(x[m], y[m], s=2.6, color=cc, lw=0, label=coh)
    for sign in (1, -1):
        m = (sign * y) > YL
        cols = np.where(d["cohort"][m] == "CVA", CVA, np.where(d["cohort"][m] == "RIL", RIL, "#9aa1aa"))
        ax.scatter(x[m], np.full(m.sum(), sign * (YL - 0.6)), s=7, marker="^" if sign > 0 else "v", c=cols, lw=0)
    ax.axhline(ba["bias"], color=INK, lw=0.8)
    for v_ in (ba["loa_lo"], ba["loa_hi"]):
        ax.axhline(v_, color=col, lw=0.7, ls="--")
    ax.text(0.98, 0.80, f"n = {len(d)}\nbias {ba['bias']:+.2f}\nLoA {ba['loa_lo']:.1f} to {ba['loa_hi']:+.1f}",
            transform=ax.transAxes, fontsize=5.4, va="top", ha="right", bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
    ax.text(0.98, 0.10, f"{int((y.abs() > YL).sum())} beyond ±{YL}", transform=ax.transAxes, fontsize=5.0, ha="right", color=GREY)
    ax.set_ylim(-YL - 1, YL + 1); ax.set_xlim(55, 160)
    ax.set_title(lab, fontsize=6.8, loc="left", pad=2, color=col, fontweight="bold")
for ax in axs[1]:
    ax.set_xlabel("Mean cadence (steps/min)")
for ax in axs[:, 0]:
    ax.set_ylabel("IMU − reference (steps/min)")
h, l = axs[0, 0].get_legend_handles_labels()
fig.legend(h[::-1], l[::-1], loc="lower center", ncol=3, fontsize=5.8, bbox_to_anchor=(0.5, 0.93), markerscale=2.5)
save(fig, "figS_ba4_v17")

# ----------------------------------------------------------------------------- fig3: cohorts (double column)
C = {r["cohort"]: r for r in json.loads((V17 / "cohort_head_vs_lb.json").read_text())}
REV = json.loads((V17 / "rev" / "reviewer_checks.json").read_text())
CI = json.loads((V17 / "fig_cis.json").read_text())
EX = np.load(V17 / "fig_examples.npz")
fig = plt.figure(figsize=(7.0, 2.35))
gs = fig.add_gridspec(1, 3, width_ratios=[1.3, 0.95, 1.25], wspace=0.10)
rows = ORDER + ["All"]
ypos = {}
yy = 0.0
for c in rows[::-1]:
    ypos[c] = yy
    yy += 1.0 + (0.6 if c in ("All", "CVA", "HOA") else 0.0)   # gaps: All | neuro | ortho | healthy
lab = {c: f"{c} ({C[c]['n_participants']})" for c in rows}
grp = {"HS": "healthy", "HOA": "orthopaedic", "CVA": "neurological"}
XMAX = 4.6
ax = fig.add_subplot(gs[0])
for k, (pre, col, off) in enumerate((("head", HEAD, 0.17), ("lb", LB, -0.17))):
    for c in rows:
        r = C[c]; y = ypos[c] + off
        lo, hi, md = r[f"{pre}_lo"], r[f"{pre}_hi"], r[f"{pre}_median"]
        ax.plot([lo, min(hi, XMAX)], [y, y], color=col, lw=1.1, solid_capstyle="butt")
        ax.plot(md, y, "o", color=col, ms=3.3, mec="white", mew=0.3, label=("Head" if pre == "head" else "Lower back") if c == "HS" else None)
        if hi > XMAX:
            ax.annotate("", xy=(XMAX + 0.12, y), xytext=(XMAX - 0.05, y), arrowprops=dict(arrowstyle="-|>", color=col, lw=0.8, mutation_scale=5))
            ax.text(XMAX + 0.15, y, f"{hi:.1f}", fontsize=5.4, va="center", color=col)
ax.set_yticks([ypos[c] for c in rows]); ax.set_yticklabels([lab[c] for c in rows], fontsize=6.4)
for c, g_ in grp.items():
    top = {"HS": ypos["HS"], "HOA": ypos["HOA"], "CVA": ypos["CVA"]}[c]
    ax.text(-0.02, top + 0.62, g_, transform=ax.get_yaxis_transform(), fontsize=5.4, color=GREY, ha="right", va="center",
            style="italic")
ax.set_xlim(0, XMAX + 0.65); ax.set_xticks([0, 1, 2, 3, 4])
ax.set_xlabel("Median |$e_C$| [95% CI] (steps/min)")
base = REV["R2"]["All"]["baseline_cohort_median"]["median"]
ax.text(XMAX + 0.6, ypos["All"], f"no-signal baseline {base:.1f} →", fontsize=5.4, color=GREY, ha="right", va="center")
ax.legend(fontsize=6, loc="lower right", handletextpad=0.2, borderaxespad=0.0, bbox_to_anchor=(1.0, 0.13))
ax.set_title("(a) Typical error", fontsize=7.2, loc="left", pad=4, fontweight="bold")
ax2 = fig.add_subplot(gs[1], sharey=ax)
ax2.axvline(0, color=GREY, lw=0.6)
for c in rows:
    r = C[c]; y = ypos[c]
    ax2.plot([r["diff_lo"], r["diff_hi"]], [y, y], color=INK, lw=1.1)
    ax2.plot(r["diff_median"], y, "D", color=INK, ms=2.8)
    ax2.text(1.72, y, f"{max(abs(r['diff_lo']), abs(r['diff_hi'])):.2f}", fontsize=5.6, va="center", ha="right", color=GREY,
             clip_on=False)
ax2.text(1.72, ypos["HS"] + 0.45, "largest difference\nnot excluded", fontsize=5.2, va="bottom", ha="right", color=GREY, clip_on=False)
ax2.set_xlim(-0.8, 1.75); ax2.set_xticks([-0.5, 0, 0.5, 1])
ax2.tick_params(axis="y", left=False, labelleft=False); ax2.spines["left"].set_visible(False)
ax2.set_xlabel("Head − lower back (steps/min)")
ax.set_ylim(-0.6, ypos["HS"] + 1.35)
ax2.set_title("(b) Paired difference [95% CI]", fontsize=7.2, loc="left", pad=4, fontweight="bold")
ax3 = fig.add_subplot(gs[2], sharey=ax)
ys = np.array([ypos[c] for c in rows])
ho = np.array([100 * C[c]["big_head_only_n"] / C[c]["n_segments"] for c in rows])
bo = np.array([100 * C[c]["big_both_n"] / C[c]["n_segments"] for c in rows])
lo_ = np.array([100 * C[c]["big_lb_only_n"] / C[c]["n_segments"] for c in rows])
ax3.barh(ys, ho, 0.62, color=HEAD, label="head only")
ax3.barh(ys, bo, 0.62, left=ho, color="#7d8794", label="both")
ax3.barh(ys, lo_, 0.62, left=ho + bo, color=LB, label="lower back only")
for y, t_ in zip(ys, ho + bo + lo_):
    ax3.text(t_ + 0.8, y, f"{t_:.1f}", fontsize=5.4, va="center", color=GREY)
ax3.tick_params(axis="y", left=False, labelleft=False); ax3.spines["left"].set_visible(False)
ax3.set_xlim(0, 58); ax3.set_xlabel("Segments with |$e_C$| > 5 steps/min (%)")
ax3.legend(fontsize=6, loc="lower right", handlelength=1.0, handletextpad=0.3, borderaxespad=0.0, bbox_to_anchor=(1.0, 0.13))
ax3.set_title("(c) Large errors by location", fontsize=7.2, loc="left", pad=4, fontweight="bold")
save(fig, "fig3_cohort_v17")

# ----------------------------------------------------------------------------- fig4: screening
cur = pd.read_csv(TR / "error_coverage_curve.csv")
test = pd.read_csv(TR / "trust_test_scored.csv")
ops = pd.read_csv(TR / "trust_operating_points.csv")
fig, axs = plt.subplots(1, 2, figsize=(3.45, 1.75), gridspec_kw={"wspace": 0.5})
ax = axs[0]
base = 100 * test["big"].mean()
SC = CI["screen"]
rem = np.arange(0, 41)
lo_ = [SC[f"q1|{x}"][1] for x in rem]; hi_ = [SC[f"q1|{x}"][2] for x in rem]
ax.fill_between(rem, lo_, hi_, color=TEAL, alpha=0.16, lw=0)
d = cur[cur["method"] == "Q1_score"]
ax.plot(100 - 100 * d["coverage"], d["big_pct"], "-", color=TEAL, lw=1.1, label="SR screen")
ax.plot([0, 40], [base, base], ":", color=GREY, lw=0.9, label="random removal")
d = cur[cur["method"] == "oracle"]
ax.plot(100 - 100 * d["coverage"], d["big_pct"], "--", color="#a9b0b8", lw=0.9, label="ideal screen")
ax.set_xlim(0, 40); ax.set_ylim(0, 13)
ax.set_xlabel("Segments removed (%)"); ax.set_ylabel("Large errors among kept (%)")
ax.legend(fontsize=5.2, loc="upper right", handlelength=1.6, bbox_to_anchor=(1.0, 0.88))
plabel(ax, "(a)", x=-0.34)
ax = axs[1]
v = ops[(ops["by"] == "vga_lvl") & (ops["method"] == "Q1")].sort_values("group")
g = v["group"].astype(float).astype(int).to_numpy()
for key, dx, mk, mfc, ls, lab_ in (("excl", -0.08, "o", TEAL, "-", "all segments"),
                                  ("fex", 0.08, "s", "white", "--", "segments without\nlarge error")):
    est = np.array([SC[f"{key}|{int(k)}"][0] for k in g])
    lo = np.array([SC[f"{key}|{int(k)}"][1] for k in g]); hi = np.array([SC[f"{key}|{int(k)}"][2] for k in g])
    ax.errorbar(g + dx, est, yerr=[est - lo, hi - est], fmt=mk + ls, color=TEAL, mfc=mfc, ms=2.7, lw=0.9, elinewidth=0.6,
                capsize=1.2, capthick=0.6, label=lab_)
chk = np.array([SC[f"excl|{int(k)}"][0] for k in g]) - (100 - v["retained_pct"].to_numpy())
assert np.abs(chk).max() < 1e-6, chk
ax.set_xticks([0, 1, 2, 3], ["0", "1", "2", "≥3"]); ax.set_ylim(0, 56)
ax.set_xlabel("Clinician-rated VGA"); ax.set_ylabel("Excluded by SR (%)")
ax.legend(fontsize=5.0, loc="upper left", handlelength=1.8, title="share of", title_fontsize=5.0, alignment="left")
plabel(ax, "(b)", x=-0.34)
save(fig, "fig4_screen_v17")

# ----------------------------------------------------------------------------- fig5: failure
sr = test[["trial", "segment", "participant", "cohort", "sr_seg", "e_C"]].rename(columns={"e_C": "e_head"})
L = lb[["trial", "segment", "e_C"]].rename(columns={"e_C": "e_lb"})
J = sr.merge(L, on=["trial", "segment"])
J = J[np.isfinite(J["sr_seg"])]
edges = [-np.inf, 0.4, 0.6, 0.8, 0.9, np.inf]
labs = ["<0.4", "0.4–0.6", "0.6–0.8", "0.8–0.9", "≥0.9"]
J["bin"] = pd.cut(J["sr_seg"], edges, labels=labs, right=False)
G = J.groupby("bin", observed=False).agg(n=("e_head", "size"), h=("e_head", lambda s: 100 * (s.abs() > 5).mean()),
                                         l=("e_lb", lambda s: 100 * (s.abs() > 5).mean()))
fig = plt.figure(figsize=(3.45, 3.55))
go = fig.add_gridspec(2, 1, height_ratios=[1.0, 0.92], hspace=0.62)
gt = go[0].subgridspec(1, 2, width_ratios=[1.25, 1], wspace=0.42)
gb = go[1].subgridspec(2, 1, hspace=0.55)
axs = [fig.add_subplot(gt[0, 0]), fig.add_subplot(gt[0, 1])]
ax = axs[0]
xs = np.arange(len(labs))
FC = CI["fail"]
for w_, col, off, lab_ in (("head", HEAD, -0.19, "head"), ("lb", LB, 0.19, "lower back")):
    est = np.array([FC[f"{b}|{w_}"][0] for b in labs]); lo = np.array([FC[f"{b}|{w_}"][1] for b in labs])
    hi = np.array([FC[f"{b}|{w_}"][2] for b in labs])
    assert np.allclose(est, G["h" if w_ == "head" else "l"].to_numpy()), (est, G)
    ax.bar(xs + off, est, 0.36, color=col, label=lab_)
    ax.errorbar(xs + off, est, yerr=[est - lo, hi - est], fmt="none", ecolor=INK, elinewidth=0.5, capsize=1.0, capthick=0.5)
ax.set_xticks(xs, [f"{l_}\n{n}" for l_, n in zip(labs, G["n"])], fontsize=4.9); ax.set_ylim(0, 85)
ax.set_xlabel("Head step regularity (SR); segments", labelpad=3); ax.set_ylabel("|$e_C$| > 5 (%)")
ax.legend(fontsize=5.4, loc="upper right", handlelength=1.0)
plabel(ax, "(a)", x=-0.3)
ax = axs[1]
cap = 30
J = he[["trial", "segment", "cohort", "e_C"]].rename(columns={"e_C": "e_head"}).merge(
    lb[["trial", "segment", "e_C"]].rename(columns={"e_C": "e_lb"}), on=["trial", "segment"])   # all 1860 segments
xh, yl = J["e_head"].abs().clip(upper=cap), J["e_lb"].abs().clip(upper=cap)
oth = ~J["cohort"].isin(["CVA", "RIL"])
ax.scatter(xh[oth], yl[oth], s=2.2, color=LIGHT, lw=0, label="other")
for coh, cc in (("RIL", RIL), ("CVA", CVA)):
    m = J["cohort"] == coh
    ax.scatter(xh[m], yl[m], s=2.6, color=cc, lw=0, label=coh)
ax.axvline(5, color=GREY, lw=0.5, ls="--"); ax.axhline(5, color=GREY, lw=0.5, ls="--")
both = ((J["e_head"].abs() > 5) & (J["e_lb"].abs() > 5)).sum()
honly = ((J["e_head"].abs() > 5) & (J["e_lb"].abs() <= 5)).sum()
lonly = ((J["e_head"].abs() <= 5) & (J["e_lb"].abs() > 5)).sum()
ax.text(cap - 0.5, cap - 1, f"both {both}", fontsize=5, ha="right", va="top")
ax.text(cap - 0.5, 2.6, f"head only {honly}", fontsize=5, ha="right", va="center", color=HEAD,
        bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))
ax.text(5.8, cap - 1, f"LB only {lonly}", fontsize=5, ha="left", va="top", color=LB,
        bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))
ax.set_xlim(0, cap + 1); ax.set_ylim(0, cap + 1)
ax.set_xticks([0, 10, 20, 30], ["0", "10", "20", "≥30"]); ax.set_yticks([0, 10, 20, 30], ["0", "10", "20", "≥30"])
ax.set_xlabel("Head |$e_C$|"); ax.set_ylabel("Lower-back |$e_C$|")
ax.legend(fontsize=5.0, loc="lower left", markerscale=2.5, handletextpad=0.1, borderaxespad=0.0, bbox_to_anchor=(0.0, 1.0),
          ncol=3, columnspacing=0.6)
plabel(ax, "(b)", x=-0.34)
fe = lambda v: "0" if abs(v) < 0.5 else f"{v:+.0f}".replace("-", "−")
for k, row in enumerate((1, 2)):
    m = json.loads(str(EX[f"{k}_meta"]))
    ax = fig.add_subplot(gb[row - 1, 0])
    t_, x_ = EX[f"{k}_t"], EX[f"{k}_x"]
    ax.plot(t_, x_, color=HEAD, lw=0.6)
    ax.plot(EX[f"{k}_c"], EX[f"{k}_cx"], "o", ms=2.2, mfc=HEAD, mec="white", mew=0.3, zorder=3)
    XW = 8.0
    top = np.nanmax(np.abs(x_[t_ <= XW])) * 1.1
    for h_ in EX[f"{k}_hs"][EX[f"{k}_hs"] <= XW]:
        ax.plot([h_, h_], [top * 1.02, top * 1.32], color=INK, lw=0.6, clip_on=False)
    ax.set_xlim(0, XW); ax.set_ylim(-top, top * 1.35)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    name = {"HS": "healthy", "CVA": "stroke"}[m["cohort"]]
    ax.text(0.0, 1.06, f"({'cd'[k]}) {name}, SR {m['sr_seg']:.2f}", transform=ax.transAxes, fontsize=6.4, fontweight="bold",
            va="bottom")
    ax.text(1.0, 1.06, f"reference {m['C_ref']:.0f} steps/min; error head {fe(m['e_head'])}, lower back {fe(m['e_lb'])}",
            transform=ax.transAxes, fontsize=5.2, va="bottom", ha="right", color=GREY)
    if k == 1:
        ax.set_xlabel("Time from segment start (s)", labelpad=1)
    else:
        ax.tick_params(labelbottom=False)
from matplotlib.lines import Line2D
fig.legend(handles=[Line2D([], [], color=HEAD, lw=0.8, label="head A1 (band-passed)"),
                    Line2D([], [], ls="", marker="o", ms=3, mfc=HEAD, mec="white", label="detected step"),
                    Line2D([], [], ls="", marker="|", ms=5, mew=0.8, color=INK, label="reference heel strike")],
           loc="upper center", ncol=3, bbox_to_anchor=(0.5, 0.005), fontsize=5.4, handlelength=1.4, columnspacing=1.0)
save(fig, "fig5_failure_v17")
json.dump({"sr_bins": G.reset_index().astype({"bin": str}).to_dict("records"), "both": int(both), "head_only": int(honly),
           "lb_only": int(lonly), "n_segments_panel_b": int(len(J))}, open(OUT / "fig5_numbers.json", "w"), indent=1, default=float)
print("ok", G, both, honly, lonly)
