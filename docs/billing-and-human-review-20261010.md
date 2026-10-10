# 账单核对与 A 人工复核（2026-10-10）

本轮成员A已提交指南五项的复核反馈，接收日期为 2026-10-10；实际审核日期原回复留空，未代填。完成范围如下：

| 项目 | 已记录范围 | 证据 |
| --- | --- | --- |
| 1 核心流程 | 本人演示，冲突 1→0，仅文档默认说明修改 | [流程](audit-samples/billing-review-20261010/core-flow-review/review.json) |
| 2 关键代码 | CLI；模型密钥/预算/响应/重试/未知用量；补丁路径、原文和 manifest 检查 | [CLI](audit-samples/billing-review-20261010/cli-review.json)、[模型](audit-samples/billing-review-20261010/provider-review.json)、[补丁](audit-samples/billing-review-20261010/patch-review.json) |
| 3 报告 | 结论与披露口径；rules 的 03/01/05 三条预测抽查 | [报告](audit-samples/billing-review-20261010/report-review.json) |
| 4 标注 | 05/06/07/13/19 五条；B/C 原表保留；标签一致不等于独立盲测 | [标注](audit-samples/billing-review-20261010/annotation-review.json) |
| 5 发布相关 | 授权范围、0.0824961 CNY 汇总账单及逐请求证据限制、未完成发布条件 | [许可/账单/发布](audit-samples/billing-review-20261010/license-billing-release-review.json) |

边界：补丁并发保护的“写入前检查、无写后检查或全程锁”是助手纠正，未代填用户确认。三条预测和五条标注不扩大为全量审核；11 条历史 AI 台账尚未统一签署，保留各记录实际覆盖范围。当前已有真实模型开发实验，待办是新独立正式测试集及其冻结后实验、其他人工复核缺项、最终材料和发布 SHA/CI/tag 一致性。

账单核对详见 [实际核对](provider-bill-reconciliation-20261010.md)。

## 一、账单核对

| 批次（2026-10-07） | 请求 / 成功 | 已知输入 | 已知输出 | 未知用量请求 |
| --- | --- | --- | --- | --- |
| 首次超时，目录提示 15:05:19 | 1 / 0 | 未知 | 未知 | 1 |
| 单例重试，目录提示 15:13:26 | 1 / 1 | 1032 | 133 | 0 |
| 五例，目录提示 15:17:34 | 4 / 4 | 4088 | 684 | 0 |
| 七方法，目录提示 22:20:34 | 85 / 85 | 71186 | 13115 | 0 |
| 合计 | 91 / 90 | 76306 | 13932 | 1 |

从各原始 manifest 的 model_calls 重新求和，与扫描 usage 和此前台账一致。零调用样本保留但不当作请求；没有将重复输入 hash 合并为同一次请求。已知 Token 合计 90238。超时记录用 null 表示未知，不算实际零用量。

[逐调用明细](audit-samples/billing-review-20261010/calls.jsonl)、[核对摘要](audit-samples/billing-review-20261010/summary.json)、[原始文件哈希](audit-samples/billing-review-20261010/source-hashes.json)已保存。目录中的时间只是用户 PowerShell 生成目录名的提示，不是精确请求时间；时间范围不能只取到 22:20:34，晚间批次在此后仍继续运行。服务端 request ID 也未记录，不能保证逐单精确匹配。

账单凭证及全部请求属于 DocSync 的确认已经收到，无需再次提供。原始私人导出不入库，汇总核对证据已归档。

本地 cache_hits=0 只说明未复用本地响应，不说明供应商 prompt cache 没有命中。当前适配器没有归档服务端缓存拆分，不能按某个单价直接把总输入换算为核对金额；平台缓存分类、折扣和超时计费应以实际账单为准。账户充值额或剩余余额也不自动等于本项目费用。

收到凭证后按以下次序关闭：确认时间与模型范围 → 排除其他请求 → 核对用量/缓存分类 → 核对金额及币种 → 记录差异和真实审核人/日期。若只有账户汇总，结果写“汇总范围核对，无法逐请求归属”，不能写“91 次全部逐笔一致”。

## 二、A 本人人工复核入口

历史 CSV 的 11 条原文保留；当前进度在 [历史补审映射](audit-samples/billing-review-20261010/historical-review-map.json)中为 11 条均已有指定范围复核记录（不等于全量签署）。具体缺口见 [H1—H6](a-historical-review-guide.md)。[待审索引](audit-samples/billing-review-20261010/human-review-pending.json)固定了当前台账哈希和行号（含表头，第一条为第 2 行）。下面是具体审查范围，不是预填的通过意见。

| 台账行 / 阶段 | 打开什么 | 本人需要核对的内容 |
| --- | --- | --- |
| 2 framework | [README](../README.md)、[CLI](../src/docsync/cli.py) | 安装和入口是否与实际使用一致；scan/patch/apply 的职责是否明确 |
| 3 core extensions | [provider](../src/docsync/llm/provider.py)、[限制说明](limitations.md) | 模型输入/校验与失败行为；是否把不支持范围误写为已实现 |
| 4 release verification | [验收记录](verification.md)、[发布清单](release-checklist.md) | 历史验证的版本和日期，跳过项是否如实保留 |
| 5 member A contract review | [契约审查](a-contract-review.md) | 退出码、报告兼容、补丁显式应用等契约是否认可 |
| 6 A acceptance and license | [授权范围](license-scope.md)、[LICENSE](../LICENSE) | 已确认的原创材料授权范围，外部竞赛资料不随意纳入 |
| 7 A development adjudication | [seed-dev-v1](../bench/frozen/seed-dev-v1/README.md) | 20 例仍为 dev；证据和候选 Recall@K 分母是否准确 |
| 8 live smoke verification | [五例实测](deepseek-smoke5-20261007.md) | 实际运行是否与保存记录一致，拒答解释局限是否接受 |
| 9 A experiment readiness | [七方法实测](deepseek-suite-20261007.md)、[运行器](../bench/run_suite.py) | 85 次请求、失败保留、预算和“不能证明 AI 优于规则”的结论 |
| 10 A annotation handoff tooling | [统一接收包](../bench/annotations/candidate-v1-received-20261009/README.md) | B/C 原始表未被改写，结构检查不代替人工判定 |
| 11 A controlled candidate collection | [候选来源](../bench/candidates/controlled-v1/README.md) | AI 辅助生成和既往接触披露，6 个合成组不是 6 个真实项目 |
| 12 A technical closeout | [24 条裁决](../bench/frozen/candidate-dev-v1/adjudication.md)、[收尾报告](a-closeout-20261010.md) | 统一证据范围和语义；全组 dev 决定；漏报/PARTIAL 和独立评测未完成是否如实记录 |

用户此前亲自运行并转交 API/实验结果是运行证据，不自动等于对上述全部代码和结论进行了人工审查。本轮助手重新核对用量和缓存字段缺失，也不是人工签字。217 passed/2 skipped 是此前完整回归结果，本轮不冒称重新运行测试。

请按实际情况回复审核人标识、已审行号、具体检查内容、发现问题与修改。示意格式：“审核人：成员 A；已审：第 X 行；核对内容：……；问题或修改：……；其余待审。”仅在本人确实检查后填写“未发现需修改项”；没有检查的行继续 pending。A 无法替 B/C 签其本人审核。

收到真实意见后再写入台账 human_reviewer/human_changes，并保留本次用户确认依据及日期；如果源台账已变更，先重新核对行号与阶段，不按旧索引盲填。
