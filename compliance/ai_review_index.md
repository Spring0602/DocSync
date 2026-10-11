# AI 人工复核记录入口

原始 `ai_assistance_log.csv` 保存各开发阶段的 AI 使用声明及当时 pending 状态，不回写历史发生日期或历史提交。2026-10-10 成员A的后续反馈作为补充台账记录：

- [逐行复核映射](../docs/audit-samples/billing-review-20261010/historical-review-map.json)：11 行均有审核人、已审范围、证据和保留边界。
- [可读汇总](../docs/a-historical-review-guide.md)：H1—H6 指定范围反馈已记录。
- [原始日志快照](../docs/audit-samples/billing-review-20261010/ai_assistance_log-before-historical-review.csv)：用于核对源行及哈希。

当前状态以原始声明和补充台账共同解释，不能只凭旧 CSV 的 pending 判定无人复核，也不能把 SCOPED_REVIEW_COMPLETED 解读为全量代码或历史提交通过。24 条标签均已获成员A逐条反馈，11 一致、8 冲突、5 证据不足；[全量复核索引](../docs/audit-samples/release-readiness-20261010/candidate-human-review-complete.json)补充冻结时的 pending 状态，后续逐条反馈见 [当前裁决复核台账](../docs/audit-samples/release-readiness-20261010/remaining-adjudications.json)。成员 B 已于 2026-10-10 完成扩展覆盖提交 `0ccbecb` 的五项本人复核，见 [B 复核记录](../docs/audit-samples/b-release-coverage-20261010/human-review.json)；对应 `ai_assistance_log.csv` 行已经在收到本人反馈后补入审核人和实际修改说明。C 本人复核、独立正式评测和最终发布验收仍独立保留；各记录的范围不得相互替代。


2026-10-11：C 对 B 的 [独立复验](../docs/c-pr1-independent-recheck-20261010.md)已合入，A 合并版验证与 CI 见 [最新验收](../docs/release-acceptance-20261011.md)。该记录不自动覆盖 C 全部历史开发改动或未来最终材料审核。

2026-10-11：C 的四条自有阶段复核记录已在提交 `6134fdf` 合入，见 [原始日志](ai_assistance_log.csv)，覆盖 C 2026-09-29、10-06、10-07、10-10 所述工作范围。本轮新增的 external-v1 具体样本筛选/打包由 AI 辅助，A 尚未对本轮逐项签署；其人工复核不能由上述历史记录替代，入口见 [新来源交接](../docs/external-annotation-handoff-20261011.md)。
