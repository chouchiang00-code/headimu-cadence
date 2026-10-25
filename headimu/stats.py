"""Participant-level statistics: bootstrap CIs, Bland-Altman with repeated measures,
Holm correction, ICC(A,1), SEM and a nested variance decomposition."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def participant_agg(df: pd.DataFrame, value: str, by=("participant",), how="median") -> pd.Series:
    g = df.dropna(subset=[value]).groupby(list(by))[value]
    return g.median() if how == "median" else g.mean()


def boot_ci(x: np.ndarray, fn=np.median, B=2000, ci=0.95, seed=0):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if x.size < 3:
        return (fn(x) if x.size else np.nan, np.nan, np.nan, int(x.size))
    rng = np.random.default_rng(seed)
    bs = np.array([fn(x[rng.integers(0, x.size, x.size)]) for _ in range(B)])
    lo, hi = np.percentile(bs, [(1 - ci) / 2 * 100, (1 + ci) / 2 * 100])
    return float(fn(x)), float(lo), float(hi), int(x.size)


def paired_compare(a: pd.Series, b: pd.Series, B=2000, seed=0):
    """Participant-level paired comparison of two series indexed by participant."""
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    d = (j["a"] - j["b"]).to_numpy()
    est, lo, hi, n = boot_ci(d, np.median, B, seed=seed)
    p = stats.wilcoxon(j["a"], j["b"]).pvalue if n >= 6 and np.any(d != 0) else np.nan
    return {"n": n, "median_diff": est, "ci_lo": lo, "ci_hi": hi, "p_wilcoxon": p}


def holm(p: list[float]) -> list[float]:
    p = np.asarray(p, float)
    out = np.full_like(p, np.nan)
    ok = np.isfinite(p)
    idx = np.argsort(p[ok])
    pv = p[ok][idx]
    m = len(pv)
    adj = np.maximum.accumulate(np.minimum(1, (m - np.arange(m)) * pv))
    tmp = np.empty(m)
    tmp[idx] = adj
    out[ok] = tmp
    return out.tolist()


def bland_altman_repeated(df: pd.DataFrame, a: str, b: str, subj="participant"):
    """Bland & Altman (2007), multiple observations per individual, true value varying.
    Returns bias, LoA and the components."""
    d = (df[a] - df[b]).to_numpy()
    s = df[subj].to_numpy()
    ok = np.isfinite(d)
    d, s = d[ok], s[ok]
    if d.size < 5:
        return {"n_obs": int(d.size)}
    groups = pd.Series(d).groupby(s)
    k = groups.ngroups
    N = d.size
    mi = groups.size().to_numpy()
    means = groups.mean().to_numpy()
    grand = d.mean()
    ssb = np.sum(mi * (means - grand) ** 2)
    ssw = np.sum((d - groups.transform("mean").to_numpy()) ** 2)
    msb = ssb / (k - 1) if k > 1 else 0
    msw = ssw / (N - k) if N > k else 0
    div = (N ** 2 - np.sum(mi ** 2)) / ((k - 1) * N) if k > 1 else 1
    s2b = max(0.0, (msb - msw) / div)
    sd = np.sqrt(s2b + msw)
    return {"n_obs": int(N), "n_participants": int(k), "bias": float(grand), "sd_total": float(sd),
            "loa_lo": float(grand - 1.96 * sd), "loa_hi": float(grand + 1.96 * sd),
            "sd_between": float(np.sqrt(s2b)), "sd_within": float(np.sqrt(msw))}


def icc_a1(X: np.ndarray):
    """ICC(A,1): two-way random effects, absolute agreement, single measurement
    (McGraw & Wong; Koo & Li 2016). X: n subjects x k sessions, complete rows only."""
    X = X[np.isfinite(X).all(1)]
    n, k = X.shape
    if n < 3:
        return {"n": int(n), "icc": np.nan}
    gm = X.mean()
    msr = k * np.sum((X.mean(1) - gm) ** 2) / (n - 1)
    msc = n * np.sum((X.mean(0) - gm) ** 2) / (k - 1)
    sse = np.sum((X - X.mean(1, keepdims=True) - X.mean(0, keepdims=True) + gm) ** 2)
    mse = sse / ((n - 1) * (k - 1))
    icc = (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)
    sd = np.sqrt(np.sum((X - X.mean()) ** 2) / (X.size - 1))
    sem = sd * np.sqrt(max(0.0, 1 - icc))
    return {"n": int(n), "icc": float(icc), "sem": float(sem), "mdc95": float(1.96 * np.sqrt(2) * sem)}


def icc_boot(X: np.ndarray, B=2000, seed=0):
    X = X[np.isfinite(X).all(1)]
    base = icc_a1(X)
    if X.shape[0] < 5:
        return {**base, "ci_lo": np.nan, "ci_hi": np.nan}
    rng = np.random.default_rng(seed)
    v = [icc_a1(X[rng.integers(0, len(X), len(X))])["icc"] for _ in range(B)]
    lo, hi = np.nanpercentile(v, [2.5, 97.5])
    return {**base, "ci_lo": float(lo), "ci_hi": float(hi)}


def nested_variance(df: pd.DataFrame, value: str):
    """Method-of-moments decomposition of `value` into participant, visit-within-participant
    and residual (trial) variance, for participants with >= 2 visits."""
    d = df.dropna(subset=[value])
    w_ss = w_df = 0.0
    vis_terms, pmeans = [], []
    for _, gp in d.groupby("participant"):
        vm, vn = [], []
        for _, gv in gp.groupby("visit"):
            x = gv[value].to_numpy()
            if len(x) >= 2:
                w_ss += np.sum((x - x.mean()) ** 2)
                w_df += len(x) - 1
            vm.append(x.mean())
            vn.append(len(x))
        if len(vm) >= 2:
            vis_terms.append((np.var(vm, ddof=1), np.mean(1.0 / np.array(vn))))
            pmeans.append((np.mean(vm), len(vm), np.mean(vn)))
    if not vis_terms or w_df == 0:
        return {"n_participants": len(vis_terms)}
    s2w = w_ss / w_df
    s2v = max(0.0, float(np.mean([v - s2w * inv for v, inv in vis_terms])))
    pm = np.array([p[0] for p in pmeans])
    nv = np.mean([p[1] for p in pmeans])
    nt = np.mean([p[2] for p in pmeans])
    s2p = max(0.0, float(np.var(pm, ddof=1) - s2v / nv - s2w / (nv * nt))) if len(pm) > 1 else np.nan
    return {"n_participants": len(vis_terms), "var_participant": s2p, "var_visit": s2v, "var_residual": s2w}
