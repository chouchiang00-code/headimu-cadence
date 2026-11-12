"""Compact graphical abstract for the first page (readable at ~3.1 in wide: every text >= 46 px at 1448 px = ~7 pt).
Person artwork reused from head-imu-cadence-revised.svg (traced figure with the repairs). Numbers as in the manuscript:
B0 1.53 steps/min (1.5%); B1 1.56, equivalent to B0 (post hoc TOST); SR AUROC 0.90, up to 0.92 (SR+2);
DUO-GAIT B1 0.70 steps/min, 16 healthy adults; B2 bias +2.2 steps/min, step confirmation 0.35 s."""
import re
from xml.sax.saxutils import escape
from PIL import ImageFont
R = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"; BD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
W = lambda t, s, b=False: ImageFont.truetype(BD if b else R, s).getlength(t)
src = open('head-imu-cadence-revised.svg').read()
defs = src[src.index('<defs>'):src.index('</defs>') + 7]
# drop the traced leader of the old "foot IMUs" callout (no callout on this compact figure)
_orig = open('fig.svg').read(); _g0 = _orig.index('<g id="traced-artwork">'); _g1 = _orig.index('</g>', _g0)
_items = re.findall(r'<path d="[^"]*" fill="#[0-9A-Fa-f]{6}" transform="translate\([-\d.]+,[-\d.]+\)" />', _orig[_g0:_g1])
for k in (32, 81, 89, 96, 174, 186, 191, 200, 230, 290):
    assert defs.count(_items[k]) == 1, k
    defs = defs.replace(_items[k], "")
person = src[src.index('<g id="person">'):]
person = person[:person.index('</g>') + 4]
NAVY, TEAL, GOLD, RED, GREY, INK = "#07366c", "#007367", "#a87900", "#c8202a", "#3e4b5b", "#0b1530"
F = 'font-family="Arial, Helvetica, sans-serif"'
def T(x, y, t, sz, fill, bold=False, anchor="start"):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{x:g}" y="{y:g}" {F} font-size="{sz}" font-weight="{700 if bold else 400}" fill="{fill}"{a}>{escape(t)}</text>'
Wc, Hc = 1448, 1010
o = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{Wc}" height="{Hc}" viewBox="0 0 {Wc} {Hc}">',
     '<title>Single Head-Worn IMU for Cadence Estimation</title>', defs, f'<rect width="{Wc}" height="{Hc}" fill="#ffffff" />']
# header
o.append('<rect x="16" y="16" width="1416" height="96" rx="14" fill="url(#header)" />')
o.append(T(724, 80, "One head-worn IMU · 8 clinical cohorts · 260 participants", 48, "#ffffff", True, "middle"))
# person: original box x 175-475, y 215-727 -> scale s, offset
s, X0, Y0 = 1.20, 112, 146
def P(x, y): return X0 + s * (x - 175), Y0 + s * (y - 215)
o.append(f'<g transform="translate({X0 - s * 175:g},{Y0 - s * 215:g}) scale({s:g})">{person}'
         '<line x1="120" y1="727" x2="530" y2="727" stroke="#98a6b7" stroke-width="3" /></g>')
hx, hy = P(388, 236)
o.append(f'<path d="M{hx:.1f} {hy:.1f} L{hx + 22:.1f} {hy - 12:.1f} H{hx + 34:.1f}" fill="none" stroke="{NAVY}" stroke-width="3" />'
         f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="5" fill="{NAVY}" />')
o.append(T(hx + 40, hy - 0, "head IMU", 46, NAVY, True))
# 180° whole-body turn
o.append(f'<path d="M52 640 V560 A30 30 0 0 1 112 560 V612" fill="none" stroke="{RED}" stroke-width="9" stroke-linecap="round" />'
         f'<path d="M112 642 L97 610 H127 Z" fill="{RED}" />')
o.append(T(30, 476, "180°", 46, RED, True)); o.append(T(30, 522, "turns", 46, RED, True))
gy = P(0, 727)[1]
o.append(T(316, gy + 58, "reference: foot IMUs", 46, GREY, False, "middle"))
# real-time cost
o.append(f'<rect x="16" y="{gy + 86:.0f}" width="600" height="{Hc - 16 - (gy + 86):.0f}" rx="14" fill="#f4f5f7" stroke="#d8dde3" stroke-width="2.5" />')
bt = gy + 86; bh = Hc - 16 - bt
o.append(T(316, bt + bh / 2 - 8, "Real time: +2.2 steps/min", 46, GREY, False, "middle"))
o.append(T(316, bt + bh / 2 + 46, "bias, 0.35 s step delay", 46, GREY, False, "middle"))
# tiles 2 x 2
tiles = [("1.53", NAVY, "url(#blue)", "#c6d7e8", ["steps/min", "with reference", "1.5% relative"]),
         ("1.56", NAVY, "url(#blue)", "#c6d7e8", ["steps/min", "head-only", "equivalent"]),
         ("0.90", TEAL, "url(#teal)", "#bcdcd5", ["AUROC", "trust flag", "up to 0.92"]),
         ("0.70", GOLD, "url(#gold)", "#f0d595", ["steps/min", "new dataset", "16 healthy adults"])]
tx0, tw, ty0, gap = 640, 384, 132, 20
th = (Hc - 16 - ty0 - gap) / 2
for k, (num, col, fill, stroke, lines) in enumerate(tiles):
    x = tx0 + (k % 2) * (tw + gap); y = ty0 + (k // 2) * (th + gap)
    o.append(f'<rect x="{x}" y="{y:.1f}" width="{tw}" height="{th:.1f}" rx="16" fill="{fill}" stroke="{stroke}" stroke-width="3" />')
    o.append(f'<path d="M{x} {y + 16:.1f} A16 16 0 0 1 {x + 16} {y:.1f} H{x + tw - 16} A16 16 0 0 1 {x + tw} {y + 16:.1f} V{y + 14:.1f} H{x}Z" fill="{col}" />')
    cx = x + tw / 2
    o.append(T(cx, y + 190, num, 150, col, True, "middle"))
    for i, ln in enumerate(lines):
        o.append(T(cx, y + 262 + 54 * i, ln, 46, INK if i else "#060e25", i == 0, "middle"))
    assert max(W(l, 46, i == 0) for i, l in enumerate(lines)) < tw - 30, lines
o.append('</svg>')
svg = "\n".join(o).replace('<use href="#traced-artwork"', '<use href="#traced-artwork"', 1)
open('graphical-abstract-compact.svg', 'w').write(svg)
print("ok gy", gy, "tile h", th)
