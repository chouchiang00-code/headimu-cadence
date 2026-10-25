"""Journal-style result figures (Figs. 4-9), single-column width (3.5 in).
Usage:  python make_result_figs.py <results_dir> <dataset_data_dir> <out_dir> [4 5 6 7 8 9]
  results_dir      : output folder of `run_pipeline.py run` (e.g. ..\\results_v11)
  dataset_data_dir : ...\\dataset_extracted\\dataset\\data (only needed for Fig. 4)"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from headimu import dsp, stats  # noqa: E402

RES, DATA, OUT = (Path(a) for a in sys.argv[1:4])
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": ["TeX Gyre Heros", "Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"], "mathtext.fontset": "stixsans", "font.size": 7,
    "axes.labelsize": 7, "axes.titlesize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
    "legend.fontsize": 6.2, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.direction": "out", "ytick.direction": "out",
    "lines.linewidth": 0.9, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "pdf.fonttype": 42})
INK, EDGE, GRID, FILL = "#1a1a1a", "#5b616b", "#d9dde2", "#eceef1"
NAVY, RED, SKY, GOLD = "#1f3b63", "#b03a2e", "#8fb3d9", "#d9822b"
COH = ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]
COH_COLORS = dict(zip(COH, ["#1f3b63", "#4c7fb8", "#8fb3d9", "#7a9e7e", "#b03a2e", "#d9822b", "#e3b23c", "#7d5a8c"]))
W1 = 3.5  # single-column width (in)


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=600)
    fig.savefig(OUT / f"{name}.pdf")
    plt.close(fig)


def plabel(ax, s, x=-0.16, y=1.04):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=8, fontweight="bold", va="bottom", ha="left")


def boot_mean_ci(x, B=2000, seed=0):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    r = np.random.default_rng(seed)
    bs = x[r.integers(0, len(x), (B, len(x)))].mean(1)
    return x.mean(), *np.percentile(bs, [2.5, 97.5])


seg = pd.read_csv(RES / "test_segments.csv")
seg = seg[seg["segment"].isin(["S1", "S2"])].copy()
seg["abs_eC"] = seg["e_C"].abs()
gat = pd.read_csv(RES / "test_gating.csv")
cfg = json.load(open(RES / "config_used.json"))
cal = json.load(open(RES / "dev_calibration.json"))
THR, BAND = cal["gate_threshold_dps"], cal["band_lo_hz"]


# ======================================================================= Fig. 4 example trial
def fig4(tid="PD_15_2"):
    from headimu import io_voisard as iov
    from headimu.evaluate import branch_signals, candidates, static_slice, windows
    folder = DATA / "neuro" / "PD" / tid.rsplit("_", 1)[0] / tid
    tr = iov.load_trial(tid, folder, cfg)
    fs = tr.fs
    w = windows(tr, fs, cfg["detect"]["window_pad_s"])
    i0, i1 = int(w["full"][0] * fs), int(w["full"][1] * fs)
    rows = []
    for loc in ("HE", "LB"):
        s = tr.sensors[loc]
        st = static_slice(tr, fs, len(s.acc), cfg["qc"]["min_static_s"])
        sig, q = branch_signals(s.acc, s.gyr, fs, cfg, BAND, static=st, which=("A1",))
        c = candidates(sig["A1"], fs, cfg, i0, i1, s.valid)
        rows.append((loc, sig["A1"], c, q))
    qhe = np.rad2deg(rows[0][3])
    gm = dsp.gate_mask(rows[0][3], fs, THR, cfg["gate"]["median_win_s"], cfg["gate"]["min_dur_s"], cfg["gate"]["pad_s"])
    t = np.arange(len(qhe)) / fs
    i0, i1 = max(0, i0), min(len(qhe), i1)
    sl = slice(i0, i1)
    fig, axs = plt.subplots(3, 1, figsize=(W1, 3.15), sharex=True,
                            gridspec_kw=dict(height_ratios=[1, 1, 0.8], hspace=0.18))
    gruns = [(a / fs, b / fs) for a, b in dsp.runs(gm[sl].copy()) ]
    gruns = [(a + i0 / fs, b + i0 / fs) for a, b in gruns]
    for k, (loc, x, c, _) in enumerate(rows):
        ax = axs[k]
        ax.axvspan(*w["turn"], color=FILL, lw=0, zorder=0)
        ax.plot(t[sl], x[sl], color=NAVY, lw=0.7, zorder=2)
        ci = (c * fs).astype(int)
        ax.plot(c, x[ci], "o", ms=2.6, mfc=RED, mec="white", mew=0.3, zorder=4)
        lag = cal["lags_s"].get(f"{loc}_A1", 0.0)
        ymax = np.nanmax(np.abs(x[sl])) * 1.08
        for h in tr.hs:
            ax.plot([h + lag] * 2, [ymax * 1.02, ymax * 1.16], color=INK, lw=0.6, zorder=3, clip_on=False)
        ax.set_ylim(-ymax, ymax * 1.18)
        ax.set_ylabel(("Head" if loc == "HE" else "Lower back") + " A1\n(m s$^{-2}$)", linespacing=1.1)
        plabel(ax, f"({'ab'[k]})", x=-0.15, y=0.98)
    axs[0].text(w["turn"][0] + (w["turn"][1] - w["turn"][0]) / 2, axs[0].get_ylim()[1] * 0.80, "U-turn",
                ha="center", va="top", fontsize=6, color=EDGE, style="italic")
    ax = axs[2]
    ax.axvspan(*w["turn"], color=FILL, lw=0, zorder=0)
    for a, b in gruns:
        ax.axvspan(a, b, ymin=0, ymax=1, facecolor="none", hatch="////", edgecolor=RED, lw=0, alpha=0.55, zorder=1)
    ax.plot(t[sl], qhe[sl], color=NAVY, lw=0.7, zorder=2)
    ax.axhline(THR, color=INK, lw=0.6, ls=(0, (3, 2)))
    ax.text(t[i1 - 1], THR + 4, f"q* = {THR:.0f}°/s", ha="right", va="bottom", fontsize=6)
    ax.set_ylabel("Head $q(t)$\n(°/s)", linespacing=1.1)
    ax.set_xlabel("Time (s)")
    ax.set_xlim(t[i0], t[i1 - 1])
    plabel(ax, "(c)", x=-0.15, y=0.98)
    handles = [Line2D([], [], color=NAVY, lw=0.8, label="band-passed signal"),
               Line2D([], [], ls="", marker="o", ms=3, mfc=RED, mec="white", label="detected step"),
               Line2D([], [], ls="", marker="|", ms=5, mew=0.8, color=INK, label="reference heel strike"),
               Patch(fc=FILL, ec="none", label="reference turn"),
               Patch(fc="none", ec=RED, hatch="////", lw=0, label="head turn gate")]
    fig.legend(handles=handles, loc="upper center", ncol=3, bbox_to_anchor=(0.53, 0.0), handlelength=1.4,
               columnspacing=1.0, handletextpad=0.4, fontsize=6)
    save(fig, "fig4_example_trial")


# ======================================================================= Fig. 5 Bland-Altman
def fig5():
    pt = pd.read_csv(RES / "table_primary.csv")
    panels = [("HE", "A1", "Head A1"), ("HE", "A0g", "Head A0g"), ("HE", "AC", "Head AC"), ("LB", "A1", "Lower back A1")]
    fig, axs = plt.subplots(2, 2, figsize=(W1, 3.05), sharex=True, sharey=True,
                            gridspec_kw=dict(hspace=0.32, wspace=0.12))
    YL = 22
    for ax, (loc, m, lab), k in zip(axs.flat, panels, range(4)):
        d = seg[(seg["loc"] == loc) & (seg["method"] == m)].dropna(subset=["C_imu", "C_ref"])
        mean = (d["C_imu"] + d["C_ref"]) / 2
        diff = d["C_imu"] - d["C_ref"]
        r = pt[(pt["sensor"] == loc) & (pt["method"] == m)].iloc[0]
        bias = float(r["BA_bias_spm"]); lo, hi = [float(v) for v in r["BA_LoA_spm"].split(" to ")]
        ax.axhspan(lo, hi, color=FILL, lw=0, zorder=0)
        cols = d["cohort"].map(COH_COLORS).fillna(EDGE)
        inside = diff.abs() <= YL
        ax.scatter(mean[inside], diff[inside], s=2.2, c=cols[inside], lw=0, alpha=0.75, zorder=2, rasterized=True)
        up, dn = int((diff > YL).sum()), int((diff < -YL).sum())
        ax.axhline(bias, color=INK, lw=0.7, zorder=3)
        for v in (lo, hi):
            ax.axhline(v, color=INK, lw=0.5, ls=(0, (3, 2)), zorder=3)
        ax.text(0.98, 0.97, rf"$\uparrow${up} off-scale", transform=ax.transAxes, ha="right", va="top", fontsize=5.5, color=EDGE, zorder=6, bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.85)) if up else None
        ax.text(0.98, 0.03, rf"$\downarrow${dn} off-scale", transform=ax.transAxes, ha="right", va="bottom", fontsize=5.5, color=EDGE, zorder=6, bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.85)) if dn else None
        ax.set_title(f"({'abcd'[k]}) {lab}", loc="left", fontsize=7, pad=2, fontweight="bold")
        ax.text(0.03, 0.97, f"bias {bias:+.2f}\nLoA {lo:.1f} to {hi:+.1f}", transform=ax.transAxes, va="top",
                fontsize=5.5, color=INK, linespacing=1.1, zorder=6,
                bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none", alpha=0.85))
        ax.set_ylim(-YL, YL); ax.set_xlim(55, 160)
        ax.set_yticks([-20, -10, 0, 10, 20]); ax.set_xticks([60, 80, 100, 120, 140, 160])
    fig.supxlabel("Mean of IMU and reference cadence (steps/min)", fontsize=7, y=0.0)
    fig.supylabel("IMU − reference (steps/min)", fontsize=7, x=0.02)
    handles = [Line2D([], [], ls="", marker="o", ms=3, mfc=COH_COLORS[c], mec="none", label=c) for c in COH]
    fig.legend(handles=handles, loc="lower center", ncol=8, bbox_to_anchor=(0.53, -0.09), handletextpad=0.1,
               columnspacing=0.7, fontsize=5.8)
    save(fig, "fig5_bland_altman")


# ======================================================================= Fig. 6 cohorts
def fig6():
    meths = [("HE", "A1", "Head A1", NAVY), ("HE", "A0g", "Head A0g", SKY), ("LB", "A1", "Lower back A1", RED)]
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(W1, 3.0), gridspec_kw=dict(height_ratios=[1.35, 1], hspace=0.38))
    YL = 8
    rng = np.random.default_rng(3)
    for j, (loc, m, lab, col) in enumerate(meths):
        d = seg[(seg["loc"] == loc) & (seg["method"] == m)]
        pp = d.groupby(["cohort", "participant"])["abs_eC"].median().reset_index()
        for i, c in enumerate(COH):
            v = pp.loc[pp["cohort"] == c, "abs_eC"].to_numpy()
            x0 = i + (j - 1) * 0.26
            vin = v[v <= YL]
            ax.scatter(x0 + rng.uniform(-0.07, 0.07, len(vin)), vin, s=2.0, color=col, alpha=0.45, lw=0, zorder=2)
            q1, q2, q3 = np.percentile(v, [25, 50, 75])
            ax.plot([x0, x0], [q1, min(q3, YL)], color=INK, lw=0.9, zorder=3, solid_capstyle="butt")
            ax.plot(x0, q2, "o", ms=3.0, mfc=col, mec=INK, mew=0.5, zorder=4)
            nout = int((v > YL).sum())
            if nout:
                ax.text(x0, YL + 0.15, f"{nout}", ha="center", va="bottom", fontsize=4.8, color=col)
    ax.set_xlim(-0.6, len(COH) - 0.4); ax.set_ylim(0, YL + 0.9)
    ax.set_xticks(range(len(COH))); ax.set_xticklabels(COH)
    ax.set_ylabel("|Cadence error|\n(steps/min)", linespacing=1.1)
    ax.axhline(YL, color=GRID, lw=0.5, ls=":")
    ax.legend(handles=[Line2D([], [], ls="", marker="o", ms=3.2, mfc=c, mec=INK, mew=0.5, label=l) for _, _, l, c in meths],
              loc="upper right", ncol=3, bbox_to_anchor=(1.0, 1.17), handletextpad=0.2, columnspacing=0.8)
    plabel(ax, "(a)", x=-0.19, y=1.03)
    # (b) share of straight segments with |error| > 5 steps/min
    for j, (loc, m, lab, col) in enumerate(meths):
        d = seg[(seg["loc"] == loc) & (seg["method"] == m)].dropna(subset=["e_C"])
        share = d.groupby("cohort")["abs_eC"].apply(lambda s: 100 * (s > 5).mean()).reindex(COH)
        bx.bar(np.arange(len(COH)) + (j - 1) * 0.26, share.to_numpy(), width=0.24, color=col, ec="none", zorder=2)
    bx.set_xticks(range(len(COH))); bx.set_xticklabels(COH)
    bx.set_xlim(-0.6, len(COH) - 0.4)
    bx.set_ylabel("Segments with |error|\n> 5 steps/min (%)", linespacing=1.1)
    bx.yaxis.grid(True, color=GRID, lw=0.4); bx.set_axisbelow(True)
    plabel(bx, "(b)", x=-0.19, y=1.03)
    save(fig, "fig6_cohorts")


# ======================================================================= Fig. 7 simulations
def _parse(s):
    a = s.replace("[", "").replace("]", "").replace(",", " ").split()
    return [float(v) for v in a]


def fig7():
    rot = pd.read_csv(RES / "table_sim_rotation.csv")
    lev = pd.read_csv(RES / "table_sim_leverarm.csv")
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(W1, 1.75), gridspec_kw=dict(wspace=0.42))
    mids = np.array([2.5, 7.5, 15, 25, 37.5])
    widths = np.array([5, 5, 10, 10, 15])
    est = np.array([_parse(s) for s in rot["A0_median_abs_eC"]])
    halv = rot["A0_halving_pct"].to_numpy(float)
    # invariant reference level (A0g, A1 at 0 cm)
    l0 = lev[(lev["offset_cm"] == 0) & lev["method"].isin(["A0g", "A1"])]
    ref = np.mean([_parse(s)[0] for s in l0["median_abs_eC"]])
    ax.axhline(ref, color=SKY, lw=1.2, zorder=1)
    ax.text(44, ref + 0.08, "A0g, A1 (invariant)", ha="right", va="bottom", fontsize=5.6, color="#4c7fb8")
    ax.fill_between(mids, est[:, 1], est[:, 2], color=NAVY, alpha=0.15, lw=0)
    ax.plot(mids, est[:, 0], "-o", color=NAVY, ms=3, mec="white", mew=0.4, zorder=3, label="A0")
    ax.set_xlim(0, 45); ax.set_xticks([0, 10, 20, 30, 45])
    ax.set_ylim(0, 4.5)
    ax.set_xlabel("Tilt of sensor X axis (°)")
    ax.set_ylabel("|Cadence error| (steps/min)")
    ax2 = ax.twinx()
    ax2.bar(mids, halv, width=widths * 0.55, color=RED, alpha=0.22, lw=0, zorder=0)
    ax2.set_ylim(0, 30); ax2.set_yticks([0, 10, 20, 30])
    ax2.spines["right"].set_visible(True); ax2.spines["top"].set_visible(False)
    ax2.tick_params(axis="y", colors=RED, labelsize=6)
    ax2.set_ylabel("Halving (%)", color=RED, fontsize=6.5, labelpad=1)
    ax.set_zorder(ax2.get_zorder() + 1); ax.patch.set_visible(False)
    ax.text(3, 4.35, "A0", color=NAVY, fontsize=6.2, va="top", fontweight="bold")
    plabel(ax, "(a)", x=-0.30, y=1.02)
    # (b) lever arm
    for j, (m, col) in enumerate((("A0g", SKY), ("A1", NAVY))):
        d = lev[lev["method"] == m].sort_values("offset_cm")
        e = np.array([_parse(s) for s in d["median_abs_eC"]])
        x = d["offset_cm"].to_numpy(float) + (j - 0.5) * 0.35
        bx.errorbar(x, e[:, 0], yerr=[e[:, 0] - e[:, 1], e[:, 2] - e[:, 0]], fmt="o", ms=3, color=col,
                    mec="white", mew=0.4, elinewidth=0.8, capsize=0, label=m)
    bx.set_ylim(0, 4.5); bx.set_xlim(-1, 9); bx.set_xticks([0, 2, 4, 6, 8])
    bx.set_xlabel("Lever-arm offset (cm)")
    bx.legend(loc="upper left", handletextpad=0.1, borderaxespad=0.2)
    plabel(bx, "(b)", x=-0.22, y=1.02)
    save(fig, "fig7_simulations")


# ======================================================================= Fig. 8 re-wear
def _visit_pairs(loc, m):
    s = seg[(seg["loc"] == loc) & (seg["method"] == m)]
    vis = s.groupby(["participant", "cohort", "visit", "sensor_type"])[["C_imu", "C_ref"]].median().reset_index()
    rows = []
    for p, g in vis.groupby("participant"):
        g = g.sort_values("visit", key=lambda x: pd.to_numeric(x, errors="coerce"))
        for st, gg in g.groupby("sensor_type"):
            if len(gg) >= 2:
                rows.append((p, gg["cohort"].iloc[0], *gg["C_imu"].to_numpy()[:2], *gg["C_ref"].to_numpy()[:2]))
                break
    return pd.DataFrame(rows, columns=["participant", "cohort", "imu1", "imu2", "ref1", "ref2"])


def fig8():
    rw = pd.read_csv(RES / "table_rewear.csv")
    rw = rw[rw["pairs"] == "same_sensor_pairs"]
    get = lambda m, loc: rw[(rw["method"] == m) & (rw["sensor"] == loc)].iloc[0]
    he = get("A1", "HE")
    mdc = float(he["MDC95_imu_spm"])
    d = _visit_pairs("HE", "A1")
    fig = plt.figure(figsize=(W1, 1.9))
    ax = fig.add_axes([0.11, 0.17, 0.33, 0.76])
    lo, hi = 65, 130
    xx = np.array([lo, hi])
    ax.fill_between(xx, xx - mdc, xx + mdc, color=FILL, lw=0, zorder=0)
    ax.plot(xx, xx, color=EDGE, lw=0.6, ls=(0, (3, 2)), zorder=1)
    for c, g in d.groupby("cohort"):
        ax.scatter(g["imu1"], g["imu2"], s=9, lw=0.35, ec="white", color=COH_COLORS.get(c, EDGE), zorder=3, label=c)
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
    ax.set_xticks([70, 90, 110, 130]); ax.set_yticks([70, 90, 110, 130])
    ax.set_xlabel("Visit 1 (steps/min)"); ax.set_ylabel("Visit 2 (steps/min)")
    ax.text(lo + 2, hi - 2, f"Head A1\n±MDC$_{{95}}$ = {mdc:.1f}", fontsize=5.6, va="top", color=EDGE, linespacing=1.1)
    fig.text(0.0, 0.97, "(a)", fontsize=8, fontweight="bold", va="top")
    ax.legend(loc="lower right", ncol=2, fontsize=5, handletextpad=0.0, columnspacing=0.4, borderaxespad=0.0,
              markerscale=0.8, labelspacing=0.2)
    # (b) forest
    bx = fig.add_axes([0.66, 0.17, 0.20, 0.76])
    nb = json.load(open(RES / "numbers_for_paper.json"))["rewear"]   # full precision (avoid 3-dp re-rounding)
    tri = lambda d: (d["icc"], d["ci_lo"], d["ci_hi"])
    items = [("Foot reference", tri(nb["same_sensor_pairs_HE_A1"]["ref"]), 0, INK, "s"),
             ("Head A1", tri(nb["same_sensor_pairs_HE_A1"]["imu"]), 0, NAVY, "o"),
             ("Head A0g", tri(nb["same_sensor_pairs_HE_A0g"]["imu"]), 0, SKY, "o"),
             ("Lower back A1", tri(nb["same_sensor_pairs_LB_A1"]["imu"]), 0, RED, "o")]
    for x0, x1, c in ((0.3, 0.5, "#f7f8f9"), (0.5, 0.75, "#eff1f3"), (0.75, 0.9, "#e4e8ec"), (0.9, 1.0, "#d8dee5")):
        bx.axvspan(x0, x1, color=c, lw=0, zorder=0)
    n = len(items)
    for i, (lab, (e, l, h), sem, col, mk) in enumerate(items):
        y = n - 1 - i
        bx.plot([l, h], [y, y], color=col, lw=1.0, zorder=2, solid_capstyle="butt")
        bx.plot(e, y, mk, ms=3.6, color=col, mec="white", mew=0.4, zorder=3)
        bx.text(1.03, y, f"{e:.2f} [{l:.2f}, {h:.2f}]", transform=bx.get_yaxis_transform(), fontsize=5.3, va="center")
    bx.set_yticks(range(n)); bx.set_yticklabels([it[0] for it in items][::-1], fontsize=6)
    bx.tick_params(axis="y", length=0, pad=2); bx.spines["left"].set_visible(False)
    bx.set_xlim(0.3, 1.0); bx.set_xticks([0.3, 0.5, 0.75, 1.0]); bx.set_xticklabels(["0.3", "0.5", "0.75", "1"])
    bx.set_ylim(-0.6, n - 0.4)
    bx.set_xlabel("ICC(A,1), n = 36")
    fig.text(0.47, 0.97, "(b)", fontsize=8, fontweight="bold", va="top")
    save(fig, "fig8_rewear")


# ======================================================================= Fig. 9 gating
def fig9():
    thrs = sorted(gat["threshold_dps"].unique())
    rng = np.random.default_rng(9)
    cov, D = [], {"precision": [], "recall": []}
    TD = {"turn_sensitivity": [], "straight_false_mark": []}
    for th in thrs:
        g = gat[gat["threshold_dps"] == th]
        cov.append(g.groupby("participant")["A2_time_coverage"].mean().mean())
        for v in D:
            x = (g[f"A2_accepted_{v}"] - g[f"A2R_accepted_{v}"]).groupby(g["participant"]).mean().dropna().to_numpy()
            bs = x[rng.integers(0, len(x), (2000, len(x)))].mean(1)
            D[v].append((100 * x.mean(), *(100 * np.percentile(bs, [2.5, 97.5]))))
        for v in TD:
            pmed = g.groupby("participant")[v].median().dropna()
            TD[v].append((pmed.median(), *pmed.quantile([0.25, 0.75])))
    cov = np.array(cov)
    fig = plt.figure(figsize=(W1, 3.25))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.72, wspace=0.48)
    for k, (v, lab, yl) in enumerate((("precision", "Precision of kept steps", (-0.5, 2.0)),
                                      ("recall", "Recall of steps in kept time", (0, 8.5)))):
        ax = fig.add_subplot(gs[0, k])
        e = np.array(D[v])
        ax.axhline(0, color=EDGE, lw=0.6, ls=":")
        ax.fill_between(cov, e[:, 1], e[:, 2], color=NAVY, alpha=0.15, lw=0)
        ax.plot(cov, e[:, 0], "-o", color=NAVY, ms=3, mec="white", mew=0.4)
        for c, val, hi, t in zip(cov, e[:, 0], e[:, 2], thrs):
            if t in (20, 30, 90) or (k == 1 and t == 60):
                ax.annotate(f"{t:.0f}°/s", (c, hi), xytext=(0, 2), textcoords="offset points", ha="center",
                            va="bottom", fontsize=5.2, color=NAVY)
        ax.set_ylim(*yl); ax.set_xlim(0.74, 0.96); ax.set_xticks([0.75, 0.85, 0.95])
        ax.set_xlabel("Fraction of time kept")
        ax.set_ylabel("A2 − A2-R (pp)" if k == 0 else "")
        ax.set_title(lab, fontsize=6.6, loc="left", pad=3)
        ax.text(0.95, 0.02 if k == 0 else 0.03, "random\nremoval", transform=ax.transAxes, ha="right", va="bottom",
                fontsize=5.0, color=EDGE, linespacing=1.0) if k == 0 else None
        plabel(ax, f"({'ab'[k]})", x=-0.34 if k == 0 else -0.22, y=1.03)
    cx = fig.add_subplot(gs[1, 0])
    for v, col, mk, name in (("turn_sensitivity", NAVY, "o", "turn sensitivity"),
                             ("straight_false_mark", RED, "s", "false-mark rate")):
        e = np.array(TD[v])
        cx.fill_between(thrs, e[:, 1], e[:, 2], color=col, alpha=0.15, lw=0)
        cx.plot(thrs, e[:, 0], "-" + mk, color=col, ms=2.8, mec="white", mew=0.4, label=name)
    cx.axvline(THR, color=INK, lw=0.6, ls=(0, (3, 2)))
    cx.set_xticks([20, 45, 90]); cx.set_xlim(15, 95); cx.set_ylim(0, 1.05)
    cx.set_xlabel("Gate threshold q* (°/s)"); cx.set_ylabel("Fraction of time")
    cx.text(55, 0.80, "turn sensitivity", fontsize=5.4, color=NAVY, ha="left")
    cx.text(55, 0.10, "false-mark rate", fontsize=5.4, color=RED, ha="left")
    cx.set_title("Turn detection", fontsize=6.6, loc="left", pad=3)
    plabel(cx, "(c)", x=-0.34, y=1.03)
    # (d) signal-quality screening by step regularity (head-only), segment level
    sr = json.load(open(RES / "sr_curve.json"))
    dx = fig.add_subplot(gs[1, 1])
    cv = np.array([c["cov"] for c in sr["curve"]]); bg = np.array([c["big"] for c in sr["curve"]])
    o = np.argsort(cv)
    dx.plot(cv[o], bg[o], "-", color=NAVY, lw=1.0, label="regularity screen")
    dx.axhline(sr["all_big"], color=RED, lw=0.8, ls=(0, (3, 2)), label="random removal")
    dx.plot(sr["op"]["cov"], sr["op"]["big"], "o", ms=3.4, mfc=NAVY, mec="white", mew=0.5, zorder=4)
    dx.annotate(f"SR ≥ {sr['thr']:.2f}", (sr["op"]["cov"], sr["op"]["big"]), xytext=(-14, 4), textcoords="offset points",
                ha="right", va="bottom", fontsize=5.2, color=NAVY)
    dx.set_xlim(0.6, 1.0); dx.set_ylim(0, 10.5); dx.set_xticks([0.6, 0.8, 1.0])
    dx.set_xlabel("Fraction of segments kept"); dx.set_ylabel("Error >5 steps/min (%)")
    dx.text(0.61, sr["all_big"] + 0.3, "random removal", fontsize=5.2, color=RED, va="bottom")
    dx.text(0.62, 2.3, "regularity screen", fontsize=5.2, color=NAVY, va="bottom")
    dx.set_title("Step-regularity screen", fontsize=6.6, loc="left", pad=3)
    plabel(dx, "(d)", x=-0.36, y=1.03)
    save(fig, "fig9_gating")


if __name__ == "__main__":
    which = sys.argv[4:] or ["4", "5", "6", "7", "8", "9"]
    for k in which:
        globals()[f"fig{k}"]()
        print("done fig", k)
