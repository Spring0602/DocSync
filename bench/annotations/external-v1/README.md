# external-v1 无标签标注包

本包包含六个外部固定提交中的 24 个声明单元，每仓库四条。**状态：等待 B/C 独立标注；正式测试集尚未冻结。** 这是按固定入口顺序筛选的小样本，未运行 DocSync、规则基线或真实模型，未预填标签。没有承诺冲突/一致/证据不足的数量，也不能据此声称六组相互独立或模型未见过这些代码。

## 从哪里开始

1. 先核验 `checksums.json`；仓库中可执行 `python -m bench.builders.build_external_packet --verify bench/annotations/external-v1`。该命令验证原始空白包，因此请把个人填写版本放到另外的工作目录，不覆盖本包。
2. B 只复制 `individual-B.csv` 与 `exposure-B.md`；C 只复制 `individual-C.csv` 与 `exposure-C.md`。两人使用相同 `packet.json` 和原文，不查看对方答案、DocSync 报告、模型预测或已知缺陷解答。
3. 打开 `SAMPLES.md`，逐条查看评估问题、原文坐标与代码入口。`external-XX/document_path.txt` 和 `code_path.txt` 是完整 Git blob，不是改写节选；编辑器从第 1 行计数。原文内的示例输出属于待核对声明，不是本包提供的 gold。
4. `context/<source-id>/...` 保存同提交的导出、包装器和配置上下文；`context-index.json` 列出原路径、固定 URL、blob SHA 与文件 SHA-256。不要安装、导入、执行第三方项目。现有上下文若不足，填 questions，A 再按同 SHA 补证并记录新包版本，不凭印象补全。
5. 按下方字段说明填写所有 24 行，并如实填写接触声明。若使用 AI 生成判断或证据，必须披露；不得自动记作盲态独立人工金标准。发现以前阅读/开发过某条也照实记录，不自行删行。
6. 完成后把个人表、接触声明、包 SHA-256 和个人表 SHA-256 交给 A；先独立冻结各自文件再交换答案。两份空表在未填写时相同是正常的。尚未收齐前不要把答案提交到对方会提前看到的共享分支。此处是交接说明，未替任何成员发送消息。

## CSV 字段

保留 14 列及行数，不修改 sample_id、head_sha、document_path、code_path。建议文本编辑器或以 UTF-8 文本导入表格，防止 SHA/行号被自动转换。

| 字段 | 如何填写 |
| --- | --- |
| reviewer | 实际审核人标识，由本人填写 |
| reviewed_at | 实际完成日期 YYYY-MM-DD，不用包生成日期代替 |
| label | CONSISTENT、INCONSISTENT、INSUFFICIENT 之一，按指定声明判断 |
| drift_type | DEFAULT_VALUE、SIGNATURE、CONFIG 之一；无冲突/证据不足也填写所核对声明类型 |
| document_lines | 原文件中实际作为证据的行号，如 12 或 12-16；至少覆盖指定文档焦点，范围可扩展 |
| code_lines | code_path 对应完整原文件的实际证据行号；入口只是查阅提示，不能不看代码直接复制 |
| target_entity | 实际归属实体，由本人确认；若文档对象是动态生成/无法静态定位，请明确写明，并在 questions 解释 |
| evidence | 文档与代码具体证据；跨文件补证用 原路径:行号，并核对 context-index 中的版本/哈希 |
| reason | 自己的判断过程；INSUFFICIENT 写明缺少什么条件/证据，不能把工具无法识别直接当证据不足 |
| questions | 未决疑问/需补的上下文；没有疑问可留空 |

CONSISTENT 要有证据支持指定声明；INCONSISTENT 要能给出具体矛盾；INSUFFICIENT 用于在可获得的固定证据与明确条件下无法裁决。不因为源码动态或文档英文就自动拒答。调用绑定评估不等于运行结果保证。原文没有声明的行为不扩大解释为一致。代码入口由采集助手提供，B/C 必须自行验证，不是标准答案或候选召回真值。

## 收齐后 A 执行

```powershell
python -m bench.annotation_packet check --packet bench/annotations/external-v1/packet.json --b <B实际交付.csv> --c <C实际交付.csv>
```

该检查只验证结构，不证明语义、人工身份、独立性或权利。A 逐条裁决两表，审核接触情况/来源家族/许可，再固定每条未来实验的扫描边界、计分声明映射、重复文档的处理方式、提交/配置/预算。多个样本共享文档和代码，不能把同一仓库级发现自动算作所有声明命中；本包不是 bench.run_suite 的 manifest。

正式冻结前禁止拿本包输出调参后仍称独立 test。若缺少冲突或某类别，不通过篡改原文/删除难例补配额；另行设计并登记新一轮采集。包版本冻结是原文交接固定，不是正式评测冻结。

## 许可证与来源

每个 `licenses/<source-id>/` 中保留上游完整许可证；版权及 MIT/BSD-3-Clause 条件继续适用。`rights-review.json` 记录原文和可见声明的检查范围。未下载或再分发 README 引用的图片、logo、外部页面；源码/docstring 的原样内容不代表 DocSync 的结论。A 后续最终发布审查未由脚本代签。

`selection.json`、`screening-policy.md`、`sources.jsonl` 保留选择与暂缓依据。每仓库一个暂定组，`overlap-review.json` 只记录可机械核对的重叠；家族关系和 B/C 接触声明仍需人审。采集助手接触过项目开发历史，来源在预训练中是否存在未知。
