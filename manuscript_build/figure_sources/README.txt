Vector figure sources.
svgrev/build.py      -> head-imu-cadence-revised.svg (full graphical abstract; from the authors' traced fig.svg)
svgrev/build_ga2.py  -> graphical-abstract-compact.svg (first-page graphical abstract)
fig1new/build_fig1b.py -> fig1_sensors_frames_leverarm.svg (Fig. 1; ga.svg = copy of the compact GA, source of the walker)
Run each script inside its own folder with Python 3 + Pillow (text widths use Liberation Sans, metric-compatible with Arial).
PNG/PDF export: node render2.js IN.svg OUT.png SCALE W H ; node pdf*.js IN.svg OUT.pdf (Playwright/Chromium).
