"""Schematic figures for V11: Fig.1 sensor placement / frames / lever arm; Fig.2 method flowchart."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Ellipse, Rectangle, FancyArrowPatch, Arc, Polygon

OUT = "fig_schematics"
import os
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6.5, "axes.linewidth": 0.6,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.02})
INK, GREY, LIGHT = "#2b2b2b", "#8a8f98", "#e9ecef"
ACC, ACC2 = "#c0392b", "#1f5fa8"   # head sensor / lever arm accent; frames


def arrow(ax, p, q, color=INK, lw=0.9, ms=6, style="-|>", **kw):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, lw=lw, color=color,
                                 shrinkA=0, shrinkB=0, **kw))


def sensor(ax, xy, w=0.11, h=0.07, color=ACC2, angle=0):
    r = Rectangle((xy[0] - w / 2, xy[1] - h / 2), w, h, angle=angle, rotation_point="center",
                  fc=color, ec=INK, lw=0.5, zorder=5)
    ax.add_patch(r)


# =============================================================== Fig. 2 flowchart (single column, vertical)
fig = plt.figure(figsize=(3.45, 5.6))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 160); ax.axis("off")
FS = 5.4


def box(x, y, w, h, text, fc="white", ec=INK, fs=FS, lw=0.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, linespacing=1.25, color=INK)


def down(x, y0, y1, color=INK):
    arrow(ax, (x, y0), (x, y1), color=color, lw=0.7, ms=5)


def band(y0, y1, label):
    ax.add_patch(Rectangle((0.5, y0), 99, y1 - y0, fc="#f4f5f7", ec="none", zorder=-2))
    ax.text(2, y1 - 0.6, label, fontsize=5.0, color=GREY, va="top", fontweight="bold", zorder=10,
            bbox=dict(boxstyle="square,pad=0.15", fc="#f4f5f7", ec="none"))

band(139, 159, "INPUT (II-B–D)")
band(119, 138, "SIGNAL CHECK (II-E)")
band(94, 118, "SIGNALS (III-A)")
band(58, 93, "ESTIMATORS (III-B–D)")
band(39, 57, "PERTURBATIONS, TEST SET (III-F)")
band(1, 38, "EVALUATION (III-G, H; IV)")

box(4, 140.5, 29, 13.5, "Preprocessed file\nHE, LB acc + gyro\nhomogenised axes")
box(36, 140.5, 28, 13.5, "Raw files\npacket counter →\ngap mask (>0.05 s)")
box(67, 140.5, 29, 13.5, "Metadata (feet, LB)\nheel strikes\nU-turn boundaries", fc="#fbeeee", ec=ACC)
down(18.5, 140.2, 132.2); down(50, 140.2, 132.2)
box(4, 120.5, 92, 11.5, "Completeness · saturation · static noise, bias, |g|\n"
    "turn angle ∫q dt ≈ 180° · dominant / step frequency\n"
    "Exclude: empty head signal, missing events or U-turn")
ax.plot([50, 50], [120.2, 116], color=INK, lw=0.7)
ax.plot([14, 84.5], [116, 116], color=INK, lw=0.7)
for x in (14, 37, 60, 84.5):
    down(x, 116, 112.2)
box(4, 95.5, 20, 16.5, "A0\nfixed X axis\n(sign from\nstatic gravity)")
box(27, 95.5, 20, 16.5, "A0g\nv = a·ĝ\ngravity-\nprojected")
box(50, 95.5, 20, 16.5, "A1\n‖a‖\nnorm")
box(73, 95.5, 23, 16.5, "q(t) = |ω·ĝ|\nturn-rate proxy\nĝ: 0.3 Hz LP")
down(14, 95.2, 87.2); down(37, 95.2, 87.2); down(60, 95.2, 87.2); down(84.5, 95.2, 87.2)
arrow(ax, (54, 95.2), (45.5, 87.2), lw=0.7, ms=5)
box(4, 74.5, 43, 12.5, "Band-pass (low cut 0.6–1.2 Hz,\nhigh 3.0 Hz), peak detection\n→ step candidates")
box(50, 74.5, 20, 12.5, "AC\nautocorrelation\nstep time")
box(73, 74.5, 23, 12.5, "Gate: q > q*\nfor ≥ 0.30 s\n→ A2")
down(84.5, 74.2, 71.2)
box(73, 61.5, 23, 9.5, "A2-R: random\ngate, same\ncoverage", fc="#fbeeee", ec=ACC)
ax.text(40, 66.5, "Same pipeline on LB (A0g, A1, AC)\n→ position reference", fontsize=FS, ha="center", va="center", color=ACC2, linespacing=1.25)
down(10, 74.2, 52.2); down(84.5, 61.2, 52.2)
box(4, 40.5, 45, 11.5, "Rigid rotation a′ = R(θ,u)·a\nθ = 5–45°, 50 reps per angle\nonly A0 changes")
box(52, 40.5, 44, 11.5, "Lever arm a″ = a + α×r + ω×(ω×r)\n|r| = 2–8 cm, 20 directions\nA0g, A1, A2 all exposed")
down(40, 40.2, 32.2); down(74, 40.2, 32.2)
box(4, 20, 29, 12, "Development set (30%)\nstrata: cohort × sensor\n→ low cut, lags, q*", fc="#eef3fa", ec=ACC2)
arrow(ax, (33.6, 26), (37.6, 26), color=ACC2, lw=0.8, ms=5)
box(38, 20, 58, 12, "Test set (70%), per participant:\ncadence error, Bland–Altman,\nhalving/doubling, event matching", fc="#eef3fa", ec=ACC2)
down(44, 19.7, 15.2); down(74, 19.7, 15.2)
box(4, 3, 44, 12, "Turn detection vs U-turn bounds\nerror–coverage: A2 vs A2-R")
box(52, 3, 44, 12, "Re-wear (same-sensor visits)\nICC(A,1), SEM, MDC₉₅:\nhead vs foot reference")
fig.savefig(f"{OUT}/fig2_method_flowchart.pdf")
fig.savefig(f"{OUT}/fig2_method_flowchart.png", dpi=400)
plt.close(fig)
print("ok")
