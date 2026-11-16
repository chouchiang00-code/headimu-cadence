"""V18 method development: extract per-trial signals for one split only (default: development set).
Stores, per trial, the band-passed A1 signal (dev-selected band), raw acc/gyr, validity, the two reference straight
segments and reference heel strikes, so that candidate estimators can be developed without touching the test set.
Usage: python analysis/v18_extract.py RESULTS_V11 PACK.npz OUT.pkl [--set dev|test] [--loc HE]"""
import json, pickle, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis import v17_reviewer_checks as rc  # noqa: E402
from headimu import pipeline as pl  # noqa: E402
from headimu.features import signals  # noqa: E402

# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v18_extract.py RESULTS_V11 PACK.npz OUT.pkl [--set dev|test] [--loc HE]')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

a = sys.argv[1:]
r11, src, out = Path(a[0]), a[1], a[2]
split = a[a.index("--set") + 1] if "--set" in a else "dev"
loc = a[a.index("--loc") + 1] if "--loc" in a else "HE"
mode = "root" if "--root" in a else "pack"
cfg = json.loads((r11 / "config_used.json").read_text(encoding="utf-8"))
cal = json.loads((r11 / "dev_calibration.json").read_text(encoding="utf-8"))
qc = pd.read_csv(r11 / "qc_trials.csv")
qc = qc[(qc["exclusion"].fillna("") == "") & (qc["set"] == split)]
rc._init(mode, src, cfg)
D = []
for t in qc["trial"]:
    tr = rc._load(t); fs = tr.fs
    if loc not in tr.sensors:
        continue
    s = tr.sensors[loc]
    w = pl.windows(tr, fs, cfg["detect"]["window_pad_s"])
    if w is None:
        continue
    sig = signals(s.acc, s.gyr, fs, cfg, float(cal["band_lo_hz"]))
    D.append({"trial": t, "participant": tr.participant, "cohort": tr.cohort, "fs": fs, "loc": loc,
              "A1": sig["A1"].astype(np.float32), "v": sig["v"].astype(np.float32), "wh": sig["wh"].astype(np.float32),
              "valid": s.valid, "full": w["full"], "segs": w["segs"], "hs": tr.hs, "hs_left": tr.hs_left,
              "hs_right": tr.hs_right})
pickle.dump({"split": split, "loc": loc, "cfg": cfg, "cal": cal, "trials": D}, open(out, "wb"))
print(split, loc, len(D), "trials", len({d['participant'] for d in D}), "participants")
