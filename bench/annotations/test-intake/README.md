# 新测试样本采集交接包

状态：已收集 **24 条 AI 辅助自建候选、6 个受控组**，intake.jsonl 已填写实际来源和固定提交；标签及独立性待 B/C 审核。直接开始请看 [candidate-v1 标注包](../candidate-v1/README.md)，无需重复准备。正式测试集尚未冻结。

## A 采集与固定来源

在 intake.jsonl 每行填写一个 JSON 对象，所有字段都是非空字符串：

| 字段 | 填写内容 |
| --- | --- |
| sample_id | 新的唯一 ID，仅字母数字、下划线和短横线 |
| repo_id / group_id | 真实来源仓库 ID / 同仓库或同模板族分组，不能与开发数据交叉 |
| repo_path | 本机仓库路径，相对 intake.jsonl 所在目录；避免提交个人绝对路径 |
| head_sha | 40 位小写完整提交 SHA |
| code_path / document_path | 固定提交内的 UTF-8 文件路径，使用 / |
| origin / source | controlled 或 real；自建来源说明或外部来源 URL |
| license / rights_evidence | 许可证及实际许可依据索引；工具不代为认定版权 |
| prior_exposure | 谁接触过标签、开发种子、模型输出，以及是否 AI 辅助编写；无接触也显式记录 |
| collected_at | 实际采集日期 |

每项应包含一个待核对声明；复杂跨文件案例先整理完整依赖证据，当前工具仅打包所列代码/文档两文件，不适合缺失依赖的案例。按 docs/formal-test-protocol.md 审查来源和组隔离。建议 24 例/6 组只是采集目标，不是已获得数据；不得编造权限或标签。不要填 gold、label、prediction。

准备好真实来源后，在项目根目录运行：

```powershell
.\.venv\Scripts\python.exe -m bench.annotation_packet prepare --intake bench/annotations/test-intake/intake.jsonl --out runs/test-annotation-v1
```

空清单会拒绝执行。工具只读 Git 固定 blob，不执行目标源码，也不调用 DocSync 扫描或模型。输出 packet.json（元数据、行数及 SHA-256）、每样本原文和两个待填表；任何已存在输出目录均拒绝覆盖。源码与 README 分别保存为 code_path.txt/document_path.txt，内容原样保留，行号按原文件计算。

## B/C 分别独立标注

A 分别交给 B/C：同一 packet.json、所有样本原文、各自的 individual-B.csv 或 individual-C.csv，另附本说明。不要把对方已填表放进标注材料。source/权限/接触说明随包披露；包中没有答案。

每位成员填写本人 reviewer/reviewed_at，独立判断 label、drift_type、目标实体、证据和理由；行号使用 3 或 3-7 格式。questions 可空，其他列必填。不要改预填的 ID、SHA 和文件路径。不足以判断时填 INSUFFICIENT 并说明缺失证据，不能猜答案；目标无法唯一确定时在 target_entity 和 reason 如实说明。

## A 收表后的检查与裁决

```powershell
.\.venv\Scripts\python.exe -m bench.annotation_packet check --packet runs/test-annotation-v1/packet.json --b runs/test-annotation-v1/individual-B.csv --c runs/test-annotation-v1/individual-C.csv
```

退出 2 表示结构缺项或不一致，按 errors 退回补充；退出 0 仅表示结构齐全。requires_adjudication 列出标签、类型、实体或坐标差异，一致行也要复核。工具不能验证人员身份、真实独立性或理由是否正确，不自动授予 adjudicated/rights cleared，也不生成 test manifest。A 逐条裁决及许可/泄漏复核完成后另建 test-v1，再进行任何扫描。当前阶段不要将数据直接交给 benchmark。
