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

## 下一步由谁推进（2026-09-30）

B-N1/C-N1 各提交完整独立标注；A-N2 负责裁决、目标实体映射、数据分组及 Recall@K 口径/实现。C 的现有预填表不是已完成标注，A 已明确暂不冻结，见 [接收记录](a-acceptance-20260930.md)。

开发数据可继续验证流程。正式实验 A-N3 等待数据、模型和相关代码修复准备好；固定同一版本运行并保留失败、拒答及 PARTIAL。分类 recall 不等于 Recall@K；当前候选指标入口为 bench/evaluate_alignment.py，旧开发集的限定结果不代表正式集指标。详细操作与交付物见 [任务清单](tasks.md)。

## 已裁决开发版本与候选指标

seed-dev-v1 已保存双人标注、技术裁决、固定 manifest 及 hash；原 build_seed.py 仍生成 provisional 样本。新入口为 bench/builders/build_reviewed_seed.py，候选指标为 bench/evaluate_alignment.py。16 个预定可判定样本、4 个排除及详细计分规则见 [冻结说明](../bench/frozen/seed-dev-v1/README.md)。正式独立测试与真实模型实验仍待完成。

## 2026-10-12 声明级匹配第一阶段

`BenchmarkSample.claim_scope` 为可选评测字段，未设置时旧 manifest 行为不变。设置时包含 `document_ranges`（start/end，闭区间）、`code_path`、`entity_names`（允许的实现限定名/别名）、`subject`（文档主体）、`predicate`（参数/属性）。声明须完整落在任一指定区间；事实须匹配实体所属路径、允许的实体名、属性及 drift_type。公开文档主体与内部事实限定名不要求字面相同，依靠显式实体映射连接。

不存在对应声明为 SKIPPED；匹配声明但无合法事实、判断矛盾、有拒绝记录或版本不符为 UNCERTAIN。rules/full 等模式的冲突需要有效且未忽略的 finding；llm/no_verifier 仍使用未验证判断。旧模式没有重新计算历史报告。评测元数据仅用于结果匹配，不传入 scan 或模型提示。

关键词基线不能验证实体归属，新范围模式保守返回 SKIPPED；它与旧关键词分数不直接可比。跨文件导出事实现在保留逐段 provenance，并在验证时重新校验每个来源文件的 blob、偏移和链条；篡改或缺失链条会拒绝发布 finding。声明级 benchmark 行记录 `evaluation_unit=declaration`，metrics 同时记录 `evaluation_unit` 和 `declaration_count`。最终扫描范围/预算仍待冻结。相同仓库、提交和配置的规则报告现在在一次 benchmark run 内复用，但每个 sample 仍写出独立报告；相同仓库发现坐标的重复 sample 会在运行前拒绝，避免同一 finding 被重复归属。

验证使用独立合成仓库（同文档两个函数），覆盖正确目标、错误实体、声明缺失、SHA 不匹配、矛盾判断及缺失 verifier 证据。不扫描 external-v1，不使用其预测调参。测试须设置 `PYTHONPATH=src`，当前虚拟环境安装包可能仍为旧版本。

本阶段实现由 Codex 完成。2026-10-12 已完成结项所列四项源码阅读复核（Codex，A 委托，披露身份），见 [评测新代码复核](a-evaluation-code-review-20261012.md)；此前 24 条标注确认不覆盖这次新代码，亦不代签成员 A 本人。

验证补记：源码全套初跑 222 passed、2 skipped、1 failed；唯一失败为新增可选字段后 benchmark JSON Schema 未同步。已重新生成 `bench/schema/sample.schema.json`，相关契约与 benchmark 复验 37 passed；Ruff 和两模块 mypy 通过，git diff --check 通过。未声称修复后重新执行了全套。两个 skip 为 Windows 符号链接权限限制。

2026-10-12 后续收尾：新增 required_provenance 精确链约束、实际路径上的重叠声明拒绝、复用行用量去重、明确一致率与分组指标。当前预算仍按样本保守估计，不能误称实际调用量。实现边界与最新验证见[工程收尾](a-evaluation-closeout-20261012.md)。
