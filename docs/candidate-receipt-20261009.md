# candidate-v1 标注接收（2026-10-09）

C 提交 4462ff7（origin/c2-action-verification）已合入 main；保留原 CSV、交接说明和建议/审查过程表，不改写 C 的原始意见。单表实际检查：24 行、ID 唯一且完整，路径/样本 SHA 对应固定 packet，必填字段完整，代码/文档行号均在原文件范围。11 CONSISTENT、8 INCONSISTENT、5 INSUFFICIENT；后者为 candidate-07/12/16/19/23。

包 SHA-256 为 9967f0890c08ec4dd3e4f41e415c9e4ad58b5f8b3c4d2941cb145643273d6055，与 B/C 交接一致。C 工作区 CSV 的 CRLF 哈希为 5082ad65c1378116cd9ee5be0e0a8ea25929ad3be0de4cf0c0758dbdbdf8c882，与 C 报告一致；Git blob 使用 LF，哈希为 4bcceb9aa571137fccad918d31176085539ad9cd23dcef1c7898a0160045ba97。逐字节归一化验证差异来自换行；跨平台核对需明确计算对象，不误报为标签内容改变。

B 的用户转交说明报告本地提交 3f74450，计划分支 member-b-candidate-v1，表哈希 02df0604d36805fb105744ae25c9946106f76ad1d6c9740c6743e1f59417c67e。本次 fetch 后远程分支未出现，且本地无该提交对象，因此不能合并或验证 B 表，不能仅靠汇总推断逐条一致。B 的 AI 辅助及旧种子接触披露保留，不能自动标作盲态人工金标准。

C 的标注已在固定提交中保存，B 可以推送自己的分支供 A 获取。当前未向 B 发送任何工具消息；由用户转达即可。B 原表到位后：核对实际表哈希和接触披露，执行 bench.annotation_packet check，再逐条裁决标签/目标/坐标，并审查模板独立性。五项环境依赖的最终口径仍需按固定证据裁决，不凭默认环境假设提前改标签。

本次只接收和合并标注文档，不变更检测代码、不调用模型。双表结构检查、最终裁决和正式测试冻结仍未完成。

## 同轮补充：B 交接附件已到本地

随后本地根目录出现 individual-B-20261009.csv 和 b-candidate-v1-handoff-to-a.md。按用户提供的交接附件接收，原文件保留；副本归档 docs/audit-samples/b-20261009，表的原始 SHA-256 与 B 提供值完全一致。未获得 3f74450 Git 对象，不能称为已合并 B 原分支；后续 B 推送仍可补入原提交历史。

双表结构检查已实际通过：structurally_complete=true、errors=[]，24/24 label 一致。工具仍列出全部 24 条待裁决，因为目标实体写法或证据坐标等字段不同；不能将标签一致等同于全部字段一致。结果见 audit-samples/candidate-pair-check-20261009.json。最终逐项语义裁决、统一定位和独立性审查尚未完成，formal_test_ready=false。
