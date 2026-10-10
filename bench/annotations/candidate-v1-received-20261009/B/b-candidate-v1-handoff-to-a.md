# B candidate-v1 独立标注交接给 A

- 标注成员：B（卢佳妮）
- 完成时间：2026-10-09T00:39:28+08:00
- 工作分支：`member-b-candidate-v1`
- 基线提交：`a95728a0216e149d8e805fac3e6f839040070a6c`
- 完成表：`bench/annotations/candidate-v1/individual-B-20261009.csv`
- 完成表 SHA-256：`02df0604d36805fb105744ae25c9946106f76ad1d6c9740c6743e1f59417c67e`
- packet SHA-256：`9967f0890c08ec4dd3e4f41e415c9e4ad58b5f8b3c4d2941cb145643273d6055`

## 完整性与分布

- 24 行、14 列、24 个唯一 sample_id、0 个重复 ID。
- 身份字段 `head_sha`、`code_path`、`document_path` 与 packet 全部一致。
- `CONSISTENT`：11 条。
- `INCONSISTENT`：8 条。
- `INSUFFICIENT`：5 条。
- `DEFAULT_VALUE`、`SIGNATURE`、`CONFIG` 各 8 条。
- 项目自带 `bench.annotation_packet` 校验器未报告任何 B 行错误。整体双表检查仍会因入库的 C 空白表缺少人工字段而失败，必须等 C 独立提交后由 A 重新运行。

## B 的待补证据项

| sample_id | 缺少的证据 |
| --- | --- |
| candidate-07 | 模块导入并定义 `flush_records` 时 `FLUSH_INTERVAL` 的实际值，或环境保证未设置该变量。 |
| candidate-12 | `NOTICE_OPTIONS` 的实际 JSON，以及 `read_options()` 是否只返回包含合法 `priority` 的关键字字典。 |
| candidate-16 | `REMOTE_DELIVERY` 的实际值，用于确定 `dispatcher()` 的运行时接收者。 |
| candidate-19 | `ARCHIVE_PROFILE` 的实际值，或固定环境是否保证为 `compact`。 |
| candidate-23 | `STORAGE_ROOT` 的实际值，或目标环境是否保证未设置该变量。 |

这些项均保留为 `INSUFFICIENT`，没有把运行时不确定性静默简化为一致。

## 既往接触与独立性声明

成员 B 及本次辅助标注的 Codex 在本批任务前已经参与并阅读过旧的 20 条开发种子、B-N1—B-N3 相关实现与验证材料，因此熟悉默认值、签名和配置类旧模板，不能声称对旧开发集盲态。

开始本批 candidate-v1 标注前，未阅读这 24 条候选的 C 标签；本次只读取固定的 B 空白表、`context.md`、`packet.json`、原始 `spec.json`、来源说明和校验器规则。没有打开或复制 C 的候选标注答案，没有运行 DocSync 扫描或模型预测来替代逐条判断。

本表由成员 B 授权 Codex 基于固定原文进行 AI 辅助标注。该事实必须随表交给 A，不能把结构通过或双方一致自动解释为“独立人工金标准”。A 仍需检查每个技术家族与旧开发种子的派生关系、逐条裁决，并决定哪些组只能保留为 dev。

## 给 A 的复验步骤

1. 核对完成表和 packet 的 SHA-256。
2. 在未向 B/C 展示对方答案的前提下收齐 C 表。
3. 运行：

   ```powershell
   .\.venv\Scripts\python.exe -m bench.annotation_packet check `
     --packet bench\annotations\candidate-v1\packet.json `
     --b bench\annotations\candidate-v1\individual-B-20261009.csv `
     --c <C 的完成表路径>
   ```

4. 对 24 条全部裁决，不只处理分歧项；5 条 `INSUFFICIENT` 必须取得缺失证据后才能改成确定标签。
5. 按 `candidate-family-01` 至 `candidate-family-06` 整组审查与旧数据的模板派生关系，同组不得跨 dev/test。

在 C 完成独立提交前，不应把本分支推送到 C 可见的公共位置，以免破坏双标独立性。
