# headimu-cadence

Analysis code for the manuscript

> Q. Qiu, S. Chen, and Z. Jin, "Cadence Estimation From a Single Forehead IMU in Clinical Gait: Site Comparison,
> Failure Analysis, and Stride-Based Statistics," submitted to *IEEE Sensors Journal*.

The study is a secondary analysis of two public datasets. No data are included in this repository.

- Voisard et al., clinical gait dataset (figshare): https://doi.org/10.6084/m9.figshare.28806086
- DUO-GAIT (Zenodo): https://doi.org/10.5281/zenodo.8244887

## Layout

| Folder | Content |
|---|---|
| `headimu/` | Library: data loading, signal features, peak detection, evaluation, head-only pipeline (B1), DUO-GAIT reader |
| `analysis/` | Analysis scripts; the prefix (`v15_` … `v19_`) is the manuscript version in which the analysis was added |
| `figures_results/` | Result figures |
| `figures_schematic/` | Schematic figures |
| `tests/` | Checks and a synthetic archive generator |
| `manuscript_build/` | Scripts that typeset the manuscript and the supplementary file from the result files (reference only; the submitted text was edited afterwards) |
| root | Data preparation (`extract_needed.py`, `pack_v16.py`, `prep*_v16.py`, `pack_v19_lb.py`) and pipeline entry points (`run_*.py`, `run_*.cmd`, `run_v16_all.sh`) |

`SCRIPTS.md` lists every script with its purpose and `Usage:` line. `代码说明_论文对应表.md` maps sections, tables and
figures of the manuscript to scripts (in Chinese).

## Key components

- Cadence estimators (step median, stride median, autocorrelation, AGS): `analysis/v18_methods.py`
- Frozen test-set evaluation and statistics: `analysis/v18_eval.py`, `analysis/v18_stats.py`
- Failure analysis, ablation and applicability rule: `analysis/v18_ext.py`, `analysis/v18_analysis.py`, `analysis/v18_review.py`
- Sampling-rate and sensor-configuration simulation: `analysis/v19_sensor_req.py`, `analysis/v19_sensor_req_paired.py`
- Comparison with mobgap (Mobilise-D): `analysis/v19_mobgap.py`, `analysis/v19_mobgap_stats.py`
- The frozen settings are recorded in `analysis/V18_FREEZE.md`.

## Requirements

Python 3.10 or later; `pip install -r requirements.txt`. The mobgap comparison additionally needs `mobgap==1.2.0`
(installed in a separate environment).

## Order of work

1. Extract the needed files from the Voisard archive (`extract_needed.py`) and run the base pipeline
   (`run_pipeline.py`, see `README_使用说明.md`). This produces the participant split and `results_v11`.
2. Pack the head and lower-back signals (`pack_v16.py`, `pack_v19_lb.py`) and prepare DUO-GAIT (`prep*_v16.py`).
3. Head-only pipeline, external check and mounting simulations: `run_v16_all.sh` (or `run_v16_all.cmd` on Windows).
4. V17–V19 analyses and figures: run the scripts in `analysis/` and `figures_results/` with the arguments given in
   their `Usage:` lines (`SCRIPTS.md`).

Random seeds are fixed inside the scripts. Run-time figures depend on the machine.
