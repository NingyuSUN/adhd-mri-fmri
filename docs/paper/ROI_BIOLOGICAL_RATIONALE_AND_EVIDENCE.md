# ROI 生物学依据与证据映射

**状态约定**：与 [handoff.md](../../handoff.md) 一致：VERIFIED＝已核实；INFERRED＝证据支持的推断；PROPOSED＝建议但未执行；NOT VERIFIED＝尚未核实。

## 0. 结论先行

用户在早期 ROI-guided CNN 分支中选择的脑区（额叶皮层、扣带皮层、丘脑-纹状体）**确实对应 ADHD 神经影像学中一套成立且被反复验证的经典假说**——"额叶-纹状体-丘脑环路"（frontostriatal/frontostriatal-thalamic circuit）功能失调模型。这套假说在教学笔记本（`ADHD_sliceCNN.ipynb` 第54个 cell）中有完整、自洽的论证，但**没有嵌入具体文献引用**。本文档做两件事：

1. 精确核实代码实际使用了哪个图谱、哪些区域、产出了哪些特征列（VERIFIED，来自 git 历史与图谱代码本身）。
2. 用 PubMed 检索到的、与这套论证逐条对应的经典文献，把"教学笔记本里的生物学论述"和"可核查的已发表证据"对上号（本节引用均来自 PubMed，含 DOI）。
3. 把项目里三条不同特征路线（早期20列强度、后期98项结构体积、424维功能连接）各自的图谱/工具来源全部核实清楚——三者互不相同，也不应互相混为一谈（见第3节）。

**重要边界**：文献支持的是"额叶-纹状体-丘脑环路在 ADHD 中功能/结构异常"这一**大类假说**，不是证明"本项目选的这15个具体子区域组合"就是原作者当年心里想的那几篇论文。这一点在第4节明确标注。

## 1. 代码实际使用的图谱与区域（VERIFIED）

来源：`utils/roi.py`（已从主分支删除，历史提交 `a43460c^` 中可读到，见 `git show a43460c^:utils/roi.py`）。

- **图谱**：Harvard-Oxford（`cort-maxprob-thr25-2mm` + `sub-maxprob-thr25-2mm`，经 nilearn 获取）。
- **皮层区域（10个，不分左右，因为 cort-maxprob 图谱本身不分侧）**：
  Frontal Pole；Superior Frontal Gyrus；Middle Frontal Gyrus；Inferior Frontal Gyrus, pars triangularis；Inferior Frontal Gyrus, pars opercularis；Frontal Medial Cortex；Frontal Orbital Cortex；Paracingulate Gyrus；Cingulate Gyrus, anterior division；Cingulate Gyrus, posterior division。
- **皮层下区域（5个 × 左右两侧 = 10个）**：Thalamus、Caudate、Putamen、Pallidum、Accumbens（sub-maxprob 图谱按左右分侧）。
- 合计 10 + 10 = **20 个区域**，与 `reproduction/legacy/build_multimodal_manifest.py:286` 注释"20 atlas ROI mean subject-zscored T1 intensities"、`run_functional_fusion.py:159-161`（`roi_columns` 断言长度为20）完全对应。**这解开了 handoff.md 第4节"20项历史ROI特征"的具体构成——此前只知道是20列，现在知道是哪20个解剖区域。**
- **这20个区域在早期管线里有两个用途，必须分清**：
  1. 作为 **mask** 决定 ROI-guided CNN 该从 T1 上截取哪些轴位切片（切片选择，不是直接的表格特征）。
  2. 作为 **20列表格特征**（每区域受试者内 z-标准化平均 T1 强度）喂给后期的 LR 融合模型（`run_functional_fusion.py`）。
  代码注释明确写着"not volume or cortical thickness"——**这20列是强度均值，不是体积或皮层厚度**。

## 2. 教学笔记本中的生物学论证（VERIFIED，来自 Google Drive `Colab Notebooks/ADHD_sliceCNN.ipynb` 第54个 cell）

笔记本把20个区域归纳为三个功能模块，逐一给出理由：

| 模块 | 区域 | 笔记本给出的理由 |
|---|---|---|
| 前额叶皮层（执行控制） | 额极、额上回、额中回、额下回（三角部/盖部）、额内侧、额眶部 | 注意力维持、行为抑制、工作记忆、决策——对应 ADHD 核心症状 |
| 扣带皮层（注意调度/冲突监控） | 旁扣带回、前扣带回、后扣带回 | 前扣带＝冲突监控/错误检测/注意资源分配；后扣带/旁扣带＝自我监控，关联默认模式网络（DMN）在任务态下抑制不足 |
| 丘脑-纹状体（经典核心环路） | 丘脑、尾状核、壳核、苍白球、伏隔核 | "前额叶→纹状体→丘脑→前额叶"环路，负责行为启动/抑制、冲动控制、奖赏动机；伏隔核对应奖赏敏感性，该环路是多巴胺能药物的作用靶点 |

笔记本原文没有引用具体论文；下节用 PubMed 补上。

## 3. 对应的已发表文献（VERIFIED，检索自 PubMed，见文末索引）

| 笔记本论证 | 对应文献 | 文献实际结论 | 是否直接支持笔记本原话 |
|---|---|---|---|
| 额叶-纹状体环路是 ADHD 的核心神经生物学基础 | Bush, Valera & Seidman 2005 [1] | 综述指出"额叶-纹状体结构功能失调（外侧前额叶皮层、背侧前扣带皮层、尾状核、壳核）很可能是 ADHD 病理生理的一部分" | 直接支持，且区域列表（外侧PFC/背侧ACC/尾状核/壳核）与本项目高度重合 |
| PFC/ACC/基底节/丘脑在功能影像上普遍低激活 | Dickstein, Bannon, Castellanos & Milham 2006（ALE 元分析）[2] | 对16项功能影像研究做体素级元分析，发现 ADHD 患者在前扣带、背外侧前额叶、眶下前额叶皮层及基底节、丘脑区域存在一致的低激活模式 | 直接支持，区域列表几乎覆盖本项目全部15个命名区域 |
| 结构像上纹状体存在异常 | Ellison-Wright, Ellison-Wright & Bullmore 2008（结构元分析）[3] | 对7项体素形态学研究做元分析，发现 ADHD 患者右侧壳核/苍白球区域灰质体积显著减少，提示额叶-纹状体环路的解剖学标志 | 直接支持苍白球、壳核作为结构层面的关注区域 |
| 背侧额叶-纹状体环路负责认知控制，腹侧环路负责奖赏 | Durston, van Belle & de Zeeuw 2010 [4] | 提出区分背侧额叶-纹状体（认知控制）与眶额-纹状体（奖赏加工）两条环路，为 ADHD 神经生物学亚型提供模型 | 支持笔记本"尾状核/壳核＝行为控制，伏隔核＝奖赏敏感性"的区分逻辑 |
| 后扣带/DMN 与任务态抑制不足有关 | Castellanos & Proal 2012 [5] | 把经典"额叶-纹状体模型"扩展到默认模式网络等大尺度静息态网络，讨论 DMN 与 ADHD 行为变异性的关系 | 支持笔记本里"后扣带/旁扣带关联 DMN 任务态抑制不足"的表述，但这是网络层面的假说，不是逐区域的因果证明 |
| 近期综合结构+功能证据 | Mizuno et al. 2025（综述）[6] | 总结 T1 结构像显示额叶/基底节/小脑灰质体积下降及皮层成熟延迟；rs-fMRI 显示 DMN、额顶网络、突显网络连接异常 | 提供2025年的最新汇总视角，确认该假说至今仍是主流框架，而非过时理论 |

## 4. 必须说清楚的限制（NOT VERIFIED，不能回避）

1. **这不是逐区域的一一因果证明**。上述文献是"额叶-纹状体-丘脑环路"这个大类假说的支持证据，其中大部分是跨多项原始研究的**元分析/综述**，报告的是**群体层面统计效应**，不是"这个区域在 ADHD 个体预测里一定有判别力"的保证——事实上本仓库自己的实验结果（strict LOSO 下 ROI-CNN pooled OOF AUC 仅 0.470，年龄+性别基线 0.619 更高）已经说明"生物学假说成立"和"该假说能支撑可靠的个体预测"是两件不同的事，不能互相替代（呼应 handoff.md 第1节"分类权重、归因图、统计关联不等于因果机制"）。
2. **无法证明这就是作者当年查阅的原始文献**。以上6篇是本轮基于笔记本论证内容检索到的、内容高度吻合的经典/权威文献，但笔记本本身没有留下引用记录，不能倒推"作者当时读的就是这几篇"。如果后续要在论文里正式引用，应以这些文献的科学内容是否站得住脚为准，而不是声称"這是原始依据"。
3. **20列历史ROI特征、98项后期结构特征、424维功能特征——三条路线的图谱来源现已全部核实清楚，三者互不相同**：

### 3a. 20列历史特征＝Harvard-Oxford（VERIFIED，见第1节）

15个命名区域（10皮层+5×2皮层下），本轮已从 `utils/roi.py` 逐字核实。

### 3b. 424维功能特征＝BrainLM 官方 A424 图谱：Glasser HCP-MMP皮层 + 皮层下 + 小脑（VERIFIED，2026-09-18 用原始图谱文件核实，纠正此前记录）

**纠正**：本文档早前版本写"A424 = AAL-424 图谱"，依据的是网络检索的二手转述（BrainLM Hugging Face 模型卡文字）。这轮直接找到并解析了 BrainLM 官方仓库（`github.com/vandijklab/BrainLM`，`ADHD_fMRI_BrainLM_A424.ipynb` 第4个 cell 里明确 `git clone` 的正是这个仓库）里的原始图谱定义文件 `toolkit/atlases/A424.dlabel.nii`（CIFTI 格式，自带424个区域的解剖标签表），**确认"AAL-424"这个说法是不准确的二手转述，真实图谱另有其名**：

- **索引1-360（皮层，共360个区域）**：命名格式为 `R_V1_ROI`、`L_p24_ROI`、`R_8Av_ROI` 等——这是 **Glasser et al. 2016（HCP Multi-Modal Parcellation, MMP1.0）** 的标准180区/侧命名，不是 AAL 命名（AAL 区域名类似 "Frontal_Sup_L"，和这里完全不同）。
- **索引361-396（皮层下+丘脑，共36个区域）**：`mAmyg/lAmyg`（杏仁核内侧/外侧）、`rHipp/cHipp`（海马前/后）、`vCa/dCa`（尾状核腹侧/背侧）、`GP`（苍白球）、`NAC`（伏隔核）、`vmPu/dlPu`（壳核腹内侧/背外侧）、以及8对功能连接定义的丘脑分区（`mPFtha`内侧前额叶连接丘脑、`mPMtha`内侧运动前区连接丘脑、`Stha`躯体感觉连接丘脑、`rTtha/cTtha`颞叶连接丘脑、`PPtha`后顶叶连接丘脑、`Otha`枕叶连接丘脑、`lPFtha`外侧前额叶连接丘脑，各左右一对）——命名风格符合基于皮层连接目标定义丘脑分区的经典方法（如 Behrens et al. 概率纤维束成像丘脑连接分区），具体引用本轮未做穷尽式核实。
- **索引397-424（小脑，共28个区域）**：`Left/Right/Vermis_I-IV`、`_V`、`_VI`、`_Crus_I`、`_Crus_II`、`_VIIb`、`_VIIIa`、`_VIIIb`、`_IX`、`_X`——标准小脑叶分区命名（左/右半球+蚓部，按小叶）。
- 360+36+28 = **424**，与项目实际使用的维度精确吻合。

**列序映射已 100% 核实，不是推测**：BrainLM 官方工具脚本 `toolkit/BrainLM_Toolkit.py` 里 `convert_fMRIvols_to_A424()` 函数的抽取循环是：
```python
for i in range(1, nParcels + 1):
    ind = (label == i)
    ...
    pmTS[:, i - 1] = np.nanmean(y, axis=1)
```
即输出的第 `i-1` 列（0基）对应图谱整数标签值 `i`（1基），与 dlabel 文件里标签表的键值编号完全一致。因此：**本项目 `timeseries.npz` 里的第 j 列（j=0..423），解剖名字就是 dlabel 标签表里键值 j+1 对应的名字**——这条映射链是从"这个项目实际克隆的官方仓库→官方抽取代码→官方标签表"逐环核实的，不是猜测或近似。

**结论**：A424 是 BrainLM 团队自己定义的复合图谱（Glasser HCP-MMP 皮层 + 类 Tian/Melbourne 命名风格的皮层下 + 标准小脑叶），和结构侧用的 Harvard-Oxford（ROI-CNN）、SynthSeg/Desikan-Killiany（98项结构特征）**是第三套完全独立的图谱体系**，区域定义、命名规则、粒度都不同，三者之间没有共享的解剖学定义可以直接对应。

**下一步要做但本轮未做**：360个 Glasser 皮层区域的缩写代码（如 `p24`、`a32pr`、`8Av`、`47l` 等）需要按照权威的"Glasser 区域→脑叶/功能模块"对照表（该表在 Glasser 2016 论文的补充材料或社区维护的对照CSV里）才能可靠地筛出"前额叶/扣带回"子集——本轮没有找这张表，**没有凭缩写代码自己猜哪些属于PFC/扣带**，因为猜错的代价是让整个功能侧对照实验建立在错误的区域选择上。皮层下+丘脑部分（36个区域）因为命名本身就是完整单词（thalamus/caudate/putamen/pallidum/accumbens的对应缩写），可以直接可靠匹配，不需要额外查表。

### 3c. 98项后期结构特征＝SynthSeg 2.0（VERIFIED，2026-09-17 服务器只读核实）

本地 git 仓库和 Google Drive Colab 笔记本里确实找不到（排查过程见上一版本的记录，结论不变：`run_structural_fusion_v2.py`/`run_structural_fusion_locked.py` 只消费一个预先算好的 `volume_fractions` 数组，两份 manifest 也没有分割脚本条目，10本 ADHD Colab 笔记本逐一搜过 aparc/aseg/FreeSurfer/FastSurfer/SynthSeg/Desikan 等关键词均无结果）。经你授权，只读登录 SV002 服务器（未修改、未重跑任何东西），在 `~/ML/synthseg_pilot_20260907/` 找到了完整的生成链路：

- **工具**：SynthSeg 2.0，通过 FreeSurfer 官方分发的模型权重运行（`model_provenance.json` 记录了 `synthseg_2.0.h5`、`synthseg_parc_2.0.h5`、`synthseg_qc_2.0.h5` 三个权重文件，均从 `surfer.nmr.mgh.harvard.edu` 官方服务器下载并 SHA256 校验通过，指向 FreeSurfer 官方仓库 `github.com/freesurfer/freesurfer`）。
- **运行方式**：`protocol.json` 明确写"SynthSeg2.0 standard with parcellation, volumes, QC, resampled image"——即标准（非 fast/robust/crop）模式，开启皮层分区（`--parc`）、体积输出、自动QC。
- **规模**：从2026-09-07的3人可行性试点（`SERVER_PILOT_HANDOFF.md`：NYU/OHSU/NeuroIMAGE各1人，每人产出"101 volume measurements and 8 predicted QC scores"）扩展为2026-09-08至09-09的批量跑（`expansion_pipeline_status.json`：17批×21人=357人，路径 `runs/standard_20260908_*`~`runs/standard_20260909_*`），时间上正好衔接后续 `structural_qc_locked_20260909` 这个 QC 锁定队列。
- **101→98的差异**：试点记录的是每人"101项体积测量"，而融合分析文档说的是"98项区域体积/TIV分数"，两者不完全相等——可能是后续流程剔除了背景/非脑组织等少数非解剖区域列，具体裁剪逻辑本轮未继续追（不是关键缺口，工具身份已经实锤）。
- **可引用的方法学文献**：SynthSeg 的皮层分区（cortical parcellation）+自动QC+颅内体积（ICV）功能，官方 README 明确要求引用：Billot, Magdamo, Cheng, Arnold, Das & Iglesias, "Robust machine learning segmentation for large-scale analysis of heterogeneous clinical brain MRI datasets," *PNAS* 2023;120(9):e2216399120. [DOI](https://doi.org/10.1073/pnas.2216399120)（经 PubMed 核验，PMID 36802420）。

**结论**：早期 ROI-CNN 用 Harvard-Oxford 图谱挑15个假说驱动区域，后期98项结构特征用 SynthSeg 2.0 做**全脑自动分割**（不是假说驱动的子集选择）——**两条路线在解剖学定义上完全独立，不能假设后者继承了前者"额叶-纹状体-丘脑"的区域范围**。这是本文档第0节结论的直接延伸：生物学假说（第2、3节）驱动了最早的 ROI-CNN 设计，但没有延续进后期结构+功能融合分析的特征工程里——后者是无先验假设的全脑分割+模型自己在训练时学权重。写论文方法部分时，这一点必须明确分开描述，不能笼统地说"基于ADHD相关脑区"。

## 5. 建议的下一步（PROPOSED，未执行）

1. （可选）如果需要论文正文精确到"98个区域分别叫什么名字"，可以进一步在服务器上读一份具体输出 CSV 的列名（`runs/standard_2026090*/*.csv` 一类路径），核对 SynthSeg 内置皮层图谱的具体区域命名规则；本轮未做，因为工具身份的核心问题已经解决，不是当前论文主线的阻塞项。
2. 论文方法部分需明确写清楚："早期 ROI-CNN 的假说驱动区域选择（Harvard-Oxford，15区）"和"后期结构+功能融合分析的全脑自动分割（SynthSeg 2.0，全脑无先验筛选）"是两种不同设计哲学，后者不继承前者的解剖假设。
3. 需要找到权威的"Glasser HCP-MMP 区域→脑叶/功能模块"对照表，才能可靠筛出360个皮层区域里的前额叶/扣带回子集（见3b节末尾）；皮层下+丘脑的36个区域已可直接匹配，不需要这一步。
4. 如果用户希望论文正式引用本文档第3节的文献，建议逐篇由用户或人类审阅者复核摘要匹配度后再定稿引用列表（本文档的检索由 PubMed 工具完成，DOI 已核验存在，但未做全文通读式的引用适配审查）。

## 6. 探索性对照实验：生物学子集 vs 全自动分割（2026-09-18，CV only）

用户要求直接检验：把98区域自动分割收窄到"有生物学证据支持的额叶-纹状体-丘脑核心回路"子集，能不能达到和全自动分割相当或更好的效果。本节记录这次探索性实验的设计、结果和限制。

### 设计

- **特征子集**：从第1/3c节核实的98列 SynthSeg 输出里，按 Desikan-Killiany 皮层区域名+皮层下结构名精确匹配出 **36 列**——9个前额叶亚区（含额极）+4个扣带回亚区（前扣带尾/喙侧、后扣带、峡部）+ 丘脑/尾状核/壳核/苍白球/伏隔核，左右各一。**明确不含**杏仁核、海马——原教学笔记本自己把这两个标为"extended/limbic"可选项并选择不用（`USE_EXTENDED=False`），本实验照此边界，不擅自加料。完整列名清单：`results/structural_biological_subset_cv_20260918/bio_subset_columns.json`。
- **数据与切分**：复用已冻结的 `primary` QC 队列（350人）和原始5次×3折切分身份（`runs/demographic_increment_20260908_locked_v2/splits.csv`），**未做任何重新切分**。
- **模型**：与冻结的 `run_structural_fusion_locked.py` 完全一致的设计——L2逻辑回归（C∈{0.01,0.1,1,10}，验证集AUC选参，平局取更小C）+ 64/16 GELU MLP（3个种子1200/2200/3200+fold，等权集成），StandardScaler 只在训练折拟合。
- **范围**：只做 CV（按用户要求，本轮不跑 LOSO）。新脚本 `reproduction/exploratory/structural_biological_subset_cv.py`，只读原始冻结数据，**没有修改任何冻结文件**，输出写入全新目录 `runs/structural_biological_subset_cv_20260918/`（服务器）。
- **有效性检验**：同一脚本同时用完全相同的代码重新拟合了"全98列"基线（`structural_lr_full98`/`structural_mlp_full98`），作为内部一致性检查——不是为了替代已发表的数字，而是验证这次复现的数据/切分/训练流程是否正确。

### 结果

| 模型 | 生物学子集(36列)CV均值 | 全98列CV均值（本次复现） | 全98列CV均值（原发表） | 差距 |
|---|---:|---:|---:|---:|
| 逻辑回归 | 0.5673 | 0.6176 | 0.6176 | **−0.0503** |
| MLP | 0.5665 | 0.6239 | 0.6256 | **−0.0574**（对比原发表为−0.0591） |

复现的全98列逻辑回归结果与原发表数字**完全一致**（0.617601 vs 0.6176），MLP复现结果与原发表数字相差0.0017（神经网络训练本身存在的随机噪声范围内）——说明本次数据/切分/训练流程的复现是可信的，两组数字可以直接比较。

逐折拆开看（`repeat_metrics.csv`）：**5次重复里，生物学子集在逻辑回归和MLP两种模型上都是5:0全部低于全98列**，不是均值被个别折拉低，是稳定的方向性差距。

### 解读边界（务必写清楚，不能夸大）

1. **这是探索性单次CV跑分，不是本项目自己要求的确证性统计框架**。没有像 v2 分析那样做 Nadeau-Bengio 校正区间、TOST 等效检验或站点分层 bootstrap；上表的"5:0"只是描述性的一致性观察，不是显著性结论。如果要写进论文正文，需要按项目已有标准补上正式的不确定性量化。
2. **这不能证明"额叶-纹状体-丘脑假说是错的"**。它只能说明：在**这一套 SynthSeg 体积特征 + 这一套 LR/MLP 训练设置**下，把特征限制到这36个区域比用全部98个区域预测力更弱。可能的原因包括但不限于：（a）该假说本身在群体统计层面成立，但36个特征的样本效率不如98个特征给模型更多可利用的（可能与ADHD无关的）方差；（b）TIV、全脑体积等"混杂"信息在98列里被模型隐式利用，本身与站点/头动等协变量相关，而非真正的解剖信号；（c）体积这种粗粒度指标可能不是这些假说区域真正携带信号的度量方式（例如假说更多来自功能激活/连接证据，而不是灰质体积）。本实验设计无法区分这几种解释。
3. **这与本仓库贯穿全部结果的既有结论方向一致**：无论是最早的 ROI-guided CNN（Harvard-Oxford，严格LOSO下 pooled OOF AUC 仅0.470，低于年龄+性别基线0.619），还是这次的 SynthSeg 生物学子集，"用文献假说去缩小特征范围"这个操作在本项目历次尝试中都没有带来更好的表现——这本身是一个值得在论文里明确指出的、一致的负结果模式，但每次的具体机制不完全相同，不能简单归并成一句话。

### 产出物

- `reproduction/exploratory/structural_biological_subset_cv.py` — 新脚本，非冻结代码
- `results/structural_biological_subset_cv_20260918/{summary,repeat_metrics,fold_metrics}.csv`、`bio_subset_columns.json`、`status.json`

## 参考文献索引

根据 PubMed 检索结果：

1. Bush G, Valera EM, Seidman LJ. Functional neuroimaging of attention-deficit/hyperactivity disorder: a review and suggested future directions. *Biol Psychiatry*. 2005;57(11):1273-84. [DOI](https://doi.org/10.1016/j.biopsych.2005.01.034)
2. Dickstein SG, Bannon K, Castellanos FX, Milham MP. The neural correlates of attention deficit hyperactivity disorder: an ALE meta-analysis. *J Child Psychol Psychiatry*. 2006;47(10):1051-62. [DOI](https://doi.org/10.1111/j.1469-7610.2006.01671.x)
3. Ellison-Wright I, Ellison-Wright Z, Bullmore E. Structural brain change in Attention Deficit Hyperactivity Disorder identified by meta-analysis. *BMC Psychiatry*. 2008;8:51. [DOI](https://doi.org/10.1186/1471-244X-8-51)
4. Durston S, van Belle J, de Zeeuw P. Differentiating frontostriatal and fronto-cerebellar circuits in attention-deficit/hyperactivity disorder. *Biol Psychiatry*. 2010;69(12):1178-84. [DOI](https://doi.org/10.1016/j.biopsych.2010.07.037)
5. Castellanos FX, Proal E. Large-scale brain systems in ADHD: beyond the prefrontal-striatal model. *Trends Cogn Sci*. 2012;16(1):17-26. [DOI](https://doi.org/10.1016/j.tics.2011.11.007)
6. Mizuno Y, Yamashita M, Shou Q, Hamatani S, Cai W. A brief review of MRI studies in patients with attention-deficit/hyperactivity disorder and future perspectives. *Brain Dev*. 2025;47(2):104340. [DOI](https://doi.org/10.1016/j.braindev.2025.104340)
