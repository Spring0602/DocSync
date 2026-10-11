# B 扩展覆盖收尾证据（2026-10-10）

本目录保存成员 B 扩展样本覆盖修复后的离线结果。数据仍为 `candidate-dev-v1` 开发集，不是独立正式测试集；本轮只运行 rules，模型 API 请求为 0。

## 固定输入与文件哈希

以下哈希统一按 Git 仓库存储的 LF 字节计算，不使用可能被本地 checkout 转换为 CRLF 的工作区副本。

- manifest SHA-256：`c8fcf3cfb3cdfb38b89266b2d7926038e774fa68293f5f3edbd8939fa8a51aae`
- 修复前指标：`../a-closeout-20261010/rules/metrics.json`
- 修复前指标文件 SHA-256：`9e8880df194747f172112b0e391fb3851fd550a550d26fb4fb273555e89f5c9a`
- 修复后指标：[after-metrics.json](after-metrics.json)
- 修复后指标文件 SHA-256：`89686d460b6b870fb899de01499e04d518e19bfac836c129b4281905f0ef7949`
- 修复后逐样本预测：[after-predictions.jsonl](after-predictions.jsonl)
- 修复后预测文件 SHA-256：`6c424d160b07d56d866acb5d19e3c99a3216641cdb7e46a4730ac5e3370775d5`
- 代码提交：`0ccbecb49e87b098abadce705f7e5168e9f74c01`

## 人工复核口径

`compliance/ai_assistance_log.csv` 中本轮记录最初以 `pending` 写入，表示写入当时尚未收到成员 B 的本人意见。成员 B 后续已于 2026-10-10 完成五项复核；当前 CSV 的本人复核字段、[机器可读复核记录](human-review.json)和 [AI 复核索引](../../../compliance/ai_review_index.md)共同记录该后续状态。

## 前后结果

| 指标 | 修复前 | 修复后 |
| --- | ---: | ---: |
| TP / FP / TN / FN | 3 / 0 / 11 / 5 | 8 / 0 / 11 / 0 |
| 可判定样本明确决策覆盖 | 6 / 19 | 18 / 19 |
| 全部样本拒答 | 18 / 24 | 6 / 24 |
| INSUFFICIENT 不当确认 | 0 / 5 | 0 / 5 |
| API 请求 | 0 | 0 |

唯一仍拒答的可判定条目是 `candidate-06`。它在定义后直接写入函数对象的 `__defaults__`；本轮不把任意函数属性变更简化为普通静态默认值。`candidate-07/12/16/19/23` 继续因环境或运行时输入未知而拒答。

`candidate-05—08` 的四个报告仍为 `PARTIAL`，但四份报告中的完整性诊断都只来自同组仓库的 `case06.py:DYNAMIC_FUNCTION`。这表示一次仓库级扫描发现同一项动态接口，不表示 05、07、08 分别发生了运行时失败。

