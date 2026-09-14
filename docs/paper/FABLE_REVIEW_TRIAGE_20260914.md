# Fable 5.1 review and integrator adjudication — 2026-09-14

**Completed: bounded AI static review plus targeted read-only follow-up. Human scientific review remains open.**

The user explicitly authorized 18 source/test/protocol files for their existing Claude Code account. Observed model: `claude-fable-5-1`; no tool calls; CLI exit 0. Chinese stdout was damaged by PowerShell encoding; the report was recovered from the exact session's UTF-8 transcript, not regenerated. Session: `27f25032-132f-4909-bca9-49e7450405cf`. Original reviewer wording is preserved in [raw review](FABLE_REVIEW_RAW_20260914.md). Interpret it through this table.

| Finding | Disposition | Evidence and action |
|---|---|---|
| F1 | 已核实，报告层闭环 | 门禁允许容差，不强制零。此次另查 132 组记录最大差均为 0；零差异是本次观测值。未来可加显式零差异汇总，不需要改冻结运行。 |
| F2 | 历史风险，有运行证据缓解 | 首次日志含 COVARIANCE 0、50…350 /378，结合最终 378 人数组及哈希支持首次计算；后续续跑可复用缓存。日志与哈希不是独立计算实现证明。 |
| F3 | 历史缺陷，已有缓解 | 历史驱动先写报告后汇总。当前 finalize_report 和最终框架/status 检查阻止只凭旧报告放行。 |
| F4 | 历史缺陷，已有缓解 | 旧恢复逻辑弱；最终门禁校验作业身份，当前 verify_unit 另有恢复身份检查。 |
| F5 | 接受为未来门禁加固 | 校验后重新发布清单存在检查与发布间的并发变更窗口。不是“所有检查必然无效”：此前已独立对比预测等。未发现本次发生变更；未来应分离采纳与只读验证并前后比较快照。 |
| F6 | 当前证据已补查 | 66 个单元的 C_search selected model/C 精确一致。门禁仍未内置该检查；未来纳入。 |
| F7 | 共享方法风险，当前部分闭环 | 独立读取 66 单元角色无交集，2244 个角色/模型块与审计名单顺序一致；15 个 CV repeat 的每人恰一次测试和队列覆盖通过。未来独立断言还应覆盖每角色类别数与完整 LOSO 站点规则。 |
| F8 | 代码脆弱性，当前错配未发生 | 冻结 bootstrap 依赖行序配对。此次核对 357 个 LOSO 站点/模型块受试者顺序一致，故本次未发现该错配；按 ID 配对的审计函数另有测试。未来冻结版本替代程序应直接按 ID 连接。 |
| F9 | 接受，补明确披露 | 选择 C/alpha/早停后并未在六站全体上重拟合；只在约 85% 内训练样本上拟合。原 D1 的“then predict”隐含了此点但不充分明确；见方法补充说明。 |
| F10 | 未确认为缺陷，已核实依赖清单 | 18 文件之外的 legacy_manifest 实际包含 468 项（450 vendor 项），本次全部哈希验证通过，preflight 会校验。Fable 未看到清单不能推出缺失。 |
| F11 | 未来运行效率与诊断加固 | 任务失败后 executor 等待其他已提交工作，可能延迟终止；建议记录失败 job 并取消尚未开始的任务。未影响本次完成证据。 |
| F12 | 低风险状态命名问题 | 部分 --limit 也可 complete_matched，但终检还检查 all_units_completed 与 units=66。本次不是部分运行。未来用 partial 命名。 |
| F13 | 未来输入契约加固 | 复现入口可补 98 特征及有限性显式检查；当前输入受冻结哈希约束，不能据此推定本次形状错误。 |

## Follow-up evidence

`../../results/paper_readiness_20260911/review_followup_checks_20260914.json` contains aggregate-only results. `../../results/paper_readiness_20260911/local_source_tests_20260914.txt` records exact local-source hashes and 19 passing synthetic tests (3.95 s) executed in an isolated server temporary directory. No training or terminal verifier was rerun; frozen model code and results were not modified.

The reviewer’s “VERIFIED” train-only statement is too broad for helpers it explicitly did not receive. Treat it as evidence about visible call sites, not a complete transitive leakage audit. Different package versions are not required for a clean independent execution environment; same versions do not invalidate refitting. Conversely, environment recreation does not establish independently implemented methods.

This review does not justify “no leakage”, “clinically useful”, or “raw MRI reproducible”. No new model experiment was undertaken. YELLOW — understanding not yet assessed: explain observed zero difference versus a tolerance gate, shared-code reproduction, and the sample-size implications of omitted refitting.
