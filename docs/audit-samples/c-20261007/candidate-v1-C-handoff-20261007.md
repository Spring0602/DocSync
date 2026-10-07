# C candidate-v1 标注交接说明（2026-10-07）

## 交接文件

| 项 | 值 |
| --- | --- |
| 标注包 | `bench/annotations/candidate-v1/packet.json` |
| 标注包 SHA-256 | `9967F0890C08EC4DD3E4F41E415C9E4AD58B5F8B3C4D2941CB145643273D6055` |
| C 完成表 | `runs/annotations-C-candidate-v1.csv` |
| C 完成表 SHA-256 | `5082AD65C1378116CD9EE5BE0E0A8EA25929AD3BE0DE4CF0C0758DBDBDF8C882` |
| 建议/审查过程表 | `runs/candidate-v1-C-suggestion-table.csv` |
| 建议/审查过程表 SHA-256 | `6730ADD15C87CA7599EA7D8ACD1D27083C8353A633EAABBF9BB8BEA94F1D8569` |
| reviewer | `C` |
| reviewed_at | `2026-10-07` |
| 固定代码基线 | 当前本地已同步到 `a95728a0216e149d8e805fac3e6f839040070a6c` |

## C 表完成情况

| 标签 | 数量 |
| --- | ---: |
| `CONSISTENT` | 11 |
| `INCONSISTENT` | 8 |
| `INSUFFICIENT` | 5 |

| 类型 | 数量 |
| --- | ---: |
| `DEFAULT_VALUE` | 8 |
| `SIGNATURE` | 8 |
| `CONFIG` | 8 |

本地字段校验结果：24 行完整，`sample_id` 无重复，`reviewer` / `reviewed_at` / `label` / `drift_type` / 行号 / target / evidence / reason 均已填写。项目官方 `bench.annotation_packet check` 需要同时提供 B 和 C 两份表；当前 B 表未在本机提供，因此双表结构检查待 A 收齐后执行。

## 需要 A 裁决或统一口径的样本

以下样本被 C 标为 `INSUFFICIENT`，原因均为固定源码无法排除运行时环境或外部输入影响：

| sample_id | 类型 | 原因 | 建议 A 关注点 |
| --- | --- | --- | --- |
| candidate-07 | `DEFAULT_VALUE` | `flush_records.interval` 来自 `flush_interval()`，读取 `FLUSH_INTERVAL` 环境变量。 | 是否按无环境变量时 fallback `8` 作为默认值。 |
| candidate-12 | `SIGNATURE` | `queue_notice(..., **read_options())` 中 `read_options()` 读取 `NOTICE_OPTIONS`，无法确认是否含 `priority`。 | 是否要求固定输入才能判定示例绑定正确。 |
| candidate-16 | `SIGNATURE` | `dispatcher()` 根据 `REMOTE_DELIVERY` 返回不同对象；远程对象的 `deliver` 需要 `token`。 | 是否按默认无环境变量路径判定，还是视为运行时不确定。 |
| candidate-19 | `CONFIG` | `ARCHIVE_LEVEL` 由 `ARCHIVE_PROFILE` 决定，可能为 2 或 7。 | 是否把无环境变量路径视为默认配置。 |
| candidate-23 | `CONFIG` | `STORAGE.local.root` 来自 `STORAGE_ROOT` 环境变量，fallback 为 `./cache`。 | 是否按 fallback 默认值判定一致。 |

## 来源/模板独立性疑问

- 本包 24 条候选来自 6 个 synthetic controlled families，不是 6 个真实外部仓库来源；正式 test 独立性需要 A 按 `bench/candidates/controlled-v1/README.md` 审查。
- 多个样本使用与开发集相近的默认值、签名绑定和配置模板；C 不判断其是否足以构成正式独立 test，仅提交标签和疑问。
- C 未为了满足 24 条数量或类别配额改变标签；环境依赖或证据不足的样本保留为 `INSUFFICIENT`。
- C 未运行规则或模型评测；本交接仅为人工标注结果和固定原文审查。

## 给 A 的一句话

> C 已完成 candidate-v1 的 24 行独立标注，文件为 `runs/annotations-C-candidate-v1.csv`，SHA-256 为 `5082AD65C1378116CD9EE5BE0E0A8EA25929AD3BE0DE4CF0C0758DBDBDF8C882`。其中 5 条因运行时环境变量或外部输入不确定标为 `INSUFFICIENT`，请 A 收齐 B 表后统一口径并运行双表结构检查。
