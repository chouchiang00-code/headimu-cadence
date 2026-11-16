"""Extract two example straight segments (head A1, B0 pipeline) for Fig. 4(c, d): band-passed signal, detected steps
(lag-corrected as in the evaluation), reference heel strikes, and the published segment errors.
Usage: python analysis/v17_fig_examples.py RESULTS_V11 PACK.npz TRUST_DIR OUT.npz TRIAL:SEG [TRIAL:SEG ...]"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis import v17_reviewer_checks as rc  # noqa: E402
from headimu import pipeline as pl  # noqa: E402
from headimu.evaluate import candidates  # noqa: E402

# Command-line diagnostics only; analysis statements remain unchanged.
if __name__ == "__main__" and (len(sys.argv) == 1 or "--help" in sys.argv[1:] or "-h" in sys.argv[1:]):
    print('Usage: python analysis/v17_fig_examples.py RESULTS_V11 PACK.npz TRUST_DIR OUT.npz TRIAL:SEG [TRIAL:SEG ...]')
    raise SystemExit(0 if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] else 2)

r11, pack, tr_dir, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), sys.argv[4]
cfg = json.loads((r11 / "config_used.json").read_text(encoding="utf-8"))
cal = json.loads((r11 / "dev_calibration.json").read_text(encoding="utf-8"))
rc._init("pack", pack, cfg)
pub = pd.read_csv(r11 / "test_segments.csv"); pub = pub[pub["method"] == "A1"]
sc = pd.read_csv(tr_dir / "trust_test_scored.csv")
res = {}
for k, spec in enumerate(sys.argv[5:]):
    t, sname = spec.split(":")
    tr = rc._load(t); fs = tr.fs; s = tr.sensors["HE"]
    w = pl.windows(tr, fs, cfg["detect"]["window_pad_s"]); a, b = w["segs"][sname]
    st = pl.static_slice(tr, fs, s.acc.shape[0], cfg["qc"]["min_static_s"])
    sig, _ = pl.branch_signals(s.acc, s.gyr, fs, cfg, float(cal["band_lo_hz"]), static=st, which=("A1",))
    i0, i1 = max(0, int(w["full"][0] * fs)), min(len(s.valid), int(w["full"][1] * fs))
    c = candidates(sig["A1"], fs, cfg, i0, i1, s.valid) - cal["lags_s"]["HE_A1"]
    c = c[(c >= a - 0.1) & (c <= b + 0.1)]
    hs = tr.hs[(tr.hs >= a) & (tr.hs <= b)]
    j0, j1 = int(a * fs), int(b * fs) + 1
    tt = np.arange(j0, j1) / fs
    x = sig["A1"][j0:j1]
    # step markers drawn on the lag-shifted signal value
    cx = np.interp(c + cal["lags_s"]["HE_A1"], np.arange(len(sig["A1"])) / fs, sig["A1"])
    g = lambda loc: float(pub[(pub["trial"] == t) & (pub["segment"] == sname) & (pub["loc"] == loc)]["e_C"].iloc[0])
    r = sc[(sc["trial"] == t) & (sc["segment"] == sname)].iloc[0]
    res.update({f"{k}_t": tt - a, f"{k}_x": x, f"{k}_c": c - a, f"{k}_cx": cx, f"{k}_hs": hs - a,
                f"{k}_meta": json.dumps({"trial": t, "segment": sname, "cohort": tr.cohort, "e_head": g("HE"),
                                         "e_lb": g("LB"), "C_ref": float(r["C_ref"]), "sr_seg": float(r["sr_seg"]),
                                         "n_ref": int(len(hs)), "n_det": int(len(c)), "dur": float(b - a)})})
    print(res[f"{k}_meta"])
np.savez(out, **res)
