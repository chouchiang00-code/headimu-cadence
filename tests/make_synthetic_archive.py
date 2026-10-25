"""SYNTHETIC data for testing the code paths ONLY. Never use outputs as study results.

Writes a folder that mimics the Voisard archive layout (raw_data_{HE,LB,LF,RF}.txt + meta.json)
so that `run_pipeline.py inspect/run` can be smoke-tested before the real data are available.
"""
import json, sys
from pathlib import Path
import numpy as np

FS = 100.0
G = 9.80665
COHORTS = {"HS": 1.08, "CVA": 1.28, "PD": 1.10, "RIL": 1.18, "KOA": 1.24}


def rot(axis, th):
    u = np.asarray(axis, float); u /= np.linalg.norm(u)
    K = np.array([[0, -u[2], u[1]], [u[2], 0, -u[0]], [-u[1], u[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def trial(rng, stride, sensor, turn_dur):
    step = stride / 2 * rng.uniform(0.95, 1.05)
    hs_times, t = [], 2.0
    n1 = rng.integers(7, 11)
    for _ in range(n1):
        hs_times.append(t); t += step * rng.normal(1, 0.03)
    ts = t; te = ts + turn_dur
    while t < te:
        t += step * 0.9
    for _ in range(n1):
        hs_times.append(t); t += step * rng.normal(1, 0.03)
    T = t + 2.0
    n = int(T * FS)
    tt = np.arange(n) / FS
    hs = np.array(hs_times)
    walking = (tt > hs[0] - 0.3) & (tt < hs[-1] + 0.3)
    # world-frame vertical acceleration: impact pulses after HS + smooth component
    av = np.zeros(n)
    for k, h in enumerate(hs):
        av += 2.0 * np.exp(-0.5 * ((tt - h - 0.06) / 0.04) ** 2) * (1.0 + (0.35 if k % 2 else -0.35) * (stride > 1.2))
    av -= np.convolve(av, np.ones(int(step * FS)) / int(step * FS), mode="same")
    aml = 0.6 * np.sin(np.pi * (tt - hs[0]) / step) * walking
    aap = 0.5 * np.sin(2 * np.pi * (tt - hs[0]) / step + 0.5) * walking
    yaw_rate = np.where((tt >= ts) & (tt <= te), np.pi / turn_dur, 0.0)
    yaw_rate = np.convolve(yaw_rate, np.hanning(41) / np.hanning(41).sum(), mode="same")
    acc_w = np.stack([aap, aml, G + av], 1)
    gyr_w = np.stack([0.05 * np.sin(2 * np.pi * tt / step), 0.05 * np.cos(2 * np.pi * tt / stride), yaw_rate], 1)
    # mounting: sensor X ~ up (craniocaudal) with ~10 deg random tilt
    base = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float)  # world->sensor: X_s = Z_w
    R = rot(rng.normal(size=3), np.deg2rad(rng.uniform(0, 10))) @ base
    acc = acc_w @ R.T + rng.normal(0, 0.03, (n, 3))
    gyr = gyr_w @ R.T + rng.normal(0, 0.003, (n, 3))
    return tt, acc, np.rad2deg(gyr), hs, (ts, te), step


def write(root, n_part=30, seed=1):
    rng = np.random.default_rng(seed)
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    for c, stride in COHORTS.items():
        for p in range(1, n_part // len(COHORTS) + 1):
            nvis = rng.integers(1, 3)
            sensor = "XSens" if rng.random() < 0.4 else "Technoconcept"
            k = 0
            for v in range(1, nvis + 1):
                for _ in range(rng.integers(2, 4)):
                    k += 1
                    tid = f"{c}_{p}_{k}"
                    tt, acc, gyr, hs, turn, step = trial(rng, stride * rng.uniform(0.92, 1.08), sensor, rng.uniform(2.0, 4.5))
                    n = len(tt)
                    counter = (np.arange(n) + rng.integers(60000, 65000)) % 65536
                    keep = np.ones(n, bool)
                    if sensor == "XSens":
                        g0 = rng.integers(300, n - 300); keep[g0:g0 + rng.integers(1, 8)] = False
                    for loc, scale in (("HE", 1.0), ("LB", 1.6), ("LF", 3.0), ("RF", 3.0)):
                        a = acc * np.array([1, 1, 1]) if loc == "HE" else acc * scale
                        lines = ["PacketCounter\tAcc_X\tAcc_Y\tAcc_Z\tGyr_X\tGyr_Y\tGyr_Z\tMag_X\tMag_Y\tMag_Z"]
                        for i in np.flatnonzero(keep):
                            lines.append("\t".join([str(int(counter[i]))] + [f"{x:.6f}" for x in a[i]] + [f"{x:.6f}" for x in np.deg2rad(gyr[i])] + ["0.1", "0.2", "0.3"]))
                        (root / f"{tid}_raw_data_{loc}.txt").write_text("\n".join(lines))
                    # processed file (homogenised frame = synthetic frame here), gyro in rad/s
                    cols = ["PacketCounter"]
                    data = [np.arange(n, dtype=float)]
                    for loc, scale in (("HE", 1.0), ("LB", 1.6), ("LF", 3.0), ("RF", 3.0)):
                        a = acc * scale if loc != "HE" else acc
                        for k, ax in enumerate("XYZ"):
                            cols.append(f"{loc}_Acc_{ax}"); data.append(a[:, k])
                        for k, ax in enumerate("XYZ"):
                            cols.append(f"{loc}_Gyr_{ax}"); data.append(np.deg2rad(gyr[:, k]))
                    M = np.column_stack(data)
                    (root / f"{tid}_processed_data.txt").write_text("\t".join(cols) + "\n" + "\n".join("\t".join(f"{x:.6f}" for x in row) for row in M))
                    hsi = np.round(hs * FS).astype(int)
                    left = [[int(h - 0.4 * FS * step), int(h)] for h in hsi[0::2]]
                    right = [[int(h - 0.4 * FS * step), int(h)] for h in hsi[1::2]]
                    meta = {"subject": f"{c}_{p}", "session": v, "sensor": "MTw Awinda XSens" if sensor == "XSens" else "Technoconcept I4 Motion",
                            "age": int(rng.integers(25, 80)), "pathologyKey": c, "TUG": "Not evaluated",
                            "uturnBoundaries": [int(turn[0] * FS), int(turn[1] * FS)],
                            "leftGaitEvents": left, "rightGaitEvents": right, "NOTE": "SYNTHETIC TEST DATA"}
                    (root / f"{tid}_meta.json").write_text(json.dumps(meta))


if __name__ == "__main__":
    write(sys.argv[1] if len(sys.argv) > 1 else "SYNTHETIC_TEST_ONLY", int(sys.argv[2]) if len(sys.argv) > 2 else 30)
