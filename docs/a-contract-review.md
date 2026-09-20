# 成员 A：契约审查与验收准备

日期：2026-09-20。范围：当前 0.2.0 实现。本文是工具辅助审查记录，待成员 A 人工复核；不代表 B、C 已签字，也不替代真实模型验证。

## 当前可执行事项及结果

| 任务 | 本轮结果 | 完成边界 |
| --- | --- | --- |
| A1 对外契约 | 已核对下表；新增 14 项自动化测试全部通过 | 人工复核后可确认 A1；已知边界均明确记录 |
| A2 真实模型 | 保留阻塞：尚未提供模型服务 | 不调用占位 endpoint，不将受控响应算作真实试运行 |
| A3 数据与指标 | 已准备独立标注、裁决模板和指标口径 | B、C 标注、正式冻结、Recall@K 与真实实验未完成 |
| A4 最终验收输入 | 已建立四类证据状态表 | 只记录实际证据；不提前通过发布验收 |

## 对外契约核对表

| 入口 | 输入和默认行为 | 输出 | 成功及失败约定 |
| --- | --- | --- | --- |
| scan | repo 默认当前目录；head 默认 HEAD；base 可选；working-tree 必须显式；config 仅显式可信 TOML | 默认 JSON、Markdown，加 manifest、snapshot、summary 和阶段 JSONL；out 必须新建或为空 | 2=全局失败；3=PARTIAL 且 require-complete；1=存在未忽略确认告警且 fail-on=warning；其余 0，按此前后顺序判定 |
| patch | report 为完整 ScanReport，必须恰有一个 VALIDATED proposal | diff 和清单，默认清单为输出路径追加 .json | 0=导出；无合格补丁或输入损坏=2；不会应用文件修改 |
| apply | repo、diff 文件和对应清单 | stdout 的 APPLIED 及路径列表 | 0=应用；哈希过期、diff 不符、越界等=2；多文件写入失败回滚由既有集成测试覆盖 |
| schema | kind=report（默认）或 benchmark；out 可选 | 文件或 stdout 的 JSON Schema | 0=导出；无法写入=2；不是扫描，也不生成 run 目录 |
| benchmark | 固定 manifest、可信 config、空 out；method 默认 rules | predictions.jsonl、metrics.json；非 keyword 方法另存逐样本扫描报告 | 0=所有样本完成；3=有 failed/partial 样本；清单/配置等全局输入错误=2 |
| 配置 | 未提供 config 时使用内置默认值；未知字段拒绝；CLI 对 mode/fail-on/require-complete 显式值覆盖配置 | 配置 hash 写入运行记录 | 密钥通过环境变量读取，未知字段报 INVALID_INPUT，不回显用户输入值 |

补充解释：scan 默认 fail-on=none、require-complete=false，因此退出 0 本身不能证明扫描完整或没有告警，调用方必须检查 summary。参数拼写/必填项错误由 argparse 返回 2，stderr 是用法文本，并非 JSON。scan 在创建输出目录前失败（例如目录非空）时保留原目录；创建后失败才尝试写结构化错误文件。其他命令的全局错误主要通过 stderr JSON 返回，不承诺都有 failure.json。

## 版本与失败报告边界

1. 支持读取实际 1.0 和当前 2.0 完整报告。新增字段使用默认值，旧版事实、声明、定位、Finding 证据、补丁内容均应保留。兼容读取不等于用新规则重新判断，也不保证 0.1.0 程序接受新报告。
2. 没有独立 `report` CLI 子命令。重生成报告使用 `reporting.write_report`，测试已覆盖 JSON 往返和 Markdown 渲染；`patch` 是公开的报告读取入口。
3. 全局失败时 `report.json`/`manifest.json` 是含 status/code/message/stage 的错误信封，不符合完整 ScanReport Schema。消费者先判断顶层 `status == FAILED`，不要直接反序列化为 ScanReport。这是当前双结构约定，不是丢失证据的成功报告。
4. 未知 Schema 版本或字段不做静默兼容；结构和证据关联校验失败必须拒绝。测试覆盖两版报告的伪造提交证据拒绝。
5. `patch` 的输出文件可能覆盖同名文件，与 scan 的非空目录保护不同。操作时使用独立输出名并先审阅；本轮只记录行为，不变更对外契约。

归档样本来源及 hash 见 [兼容性样本说明](../tests/fixtures/reports/README.md)。没有升级 Schema 或修改 B 的静态分析逻辑。

## 重复执行

在仓库根目录执行；测试使用临时目录，自建 Git 样本，不需要网络或模型密钥。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/integration/test_a_contract_review.py -q --junitxml=runs/a-review/contracts.xml
.\.venv\Scripts\python.exe -m pytest tests/unit/test_metrics.py tests/integration/test_benchmark.py -q --junitxml=runs/a-review/metrics.xml
```

实际结果：第一条 14 passed，第二条 8 passed；新增测试文件的 Ruff 检查及格式检查通过。契约测试覆盖两版读取/输出/补丁、篡改拒绝、失败信封、退出码优先级、两类 Schema 导出和未知配置脱敏拒绝。指标测试覆盖失败正例、拒答、零分母、无模型不伪造预测及数据划分。完整扫描、apply、benchmark 行为另由已有集成测试支撑，不将单份归档样本称为覆盖所有历史报告。

## A3 指标裁决口径与缺口

| 项目 | 当前口径 | A 的后续动作 |
| --- | --- | --- |
| TP/FP/TN/FN | 正例拒答/跳过/失败计 FN；负例拒答计 TN，但降低决策覆盖率 | 同时展示覆盖率和拒答率，不以 TN 增多声称模型效果提高 |
| 证据不足 | INSUFFICIENT 不纳入二分类分母；预测冲突计不当确认 | 单独报告数量与不当确认率 |
| 零分母 | 指标为 null | 不改写成 0 或 100% |
| FAILED/PARTIAL | FAILED 不允许确定预测；PARTIAL 可保留规则已验证结果；benchmark 汇总 failed_or_partial | 区分“局部有证据”与“完整实验成功”，每种方法都报告状态数量 |
| Recall@K | 目前未实现；现有 gold 只有分类标签，没有人工确认的目标事实映射 | 标注时补目标源码位置和实体；冻结后建立稳定目标映射，再实现候选命中统计，不能用分类 recall 冒充 |
| 正式分组冻结 | runner 已检查 repo/group 跨 split 泄漏；20 个现有样本均是 provisional dev | B、C 独立标注后 A 裁决；标注完成不自动成为 test，另行确定组划分 |
| 方法公平性 | llm/no_static 保留固定提取范围和候选 ID | 按 docs/benchmark.md 披露边界；不能宣称无限制全文 LLM 对比 |

可立即交给 B、C 的材料见 [标注与裁决步骤](../bench/annotations/review-protocol.md)。模板为空，不代填任何人的判断、姓名或签字。

## A4 四类验收证据

| 类别 | 已有证据 | 当前结论 | 还需要谁交付 |
| --- | --- | --- | --- |
| 本地已验证 | docs/verification.md 中 98 通过/1 跳过记录；本轮新增契约测试与指标测试 XML | 已有自动化证据，Windows symlink 用例仍受权限限制 | A 复核，B/C 交付各自审核结果 |
| 真实模型已验证 | 无；现有 provider 测试为受控传输 | 未完成 | 用户准备服务；A 保存实际调用、版本、usage、失败和费用记录 |
| 远程 CI 已验证 | 只有工作流文件和本地 Action 测试 | 未完成，没有远程成功链接 | C 提交实际 SHA、Windows/Linux 运行链接及日志 |
| 人工审核已验证 | 未收到 B、C 独立标注、权利签名或第二设备记录 | 未完成 | B、C 标注，A 裁决；团队确认权利和发布材料 |

提交身份与首次推送授权仍待确认；本轮不创建虚构提交 SHA，不推送远程，不勾选真实模型、人工或远程验收项。
