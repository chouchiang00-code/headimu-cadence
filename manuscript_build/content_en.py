# -*- coding: utf-8 -*-
"""English IEEE manuscript content (V16) = refs_part.py + body_v16.py, with supplement markers resolved.
Inline markup: ⟦key,key⟧ citation; *italic*; **bold**; _{sub}; ^{sup}; [[placeholder]] (yellow).
Supplement markers: ⟪T:key⟫ / ⟪F:key⟫ (numbered by first mention, see content_supp.py)."""
import re
from pathlib import Path

_HERE = Path(__file__).resolve().parent
exec(compile((_HERE / "refs_part.py").read_text(encoding="utf-8"), "refs_part.py", "exec"))
ref("duogait", "L. Zhou, E. Fischer, C. M. Brahms, U. Granacher, and B. Arnrich, “DUO-GAIT: A gait dataset for walking under "
    "dual-task and fatigue conditions with inertial measurement units,” *Sci. Data*, vol. 10, Art. no. 543, 2023, "
    "doi: 10.1038/s41597-023-02391-w.")
ref("duogait_data", "L. Zhou, E. Fischer, M. C. Brahms, U. Granacher, and B. Arnrich, “DUO-GAIT: A gait dataset for walking "
    "under dual-task and fatigue conditions with inertial measurement units,” Zenodo, ver. 3, data set, 2022, "
    "doi: 10.5281/zenodo.8244887.")
import os as _os
_BODY = _os.environ.get("BODY_EN", "body_v16.py")
exec(compile((_HERE / _BODY).read_text(encoding="utf-8"), _BODY, "exec"))

import content_supp as _S  # noqa: E402

GRAPHICAL_ABSTRACT = globals().get("GA_PATH", "fig_v16/graphical_abstract_compact.png")


def _res(x):
    if isinstance(x, str):
        return _S.resolve(x) if "⟪" in x else x
    if isinstance(x, tuple):
        return tuple(_res(y) for y in x)
    if isinstance(x, list):
        return [_res(y) for y in x]
    return x


ABSTRACT, B, TAIL, INDEX, FOOTNOTE = _res(ABSTRACT), _res(B), _res(TAIL), _res(INDEX), _res(FOOTNOTE)
_cited = set()
for _s in re.findall(r"⟦([^⟧]+)⟧", repr((ABSTRACT, B, TAIL))):
    _cited.update(k.strip() for k in _s.split(","))
_missing = _cited - set(R)
assert not _missing, _missing
R = {k: v for k, v in R.items() if k in _cited}
