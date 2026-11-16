"""V17, POST HOC: share of segments flagged by the SR screen (Q1, sr_trial < 0.32) by large-error location
(both / head only / LB only / neither; B0 A1 test set), participant bootstrap 95% CIs (2000).
Usage: python analysis/v17_flag_by_kind.py TRUST_DIR HEAD_TRUNK_DIR"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v17_flag_by_kind.py TRUST_DIR HEAD_TRUNK_DIR')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

t = pd.read_csv(Path(sys.argv[1]) / "trust_test_scored.csv")
D = pd.read_csv(Path(sys.argv[2]) / "head_trunk_segments.csv")
J = D[["trial", "segment", "kind", "participant"]].merge(t[["trial", "segment", "Q1_flag"]], on=["trial", "segment"])
f = lambda d: {**{k: 100 * g["Q1_flag"].mean() for k, g in d.groupby("kind")}}
est = f(J); rng = np.random.default_rng(20261112); parts = J["participant"].unique(); idx = J.groupby("participant").indices
dr = []
for _ in range(2000):
    pk = rng.choice(parts, len(parts), replace=True); d = J.iloc[np.concatenate([idx[p] for p in pk])]
    r = f(d); r["both-head_only"] = r.get("both", np.nan) - r.get("head_only", np.nan); dr.append(r)
dr = pd.DataFrame(dr); est["both-head_only"] = est["both"] - est["head_only"]
out = {k: [float(est[k]), float(np.nanpercentile(dr[k], 2.5)), float(np.nanpercentile(dr[k], 97.5))] for k in est}
out["n"] = J.groupby("kind").size().to_dict()
(Path(sys.argv[2]) / "flag_by_kind.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=0))
