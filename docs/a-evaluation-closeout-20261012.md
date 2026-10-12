# A 评测工程收尾与本人复核入口

日期：2026-10-12。本轮完成源码级实现与合成验证，未扫描 external-v1、未执行上游代码、未调用实验 API。当前为本地未提交工作区；不能用旧 main 的 CI 证明本轮修改。证据：`runs/a-readiness-20261012/verification.json`、`tests.xml`、`followup.xml`。

## 已完成

- 同仓库绝对路径/提交/有效配置复用 ScanReport。首次结果记录实际 usage，复用行 usage 为空，同时提供 report_run_id/report_reused；逐样本报告内保留原始扫描用量，汇总应使用 predictions 的归属用量，不逐份 report 相加。返回 FAILED/PARTIAL 报告也复用；抛异常未生成报告的情况不缓存，可能重试，因此预算仍保留按样本的保守上界。
- 原有完全重复坐标检查之外，按实际仓库路径、提交、文档、主体/属性拒绝重叠声明区间，不让换 repo_id 或别名绕过范围归属检查。该策略偏保守；不是任意不同主张之间语义等价的自动证明。
- claim_scope.required_provenance 可指定精确 SourceSpan（含路径、行、字节、哈希）；全部必须属于事实原始跨度或 provenance 链。导出事实记录跨文件链；verifier 校验哈希和坐标并重新提取比较，报告读取校验来源哈希及 finding 与 fact 链一致。空列表兼容旧报告，不捏造旧来源。
- 新增 explicit_consistency_rate、complete_run_rate、按 group 指标与 unique_scan_count。原 TN 口径保留以便历史解释；拒答不进入明确一致分子。全部 gold 为一致时 recall 仍为 null。
- report/benchmark 两份 JSON Schema 已同步。Schema 2.0 可选扩展沿用当前策略：新程序读旧报告，不保证旧程序读新字段；旧报告缺来源链时补空列表，不重算标签或补丁。

## 验证

相关专项 61 passed。随后全套初跑 226 passed、2 failed、2 skipped：失败为新增指标测试缺导入，以及旧报告比较未将新增空来源链默认值纳入预期。已修复并复验相关 18 项通过；额外 scope/metrics 8 项通过。Ruff 全部通过，mypy 21 个源码文件通过。未声称修复后再次全套执行。两个 skip 是 Windows 符号链接权限限制。

## A 本人接下来怎么审

1. `src/docsync/benchmark.py`：看首次/复用的 usage 和 report_reused，解释为什么同组多个声明不能把请求数重复相加；看重叠范围何时拒绝。
2. `src/docsync/benchmark_scope.py`：看完整声明范围、主体/属性、实体映射和 required_provenance；解释证据缺失为何拒答、gold 为什么没有传进 scan。
3. `src/docsync/verification/__init__.py` 与 `src/docsync/models.py`：看来源链哈希/偏移、重新提取校验及报告引用校验；区分读取旧报告补默认字段与重新验证历史判断。
4. `src/docsync/metrics.py`：解释 TN 中含拒答但明确一致率不含；无冲突正例为什么不能报告冲突召回。

2026-10-12 四项源码阅读已完成，见 [评测新代码复核](a-evaluation-code-review-20261012.md)。审查人为 Codex（A 委托，披露身份）；结论为与结项口径一致并附使用说明。此前 24 条标签确认仍不覆盖新代码。原助手记录不作为本人签署；随后成员A明确反馈已阅读四项并确认无异议，2026-10-12 已归档本人补充确认，实际阅读日期未另行提供。

## 仍不能自动关闭的条件

B 既往接触继续 unknown；正式 test=0；10 未决。完整正式效果需要补充预登记来源及独立标注，不得用全一致集证明冲突检出能力。生成接口的任意跨段语义不因新增 provenance 就自动受到提取器支持；无法提取的声明如实拒答。

最终扫描/预算冻结须绑定最终 manifest、代码 SHA 与配置，当前还没有可宣称最终的实验 manifest。付费实验、账单、最终材料、C 的匿名化/链接/版本复查及对应 SHA CI/tag 依赖这些条件。关键词 baseline 对 claim_scope 仍 SKIPPED，不用 gold 提供的源码信息把基线升级成答案驱动的方法。
