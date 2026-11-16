#!/usr/bin/env python3
"""V18.2 review checks (post hoc, test set only, nothing re-tuned):
 (a) head minus lower back under the stride-defined reference, for the published peak estimator and AGS;
 (b) cost of the operating-envelope rule (segment SR of the same sensor >= 0.7, chosen on dev) by clinician VGA level;
 (c) which large errors the rule flags, split by where they occur (both locations / head only), for the published
     estimator and for AGS.
Usage: python analysis/v18_review.py EXT_TEST.csv TRUST_TEST_SCORED.csv OUT.json"""
import json, sys
import numpy as np, pandas as pd

# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v18_review.py EXT_TEST.csv TRUST_TEST_SCORED.csv OUT.json')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

EXT, TRUST, OUT = sys.argv[1:4]
SR_RULE = 0.7
B = int(__import__("os").environ.get("NB", 2000))
rng = np.random.default_rng(20261113)

e = pd.read_csv(EXT)
e = e[e.C_peak.notna()]
he = e[e["loc"] == "HE"].set_index(["trial", "segment"])
lb = e[e["loc"] == "LB"].set_index(["trial", "segment"])
keys = he.index.intersection(lb.index)
he, lb = he.loc[keys], lb.loc[keys]
vga = pd.read_csv(TRUST).set_index(["trial", "segment"])["vga"]
D = pd.DataFrame({"participant": he.participant, "cohort": he.cohort, "vga": vga.reindex(keys).values,
                  "R_step": he.R_step, "R_stride": he.R_stride,
                  "HE_peak": he.C_peak, "LB_peak": lb.C_peak, "HE_ags": he.C_ags, "LB_ags": lb.C_ags,
                  "HE_sr": he.sr, "LB_sr": lb.sr}).reset_index()
for loc in ("HE", "LB"):
    D[f"{loc}_in"] = D[f"{loc}_sr"].fillna(0) >= SR_RULE
    for est in ("peak", "ags"):
        D[f"{loc}_{est}_big"] = (D[f"{loc}_{est}"] - D.R_step).abs() > 5
idx = D.groupby("participant").indices
parts = np.array(list(idx))


def boot(fn):
    est = fn(D)
    v = []
    for _ in range(B):
        pk = rng.choice(parts, len(parts))
        v.append(fn(D.iloc[np.concatenate([idx[p] for p in pk])]))
    v = np.array(v, dtype=float)
    return [float(est), float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]


def pmed(X, col, ref):
    return (X[col] - X[ref]).abs().groupby(X.participant).median().median()


def pmed_diff(X, a, b, ref):
    return ((X[a] - X[ref]).abs() - (X[b] - X[ref]).abs()).groupby(X.participant).median().median()


def pbig(X, col, ref):
    return 100 * ((X[col] - X[ref]).abs() > 5).mean()


R = {"n_segments": int(len(D)), "n_participants": int(D.participant.nunique()), "sr_rule": SR_RULE}
# (a) stride-defined reference
R["stride_ref"] = {}
for est in ("peak", "ags"):
    R["stride_ref"][est] = {
        "HE_med": boot(lambda X: pmed(X, f"HE_{est}", "R_stride")),
        "LB_med": boot(lambda X: pmed(X, f"LB_{est}", "R_stride")),
        "HE-LB_med": boot(lambda X: pmed_diff(X, f"HE_{est}", f"LB_{est}", "R_stride")),
        "HE_big": boot(lambda X: pbig(X, f"HE_{est}", "R_stride")),
        "LB_big": boot(lambda X: pbig(X, f"LB_{est}", "R_stride")),
        "HE-LB_big": boot(lambda X: pbig(X, f"HE_{est}", "R_stride") - pbig(X, f"LB_{est}", "R_stride")),
    }
R["ref_def_disagree_gt5_pct"] = float(100 * ((D.R_step - D.R_stride).abs() > 5).mean())

# (b) envelope cost by VGA level (head and lower back; AGS errors)
D["vga_lvl"] = D.vga.clip(upper=3)
R["vga"] = {}
for loc in ("HE", "LB"):
    r = {}
    for lv in (0, 1, 2, 3):
        m = D.vga_lvl == lv
        sub = D[m]
        r[str(lv)] = {
            "n_seg": int(m.sum()), "n_part": int(sub.participant.nunique()),
            "excluded": boot(lambda X, lv=lv: 100 * (~X[f"{loc}_in"][X.vga_lvl == lv]).mean()),
            "false_excl": boot(lambda X, lv=lv: 100 * (~X[f"{loc}_in"][(X.vga_lvl == lv) & ~X[f"{loc}_ags_big"]]).mean()),
            "big_in": boot(lambda X, lv=lv: 100 * X[f"{loc}_ags_big"][(X.vga_lvl == lv) & X[f"{loc}_in"]].mean()),
            "big_all": boot(lambda X, lv=lv: 100 * X[f"{loc}_ags_big"][X.vga_lvl == lv].mean()),
            "sens": boot(lambda X, lv=lv: 100 * (~X[f"{loc}_in"][(X.vga_lvl == lv) & X[f"{loc}_ags_big"]]).mean()),
        }
    R["vga"][loc] = r
    R.setdefault("overall", {})[loc] = {
        "excluded": boot(lambda X: 100 * (~X[f"{loc}_in"]).mean()),
        "false_excl": boot(lambda X: 100 * (~X[f"{loc}_in"][~X[f"{loc}_ags_big"]]).mean()),
        "sens": boot(lambda X: 100 * (~X[f"{loc}_in"][X[f"{loc}_ags_big"]]).mean()),
        "big_in": boot(lambda X: 100 * X[f"{loc}_ags_big"][X[f"{loc}_in"]].mean()),
        "big_in_peak": boot(lambda X: 100 * X[f"{loc}_peak_big"][X[f"{loc}_in"]].mean()),
    }

# (c) which large errors the head rule flags, by where they occur
R["flag_by_source"] = {}
for est in ("peak", "ags"):
    hb, lbb = f"HE_{est}_big", f"LB_{est}_big"
    both = lambda X: X[hb] & X[lbb]
    honly = lambda X: X[hb] & ~X[lbb]
    R["flag_by_source"][est] = {
        "n_both": int(both(D).sum()), "n_head_only": int(honly(D).sum()),
        "both": boot(lambda X: 100 * (~X.HE_in[both(X)]).mean()),
        "head_only": boot(lambda X: 100 * (~X.HE_in[honly(X)]).mean()),
        "diff": boot(lambda X: 100 * (~X.HE_in[both(X)]).mean() - 100 * (~X.HE_in[honly(X)]).mean()),
    }

# (d) where the head large errors removed by AGS come from (segment counts)
R["head_big_drop_by_cohort"] = {c: int(g.HE_peak_big.sum() - g.HE_ags_big.sum()) for c, g in D.groupby("cohort")}

with open(OUT, "w") as f:
    json.dump(R, f, indent=1)
print(json.dumps({k: v for k, v in R.items()}, indent=1)[:6000])
