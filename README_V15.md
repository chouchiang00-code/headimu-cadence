# V15 补充分析（特征层级、可靠性、安装敏感性、VGA）

双击 `run_v15.cmd` 即可。它只读取 `Voisard2025\dataset_extracted` 和 `Voisard2025\results_v11`（不修改），结果写到新文件夹 `Voisard2025\results_v15`：

| 文件 | 内容 |
|---|---|
| clinical_meta.csv | 每个试次的 VGA、TUG、专科量表、患侧、性别、身高、体重 |
| features_segments.csv | 每个直行片段的 9 个头部特征 + 2 个固定轴对照 + 足部参考对应量 |
| sim_features.csv | 测试集试次在刚性旋转（10–45°，各 10 轴）和杆臂（2/4/8 cm，各 10 方向）下的特征值 |
| v15_summary.json, v15_tables\*.csv | 效度、试次间信度、安装敏感性、VGA 关联与增量价值、筛查按 VGA 分层 |
| sr_screen.json, sr_curve.json | 步态规律性筛查（与论文 V14 一致） |

特征定义全部写死在 `headimu\features.py` 顶部，参与者划分、频带和时滞全部沿用 results_v11，不重新选择任何参数。
完成后把整个 `results_v15` 文件夹（约几十 MB）传给我即可。
