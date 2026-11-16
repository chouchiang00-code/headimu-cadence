"""Participant-bootstrap 95% CIs for the V17 figures (post hoc, descriptive).
fig4 (failure): share of |e_C|>5 by head segment-SR bin, head and lower back.
fig5 (screening): large-error share among kept segments vs fraction removed (Q1 = -sr_trial, keep_by_risk as in
run_v16_trust.py); overall large-error share (random removal); excluded and false-exclusion shares by VGA level
(false exclusion = flagged among segments without a large error, as in trust_operating_points.csv).
Usage: python analysis/v17_fig_cis.py RESULTS_V11 TRUST_DIR OUT_JSON"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v17_fig_cis.py RESULTS_V11 TRUST_DIR OUT_JSON')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

R11, TR, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
B, rng = 2000, np.random.default_rng(20261112)
seg = pd.read_csv(R11 / "test_segments.csv")
a1 = seg[(seg["method"] == "A1") & np.isfinite(seg["e_C"])]
lb = a1[a1["loc"] == "LB"][["trial", "segment", "e_C"]].rename(columns={"e_C": "e_lb"})
test = pd.read_csv(TR / "trust_test_scored.csv")
test["vga_lvl"] = test["vga"].clip(upper=3)
J = test[["trial", "segment", "participant", "sr_seg", "e_C"]].rename(columns={"e_C": "e_head"}).merge(lb, on=["trial", "segment"])
J = J[np.isfinite(J["sr_seg"])].copy()
edges = [-np.inf, 0.4, 0.6, 0.8, 0.9, np.inf]
labs = ["<0.4", "0.4–0.6", "0.6–0.8", "0.8–0.9", "≥0.9"]
J["bin"] = pd.cut(J["sr_seg"], edges, labels=labs, right=False).astype(str)
J["bh"], J["bl"] = J["e_head"].abs() > 5, J["e_lb"].abs() > 5
REM = np.arange(0, 41, 1)


def keep_by_risk(risk, cov):
    n = len(risk); k = int(round(cov * n)); o = np.argsort(risk, kind="stable"); m = np.zeros(n, bool); m[o[:k]] = True
    return m


def stats_fail(d):
    g = d.groupby("bin")
    return {f"{b}|{w}": 100 * g[c].mean().get(b, np.nan) for b in labs for w, c in (("head", "bh"), ("lb", "bl"))}


def stats_screen(d):
    r = {"base": 100 * d["big"].mean()}
    risk, big = -d["sr_trial"].to_numpy(), d["big"].to_numpy().astype(bool)
    ok = np.isfinite(risk)
    for x in REM:
        k = keep_by_risk(risk[ok], 1 - x / 100)
        r[f"q1|{x}"] = 100 * big[ok][k].mean()
    for v, g in d.groupby("vga_lvl"):
        f, y = g["Q1_flag"].astype(bool), g["big"].astype(bool)
        r[f"excl|{int(v)}"] = 100 * f.mean()
        r[f"fex|{int(v)}"] = 100 * f[~y].mean() if (~y).any() else np.nan
    return r


def boot(df, fn):
    est = fn(df)
    parts = df["participant"].unique(); idx = {p: i for p, i in df.groupby("participant").indices.items()}
    draws = []
    for _ in range(B):
        pick = rng.choice(parts, len(parts), replace=True)
        draws.append(fn(df.iloc[np.concatenate([idx[p] for p in pick])]))
    D = pd.DataFrame(draws)
    return {k: [est[k], float(np.nanpercentile(D[k], 2.5)), float(np.nanpercentile(D[k], 97.5))] for k in est}


out = {"fail": boot(J, stats_fail), "screen": boot(test, stats_screen),
       "n_bin": J.groupby("bin").size().to_dict(),
       "n_bin_participants": J.groupby("bin")["participant"].nunique().to_dict(),
       "vga": {int(v): {"segments": len(g), "participants": int(g["participant"].nunique()),
                        "no_large_error": int((~g["big"].astype(bool)).sum()),
                        "flagged": int(g["Q1_flag"].sum()),
                        "flagged_no_large_error": int((g["Q1_flag"].astype(bool) & ~g["big"].astype(bool)).sum())}
               for v, g in test.groupby("vga_lvl")}}
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float))
print(json.dumps({k: out[k] for k in ("n_bin", "n_bin_participants", "vga")}, ensure_ascii=False, indent=0))
for k, v in out["fail"].items(): print(k, [round(x, 1) for x in v])
for k in ["base", "q1|0", "q1|5", "q1|10", "q1|20", "q1|40"] + [f"{a}|{v}" for a in ("excl", "fex") for v in range(4)]:
    print(k, [round(x, 2) for x in out["screen"][k]])
