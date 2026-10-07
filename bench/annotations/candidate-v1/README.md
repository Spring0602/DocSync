# B/C 新候选样本标注任务

本包含 24 条未标注受控候选。代码/文档已固定 Git SHA，来源与接触情况见 packet.json；内容索引为 [context.md](context.md)。这里没有 gold 或预测；未运行规则或模型。6 个技术家族不是 6 个外部真实来源，独立性仍待复核。

## B 现在做什么

1. 复制 individual-B.csv 到自己的工作目录，保留原始空白表；阅读全部 context.md（有原文行号）。也可逐个打开 candidate-XX/code_path.txt、document_path.txt。
2. 仅根据固定原文独立填写 reviewer、reviewed_at、label、drift_type、行范围、target_entity、evidence、reason；label 限定 CONSISTENT / INCONSISTENT / INSUFFICIENT。行范围采用 3 或 3-7，不填写模型建议，不先看 C 的表。
3. 如果声明含歧义、依赖运行时环境或证据超出两文件，记录实际缺失，不猜标签；有候选不足或熟悉旧模板的问题写 questions。
4. 独立提交填好的表给 A，附本包 packet.json 的 SHA-256，并说明此前是否见过这些材料/他人标签。不要把填好表传给 C。

## C 现在做什么

按相同步骤独立填写 individual-C.csv；不参考 B 的判断。另向 A 报告来源/模板家族独立性疑问，以及文件缺失和行号问题；不为了达到 24 例或类别配额改变标签。最终匿名化检查仍待发布材料定稿，不与此次标注混为一项。

## A 收表后做什么

核对包 hash 和样本身份；运行结构检查，再逐条裁决。独立性审查见 bench/candidates/controlled-v1/README.md，重点关注与旧动态默认值、签名、配置模板的关系。全部一致也不自动成为 test，不能代签 B/C 或人工审核日志。

```powershell
.\.venv\Scripts\python.exe -m bench.annotation_packet check --packet bench/annotations/candidate-v1/packet.json --b runs/annotations-B.csv --c runs/annotations-C.csv
```

空白原表的检查应失败，这是尚未人工填写的正确状态。保留 packet.json 和原表；各自的完成表另存，不修改已固定原文。完整来源、LICENSE 和已知接触情况随包交付；同组及其派生材料不得跨 dev/test。未完成标签与独立性审核前，不运行模型或规则评测。
