# B-N2 英文默认句式修复与回归记录

- 执行人：B
- 执行日期：2026-10-04
- 修复范围：C1 缺陷 D-1（`The default value of X is Y` 未提取）
- 状态：B 已完成实现与本地验证，等待 C 按本记录复核并关闭 D-1

## 缺陷复现与修复

修复前，下面的常见英文声明不会生成 `DEFAULT_ASSERTION`：

```markdown
## `connect`

The default value of `timeout` is `60`.
```

先加入 `tests/integration/test_b_n2_english_defaults.py` 后执行专项测试，结果为 **6 failed**；一致和冲突用例均因找不到默认值声明失败，限定与歧义用例也无法进入应有的拒答路径。

修复在 `src/docsync/extractors/markdown.py` 中增加独立的 `DEFAULT_VALUE_OF` 模式，并复用既有的标题/源码链接归属、历史语境判断、`add_value` 值解析及 UTF-8 字节定位逻辑。没有为该句式建立旁路判断，也没有把动态或歧义语义简化为一致。

## 回归矩阵

| 场景 | 预期与结果 |
| --- | --- |
| 文档值 60、代码默认值 60 | `CONSISTENT / LITERAL_EQUAL` |
| 文档值 30、代码默认值 60 | `INCONSISTENT / LITERAL_MISMATCH`，生成 1 条 finding |
| `Old version` 标题 | `UNCERTAIN / VERSION_UNRESOLVED`，不生成 finding |
| 两个同名 `connect` 定义 | `UNCERTAIN / AMBIGUOUS`，不取 top-1 强行确认 |
| 标题显式链接到 `client.py` | 只按链接归属 `client.py`，冲突证据指向该文件 |
| 同页合法显式调用 `connect(timeout=30)` | 调用为 `CONSISTENT / CALL_ACCEPTED`，不与默认值声明混淆 |

一致/冲突用例还验证了声明所属符号、文档路径、行号、SHA-256 blob hash，以及值在含中文前缀和 CRLF 文档中的精确 UTF-8 字节范围。

## 验证结果

- 修复前专项：**6 failed**。
- 修复后专项：**6 passed**。
- 原有流水线与静态扩展联合回归：**56 passed**。
- 全量回归：**186 passed，1 skipped**；唯一跳过是当前 Windows 进程无符号链接创建权限。
- Ruff：修改的两个 Python 文件检查及格式检查通过。
- mypy：20 个源文件通过。
- 构建：wheel 与 sdist 均成功。

Windows 下若仓库上级路径包含非 ASCII 字符，应把 pytest 的临时目录放到纯 ASCII 路径，避免 Action 包装器测试中的子进程路径被本地代码页改写。该环境问题与本次提取逻辑无关。

## 交给 C 的复验步骤

在项目根目录执行：

```powershell
python -m pytest tests/integration/test_b_n2_english_defaults.py -q -p no:cacheprovider --basetemp "$env:TEMP/pytest-b-n2-c-review"
python -m pytest tests/integration/test_pipeline.py tests/integration/test_static_extensions.py -q -p no:cacheprovider --basetemp "$env:TEMP/pytest-b-n2-c-related"
```

C 应重点复核：英文声明出现在 claims 中；一致/冲突判定符合固定源码；历史限定和同名歧义仍为 `UNCERTAIN`；`span` 与 `value_span` 能按 blob hash、行号和字节范围定位；随后在 C1 记录中追加真实复验结果。B 的本地通过不能代替 C 验收签字。

## 保留边界

本修复只承诺明确的 `default value of <identifier> is|:|= <literal>` 句式（允许开头的 `The` 和标识符反引号），不代表支持任意英语自然语言。无法归属实体、动态值、条件语境及复杂 Markdown 仍按既有规则拒答或不提取；未提取不等于一致。
