# 独立标注与 A 裁决操作步骤

用途：准备 A3 的输入。现有 20 个自建种子是开发数据，provisional 标签不是人工金标准。本步骤不把机器生成内容当作 B/C 审核意见。

1. B 固定一份种子 manifest，记录原始文件 SHA-256 和每个仓库 head_sha。C 将样本来源、路径、提交及代码/文档材料整理成待标注包，隐藏现有 gold、工具预测和对方标注。开发成员已接触种子标签的事实应记录，不能声称这些数据是盲测集。
2. B、C 各复制 `individual.template.csv` 为自己的标注文件。各自读取固定提交中的文档和代码，独立填写；reviewer、reviewed_at 使用真实人员和时间，不使用 Agent 代签。
3. 每个 sample_id 填一行：label 为 INCONSISTENT、CONSISTENT 或 INSUFFICIENT；同时给出源码/文档行区间、目标实体、证据和判定理由。证据不足写明缺什么，不通过猜测补标签；真实来源另填 data_rights.csv。
4. 两份标注提交后，A 才逐条比较。复制 `adjudication.template.csv`，记录 B/C 原标签、分歧、最终标签和依据；一致项也记“双方一致，已抽查证据”，不能只保存分歧项而丢失完整覆盖。
5. A 核对 sample_id 无遗漏/重复，提交和证据位置对应，类型与标签一致。对于无法裁决的项保留 unresolved，不标 adjudicated，不纳入正式冻结集。
6. 所有项裁决后另存新版本 manifest，更新 annotation_status；按 repo_id/group_id 分 dev/test，保存划分理由、代码版本、manifest 原始字节 hash、两份标注和裁决表。禁止覆盖开发集以伪装独立测试集。
7. A 执行固定配置 benchmark。真实模型未准备时可跑 rules/keyword 验证流程，但所有数字标为开发验证；真实模型方法另开输出目录，保存完整调用证据。

目标代码位置与 target_entity 是后续 Recall@K 的人工真值输入；目前运行器没有自动读取这些列，指标实现完成前不得报告 Recall@K 数值。

模板中的 CSV 引号、逗号和换行应由 CSV 编辑器正确转义。每次交接附 manifest hash、标注文件版本和待解决问题，A 据此追溯，不只接收截图或汇总分数。
