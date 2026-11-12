"""Check headimu.eargait_diao.ssa_components against the SSA kernel of pyts (used by EarGait).

Usage: python tests/check_eargait_ssa_vs_pyts.py PATH_TO_PYTS_CLONE
       (git clone https://github.com/johannfaouzi/pyts). numba is stubbed so the kernel runs in pure Python.
"""
import sys
import types
from pathlib import Path

import numpy as np

nb = types.ModuleType("numba"); nb.njit = lambda *a, **k: (lambda f: f); nb.prange = range
sys.modules["numba"] = nb
pyts = Path(sys.argv[1] if len(sys.argv) > 1 else "../ext_src/pyts")
src = (pyts / "pyts" / "decomposition" / "_ssa.py").read_text()
ns = {}
exec(compile("import numpy as np\nimport numpy.typing as npt\nfrom numba import njit, prange\n"
             + src[src.index("@njit"):src.index("class SingularSpectrumAnalysis")], "ssa", "exec"), ns)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from headimu.eargait_diao import ssa_components  # noqa: E402

rng = np.random.default_rng(0)
t = np.arange(600) / 100
x = 9.8 + np.sin(2 * np.pi * 1.8 * t) + 0.3 * np.sin(2 * np.pi * 0.9 * t) + 0.2 * rng.standard_normal(600)
L, N = 100, 600; K = N - L + 1
Xw = np.array([x[i:i + L] for i in range(K)]).T[None]
w, v = np.linalg.eigh(Xw[0] @ Xw[0].T); v = v[:, ::-1][None]
memb = np.zeros((1, 4, L)); memb[0, 0, 0] = memb[0, 1, 1] = memb[0, 2, 2] = 1; memb[0, 3, 3:] = 1
ref = ns["_ssa_fused"](v, Xw, memb, 1, N, L, K, 4)[0]
diff = np.abs(ref[:3] - ssa_components(x, L, (0, 1, 2))).max()
print("max abs difference, components 0-2:", diff)
assert diff < 1e-9
