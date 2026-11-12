#!/usr/bin/env python3
"""V16 post hoc: errors relative to the smallest detectable change of cadence.

Usage: python v16_post_clinical.py RESULTS_V11 E2E_DIR POST_DIR
Anchors: MDC 15.1 steps/min (comfortable 10-m walk, Parkinson's disease; Lang et al., J Geriatr Phys Ther 2016) and the
cross-visit MDC95 of this study (numbers_for_paper.json, same-system pairs). Reports, per pipeline, the share of test
segments whose |e_C| exceeds each anchor (all and CVA) and the median |e_C| as a fraction of each anchor.
Writes POST_DIR/clinical_summary.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Command-line diagnostics only; analysis statements are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/v16_post_clinical.py RESULTS_V11 E2E_DIR POST_DIR')
        raise SystemExit(0)
    if len(sys.argv) < 4:
        print('Usage: python analysis/v16_post_clinical.py RESULTS_V11 E2E_DIR POST_DIR', file=sys.stderr)
        raise SystemExit(2)


r11, e2e, post = map(Path, sys.argv[1:4])
nb = json.loads((r11 / "numbers_for_paper.json").read_text())["rewear"]
mdc_head = nb["same_sensor_pairs_HE_A1"]["imu"]["mdc95"]; mdc_ref = nb["same_sensor_pairs_HE_A1"]["ref"]["mdc95"]
anchors = {"lang2016_PD": 15.1, "crossvisit_head_A1": mdc_head, "crossvisit_reference": mdc_ref}
e = pd.read_csv(e2e / "endtoend_segments.csv"); e = e[(e["set"] == "test") & np.isfinite(e["C_ref"])]
out = {"anchors_spm": {k: round(v, 2) for k, v in anchors.items()}, "pipelines": {}}
for c in ("B0_e", "B1_e", "B2_e", "B2t_e"):
    x = e[c]; med = float(e.assign(a=x.abs()).groupby("participant")["a"].median().median())
    out["pipelines"][c[:-2]] = {
        "median_abs_err": round(med, 2),
        **{f"median_over_{k}": round(med / v, 3) for k, v in anchors.items()},
        **{f"pct_exceeding_{k}": round(100 * float((x.abs() > v).mean()), 2) for k, v in anchors.items()},
        **{f"pct_exceeding_{k}_CVA": round(100 * float((e.loc[e["cohort"] == "CVA", c].abs() > v).mean()), 1) for k, v in anchors.items()}}
(post / "clinical_summary.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
