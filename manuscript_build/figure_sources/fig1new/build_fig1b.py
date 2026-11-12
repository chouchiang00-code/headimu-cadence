"""Fig. 1, single column (3.1 in), compact 2 x 2 layout: (a) placement, (b) rotation and offset (side view),
(c) lever-arm terms (top view), and a key. Redrawn after the authors' sketch. Physics per Eq. (5): a sensor offset by r
from HE additionally senses alpha x r (perpendicular to r) and omega x (omega x r) = -omega^2 r (r perpendicular to
omega; from the offset site back toward HE). Simulation ranges from the Methods: tilt 5-45 deg, |r| 2-8 cm.
Sensor sites per the Voisard data descriptor: forehead (HE), lower back L4/L5 (LB), dorsal face of each foot (LF/RF)."""
import math, re
from xml.sax.saxutils import escape
ga = open('ga.svg').read()
defs = ga[ga.index('<defs>'):ga.index('</defs>') + 7]
_orig = open('../svgrev/fig.svg').read(); _g0 = _orig.index('<g id="traced-artwork">'); _g1 = _orig.index('</g>', _g0)
_items = re.findall(r'<path d="[^"]*" fill="#[0-9A-Fa-f]{6}" transform="translate\([-\d.]+,[-\d.]+\)" />', _orig[_g0:_g1])
for k in (61, 101, 292):        # remnants of the old 'head IMU' leader at the visor
    assert defs.count(_items[k]) == 1, k
    defs = defs.replace(_items[k], "")
person = ga[ga.index('<g id="person">'):]; person = person[:person.index('</g>') + 4]
NAVY, RED, BLUE, INK, GREY, SKIN, LINE, FRAME = "#07366c", "#c8202a", "#1d4f91", "#111827", "#4b5563", "#dfe3e8", "#8a94a3", "#374151"
F = 'font-family="Arial, Helvetica, sans-serif"'
def T(x, y, t, sz=30, fill=INK, bold=False, anchor="start", italic=False, raw=False):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    st = ' font-style="italic"' if italic else ""
    return f'<text x="{x:g}" y="{y:g}" {F} font-size="{sz}" font-weight="{700 if bold else 400}" fill="{fill}"{a}{st}>{t if raw else escape(t)}</text>'
V = lambda s: f'<tspan font-weight="700" font-style="italic">{s}</tspan>'
def arrow(x1, y1, x2, y2, col, w=3.5, head=15, dash=None):
    ang = math.atan2(y2 - y1, x2 - x1)
    xe, ye = x2 - head * 0.8 * math.cos(ang), y2 - head * 0.8 * math.sin(ang)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    c, s_ = math.cos(ang), math.sin(ang)
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{xe:.1f}" y2="{ye:.1f}" stroke="{col}" stroke-width="{w}"{d} />'
            f'<path d="M{x2:.1f} {y2:.1f} L{x2 - head * c + head * .45 * s_:.1f} {y2 - head * s_ - head * .45 * c:.1f} '
            f'L{x2 - head * c - head * .45 * s_:.1f} {y2 - head * s_ + head * .45 * c:.1f} Z" fill="{col}" />')
W, H = 900, 930
YM = 505            # row divider
o = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
     '<title>Fig. 1 Sensor placement and mounting errors</title>', defs, f'<rect width="{W}" height="{H}" fill="#ffffff" />']
o.append(f'<line x1="450" y1="8" x2="450" y2="{H - 8}" stroke="#c9ced6" stroke-width="2" stroke-dasharray="8 7" />')
o.append(f'<line x1="8" y1="{YM}" x2="{W - 8}" y2="{YM}" stroke="#c9ced6" stroke-width="2" stroke-dasharray="8 7" />')
# ------------------------------------------------------------------ (a) placement
o.append(T(10, 36, "(a) Placement", 30, INK, True))
s, X0, Y0 = 0.80, 112, 74
P = lambda x, y: (X0 + s * (x - 175), Y0 + s * (y - 215))
o.append(f'<g transform="translate({X0 - s * 175:g},{Y0 - s * 215:g}) scale({s:g})">{person}'
         '<line x1="120" y1="727" x2="530" y2="727" stroke="#98a6b7" stroke-width="3" /></g>')
he = P(372, 238); lb = P(287.5, 448); rf = P(400, 688); lf = P(213, 676); gnd = P(0, 727)[1]
o.append(arrow(he[0], he[1] - 4, he[0], he[1] - 62, INK, 3, 13)); o.append(T(he[0] + 8, he[1] - 46, "X", 28, INK, italic=True))
o.append(arrow(lb[0], lb[1] - 18, lb[0], lb[1] - 78, INK, 3, 13)); o.append(T(lb[0] + 8, lb[1] - 62, "X", 28, INK, italic=True))
o.append(f'<path d="M{he[0] + 12:.0f} {he[1] + 2:.0f} L{he[0] + 40:.0f} {he[1] + 2:.0f}" stroke="{GREY}" stroke-width="2" />')
o.append(T(he[0] + 46, he[1] + 12, "HE", 30, NAVY, True))
o.append(f'<path d="M{lb[0] - 10:.0f} {lb[1]:.0f} L{lb[0] - 46:.0f} {lb[1]:.0f}" stroke="{GREY}" stroke-width="2" />')
o.append(T(lb[0] - 52, lb[1] + 11, "LB", 30, INK, True, "end"))
o.append(f'<path d="M{rf[0] + 10:.0f} {rf[1] - 4:.0f} L{rf[0] + 36:.0f} {rf[1] - 30:.0f}" stroke="{GREY}" stroke-width="2" />')
o.append(T(rf[0] + 38, rf[1] - 34, "LF/RF", 30, INK, True))
# ------------------------------------------------------------------ (b) side view: rotation and offset
o.append(T(462, 36, "(b) Rotation, offset", 30, INK, True))
k = 0.78; ox, oy = 560, 205
L = lambda x, y: (ox + k * (x - 100), oy + k * (y - 64))
head = ("M118 190 C110 110 175 62 245 64 C300 66 328 104 330 150 C331 172 334 186 340 200 L356 230 "
        "C358 236 352 238 344 240 C346 250 344 258 340 264 C346 270 344 280 336 286 C336 306 324 318 300 320 "
        "C284 321 270 320 262 330 L262 380 L168 380 L170 318 C140 296 122 252 118 190 Z")
o.append(f'<g transform="translate({ox - k * 100:g},{oy - k * 64:g}) scale({k})">'
         f'<path d="{head}" fill="{SKIN}" stroke="{LINE}" stroke-width="3.5" stroke-linejoin="round" />'
         f'<path d="M200 186 C186 186 182 204 184 216 C186 232 196 242 208 238" fill="#cfd5dc" stroke="{LINE}" stroke-width="3" />'
         f'<rect x="312" y="184" width="32" height="32" rx="9" fill="none" stroke="{FRAME}" stroke-width="6" />'
         f'<path d="M314 196 L214 200 C202 201 194 214 198 236" fill="none" stroke="{FRAME}" stroke-width="6" stroke-linecap="round" />'
         '</g>')
hb = L(322, 122)
o.append(f'<g transform="rotate(-18 {hb[0]:.1f} {hb[1]:.1f})"><rect x="{hb[0] - 13:.1f}" y="{hb[1] - 9:.1f}" width="26" height="18" rx="3" fill="{NAVY}" /></g>')
phi, Lx = math.radians(32), 112
o.append(arrow(hb[0], hb[1] - 10, hb[0], hb[1] - Lx, INK)); o.append(T(hb[0] - 30, hb[1] - Lx + 16, "X", 28, INK, italic=True))
xe, ye = hb[0] + Lx * math.sin(phi), hb[1] - Lx * math.cos(phi)
o.append(arrow(hb[0] + 10 * math.sin(phi), hb[1] - 10 * math.cos(phi), xe, ye, BLUE, dash="8 5"))
o.append(T(xe + 4, ye + 8, "X′", 28, BLUE, italic=True))
ra = 60
o.append(f'<path d="M{hb[0]:.1f} {hb[1] - ra:.1f} A{ra} {ra} 0 0 1 {hb[0] + ra * math.sin(phi):.1f} {hb[1] - ra * math.cos(phi):.1f}" fill="none" stroke="{INK}" stroke-width="2.5" />')
o.append(T(hb[0] + 14, hb[1] - ra - 10, "φ", 28, INK, italic=True))
tp = L(244, 199)
o.append(f'<rect x="{tp[0] - 18:.1f}" y="{tp[1] - 12:.1f}" width="36" height="24" rx="4" fill="#ffffff" fill-opacity="0.6" stroke="{RED}" stroke-width="3" stroke-dasharray="6 4" />')
o.append(arrow(hb[0] - 8, hb[1] + 8, tp[0] + 18, tp[1] - 10, RED))
o.append(T((hb[0] + tp[0]) / 2 - 8, (hb[1] + tp[1]) / 2 - 6, V("r"), 28, RED, raw=True))
o.append(T(hb[0] + 18, hb[1] + 22, "HE", 28, NAVY, True))
o.append(T(462, YM - 18, "temple (simulated)", 26, RED))
o.append(f'<path d="M{tp[0] - 4:.0f} {tp[1] + 13:.0f} L{560:.0f} {YM - 44:.0f}" fill="none" stroke="{RED}" stroke-width="1.8" />')
# ------------------------------------------------------------------ (c) top view: lever-arm terms
o.append(T(10, YM + 38, "(c) Lever arm", 30, INK, True))
cx, cy, R = 225, YM + 240, 105
o.append(f'<ellipse cx="{cx - R - 2}" cy="{cy + 8}" rx="12" ry="24" fill="#cfd5dc" stroke="{LINE}" stroke-width="2.5" />'
         f'<ellipse cx="{cx + R + 2}" cy="{cy + 8}" rx="12" ry="24" fill="#cfd5dc" stroke="{LINE}" stroke-width="2.5" />')
o.append(f'<path d="M{cx - 13} {cy - R + 3} Q{cx} {cy - R - 24} {cx + 13} {cy - R + 3}" fill="{SKIN}" stroke="{LINE}" stroke-width="2.5" />')
o.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{SKIN}" stroke="{LINE}" stroke-width="3" />')
gy = cy - R - 2
o.append(f'<path d="M{cx - 82} {gy + 26} L{cx - 82} {gy} H{cx + 82} V{gy + 26}" fill="none" stroke="{FRAME}" stroke-width="5" stroke-linejoin="round" />'
         f'<path d="M{cx - 82} {gy + 26} C{cx - 100} {gy + 62} {cx - 109} {cy - 28} {cx - 107} {cy + 2}" fill="none" stroke="{FRAME}" stroke-width="5" />'
         f'<path d="M{cx + 82} {gy + 26} C{cx + 100} {gy + 62} {cx + 109} {cy - 28} {cx + 107} {cy + 2}" fill="none" stroke="{FRAME}" stroke-width="5" />')
hc = (cx, gy + 2)
o.append(f'<rect x="{hc[0] - 16}" y="{hc[1] - 10}" width="32" height="20" rx="3" fill="{NAVY}" />')
o.append(T(hc[0] - 24, hc[1] - 18, "HE", 28, NAVY, True, "end"))
tc = (cx + 101, cy - 36)
o.append(f'<rect x="{tc[0] - 13}" y="{tc[1] - 20}" width="26" height="40" rx="4" fill="#ffffff" fill-opacity="0.6" stroke="{RED}" stroke-width="3" stroke-dasharray="6 4" />')
o.append(arrow(hc[0] + 16, hc[1] + 6, tc[0] - 12, tc[1] - 9, RED))
rx_, ry_ = tc[0] - hc[0], tc[1] - hc[1]; rn = math.hypot(rx_, ry_); ux, uy = rx_ / rn, ry_ / rn
o.append(T(hc[0] + rx_ * .5 + 8, hc[1] + ry_ * .5 - 10, V("r"), 28, RED, raw=True))
px, py = uy, -ux          # alpha out of page, counter-clockwise as drawn: r rotated by +90 deg
Lt = 72; tip = (tc[0] + 6 + Lt * px, tc[1] - 8 + Lt * py)
o.append(arrow(tc[0] + 6, tc[1] - 8, tip[0], tip[1], BLUE, 3.5, 15))
o.append(T(tip[0] - 12, tip[1] + 4, V("α") + " × " + V("r"), 26, BLUE, anchor="end", raw=True))
Lc, off = 74, 18
sx, sy = tc[0] - 12 - off * px, tc[1] + 4 - off * py
o.append(arrow(sx, sy, sx - Lc * ux, sy - Lc * uy, BLUE, 3.5, 15))
o.append(T(cx + 2, cy - 2, V("ω") + " × (" + V("ω") + " × " + V("r") + ")", 26, BLUE, anchor="middle", raw=True))
o.append(f'<circle cx="{cx}" cy="{cy + 30}" r="12" fill="#ffffff" stroke="{INK}" stroke-width="3" /><circle cx="{cx}" cy="{cy + 30}" r="4" fill="{INK}" />')
o.append(f'<path d="M{cx - 54} {cy + 50} A58 46 0 0 0 {cx + 46} {cy + 60}" fill="none" stroke="{INK}" stroke-width="3.5" />')
o.append(f'<path d="M{cx + 56} {cy + 48} L{cx + 34} {cy + 52} L{cx + 48} {cy + 70} Z" fill="{INK}" />')
o.append(T(cx, cy + 102, V("ω") + ", " + V("α"), 28, INK, anchor="middle", raw=True))
o.append(T(cx, H - 14, "top view, anterior up", 24, GREY, anchor="middle", italic=True))
# ------------------------------------------------------------------ key
kx, ky, ls = 466, YM + 40, 37
o.append(T(kx, ky, "Sites (dataset)", 28, INK, True))
rows = [("HE", " forehead", NAVY), ("LB", " L4/L5; turn boundaries", INK), ("LF/RF", " dorsal foot;", INK)]
for i, (a, b_, col) in enumerate(rows):
    o.append(T(kx, ky + ls * (i + 1), f'<tspan font-weight="700" fill="{col}">{a}</tspan>{escape(b_)}', 26, INK, raw=True))
o.append(T(kx + 18, ky + ls * 4, "heel strikes (reference)", 26, INK))
o.append(T(kx, ky + ls * 5, "X: craniocaudal axis", 26, INK, raw=False))
o.append(T(kx, ky + ls * 6 + 18, "Simulated", 28, INK, True))
o.append(T(kx, ky + ls * 7 + 18, "tilt φ = 5°–45°", 26, INK))
o.append(T(kx, ky + ls * 8 + 18, "offset |" + V("r") + "| = 2–8 cm", 26, INK, raw=True))
o.append('</svg>')
open('fig1_sensors_frames_leverarm.svg', 'w').write("\n".join(o))
