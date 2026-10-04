# B-N3 忽略到期日字段契约提案

- 提案人：成员 B
- 日期：2026-10-04
- 状态：A 已于 2026-10-04 确认方案 1；B 按确认契约实施；等待 C 确认报告展示需求
- 修改边界：B 修改模型、忽略匹配、Schema 和契约测试；C 修改 JSON/Markdown 报告展示及展示测试

## 1. 提议字段

在 `Finding` 增加：

```python
ignore_expires: date | None = None
```

JSON 使用 ISO 8601 日期字符串，例如 `"2026-10-31"`；无期限或旧报告缺失该字段时为 `null`。`ignored` 是扫描发生时是否实际忽略的权威状态，报告不得根据阅读报告当天的日期重新计算它。

## 2. 状态语义

| 场景 | `ignored` | `ignore_reason` | `ignore_expires` | 含义 |
| --- | --- | --- | --- | --- |
| 没有规则匹配 | `false` | `null` | `null` | 未忽略 |
| 匹配无期限规则 | `true` | 规则原因 | `null` | 当前忽略，无期限 |
| 到期日晚于扫描日 | `true` | 规则原因 | ISO 日期 | 当前忽略，在该日结束后失效 |
| 到期日等于扫描日 | `true` | 规则原因 | ISO 日期 | 边界日仍有效 |
| 到期日早于扫描日 | `false` | 规则原因 | ISO 日期 | 匹配到已失效规则，Finding 仍是活动问题 |
| 旧报告缺少字段 | 保留原值 | 保留原值 | 默认 `null` | 不重算历史结果 |

过期规则只有在确实满足 finding ID、rule ID 和路径条件时才写入元数据。若多个规则匹配，按配置顺序选择第一个仍有效的规则；只有没有有效匹配时，才记录第一个已过期匹配。这样不会让前面的过期规则遮蔽后面的有效规则。

## 3. 不变量

- `ignored=true` 时 `ignore_reason` 必须来自实际匹配规则。
- `ignored=false` 且 `ignore_expires` 非空时，表示匹配规则在扫描日之前已过期；不得计入 `ignored_count`，也不得阻止补丁或失败阈值。
- `ignore_expires=null` 不能单独区分“无规则”和“无期限规则”，必须结合 `ignored` 与 `ignore_reason`。
- 到期判断保持当前规则：`expires < scan_date` 才算过期，因此 `expires == scan_date` 当日仍有效。
- 读取旧报告只填默认值，不重新运行忽略匹配，不更改历史 `ignored`、计数、Finding 或补丁。

## 4. A 的兼容性决定

该字段有默认值，当前程序可以读取字段缺失的真实 1.0 报告和已有 2.0 报告，属于“新读旧”兼容。

但模型使用 `extra="forbid"`：旧版程序读取包含 `ignore_expires` 的新报告时会拒绝未知字段。因此在不提升 `schema_version` 的情况下，这不是严格的双向兼容。

A 于 2026-10-04 明确同意方案 1：继续使用 `schema_version="2.0"`，`ignore_expires` 不列为必填字段；只承诺新程序读取旧 1.0/2.0 报告，不承诺旧程序读取新增字段后的报告。旧报告缺失字段时填 `null`，不重新计算历史状态，不改变原 Finding ID 或补丁。

A 同时确认一次扫描固定同一个日期、到期日当天仍有效、早于扫描日才失效，以及多规则按原优先级选择且有效/过期规则的原因和日期不得混用。

## 5. C 的展示契约（请 C 确认）

C 的报告渲染应直接展示扫描结果，不按当前日期重算：

- `ignored=true, ignore_expires=null`：显示“当前忽略；无期限”。
- `ignored=true, ignore_expires=<date>`：显示“当前忽略；到期日 `<date>`”。
- `ignored=false, ignore_expires=<date>`：显示“忽略规则已失效；到期日 `<date>`”，同时仍作为未忽略 Finding 展示。
- 全部忽略字段为空：不编造忽略信息。

请 C 确认字段足以完成 JSON/Markdown 一致展示，并说明计划修改的报告文件，避免与 B 同时编辑。

## 6. B 计划的验收测试

- 无匹配、无期限、未来日期、当天边界、昨天过期。
- 前一个规则过期、后一个规则有效时选择有效规则。
- 过期规则不降低 `confirmed_count`，不阻止补丁，不绕过 `fail_on=warning`。
- 缺少新字段的真实 1.0 归档报告和 2.0 报告均可读取，默认值为 `null`，原判断保持不变。
- 新生成 Schema 与仓库固定 Schema 一致，字段类型为 `string(date) | null`，默认 `null`。
