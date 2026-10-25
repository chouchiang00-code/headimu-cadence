"""Extra V16 trust statistics: Q1 AUROC on segments with SR, and participant-bootstrap CIs for the VGA>=3 / CVA
false-exclusion and retention differences between Q2 variants and Q1. Usage: python v16_trust_extra.py TRUST_DIR"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from run_v16_trust import auc, auprc, boot
# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/v16_trust_extra.py TRUST_DIR')
        raise SystemExit(0)
    if len(sys.argv) < 2:
        print('Usage: python analysis/v16_trust_extra.py TRUST_DIR', file=sys.stderr)
        raise SystemExit(2)


D = Path(sys.argv[1])
t = pd.read_csv(D / "trust_test_scored.csv")
X = {}
q = t[np.isfinite(t["sr_trial"])]
X["Q1_auroc"] = [auc(q["big"], -q["sr_trial"]), boot(lambda b: auc(b["big"], -b["sr_trial"]), q)]
X["Q1_auprc"] = [auprc(q["big"], -q["sr_trial"]), boot(lambda b: auprc(b["big"], -b["sr_trial"]), q)]
X["n_Q1"] = len(q)
def fe(b, flag):  # false exclusion: flagged among segments without large error
    nb = b[b["big"] == 0]
    return 100 * nb[flag].mean() if len(nb) else np.nan
def ret(b, flag):
    return 100 * (1 - b[flag].mean())
for name, sel in (("vga3", t["vga"] >= 3), ("CVA", t["cohort"] == "CVA")):
    g = t[sel]
    for m in ("Q2b_SR_segment_flag", "Q2c_SR_plus_2_flag", "Q2d_full_flag"):
        X[f"{name}_{m}_false_excl_diff_vs_Q1"] = [fe(g, m) - fe(g, "Q1_flag"), boot(lambda b: fe(b, m) - fe(b, "Q1_flag"), g)]
        X[f"{name}_{m}_retained_diff_vs_Q1"] = [ret(g, m) - ret(g, "Q1_flag"), boot(lambda b: ret(b, m) - ret(b, "Q1_flag"), g)]
    X[f"{name}_n_segments_participants"] = [len(g), int(g["participant"].nunique())]
(D / "trust_extra.json").write_text(json.dumps(X, indent=1, default=float))
print(json.dumps(X, indent=1, default=float))
