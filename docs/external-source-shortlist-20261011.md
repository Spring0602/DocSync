# 外部正式测试候选来源清单（2026-10-11）

**后续进展：已按本清单完成 24 个具体无标签声明单元，见 [本轮交接](external-annotation-handoff-20261011.md)。下文保留来源发现阶段状态；当前尚无冻结正式测试集。**

已收集 6 个外部仓库来源，另保留 1 个排除记录。**目前是来源清单：已冻结到完整 Git SHA，但尚未采集具体样本、预填标签或运行 DocSync/模型；正式样本数为 0。** 六个仓库不自动等于六个独立样本家族。

本次通过 GitHub API 核对仓库、提交、递归目录和许可证 blob。候选代码/文档路径已验证存在并记录 Git blob SHA；尚未读取并选定具体声明，所以行号、文件 SHA-256 及逐文件权利状态保持待定，不能交给 benchmark 当成正式 manifest。

| ID | 来源（固定版本入口） | 许可证标识 | 优先查看文档 | 筛选注意点 |
| --- | --- | --- | --- | --- |
| external-source-01 | [encode/httpx](https://github.com/encode/httpx/tree/b5addb64f0161ff6bfe94c124ef76f6a1fba5254) | BSD-3-Clause | `docs/advanced/timeouts.md`、`docs/advanced/resource-limits.md` | 默认值/配置候选入口；具体声明是否可提取尚未评估 |
| external-source-02 | [Delgan/loguru](https://github.com/Delgan/loguru/tree/0412a60d6aff63a4ed009c7445993b42d294c2f1) | MIT | `README.md` | 调用签名/默认值候选入口；动态日志配置不预判 |
| external-source-03 | [theskumar/python-dotenv](https://github.com/theskumar/python-dotenv/tree/0b2880591780a426b0551436f47a17e7a76d954f) | BSD-3-Clause | `README.md`、`docs/index.md` | 默认值/环境配置候选入口；不将环境 fallback 当真实值 |
| external-source-04 | [Textualize/rich](https://github.com/Textualize/rich/tree/9d8f9a372cc5916fd4781fec207ced7ddac2f08f) | MIT | `README.md` | 调用示例候选入口；主要详细文档格式与当前支持范围需另查 |
| external-source-05 | [python-attrs/attrs](https://github.com/python-attrs/attrs/tree/644b4e165bfbeee7e127de6fcbda08b64014316f) | MIT | `docs/examples.md`、`docs/init.md` | 调用接口候选入口；装饰器生成接口可能超出静态支持范围 |
| external-source-06 | [rsalmei/alive-progress](https://github.com/rsalmei/alive-progress/tree/69d9bf0aba6276e2434a3a595cceca55040d64d7) | MIT | `README.md` | 进度条调用/配置候选入口；上下文管理和动态配置需另审 |

完整 SHA、候选代码路径和许可证原文索引见 [机器可读清单](../bench/sources/external-v1/sources.jsonl)。许可证证据来自各固定版本，外部材料不自动纳入本项目的 Apache-2.0。后续实际摘录需保留适用版权、许可证及额外说明，当前未标记 rights_status=cleared。

排除：[Tenacity](https://github.com/jd/tenacity) 的目录筛查未发现适合本轮的 Markdown 文档；不为纳入它而先转换文档或修改工具。记录见 [excluded.json](../bench/sources/external-v1/excluded.json)。未检索 issues/PR 中的已知缺陷答案，未按扫描预测筛选项目。

## 用户来源确认

2026-10-11 成员A认可这六个来源，并回复“还没用过”。已记入 [来源确认](../bench/sources/external-v1/source-acceptance.json)，允许进入具体样本准备。该反馈未单独证明 B/C 从未阅读代码或缺陷；各自接触声明随标注交接补充，不要求重复确认本次来源认可。

## 下一步如何使用

1. A/B/C 先对这六个仓库填写是否接触过具体代码、文档、缺陷或开发样本；不熟悉项目不等于可证明模型训练时没见过。来源收集由接触过开发历史的助手辅助，已披露，不能称采集者盲态。
2. 按固定 SHA 查看上述入口，选择具体声明及相关代码；记录代码/文档行号、完整文件 SHA-256、归属实体、权利证据。先确定纳入规则，不根据 DocSync 输出挑选。文档缺少可评估声明时保留排除理由，不强凑 24 条或标签比例。
3. 同仓库、派生或同模板关系按组审查；路径/哈希不同不证明独立。存在开发接触时需裁决排除或降级为 dev。
4. 获得足够合格样本后另建外部样本 intake，利用既有 prepare 工具生成同版本原文及 B/C 空白表。不要覆盖旧 test-intake/intake.jsonl 或 candidate-v1。B/C 的旧成果无需重做。
5. 双标、裁决及独立性审查完成后冻结正式集，再运行模型。当前不授予 split=test、人工标签或发布许可结论。

Rich 的 AI_POLICY.md 已查阅，仅讨论向其项目提交 AI 生成 PR 的条件；本次未向任何上游提交 PR 或发送消息。来源选择不代表上游认可本项目。
