# ADHD 结果专册：2026-09-17

将用户指定的两套课件整理为53页结果PPT：26页主线、27页补充结果。所有页有详细中文演讲者备注，共48,774字符；包含37个原生表格、3个可编辑图表、9幅冻结科研图。长补表展示原课件摘要，并随交付包附完整14份CSV。

## 输入与版本

- `ADHD_fMRI.pptx`（58页）与 `ADHD_结构MRI与多模态融合_图表讲解版_20260914.pptx`（91页），来自用户指定的ADHD-ppt文件夹；SHA-256见content.json。
- 冻结图表：`results/tables_figures_20260914/`。
- 本地证据基线：`ed50a60c6da9f898160fb6a17ba4faa3cf0011a8`。
- 本轮只读核对GitHub main：`3f39504e08141dee9aa751f66a1eb08973b56961`；图表目录与本地无差异。
- 复用本地2026-09-15 AI审阅与2026-09-16定向已发表文献对照；未将这些本地补充称为GitHub已发表成果。

## 文件与重建

`content.json`是逐页内容、详细备注、来源页码与元数据的可审阅主文件。它保存的是聚合图表与研究说明，没有个体MRI/标签记录。`build.py`使用python-pptx和Pillow；`render.mjs`使用Codex bundled Node的artifact-tool，渲染不修改交付PPT。

```bash
python build.py --repo REPO --output-dir OUTPUT
node render.mjs OUTPUT/ADHD_结果与论文主线_详细备注版.pptx OUTPUT/preview
python validate_package.py --content content.json --source-dir ORIGINAL_DECK_DIRECTORY --output-dir OUTPUT
```

输出：PPTX、同内容Markdown讲稿、新旧页码CSV、完整图表附件、内容JSON及validation.json。实际交付保存到用户指定ADHD-ppt目录下的`ADHD_结果提取与论文主线_20260917`，原始两套课件未修改。大型二进制成品留在用户输出目录，本仓库仅保存本轮可重建内容和代码。

## 本轮更改与科学边界

1. 删除基础教学/课堂练习，提取结果并按研究论证重排。将旧柱图的AUC×100换算到0–1，保留原缓存数值。
2. 统一称“基础信息/扫描质量对照”，避免把头动、TIV误称完全无影像来源。
3. CV按各折AUC汇总，不与pooled AUC混淆；历史409/378人实验不与350人融合直接作配对差值。
4. Table3 LOSO、Figure2和FigureS5显式保留原始区间，并标注同分算法缺陷真实影响待核验。未运行真实同分审计、未重算这些区间。
5. 论文方向是PROPOSED：增量预测及其对QC、内部选择与评估目标的敏感性；不宣称临床诊断、新颖性已经确认或保证发表。
6. 文献页复用已经核对的文献报告，没有把本轮称为新系统综述。没有新增训练、MRI原图QC或外部验证。

## 验证

- 53页成品备注逐页与内容源一致。
- 30页提取表格在术语及换行规范化后与原PPT逐单元一致；第22页复现表由原第53页文字重新排表。
- 9幅冻结PNG在PPT包内与原文件逐字节一致；3张原生图缓存值与源数据一致。
- PPTX压缩包、内部关系目标、形状页面边界均通过检查。
- 53页使用artifact-tool实际渲染，并逐页通过五张联系表检查；密集的TableS8另以全分辨率检查，未见越界或遮挡。这不是在Microsoft PowerPoint内实机验收。
- 图表构建库使用负数坐标轴ID，初次渲染器拒绝导入；已转换为等价32位无符号ID，交叉引用同步保留，重新渲染53页通过。Windows控制台编码也已修复。
- 原始两套PPT的SHA-256未变化。结果包检查记录见validation_receipt.json。

这些检查确认交付内容与版式，不构成科学、影像或临床验证。用户理解状态为YELLOW（尚未评估）；不因AI完成交付而推定理解。
