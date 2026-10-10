# candidate-v1：B/C 已完成标注统一接收目录

整理日期：2026-10-09。这里放已完成的两份表及交接说明；原始根目录附件、原 docs/audit-samples 归档及 candidate-v1 空白表均保留。本目录是接收归档，不是新的候选数据版本，不改写成员意见，也没有生成最终标签。

| 成员 | 完成表 | 交接与补充 |
| --- | --- | --- |
| B | [individual-B-20261009.csv](B/individual-B-20261009.csv) | [交接说明](B/b-candidate-v1-handoff-to-a.md) |
| C | [annotations-C-candidate-v1.csv](C/annotations-C-candidate-v1.csv) | [交接说明](C/candidate-v1-C-handoff-20261007.md)、[审查过程表](C/candidate-v1-C-suggestion-table.md) |

共 24 条；两表均为 11 CONSISTENT、8 INCONSISTENT、5 INSUFFICIENT，标签逐条一致。结构检查已通过，实体写法/证据坐标等差异见 [对照表](comparison.md)、[结构结果](pair-check.json)及 [JSON 对照](comparison.json)。不能把 label 相同当作所有字段一致或正式测试已验收。

B 表来源为用户放在项目根目录的原件，原始 SHA-256 与 B 提供的 02df0604d36805fb105744ae25c9946106f76ad1d6c9740c6743e1f59417c67e 一致。C 来源于合并的 4462ff7；原交接哈希按 CRLF 计算，Git blob 为 LF，原始字节与 LF 归一化哈希同时记录于 [source-index.json](source-index.json)。复制文件逐字节核对，目录的 Git 属性保留原始字节以便跨平台验收。

固定原文仍见 [candidate-v1/context.md](../candidate-v1/context.md)，packet SHA-256 为 9967f0890c08ec4dd3e4f41e415c9e4ad58b5f8b3c4d2941cb145643273d6055。交接说明中的旧 runs 路径和状态属于成员提交时的记录，不直接修改；当前接收状态以本页为准。

A 下一步：结合原文逐条统一实体与证据范围，再裁决 24 行，按组审查与开发种子的模板关系；保留 B 的 AI 辅助和既往接触披露。candidate-07/12/16/19/23 在两表中均为 INSUFFICIENT，不能未经补证就改成确定标签。尚未完成最终裁决或正式 test 冻结，本轮未执行扫描或模型请求。

复验命令（项目根目录）：

```powershell
.\.venv\Scripts\python.exe -m bench.annotation_packet check --packet bench/annotations/candidate-v1/packet.json --b bench/annotations/candidate-v1-received-20261009/B/individual-B-20261009.csv --c bench/annotations/candidate-v1-received-20261009/C/annotations-C-candidate-v1.csv
```

## 技术裁决已完成（2026-10-10）

本目录的 comparison 保留接收时原始差异，不回写伪装双方一致。最终统一实体、证据和标签见 [candidate-dev-v1](../../frozen/candidate-dev-v1/README.md)。全部六组按已知来源与接触情况保留 dev，human_signoff 仍待本人，正式测试冻结未完成。
