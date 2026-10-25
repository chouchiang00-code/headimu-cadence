# Head-worn IMU cadence analysis

Code for **“Cadence From a Single Head-Worn IMU Across Clinical Cohorts: Head-Only Estimation, Failure Modes, Trustworthiness, and External Validation”**, submitted to *IEEE Sensors Journal*.

**Authors:** Qiu Qiang, Chen Shiqi, and Jin Zhenkun (corresponding author), School of Artificial Intelligence and Big Data, Wuhan University of Business.

**Paper link:** [to be added]

This repository contains the reference-assisted and head-only cadence pipelines, failure analyses, trustworthiness analyses, external validation, and simulations used for the paper. The analyses use the public Voisard dataset and DUO-GAIT, with participant-level development/test separation and development-selected parameters. The code evaluates walking, turning, and step detection, examines cadence error and error-risk screening, and applies the frozen pipeline to the external dataset. Synthetic perturbations assess mounting and sensor sensitivity. The data must be downloaded separately; neither dataset is included here.

## Repository layout

- `headimu/`: signal processing, dataset adapters, cadence pipelines, features, statistics, and reporting.
- `analysis/`: primary-output audits, secondary statistics, failure analyses, and result comparison scripts.
- `figures_results/`: scripts that generate result figures from locally regenerated outputs.
- `figures_schematic/`: scripts that draw the sensor and method schematics.
- `tests/`: a synthetic archive generator for code-path smoke checks; its outputs are not study results.
- `manuscript_build/`: manuscript build instructions, graphical-abstract script, and supporting figure assets.
- `manuscript_build/ieee/`: Word manuscript and supplement builders, manuscript text, and references.
- `manuscript_build/ieee/jsen_assets/`: journal-logo and author-photo placeholder assets supplied with the builders.
- `manuscript_build/fig_ieee/`: supplied method-flowchart asset.
- `manuscript_build/fig_results/`: supplied manuscript result-figure assets.
- `manuscript_build/fig_schematics/`: supplied sensor schematic asset.
- `manuscript_build/fig_v16/`: supplied V16 manuscript figures and graphical abstract.

The repository root contains `run_*.py`, data preparation scripts, `config.json`, and Windows/POSIX launchers. `README_V16.md` preserves the original reproducibility notes. `README_V15.md` and `README_使用说明.md` are historical guides; use the instructions below for this release.

## Environment

**Python baseline: 3.11+.** The exact pinned NumPy and SciPy distributions declare Python 3.12 or newer, so use **Python 3.12+ for this pinned environment**. From `headimu-cadence/`, create a sibling environment so the Windows launchers can find it:

```sh
python -m venv ../.venv
```

Activate it on Linux/macOS:

```sh
source ../.venv/bin/activate
```

Or in Windows PowerShell:

```powershell
..\.venv\Scripts\Activate.ps1
```

Then install the analysis dependencies:

```sh
pip install -r requirements.txt
```

The supplied archive did not contain the `requirements.lock.txt` mentioned in `README_V16.md`. With approval for this release, `requirements.txt` pins the exact container versions explicitly recorded there: numpy 2.5.3, scipy 1.18.1, pandas 3.0.5, and matplotlib 3.11.2. There is no scikit-learn dependency. These pins have been checked on Python 3.12.14; Python 3.11 cannot install the pinned NumPy/SciPy distributions, and other platforms have not been tested for this release.

Building the optional Word manuscripts additionally requires the source-documented dependency:

```sh
pip install python-docx==1.2.0
```

## Download the data separately

- **Voisard et al. (2025):** [figshare, doi:10.6084/m9.figshare.28806086](https://doi.org/10.6084/m9.figshare.28806086). Download the complete `dataset.zip` archive used in the original guide. The analysis uses processed HE/LB/foot signals, raw sensor files for validity/QC, heel strikes, turn boundaries, and clinical metadata. `extract_needed.py` extracts the required files while preserving archive paths.
- **DUO-GAIT (Zhou et al., 2023):** [Zenodo, doi:10.5281/zenodo.8244887](https://doi.org/10.5281/zenodo.8244887). Download **`processed.zip` and `interim.zip`** from this record. Keep the archives unchanged. The local preparation route below does not require `raw.zip`. The original notes recommend browser downloads after scripted requests returned HTTP 403.

The unchanged `run_v16_all.sh` and `.cmd` launchers read and write sibling directories. Arrange local files as follows:

```text
work/
├── headimu-cadence/                 # this repository; run commands here
├── .venv/                          # local Python environment
├── downloads/
│   └── dataset.zip                 # Voisard archive; not committed
├── dataset_extracted/              # output of extract_needed.py
│   └── dataset/data/.../           # preserve the archive's cohort/trial tree
│       ├── <trial>_meta.json
│       ├── <trial>_processed_data.txt
│       └── <trial>_raw_data_*.txt
├── external/duogait/
│   ├── processed.zip
│   └── interim.zip
├── results_v11/                    # regenerate before pack_v16.py
├── results_v15/                    # optional older feature analyses
├── v16_data/                       # output of pack_v16.py and prep3_v16.py
└── results_v16/                    # output of run_v16_all.sh/.cmd
```

## Reproduction

Run commands from `headimu-cadence/` with the environment activated. Do not use `--quick` for paper results. Inspect the QC outputs before the full primary run; retain the released configuration and development-selection rules.

### Prerequisite: extract Voisard and regenerate the primary outputs

```sh
python extract_needed.py ../downloads/dataset.zip ../dataset_extracted
python run_pipeline.py inspect --data ../dataset_extracted --out ../results_v11_inspect --jobs 2
python run_pipeline.py run --data ../dataset_extracted --out ../results_v11 --jobs 2
```

Extraction writes the required trial files to `../dataset_extracted/`. Inspection writes QC tables, a report, and example plots to `../results_v11_inspect/`. The full primary run writes the participant split and QC table (`qc_trials.csv`), `config_used.json`, `dev_calibration.json`, trial/segment outputs, simulation outputs, tables, and figures to `../results_v11/`. These outputs are inputs to V16; they are not bundled with the code.

### 1. Pack the Voisard signals

```sh
python pack_v16.py --data ../dataset_extracted --results ../results_v11 --out ../v16_data --skip-duogait
```

Output: `../v16_data/voisard_head_pack.npz`, containing head signals, validity masks, evaluation references, and clinical metadata. `--skip-duogait` uses the separately downloaded DUO-GAIT archives instead of the optional remote subset-download route.

### 2. Prepare the DUO-GAIT head signals

```sh
python prep3_v16.py ..
```

Input: `../external/duogait/interim.zip`. Outputs: `../v16_data/duogait_head_<condition>.npz` for the four walking conditions defined in the script, plus the inspection text and available auxiliary CSV files described in its docstring.

### 3. Run all V16 analyses

Linux/macOS:

```sh
bash run_v16_all.sh
```

Windows Command Prompt, or from PowerShell as `cmd /c run_v16_all.cmd`:

```bat
run_v16_all.cmd
```

The launcher merges the DUO-GAIT packs, runs head-only estimation and B2-t tuning/evaluation, computes statistics and gyroscope-offset failures, fits and evaluates error-risk models, performs frozen external validation and sensor-sensitivity simulations, audits older descriptive numbers, and draws V16 figures. Outputs are in:

- `../results_v16/e2e/`: segment/trial cadence and detection outputs, development tuning, parameters, statistics, and gyroscope-offset summaries.
- `../results_v16/trust/`: features, fitted risk models, scored test outputs, summaries, and error/coverage curves.
- `../results_v16/ext/`: merged DUO-GAIT pack, signal audit, pass/walk outputs, and external statistics.
- `../results_v16/sens/`: per-trial perturbation rows and sensitivity summaries.
- `../results_v16/figures/`: regenerated V16 result figures.

`run_v16_b2t_eval.py` wraps its unchanged evaluation block in `main()` and calls it only under `if __name__ == "__main__"`, so Windows-spawned workers can import the module without starting the evaluation again. The worker count and all analysis statements are unchanged. This entry-point organization was explicitly approved for the release; smoke checks do not replace full-data reproduction.

For older feature analyses referenced in the supplied documents:

```sh
python run_features.py --data ../dataset_extracted --results ../results_v11 --out ../results_v15 --jobs 2
python analysis/v15_stats.py ../results_v11 ../results_v15
python analysis/v15_extra.py ../results_v11 ../results_v15
python analysis/sr_screen.py ../results_v11 ../results_v15/sr_screen.json
```

Compare a local rerun with an independently retained output folder using `python analysis/compare_results.py REFERENCE_DIR NEW_DIR`. Historical verification claims in `README_V16.md` describe the supplied package's earlier verification, not a new full-data run of this release.

### Fixed seeds and analysis status

Participant split: **20261022**. Bootstrap and simulation: **20261023**, as documented for V16 in `README_V16.md`. No source seeds, parameters, or thresholds have been changed in this release. Older scripts retain their original seed values.

The following wording is copied unchanged from `README_V16.md`:

> No parameter
> was set by hand after looking at test or external results, except where labelled post hoc (B2-t).

`README_V16.md` does not contain a complete status list. With author approval, the following complete status wording is copied verbatim from `manuscript_build/ieee/content_supp.py`:

> Analysis status: the reference-assisted analysis (B0) and the mounting simulations are prespecified; head features beyond cadence are secondary; the step-regularity screen is post hoc; the head-only pipelines (B1, B2), the sensor-sensitivity simulations, and the error-risk models (Q2) are exploratory, B2-t is post hoc; DUO-GAIT results are a frozen external validation. Simulation results describe recorded signals with synthetic perturbations, not real re-wearing.

### Optional manuscript build

The manuscript scripts and their supplied PNG/JPEG assets are in `manuscript_build/`. Word and PDF files are excluded. Supplied figure assets are retained for the manuscript build; regenerate result figures from the public data when reproducing the analyses.

After regenerating V16 outputs, set `V16_RESULTS` to their location, then build from `manuscript_build/ieee/`. For Linux/macOS:

```sh
cd manuscript_build/ieee
export V16_RESULTS="$(cd ../../../results_v16 && pwd)"
python build_jsen.py main OUT.docx --bios
python build_jsen.py supp SUPPLEMENT.docx
```

Or Windows PowerShell:

```powershell
cd manuscript_build/ieee
$env:V16_RESULTS = (Resolve-Path ../../../results_v16).Path
python build_jsen.py main OUT.docx --bios
python build_jsen.py supp SUPPLEMENT.docx
```

The environment variable is needed because the builders' original default looks inside `manuscript_build/`. Their original manuscript content, references, and supplied author contact details are retained. The build requires locally regenerated result files and is separate from analysis smoke validation.

## Tests and validation scope

`tests/` contains a runnable synthetic archive generator rather than an assertion-based test suite:

```sh
python tests/make_synthetic_archive.py ../SYNTHETIC_TEST_ONLY 5
python run_pipeline.py inspect --data ../SYNTHETIC_TEST_ONLY --out ../SYNTHETIC_TEST_ONLY/inspect --jobs 1
```

Synthetic outputs only exercise code paths and must never be reported as study results. Release checks cover compilation of every Python source, usage/argument handling of all `run_*.py` and `analysis/*.py` scripts, synthetic archive generation/inspection, and Git ignore rules. They do not establish numerical reproduction on the two real datasets.

## Citation

Complete the publication fields when available. `CITATION.cff` contains the code title, authors, version 1.0.0, and MIT license; its DOI is blank.

```bibtex
% TODO: replace this placeholder with the verified paper BibTeX entry.
```

## Licences

The code is licensed under the [MIT License](LICENSE), copyright 2026 Qiu Qiang, Chen Shiqi, and Jin Zhenkun. The datasets follow their original licences and must be obtained from their original records. Voisard data: consult the figshare record for its original licence. **DUO-GAIT data licence: [to be confirmed].** Third-party journal logos remain subject to their owners' rights; the code licence does not grant rights to those marks.

## 中文概述

本仓库整理了论文的头戴式 IMU 步频分析、失效分析、可信度评估、外部验证及仿真代码，不包含两个公开数据集。请分别从上方 DOI 下载数据，按所示目录结构放置，并先生成 `results_v11/`，再依次运行 `pack_v16.py`、`prep3_v16.py` 和 `run_v16_all.sh`／`.cmd`。预设、探索性、事后、外部验证及仿真分析的状态见上方原文说明。合成测试数据仅用于检查程序流程，不得作为论文结果。代码采用 MIT 许可证；数据遵循原始许可，DUO-GAIT 的许可仍待确认。
