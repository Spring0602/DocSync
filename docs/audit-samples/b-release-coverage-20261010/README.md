# B 扩展覆盖收尾证据（2026-10-10）

本目录保存成员 B 扩展样本覆盖修复后的离线结果。数据仍为 `candidate-dev-v1` 开发集，不是独立正式测试集；本轮只运行 rules，模型 API 请求为 0。

## 固定输入与文件哈希

- manifest SHA-256：`c8fcf3cfb3cdfb38b89266b2d7926038e774fa68293f5f3edbd8939fa8a51aae`
- 修复前指标：`../a-closeout-20261010/rules/metrics.json`
- 修复前指标文件 SHA-256：`9e8880df194747f172112b0e391fb3851fd550a550d26fb4fb273555e89f5c9a`
- 修复后指标：[after-metrics.json](after-metrics.json)
- 修复后指标文件 SHA-256：`6c59ea53103f6cd72339e16c336d1e2ee14c79bdfee69d013f9c787e8f1eee8`
- 修复后逐样本预测：[after-predictions.jsonl](after-predictions.jsonl)
- 修复后预测文件 SHA-256：`7f585f085e8b9eae560e376ee7ffc0d830a58645dcc36cd5053e1b717e0f4deb`
- 代码提交：`7a16354f0ff1ad4c6ed544cd19a926c867848897`

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

