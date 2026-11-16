#!/usr/bin/env python3
"""V17 restructuring (post hoc presentation of prespecified B0 outcomes): cohort-stratified head vs lower-back table
and figure.

For each cohort of the test set: participants, segments, median reference cadence, head A1 and lower-back A1 median
|e_C| (median of participant medians, 95% CI from 2000 participant bootstrap resamples, each draw relabelled), the
paired head - lower-back difference of participant medians (95% CI), and the share of segments with |e_C| > 5
steps/min at the head, the lower back, and both. Values for 'All' use the same code, so they must reproduce Table II
(head A1 1.53 [1.31, 1.71], lower back A1 1.36 [1.21, 1.54]); the script asserts this.

Usage: python analysis/v17_cohort_table.py RESULTS_V11 OUT
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from headimu import stats  # noqa: E402

ORDER = ["HS", "HOA", "KOA", "ACL", "CVA", "PD", "CIPN", "RIL"]
B = 2000


def boot_pair(df, seed):
    """CI of (median of head participant medians) - (median of LB participant medians) and of the median paired diff."""
    rng = np.random.default_rng(seed)
    ids = df.index.to_numpy()
    out = []
    for _ in range(B):
        s = df.loc[rng.choice(ids, len(ids))]
        out.append(np.median(s["d"]))
    return np.percentile(out, [2.5, 97.5])


def main():
    r11, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    seg = pd.read_csv(r11 / "test_segments.csv")
    seg = seg[seg["method"] == "A1"].copy()
    seg["abs"] = seg["e_C"].abs()
    seg["big"] = seg["abs"] > 5
    he = seg[seg["loc"] == "HE"].set_index(["trial", "segment"])
    lb = seg[seg["loc"] == "LB"].set_index(["trial", "segment"])
    j = he[["participant", "cohort", "C_ref", "abs", "big"]].join(lb[["abs", "big"]], rsuffix="_lb", how="inner")
    rows = []
    for k, coh in enumerate(["All"] + ORDER):
        d = j if coh == "All" else j[j["cohort"] == coh]
        pm = d.groupby("participant")[["abs", "abs_lb"]].median()
        pm["d"] = pm["abs"] - pm["abs_lb"]
        h_ci = stats.boot_ci(pm["abs"].to_numpy(), np.median, B, seed=1)
        l_ci = stats.boot_ci(pm["abs_lb"].to_numpy(), np.median, B, seed=1)
        d_ci = boot_pair(pm, 100 + k)
        rows.append({
            "cohort": coh, "n_participants": int(len(pm)), "n_segments": int(len(d)),
            "cadence_ref_median": float(d["C_ref"].median()),
            "head_median": float(h_ci[0]), "head_lo": float(h_ci[1]), "head_hi": float(h_ci[2]),
            "lb_median": float(l_ci[0]), "lb_lo": float(l_ci[1]), "lb_hi": float(l_ci[2]),
            "diff_median": float(np.median(pm["d"])), "diff_lo": float(d_ci[0]), "diff_hi": float(d_ci[1]),
            "big_head_pct": float(100 * d["big"].mean()), "big_lb_pct": float(100 * d["big_lb"].mean()),
            "big_both_pct": float(100 * (d["big"] & d["big_lb"]).mean()),
            "big_head_only_n": int((d["big"] & ~d["big_lb"]).sum()), "big_lb_only_n": int((~d["big"] & d["big_lb"]).sum()),
            "big_both_n": int((d["big"] & d["big_lb"]).sum()),
        })
    T = pd.DataFrame(rows)
    a = T.iloc[0]
    assert abs(a["head_median"] - 1.53) < 0.006 and abs(a["head_lo"] - 1.31) < 0.006 and abs(a["head_hi"] - 1.71) < 0.006, a
    assert abs(a["lb_median"] - 1.36) < 0.006, a
    T.to_csv(out / "cohort_head_vs_lb.csv", index=False)
    (out / "cohort_head_vs_lb.json").write_text(json.dumps(rows, indent=1))
    print(T.round(2).to_string())

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "svg.fonttype": "none", "pdf.fonttype": 42})
    C = T.iloc[1:].reset_index(drop=True)
    y = np.arange(len(C))[::-1]
    fig, ax = plt.subplots(1, 2, figsize=(3.45, 2.7), gridspec_kw={"width_ratios": [1.25, 1], "wspace": 0.12})
    for off, pre, col, lab in ((0.16, "head", "#2a6fb0", "Head"), (-0.16, "lb", "#d07a2a", "Lower back")):
        ax[0].errorbar(C[f"{pre}_median"], y + off, xerr=[C[f"{pre}_median"] - C[f"{pre}_lo"], C[f"{pre}_hi"] - C[f"{pre}_median"]],
                       fmt="o", ms=3.2, color=col, elinewidth=0.9, capsize=1.6, label=lab)
    ax[0].set_yticks(y)
    ax[0].set_yticklabels([f"{c} ({n})" for c, n in zip(C["cohort"], C["n_participants"])])
    ax[0].set_xlabel("Median |$e_C$| (steps/min)")
    ax[0].set_xlim(0, max(C["head_hi"].max(), C["lb_hi"].max()) * 1.08)
    ax[0].legend(frameon=False, loc="lower right", fontsize=6.5, handletextpad=0.2)
    ax[0].set_title("(a) Typical error", fontsize=7.5, loc="left")
    w = 0.34
    ax[1].barh(y + 0.18, C["big_head_pct"], height=w, color="#2a6fb0", label="Head")
    ax[1].barh(y - 0.18, C["big_lb_pct"], height=w, color="#d07a2a", label="Lower back")
    ax[1].barh(y - 0.18, C["big_both_pct"], height=w, color="none", edgecolor="k", hatch="////", lw=0.4, label="Both")
    ax[1].barh(y + 0.18, C["big_both_pct"], height=w, color="none", edgecolor="k", hatch="////", lw=0.4)
    ax[1].set_yticks(y); ax[1].set_yticklabels([]); ax[1].tick_params(axis="y", length=0)
    ax[1].set_xlabel("Segments, |$e_C$| > 5 (%)")
    ax[1].legend(frameon=False, loc="lower right", fontsize=6.5, handletextpad=0.3)
    ax[1].set_title("(b) Large errors", fontsize=7.5, loc="left")
    for a_ in ax:
        a_.spines[["top", "right"]].set_visible(False)
        a_.grid(axis="x", lw=0.3, alpha=0.5)
    fig.subplots_adjust(left=0.2, right=0.98, bottom=0.17, top=0.92)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out / f"fig_cohort_head_vs_lb.{ext}", dpi=600 if ext == "png" else None)


# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v17_cohort_table.py RESULTS_V11 OUT')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

if __name__ == "__main__":
    main()
