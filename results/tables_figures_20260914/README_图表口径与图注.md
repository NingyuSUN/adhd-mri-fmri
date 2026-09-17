# Tables and figures — 2026-09-14

用途：本文档汇总图表口径与图注，供论文写作与结果核查参考。ADHD-200 数据使用条款见 DATA.md；本页不构成论文正文，不用于临床诊断，也不涉及新的模型训练。

## 表格口径

- Table1：主队列，按冻结二分类标签分组；均值（样本 SD）或中位数 [Q1,Q3]。连续值为填补前观测值，并列缺失人数；类别百分比分母为相应列总人数。
- 年龄/性别采用实际模型输入 participant_age / participant_sex_male。这里是记录的 sex，不等于 gender identity。标签1按项目映射称 ADHD，标签0称对照，未独立重审临床诊断。
- 头动 pct_fd_gt_0p2 原值为 0–1 比例，显示为百分比乘100；TIV 从 mm³ 转 mL 除1000。FD/DVARS 保留元数据量纲，采集与计算来源单位需在正式投稿前核实。没有按异常值重新删人。
- Table2：CV 是平均折 AUC，经重复汇总；不是将所有重复预测混合后算的 AUC。LOSO 配对加权与等站点宏平均分别列出，不互换。7 个展示模型按研究角色固定；17 个输出全表在 TableS2，未按高分筛选。
- Table3：主比较及原始区间；TableS7/S8 为后来增加的区间敏感性，不能混为同一种 bootstrap。
- Table4/TableS3：事后描述性分解。所有 QC 队列重叠，未进行独立组差异检验。
- TableS5：训练/验证/测试人数按66个单元列出，合计不能当作参与者人数。

## 方法边界

LOSO 使用六个训练站点内一次85/15划分，选择后未在全六站上重新拟合。当前结果反映这套实际执行流程。完整复现仅从冻结时间序列和体积派生数据开始；原始 MRI 预处理、专家完整 QC、外部验证未由此建立。

## 图注

### Figure1_participant_flow

从已核实的 378 人配对队列开始的 QC 流程。3 人影像质量失败；其余 375 人构成含 HOLD 队列。再排除 25 个 HOLD 得到主队列 350 人；再排除 48 个信号警告得到无警告队列 302 人。三个队列重叠。QC 为抽样辅助审查，不等于专家全体积判定。更早的数据招募/筛选流程未在本图重建。

### Figure2_primary_contrast

主要比较：full_fusion_structural_mlp − full_functional_mlp。CV 为 15 折差值的均值及原始修正 t 90% 区间；LOSO 为站点内病例–对照配对加权 ΔAUC 及原始 10,000 次站点内受试者 bootstrap 90% 区间。灰带为 ±0.02。两类区间的条件不同；LOSO 不包含重新训练或新站点抽样的不确定性。

### Figure3_QC_decomposition

事后分解 QC 队列变化。共同测试参与者与固定主队列站点权重下，分解拟合流程、评估样本组成和站点权重贡献。分量精确重构总差，属于描述性分解，不是因果效应。

### Figure4_NYU_selector_stability

NYU 留出折最终结构融合权重的选择稳定性。只在其余训练站点的内部验证集中，按站点和标签 bootstrap 1,000 次；拟合模型、上游权重和早停保持固定。不是 NYU 测试数据选参，也不是全流程置信区间。

### FigureS1_CV_models

主队列 7 个按研究角色固定展示的模型，与 Table2 一致。点为平均折 AUC；误差条为5次重复均值的最小值至最大值，不是置信区间。17 个输出完整数值见 TableS2。

### FigureS2_calibration

冻结重复 CV 预测的描述性校准曲线。主队列 n=1750 指 350 人各 5 次预测；不是 1750 位独立参与者。加权训练输出不是已验证的个体诊断风险。

### FigureS3_site_contributions

站点对配对加权结果的贡献。NYU 占主队列人数 39.7%，占站点内正负配对权重 67.07%；其主队列结构增量为零，不能把总体正增量归因于 NYU。

### FigureS4_CV_interval_sensitivity

对自由度与 test/fit 比例约定的事后区间敏感性。各区间来自同一批结果，不是独立重复研究。

### FigureS5_LOSO_contrasts

主要结构增量在各站点和 QC 队列的估计，误差条为原始95%站点内受试者 bootstrap 区间。不同于 Figure2 的总体90%区间。区间条件于已观察站点及冻结模型；小站点估计不精确，实际LOSO没有选择后全训练站点重拟合。


## 文件与复现

打开 index.html 查看全部主表与图；tables 为可编辑 CSV；figures 为 PNG/PDF；source_aggregates 为本次新汇总及冻结输入哈希；source_results 为已有图表数值来源。scripts 为本次整理代码快照，需要原项目路径/服务器输入执行参与者汇总；导出的包不含个体记录或原始影像。

source_results/original_cv_contrast_stats.csv 与 original_loso_contrast_stats.csv 支持 Figure2/Table3；qc_decomposition.csv 支持 Figure3/Table4；selector_alpha_distribution.csv 支持 Figure4；original_cv_primary_summary.csv 支持 FigureS1；original_calibration.csv 支持 FigureS2；site_contributions.csv 支持 FigureS3；cv_interval_audit.csv 支持 FigureS4；original_loso_per_site_deltas.csv 支持 FigureS5。新分析并未因展示而重新选择参数。

验证：参与者分组人数、加权均值、21组站点/队列既有计数、输入哈希、CSV结构和HTML链接均通过；9幅图已逐一检查。原历史图和冻结运行未被覆盖。
