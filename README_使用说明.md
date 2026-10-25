# 头部IMU步态节律分析代码（Voisard 2025 公开数据集）

本代码实现论文初稿 V11 第 III–IV 节的全部分析：信号级质控、A0/A0g/A1/A2/A2-R 与自相关法、下背部参照、开发集参数确定、刚体旋转与杠杆臂仿真、跨就诊重测信度，以及论文所需的全部表格和图。

## 0. 一键运行（推荐）

数据压缩包放在 `Voisard2025\downloads\dataset.zip`、本文件夹放在 `Voisard2025\headimu_code` 时，直接双击 `run_all.cmd` 即可。它会：

1. 用 `Voisard2025\.venv` 里的 Python（没有则用系统 Python）；
2. 从压缩包中只解压分析需要的文件到 `Voisard2025\dataset_extracted`（约 4–5 GB，只做一次）；
3. 运行格式检查，结果在 `Voisard2025\results_v11_inspect`；
4. 运行全部分析，结果在 `Voisard2025\results_v11`。

全程不需要手动输入命令。窗口最后显示 DONE 即完成；如显示 FAILED，把窗口截图发给我。

## 1. 准备数据

你电脑上的 `../downloads/Voisard2025` 目前只有 1 个试次（HS_1_3），是之前用 HTTP 分段方式单独取出的。正式分析需要完整归档（约 2.19 GB，1356 个试次）：

1. 用 `Voisard_2025_HS_1_3_Windows一键获取工具_V2` 运行 `Windows_双击下载.cmd`，选**菜单 2**完整下载（可断点续传）。
2. 解压到任意文件夹，例如 `../dataset_extracted`。解压后的结构是 `dataset/data/{healthy,neuro,ortho}/队列/受试者/试次/`，每个试次 7 个文件。`--data` 指向解压后的根目录即可，代码会递归查找。

## 2. 安装依赖（一次）

```
pip install numpy scipy pandas matplotlib openpyxl
```

需要 Python 3.10 及以上。

## 3. 先跑格式检查（必须）

```
python run_pipeline.py inspect --data ../dataset_extracted --out inspect_out --jobs 4
```

逐项核对屏幕输出和 `inspect_out` 文件夹：

| 检查项 | 正常表现 | 不正常时改 config.json 的哪里 |
|---|---|---|
| `HE_static_gnorm_mps2` 中位数 | 约 9.8 | `io.acc_unit` 设为 `"mps2"` 或 `"g"` |
| `HE_turn_angle_deg` 中位数 | 约 170–180 | `io.gyr_unit` 设为 `"dps"` 或 `"rads"` |
| `inspect_*.png` 中竖线（参考足跟着地）与左足角速度波形 | 每个步态周期对齐 | `io.event_pair_order`（TO/HS 顺序）、`io.event_index_unit` |
| `sensor_type_counts` | XSens 约 569、Technoconcept 约 787 | `io.meta_keys.sensor_type` |
| `meta_keys_first_trial` | 能看到事件、转身边界、就诊、传感器字段 | `io.meta_keys` 里补上实际字段名 |
| `HE_static_xfrac` 中位数 | 约 0.9 以上（数据论文报告 93%） | 若很低，说明 X 轴不是颅尾方向，改 `detect.a0_axis` |

确认无误后再进入下一步。**config.json 中 `dev_select` 以外的参数，在看到测试集结果之后不得修改。**

## 4. 正式运行

```
python run_pipeline.py run --data ../dataset_extracted --out results --jobs 6
```

可先加 `--quick` 做一次快速试跑（重复次数减少，结果不可用于论文）。完整运行时间取决于 CPU，一般在一小时以内。

## 5. 输出文件与论文对应关系

| 文件 | 论文位置 |
|---|---|
| `table_inclusion.csv` | 表 II（纳入与排除） |
| `table_signal_qc.csv` | 表 III（信号级质控） |
| `table_primary.csv`、`table_paired_comparisons.csv` | 表 IV（主要结局）及 V-B 节 |
| `table_event_matching.csv` | V-B 节次要指标 |
| `table_strata.csv` | 表 V（队列、传感器型号、年龄分层） |
| `table_sim_rotation.csv`、`table_sim_leverarm.csv` | 表 VI（安装误差仿真） |
| `table_rewear.csv` | 表 VII（重测信度） |
| `table_gating.csv`、`table_turn_detection_by_cohort.csv` | 表 VIII（转身识别与门控） |
| `fig3_inclusion_flow` | 图 3（纳入、排除与划分流程） |
| `fig4_example_trial`、`fig5_bland_altman`、`fig6_cohorts`、`fig7_simulations` | 图 4–7 |
| `fig8_rewear` | 图 8（重测信度散点） |
| `fig9_gating` | 图 9（门控误差—覆盖率） |
| `figS1_signal_qc` | 补充图 S1（信号级质控分布） |
| `figures_schematic/make_fig1.py`、`make_fig2.py` | 图 1（佩戴与杠杆臂示意）、图 2（流程图） |
| `dev_calibration.json` | III-F 节：开发集确定的通带下限、滞后、门控阈值 |
| `numbers_for_paper.json` | 全部数值汇总，便于回填正文 |
| `qc_trials.csv`、`test_*.csv`、`sim_*.csv` | 逐试次原始结果，供核查和补充材料 |

## 6. 关于 tests 文件夹

`tests/make_synthetic_archive.py` 生成的是**合成测试数据**，只用来检查代码能否跑通，**不得用于任何论文结果**。

## 7. 已核实与仍需注意的地方

已对照数据论文（Sci Data 12:1674，表 3、5、9）和真实试次 HS_1_3 核实：原始文件为制表符分隔，加速度单位 m/s²、角速度 rad/s；元数据键为 `leftGaitEvents`/`rightGaitEvents`（每对为 [足尖离地, 足跟着地] 的采样序号）、`uturnBoundaries`（采样序号）、`session`、`sensor`、`pathologyKey`；XSens 量程 ±160 m/s²、±2000°/s，Technoconcept ±6 g、±500°/s。

**重要：** 原始文件保留各传感器自身坐标系（HS_1_3 头部重力在 −Y 轴），数据集提供者在预处理文件中统一了坐标轴（头部、下背部 X 轴为颅尾方向）。因此 `config.json` 中 `io.signal_source` 默认取 `processed`，算法读取预处理文件中的 `HE_Acc_*`、`HE_Gyr_*`、`LB_Acc_*`、`LB_Gyr_*`，原始文件只用于缺口标记和信号级质控。

在 HS_1_3 上的检查：静立重力模长 9.80 m/s²，统一坐标系中重力 X 轴分量比例 0.99，转身积分角度 192°，主频/参考步频 1.02。以上只用于确认代码与格式，不是研究结果。

## 论文结果图（图4–图9，期刊单栏版式）

`run_pipeline.py report` 生成的图用于快速检查；投稿用的图4–图9由下面的脚本从同一批CSV重新绘制（单栏3.5英寸、统一字体与配色）：

```
..\.venv\Scripts\python.exe figures_results\make_result_figs.py ..\results_v11 ..\dataset_extracted\dataset\data ..\figures_v11
```

图3（纳入流程）与补充图S1仍由 `report` 生成。
