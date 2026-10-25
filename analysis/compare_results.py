#!/usr/bin/env python3
"""Compare two result folders (e.g. a fresh re-run against the delivered results_v16): every CSV and JSON file present
in both is compared numerically; prints the maximum absolute difference per file and lists files present in only one.

Usage: python compare_results.py REFERENCE_DIR RERUN_DIR [--tol 1e-9]
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def flat(x, pre=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from flat(v, f"{pre}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from flat(v, f"{pre}[{i}]")
    else:
        yield pre, x


def cmp_json(a, b):
    fa, fb = dict(flat(json.loads(a.read_text()))), dict(flat(json.loads(b.read_text())))
    worst, bad = 0.0, []
    for k in set(fa) | set(fb):
        x, y = fa.get(k, "<missing>"), fb.get(k, "<missing>")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
            if np.isnan(x) and np.isnan(y):
                continue
            worst = max(worst, abs(x - y) if np.isfinite(x - y) else np.inf)
        elif x != y:
            bad.append(k)
    return worst, bad


def cmp_csv(a, b):
    x, y = pd.read_csv(a), pd.read_csv(b)
    if list(x.columns) != list(y.columns) or len(x) != len(y):
        return np.inf, [f"shape/columns differ {x.shape} vs {y.shape}"]
    worst, bad = 0.0, []
    for c in x.columns:
        if pd.api.types.is_numeric_dtype(x[c]) and pd.api.types.is_numeric_dtype(y[c]):
            u, v = x[c].to_numpy(float), y[c].to_numpy(float)
            if not np.array_equal(np.isnan(u), np.isnan(v)):
                bad.append(f"{c}: NaN pattern")
                continue
            m = np.isfinite(u)
            if m.any():
                worst = max(worst, float(np.max(np.abs(u[m] - v[m]))))
        elif not x[c].astype(str).equals(y[c].astype(str)):
            bad.append(c)
    return worst, bad


def main():
    ref, new = Path(sys.argv[1]), Path(sys.argv[2])
    tol = float(sys.argv[sys.argv.index("--tol") + 1]) if "--tol" in sys.argv else 1e-9
    files_r = {p.relative_to(ref) for p in ref.rglob("*") if p.suffix in (".csv", ".json")}
    files_n = {p.relative_to(new) for p in new.rglob("*") if p.suffix in (".csv", ".json")}
    n_ok = 0
    for f in sorted(files_r & files_n):
        worst, bad = (cmp_json if f.suffix == ".json" else cmp_csv)(ref / f, new / f)
        ok = worst <= tol and not bad
        n_ok += ok
        print(f"{'OK  ' if ok else 'DIFF'} {f}  max|diff| = {worst:.3g}" + (f"  non-numeric differences: {bad[:5]}" if bad else ""))
    for f in sorted(files_r - files_n):
        print(f"ONLY IN REFERENCE {f}")
    for f in sorted(files_n - files_r):
        print(f"ONLY IN RE-RUN    {f}")
    print(f"{n_ok} of {len(files_r & files_n)} common files identical within {tol:g}")


# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python analysis/compare_results.py REFERENCE_DIR NEW_DIR [--tol VALUE]')
        raise SystemExit(0)
    if len(sys.argv) < 3:
        print('Usage: python analysis/compare_results.py REFERENCE_DIR NEW_DIR [--tol VALUE]', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
