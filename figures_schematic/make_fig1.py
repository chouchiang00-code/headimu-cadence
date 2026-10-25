"""Fig. 1 (journal line-art style): (a) sensor placement, sagittal view; (b) head close-up with
eyeglasses: craniocaudal axis X, rigidly rotated X' (tilt phi) and lever arm r to the temple;
(c) transverse view: yaw rate omega and the lever-arm terms omega x (omega x r) = -omega^2 r and alpha x r."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Ellipse, FancyArrowPatch, Arc, Circle, FancyBboxPatch
from matplotlib.transforms import Affine2D
from scipy.interpolate import splprep, splev

OUT = "fig_schematics"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "TeX Gyre Heros", "mathtext.fontset": "stixsans", "font.size": 7,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.015})
INK, EDGE, FILL, FILL2 = "#1a1a1a", "#5b616b", "#e7e9ec", "#d5d9de"
NAVY, RED = "#1f3b63", "#b03a2e"
LW = 0.6


def smooth(pts, n=600, s=2.0, closed=True):
    p = np.asarray(pts, float)
    if closed:
        p = np.vstack([p, p[:1]])
    tck, _ = splprep([p[:, 0], p[:, 1]], s=s, per=closed)
    x, y = splev(np.linspace(0, 1, n), tck)
    return np.column_stack([x, y])


def arrow(ax, p, q, color=INK, lw=0.8, ms=6, ls="-", z=8):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=ms, lw=lw, color=color,
                                 shrinkA=0, shrinkB=0, linestyle=ls, zorder=z, joinstyle="miter"))


def sensor(ax, c, w, h, ang=0, measured=True, z=9):
    box = FancyBboxPatch((-w / 2, -h / 2), w, h, boxstyle="round,pad=0,rounding_size=%.3f" % (0.18 * min(w, h)),
                         fc=NAVY if measured else "white", ec=NAVY if measured else RED,
                         lw=0.7, ls="-" if measured else (0, (2, 1.2)), zorder=z)
    box.set_transform(Affine2D().rotate_deg(ang).translate(*c) + ax.transData)
    ax.add_patch(box)


def callout(ax, p, q, text, ha="left"):
    ax.plot([p[0], q[0]], [p[1], q[1]], color=INK, lw=0.4, zorder=7)
    ax.plot(*p, "o", ms=1.6, color=INK, zorder=10)
    ax.text(q[0] + (0.8 if ha == "left" else -0.8), q[1], text, ha=ha, va="center", fontsize=6.5)


# ------------------------------------------------------------------ body outline (sagittal, facing +x)
BODY = [(0, 175), (6, 173), (9.5, 168), (10.6, 163), (11, 160.5), (13.4, 156.3), (11.3, 154.6), (11.6, 152.8),
        (11.0, 151.2), (10.6, 148.4), (7.5, 146.2), (5.2, 143.5), (5.8, 139), (9.5, 134), (13, 126), (12.4, 118),
        (10.5, 109), (10.2, 100), (9, 92), (9.6, 78), (8.2, 62), (7.4, 49), (6.4, 32), (5.4, 10), (10, 5.5),
        (18.5, 1.6), (19, 0), (-3, 0), (-4.2, 3.5), (-3.2, 9), (-5.6, 30), (-3.6, 48), (-6.5, 66), (-9.6, 86),
        (-8.6, 96), (-5.4, 105), (-7.2, 118), (-9.4, 131), (-8.2, 139), (-3.6, 143.5), (-6.6, 150), (-9.6, 159),
        (-7.4, 169)]
ARM = [(3.2, 140), (5.4, 126), (5.6, 112), (4.6, 99), (5.6, 90), (5.2, 85.5), (2.2, 83.5), (-0.8, 86),
       (-2.8, 97), (-4.2, 111), (-5.6, 125), (-5.6, 136)]

HEAD = [(0, 12), (5, 10.9), (8, 8.2), (9.2, 5.0), (9.7, 2.6), (9.3, 1.5), (10.6, -0.8), (11.7, -2.6),
        (10.7, -3.4), (9.7, -3.6), (10.1, -4.6), (9.7, -5.4), (9.9, -6.2), (9.1, -7.0), (9.5, -8.4), (8.4, -9.8),
        (5.0, -10.3), (3.6, -10.9), (3.2, -14), (3.3, -16.5), (-4.6, -16.5), (-4.7, -12.5), (-5.6, -8.6),
        (-8.5, -4.2), (-9.7, 1.0), (-7.8, 8.0), (-3.6, 11.7)]


def head_profile(ax, z=2):
    pts = smooth(HEAD, s=0.25, n=900)
    ax.add_patch(Polygon(pts, closed=True, fc=FILL, ec=EDGE, lw=LW, zorder=z))
    ax.add_patch(Polygon([(-6, -16.5), (5, -16.5), (5, -18.5), (-6, -18.5)], closed=True, fc="white", ec="none", zorder=z + 0.5))
    # ear with helix
    ax.add_patch(Ellipse((-1.2, -0.6), 2.9, 4.8, angle=8, fc=FILL2, ec=EDGE, lw=0.5, zorder=z + 1))
    ax.add_patch(Arc((-1.0, -0.3), 1.5, 2.8, angle=8, theta1=-60, theta2=150, lw=0.4, color=EDGE, zorder=z + 1))
    # eye
    ax.plot([7.4, 8.3, 8.9], [0.45, 0.75, 0.45], color=EDGE, lw=0.5, zorder=z + 1)


fig = plt.figure(figsize=(3.45, 3.45))

# ================================================================== (a) link-segment model
ax = fig.add_axes([0.0, 0.0, 0.40, 1.0])
ax.set_xlim(-36, 42); ax.set_ylim(-6, 186); ax.set_aspect("equal"); ax.axis("off")
J = dict(head=(0, 164), neck=(0, 151), sh=(0, 145), hip=(-2, 95), elb=(5, 120), wri=(10, 97),
         kn=(10, 52), an=(6, 11), toe=(20, 3), heel=(2, 3),
         kn2=(-8, 53), an2=(-19, 15), toe2=(-7, 1), heel2=(-23, 10), elb2=(-10, 124), wri2=(-20, 107))
seg = lambda a, b, c, w=3.2, z=3: ax.plot([J[a][0], J[b][0]], [J[a][1], J[b][1]], color=c, lw=w, solid_capstyle="round", zorder=z)
back, front = "#c9ced5", "#9aa1ab"
for a, b in (("hip", "kn2"), ("kn2", "an2"), ("an2", "toe2"), ("an2", "heel2"), ("sh", "elb2"), ("elb2", "wri2")):
    seg(a, b, back, z=2)
seg("neck", "hip", front, w=5.0)
for a, b in (("hip", "kn"), ("kn", "an"), ("an", "toe"), ("an", "heel"), ("sh", "elb"), ("elb", "wri")):
    seg(a, b, front)
ax.add_patch(Circle(J["head"], 10, fc=FILL, ec=EDGE, lw=LW, zorder=4))
for k in ("sh", "elb", "wri", "hip", "kn", "an"):
    ax.add_patch(Circle(J[k], 1.6, fc="white", ec=EDGE, lw=0.5, zorder=5))
ax.plot([-26, 26], [0, 0], color=EDGE, lw=0.4)
he, lb, ft = (9.6, 167.5), (-6.4, 103.5), (12.5, 7.8)
sensor(ax, he, 3.0, 4.2, ang=-12)
sensor(ax, lb, 3.0, 5.2, ang=-4)
sensor(ax, ft, 5.0, 2.2, ang=-30)
for p in (he, lb):
    arrow(ax, p, (p[0], p[1] + 15), color=INK, lw=0.7, ms=5)
    ax.text(p[0] + 1.6, p[1] + 13.5, r"$X$", fontsize=7, va="center")
callout(ax, (he[0] + 1.5, he[1] - 1.5), (24, 176), "HE  forehead")
callout(ax, lb, (-17, 120), "LB  L4/L5", ha="right")
callout(ax, ft, (24, 22), "LF/RF\ndorsal foot")
ax.text(-17, 113.5, "U-turn boundaries", ha="right", va="center", fontsize=5.6, color=EDGE, style="italic")
ax.text(25, 12.4, "heel strikes", ha="left", va="center", fontsize=5.6, color=EDGE, style="italic")
ax.text(-35, 182, "(a)", fontsize=8, fontweight="bold")

# ================================================================== (b) head close-up, sagittal
bx = fig.add_axes([0.42, 0.50, 0.58, 0.50])
bx.set_xlim(-19, 26); bx.set_ylim(-18.5, 26.5); bx.set_aspect("equal"); bx.axis("off")
head_profile(bx)
# forehead strap (Velcro band)
bx.plot([8.6, 3, -3, -8.9], [6.9, 9.3, 9.6, 6.0], color=EDGE, lw=1.6, alpha=0.4, zorder=4, solid_capstyle="round")
# eyeglasses: lens (side view) + temple arm hooked behind the ear
bx.add_patch(Ellipse((10.0, 0.3), 1.1, 3.6, fc="none", ec=INK, lw=0.8, zorder=6))
bx.plot([9.8, 5, 1, -1.6, -3.1, -3.4], [1.9, 1.95, 1.85, 1.55, 0.3, -2.6], color=INK, lw=0.9, zorder=6, solid_capstyle="round")
heb, tmp = (9.0, 6.0), (3.4, 1.95)
sensor(bx, heb, 2.4, 1.6, ang=-72)
sensor(bx, tmp, 2.8, 1.4, ang=0, measured=False)
L = 13
arrow(bx, heb, (heb[0], heb[1] + L), lw=0.8, ms=5)
bx.text(heb[0] - 1.0, heb[1] + L - 0.4, r"$X$", ha="right", va="center")
phi = np.deg2rad(28)
xp = (heb[0] + L * np.sin(phi), heb[1] + L * np.cos(phi))
arrow(bx, heb, xp, lw=0.8, ms=5, ls=(0, (3, 1.5)))
bx.text(xp[0] + 0.5, xp[1], r"$X'$", ha="left", va="center")
bx.add_patch(Arc(heb, 11, 11, theta1=90 - np.rad2deg(phi), theta2=90, lw=0.5, color=INK))
bx.text(heb[0] + 1.9, heb[1] + 6.6, r"$\varphi$", fontsize=7)
arrow(bx, heb, tmp, color=RED, lw=1.0, ms=6)
bx.text(5.3, 4.9, r"$\boldsymbol{r}$", color=RED, fontsize=8, ha="center", va="bottom")
bx.text(heb[0] + 2.0, heb[1] - 1.9, "HE", fontsize=6.5, va="center", color=NAVY, fontweight="bold")
callout(bx, (tmp[0], tmp[1] - 0.8), (-6.5, -12.5), "temple position\n(simulated)", ha="right")
bx.text(-18.5, 24, "(b)", fontsize=8, fontweight="bold")

# ================================================================== (c) transverse view, top of head
cx = fig.add_axes([0.42, 0.0, 0.58, 0.49])
cx.set_xlim(-15, 17); cx.set_ylim(-13.5, 15); cx.set_aspect("equal"); cx.axis("off")
head = Ellipse((0, 0), 15.5, 19.5, fc=FILL, ec=EDGE, lw=LW, zorder=2)
cx.add_patch(head)
cx.add_patch(Polygon([(-1.4, 9.2), (-0.5, 11.0), (0, 11.3), (0.5, 11.0), (1.4, 9.2)], closed=True, fc=FILL, ec=EDGE, lw=LW, zorder=1))
for sgn in (-1, 1):
    cx.add_patch(Ellipse((sgn * 7.9, -0.5), 1.6, 3.6, fc=FILL2, ec=EDGE, lw=0.5, zorder=1))
    # lenses + temple arms
    cx.add_patch(Ellipse((sgn * 3.0, 10.4), 4.4, 1.1, fc="none", ec=INK, lw=0.8, zorder=6))
    cx.plot([sgn * 5.2, sgn * 7.6, sgn * 8.2, sgn * 8.1], [10.4, 8.6, 2.0, -1.2], color=INK, lw=0.9, zorder=6)
cx.plot([-0.8, 0.8], [10.4, 10.4], color=INK, lw=0.8, zorder=6)  # bridge
heo, tpo = (0.0, 9.15), (8.0, 4.6)
sensor(cx, heo, 2.6, 1.4)
sensor(cx, tpo, 1.3, 2.6, measured=False)
# rotation axis (vertical, out of page) and yaw rate
cx.add_patch(Circle((0, 0), 0.75, fc="white", ec=INK, lw=0.6, zorder=7))
cx.plot(0, 0, "o", ms=1.4, color=INK, zorder=8)
cx.add_patch(Arc((0, 0), 6.0, 6.0, theta1=200, theta2=320, lw=0.7, color=INK, zorder=7))
a1 = np.deg2rad(320)
arrow(cx, (3 * np.cos(a1 - 0.12), 3 * np.sin(a1 - 0.12)), (3 * np.cos(a1 + 0.02), 3 * np.sin(a1 + 0.02)), lw=0.7, ms=5)
cx.text(-3.9, -2.9, r"$\boldsymbol{\omega},\,\boldsymbol{\alpha}$", fontsize=7, ha="right")
# lever arm and the two added acceleration terms at the temple
arrow(cx, heo, tpo, color=RED, lw=1.0, ms=6)
cx.text(4.6, 7.7, r"$\boldsymbol{r}$", color=RED, fontsize=8)
r = np.array(tpo) - np.array(heo); rh = r / np.linalg.norm(r)
cen = np.array(tpo) - 4.6 * rh                      # omega x (omega x r) = -omega^2 r  (along -r)
arrow(cx, tpo, tuple(cen), color=NAVY, lw=0.9, ms=6)
cx.text(3.6, 4.3, r"$-\omega^{2}\boldsymbol{r}$", fontsize=7, color=NAVY, ha="center", va="top")
tan = np.array([-rh[1], rh[0]])                     # alpha x r for alpha along +z (counter-clockwise)
tq = np.array(tpo) + 4.2 * tan
arrow(cx, tpo, tuple(tq), color=NAVY, lw=0.9, ms=6)
cx.text(tq[0] + 0.4, tq[1] + 0.3, r"$\boldsymbol{\alpha}\!\times\!\boldsymbol{r}$", fontsize=6.5, color=NAVY, ha="left", va="bottom")
cx.text(0, -11.4, "anterior ↑", fontsize=5.6, color=EDGE, ha="center")
cx.text(-14.6, 13.6, "(c)", fontsize=8, fontweight="bold")

fig.savefig(f"{OUT}/fig1_sensors_frames_leverarm.pdf")
fig.savefig(f"{OUT}/fig1_sensors_frames_leverarm.png", dpi=600)
print("ok")
