"""Graphical abstract V16 for IEEE Sensors Journal (landscape, journal palette). Numbers from results_v11 / results_v16:
B0 relative error 1.5% (table_primary.csv), B1 1.6% (endtoend_stats.json), CVA large errors 35% (B0),
SR AUROC 0.90 / SR+2 0.92 (trust_extra.json, trust_summary.json), CVA excluded by SR 21% (trust_operating_points.csv),
DUO-GAIT B1 0.70 steps/min (external_stats.json)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch, Ellipse
import numpy as np

plt.rcParams.update({"font.family": "TeX Gyre Heros", "mathtext.fontset": "stixsans", "font.size": 7,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.03})
INK, EDGE, FILL = "#1a1a1a", "#5b616b", "#e7e9ec"
NAVY, RED, SKY = "#1f3b63", "#b03a2e", "#8fb3d9"

fig = plt.figure(figsize=(3.3, 2.15))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 330); ax.set_ylim(0, 215); ax.axis("off")

# header band
ax.add_patch(Rectangle((0, 192), 330, 23, fc=NAVY, ec="none"))
ax.text(165, 203.5, "Single forehead IMU  ·  8 clinical cohorts  ·  260 participants  ·  external test", ha="center",
        va="center", color="white", fontsize=6.3, fontweight="bold")

# --- left: figure with sensors
def seg(p, q, w=3.2, c="#9aa1ab"):
    ax.plot([p[0], q[0]], [p[1], q[1]], color=c, lw=w, solid_capstyle="round", zorder=2)
hx, hy = 52, 158
ax.add_patch(Circle((hx, hy), 13, fc=FILL, ec=EDGE, lw=0.8, zorder=3))
# glasses temple hint
ax.plot([hx - 2, hx + 13], [hy + 1, hy + 1], color=INK, lw=0.7, zorder=4)
ax.add_patch(Ellipse((hx + 14, hy + 1), 4, 5, fc="white", ec=INK, lw=0.7, zorder=4))
ax.add_patch(Rectangle((hx + 5, hy + 7), 7, 5, angle=-15, fc=NAVY, ec="none", zorder=5))
neck, hip = (hx - 2, 144), (hx - 4, 98)
seg(neck, hip, 4)
seg((hx - 2, 138), (hx + 14, 116)); seg((hx + 14, 116), (hx + 20, 100))
seg((hx - 3, 138), (hx - 14, 118), c="#c9ced5"); seg((hx - 14, 118), (hx - 18, 103), c="#c9ced5")
seg(hip, (hx + 10, 64)); seg((hx + 10, 64), (hx + 8, 30))
seg(hip, (hx - 14, 64), c="#c9ced5"); seg((hx - 14, 64), (hx - 22, 32), c="#c9ced5")
ax.add_patch(Rectangle((hx - 9, 104), 6, 8, fc=EDGE, ec="none", zorder=5))
ax.add_patch(Rectangle((hx + 7, 29), 8, 5, angle=-20, fc=EDGE, ec="none", zorder=5))
ax.plot([10, 100], [26, 26], color=EDGE, lw=0.6)
ax.text(hx + 19, hy + 17, "head IMU", fontsize=6.3, color=NAVY, fontweight="bold", ha="left", va="center")
ax.text(hx - 21, 96, "lower back\n(comparator)", fontsize=5.4, color=EDGE, ha="right", va="center", linespacing=1.05)
ax.text(hx + 17, 38, "foot IMUs\n(reference)", fontsize=5.4, color=EDGE, ha="left", va="center", linespacing=1.05)
# turn arrow + tilt
ax.add_patch(FancyArrowPatch((hx - 15, hy - 18), (hx + 15, hy - 18), connectionstyle="arc3,rad=0.45",
                             arrowstyle="-|>", mutation_scale=6, color=RED, lw=0.8, zorder=6))
ax.text(hx - 26, hy - 24, "turns", fontsize=5.6, color=RED, ha="center")
ax.text(6, 12, "accuracy · mounting · trust · transfer", fontsize=5.0, color=EDGE, ha="left", style="italic")

# --- right: result cards
GOLD = "#a8730f"
cards = [("1.5%", "median cadence error\n(head-only offline: 1.6%);\nstroke: 35% large errors", NAVY),
         ("> 20°", "tilt degrades fixed-axis\ndetection; norm and vertical\nacceleration are invariant", NAVY),
         ("0.90", "AUROC of step-regularity flag\n(0.92 with two more features);\ncost: 21% of stroke data", RED),
         ("0.70", "steps/min on an independent\ndataset, frozen parameters\n(16 healthy adults)", GOLD)]
y = 186
for big, small, col in cards:
    ax.add_patch(FancyBboxPatch((128, y - 39), 196, 37, boxstyle="round,pad=0,rounding_size=4",
                                fc="#f6f7f9", ec="#d5d9de", lw=0.6))
    ax.add_patch(Rectangle((128, y - 39), 3.5, 37, fc=col, ec="none"))
    ax.text(140, y - 20.5, big, fontsize=12, fontweight="bold", color=col, va="center", ha="left")
    ax.text(207, y - 20.5, small, fontsize=5.5, color=INK, va="center", ha="left", linespacing=1.12)
    y -= 42
import sys
out = sys.argv[1] if len(sys.argv) > 1 else "fig_v16/graphical_abstract_v16"
fig.savefig(out + ".png", dpi=600)
fig.savefig(out + ".pdf")
print("ok")
