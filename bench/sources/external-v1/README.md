# external-v1 来源与具体样本准备

六个候选来源已经进入具体筛选，生成 **24 个无标签声明单元**，见 [标注包](../../annotations/external-v1/README.md) 与 [样本导航](../../annotations/external-v1/SAMPLES.md)。正式测试集仍未冻结，正式可计分样本数仍为 0。

`sources.jsonl` 和 `source-acceptance.json` 保留来源发现/用户接受时的记录（其中 sample_count=0、尚未读正文等字段是当时状态）；不回写它们冒充采集前就已知道样本。当前筛选结果由 `selection.json`、`screening-policy.md` 及标注包的 `context-index.json` 补充。代码/文档完整 SHA-256、行数和 Git blob SHA 以该索引为准。

- screening-policy.md：读取正文前确定的纳入顺序、每来源四条上限及保留难例规则。
- selection.json：24 条具体评估问题、原文焦点/源码入口、补充上下文和排除/上限暂缓记录。
- handoff.md：打包时复制成包 README 的 B/C 操作说明。
- licenses/：各固定版本上游完整许可证，保持字节与 SHA-256。
- excluded.json：来源发现阶段的排除记录；不等于本轮声明筛选结果。

新脚本 `python -m bench.builders.build_external_packet --out <全新目录>` 从本地固定 Git 对象离线重建，不扫描或导入目标项目。源缓存位于被 Git 忽略的 `runs/external-v1-repos/<source-id>`。新机器先按 sources.jsonl 的 source_url/head_sha 创建 bare 仓库并 fetch 固定 SHA（命令见项目 docs/external-annotation-handoff-20261011.md）。检验已有包不需要下载源仓库：

```powershell
.\.venv\Scripts\python.exe -m bench.builders.build_external_packet --verify bench/annotations/external-v1
```

B/C 私有工作副本完成前不交换答案；各自接触声明、A 家族/许可审查、逐条裁决及实验范围设计仍待完成。原文属于第三方 MIT/BSD-3-Clause 授权，不改授项目 Apache-2.0。来源收集由接触过开发历史的 AI 辅助，不声称随机抽样、类别均衡或模型训练不可见。
