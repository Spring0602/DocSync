# DeepSeek 5 例试运行验收（2026-10-07）

运行目录：runs/deepseek-smoke5-20261007-151734。方法 full，模型 deepseek-flash，非思考模式；由用户在持有密钥的终端执行。原准备计划保留 PREPARED_NOT_RUN 作为历史记录，实际完成状态见 result-summary.json。

| 样本 | 标注 | 结果 | 实际模型请求 |
| --- | --- | --- | --- |
| seed-01 默认值冲突 | INCONSISTENT | INCONSISTENT，已验证 | 1 |
| seed-02 默认值一致 | CONSISTENT | CONSISTENT，规则直接处理 | 0 |
| seed-04 动态工厂值 | INSUFFICIENT | UNCERTAIN，未发布冲突 | 1 |
| seed-10 配置冲突 | INCONSISTENT | INCONSISTENT，已验证 | 1 |
| seed-14 缺必选参数 | INCONSISTENT | INCONSISTENT，已验证 | 1 |

5 个样本均 COMPLETED；4 次真实调用全部 SUCCEEDED，无缓存、无重试、无未知用量。输入 4088、输出 684，合计 4772 Token。各样本耗时合计约 26.43 秒。TP=3、FP=0、TN=1、FN=0，证据不足样本 1 例正确拒答，不当确认 0。摘要计数与逐样本模型调用 usage 对账，分类指标已从原预测重新计算核对。

**验收结论：A-N1 的 3—5 例小样本试运行技术部分通过。** 一致样本未请求模型，所以不能声称模型亲自判对全部 5 例；也不能用这几个已参与开发的种子证明正式准确率、泛化效果或 AI 优于规则。后续七方法开发实验已完成，见 deepseek-suite-20261007.md；独立正式测试集及其实验仍未完成。

## 解释质量与后续限制

动态值样本的拒答结论正确，理由中的“没有确定值”有依据；但模型同时将 client.connect 与 connect 的限定名差异当成实体不匹配，这一附带解释不成立。保留原响应，不润色成完美判断；后续 A 应在更丰富的别名/归属样本上单独审查解释质量。

两条冲突响应 score 偏低，但系统按证据与独立 Verifier 发布 Finding，不将模型分数解释为校准概率，也不以此覆盖真实标签。

2026-10-10 已完成供应商日汇总账单核对，见 provider-bill-reconciliation-20261010.md；本批不单独拆分金额，不从日汇总推断逐请求费用。此前约 125 秒失败请求保持 unknown_usage_requests=1；本轮成功不能抹去该失败。

代码基于 ac8081d 的本地未提交适配器修改，配置和关键代码 hash 已归档；正式大批量实验前应固定提交和配置。原始样本库版本为 seed-dev-v1，仍为 dev。

证据：[运行汇总](audit-samples/deepseek-smoke5-20261007/result-summary.json)、[指标](audit-samples/deepseek-smoke5-20261007/metrics.json)、[逐样本预测](audit-samples/deepseek-smoke5-20261007/predictions.jsonl)。同目录保存各样本完整报告与调用 manifest，不含密钥。
