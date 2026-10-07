# B-N3 到期日契约与坏链接复核记录

- 执行人：成员 B
- 日期：2026-10-04
- A 的契约决定：方案 1，保持 Schema 2.0，以非必填字段扩展
- 状态：B 负责的模型、匹配、Schema、兼容测试和路径加固已完成；等待 C 完成报告展示与独立复核

## 1. 到期日字段

`Finding` 新增 `ignore_expires: date | null = null`。JSON 日期格式为 `YYYY-MM-DD`，导出 Schema 不将该字段列为必填项。

扫描开始时只获取一次日期，主扫描和补丁内存复扫使用同一日期。到期日等于扫描日时仍有效；只有到期日早于扫描日才失效。

匹配结果遵循以下契约：

| 场景 | ignored | ignore_reason | ignore_expires |
| --- | --- | --- | --- |
| 无规则匹配 | false | null | null |
| 无期限规则 | true | 规则原因 | null |
| 未来或当天到期 | true | 规则原因 | ISO 日期 |
| 已经过期 | false | 规则原因 | ISO 日期 |

多条规则仍按配置顺序处理：选择第一个有效匹配；只有没有有效匹配时才保存第一个过期匹配。有效规则的原因和日期来自同一条规则，不与过期规则混用。过期规则不会降低 `confirmed_count`，不会阻止补丁，也不会绕过 `fail_on=warning`。

## 2. Schema 与旧报告兼容

A 于 2026-10-04 确认继续使用 `schema_version="2.0"`：只承诺新程序读取旧报告，不承诺旧程序读取包含新字段的报告。原因是模型采用 `extra="forbid"`，旧程序会拒绝未知字段。

测试直接读取真实 1.0 归档 `tests/fixtures/reports/v1-default.json` 和已有 2.0 审计报告 `docs/audit-samples/b3/default/report.json`。缺失字段默认成 `null`，不重算历史忽略状态；Finding ID、patch ID 和 diff 保持不变。

固定 Schema 已重新导出到 `schemas/report.schema.json`，并由既有“生成 Schema 等于仓库 Schema”测试覆盖。

## 3. 坏链接与底层文件异常

复核结果分为三类：

| 场景 | 本轮结果 | 结论 |
| --- | --- | --- |
| 无权创建真实 symlink | 本机 `Path.symlink_to()` 抛出 OSError，测试跳过 | 环境能力不足，不等于产品通过或失败 |
| Git mode `120000` symlink blob | 既有集成测试通过 | 提交快照稳定产生 `SYMLINK_SKIPPED` |
| 补丁目标缺失/不可访问 | 修复前失败测试证明 `safe_target` 未抛项目错误；修复后返回 `UNSAFE_PATCH` | 底层 `lstat`/严格解析失败被收敛为结构化项目错误 |
| 真实越界或 dangling symlink | 测试存在；本机因创建权限跳过 | 由可创建链接的 Windows/Linux CI 复验 |

`safe_target` 现在先验证相对 Markdown 路径，再使用 `lstat` 检查普通文件、symlink 和 Windows reparse point，并用 `resolve(strict=True)` 验证最终位置仍在仓库内。缺失、无法读取状态或无法安全解析时统一抛 `UNSAFE_PATCH`，不暴露原始 `FileNotFoundError`。

C 记录的“`symlink_to` 返回后条目异常、`is_symlink` 为 false 且 `lstat` 抛 WinError 2”未在本机直接重现。本轮修复覆盖其最终错误面，因为 `lstat` 失败会转换为 `UNSAFE_PATCH`；在 C 提供原设备复现或新 CI 证据前，不宣称该历史环境现象已完全复现。

## 4. 测试证据

- 到期日失败优先测试：实现前 **10 failed**。
- B-N3 专项最终：**11 passed**。
- 契约、旧报告、Schema、既有忽略规则、补丁和路径联合回归：**109 passed，2 skipped**。
- 全量回归：**198 passed，2 skipped**。
- Ruff：43 个 Python 文件检查及格式检查通过。
- mypy：20 个源文件无类型错误。
- wheel/sdist：构建成功。

两个 skip 都是当前 Windows 进程无权创建真实文件系统 symlink；测试没有把 skip 计为通过。

## 5. 交给 C 的剩余工作

C 应只修改报告渲染及其测试，使用已落地字段区分：

- 当前忽略且无期限；
- 当前忽略且有到期日；
- 规则已过期、告警未忽略；
- 完全没有忽略信息。

报告必须使用扫描时保存的 `ignored` 状态，不得按阅读报告当天重新计算；旧报告字段缺失时不得编造日期。C 完成后需复验 JSON/Markdown 语义一致，并记录实际提交 SHA 和测试结果。
