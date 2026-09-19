# DocCodeBench 与实验运行器

本轮提供 20 个自建开发种子的重建脚本、固定提交清单、指标计算和统一方法运行器。标签由开发阶段给出并标记 **provisional**，需要两人独立标注和裁决；这些不是已发现的真实开源案例，也不是正式测试成绩。

```powershell
.\.venv\Scripts\python.exe bench/builders/build_seed.py --out runs/my-seed
.\.venv\Scripts\docsync.exe benchmark --manifest runs/my-seed/manifest.jsonl --method rules --out runs/my-benchmark
```

构建器固定提交作者、时间、内容，生成 `manifest.jsonl` 和 SHA-256；仓库不需要联网重建，所有样本目前都属于 dev。重复执行选用新输出目录，避免覆盖既有实验。

清单 Schema 在 `bench/schema/sample.schema.json`。每个样本包含 repo_id/group_id、固定 head_sha、目标文档与代码路径、可选 claim_line、来源、标签、类型、split、权利和标注状态。仓库必须位于 manifest 所在目录内部；runner 不执行目标代码。相同 repo_id 或 group_id 跨 dev/test 会直接拒绝运行，重复 sample_id 也拒绝。正式数据应增加真实来源、独立标注与按组冻结的测试集。

| method | 实际行为 | 预测来源 |
| --- | --- | --- |
| keyword | B1 全局参数名/字面文本匹配；无 AST、类型比较或实体归属 | 原始词法比较，无证据验证 |
| rules | 静态提取、确定性对齐、规则判断、独立验证 | 已验证 Finding |
| full | hybrid 规则与 AI 复核、完整独立验证 | 已验证 Finding |
| llm | 固定声明/候选范围的原始文档与代码交给模型，不提供解析后的默认值/参数 | 未验证模型判断，明确标为 unverified_judge |
| no_alignment | 用属性名候选替代符号/链接归属，保留后续判断与验证 | 已验证 Finding |
| no_verifier | 与 Full 同样的判断链，指标在验证前取数 | 未验证 Judge；正常报告仍只发布已验证告警 |
| no_static | 保留同样候选 ID/范围，将原始代码交给模型，不提供结构事实，后续仍验证 | 已验证 Finding |

除 keyword 直接匹配原文外，其余方法共享当前支持的声明提取范围；llm 基线并非对整个仓库无边界全文提示。no_static 保留候选 ID 用于受控对比，去掉的是判断阶段的结构事实，不宣称已去掉所有静态索引。报告这两个实验边界，不把不同范围方法的效果混称为公平全文比较。keyword 不支持签名/复杂表格时返回 SKIPPED，相关正例计漏检。

模型配置和调用预算见 [model-provider.md](model-provider.md)。除 rules/keyword 外的方法请求模型但配置缺失时会记录 PARTIAL；llm/no_static 不产生模拟成功。此时输出用于验证失败/拒答记录，不能标为该方法真实实验完成。

输出包括逐样本报告、`predictions.jsonl` 和 `metrics.json`，记录 manifest/config 哈希、方法、来源、标注状态、实际 usage、耗时、错误及分类型指标。基准运行自动禁用用户忽略规则；缺失提交、解析失败、无候选等不删除样本。

正例拒答/跳过/失败计 FN；负例拒答不算 FP，但降低决策覆盖率。INSUFFICIENT 单列不当确认率。零分母为 JSON null。可单独重算：

```bash
python bench/evaluate.py --input runs/my-benchmark/predictions.jsonl --out runs/recomputed-metrics.json
```

尚待团队完成：人工标注、合法真实案例、测试集冻结、真实模型主实验与重复运行、组 bootstrap、人工证据/补丁正确率、成本金额、真实社区反馈。当前受控案例指标不用于声称达到策划案中正式 Precision/Recall 目标。
