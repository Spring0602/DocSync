# A 新候选采集及 B/C 交接（2026-10-07）

完成 A-N2 的候选准备部分：24 条 AI 辅助原创受控候选，6 个合成仓库，0 个真实外部仓库；代码、文档、来源说明、许可依据、接触情况和 Git SHA 均已保存。无 gold、预测或伪造人工字段。**人工双标与独立性审查尚未完成，不能称为正式 test。**

入库材料：[候选来源与风险](../bench/candidates/controlled-v1/README.md)、[B/C 标注操作](../bench/annotations/candidate-v1/README.md)、[带行号原文](../bench/annotations/candidate-v1/context.md)、[版本哈希](../bench/candidates/controlled-v1/freeze.json)。

本地已生成 runs/candidate-v1-handoff-20261007/candidate-v1-B.zip 和 candidate-v1-C.zip。每包仅含对应成员的空白表、相同原文/packet、说明和许可；已检查 ZIP 完整性、表格隔离和 packet hash 一致。压缩包是便于分发的本地产物，不入 Git；入库目录可用于重新分发。

验证：24 个代码文件仅做 ast.parse，不执行；全部内容哈希核对；两次重建后再做最终冻结校验，intake 字节与 6 个 Git SHA 一致。与原开发集代码/文档无完全相同 blob，但字节差异不能证明模板独立。B/C 表各 24 行，身份、时间、标签、证据等人工字段保持空白；结构检查按预期拒绝。相关测试 5 passed（2.32 秒），Ruff 通过。没有运行任何候选扫描或模型请求。

接下来 B/C 各自填写自己的表并独立交 A，另附 packet hash 与既往接触情况。A 检查结构后，审查每个家族与旧种子的派生关系，逐条裁决；与旧数据同族的组保留为 dev，不通过改组名伪装独立。通过审核的实际数量决定最终测试集，不追求填满预设标签配额。账单和 AI 日志人工复核仍分别待负责人提供真实记录。
