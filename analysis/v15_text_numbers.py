"""Recompute, from results_v11 outputs, the descriptive numbers quoted in the V15 text that were first obtained
interactively (audit for V16). Usage: python v15_text_numbers.py RESULTS_V11"""
import sys, json
import numpy as np, pandas as pd
# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/v15_text_numbers.py RESULTS_V11')
        raise SystemExit(0)
    if len(sys.argv) < 2:
        print('Usage: python analysis/v15_text_numbers.py RESULTS_V11', file=sys.stderr)
        raise SystemExit(2)


R = sys.argv[1]
seg = pd.read_csv(f"{R}/test_segments.csv"); qc = pd.read_csv(f"{R}/qc_trials.csv")
he = seg[(seg["loc"] == "HE") & (seg.method == "A1")].copy(); lb = seg[(seg["loc"] == "LB") & (seg.method == "A1")].copy()
he = he[np.isfinite(he.e_C)]
out = {}
a = he.e_C.abs()
out["n_segments"] = len(he)
out["pct_zero_error"] = 100 * (a < 1e-6).mean()
out["pct_le_2p5"] = 100 * (a <= 2.5).mean()
out["pct_gt5"] = 100 * (a > 5).mean()
out["pct_gt5_by_cohort"] = (he.assign(b=a > 5).groupby("cohort").b.mean() * 100).round(1).to_dict()
out["halving_by_cohort_max_pct"] = float((he.groupby("cohort").halving.mean() * 100).max())
m = he.merge(lb[["trial", "segment", "e_C"]], on=["trial", "segment"], suffixes=("", "_lb"))
bh, bl = m.e_C.abs() > 5, m.e_C_lb.abs() > 5
out["overlap_both_headonly_lbonly"] = [int((bh & bl).sum()), int((bh & ~bl).sum()), int((~bh & bl).sum())]
big = he[a > 5]
out["median_ratio_big"] = float(big.ratio.median())
sr = qc.set_index("trial")["HE_step_regularity"]
out["median_SR_big_vs_rest"] = [float(sr.reindex(big.trial).median()), float(sr.reindex(he[a <= 5].trial).median())]
out["median_nref_big_vs_rest"] = [float(big.n_ref.median()), float(he[a <= 5].n_ref.median())]
ok = he[a <= 5].e_C
out["loa_without_big_segment_level"] = [float(ok.mean() - 1.96 * ok.std()), float(ok.mean() + 1.96 * ok.std())]
out["median_step_time_s"] = float(he.T_ref.median())
out["one_sample_quantization_spm_at_median"] = float(60 / he.T_ref.median() - 60 / (he.T_ref.median() + 0.01))
print(json.dumps(out, indent=1, default=float))
