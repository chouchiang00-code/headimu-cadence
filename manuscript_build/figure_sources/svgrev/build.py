import re, json
from xml.sax.saxutils import escape
from PIL import ImageFont
R = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"; BD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
def W(t, sz, b=False): return ImageFont.truetype(BD if b else R, sz).getlength(t)

src = open('fig.svg').read()
rows = json.load(open('bbox.json'))
# ---- traced artwork: drop the neck-arrow paths, the old lower-back sensor, the page/panel background tiles, the foot-leader ghost
drop = set(json.load(open('drop.json')))
drop |= {0, 1, 12}
g0 = src.index('<g id="traced-artwork">'); g1 = src.index('</g>', g0)
items = re.findall(r'<path d="[^"]*" fill="#[0-9A-Fa-f]{6}" transform="translate\([-\d.]+,[-\d.]+\)" />\n?', src[g0:g1])
assert len(items) == 294
traced = '<g id="traced-artwork">' + ''.join(p for k, p in enumerate(items) if k not in drop) + '</g>'
grads = src[src.index('<defs>') + 6:src.index('<g id="traced-artwork">')]
person_clip = re.search(r'<clipPath id="person-clip">.*?</clipPath>', src).group(0)

NAVY, TEAL, GOLD, INK, GREY, RED = "#07366c", "#007367", "#a87900", "#0b1530", "#3e4b5b", "#c8202a"
FONT = 'font-family="Arial, Helvetica, sans-serif"'
def text(x, y, t, sz, fill, bold=False, anchor="start", extra=""):
    return (f'<text x="{x:g}" y="{y:g}" {FONT} font-size="{sz}" font-weight="{700 if bold else 400}" fill="{fill}"'
            + (f' text-anchor="{anchor}"' if anchor != "start" else "") + f'{extra}>{escape(t)}</text>')

out = []
out.append('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1448" height="1086" viewBox="0 0 1448 1086">')
out.append('<title>Single Head-Worn IMU for Cadence Estimation</title>')
out.append('<defs>' + grads.replace('</defs>', '') +
           '<linearGradient id="teal" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#f1f8f6" /><stop offset="100%" stop-color="#e7f2ef" /></linearGradient>'
           + traced + person_clip +
           '<clipPath id="icon-1"><rect x="214" y="830" width="99" height="71" /></clipPath>'
           '<clipPath id="icon-2"><rect x="407" y="830" width="63" height="65" /></clipPath>'
           '<clipPath id="icon-3"><rect x="555" y="827" width="61" height="74" /></clipPath>'
           + ''.join(f'<clipPath id="card-{y}"><rect x="681" y="{y}" width="747" height="{h}" rx="14" /></clipPath>'
                     for y, h in ((217, 159), (394, 159), (644, 159), (821, 159)))
           + '<linearGradient id="armfix" gradientUnits="userSpaceOnUse" x1="0" y1="433" x2="0" y2="458"><stop offset="0" stop-color="#b9c0ca" /><stop offset="1" stop-color="#bcc2cd" /></linearGradient>'
           + '</defs>')
out.append('<rect width="1448" height="1086" fill="#ffffff" />')
# ---- header
out.append('<rect x="16" y="40" width="1416" height="146" rx="13" fill="url(#header)" />')
out.append(text(724, 109, "Single Head-Worn IMU for Cadence Estimation", 52, "#ffffff", True, "middle"))
out.append(text(724, 161, "8 clinical cohorts · 260 participants · external validation", 38, "#ffffff", False, "middle"))
# ---- figure
out.append('<g id="person"><use href="#traced-artwork" clip-path="url(#person-clip)" />')
# repair where the neck arrow was: clear the band, restore the neck
out.append('<rect x="268" y="300.6" width="128" height="29" fill="#ffffff" />')
out.append('<path d="M312.5 299 C311.8 305 309 312 304.5 318 C301 323 298 328 296 334 L353 334 C350.5 328 347 322 344.5 316 C344 310 346 304 349.5 299 Z" fill="#bbc1cb" />')
# repair where the old lower-back leader crossed the arm (leader redrawn below)
L = [(251, 431), (250.4, 440), (249.6, 448), (249, 456), (248.7, 459.5)]
Rr = [(275.3, 431), (274.3, 436), (273.3, 440), (271.5, 444), (270.2, 448), (269.6, 452), (269, 456), (268.4, 459.5)]
pt = lambda q: " ".join(f"{x:g} {y:g}" for x, y in q)
out.append(f'<path d="M226.5 430 L{pt(L)} L226.5 459.5Z" fill="#ffffff" />')
out.append(f'<path d="M279.5 431 L{pt(Rr[::-1])[0:0]}{pt(Rr)} L279.5 459.5Z" fill="#ffffff" />')
out.append(f'<path d="M{pt(L)} L{pt(Rr[::-1])}Z" fill="url(#armfix)" />')
# lower-back IMU on the back, at waist level
out.append('<rect x="279" y="430" width="17" height="36" rx="3.5" fill="#2f3b4b" /><rect x="282" y="434" width="3" height="28" rx="1.5" fill="#56657a" />')
out.append('</g>')
out.append('<line x1="91" y1="727" x2="546" y2="727" stroke="#98a6b7" stroke-width="3" />')
out.append(text(436, 235, "head IMU", 30, NAVY, True))
out.append(f'<path d="M390 236L416 224H429" fill="none" stroke="{NAVY}" stroke-width="2" /><circle cx="390" cy="236" r="3.7" fill="{NAVY}" />')
out.append(f'<path d="M230 435.5L280 447" fill="none" stroke="{GREY}" stroke-width="2" /><circle cx="281" cy="447.3" r="3.2" fill="{GREY}" />')
out.append(text(92, 437, "lower back", 28, GREY)); out.append(text(92, 465, "comparator", 28, GREY))
out.append(text(487, 656, "foot IMUs", 28, GREY)); out.append(text(487, 684, "reference", 28, GREY))
# whole-body 180° turn: a U-turn arrow beside the walker (walk out, turn, walk back)
out.append(f'<path d="M78 606 V548 A32 32 0 0 1 142 548 V586" fill="none" stroke="{RED}" stroke-width="7" stroke-linecap="round" />')
out.append(f'<path d="M142 609 L129.5 584 H154.5 Z" fill="{RED}" />')
out.append(text(40, 646, "180° turns", 28, RED, True))
out.append(text(40, 674, "whole body", 24, GREY))
# ---- cards
cards = [(217, 159, "url(#blue)", "#c6d7e8", NAVY, "#9bb5cf", "1.53", "median error, reference-assisted", "steps/min · 1.5% relative error"),
         (394, 159, "url(#blue)", "#c6d7e8", NAVY, "#9bb5cf", "1.56", "median error, head-only offline", "steps/min · equivalent · 1.6% missing"),
         (644, 159, "url(#teal)", "#bcdcd5", TEAL, "#9fcbc1", "0.90", "AUROC, step-regularity flag", "0.92 with two more features"),
         (821, 159, "url(#gold)", "#f0d595", GOLD, "#e3c477", "0.70", "median error, external dataset", "steps/min · 16 healthy adults")]
tsz = 28
while max(W(c[7], tsz, True) for c in cards) > 404: tsz -= 0.5
ssz = 26
while max(W(c[8], ssz) for c in cards) > 404: ssz -= 0.5
for y, h, fill, stroke, col, div, num, ttl, sub in cards:
    out.append(f'<rect x="681" y="{y}" width="747" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="2.7" />')
    out.append(f'<rect x="681" y="{y}" width="24" height="{h}" fill="{col}" clip-path="url(#card-{y})" />')
    out.append(f'<line x1="962" y1="{y + 25}" x2="962" y2="{y + h - 25}" stroke="{div}" stroke-width="2" />')
    out.append(text(833.5, y + 114, num, 96, col, True, "middle"))
    out.append(text(1000, y + 71, ttl, tsz, "#060e25", True))
    out.append(text(1000, y + 111, sub, ssz, "#1d2638"))
strip = "Robust to rotation, lever arm, noise · needs ≥ 50 Hz, gyro calibration"
s_sz = 24
while W(strip, s_sz) > 690: s_sz -= 0.5
out.append('<rect x="681" y="571" width="747" height="55" rx="14" fill="#eaf0f7" stroke="#d9e2ee" stroke-width="2.5" />')
out.append(text(1054.5, 606.5, strip, s_sz, "#123c73", False, "middle"))
# ---- pipeline panel
out.append('<rect x="21" y="759" width="633" height="220" rx="18" fill="url(#panel)" stroke="#e4eaf1" stroke-width="3" />')
out.append(text(48, 803, "Head-only processing pipeline", 29, "#07132d", True))
# IMU chip icon (replaces the duplicate head icon)
pins = ''.join(f'<rect x="{x}" y="839" width="5" height="9" rx="1.5" fill="{NAVY}" /><rect x="{x}" y="886" width="5" height="9" rx="1.5" fill="{NAVY}" />' for x in (75, 88, 101))
out.append(pins + f'<rect x="64" y="845" width="58" height="44" rx="7" fill="{NAVY}" />'
           + text(93, 873, "IMU", 17, "#ffffff", True, "middle"))
for i in (1, 2, 3): out.append(f'<use href="#traced-artwork" clip-path="url(#icon-{i})" />')
for d in ("M151 862h27v-7l15 10-15 10v-7h-27Z", "M345 862h27v-7l15 10-15 10v-7h-27Z", "M492 862h27v-7l15 10-15 10v-7h-27Z"):
    out.append(f'<path d="{d}" fill="#94a1b1" />')
for x, lines in ((93, ["Head IMU"]), (263.5, ["walking / turn /", "step detection"]), (438.5, ["cadence", "estimate"]), (585.5, ["trust", "screening"])):
    ys = [945] if len(lines) == 1 else [925, 953]
    for yy, t in zip(ys, lines): out.append(text(x, yy, t, 24, INK, False, "middle"))
# ---- cost of real-time operation (balance)
low = "Real-time cost: +2.2 steps/min bias · steps confirmed 0.35 s late · largest errors after stroke"
l_sz = 25
while W(low, l_sz) > 1340: l_sz -= 0.5
out.append('<rect x="21" y="996" width="1407" height="52" rx="14" fill="#f4f5f7" stroke="#d8dde3" stroke-width="2.5" />')
out.append(text(724.5, 1030, low, l_sz, "#3e4c62", False, "middle"))
out.append('</svg>')
svg = "\n".join(out).replace('<use href="#traced-artwork"', '<use href="#traced-artwork" xlink:href="#traced-artwork"')
open('head-imu-cadence-revised.svg', 'w').write(svg)
print("sizes", tsz, ssz, s_sz, l_sz, len(svg))
