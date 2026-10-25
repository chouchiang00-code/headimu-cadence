"""Tables (CSV/XLSX) and figures (PNG/PDF) for the paper."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import dsp, stats  # noqa: E402

METHODS = [("HE", "A0"), ("HE", "A0g"), ("HE", "A1"), ("HE", "AC"), ("LB", "A0g"), ("LB", "A1"), ("LB", "AC")]
COHORT_ORDER = ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]
plt.rcParams.update({"font.family": "sans-serif",
                     "font.sans-serif": ["Arial", "Helvetica", "TeX Gyre Heros", "Liberation Sans", "DejaVu Sans"],
                     "mathtext.fontset": "stixsans", "font.size": 7, "axes.titlesize": 7, "axes.labelsize": 7,
                     "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6, "axes.linewidth": 0.6,
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6, "lines.linewidth": 0.9,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.02})
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
INK, EDGE, NAVY, RED = "#1a1a1a", "#5b616b", "#1f3b63", "#b03a2e"
COH_COLORS = dict(zip(["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"],
                      ["#1f3b63", "#4c7fb8", "#8fb3d9", "#7a9e7e", "#b03a2e", "#d9822b", "#e3b23c", "#7d5a8c"]))


def _fmt(est, lo=None, hi=None, nd=2):
    if est is None or not np.isfinite(est):
        return "NA"
    if lo is None or not np.isfinite(lo):
        return f"{est:.{nd}f}"
    return f"{est:.{nd}f} [{lo:.{nd}f}, {hi:.{nd}f}]"


def _miqr(x, nd=3):
    x = pd.Series(x).dropna()
    if x.empty:
        return "NA"
    q = x.quantile([0.25, 0.5, 0.75])
    return f"{q[0.5]:.{nd}f} [{q[0.25]:.{nd}f}, {q[0.75]:.{nd}f}]"


def _pp(df, val, how="median"):
    return stats.participant_agg(df, val, how=how)


# ============================================================================= tables
def make_tables(qc, seg, mat, gat, rot, lev, cfg, thr, band_lo):
    B = cfg["stats"]["bootstrap"]
    T, N = {}, {}
    seg = seg.copy()
    seg["abs_eC"] = seg["e_C"].abs()
    seg["rel_err_pct"] = 100 * seg["abs_eC"] / seg["C_ref"]

    # ---- inclusion
    inc = []
    allp = qc["participant"].nunique()
    inc.append({"item": "trials found", "n_trials": len(qc), "n_participants": allp})
    for r, g in qc[qc["exclusion"].fillna("") != ""].groupby("exclusion"):
        inc.append({"item": f"excluded: {r}", "n_trials": len(g), "n_participants": g["participant"].nunique()})
    ok = qc[qc["exclusion"].fillna("") == ""]
    for s, g in ok.groupby("set"):
        inc.append({"item": f"included, {s} set", "n_trials": len(g), "n_participants": g["participant"].nunique()})
    for s, g in ok.groupby("sensor_type"):
        inc.append({"item": f"included, sensor {s}", "n_trials": len(g), "n_participants": g["participant"].nunique()})
    T["inclusion"] = pd.DataFrame(inc)

    # ---- signal-level QC by sensor type (Table II)
    qcols = ["missing_frac", "longest_gap_s", "invalid_frac", "acc_sat_frac", "gyr_sat_frac", "static_acc_sd_mps2",
             "static_gyr_sd_dps", "static_gnorm_mps2", "static_gyr_bias_dps", "static_xfrac", "turn_angle_deg",
             "fdom_over_fstep", "step_regularity"]
    rows = []
    for loc in ("HE", "LB"):
        for c in qcols:
            col = f"{loc}_{c}"
            if col not in qc:
                continue
            r = {"sensor": loc, "metric": c}
            for s, g in ok.groupby("sensor_type"):
                r[s] = _miqr(g[col])
            r["all"] = _miqr(ok[col])
            rows.append(r)
    T["signal_qc"] = pd.DataFrame(rows)

    # ---- primary agreement (Table III)
    rows = []
    pser = {}
    for loc, m in METHODS:
        s = seg[(seg["loc"] == loc) & (seg["method"] == m)]
        if s.empty:
            continue
        pa = _pp(s, "abs_eC")
        pb = _pp(s, "e_C")
        pser[(loc, m)] = pa
        e1 = stats.boot_ci(pa.to_numpy(), np.median, B, seed=1)
        e2 = stats.boot_ci(pb.to_numpy(), np.median, B, seed=2)
        e3 = stats.boot_ci(_pp(s, "rel_err_pct").to_numpy(), np.median, B, seed=13)
        ba = stats.bland_altman_repeated(s.dropna(subset=["C_imu", "C_ref"]), "C_imu", "C_ref")
        acc_thr = cfg["metrics"]["acceptable_loa_spm"]
        rows.append({"sensor": loc, "method": m, "n_participants": e1[3], "n_segments": int(s["e_C"].notna().sum()),
                     "median_abs_eC_spm": _fmt(*e1[:3]), "median_rel_err_pct": _fmt(*e3[:3]), "median_eC_spm": _fmt(*e2[:3]),
                     "BA_bias_spm": _fmt(ba.get("bias", np.nan)), "BA_LoA_spm": f"{_fmt(ba.get('loa_lo', np.nan))} to {_fmt(ba.get('loa_hi', np.nan))}",
                     "LoA_within_acceptable": (abs(ba.get("loa_lo", np.inf)) <= acc_thr and abs(ba.get("loa_hi", np.inf)) <= acc_thr) if acc_thr else "threshold not set",
                     "median_detect_ratio": _fmt(_pp(s, "detect_ratio").median()) if m != "AC" else "NA",
                     "halving_pct": _fmt(100 * s["halving"].mean(), nd=1), "doubling_pct": _fmt(100 * s["doubling"].mean(), nd=1),
                     "missing_estimate_pct": _fmt(100 * s["e_C"].isna().mean(), nd=1)})
        N[f"{loc}_{m}"] = {"median_abs_eC": e1[:3], "median_rel_err_pct": e3[:3], "median_eC": e2[:3], "BA": ba}
    T["primary"] = pd.DataFrame(rows)

    # ---- paired comparisons with Holm
    comps = [(("HE", "A0g"), ("HE", "A0")), (("HE", "A1"), ("HE", "A0g")), (("HE", "A1"), ("HE", "AC")),
             (("HE", "A1"), ("LB", "A1")), (("HE", "A0g"), ("LB", "A0g")), (("HE", "AC"), ("LB", "AC"))]
    rows = []
    for x, y in comps:
        if x in pser and y in pser:
            r = stats.paired_compare(pser[x], pser[y], B, seed=3)
            rows.append({"comparison": f"{x[0]}-{x[1]} vs {y[0]}-{y[1]}", **r})
    cmp = pd.DataFrame(rows)
    if not cmp.empty:
        cmp["p_holm"] = stats.holm(cmp["p_wilcoxon"].tolist())
    T["paired_comparisons"] = cmp

    # ---- event matching (secondary)
    rows = []
    for (m, tol), g in mat.groupby(["method", "tol_s"]):
        r = {"method": m, "tol_s": tol}
        for v in ("precision", "recall", "f1", "mae_s", "bias_s", "step_interval_abs_err_s"):
            e = stats.boot_ci(_pp(g, v).to_numpy(), np.median, B, seed=4)
            sc = 1000 if v.endswith("_s") else 1
            r[v if sc == 1 else v.replace("_s", "_ms")] = _fmt(e[0] * sc, e[1] * sc, e[2] * sc, nd=1 if sc > 1 else 3)
        rows.append(r)
    T["event_matching"] = pd.DataFrame(rows)

    # ---- strata (cohort, sensor, age)
    rows = []
    age_cut = cfg["stats"]["age_cut"]
    seg["age_group"] = np.where(seg["age"] >= age_cut, f">={age_cut}", f"<{age_cut}")
    for col, levels in (("cohort", COHORT_ORDER), ("sensor_type", None), ("age_group", None)):
        lv = levels or sorted(seg[col].dropna().unique())
        for L in lv:
            g = seg[seg[col] == L]
            if g.empty:
                continue
            r = {"stratum": col, "level": L, "n_participants": g["participant"].nunique()}
            for loc, m in (("HE", "A0g"), ("HE", "A1"), ("HE", "AC"), ("LB", "A1")):
                s = g[(g["loc"] == loc) & (g["method"] == m)]
                e = stats.boot_ci(_pp(s, "abs_eC").to_numpy(), np.median, B, seed=5)
                r[f"{loc}_{m}_median_abs_eC"] = _fmt(*e[:3])
            s = g[(g["loc"] == "HE") & (g["method"] == "A1")]
            r["HE_A1_halving_pct"] = _fmt(100 * s["halving"].mean(), nd=1)
            rows.append(r)
    T["strata"] = pd.DataFrame(rows)

    # ---- rotation simulation
    if not rot.empty:
        rot = rot.copy()
        rot["abs_eC"] = rot["e_C"].abs()
        bins = [-0.1, 5, 10, 20, 30, 45, 90, 180]
        rot["tilt_bin"] = pd.cut(rot["tilt_deg"], bins).astype(str)
        rows = []
        for b, g in rot.groupby("tilt_bin", sort=False):
            pa = g.groupby("participant")["abs_eC"].median()
            e = stats.boot_ci(pa.to_numpy(), np.median, B, seed=6)
            rows.append({"tilt_deg": b, "n_runs": len(g), "A0_median_abs_eC": _fmt(*e[:3]),
                         "A0_median_detect_ratio": _fmt(g.groupby("participant")["detect_ratio"].median().median()),
                         "A0_halving_pct": _fmt(100 * g["halving"].mean(), nd=1)})
        T["sim_rotation"] = pd.DataFrame(rows)
    if not lev.empty:
        lev = lev.copy()
        lev["abs_eC"] = lev["e_C"].abs() if "e_C" in lev else np.nan
        rows = []
        for (off, m), g in lev.groupby(["offset_m", "method"]):
            r = {"offset_cm": round(100 * off, 1), "method": m}
            if m == "A2":
                r["accepted_precision"] = _fmt(g.groupby("participant")["accepted_precision"].median().median(), nd=3)
                r["time_coverage"] = _fmt(g.groupby("participant")["time_coverage"].median().median(), nd=3)
            else:
                e = stats.boot_ci(g.groupby("participant")["abs_eC"].median().to_numpy(), np.median, B, seed=7)
                r["median_abs_eC"] = _fmt(*e[:3])
                r["median_detect_ratio"] = _fmt(g.groupby("participant")["detect_ratio"].median().median())
                r["halving_pct"] = _fmt(100 * g["halving"].mean(), nd=1)
            rows.append(r)
        T["sim_leverarm"] = pd.DataFrame(rows)

    # ---- gating, turn detection, A2 vs A2-R
    rows = []
    for th, g in gat.groupby("threshold_dps"):
        r = {"threshold_dps": th, "selected": th == thr}
        for v in ("turn_sensitivity", "straight_false_mark", "turn_detected", "turn_start_err_s", "turn_end_err_s"):
            r[v] = _fmt(g.groupby("participant")[v].median().median(), nd=3)
        pm = lambda col: g.groupby("participant")[col].mean().mean()   # proportions: mean of participant means
        for v in ("time_coverage", "ref_event_coverage", "accepted_precision", "accepted_recall", "full_window_recall"):
            r[f"A2_{v}"] = _fmt(pm(f"A2_{v}"), nd=3)
            r[f"A2R_{v}"] = _fmt(pm(f"A2R_{v}"), nd=3)
        r["A2_step_interval_err_ms"] = _fmt(1000 * g.groupby("participant")["A2_accepted_step_interval_abs_err_s"].median().median(), nd=1)
        r["A1_precision"] = _fmt(pm("A1_accepted_precision"), nd=3)
        r["A1_recall"] = _fmt(pm("A1_accepted_recall"), nd=3)
        for v in ("precision", "recall"):
            d = (g[f"A2_accepted_{v}"] - g[f"A2R_accepted_{v}"]).groupby(g["participant"]).mean()
            e = stats.boot_ci(d.to_numpy(), np.mean, B, seed=8)
            r[f"A2_minus_A2R_{v}"] = _fmt(*e[:3], nd=4)
        rows.append(r)
    T["gating"] = pd.DataFrame(rows)
    gsel = gat[gat["threshold_dps"] == thr]
    rows = []
    for c in COHORT_ORDER:
        g = gsel[gsel["cohort"] == c]
        if g.empty:
            continue
        rows.append({"cohort": c, "n_participants": g["participant"].nunique(),
                     "turn_sensitivity": _fmt(g.groupby("participant")["turn_sensitivity"].median().median(), nd=3),
                     "straight_false_mark": _fmt(g.groupby("participant")["straight_false_mark"].median().median(), nd=3),
                     "turn_detected_pct": _fmt(100 * g["turn_detected"].mean(), nd=1)})
    T["turn_detection_by_cohort"] = pd.DataFrame(rows)

    # ---- re-wear (between-visit) reliability
    T["rewear"], N["rewear"] = rewear_tables(seg, B)

    # ---- exploratory TUG (only if present in metadata)
    if "tug" in qc and qc["tug"].notna().sum() >= 10:
        pass  # left to the author: correlate visit-level head cadence with TUG

    N["tables"] = {k: v.to_dict(orient="records") for k, v in T.items()}
    return T, N


def rewear_tables(seg, B):
    s = seg[seg["segment"].isin(["S1", "S2"])]
    vis = (s.groupby(["participant", "visit", "sensor_type", "loc", "method"])[["C_imu", "C_ref", "e_T"]]
           .median().reset_index())
    rows, num = [], {}
    for label, same in (("same_sensor_pairs", True), ("different_sensor_pairs", False)):
        for (loc, m) in (("HE", "A1"), ("HE", "A0g"), ("LB", "A1")):
            v = vis[(vis["loc"] == loc) & (vis["method"] == m)]
            Xh, Xr = [], []
            for p, g in v.groupby("participant"):
                g = g.sort_values("visit", key=lambda x: pd.to_numeric(x, errors="coerce"))
                if len(g) < 2:
                    continue
                if same:
                    for st, gg in g.groupby("sensor_type"):
                        if len(gg) >= 2:
                            Xh.append(gg["C_imu"].to_numpy()[:2]); Xr.append(gg["C_ref"].to_numpy()[:2]); break
                else:
                    if g["sensor_type"].iloc[0] != g["sensor_type"].iloc[1]:
                        Xh.append(g["C_imu"].to_numpy()[:2]); Xr.append(g["C_ref"].to_numpy()[:2])
            Xh, Xr = np.array(Xh, float).reshape(-1, 2), np.array(Xr, float).reshape(-1, 2)
            ih, ir = stats.icc_boot(Xh, B, seed=9), stats.icc_boot(Xr, B, seed=10)
            rows.append({"pairs": label, "sensor": loc, "method": m, "n_participants": ih.get("n"),
                         "ICC_A1_imu": _fmt(ih.get("icc", np.nan), ih.get("ci_lo"), ih.get("ci_hi"), nd=3),
                         "SEM_imu_spm": _fmt(ih.get("sem", np.nan)), "MDC95_imu_spm": _fmt(ih.get("mdc95", np.nan)),
                         "ICC_A1_reference": _fmt(ir.get("icc", np.nan), ir.get("ci_lo"), ir.get("ci_hi"), nd=3),
                         "SEM_reference_spm": _fmt(ir.get("sem", np.nan))})
            num[f"{label}_{loc}_{m}"] = {"imu": ih, "ref": ir}
    he = s[(s["loc"] == "HE") & (s["method"] == "A1")]
    trial = he.groupby(["participant", "visit", "trial"])["e_T"].median().reset_index()
    nv = stats.nested_variance(trial, "e_T")
    rows.append({"pairs": "variance_decomposition_eT_HE_A1", "sensor": "HE", "method": "A1",
                 "n_participants": nv.get("n_participants"),
                 "ICC_A1_imu": f"participant {nv.get('var_participant', np.nan):.2e}; visit {nv.get('var_visit', np.nan):.2e}; residual {nv.get('var_residual', np.nan):.2e} (s^2)"
                 if "var_visit" in nv else "insufficient data"})
    num["variance_decomposition"] = nv
    return pd.DataFrame(rows), num


# ============================================================================= figures
def _save(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=300)
    fig.savefig(out / f"{name}.pdf")
    plt.close(fig)


def fig_inspect(tr, cfg, path):
    fs = tr.fs
    fig, ax = plt.subplots(3, 1, figsize=(7.2, 6), sharex=True)
    if "HE" in tr.sensors:
        a = tr.sensors["HE"].acc
        t = np.arange(len(a)) / fs
        ax[0].plot(t, np.linalg.norm(a, axis=1), lw=0.6, label="|a| head")
        ax[0].set_ylabel("m/s$^2$")
        ghat = dsp.gravity_dir(a, fs, cfg["detect"]["gravity_lp_hz"])
        q = np.rad2deg(dsp.turn_rate(tr.sensors["HE"].gyr, ghat))
        ax[2].plot(t, q, lw=0.6, color="C2", label="q(t) head")
        ax[2].set_ylabel("deg/s")
    for h in tr.hs_left:
        ax[0].axvline(h, color="C1", lw=0.4)
    for h in tr.hs_right:
        ax[0].axvline(h, color="C3", lw=0.4, ls="--")
    if "LF" in tr.sensors:
        g = tr.sensors["LF"].gyr
        ax[1].plot(np.arange(len(g)) / fs, np.rad2deg(np.linalg.norm(g, axis=1)), lw=0.6, label="|w| left foot")
        for h in tr.hs_left:
            ax[1].axvline(h, color="C1", lw=0.5)
        ax[1].set_ylabel("deg/s")
    if tr.turn:
        for k in range(3):
            ax[k].axvspan(*tr.turn, color="0.85", zorder=0)
    ax[0].set_title(f"{tr.trial_id}  ({tr.sensor_type}); vertical lines = reference heel strikes (L solid, R dashed); grey = turn")
    for k in range(3):
        ax[k].legend(loc="upper right", fontsize=6)
    ax[2].set_xlabel("time (s)")
    fig.savefig(path, dpi=150)
    plt.close(fig)


def make_figures(qc, seg, mat, gat, rot, lev, cfg, thr, out, folder_of, test_ids, band_lo, lags):
    from . import io_voisard as iov
    from .evaluate import branch_signals, candidates, static_slice, windows
    out = Path(out)
    # Fig. 1: example trial
    if test_ids:
        tid = test_ids[len(test_ids) // 2]
        tr = iov.load_trial(tid, Path(folder_of[tid]), cfg)
        s = tr.sensors["HE"]
        fs = tr.fs
        st = static_slice(tr, fs, len(s.acc), cfg["qc"]["min_static_s"])
        sig, q = branch_signals(s.acc, s.gyr, fs, cfg, band_lo, static=st)
        w = windows(tr, fs, cfg["detect"]["window_pad_s"])
        i0, i1 = int(w["full"][0] * fs), int(w["full"][1] * fs)
        t = np.arange(len(s.acc)) / fs
        gm = dsp.gate_mask(q, fs, thr, cfg["gate"]["median_win_s"], cfg["gate"]["min_dur_s"], cfg["gate"]["pad_s"])
        fig, ax = plt.subplots(4, 1, figsize=(7.2, 6.2), sharex=True)
        for k, (name, lab) in enumerate((("A0", "A0: fixed X axis"), ("A0g", "A0g: gravity-projected vertical"), ("A1", "A1: norm"))):
            ax[k].plot(t[i0:i1], sig[name][i0:i1], lw=0.7, color=NAVY)
            c = candidates(sig[name], fs, cfg, i0, i1, s.valid)
            ax[k].plot(c, sig[name][(c * fs).astype(int)], "v", ms=3, color=RED)
            for h in tr.hs:
                ax[k].axvline(h + lags.get(f"HE_{name}", 0), color="0.5", lw=0.4, ls=":")
            ax[k].set_ylabel(lab, fontsize=6)
        ax[3].plot(t[i0:i1], np.rad2deg(q[i0:i1]), lw=0.7, color=NAVY)
        ax[3].axhline(thr, color="k", lw=0.5, ls="--")
        ax[3].fill_between(t[i0:i1], 0, np.where(gm[i0:i1], np.rad2deg(q[i0:i1]).max(), 0), color=RED, alpha=0.12, step="mid")
        ax[3].set_ylabel("q(t) (deg/s)", fontsize=6)
        for k in range(4):
            ax[k].axvspan(*w["turn"], color="0.9", zorder=0)
        ax[3].set_xlabel("time (s)")
        ax[0].set_title(f"Example test trial {tid}: band-passed head signals, detected peaks (triangles), "
                        "lag-shifted reference heel strikes (dotted), reference turn (grey)", fontsize=6)
        _save(fig, out, "fig4_example_trial")

    # Fig. 2: Bland-Altman
    seg = seg.copy()
    panels = [("HE", "A0g"), ("HE", "A1"), ("HE", "AC"), ("LB", "A1")]
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.4))
    for ax, (loc, m) in zip(axs.ravel(), panels):
        s = seg[(seg["loc"] == loc) & (seg["method"] == m)].dropna(subset=["C_imu", "C_ref"])
        if s.empty:
            continue
        mean = (s["C_imu"] + s["C_ref"]) / 2
        diff = s["C_imu"] - s["C_ref"]
        for k, c in enumerate(COHORT_ORDER):
            sel = s["cohort"] == c
            ax.scatter(mean[sel], diff[sel], s=3, alpha=0.55, lw=0, label=c, color=COH_COLORS[c])
        ba = stats.bland_altman_repeated(s, "C_imu", "C_ref")
        for y, ls in ((ba["bias"], "-"), (ba["loa_lo"], "--"), (ba["loa_hi"], "--")):
            ax.axhline(y, color="k", lw=0.7, ls=ls)
        ax.set_title(f"{loc} {m}: bias {ba['bias']:.2f}, LoA {ba['loa_lo']:.1f} to {ba['loa_hi']:.1f} steps/min", fontsize=7)
        ax.set_xlabel("mean cadence (steps/min)")
        ax.set_ylabel("IMU - reference (steps/min)")
        ax.set_ylim(np.nanpercentile(diff, 0.5) - 2, np.nanpercentile(diff, 99.5) + 2)
    axs[0, 0].legend(fontsize=5, markerscale=2, ncol=2)
    fig.tight_layout()
    _save(fig, out, "fig5_bland_altman")

    # Fig. 3: cohort comparison head vs lower back
    seg["abs_eC"] = seg["e_C"].abs()
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    pos = np.arange(len(COHORT_ORDER))
    for k, (loc, m, dx) in enumerate((("HE", "A1", -0.2), ("HE", "A0g", 0.0), ("LB", "A1", 0.2))):
        data = []
        for c in COHORT_ORDER:
            s = seg[(seg["loc"] == loc) & (seg["method"] == m) & (seg["cohort"] == c)]
            data.append(s.groupby("participant")["abs_eC"].median().dropna().to_numpy())
        bp = ax.boxplot(data, positions=pos + dx, widths=0.18, showfliers=False, patch_artist=True)
        for b in bp["boxes"]:
            b.set_facecolor([NAVY, "#8fb3d9", RED][k]); b.set_alpha(0.75); b.set_linewidth(0.5)
        for el in ("medians",):
            for ln in bp[el]:
                ln.set_color(INK)
        ax.plot([], [], color=[NAVY, "#8fb3d9", RED][k], lw=6, alpha=0.75, label=f"{loc} {m}")
    ax.set_xticks(pos, COHORT_ORDER)
    ax.set_ylabel("|cadence error| (steps/min)\nparticipant median")
    ax.legend(fontsize=6)
    _save(fig, out, "fig6_cohorts")

    # Fig. 4: simulations
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.8))
    if not rot.empty:
        r = rot.copy()
        r["abs_eC"] = r["e_C"].abs()
        r["tb"] = pd.cut(r["tilt_deg"], [-0.1, 5, 10, 20, 30, 45, 90, 180])
        g = r.groupby(["tb", "participant"], observed=True)["abs_eC"].median().groupby(level=0, observed=True)
        x = [iv.mid for iv in g.median().index]
        axs[0].errorbar(x, g.median().values, yerr=[g.median().values - g.quantile(0.25).values,
                                                     g.quantile(0.75).values - g.median().values], fmt="o-", ms=3, color=NAVY, capsize=2)
        axs[0].set_xlabel("tilt of X axis (\u00b0)")
        axs[0].set_ylabel("A0 |cadence error| (steps/min)")
        axs[0].set_title("A0 under rigid rotation (A0g, A1, A2 invariant)", fontsize=6.5, loc="left")
        axs[0].text(-0.16, 1.06, "a", transform=axs[0].transAxes, fontsize=8, fontweight="bold")
    if not lev.empty:
        lv = lev[lev["method"].isin(["A0g", "A1"])].copy()
        lv["abs_eC"] = lv["e_C"].abs()
        for m in ("A0g", "A1"):
            g = lv[lv["method"] == m].groupby(["offset_m", "participant"])["abs_eC"].median().groupby(level=0)
            axs[1].errorbar(100 * g.median().index.to_numpy(), g.median().values,
                            yerr=[g.median().values - g.quantile(0.25).values, g.quantile(0.75).values - g.median().values],
                            fmt="o-", ms=3, label=m, capsize=2, color={"A0g": NAVY, "A1": RED}[m])
        axs[1].set_xlabel("lever-arm offset (cm)")
        axs[1].set_ylabel("|cadence error| (steps/min)")
        axs[1].legend(fontsize=6)
        axs[1].set_title("Lever arm (median, IQR)", fontsize=6.5, loc="left")
        axs[1].text(-0.16, 1.06, "b", transform=axs[1].transAxes, fontsize=8, fontweight="bold")
    fig.tight_layout()
    _save(fig, out, "fig7_simulations")

    # Fig. 9: error-coverage, A2 vs random gating (proportions: mean of participant means)
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.6))
    g = gat.groupby("threshold_dps")
    pmean = lambda col: g.apply(lambda d: d.groupby("participant")[col].mean().mean())
    cov, p2, pr, p1 = pmean("A2_time_coverage"), pmean("A2_accepted_precision"), pmean("A2R_accepted_precision"), pmean("A1_accepted_precision")
    axs[0].plot(cov.values, p2.values, "o-", color=NAVY, ms=4, label="A2 (turn gate)")
    axs[0].plot(cov.values, pr.values, "s--", color=RED, ms=4, label="A2-R (random gate, same coverage)")
    axs[0].axhline(p1.mean(), color=EDGE, lw=0.7, ls=":", label="A1 (no gate)")
    for th, x_, y_ in zip(cov.index, cov.values, p2.values):
        axs[0].annotate(f"{th:g}\u00b0/s", (x_, y_), fontsize=5.5, xytext=(2, 3), textcoords="offset points")
    axs[0].set_xlabel("time coverage"); axs[0].set_ylabel("precision of kept candidates")
    axs[0].legend(fontsize=5.5, frameon=False)
    axs[0].text(-0.14, 1.04, "a", transform=axs[0].transAxes, fontsize=8, fontweight="bold")
    sens = g.apply(lambda d: d.groupby("participant")["turn_sensitivity"].median().median())
    fm = g.apply(lambda d: d.groupby("participant")["straight_false_mark"].median().median())
    axs[1].plot(sens.index, sens.values, "o-", color=NAVY, ms=4, label="turn sensitivity")
    axs[1].plot(fm.index, fm.values, "s-", color=RED, ms=4, label="straight-walking false-mark rate")
    axs[1].axvline(thr, color=EDGE, lw=0.6, ls="--")
    axs[1].set_xlabel("gate threshold q* (\u00b0/s)")
    axs[1].legend(fontsize=5.5, frameon=False)
    axs[1].text(-0.14, 1.04, "b", transform=axs[1].transAxes, fontsize=8, fontweight="bold")
    fig.tight_layout()
    _save(fig, out, "fig9_gating")

    fig_inclusion_flow(qc, out)
    fig_rewear(seg, out, cfg)
    fig_signal_qc(qc, out)


# ============================================================================= Fig. 3: alluvial (Sankey) of trial flow
def _ribbon(ax, x0, x1, y0a, y0b, y1a, y1b, color, alpha=0.5):
    t = np.linspace(0, 1, 60)
    sm = 3 * t ** 2 - 2 * t ** 3
    xs = x0 + (x1 - x0) * t
    lo = y0a + (y1a - y0a) * sm
    hi = y0b + (y1b - y0b) * sm
    ax.fill_between(xs, lo, hi, color=color, alpha=alpha, lw=0, zorder=1)


def fig_inclusion_flow(qc, out):
    q = qc.copy()
    q["exclusion"] = q["exclusion"].fillna("")
    q["cohort"] = q["cohort"].fillna("NA")
    q["c1"] = np.where(q["exclusion"] == "", "Included", "Excluded")
    q["c2"] = np.where(q["c1"] == "Excluded", None, np.where(q["set"] == "dev", "Development", "Test"))
    tt = q[q["c2"] == "Test"]
    nv = tt.groupby(["participant", "sensor_type"])["visit"].nunique()
    rw_part = set(nv[nv >= 2].reset_index()["participant"])
    q["c3"] = np.where(q["c2"] == "Test", np.where(q["participant"].isin(rw_part), "Re-wear subset", "Single visit"), None)
    cohorts = [c for c in COHORT_ORDER if c in set(q["cohort"])] + sorted(set(q["cohort"]) - set(COHORT_ORDER))
    cols = [("cohort", cohorts), ("c1", ["Included", "Excluded"]), ("c2", ["Development", "Test"]),
            ("c3", ["Single visit", "Re-wear subset"])]
    N = len(q)
    gap = 0.035 * N
    gaps = [0.035 * N, 0.16 * N, 0.16 * N, 0.10 * N]
    xs = [0.0, 1.0, 2.0, 3.0]
    bw = 0.06
    # node positions (top-down)
    pos = {}
    H = N + gaps[0] * (len(cohorts) - 1)
    for (col, nodes), x, g in zip(cols, xs, gaps):
        sizes = [int((q[col] == n).sum()) for n in nodes]
        tot = sum(sizes) + g * (len([s for s in sizes if s]) - 1)
        y = (H + tot) / 2 if col != "c1" else H         # QC column aligned to the top
        for n, sz in zip(nodes, sizes):
            if sz == 0:
                continue
            pos[(col, n)] = [y - sz, y]
            y -= sz + g
    fig = plt.figure(figsize=(3.45, 2.75))
    ax = fig.add_axes([0.13, 0.02, 0.62, 0.92]); ax.axis("off")
    # ribbons between consecutive columns; stacking order = cohort order inside each node
    for k in range(len(cols) - 1):
        a_col, b_col = cols[k][0], cols[k + 1][0]
        sub = q[q[b_col].notna()] if b_col != "cohort" else q
        grp = sub.groupby([a_col, b_col, "cohort"]).size()
        cur_a = {key: v[1] for key, v in pos.items() if key[0] == a_col}
        cur_b = {key: v[1] for key, v in pos.items() if key[0] == b_col}
        order = sorted(grp.index, key=lambda g: (cols[k][1].index(g[0]), cols[k + 1][1].index(g[1]), cohorts.index(g[2])))
        for a, b, c in order:
            n = grp[(a, b, c)]
            ya = cur_a[(a_col, a)]; yb = cur_b[(b_col, b)]
            col = COH_COLORS.get(c, EDGE) if not (b == "Excluded") else RED
            _ribbon(ax, xs[k] + bw / 2, xs[k + 1] - bw / 2, ya - n, ya, yb - n, yb, col, 0.45 if b != "Excluded" else 0.6)
            cur_a[(a_col, a)] -= n; cur_b[(b_col, b)] -= n
    # nodes and labels
    for (col, nodes), x in zip(cols, xs):
        for n in nodes:
            if (col, n) not in pos:
                continue
            y0, y1 = pos[(col, n)]
            sel = q[q[col] == n]
            fc = COH_COLORS.get(n, INK) if col == "cohort" else (RED if n == "Excluded" else "#3a3f47")
            ax.add_patch(plt.Rectangle((x - bw / 2, y0), bw, y1 - y0, fc=fc, ec="none", zorder=3))
            if col == "cohort":
                ax.text(x - bw, (y0 + y1) / 2, f"{n}  {len(sel)}", ha="right", va="center", fontsize=6)
            else:
                lab = (f"{n}\n{len(sel)} trials · {sel.groupby(['participant', 'visit']).ngroups} visit"
                       if n == "Excluded" else f"{n}\n{len(sel)} trials · {sel['participant'].nunique()} part.")
                if col == "c3":
                    ha, dx, yy, va = "left", bw, (y0 + y1) / 2, "center"
                elif n == "Excluded":
                    ha, dx, yy, va = "right", bw / 2, y0 - 0.05 * N, "top"
                elif n == "Test":
                    ha, dx, yy, va = "center", 0, y0 - 0.015 * N, "top"
                elif col == "c1":
                    ha, dx, yy, va = "right", bw / 2, y1 + 0.015 * N, "bottom"
                else:
                    ha, dx, yy, va = "left", -bw / 2, y1 + 0.015 * N, "bottom"
                ax.text(x + dx, yy, lab, ha=ha, va=va, fontsize=5.6, linespacing=1.15, zorder=5,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    top = max(v[1] for v in pos.values())
    for x, t in zip(xs, ["Cohort", "Quality\ncontrol", "Participant-\nwise split", "Test-set\nuse"]):
        ax.text(x, top + 0.17 * N, t, ha="center", va="bottom", fontsize=6.2, fontweight="bold", color=EDGE, linespacing=1.1)
    ax.set_xlim(-0.35, 3.25)
    ax.set_ylim(min(v[0] for v in pos.values()) - 0.12 * N, top + 0.32 * N)
    _save(fig, out, "fig3_inclusion_flow")


# ============================================================================= Fig. 8: re-wear agreement + ICC forest plot
def _visit_pairs(seg, loc, m):
    s = seg[seg["segment"].isin(["S1", "S2"]) & (seg["loc"] == loc) & (seg["method"] == m)]
    vis = s.groupby(["participant", "cohort", "visit", "sensor_type"])[["C_imu", "C_ref"]].median().reset_index()
    rows = []
    for p, g in vis.groupby("participant"):
        g = g.sort_values("visit", key=lambda x: pd.to_numeric(x, errors="coerce"))
        for st, gg in g.groupby("sensor_type"):
            if len(gg) >= 2:
                rows.append((p, gg["cohort"].iloc[0], *gg["C_imu"].to_numpy()[:2], *gg["C_ref"].to_numpy()[:2]))
                break
    return pd.DataFrame(rows, columns=["participant", "cohort", "imu1", "imu2", "ref1", "ref2"])


def fig_rewear(seg, out, cfg):
    B = cfg["stats"]["bootstrap"]
    d = _visit_pairs(seg, "HE", "A1")
    fig = plt.figure(figsize=(3.45, 1.95))
    # (a) scatter with MDC band
    ax = fig.add_axes([0.10, 0.20, 0.36, 0.70])
    if not d.empty:
        icc = stats.icc_boot(d[["imu1", "imu2"]].to_numpy(float), B, seed=11)
        lo = np.nanmin(d[["imu1", "imu2"]].to_numpy()) - 4
        hi = np.nanmax(d[["imu1", "imu2"]].to_numpy()) + 4
        xx = np.array([lo, hi])
        mdc = icc.get("mdc95", np.nan)
        if np.isfinite(mdc):
            ax.fill_between(xx, xx - mdc, xx + mdc, color="#e7e9ec", lw=0, zorder=0)
        ax.plot(xx, xx, color=EDGE, lw=0.6, ls="--", zorder=1)
        for c, g in d.groupby("cohort"):
            ax.scatter(g["imu1"], g["imu2"], s=9, lw=0.3, ec="white", color=COH_COLORS.get(c, EDGE), label=c, zorder=3)
        ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
        ax.text(0.03, 0.97, f"band: ±MDC$_{{95}}$ = {mdc:.1f}", transform=ax.transAxes, fontsize=5.5, va="top", color=EDGE)
        ax.legend(fontsize=5.2, frameon=False, loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=4,
                  handletextpad=0.0, columnspacing=0.5, borderaxespad=0.1, markerscale=0.9)
    ax.set_xlabel("visit 1 head cadence (steps/min)", fontsize=6); ax.set_ylabel("visit 2 (steps/min)", fontsize=6)
    ax.text(-0.32, 1.14, "a", transform=ax.transAxes, fontsize=8, fontweight="bold")
    # (b) ICC forest plot
    bx = fig.add_axes([0.64, 0.20, 0.22, 0.70])
    rows = []
    for lab, loc, m, col in (("Foot reference", "HE", "A1", "ref"), ("Head A1", "HE", "A1", "imu"),
                             ("Head A0g", "HE", "A0g", "imu"), ("Lower back A1", "LB", "A1", "imu")):
        dd = _visit_pairs(seg, loc, m)
        if dd.empty:
            continue
        r = stats.icc_boot(dd[[f"{col}1", f"{col}2"]].to_numpy(float), B, seed=12)
        rows.append((lab, r))
    lows = [r.get("ci_lo", np.nan) for _, r in rows]
    xmin = min([0.5] + [np.floor(v * 10) / 10 for v in lows if np.isfinite(v)])
    for x0, x1, c in ((xmin, 0.5, "#fbfbfc"), (0.5, 0.75, "#f4f5f7"), (0.75, 0.9, "#eaedf1"), (0.9, 1.0, "#dfe4ea")):
        if x1 > x0:
            bx.axvspan(x0, x1, color=c, lw=0, zorder=0)
    for x, t in (((xmin + 0.5) / 2, "poor"), (0.625, "moderate"), (0.825, "good"), (0.95, "exc.")):
        if x > xmin and not (t == "poor" and xmin >= 0.5):
            bx.text(x, len(rows) - 0.35, t, ha="center", va="bottom", fontsize=4.8, color=EDGE)
    for i, (lab, r) in enumerate(rows):
        y = len(rows) - 1 - i
        c = INK if lab == "Foot reference" else NAVY
        bx.plot([r.get("ci_lo", np.nan), r.get("ci_hi", np.nan)], [y, y], color=c, lw=1.0, zorder=2)
        bx.plot(r.get("icc", np.nan), y, "s" if lab == "Foot reference" else "o", ms=3.6, color=c, mec="white", mew=0.4, zorder=3)
        bx.text(1.03, y, f"{r.get('icc', np.nan):.2f} [{r.get('ci_lo', np.nan):.2f}, {r.get('ci_hi', np.nan):.2f}]\nSEM {r.get('sem', np.nan):.1f} · n={r.get('n', 0)}",
                transform=bx.get_yaxis_transform(), fontsize=4.9, va="center", linespacing=1.1)
    bx.set_yticks(range(len(rows))); bx.set_yticklabels([r[0] for r in rows][::-1], fontsize=5.8)
    bx.tick_params(axis="y", pad=1)
    bx.set_ylim(-0.6, len(rows) - 0.1)
    bx.set_xlim(xmin, 1.0); bx.set_xlabel("ICC(A,1) [95% CI]")
    bx.spines["left"].set_visible(False); bx.tick_params(axis="y", length=0)
    bx.text(-0.80, 1.08, "b", transform=bx.transAxes, fontsize=8, fontweight="bold")
    _save(fig, out, "fig8_rewear")


# ============================================================================= Fig. S1: raincloud plots of signal-level QC
def fig_signal_qc(qc, out):
    from scipy.stats import gaussian_kde
    ok = qc[qc["exclusion"].fillna("") == ""]
    panels = [("HE_static_gnorm_mps2", "static |a| (m s$^{-2}$)", (9.31, 10.31), 9.81),
              ("HE_static_xfrac", "gravity fraction on X", (0.85, 1.0), None),
              ("HE_turn_angle_deg", "integrated turn angle (°)", (150, 210), 180),
              ("HE_fdom_over_fstep", "dominant / step frequency", (0.9, 1.1), 1.0),
              ("HE_static_gyr_sd_dps", "static gyro SD (° s$^{-1}$)", None, None),
              ("HE_step_regularity", "step regularity", None, None)]
    types = [t for t in ("XSens", "Technoconcept") if t in set(ok["sensor_type"])] or sorted(ok["sensor_type"].dropna().unique())
    pal = {"XSens": RED, "Technoconcept": NAVY}
    rng = np.random.default_rng(0)
    fig, axs = plt.subplots(3, 2, figsize=(3.45, 3.0))
    for k, (ax, (col, lab, band, ref)) in enumerate(zip(axs.ravel(), panels)):
        if col not in ok:
            ax.axis("off"); continue
        allv = ok[col].dropna()
        if band:
            ax.axvspan(*band, color="#eef1f4", lw=0, zorder=0)
        if ref is not None:
            ax.axvline(ref, color=EDGE, lw=0.5, ls="--", zorder=1)
        for j, t in enumerate(types):
            x = ok.loc[ok["sensor_type"] == t, col].dropna().to_numpy()
            if x.size < 3:
                continue
            y0 = j * 1.0
            c = pal.get(t, EDGE)
            grid = np.linspace(allv.min(), allv.max(), 200)
            try:
                dens = gaussian_kde(x)(grid)
                dens = 0.42 * dens / dens.max()
                ax.fill_between(grid, y0 + 0.08, y0 + 0.08 + dens, color=c, alpha=0.35, lw=0)
                ax.plot(grid, y0 + 0.08 + dens, color=c, lw=0.6)
            except Exception:
                pass
            ax.scatter(x, y0 - 0.12 + rng.uniform(-0.09, 0.09, x.size), s=1.6, color=c, alpha=0.6, lw=0)
            q1, q2, q3 = np.percentile(x, [25, 50, 75])
            ax.plot([q1, q3], [y0 + 0.02, y0 + 0.02], color=INK, lw=1.4, solid_capstyle="butt")
            ax.plot(q2, y0 + 0.02, "o", ms=2.6, color="white", mec=INK, mew=0.6, zorder=5)
        ax.set_yticks([j for j in range(len(types))])
        ax.set_yticklabels(types if k % 2 == 0 else [""] * len(types), fontsize=5.8)
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        ax.set_ylim(-0.35, len(types) - 0.4)
        ax.set_xlabel(lab, fontsize=6, labelpad=1)
        ax.text(-0.02 if k % 2 else -0.36, 1.02, "abcdef"[k], transform=ax.transAxes, fontsize=7.5, fontweight="bold")
    fig.tight_layout(h_pad=0.6, w_pad=0.8)
    _save(fig, out, "figS1_signal_qc")
