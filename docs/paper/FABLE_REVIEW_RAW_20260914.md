# Fable 5.1 static review — unadjudicated reviewer output

Recovered from the exact Claude Code session UTF-8 transcript. This text is reviewer opinion, not integrator-confirmed findings; see FABLE_REVIEW_TRIAGE_20260914.md. Model: claude-fable-5-1; tools disabled; 18 approved files.

我将直接基于所给源码进行静态审查，不使用工具，按要求以中文输出。

## 审查范围

对象：`reproduction/reproduce_v2.py`（当前驱动）、`execution_history/reproduce_v2_launched_20260911.py`（9/11 实际执行驱动）、`verify_fresh.py`（终检门禁）、`integrity.py`、`completion.py`、`finish_execution.py`、`regenerate_tables.py`、legacy 训练与统计脚本、测试与协议文档。未提供的 `controls`、`demographic`、`transform`、`select_features`、`choose_alpha`、`conditional_auc`、`figures_v2`、`statistics_audit` 均未审。

## 已核实事实（VERIFIED）

- 单元覆盖：`jobs()` 生成 2 框架 × 3 队列 × (15 或 7) = 66；`run_fold` 断言 17 模型（legacy:228）；`verify_fresh.py:74` 检查 17；`summarize_*` 断言行数 = 人数 × 17。
- 角色划分：`run_fold:188-189` 断言 tr/va/te 无交集且覆盖全体；`reproduce_v2.py:56-57` 与 `verify_fresh.py:69-70` 对照原始 `audit.json`。CV 的 fold_id/seed_off 与 legacy `main:346` 一致，LOSO 与 `main:356-357` 一致。
- 仅训练拟合：几何均值、白化、ANOVA 选特征、两处 StandardScaler 均只用 `tr`（legacy:195-206）；C、早停、alpha 均只用验证集（locked:118-121、functional:91-99、locked:144）。测试集未参与任何选择。
- 输入谱系：协议 `input_hashes` 覆盖 QC、体积、父队列/划分、时间序列 `verification.json`；当前驱动 `:89-91` 再校验 timeseries 哈希；协方差重算后与原始比较 1e-12 并要求字节相同（`:122-123`、`verify_fresh:49`）。原始运行的 `covariances.npy` 实际是从 20260909 轮复制的（legacy `prepare:108-112`），因此复现的从头重算确有增量价值。
- 预测比较：`compare_predictions` 按 (subject_id, model) 对齐，校验 site/y 一致、有限性，判定阈值 rtol 1e-5 / atol 1e-6，同时记录最大绝对差。
- 终检：`verify_fresh` 要求 status 为 complete_matched 且 66 单元，重算全部比较、alpha 精确相等、summary 等 15 个表 1e-10 一致，`regenerate_tables` 重算 5 个统计表并要求 `decision.json` 完全相等。

## 发现（含严重度、位置、触发、影响、最小修复）

**F1 [中] "零预测差异"未被代码强制**。`integrity.py:28`、`reproduce_v2.py:135`、`verify_fresh.py:76` 只判容差；最大差仅记录。触发：任何 ≤ 容差的漂移仍判 matched。影响：报告中的"零差异"只能从 `unit_comparisons` 内 132 条 `max_abs_score_difference` 逐条推断，非门禁保证。修复：`validate_units` 增加全局最大差汇总并在 final 中显式输出；若声称为零则断言 `==0`。

**F2 [中，历史缺陷] 协方差"重算"不可由产物证明**。launched `:117` 将 `recomputed_from_timeseries=True` 硬编码；`covariance_cache`（legacy:139-143）遇 `covariances.json` 存在即复用且不读时间序列；launched 主流程本身不校验 timeseries 哈希。触发：9/11 执行若曾重启或 out 目录预置协方差文件。影响：字节相同只证明"与原始一致"，不证明"本次从时间序列算出"。终检缓解：`verify_fresh:47-49` 证明 ids、source_sha256 与字节一致；当前驱动 `:119,123` 已记录 `cache_reused_this_invocation`。修复：终检核对启动日志中 `COVARIANCE n /378` 行，或要求首轮 `covariance_comparison.json` 中 reused=False。

**F3 [中，历史缺陷，已被门禁拦截] 报告先于汇总写出**。launched `:132-134` 先写 `complete_matched` 报告与状态再 `summarize`；汇总失败时报告文件残留。缓解：except 覆写 status 为 failed；`verify_fresh:127` 读 status，`:92-93` 还要求框架 status 为 `complete_replay_checked`。当前 `completion.finalize_report` 修复并有测试。行动：在证明文档中记录该历史缺陷及拦截路径。

**F4 [低，历史缺陷] 恢复门不校验作业身份**。launched `:40-42` 仅看 `comparison.json` 存在。崩溃于 `:74-78` 之间时日志哈希不匹配会 fail-closed，但复制的单元目录可被误当作另一作业恢复。缓解：`verify_fresh:83` 校验 framework/cohort/unit；当前 `verify_unit:30-31` 修复。

**F5 [中，当前+终检] 验证器改写被验证对象**。`verify_fresh.py:84` 在校验中调用 `publish_unit` 重写 `complete.json` 并创建 `reproduction_complete.json`，随后 `verify_unit` 必然通过（自证）。`:66` 校验与 `:84` 改写之间的文件变动会被盖章。修复：仅当标记缺失时发布，且发布后与 `:66` 之前记录的哈希再次对照；或将"采纳"独立为单独步骤。

**F6 [低] LR 的 C 选择未被比较**。`reproduce_v2:69-73`、`verify_fresh:77-80` 只比较 `selection.csv` 的 alpha；`C_search.csv` 的 selected 行未核对，仅由预测容差相等间接暗示。修复：增加 `C_search.csv` selected 行精确比较。

**F7 [中，共享方法风险] 角色对齐检查是循环的**。复现与终检都以原始 `audit.json` 为基准，而它与复现来自同一 `splits.csv`；legacy `prepare:122-127` 的"每 repeat 每人恰为一次 test、每角色两类齐全"断言在复现中未重跑（`prepare` 未被调用）。修复：preflight 对 `out/*/splits.csv` 重跑该组断言。

**F8 [中，共享统计风险] 按行序配对**。`analyze_v2_stats.py:98-105` 对候选/参照只断言 y 相等，不比 subject_id，正确性依赖 `run_fold:229-236` 的写出顺序。`tests/test_statistics.py` 测的是未提供的 `statistics_audit`，不是冻结的统计脚本。5 表与决策一致不能排除此类共享逻辑错误。修复：终检用按 subject_id 配对的路径交叉重算主对比 P。

**F9 [中，共享方法/文档差异] LOSO 未按预注册"选择后在 6 站全量重拟合"**。协议 `docs/analysis_v2_protocol.md:123-124` 要求重拟合；代码在 85% 内训练集上训练并直接预测留出站（`run_fold` 无重拟合）。`deviations.md` D1 只记录内层由 3 折改为单留出，未明示省略重拟合。修复：在 D1 补记；或作为有界重跑。

**F10 [低] 传递导入未入哈希**。`run_functional_fusion:24`、`run_connectome_representations:24,26` 与 vendored nilearn 其他模块不在协议 `code_hashes`（legacy:46-48）中；是否在 `legacy_manifest.json` 内不可知。修复：legacy 清单覆盖 `legacy/` 全目录并在 preflight 校验。

**F11 [低] 失败传播**。`reproduce_v2:129-132` 首个单元异常后，`with` 退出等待其余已提交单元跑完（不取消）；failed 状态不含失败单元名。修复：`shutdown(cancel_futures=True)`，错误中写入 job。

**F12 [低] `--limit` 语义**。`reproduce_v2:126-137` 部分运行仍写 `complete_matched`（planned 硬编码 66）；仅靠 `all_units_completed/units` 区分，`verify_fresh:127` 已拦截。修复：部分运行改用 `partial` 状态。

**F13 [低] 缺少输入形状断言**。`reproduce_v2:58-60` 未复刻 legacy `main:337` 的 `vol.shape==(n,98)` 与有限性断言。

## 推断风险（INFERRED）

- 字节相同的协方差与零差异预测，暗示"新环境"与原环境在 BLAS/torch 上高度一致；"独立环境"的强度取决于 manifest 中包版本是否确实不同，本审查无法核实。
- `reference_manifest.json` 的生成时点与作者未知；若在执行后由原始运行生成，则它是快照而非独立基线。`v2_stats/decision.json` 是否在其中亦未知（`regenerate_tables:27,32` 以其为参照）。
- 当前驱动 manifest 含 `completion_sha256` 等新键，`:110` 会拒绝续跑历史执行，这是安全的，但意味着历史执行只能由历史驱动或终检完成。

## 建议行动（PROPOSED）

优先级：F1、F5、F7、F8 影响"零差异/独立验证"的可信度，建议先补；F2、F9 需在证明文档中如实限定措辞；其余为加固。

## 局限

未审未提供的六个 legacy 依赖及图表模块；未运行任何测试或脚本；无法核实 manifest 实际内容、包版本与日志。原始 MRI 预处理与外部验证不在范围内。所有"匹配"结论均建立在与原始运行共享同一冻结代码路径之上，因此只能证明可复现执行，不能证明方法学正确。