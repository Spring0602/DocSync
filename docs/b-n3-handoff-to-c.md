# B-N3 交付成员 C 联调与复验说明

成员 C 你好，成员 B 已完成 B-N3 中由 B 负责的到期日字段、忽略匹配、Schema、兼容测试和坏链接加固，现交给你完成报告展示与独立复验。

## 一、交付信息

- 项目：DocSync
- 分支：`member-b-tasks`
- B-N3 实现提交：`1edda88`
- 提交说明：`feat: implement B-N3 expiry contract and path guards`
- 字段契约：`docs/b-n3-ignore-expiry-contract-proposal.md`
- B 的复核报告：`docs/b-n3-ignore-expiry-symlink-review.md`
- 专项测试：`tests/integration/test_b_n3_ignore_expiry.py`
- 固定 Schema：`schemas/report.schema.json`

## 二、A 已确认的契约

A 已明确同意继续使用 `schema_version="2.0"`，并增加非必填字段：

```python
ignore_expires: date | None = None
```

JSON 使用 `YYYY-MM-DD`。只承诺新程序读取旧 1.0/2.0 报告，不承诺旧程序读取包含新字段的报告；原因是旧模型使用 `extra="forbid"`，会拒绝未知字段。

一次扫描固定使用同一个扫描日期。到期日等于扫描日时仍有效，只有早于扫描日才失效。读取旧报告时，缺失字段补 `null`，不得重新计算历史忽略状态，也不得改变原 Finding ID、patch ID 或 diff。

## 三、字段状态

| 场景 | `ignored` | `ignore_reason` | `ignore_expires` | 报告含义 |
| --- | --- | --- | --- | --- |
| 没有规则匹配 | `false` | `null` | `null` | 不显示忽略信息 |
| 匹配无期限规则 | `true` | 规则原因 | `null` | 当前忽略，无期限 |
| 未来或当天到期 | `true` | 规则原因 | `YYYY-MM-DD` | 当前忽略，并显示到期日 |
| 规则已经过期 | `false` | 规则原因 | `YYYY-MM-DD` | 规则已过期，告警未忽略 |

`ignored` 是扫描发生时的权威状态。报告打开或重新渲染时不得按照阅读当天的日期重新判断。

多条规则同时匹配时，B 的实现选择第一个有效规则；只有没有有效匹配时，才保留第一个已过期匹配。原因和日期始终来自同一条规则，不会混用。

## 四、请 C 完成的工作

C 负责修改报告渲染及其测试，不修改 B 已完成的数据模型、pipeline、Schema 和路径守卫。

建议修改范围：

- `src/docsync/reporting/__init__.py`
- C 新增或维护的报告展示测试
- C 自己的复验记录

请让 Markdown 报告明确展示：

1. 当前忽略且无期限：显示忽略原因和“无期限”。
2. 当前忽略且有期限：显示忽略原因和到期日。
3. 规则已经过期：显示原因、到期日及“规则已过期，告警未忽略”。
4. 没有匹配规则：不编造原因或日期。
5. JSON 和 Markdown 对同一 Finding 的含义一致。
6. 旧报告缺少字段时不得编造到期日。

过期规则对应的 Finding 仍应计入 `confirmed_count`，仍可生成补丁，并在 `fail_on=warning` 时触发相应退出状态。

## 五、B-N3 复验命令

在 DocSync 项目根目录执行：

```powershell
python -m pytest tests/integration/test_b_n3_ignore_expiry.py tests/unit/test_patch_guards.py -q -p no:cacheprovider --basetemp "$env:TEMP/pytest-b-n3-c-review"
```

B 本地结果为：

```text
17 passed, 2 skipped
```

两个 skip 都是当前 Windows 进程无权创建真实文件系统 symlink；不能将 skip 写成通过。

完成报告展示后，请运行相关契约回归：

```powershell
python -m pytest tests/integration/test_b_n3_ignore_expiry.py tests/integration/test_static_extensions.py tests/integration/test_a_contract_review.py tests/integration/test_b_repository_contracts.py tests/integration/test_b_alignment_patches.py tests/unit/test_patch_guards.py -q -p no:cacheprovider --basetemp "$env:TEMP/pytest-b-n3-c-related"
```

B 修改完成时的结果为：

```text
109 passed, 2 skipped
```

全量复验命令：

```powershell
python -m pytest -q -p no:cacheprovider --basetemp "$env:TEMP/pytest-b-n3-c-full"
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m build --no-isolation
```

B 修改完成时的全量结果为 `198 passed, 2 skipped`，Ruff、mypy 和 wheel/sdist 构建均通过。C 新增测试后通过数量应相应增加。

## 六、坏链接复核注意事项

B 已确认：

- Git mode `120000` symlink blob 会产生 `SYMLINK_SKIPPED`。
- 缺失或不可访问的补丁目标现在稳定返回 `UNSAFE_PATCH`，不会泄漏原始 `FileNotFoundError`。
- `safe_target` 会检查 symlink、Windows reparse point、严格解析结果和越界路径。

B 本机没有创建真实 symlink 的权限，因此真实越界和 dangling symlink 测试被明确跳过。请在有权限的 Windows/Linux 环境或远程 CI 中复验，记录实际结果；在获得证据前，不要写成“历史异常已经完全复现并关闭”。

如果你还能访问原来出现异常链接条目的设备，请补充：

- Windows 和 Python 版本；
- `symlink_to()` 是否抛异常；
- `exists()`、`is_symlink()` 和 `os.path.lexists()` 的值；
- `os.lstat()` 的完整结果或异常；
- `resolve(strict=True)` 的结果。

## 七、请 C 返回的结果

请在完成后提供：

- C 的提交 SHA；
- 实际修改文件；
- 专项、相关回归和全量测试结果；
- JSON/Markdown 四种状态展示样例；
- symlink 测试是通过、失败还是因权限跳过；
- 是否同意 B-N3 的字段与匹配部分通过验收。

全部通过时可以回复：

```text
C 已复验 B-N3 实现提交 1edda88，并完成报告展示。
JSON/Markdown 能区分无期限、有效期、规则已过期和无匹配四种状态；
过期规则显示“规则已过期，告警未忽略”，未重新计算历史报告；
专项与相关回归通过，symlink 场景结果已按实际通过/失败/跳过记录。
同意 B-N3 的字段、匹配和报告展示进入 A 的最终验收。
```

如果失败，请返回测试名称、完整错误、环境、预期结果和实际结果，不要提前标记 B-N3 已最终关闭。
