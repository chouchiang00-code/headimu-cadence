#!/usr/bin/env python3
"""POST HOC checks requested in the V16.3 review (added after the V16 draft; reported as post hoc).

 (1) DUO-GAIT: why B2 had the smallest and B1 a larger error than B0.
     - step detection precision / recall / over-detection (detected / reference events) of B1 and B2, DUO-GAIT vs Voisard
     - B1 segmentation: the B1 segment assigned to each reference pass, its extension beyond the pass, and the cadence the
       B1 peaks give when restricted to the reference pass (separates segmentation from step detection)
     - B2: number of running outputs per pass
 (2) Voisard B2 turn detection (precision 0.39): where the false turn onsets occur (before the first / after the last
     heel strike, or during straight walking), their duration and integrated rotation (B1 requires >= 90 deg; B2 does not)
 (3) Accelerometer noise: per-segment change of the A1 cadence error with added noise (paired), share of zero-error
     segments, large errors, and a participant-bootstrap CI (unique relabelling) of the change in the median of
     participant-median |e_C|.

Usage: python analysis/v16_post_b_checks.py PACK.npz RESULTS_V11 E2E HEAD_NPZ PROCESSED_ZIP SENS_ROWS OUT [--jobs N]
"""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from headimu import endtoend as E, duogait as dg  # noqa: E402

FS = 100.0
B = 2000


def prf(tp, nd, nr):
    return {"precision": tp / nd, "recall": tp / nr, "f1": 2 * tp / (nd + nr), "detected_per_reference": nd / nr}


# ----------------------------------------------------------------------------- (1) DUO-GAIT
def duogait(head_npz, proc_zip, P):
    z = np.load(head_npz)
    walks = sorted({tuple(k.split("|")[:2]) for k in z.files if k.count("|") == 2})
    rows = []
    for cond, sub in walks:
        acc, gyr = dg.adapt_head(z[f"{cond}|{sub}|acc_g"], z[f"{cond}|{sub}|gyr_dps"], float(z[f"{cond}|{sub}|fs"]))
        valid = np.isfinite(acc).all(1) & np.isfinite(gyr).all(1)
        acc = np.nan_to_num(acc); gyr = np.nan_to_num(gyr)
        ref = dg.load_reference(proc_zip, cond, sub)
        passes, turns, ics = dg.reference_passes(ref)
        o = E.offline(acc, gyr, valid, FS, P)
        c = E.causal(acc, gyr, valid, FS, P)
        pk = o["peaks"] - P.get("lag_b1", 0.0)
        outs = c["outputs"]
        for k, p in enumerate(passes):
            a, b = p["t0"], p["t1"]
            ov = [(min(s["t1"], b) - max(s["t0"], a), s) for s in o["segments"]]
            ov = [x for x in ov if x[0] >= 1.0]
            r = {"cond": cond, "sub": sub, "pass": k, "C_ref": p["C_ref"], "dur": b - a}
            if ov:
                s = max(ov, key=lambda x: x[0])[1]
                r.update({"B1_C": s["cadence"], "B1_seg_t0": s["t0"], "B1_seg_t1": s["t1"],
                          "B1_ext_before_s": max(0.0, a - s["t0"]), "B1_ext_after_s": max(0.0, s["t1"] - b),
                          "B1_short_before_s": max(0.0, s["t0"] - a), "B1_short_after_s": max(0.0, b - s["t1"])})
            iv = np.diff(pk[(pk >= a - 0.1) & (pk <= b + 0.1)])
            r["B1peaks_in_pass_C"] = 60.0 / np.median(iv) if len(iv) >= 3 else np.nan
            sel = outs[(outs[:, 0] >= a) & (outs[:, 0] <= b + P["confirm_s"])] if len(outs) else np.zeros((0, 3))
            r["B2_n_out"] = int(len(sel))
            rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- (2) Voisard B2 turns
def b2_turns(args):
    t, acc, gyr, valid, hs, turn, P = args
    c = E.causal(acc, gyr, valid, FS, P)
    ev = c["events"]; q = c["q"]
    # events are stored in seconds; convert to sample indices
    ons = [int(round(k * FS)) for e, k in ev if e == "turn_on"]; offs = [int(round(k * FS)) for e, k in ev if e == "turn_off"]
    out = []
    for on in ons:
        x = on / FS
        nxt = [f for f in offs if f > on]
        off = nxt[0] if nxt else len(q)
        # rotation integrated over the declared turn (onset declared after gate_min_s; include that lead-in)
        a0 = max(0, on - int(round(P["gate_min_s"] * FS)))
        ang = float(np.sum(q[a0:off]) / FS)
        if turn[0] - 1.0 <= x <= turn[1] and hs[0] <= x <= hs[-1]:
            where = "true_turn_window"
        elif x < hs[0]:
            where = "before_first_hs"
        elif x > hs[-1]:
            where = "after_last_hs"
        elif abs(x - turn[0]) <= 3.0 or abs(x - turn[1]) <= 3.0:
            where = "straight_within_3s_of_turn"
        else:
            where = "straight_walking"
        out.append({"trial": t, "t_on": x, "where": where, "dur_s": (off - a0) / FS, "angle_deg": ang})
    return out


def main():
    a = sys.argv[1:]
    pack, r11, e2e, head_npz, proc_zip, sens_rows, out = map(Path, a[:7])
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 1
    out.mkdir(parents=True, exist_ok=True)
    P = json.loads((e2e / "endtoend_params.json").read_text(encoding="utf-8"))["params"]
    R = {}

    # (1)
    D = duogait(head_npz, proc_zip, P)
    D.to_csv(out / "duogait_b1_segmentation.csv", index=False)
    ext_passes = pd.read_csv(e2e.parent / "ext" / "external_passes.csv")
    D = D.merge(ext_passes[["cond", "sub", "pass", "B0_C", "B1_C", "B2_C"]].rename(columns={"B1_C": "B1_C_ext"}),
                on=["cond", "sub", "pass"])
    assert np.allclose(D["B1_C"], D["B1_C_ext"], equal_nan=True), "B1 cadence differs from the external run"
    for k in ("B0", "B1", "B2"):
        D[f"{k}_e"] = D[f"{k}_C"] - D["C_ref"]
    D["B1peaks_in_pass_e"] = D["B1peaks_in_pass_C"] - D["C_ref"]
    pm = lambda col: float(D.assign(x=D[col].abs()).groupby("sub")["x"].median().median())
    W = pd.read_csv(e2e.parent / "ext" / "external_walks.csv")
    T = pd.read_csv(e2e / "endtoend_trials.csv"); T = T[T["set"] == "test"]
    R["duogait"] = {
        "median_abs_err_participant": {k: pm(f"{k}_e") for k in ("B0", "B1", "B2", "B1peaks_in_pass")},
        "bias_mean": {k: float(D[f"{k}_e"].mean()) for k in ("B0", "B1", "B2", "B1peaks_in_pass")},
        "B1_segment_extension_s_median": {"before": float(D["B1_ext_before_s"].median()), "after": float(D["B1_ext_after_s"].median())},
        "B1_segment_shortfall_s_median": {"start": float(D["B1_short_before_s"].median()), "end": float(D["B1_short_after_s"].median())},
        "pct_passes_B1_ext_gt_1s": float(100 * ((D["B1_ext_before_s"] > 1) | (D["B1_ext_after_s"] > 1)).mean()),
        "B1_e_mean_by_ext_gt_1s": D.assign(ext=(D["B1_ext_before_s"] > 1) | (D["B1_ext_after_s"] > 1))
                                   .groupby("ext")["B1_e"].agg(["mean", "count"]).reset_index().to_dict("records"),
        "spearman_B1_e_vs_total_ext": float(D[["B1_e"]].assign(x=D["B1_ext_before_s"] + D["B1_ext_after_s"]).corr("spearman").iloc[0, 1]),
        "B2_outputs_per_pass_median": float(D["B2_n_out"].median()),
        "steps_B1": prf(W["B1_step_tp"].sum(), W["B1_step_nd"].sum(), W["B1_step_nr"].sum()),
        "steps_B2": prf(W["B2_step_tp"].sum(), W["B2_step_nd"].sum(), W["B2_step_nr"].sum()),
        "voisard_steps_B1": prf(T["B1_step_tp"].sum(), T["B1_step_nd"].sum(), T["B1_step_nr"].sum()),
        "voisard_steps_B2": prf(T["B2_step_tp"].sum(), T["B2_step_nd"].sum(), T["B2_step_nr"].sum()),
        "voisard_B2_pct_trials_steps_over_110pct": float(100 * (T["B2_step_nd"] / T["B2_step_nr"] > 1.10).mean()),
        "voisard_B2_over_detection_by_cohort": T.groupby("cohort").apply(lambda g: g["B2_step_nd"].sum() / g["B2_step_nr"].sum()).round(3).to_dict(),
    }

    # (2)
    z = np.load(pack)
    meta = {m["trial"]: m for m in json.loads(str(z["__meta__"]))}
    tests = list(T["trial"])
    args = []
    for t in tests:
        hs = np.sort(np.concatenate([z[f"{t}|ref_hs_left"], z[f"{t}|ref_hs_right"]]))
        args.append((t, z[f"{t}|acc"].astype(float), z[f"{t}|gyr"].astype(float), z[f"{t}|valid"], hs, z[f"{t}|ref_turn"], P))
    with Pool(jobs) as pool:
        res = pool.map(b2_turns, args, chunksize=8)
    TT = pd.DataFrame([r for x in res for r in x]).merge(T[["trial", "cohort"]], on="trial")
    TT.to_csv(out / "voisard_b2_turn_onsets.csv", index=False)
    fp = TT[TT["where"] != "true_turn_window"]
    # the V16 FP count: onsets outside [hs0, hsN] or outside the window; recompute and check against the trial table
    n_fp_v16 = int(T["B2_turn_fp"].sum())
    R["voisard_b2_turns"] = {
        "n_trials": len(tests), "n_onsets": int(len(TT)), "n_false_onsets": int(len(fp)), "n_false_onsets_v16_table": n_fp_v16,
        "precision_onsets": float((TT["where"] == "true_turn_window").sum() / len(TT)),
        "false_by_location_pct": (fp["where"].value_counts(normalize=True) * 100).round(1).to_dict(),
        "false_angle_deg_median_iqr": [float(x) for x in fp["angle_deg"].quantile([0.25, 0.5, 0.75])],
        "false_pct_below_90deg": float(100 * (fp["angle_deg"] < 90).mean()),
        "true_angle_deg_median": float(TT.loc[TT["where"] == "true_turn_window", "angle_deg"].median()),
        "false_dur_s_median": float(fp["dur_s"].median()),
        "precision_if_90deg_rule": float(((TT["where"] == "true_turn_window") & (TT["angle_deg"] >= 90)).sum()
                                         / max(1, (TT["angle_deg"] >= 90).sum())),
        "recall_if_90deg_rule_trials": float(TT[(TT["where"] == "true_turn_window") & (TT["angle_deg"] >= 90)]["trial"].nunique() / len(tests)),
        "false_per_trial_by_cohort": (fp.groupby("cohort").size() / T.groupby("cohort").size()).round(2).to_dict(),
    }

    # (3)
    sr = pd.read_csv(sens_rows)
    a1 = sr[sr["method"] == "A1"]
    base = a1[a1["pert"] == "none"].set_index(["trial", "segment"])
    noise = {}
    for lev in (0.05, 0.1, 0.2):
        x = a1[(a1["pert"] == "acc_noise") & (a1["level"] == lev)].set_index(["trial", "segment"])
        j = base[["participant", "e_C"]].join(x["e_C"].rename("e_n"))
        j["d_abs"] = j["e_n"].abs() - j["e_C"].abs()
        def stat(df):
            p0 = df.assign(v=df["e_C"].abs()).groupby("participant")["v"].median().median()
            p1 = df.assign(v=df["e_n"].abs()).groupby("participant")["v"].median().median()
            return p1 - p0
        rng = np.random.default_rng(20261109)
        g = {k: v for k, v in j.reset_index().groupby("participant")}
        ids = list(g)
        bs = [stat(pd.concat([g[i].assign(participant=k) for k, i in enumerate(rng.choice(ids, len(ids)))])) for _ in range(B)]
        noise[str(lev)] = {
            "median_participant_abs_change": float(stat(j.reset_index())), "ci95": [float(v) for v in np.percentile(bs, [2.5, 97.5])],
            "mean_abs_err": [float(j["e_C"].abs().mean()), float(j["e_n"].abs().mean())],
            "pct_zero_error": [float(100 * (j["e_C"].abs() < 1e-9).mean()), float(100 * (j["e_n"].abs() < 1e-9).mean())],
            "pct_big": [float(100 * (j["e_C"].abs() > 5).mean()), float(100 * (j["e_n"].abs() > 5).mean())],
            "pct_segments_unchanged": float(100 * (j["d_abs"].abs() < 1e-9).mean()),
            "pct_better_worse": [float(100 * (j["d_abs"] < -1e-9).mean()), float(100 * (j["d_abs"] > 1e-9).mean())],
        }
    R["acc_noise_A1"] = noise
    (out / "b_checks_summary.json").write_text(json.dumps(R, indent=1, default=float))
    print(json.dumps(R, indent=1, default=float))


# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v16_post_b_checks.py PACK.npz RESULTS_V11 E2E HEAD_NPZ PROCESSED_ZIP SENS_ROWS OUT [--jobs N]')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

if __name__ == "__main__":
    main()
